# -*- coding: utf-8 -*-
"""Kiểm thử bảo mật (NFR-S1..S7) trên hệ thống chạy bằng docker compose: tấn công thử qua Nginx như người ngoài,
kiểm tra dữ liệu lưu trong CSDL bằng psql.

    .venv\\Scripts\\python st_bao_mat.py
"""
from __future__ import annotations

import base64
import json
import re

import httpx
from websockets.exceptions import ConnectionClosed, InvalidStatus
from websockets.sync.client import connect as ws_connect

from common import DEMO_PHONE, Report, args, branches, login, member_login, menu, place_order, random_phone, sql, \
    tables

rep = Report()


def claims(header: dict) -> dict:
    tok = header["Authorization"].split()[1]
    part = tok.split(".")[1]
    return json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))


def b64(obj: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(obj).encode()).decode().rstrip("=")


def ws_close_code(url: str) -> int | str | None:
    try:
        with ws_connect(url, open_timeout=5) as ws:
            ws.recv(timeout=3)
            return None                         # vẫn nhận được dữ liệu → không bị chặn
    except ConnectionClosed as e:
        return e.rcvd.code if e.rcvd else None
    except InvalidStatus as e:                  # từ chối ngay ở bước bắt tay (VD thiếu tham số token)
        return f"HTTP {e.response.status_code}"
    except TimeoutError:
        return None


