# -*- coding: utf-8 -*-
"""Kiểm thử vận hành & bảo trì (NFR-R5, NFR-M1, M2, M4, M5) trên bản chạy docker compose.

    .venv\\Scripts\\python st_van_hanh.py

ST-82 sao lưu CSDL bằng scripts/backup_db.ps1 rồi khôi phục vào một CSDL TẠM (smartcafe_restore_check) để đối chiếu,
không đụng CSDL demo; CSDL tạm bị xóa sau khi kiểm tra.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import httpx

from common import ROOT, Report, args, docker, sql

rep = Report()
TABLES = ["branches", "dining_tables", "staff", "menu_items", "orders", "order_items", "payments", "customers",
          "loyalty_transactions", "daily_sales_reports", "association_rules"]


def compose(*cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run([docker(), "compose", *cmd], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")


def counts(db: str) -> dict[str, int]:
    q = " UNION ALL ".join(f"SELECT '{t}', count(*) FROM {t}" for t in TABLES)
    out = compose("exec", "-T", "db", "psql", "-U", "smartcafe", "-d", db, "-At", "-F", "|", "-c", q).stdout
    return {k: int(v) for k, v in (line.split("|") for line in out.splitlines() if line)}


def main() -> int:
    a = args()
    api = httpx.Client(base_url=a.api_url, timeout=15)

    # NFR-M1: Swagger tự sinh, module theo nghiệp vụ
    docs = api.get("/docs")
    spec = api.get("/openapi.json").json()
    paths = spec["paths"]
    tags = sorted({t for p in paths.values() for op in p.values() for t in op.get("tags", [])})
    modules = sorted(d.name for d in (ROOT / "backend" / "app" / "modules").iterdir() if d.is_dir() and not d.name.startswith("_"))
    need = {"auth", "customer", "menu", "branch", "order", "payment", "recommend"}
    rep.check("ST-80", "NFR-M1: Swagger /docs tự sinh; backend chia module theo nghiệp vụ (auth, customer, menu, branch, "
              "order, payment, recommend …)", docs.status_code == 200 and "swagger" in docs.text.lower()
              and need <= set(modules) and len(paths) >= 30,
              f"{len(paths)} đường dẫn API, nhóm {tags}; module {modules}")

    # NFR-M2: Alembic
    cur = compose("exec", "-T", "backend", "alembic", "current").stdout
    heads = compose("exec", "-T", "backend", "alembic", "heads").stdout
    head = re.findall(r"^(\w+) \(head\)", heads, re.M)
    rep.check("ST-81", "NFR-M2: CSDL đang ở đúng phiên bản migration mới nhất của Alembic (1 head)",
              len(head) == 1 and head[0] in cur, f"current: {cur.strip()} | heads: {heads.strip()}")

    # NFR-R5: sao lưu + khôi phục thử
    out = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                          str(ROOT / "scripts" / "backup_db.ps1")], cwd=ROOT, capture_output=True, text=True)
    m = re.search(r"BACKUP_OK (.+\.dump) (\d+)", out.stdout)
    restored, before, after = False, {}, {}
    if m:
        dump = Path(m.group(1))
        before = counts("smartcafe")
        compose("exec", "-T", "db", "dropdb", "-U", "smartcafe", "--if-exists", "smartcafe_restore_check")
        r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                            str(ROOT / "scripts" / "restore_db.ps1"), "-File", str(dump), "-DbName",
                            "smartcafe_restore_check"], cwd=ROOT, capture_output=True, text=True)
        restored = "RESTORE_OK" in r.stdout
        after = counts("smartcafe_restore_check")
        compose("exec", "-T", "db", "dropdb", "-U", "smartcafe", "--if-exists", "smartcafe_restore_check")
    rep.check("ST-82", "NFR-R5: scripts/backup_db.ps1 sao lưu CSDL (pg_dump); khôi phục bản sao lưu vào CSDL tạm → "
              "số dòng 11 bảng chính khớp CSDL gốc", m and restored and before and before == after,
              f"{Path(m.group(1)).name if m else out.stderr[-200:]} ({int(m.group(2)) // 1024 if m else 0} KB); "
              f"orders {before.get('orders')} → {after.get('orders')}; lệch: "
              f"{ {k: (before[k], after.get(k)) for k in before if before[k] != after.get(k)} }")

    # NFR-M4: interface Payment / SMS
    sms = (ROOT / "backend" / "app" / "modules" / "customer" / "sms.py").read_text(encoding="utf-8")
    pay = (ROOT / "backend" / "app" / "modules" / "payment" / "gateway.py").read_text(encoding="utf-8")
    rep.check("ST-83", "NFR-M4: SMS và cổng thanh toán đi qua interface (Protocol) – bản giả lập là 1 cài đặt, thay bằng "
              "dịch vụ thật không sửa nghiệp vụ", "class SmsSender(Protocol)" in sms and "class PaymentGateway(Protocol)" in pay
              and "class MockSmsSender" in sms and "class MockPaymentGateway" in pay)

    # NFR-M5: docker compose + .env.example
    cfg = compose("config", "--services")
    env_keys = set(re.findall(r"^([A-Z_]+)=", (ROOT / ".env.example").read_text(encoding="utf-8"), re.M))
    settings = (ROOT / "backend" / "app" / "core" / "config.py").read_text(encoding="utf-8")
    fields = {f.upper() for f in re.findall(r"^    (\w+): ", settings, re.M)}
    missing = sorted(fields - env_keys - {"DATABASE_URL", "JWT_ALGORITHM", "TEST_DATABASE_URL"})
    ps = compose("ps", "--format", "{{.Service}} {{.State}}").stdout.split("\n")
    rep.check("ST-84", "NFR-M5: chạy toàn hệ thống bằng docker compose (db, backend, frontend đang chạy); .env.example có "
              "các biến cấu hình chính", cfg.returncode == 0 and set(cfg.stdout.split()) == {"db", "backend", "frontend"}
              and sum("running" in x for x in ps) == 3 and len(env_keys) >= 15,
              f"{len(env_keys)} biến trong .env.example; biến cấu hình chưa có trong .env.example: {missing}")
    print("Bảng có dữ liệu:", sql("SELECT count(*) FROM orders")[0][0], "đơn")
    return rep.finish()


if __name__ == "__main__":
    raise SystemExit(main())
