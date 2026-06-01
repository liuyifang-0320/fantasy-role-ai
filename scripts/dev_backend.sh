#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/../backend"
echo "Starting backend at http://127.0.0.1:8000"
python -m uvicorn main:app --host 127.0.0.1 --port 8000
