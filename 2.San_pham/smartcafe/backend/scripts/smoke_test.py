"""Kiểm thử khói (smoke test) trên hệ thống đang chạy bằng docker compose, đi qua Nginx như điện thoại khách.

    python -m scripts.smoke_test --base-url http://localhost:8080 --qr-token <token của 1 bàn>
    (lấy token: docker compose exec backend python -m scripts.seed_data --print-qr)
"""
import argparse
import sys
import time

import httpx

RESULTS: list[tuple[str, str, bool, str]] = []


def check(tc: str, name: str, cond: bool, info: str = "") -> None:
    RESULTS.append((tc, name, cond, info))
    print(f"[{'ĐẠT' if cond else 'KHÔNG ĐẠT'}] {tc} {name} {info}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8080")
    ap.add_argument("--qr-token", required=True)
    ap.add_argument("--password", default="smartcafe123")
    a = ap.parse_args()
    c = httpx.Client(base_url=a.base_url, timeout=10)

    r = c.get("/api/health")
    check("SM-01", "Backend sống qua Nginx", r.status_code == 200 and r.json() == {"status": "ok"})

    r = c.get("/admin/login")
    check("SM-02", "Nginx trả SPA cho /admin/login", r.status_code == 200 and '<div id="root">' in r.text)
    r = c.get(f"/t/{a.qr_token}")
    check("SM-03", "Nginx trả SPA cho link QR /t/<token>", r.status_code == 200 and '<div id="root">' in r.text)

    r = c.post("/api/auth/login", json={"username": "admin", "password": a.password})
    ok = r.status_code == 200 and r.json()["staff"]["role"] == "ADMIN"
    check("SM-04", "Đăng nhập tài khoản mẫu admin", ok)
    if ok:
        me = c.get("/api/auth/me", headers={"Authorization": f"Bearer {r.json()['access_token']}"})
        check("SM-05", "/api/auth/me với token vừa cấp", me.status_code == 200 and me.json()["username"] == "admin")

    r = c.post("/api/auth/login", json={"username": "pc1_cg", "password": "sai"})
    check("SM-06", "Sai mật khẩu bị từ chối", r.status_code == 401 and r.json()["error"]["code"] == "INVALID_CREDENTIALS")

    r = c.get(f"/api/public/tables/{a.qr_token}")
    ok = r.status_code == 200
    check("SM-07", "Quét QR thật -> chi nhánh + bàn", ok, r.text[:120] if ok else str(r.status_code))
    if ok:
        bid = r.json()["branch"]["id"]
        t0 = time.perf_counter()
        m = c.get(f"/api/public/branches/{bid}/menu")
        ms = (time.perf_counter() - t0) * 1000
        n = sum(len(cat["items"]) for cat in m.json()["categories"])
        check("SM-08", "Menu chi nhánh có đủ 35 món, 5 danh mục", m.status_code == 200 and n == 35 and len(m.json()["categories"]) == 5)
        check("SM-09", "API menu phản hồi < 300 ms (1 request, tham khảo NFR-P2)", ms < 300, f"{ms:.0f} ms")

    r = c.get("/api/public/tables/qr-gia-mao")
    check("SM-10", "QR giả -> TABLE_NOT_FOUND", r.status_code == 404 and r.json()["error"]["code"] == "TABLE_NOT_FOUND")

    failed = [x for x in RESULTS if not x[2]]
    print(f"\nTổng: {len(RESULTS)} | Đạt: {len(RESULTS) - len(failed)} | Không đạt: {len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
