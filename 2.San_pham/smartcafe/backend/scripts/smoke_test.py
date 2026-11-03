"""Kiểm thử khói (smoke test) trên hệ thống đang chạy bằng docker compose, đi qua Nginx như điện thoại khách.

    python -m scripts.smoke_test --base-url http://localhost:8080 --qr-token <token của 1 bàn>
    (lấy token: docker compose exec backend python -m scripts.seed_data --print-qr)
"""
import argparse
import json
import random
import sys
import time

import httpx
from websockets.sync.client import connect as ws_connect

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

    # ---- F2: đặt món & thanh toán giả lập ----
    if ok:
        items = {i["name"]: i for cat in m.json()["categories"] for i in cat["items"]}
        lines = [items["Cà phê sữa đá"], items["Trà đào cam sả"]]
        expected = lines[0]["sell_price"] * 2 + lines[1]["sell_price"]
        body = {"qr_token": a.qr_token, "expected_total": expected, "items": [
            {"menu_item_id": lines[0]["id"], "quantity": 2, "note": "ít đường"},
            {"menu_item_id": lines[1]["id"], "quantity": 1}]}
        r = c.post("/api/public/orders", json=body)
        o = r.json() if r.status_code == 201 else {}
        check("SM-11", "Tạo đơn qua Nginx, server tính đúng tổng tiền", r.status_code == 201 and o.get("total") == expected,
              f"{o.get('order_code')} tổng {o.get('total')}")
        if o:
            ws_url = a.base_url.replace("http", "ws", 1) + f"/ws/order/{o['order_id']}?token={o['access_token']}"
            with ws_connect(ws_url, open_timeout=5) as ws:
                snap = json.loads(ws.recv(timeout=5))
                check("SM-12", "WebSocket qua Nginx nhận ảnh chụp đơn", snap["type"] == "ORDER_SNAPSHOT"
                      and snap["data"]["status"] == "PENDING_PAYMENT")
                t0 = time.perf_counter()
                p = c.post(f"/api/public/orders/{o['order_id']}/pay",
                           json={"access_token": o["access_token"], "method": "MOCK_EWALLET"})
                check("SM-13", "Thanh toán giả lập thành công", p.status_code == 200 and p.json()["status"] == "PAID")
                evt = json.loads(ws.recv(timeout=5))
                ms = (time.perf_counter() - t0) * 1000
                check("SM-14", "Trang theo dõi nhận ORDER_PAID realtime ≤ 2 giây (NFR-P4)",
                      evt["type"] == "ORDER_PAID" and evt["data"]["status"] == "PAID" and ms <= 2000, f"{ms:.0f} ms")
            v = c.get(f"/api/public/orders/{o['order_id']}", params={"token": o["access_token"]})
            check("SM-15", "Xem đơn: PAID, có vị trí hàng đợi", v.status_code == 200 and v.json()["status"] == "PAID"
                  and v.json()["queue_position"] >= 1, f"vị trí {v.json().get('queue_position')}")
            v = c.get(f"/api/public/orders/{o['order_id']}", params={"token": "doan-mo"})
            check("SM-16", "Sai access_token -> ORDER_NOT_FOUND", v.status_code == 404)
            smoke_bar(c, a, bid, r_table_code(c, a.qr_token), o)
            smoke_member(c, a, bid, r_table_code(c, a.qr_token), lines)
            smoke_support(c, a, bid, r_table_code(c, a.qr_token), lines)

    failed = [x for x in RESULTS if not x[2]]
    print(f"\nTổng: {len(RESULTS)} | Đạt: {len(RESULTS) - len(failed)} | Không đạt: {len(failed)}")
    return 1 if failed else 0


def r_table_code(c: httpx.Client, qr_token: str) -> str:
    return c.get(f"/api/public/tables/{qr_token}").json()["branch"]["code"].lower()


def recv_until(ws, type_: str, timeout: float = 5) -> dict:
    """Đọc message tới khi gặp đúng loại sự kiện (bỏ qua các sự kiện khác như QUEUE_POSITION)."""
    end = time.perf_counter() + timeout
    while True:
        msg = json.loads(ws.recv(timeout=max(0.1, end - time.perf_counter())))
        if msg["type"] == type_:
            return msg


