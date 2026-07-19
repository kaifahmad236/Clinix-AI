#!/usr/bin/env bash
# Start the FastAPI backend with Uvicorn, honoring the $PORT env var
# (defaults to 8000 when PORT is not set, e.g. for local runs).
set -e

PORT="${PORT:-8000}"

exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
