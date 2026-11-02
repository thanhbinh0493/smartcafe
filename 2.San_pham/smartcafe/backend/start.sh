#!/bin/sh
set -e
alembic upgrade head
if [ "${SEED_ON_START:-true}" = "true" ]; then
  python -m scripts.seed_data --if-empty
fi
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
