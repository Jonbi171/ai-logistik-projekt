#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
VENV_DIR="$BACKEND_DIR/venv"
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  local exit_status=$?
  trap - EXIT INT TERM

  if [[ -n "$BACKEND_PID" ]] || [[ -n "$FRONTEND_PID" ]]; then
    printf '\nStopping backend and frontend...\n'
  fi

  if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi

  if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi

  [[ -z "$BACKEND_PID" ]] || wait "$BACKEND_PID" 2>/dev/null || true
  [[ -z "$FRONTEND_PID" ]] || wait "$FRONTEND_PID" 2>/dev/null || true

  exit "$exit_status"
}

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

if [[ ! -f "$VENV_DIR/bin/activate" ]]; then
  if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: Python 3 is required to create the backend virtual environment." >&2
    exit 1
  fi

  echo "Creating backend virtual environment..."
  python3 -m venv "$VENV_DIR"
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
  python -m pip install -r "$BACKEND_DIR/requirements.txt"
else
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
fi

# Support both `backend.*` and `models.*` imports used by the backend modules.
export PYTHONPATH="$PROJECT_ROOT:$BACKEND_DIR${PYTHONPATH:+:$PYTHONPATH}"

#TODO: This needs to be more general //Jonte
if ! python -c 'import fastapi, matplotlib, numpy, pandas, psycopg, sklearn, sqlalchemy' >/dev/null 2>&1; then
  echo "Backend dependencies are missing or out of date; installing them..."
  python -m pip install -r "$BACKEND_DIR/requirements.txt"
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "Error: Node.js and npm are required to start the frontend." >&2
  exit 1
fi

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  echo "Installing frontend dependencies..."
  (cd "$FRONTEND_DIR" && npm ci)
fi

echo "Starting backend at http://127.0.0.1:8000"
(
  cd "$PROJECT_ROOT"
  exec fastapi dev backend/app/main.py --host 127.0.0.1 --port 8000
) &
BACKEND_PID=$!

echo "Starting frontend at http://127.0.0.1:5173"
(
  cd "$FRONTEND_DIR"
  exec npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
) &
FRONTEND_PID=$!

echo "Press Ctrl+C to stop both servers."

exit_status=0
while true; do
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    wait "$BACKEND_PID" || exit_status=$?
    echo "Backend stopped; shutting down the frontend." >&2
    break
  fi

  if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
    wait "$FRONTEND_PID" || exit_status=$?
    echo "Frontend stopped; shutting down the backend." >&2
    break
  fi

  sleep 1
done

exit "$exit_status"