def smoke_bar(c: httpx.Client, a, bid: int, code: str, o: dict) -> None:
    """F3: pha chế xử lý đơn vừa đặt trên màn hình Bar; khách nhận trạng thái realtime."""
    r = c.post("/api/auth/login", json={"username": f"pc1_{code}", "password": a.password})
    if r.status_code != 200:
        check("SM-17", f"Đăng nhập pha chế pc1_{code}", False, str(r.status_code))
        return
    tok = r.json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    q = c.get(f"/api/staff/branches/{bid}/queue", headers=h)
    mine = [i for i in q.json()["items"] if i["order_id"] == o["order_id"]]
    check("SM-17", "Hàng đợi Bar có 2 món của đơn vừa thanh toán", q.status_code == 200 and len(mine) == 2,
          f"{len(q.json()['items'])} món trong hàng đợi")

    base_ws = a.base_url.replace("http", "ws", 1)
    with ws_connect(f"{base_ws}/ws/bar/{bid}?token={tok}", open_timeout=5) as bar_ws, \
            ws_connect(f"{base_ws}/ws/order/{o['order_id']}?token={o['access_token']}", open_timeout=5) as cust_ws:
        recv_until(cust_ws, "ORDER_SNAPSHOT")
        t0 = time.perf_counter()
        s = c.post(f"/api/staff/order-items/{mine[0]['id']}/start", headers=h)
        evt = recv_until(cust_ws, "ITEM_PREPARING")
        ms = (time.perf_counter() - t0) * 1000
        check("SM-18", "Pha chế bấm Bắt đầu -> khách thấy 'Đang pha chế' ≤ 2 giây",
              s.status_code == 200 and evt["data"]["status"] == "PREPARING" and ms <= 2000, f"{ms:.0f} ms")
        upd = recv_until(bar_ws, "ITEM_UPDATED")
        check("SM-19", "Màn hình Bar khác nhận ITEM_UPDATED qua WebSocket", upd["data"]["item_id"] == mine[0]["id"])

        c.post(f"/api/staff/order-items/{mine[1]['id']}/start", headers=h)
        c.post(f"/api/staff/order-items/{mine[0]['id']}/done", headers=h)
        t0 = time.perf_counter()
        d = c.post(f"/api/staff/order-items/{mine[1]['id']}/done", headers=h)
        evt = recv_until(cust_ws, "ORDER_READY")
        ms = (time.perf_counter() - t0) * 1000
        check("SM-20", "Xong món cuối -> khách nhận 'Có thể lấy' ≤ 2 giây (NFR-P4)",
              d.status_code == 200 and d.json()["order_status"] == "READY" and ms <= 2000, f"{ms:.0f} ms")
        ready = c.get(f"/api/staff/branches/{bid}/orders", params={"status": "READY"}, headers=h).json()
        check("SM-21", "Đơn xuất hiện ở cột 'Có thể lấy'", any(x["id"] == o["order_id"] for x in ready))

        tn = c.post("/api/auth/login", json={"username": f"tn_{code}", "password": a.password}).json()["access_token"]
        r = c.post(f"/api/staff/orders/{o['order_id']}/complete", headers={"Authorization": f"Bearer {tn}"})
        check("SM-22", "Thu ngân không được bấm 'Đã giao' (403)", r.status_code == 403)

        r = c.post(f"/api/staff/orders/{o['order_id']}/complete", headers=h)
        evt = recv_until(cust_ws, "ORDER_COMPLETED")
        check("SM-23", "Pha chế bấm 'Đã giao' -> đơn hoàn tất, khách nhận ORDER_COMPLETED",
              r.status_code == 200 and r.json()["status"] == "COMPLETED" and evt["data"]["status"] == "COMPLETED")


def smoke_member(c: httpx.Client, a, bid: int, code: str, lines: list[dict]) -> None:
    """F4: khách nhập SĐT + OTP giả lập, đặt món ở chế độ thành viên, nhận đồ thì được cộng điểm."""
    phone = "09" + "".join(random.choices("0123456789", k=8))  # SĐT mới mỗi lần chạy (tránh giới hạn gửi mã)
    r = c.post("/api/public/otp/request", json={"phone": phone})
    sent = r.json() if r.status_code == 200 else {}
    check("SM-24", "Gửi OTP giả lập: hạn 5 phút, chờ 60 giây, có mã [DEMO]", r.status_code == 200
          and sent["expires_in"] == 300 and sent["resend_after"] == 60 and len(sent.get("demo_code") or "") == 6,
          sent.get("phone_masked", str(r.status_code)))
    if not sent:
        return
    r = c.post("/api/public/otp/request", json={"phone": phone})
    check("SM-25", "Gửi lại ngay -> 429 OTP_RATE_LIMITED", r.status_code == 429
          and r.json()["error"]["code"] == "OTP_RATE_LIMITED", r.json()["error"]["message"])
    bad = f"{(int(sent['demo_code']) + 1) % 1_000_000:06d}"
    r = c.post("/api/public/otp/verify", json={"phone": phone, "code": bad})
    check("SM-26", "Sai mã -> OTP_INVALID, còn 4 lần thử", r.status_code == 400
          and r.json()["error"]["details"] == {"reason": "WRONG", "attempts_left": 4})
    r = c.post("/api/public/otp/verify", json={"phone": phone, "code": sent["demo_code"]})
    ok = r.status_code == 200
    check("SM-27", "Nhập đúng mã -> customer token, 0 điểm", ok and r.json()["loyalty_points"] == 0)
    if not ok:
        return
    h = {"Authorization": f"Bearer {r.json()['customer_token']}"}
    me = c.get("/api/public/me", headers=h)
    check("SM-28", "Xem điểm /api/public/me", me.status_code == 200 and me.json()["loyalty_points"] == 0,
          me.json().get("phone_masked", ""))
    r = c.get(f"/api/staff/branches/{bid}/queue", headers=h)
    check("SM-29", "Customer token không gọi được API nhân viên (403)", r.status_code == 403)

    body = {"qr_token": a.qr_token, "items": [{"menu_item_id": lines[1]["id"], "quantity": 3}]}
    o = c.post("/api/public/orders", json=body, headers=h).json()
    expected = (lines[1]["sell_price"] * 3) // 10_000
    check("SM-30", "Đặt món chế độ thành viên: có expected_points", o.get("expected_points") == expected,
          f"{o.get('order_code')} tổng {o.get('total')}, +{o.get('expected_points')} điểm")
    c.post(f"/api/public/orders/{o['order_id']}/pay", json={"access_token": o["access_token"], "method": "MOCK_CARD"})
    tok = c.post("/api/auth/login", json={"username": f"pc1_{code}", "password": a.password}).json()["access_token"]
    sh = {"Authorization": f"Bearer {tok}"}
    for it in o["items"]:
        c.post(f"/api/staff/order-items/{it['id']}/start", headers=sh)
        c.post(f"/api/staff/order-items/{it['id']}/done", headers=sh)
    r = c.post(f"/api/staff/orders/{o['order_id']}/complete", headers=sh)
    me = c.get("/api/public/me", headers=h).json()
    tx = me["recent_transactions"][0] if me["recent_transactions"] else {}
    check("SM-31", "Đã giao -> cộng điểm, /me có giao dịch của đơn", r.status_code == 200
          and r.json()["points_earned"] == expected and me["loyalty_points"] == expected
          and tx.get("order_code") == o["order_code"], f"+{expected} điểm, tổng {me['loyalty_points']}")


