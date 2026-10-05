#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
python3 -m pip install -r requirements.txt
python3 -X utf8 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
