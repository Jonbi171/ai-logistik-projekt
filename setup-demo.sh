#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
command -v python3 >/dev/null || { echo 'Python 3.12+ is required.' >&2; exit 1; }
command -v node >/dev/null || { echo 'Node.js 22.12+ and npm are required.' >&2; exit 1; }
if [[ ! -x backend/venv/bin/python ]]; then python3 -m venv backend/venv; fi
PYTHON="$ROOT/backend/venv/bin/python"
if ! "$PYTHON" -c 'import fastapi, uvicorn, numpy, pandas, psycopg, sklearn, sqlalchemy, joblib' >/dev/null 2>&1; then
  "$PYTHON" -m pip install -r backend/requirements.txt
fi
if [[ ! -d frontend/node_modules/recharts || ! -d frontend/node_modules/lucide-react ]]; then
  (cd frontend && npm ci)
fi
if [[ ! -f backend/artifacts/models.joblib || "${DEMO_RETRAIN:-0}" == 1 ]]; then
  echo 'Training evaluated models (initial setup only)...'
  if [[ "${DEMO_OFFLINE:-0}" == 1 ]]; then
    "$PYTHON" -m backend.ml.train_all --offline
  else
    "$PYTHON" -m backend.ml.train_all
  fi
fi
echo 'Demo dependencies and model artifacts are ready.'
