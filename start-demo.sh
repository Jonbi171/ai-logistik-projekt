#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
./setup-demo.sh
PYTHON="$ROOT/backend/venv/bin/python"
BACKEND_PID=""
FRONTEND_PID=""
cleanup() {
  local status=$?
  trap - EXIT INT TERM
  [[ -z "$BACKEND_PID" ]] || kill "$BACKEND_PID" 2>/dev/null || true
  [[ -z "$FRONTEND_PID" ]] || kill "$FRONTEND_PID" 2>/dev/null || true
  [[ -z "$BACKEND_PID" ]] || wait "$BACKEND_PID" 2>/dev/null || true
  [[ -z "$FRONTEND_PID" ]] || wait "$FRONTEND_PID" 2>/dev/null || true
  echo 'Demo stopped.'
  exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
"$PYTHON" - <<'PY'
import socket
for port in (8000,5173):
    with socket.socket() as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(('127.0.0.1',port))
        except PermissionError:
            raise SystemExit(f'Permission denied binding local port {port}. Run the startup script with local networking allowed.')
        except OSError:
            raise SystemExit(f'Port {port} is unavailable. Stop the process using it before starting the demo.')
PY
"$PYTHON" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
for attempt in {1..60}; do
  if curl --silent --fail http://127.0.0.1:8000/health >/dev/null; then break; fi
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then echo 'Backend failed to start.' >&2; exit 1; fi
  if [[ "$attempt" == 60 ]]; then echo 'Backend readiness timed out. Check data access and model artifacts.' >&2; exit 1; fi
  sleep 1
done
(cd frontend && exec node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort) &
FRONTEND_PID=$!
echo ''
echo 'Intelligent Control Tower: http://127.0.0.1:5173'
echo 'API documentation:        http://127.0.0.1:8000/docs'
echo 'Press Ctrl+C to stop both servers.'
while kill -0 "$BACKEND_PID" 2>/dev/null && kill -0 "$FRONTEND_PID" 2>/dev/null; do sleep 1; done
echo 'A server stopped unexpectedly.' >&2
exit 1
