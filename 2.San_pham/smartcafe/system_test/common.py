# -*- coding: utf-8 -*-
"""Tiện ích dùng chung cho bộ kiểm thử hệ thống (giai đoạn VI) trên bản chạy `docker compose`.

Mọi script nhận `--base-url` (mặc định http://localhost:8080, đi qua Nginx như người dùng thật)
và tự lấy mã QR bàn bằng API quản trị, không cần truyền token bằng tay.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent          # 2.San_pham/smartcafe
PASSWORD = "smartcafe123"
DEMO_PHONE = "0901000001"                                # SĐT demo có lịch sử (D32), chi nhánh Cầu Giấy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


class Report:
    """Ghi kết quả từng ca kiểm thử theo dạng [ĐẠT] ST-xx ... giống các biên bản luồng."""

    def __init__(self) -> None:
        self.results: list[tuple[str, str, bool, str]] = []

    def check(self, tc: str, name: str, ok: object, info: str = "") -> bool:
        ok = bool(ok)
        self.results.append((tc, name, ok, info))
        print(f"[{'ĐẠT' if ok else 'KHÔNG ĐẠT'}] {tc} {name} {info}".rstrip(), flush=True)
        return ok

    def finish(self) -> int:
        failed = [r for r in self.results if not r[2]]
        print(f"\nTổng: {len(self.results)} | Đạt: {len(self.results) - len(failed)} | Không đạt: {len(failed)}")
        return 1 if failed else 0


def args(extra=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=os.environ.get("SMARTCAFE_URL", "http://localhost:8080"))
    ap.add_argument("--api-url", default="http://localhost:8000", help="backend trực tiếp (Swagger)")
    ap.add_argument("--img", default=str(ROOT.parent.parent / "1.Bao_cao" / "Kiem_thu" / "img"))
    if extra:
        extra(ap)
    return ap.parse_args()


def login(c: httpx.Client, username: str, password: str = PASSWORD) -> dict:
    r = c.post("/api/auth/login", json={"username": username, "password": password})
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def branches(c: httpx.Client, admin: dict) -> dict[str, dict]:
    """{mã chi nhánh: chi nhánh}, VD {'CG': {...}, 'HD': {...}, 'TX': {...}}."""
    return {b["code"]: b for b in c.get("/api/staff/branches", headers=admin).json()}


def tables(c: httpx.Client, admin: dict, branch_id: int) -> list[dict]:
    return [t for t in c.get(f"/api/staff/branches/{branch_id}/tables", headers=admin).json() if t["is_active"]]


def menu(c: httpx.Client, branch_id: int) -> dict[str, dict]:
    """Menu công khai của chi nhánh: {tên món: món}."""
    data = c.get(f"/api/public/branches/{branch_id}/menu").json()
    return {i["name"]: i for cat in data["categories"] for i in cat["items"]}


def place_order(c: httpx.Client, qr_token: str, lines: list[tuple[dict, int]], headers: dict | None = None,
                pay: bool = True, **extra) -> dict:
    """Tạo đơn (server tính tiền) rồi thanh toán giả lập. Trả dữ liệu đơn kèm thời điểm thanh toán."""
    body = {"qr_token": qr_token, "items": [{"menu_item_id": m["id"], "quantity": q} for m, q in lines], **extra}
    r = c.post("/api/public/orders", json=body, headers=headers or {})
    r.raise_for_status()
    o = r.json()
    if pay:
        p = c.post(f"/api/public/orders/{o['order_id']}/pay",
                   json={"access_token": o["access_token"], "method": "MOCK_EWALLET"})
        p.raise_for_status()
        o["paid_at_perf"] = time.perf_counter()
    return o


def member_login(c: httpx.Client, phone: str) -> dict:
    """OTP giả lập (D12): lấy mã ở trường demo_code rồi xác thực. Trả header của phiên thành viên."""
    r = c.post("/api/public/otp/request", json={"phone": phone})
    r.raise_for_status()
    v = c.post("/api/public/otp/verify", json={"phone": phone, "code": r.json()["demo_code"]})
    v.raise_for_status()
    return {"Authorization": f"Bearer {v.json()['customer_token']}"}


def member_token(phone: str) -> dict:
    """Cấp phiên thành viên cho SĐT đã có trong CSDL mà không qua OTP (OTP giới hạn 5 mã/giờ/SĐT – NFR-S4),
    dùng cho các ca không kiểm thử OTP. Ký bằng chính hàm của backend."""
    tok = backend_py(
        "from sqlalchemy import select\n"
        "from app.core.db import SessionLocal\n"
        "from app.core.security import create_customer_token\n"
        "from app.models.customer import Customer\n"
        f"db = SessionLocal(); cid = db.scalar(select(Customer.id).where(Customer.phone == '{phone}'))\n"
        "print(create_customer_token(cid)[0])\n").strip()
    return {"Authorization": f"Bearer {tok}"}


def random_phone() -> str:
    """SĐT di động chưa từng dùng (đầu 09, 10 số) để không đụng giới hạn OTP của SĐT demo."""
    import random
    return "09" + "".join(random.choice("0123456789") for _ in range(8))


def finish_order(c: httpx.Client, bar: dict, order_id: int, branch_id: int) -> None:
    """Pha chế làm hết món của đơn rồi bấm "Đã giao"."""
    q = c.get(f"/api/staff/branches/{branch_id}/queue", headers=bar).json()["items"]
    for it in [i for i in q if i["order_id"] == order_id]:
        if it["status"] == "WAITING":
            c.post(f"/api/staff/order-items/{it['id']}/start", headers=bar).raise_for_status()
        c.post(f"/api/staff/order-items/{it['id']}/done", headers=bar).raise_for_status()
    c.post(f"/api/staff/orders/{order_id}/complete", headers=bar).raise_for_status()


def p95(values: list[float]) -> float:
    if len(values) < 2:
        return values[0] if values else 0.0
    return statistics.quantiles(values, n=100, method="inclusive")[94]


def docker() -> str:
    exe = shutil.which("docker") or r"D:\Docker\DockerDesktop\resources\bin\docker.exe"
    return exe


def sql(query: str) -> list[list[str]]:
    """Chạy SQL trong container db (psql), trả các dòng đã tách cột theo '|'."""
    out = subprocess.run([docker(), "compose", "exec", "-T", "db", "psql", "-U", "smartcafe", "-d", "smartcafe",
                          "-At", "-F", "|", "-c", query], cwd=ROOT, capture_output=True, text=True,
                         encoding="utf-8", check=True).stdout
    return [line.split("|") for line in out.splitlines() if line]


def backend_py(code: str) -> str:
    """Chạy đoạn Python trong container backend (dùng được app.*), trả stdout."""
    r = subprocess.run([docker(), "compose", "exec", "-T", "backend", "python", "-c", code], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise RuntimeError(r.stderr[-2000:])
    return r.stdout


def dump(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)