def main() -> int:
    a = args()
    c = httpx.Client(base_url=a.base_url, timeout=15)
    admin = login(c, "admin")
    bs = branches(c, admin)
    cg, hd = bs["CG"], bs["HD"]
    qr = tables(c, admin, cg["id"])[0]["qr_token"]
    m = menu(c, cg["id"])
    pc_cg, tn_cg, ql_cg = login(c, "pc1_cg"), login(c, "tn_cg"), login(c, "ql_cg")

    # ---- NFR-S1: bcrypt ----
    rows = sql("SELECT username, password_hash FROM staff")
    costs = {u: int(h.split("$")[2]) if re.fullmatch(r"\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}", h) else 0 for u, h in rows}
    rep.check("ST-40", "NFR-S1: mật khẩu mọi nhân viên lưu dạng băm bcrypt, cost ≥ 10, không có mật khẩu rõ",
              rows and all(v >= 10 for v in costs.values()) and not any("smartcafe123" in h for _, h in rows),
              f"{len(rows)} tài khoản, cost {sorted(set(costs.values()))}")

    # ---- NFR-S2: JWT + RBAC ----
    st, cu = claims(pc_cg), claims(member_login(c, random_phone()))
    rep.check("ST-41", "NFR-S2: JWT nhân viên hết hạn sau 8 giờ; JWT khách thành viên (role CUSTOMER) sau 1 giờ",
              st["exp"] - st["iat"] == 8 * 3600 and cu["exp"] - cu["iat"] == 3600 and cu["role"] == "CUSTOMER",
              f"nhân viên {(st['exp'] - st['iat']) / 3600:g} giờ, khách {(cu['exp'] - cu['iat']) / 60:g} phút")

    staff_get = ["/api/auth/me", f"/api/staff/branches/{cg['id']}/queue", "/api/staff/orders/search?code=CG",
                 "/api/staff/reports/daily", "/api/staff/staff", "/api/staff/categories"]
    real = pc_cg["Authorization"].split()[1]
    h, p, s = real.split(".")
    forged = {
        "không có token": {},
        "token rác": {"Authorization": "Bearer abc.def.ghi"},
        "sửa role=ADMIN, giữ chữ ký cũ": {"Authorization": f"Bearer {h}.{b64({**st, 'role': 'ADMIN', 'branch_id': None})}.{s}"},
        "alg=none": {"Authorization": f"Bearer {b64({'alg': 'none', 'typ': 'JWT'})}.{b64({**st, 'role': 'ADMIN'})}."},
    }
    bad = [(k, u, c.get(u, headers=hd_).status_code) for k, hd_ in forged.items() for u in staff_get]
    rep.check("ST-42", "NFR-S2: API nhân viên từ chối (401) khi không có token / token rác / sửa payload / alg=none",
              all(code == 401 for *_, code in bad), f"{len(bad)} lần thử, mã trả về {sorted({x[2] for x in bad})}")

    cust = member_login(c, random_phone())
    got = [c.get(u, headers=cust).status_code for u in staff_get]
    rep.check("ST-43", "NFR-S2: token khách thành viên không gọi được API nhân viên",
              all(code in (401, 403) for code in got), f"mã trả về {sorted(set(got))}")

    matrix = [  # (vai trò, token, method, url, body) → phải bị chặn 403
        ("Pha chế", pc_cg, "GET", "/api/staff/reports/daily", None),
        ("Pha chế", pc_cg, "GET", "/api/staff/staff", None),
        ("Pha chế", pc_cg, "POST", "/api/staff/categories", {"name": "X"}),
        ("Pha chế", pc_cg, "POST", f"/api/staff/orders/1/cancel", {"reason": "x"}),
        ("Thu ngân", tn_cg, "POST", "/api/staff/order-items/1/start", None),
        ("Thu ngân", tn_cg, "GET", "/api/staff/reports/daily", None),
        ("Quản lý CG", ql_cg, "POST", "/api/staff/promotions", {"name": "X"}),
        ("Quản lý CG", ql_cg, "POST", "/api/staff/menu-items", {"category_id": 1, "name": "X", "base_price": 1}),
        ("Quản lý CG", ql_cg, "GET", f"/api/staff/branches/{hd['id']}/queue", None),
        ("Quản lý CG", ql_cg, "GET", f"/api/staff/branches/{hd['id']}/menu", None),
        ("Quản lý CG", ql_cg, "GET", f"/api/staff/reports/daily?branch_id={hd['id']}", None),
        ("Pha chế CG", pc_cg, "GET", f"/api/staff/branches/{hd['id']}/queue", None),
    ]
    res = [(role, url, c.request(meth, url, headers=tok, json=body).status_code) for role, tok, meth, url, body in matrix]
    leak = [x for x in res if x[2] != 403]
    rep.check("ST-44", "NFR-S2: ma trận RBAC – sai vai trò hoặc khác chi nhánh bị chặn 403 (12 thao tác)", not leak,
              f"lọt: {leak}" if leak else "12/12 bị chặn")

    o = place_order(c, qr, [(m["Cà phê sữa đá"], 1)])
    base_ws = a.base_url.replace("http", "ws", 1)
    codes = {
        "Bar không token": ws_close_code(f"{base_ws}/ws/bar/{cg['id']}"),
        "Bar token rác": ws_close_code(f"{base_ws}/ws/bar/{cg['id']}?token=abc"),
        "Pha chế CG vào Bar HD": ws_close_code(f"{base_ws}/ws/bar/{hd['id']}?token={real}"),
        "Đơn sai access_token": ws_close_code(f"{base_ws}/ws/order/{o['order_id']}?token=doan-bua"),
    }
    rep.check("ST-45", "NFR-S2: WebSocket Bar / theo dõi đơn từ chối kết nối trái phép (mã đóng 4401 / 4403 / 4404 tới được client – hồi quy BUG-ST-01)",
              list(codes.values()) == [4401, 4401, 4403, 4404], dump_codes(codes))

    # ---- NFR-S3: token ngẫu nhiên, không đoán được ID ----
    qrs = [r[0] for r in sql("SELECT qr_token FROM dining_tables")]
    acc = [r[0] for r in sql("SELECT access_token FROM orders WHERE created_at > now() - interval '1 day'")]
    short = [t for t in qrs + acc if len(t) < 22 or not re.fullmatch(r"[A-Za-z0-9_-]+", t)]
    rep.check("ST-46", "NFR-S3: qr_token bàn & access_token đơn ≥ 128 bit (≥ 22 ký tự token_urlsafe), không trùng",
              not short and len(set(qrs)) == len(qrs) and len(set(acc)) == len(acc),
              f"{len(qrs)} QR, {len(acc)} đơn hôm nay, độ dài nhỏ nhất {min(map(len, qrs + acc))}")
    other = place_order(c, qr, [(m["Trà đào cam sả"], 1)], pay=False)
    idor = [c.get(f"/api/public/orders/{oid}", params={"token": o["access_token"]}).status_code
            for oid in (other["order_id"], o["order_id"] - 1, o["order_id"] + 1)]
    pay_other = c.post(f"/api/public/orders/{other['order_id']}/pay", json={"access_token": o["access_token"], "method": "MOCK_CARD"})
    rep.check("ST-47", "NFR-S3: đổi ID đơn trên URL (đơn của người khác) với access_token của mình → không xem / không trả hộ được",
              all(x == 404 for x in idor) and pay_other.status_code == 404, f"xem: {idor}, thanh toán: {pay_other.status_code}")

    # ---- NFR-S4: OTP ----
    ph = random_phone()
    r1 = c.post("/api/public/otp/request", json={"phone": ph})
    stored = sql(f"SELECT code_hash FROM otp_requests WHERE phone = '{ph}'")
    rep.check("ST-48", "NFR-S4: OTP 6 số, chỉ lưu dạng băm (HMAC-SHA256), hết hạn 5 phút",
              r1.status_code == 200 and re.fullmatch(r"\d{6}", r1.json()["demo_code"]) and len(stored) == 1
              and re.fullmatch(r"[0-9a-f]{64}", stored[0][0]) and r1.json()["demo_code"] not in stored[0][0]
              and r1.json()["expires_in"] == 300, f"lưu: {stored[0][0][:12]}…")
    again = c.post("/api/public/otp/request", json={"phone": ph})
    wrong = [c.post("/api/public/otp/verify", json={"phone": ph, "code": f"{(int(r1.json()['demo_code']) + k) % 10**6:06d}"})
             for k in range(1, 6)]
    right = c.post("/api/public/otp/verify", json={"phone": ph, "code": r1.json()["demo_code"]})
    rep.check("ST-49", "NFR-S4: gửi lại trong 60 giây bị chặn (429); sai 5 lần thì mã bị hủy, nhập đúng cũng không vào được",
              again.status_code == 429 and [w.json()["error"]["details"]["attempts_left"] for w in wrong] == [4, 3, 2, 1, 0]
              and right.status_code == 400 and right.json()["error"]["details"]["reason"] == "LOCKED",
              f"gửi lại: {again.status_code}; còn lại: {[w.json()['error']['details']['attempts_left'] for w in wrong]}; "
              f"mã đúng: {right.json()['error']['details']['reason']}")
    new_ph = random_phone()
    shapes = []
    member_ph = sql(f"SELECT phone FROM customers WHERE phone <> '{DEMO_PHONE}' ORDER BY id LIMIT 1")[0][0]  # thành viên có sẵn
    for phone in (member_ph, new_ph):
        r = c.post("/api/public/otp/request", json={"phone": phone})
        if r.status_code == 429:                       # SĐT demo vừa được dùng < 60 giây: bỏ qua, so khóa của lỗi
            shapes.append(("429",))
        else:
            shapes.append(tuple(sorted(r.json())) + (r.json()["expires_in"], r.json()["resend_after"]))
    rep.check("ST-50", "NFR-S4: phản hồi gửi OTP giống hệt nhau giữa SĐT đã là thành viên và SĐT mới (không lộ thành viên)",
              shapes[0] == shapes[1] or shapes[0] == ("429",), f"thành viên {shapes[0]} | mới {shapes[1]}")

    # ---- NFR-S5: đầu vào ----
    probes = ["' OR '1'='1", "1; DROP TABLE orders;--", "CG-0001' UNION SELECT password_hash FROM staff--", "%' --"]
    resp = []
    for pr in probes:
        resp.append(c.get("/api/staff/orders/search", params={"code": pr}, headers=tn_cg))
        resp.append(c.get("/api/staff/orders/search", params={"table": pr[:10]}, headers=tn_cg))
        resp.append(c.get(f"/api/public/tables/{pr}"))
        resp.append(c.post("/api/public/otp/request", json={"phone": pr}))
        resp.append(c.post("/api/auth/login", json={"username": pr, "password": pr}))
    leaked = [r for r in resp if r.status_code >= 500 or "$2b$" in r.text or (r.status_code == 200 and r.json())]
    intact = sql("SELECT count(*) FROM orders")[0][0]
    rep.check("ST-51", "NFR-S5: thử SQL injection ở tìm kiếm đơn, mã QR, SĐT, đăng nhập → không lỗi 500, không lộ dữ liệu, CSDL nguyên vẹn",
              not leaked and int(intact) > 5000, f"{len(resp)} request, mã trả về {sorted({r.status_code for r in resp})}, "
              f"bảng orders còn {intact} dòng")
    item = m["Cà phê sữa đá"]["id"]
    bodies = {
        "số lượng 0": [{"menu_item_id": item, "quantity": 0}],
        "số lượng âm": [{"menu_item_id": item, "quantity": -3}],
        "số lượng 1000": [{"menu_item_id": item, "quantity": 1000}],
        "số lượng là chữ": [{"menu_item_id": item, "quantity": "hai"}],
        "giỏ rỗng": [],
        "món không tồn tại": [{"menu_item_id": 999999, "quantity": 1}],
        "ghi chú 5.000 ký tự": [{"menu_item_id": item, "quantity": 1, "note": "a" * 5000}],
    }
    got = {k: c.post("/api/public/orders", json={"qr_token": qr, "items": v}).status_code for k, v in bodies.items()}
    rep.check("ST-52", "NFR-S5: dữ liệu đặt món sai kiểu / ngoài giới hạn bị từ chối (4xx) có thông báo, không tạo đơn",
              all(400 <= v < 500 for v in got.values()), dump_codes(got))

    # ---- NFR-S6: giá tính ở server ----
    price = m["Cà phê sữa đá"]["sell_price"]
    cheat = c.post("/api/public/orders", json={"qr_token": qr, "expected_total": 1000, "items": [
        {"menu_item_id": item, "quantity": 2}]})
    extra = c.post("/api/public/orders", json={"qr_token": qr, "total": 1, "items": [
        {"menu_item_id": item, "quantity": 2, "unit_price": 1, "sell_price": 1, "line_total": 1}]})
    rep.check("ST-53", "NFR-S6: client gửi tổng tiền / đơn giá giả → server bỏ qua, luôn tính lại theo giá menu",
              cheat.status_code == 409 and cheat.json()["error"]["code"] == "PRICE_CHANGED"
              and extra.status_code == 201 and extra.json()["total"] == 2 * price,
              f"expected_total=1000 → {cheat.status_code} {cheat.json()['error']['code']}; "
              f"unit_price=1 → tổng {extra.json().get('total')} (đúng {2 * price})")

    # ---- NFR-S7: dữ liệu cá nhân ----
    ph = random_phone()
    req = c.post("/api/public/otp/request", json={"phone": ph})
    before = sql(f"SELECT count(*) FROM customers WHERE phone = '{ph}'")[0][0]
    ver = c.post("/api/public/otp/verify", json={"phone": ph, "code": req.json()["demo_code"]})
    after = sql(f"SELECT count(*) FROM customers WHERE phone = '{ph}'")[0][0]
    cols = [r[0] for r in sql("SELECT column_name FROM information_schema.columns WHERE table_name IN "
                              "('customers','orders','otp_requests','recommendation_logs')")]
    device = [x for x in cols if re.search(r"device|fingerprint|user_agent|ip_addr|cookie", x)]
    cookies = [r.headers.get("set-cookie") for r in (req, ver, o.get("_r", req)) if r.headers.get("set-cookie")]
    rep.check("ST-54", "NFR-S7: chỉ lưu SĐT sau khi xác thực OTP thành công; không cookie, không cột định danh thiết bị",
              before == "0" and after == "1" and not device and not cookies,
              f"trước xác thực {before} dòng, sau {after}; cột thiết bị: {device}; Set-Cookie: {cookies}")
    return rep.finish()


def dump_codes(d: dict) -> str:
    return "; ".join(f"{k}: {v}" for k, v in d.items())


if __name__ == "__main__":
    raise SystemExit(main())
