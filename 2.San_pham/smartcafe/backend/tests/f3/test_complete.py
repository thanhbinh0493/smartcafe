"""F3 – UC19: pha chế giao đồ, bấm "Đã giao" → COMPLETED; cộng điểm khách thành viên (D11, D15)."""
from sqlalchemy import func, select

from app.models import Customer, LoyaltyTransaction, Order
from tests import factories as f
from tests.f2.conftest import place_and_pay
from tests.f3.conftest import complete, make_ready, ready, view


def as_member(db, o, customer) -> None:
    """F4 mới có OTP; ở đây gắn khách thành viên trực tiếp vào đơn."""
    db.get(Order, o["order_id"]).customer_id = customer.id
    db.flush()


def test_F3_17_da_giao_don_an_danh(client, db, bar):
    o = place_and_pay(client, bar.t_cg, (bar.sua_da, 2, "ít đường"), (bar.tra_dao, 1))
    make_ready(client, bar.pc, o)
    r = complete(client, bar.pc, o["order_id"])
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "COMPLETED" and body["completed_at"] and body["points_earned"] is None
    order = db.get(Order, o["order_id"])
    assert order.completed_by == bar.pc.id
    assert ready(client, bar.pc, bar.cg) == []
    v = view(client, o)
    assert v["status"] == "COMPLETED" and v["completed_at"] and v["points_earned"] is None
    assert db.scalar(select(func.count()).select_from(LoyaltyTransaction)) == 0


def test_F3_18_cong_diem_khach_thanh_vien(client, db, bar):
    cust = f.customer(db, points=5)
    o = place_and_pay(client, bar.t_cg, (bar.sua_da, 2), (bar.tra_dao, 1))  # 58.000 + 36.000 (giá KM) = 94.000đ
    as_member(db, o, cust)
    assert view(client, o)["points_earned"] is None  # chưa giao: chưa cộng điểm
    make_ready(client, bar.pc, o)
    assert ready(client, bar.pc, bar.cg)[0]["is_member"] is True
    assert complete(client, bar.pc, o["order_id"]).json()["points_earned"] == 9  # floor(94.000 / 10.000)
    db.refresh(cust)
    assert cust.loyalty_points == 14
    tx = db.scalar(select(LoyaltyTransaction).where(LoyaltyTransaction.order_id == o["order_id"]))
    assert (tx.customer_id, tx.points, tx.type) == (cust.id, 9, "EARN")
    assert view(client, o)["points_earned"] == 9


def test_F3_19_da_giao_hai_lan_khong_cong_diem_hai_lan(client, db, bar):
    cust = f.customer(db)
    o = place_and_pay(client, bar.t_cg, (bar.tra_dao, 1))
    as_member(db, o, cust)
    make_ready(client, bar.pc, o)
    assert complete(client, bar.pc, o["order_id"]).status_code == 200
    r = complete(client, bar.pc2, o["order_id"])
    assert r.status_code == 409 and r.json()["error"]["code"] == "INVALID_STATE_TRANSITION"
    db.refresh(cust)
    assert cust.loyalty_points == 3
    assert db.scalar(select(func.count()).select_from(LoyaltyTransaction)) == 1


def test_F3_20_don_duoi_10000d_khong_phat_sinh_giao_dich_diem(client, db, bar):
    cheap = f.item(db, f.category(db, "Topping", 9), "Them shot", 9000)
    cust = f.customer(db)
    o = place_and_pay(client, bar.t_cg, (cheap, 1))
    as_member(db, o, cust)
    make_ready(client, bar.pc, o)
    assert complete(client, bar.pc, o["order_id"]).json()["points_earned"] == 0
    assert db.scalar(select(func.count()).select_from(LoyaltyTransaction)) == 0
    assert db.get(Customer, cust.id).loyalty_points == 0
    assert view(client, o)["points_earned"] == 0


def test_F3_21_chi_don_co_the_lay_moi_bam_da_giao(client, db, bar):
    o = place_and_pay(client, bar.t_cg, (bar.sua_da, 1))
    r = complete(client, bar.pc, o["order_id"])
    assert r.status_code == 409 and r.json()["error"]["details"]["order_status"] == "PAID"
    make_ready(client, bar.pc, o)
    assert complete(client, bar.tn, o["order_id"]).status_code == 403      # thu ngân không bấm "Đã giao"
    assert complete(client, bar.pc_hd, o["order_id"]).status_code == 403   # chi nhánh khác
    assert complete(client, bar.ql, o["order_id"]).status_code == 200
