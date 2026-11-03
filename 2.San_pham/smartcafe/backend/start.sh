#!/bin/sh
set -e
alembic upgrade head
if [ "${SEED_ON_START:-true}" = "true" ]; then
  python -m scripts.seed_data --if-empty
  python -m scripts.seed_orders --if-empty   # đơn lịch sử + thành viên + luật kết hợp (F7, D32)
fi
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