def smoke_support(c: httpx.Client, a, bid: int, code: str, lines: list[dict]) -> None:
    """F5: thu ngân tra cứu đơn của khách, hủy & hoàn tiền giả lập; khách và màn hình Bar nhận sự kiện realtime."""
    body = {"qr_token": a.qr_token, "items": [{"menu_item_id": lines[0]["id"], "quantity": 1}]}
    o = c.post("/api/public/orders", json=body).json()
    c.post(f"/api/public/orders/{o['order_id']}/pay", json={"access_token": o["access_token"], "method": "MOCK_EWALLET"})
    r = c.post("/api/auth/login", json={"username": f"tn_{code}", "password": a.password})
    if r.status_code != 200:
        check("SM-32", f"Đăng nhập thu ngân tn_{code}", False, str(r.status_code))
        return
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    found = c.get("/api/staff/orders/search", params={"code": o["order_code"]}, headers=h).json()
    check("SM-32", "Thu ngân tra cứu đơn theo mã: thấy đơn PAID, được phép hủy", len(found) == 1
          and found[0]["status"] == "PAID" and found[0]["can_cancel"], o["order_code"])

    pc = c.post("/api/auth/login", json={"username": f"pc1_{code}", "password": a.password}).json()["access_token"]
    r = c.post(f"/api/staff/orders/{o['order_id']}/cancel", json={"reason": "Khách đổi ý"},
               headers={"Authorization": f"Bearer {pc}"})
    check("SM-33", "Pha chế không được hủy đơn (403)", r.status_code == 403)

    base_ws = a.base_url.replace("http", "ws", 1)
    with ws_connect(f"{base_ws}/ws/bar/{bid}?token={pc}", open_timeout=5) as bar_ws,             ws_connect(f"{base_ws}/ws/order/{o['order_id']}?token={o['access_token']}", open_timeout=5) as cust_ws:
        recv_until(cust_ws, "ORDER_SNAPSHOT")
        t0 = time.perf_counter()
        r = c.post(f"/api/staff/orders/{o['order_id']}/cancel", json={"reason": "Khách đổi ý"}, headers=h)
        evt = recv_until(cust_ws, "ORDER_CANCELLED")
        ms = (time.perf_counter() - t0) * 1000
        check("SM-34", "Hủy & hoàn tiền -> khách nhận 'Đơn đã hủy' kèm lý do ≤ 2 giây", r.status_code == 200
              and r.json()["payment"]["status"] == "REFUNDED" and evt["data"]["cancel_reason"] == "Khách đổi ý"
              and ms <= 2000, f"{ms:.0f} ms")
        b = recv_until(bar_ws, "ORDER_CANCELLED")
        check("SM-35", "Màn hình Bar nhận ORDER_CANCELLED", b["data"]["order_id"] == o["order_id"])
    q = c.get(f"/api/staff/branches/{bid}/queue", headers={"Authorization": f"Bearer {pc}"}).json()["items"]
    check("SM-36", "Món của đơn đã hủy rời hàng đợi Bar", all(i["order_id"] != o["order_id"] for i in q))
    r = c.post(f"/api/staff/orders/{o['order_id']}/cancel", json={"reason": "Khách đổi ý"}, headers=h)
    check("SM-37", "Hủy lần 2 -> 409 CANNOT_CANCEL", r.status_code == 409 and r.json()["error"]["code"] == "CANNOT_CANCEL")


if __name__ == "__main__":
    sys.exit(main())
