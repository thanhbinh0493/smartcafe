"""F4 – UC07 xem điểm; đặt món ở chế độ thành viên (UC05 bước 3) và cộng điểm đầu-cuối (UC19, D11, D15)."""
from datetime import timedelta

from sqlalchemy import func, select

from app.core.security import create_customer_token, create_staff_token, decode_token
from app.models import Customer, LoyaltyTransaction, Order
from tests import factories as f
from tests.f2.conftest import order_body
from tests.f3.conftest import complete, make_ready, view
from tests.f4.conftest import PHONE, bearer, expired_customer_token, login


def place(client, table, *lines, token: str | None = None):
    return client.post("/api/public/orders", json=order_body(table, *lines), headers=bearer(token) if token else {})


def pay(client, o: dict) -> None:
    r = client.post(f"/api/public/orders/{o['order_id']}/pay", json={"access_token": o["access_token"], "method": "MOCK_CARD"})
    assert r.status_code == 200, r.text


def test_F4_25_xem_diem_va_lich_su(client, db, clock, shop):
    tok = login(client)["customer_token"]
    cust = db.scalar(select(Customer).where(Customer.phone == PHONE))
    r = client.get("/api/public/me", headers=bearer(tok))
    assert r.status_code == 200
    assert r.json() == {"phone_masked": "0912 *** 678", "loyalty_points": 0, "point_value_vnd": 100,
                        "points_value": 0, "recent_transactions": []}

    # 7 giao dịch: chỉ trả 5 giao dịch gần nhất, mới nhất trước
    for i in range(7):
        o = place(client, shop.t_cg, (shop.sua_da, i + 1), token=tok).json()
        pay(client, o)
        make_ready(client, shop.pc, o)
        assert complete(client, shop.pc, o["order_id"]).status_code == 200
        tx = db.scalar(select(LoyaltyTransaction).where(LoyaltyTransaction.order_id == o["order_id"]))
        tx.created_at = tx.created_at + timedelta(seconds=i)  # cùng transaction test: now() giống nhau
    db.flush()
    me = client.get("/api/public/me", headers=bearer(tok)).json()
    total = sum((29000 * (i + 1)) // 10000 for i in range(7))  # 2+5+8+11+14+17+20 = 77
    assert me["loyalty_points"] == total and me["points_value"] == total * 100
    txs = me["recent_transactions"]
    assert len(txs) == 5
    assert [t["points"] for t in txs] == [20, 17, 14, 11, 8]
    assert all(t["type"] == "EARN" and t["order_code"].startswith("CG-") for t in txs)
    db.refresh(cust)
    assert cust.loyalty_points == total


def test_F4_26_xem_diem_can_customer_token(client, db, clock):
    cust = f.customer(db)
    staff = f.staff(db, "adm", "ADMIN")
    cases = [
        ({}, "UNAUTHORIZED"),
        (bearer("rac"), "UNAUTHORIZED"),
        (bearer(expired_customer_token(cust.id)), "TOKEN_EXPIRED"),
        (bearer(create_staff_token(staff.id, "ADMIN", None)), "UNAUTHORIZED"),  # token nhân viên không dùng thay được
        (bearer(create_customer_token(999_999)[0]), "UNAUTHORIZED"),             # khách không tồn tại
    ]
    for headers, code in cases:
        r = client.get("/api/public/me", headers=headers)
        assert r.status_code == 401 and r.json()["error"]["code"] == code, (headers, r.text)


def test_F4_27_customer_token_khong_goi_duoc_api_nhan_vien(client, db, clock, shop):
    tok = login(client)["customer_token"]
    for url in ("/api/auth/me", f"/api/staff/branches/{shop.cg.id}/queue"):
        r = client.get(url, headers=bearer(tok))
        assert r.status_code == 403 and r.json()["error"]["code"] == "FORBIDDEN", url


def test_F4_28_dat_mon_che_do_thanh_vien(client, db, clock, shop):
    tok = login(client)["customer_token"]
    cust_id = int(decode_token(tok)["sub"])
    r = place(client, shop.t_cg, (shop.sua_da, 2), (shop.tra_dao, 1), token=tok)  # 58.000 + 36.000 = 94.000đ
    assert r.status_code == 201
    o = r.json()
    assert o["expected_points"] == 9
    assert db.get(Order, o["order_id"]).customer_id == cust_id
    v = view(client, o)
    assert v["expected_points"] == 9 and v["points_earned"] is None


def test_F4_29_don_an_danh_khong_gan_khach(client, db, clock, shop):
    login(client)  # đã có khách trong CSDL nhưng không gửi token
    o = place(client, shop.t_cg, (shop.sua_da, 1)).json()
    assert o["expected_points"] is None and db.get(Order, o["order_id"]).customer_id is None
    assert view(client, o)["expected_points"] is None


def test_F4_30_token_het_han_hoac_sai_thi_khong_tao_don(client, db, clock, shop):
    cust = f.customer(db)
    staff_tok = create_staff_token(shop.pc.id, "BARISTA", shop.cg.id)
    for tok, code in ((expired_customer_token(cust.id), "TOKEN_EXPIRED"), (staff_tok, "UNAUTHORIZED"), ("rac", "UNAUTHORIZED")):
        r = place(client, shop.t_cg, (shop.sua_da, 1), token=tok)
        assert r.status_code == 401 and r.json()["error"]["code"] == code
    # Không âm thầm tạo đơn ẩn danh khi phiên thành viên đã hết (khách sẽ mất điểm)
    assert db.scalar(select(func.count()).select_from(Order)) == 0


def test_F4_31_dau_cuoi_otp_dat_mon_giao_do_cong_diem(client, db, clock, shop):
    """Luồng demo thành viên: OTP → đặt món → thanh toán → pha chế → Đã giao → điểm hiện ở /me và trang theo dõi."""
    f.customer(db, PHONE, points=120)
    login_body = login(client)
    assert login_body["loyalty_points"] == 120
    tok = login_body["customer_token"]

    o = place(client, shop.t_cg, (shop.sua_da, 2), (shop.tra_dao, 1), token=tok).json()
    pay(client, o)
    make_ready(client, shop.pc, o)
    assert complete(client, shop.pc, o["order_id"]).json()["points_earned"] == 9
    assert view(client, o)["points_earned"] == 9

    me = client.get("/api/public/me", headers=bearer(tok)).json()
    assert me["loyalty_points"] == 129 and me["points_value"] == 12_900
    assert me["recent_transactions"][0] == {**me["recent_transactions"][0], "order_code": o["order_code"], "points": 9}
    # Gọi "Đã giao" lần 2 không cộng thêm điểm (NFR-R4)
    assert complete(client, shop.pc, o["order_id"]).status_code == 409
    assert client.get("/api/public/me", headers=bearer(tok)).json()["loyalty_points"] == 129


def test_F4_32_het_phien_van_cong_diem_don_da_dat(client, db, clock, shop):
    """UC06: đơn đặt khi còn phiên vẫn được cộng điểm dù token đã hết hạn lúc giao đồ."""
    tok = login(client)["customer_token"]
    cust_id = int(decode_token(tok)["sub"])
    o = place(client, shop.t_cg, (shop.tra_dao, 3), token=tok).json()  # 108.000đ
    pay(client, o)
    # ... 1 giờ sau token hết hạn, khách vẫn xem đơn bằng access_token và vẫn được cộng điểm
    make_ready(client, shop.pc, o)
    assert complete(client, shop.pc, o["order_id"]).json()["points_earned"] == 10
    assert client.get("/api/public/me", headers=bearer(expired_customer_token(cust_id))).status_code == 401
    assert db.get(Customer, cust_id).loyalty_points == 10
