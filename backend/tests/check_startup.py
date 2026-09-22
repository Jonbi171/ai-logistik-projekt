"""Verify real startup, offline mode and cleanup without touching database state.

Run while ports 8000 and 5173 are free, after preparing model artifacts.
"""

import json
import os
import signal
import socket
import subprocess
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]


def port_open(port):
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


def check(offline):
    for port in (8000, 5173):
        if port_open(port):
            raise RuntimeError(f"Port {port} is occupied; stop existing servers first.")
    stamp = (ROOT / "backend/artifacts/models.joblib").stat().st_mtime_ns
    env = os.environ.copy()
    if offline:
        env["DEMO_OFFLINE"] = "1"
    else:
        env.pop("DEMO_OFFLINE", None)
    process = subprocess.Popen(
        ["./start-demo.sh"],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    captured = ""
    try:
        deadline = time.monotonic() + 55
        while time.monotonic() < deadline:
            if process.poll() is not None:
                captured = process.stdout.read()
                raise RuntimeError("Startup process exited early: " + captured[-1500:])
            try:
                with urlopen("http://127.0.0.1:5173/api/tower/overview", timeout=2) as response:
                    overview = json.load(response)
                break
            except (URLError, TimeoutError, ConnectionError):
                time.sleep(0.4)
        else:
            raise RuntimeError("Demo did not become ready within 55 seconds.")
        with urlopen("http://127.0.0.1:5173/", timeout=3) as response:
            assert "NordicFlow" in response.read().decode()
        assert overview["source"]["offline"] == offline, overview["source"]
        assert len(overview["kpis"]) == 8
        assert (ROOT / "backend/artifacts/models.joblib").stat().st_mtime_ns == stamp, (
            "Normal startup unexpectedly retrained models"
        )
        print(
            f"{'Offline' if offline else 'PostgreSQL'} startup: API proxy, frontend, KPIs and cached models verified.",
            flush=True,
        )
    finally:
        process.send_signal(signal.SIGINT)
        try:
            output = captured + process.communicate(timeout=10)[0]
        except subprocess.TimeoutExpired:
            process.terminate()
            output = process.communicate(timeout=5)[0]
        if port_open(8000) or port_open(5173):
            raise RuntimeError("A server remained listening after startup script cleanup.")
        if "Demo stopped." not in output:
            raise RuntimeError("Cleanup confirmation missing.")
        print("Ctrl+C cleanup: both ports released.", flush=True)


if __name__ == "__main__":
    check(False)
    check(True)
