#!/usr/bin/env bash
# Chạy toàn bộ kiểm thử giai đoạn VI trên CSDL sạch (Git Bash trên Windows). Log ghi vào 1.Bao_cao/Kiem_thu/logs/ST_*.txt
#   bash system_test/chay_tat_ca.sh            (chạy từ thư mục 2.San_pham/smartcafe)
set -u
cd "$(dirname "$0")/.."
export PATH="$PATH:/d/Docker/DockerDesktop/resources/bin:/d/Dev/nodejs" PYTHONIOENCODING=utf-8
L="$(pwd)/../../1.Bao_cao/Kiem_thu/logs"
PY="$(pwd)/system_test/.venv/Scripts/python.exe"

echo "== Dựng lại hệ thống, CSDL sạch"
docker compose down -v >/dev/null 2>&1
docker compose up -d --build >/dev/null 2>&1
for i in $(seq 1 120); do
  docker compose logs backend 2>&1 | grep -q "startup complete" && curl -sf http://localhost:8080/api/health >/dev/null && break
  sleep 2
done
docker compose logs backend 2>&1 | grep "\[seed" | tee "$L/ST_moi_truong.txt"
docker compose ps --format "{{.Service}} {{.Image}} {{.Status}}" >> "$L/ST_moi_truong.txt"

run() {  # run <log> <lệnh...>
  local log=$1; shift
  echo "== $log"
  "$@" > "$L/$log" 2>&1
  echo "   exit $? – $(grep -a '^Tổng\|passed\|Tests ' "$L/$log" | tail -1)"
}
cd system_test
run ST_kich_ban_xuyen_luong.txt "$PY" -u st_kich_ban.py
sleep 65                                   # OTP SĐT demo: gửi lại sau 60 giây (NFR-S4)
run ST_bao_mat.txt "$PY" -u st_bao_mat.py
run ST_giao_dien_trinh_duyet.txt "$PY" -u st_giao_dien.py --webkit
run ST_hieu_nang_tai.txt "$PY" -u st_hieu_nang.py
run ST_van_hanh.txt "$PY" -u st_van_hanh.py
rm -f ../backups/*.dump
cd ../backend
TOK=$(MSYS_NO_PATHCONV=1 docker compose exec -T backend python -m scripts.seed_data --print-qr | grep -o "/t/[A-Za-z0-9_-]*" | head -1 | cut -d/ -f3)
sleep 65
run ST_hoi_quy_smoke_test.txt .venv/Scripts/python.exe -m scripts.smoke_test --qr-token "$TOK"
run ST_hoi_quy_backend_toan_bo.txt .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --cov=app --cov-report=term
cd ../frontend
run ST_hoi_quy_frontend_vitest.txt npx vitest run --coverage
echo "== Xong"
