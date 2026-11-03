"""F5 – UC20: hủy đơn & hoàn tiền giả lập (SD06), quy tắc trạng thái, phân quyền, realtime."""
import pytest
from sqlalchemy import func, select

from app.main import app
from app.models import Customer, LoyaltyTransaction, Order, OrderStatusHistory, Payment
from app.modules.payment.gateway import ChargeResult, get_payment_gateway
from tests import factories as f
from tests.f2.conftest import place, place_and_pay
from tests.f3.conftest import act, complete, item_ids, make_ready, queue, token, view
from tests.f5.conftest import cancel


def state(db, o) -> tuple:
    db.expire_all()
    order = db.get(Order, o["order_id"])
    pay = db.scalar(select(Payment).where(Payment.order_id == order.id))
    return order.status, sorted(i.status for i in order.items), pay.status if pay else None


def test_F5_08_huy_don_dang_cho(client, db, sup):
    o = place_and_pay(client, sup.t_cg, (sup.sua_da, 2), (sup.tra_dao, 1))
    r = cancel(client, sup.tn, o["order_id"], "  Khách gọi nhầm món  ")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "CANCELLED" and body["can_cancel"] is False
    assert body["cancel_reason"] == "Khách gọi nhầm món"  # bỏ khoảng trắng thừa
    assert body["payment"]["status"] == "REFUNDED" and body["payment"]["refunded_at"]
    assert [i["status"] for i in body["items"]] == ["CANCELLED", "CANCELLED"]

    order = db.get(Order, o["order_id"])
    assert order.cancelled_by == sup.tn.id and order.cancelled_at is not None
    h = db.scalars(select(OrderStatusHistory).where(OrderStatusHistory.order_id == order.id)
                   .order_by(OrderStatusHistory.id)).all()[-1]
    assert (h.from_status, h.to_status, h.source, h.staff_id) == ("PAID", "CANCELLED", "STAFF", sup.tn.id)
    # Món rời hàng đợi Bar; khách thấy đơn đã hủy kèm lý do
    assert [q for q in queue(client, sup.pc, sup.cg) if q["order_id"] == o["order_id"]] == []
    v = view(client, o)
    assert v["status"] == "CANCELLED" and v["cancel_reason"] == "Khách gọi nhầm món" and v["queue_position"] is None


def test_F5_09_huy_don_dang_pha_co_mon_da_xong(client, db, sup):
    o = place_and_pay(client, sup.t_cg, (sup.sua_da, 1), (sup.tra_dao, 1))
    a, b = item_ids(o)
    act(client, sup.pc, a, "start")
    act(client, sup.pc, a, "done")
    act(client, sup.pc, b, "start")
    r = cancel(client, sup.ql, o["order_id"])  # quản lý chi nhánh cũng hủy được
    assert r.status_code == 200
    assert state(db, o) == ("CANCELLED", ["CANCELLED", "CANCELLED"], "REFUNDED")
    # Pha chế không thao tác tiếp được trên món của đơn đã hủy
    assert act(client, sup.pc, b, "done").status_code == 409


@pytest.mark.parametrize("prepare, status, msg", [
    (lambda c, s, o: None, "PENDING_PAYMENT", "tự hủy sau 15 phút"),
    (lambda c, s, o: make_ready(c, s.pc, o), "READY", "không thể hủy"),
    (lambda c, s, o: (make_ready(c, s.pc, o), complete(c, s.pc, o["order_id"])), "COMPLETED", "đã nhận đồ"),
    (lambda c, s, o: cancel(c, s.tn, o["order_id"]), "CANCELLED", "đã được hủy trước đó"),
], ids=["chua_thanh_toan", "co_the_lay", "da_giao", "da_huy"])
def test_F5_10_khong_huy_duoc_theo_trang_thai(client, db, sup, prepare, status, msg):
    if status == "PENDING_PAYMENT":
        o = place(client, sup.t_cg, (sup.sua_da, 1)).json()
    else:
        o = place_and_pay(client, sup.t_cg, (sup.sua_da, 1))
    prepare(client, sup, o)
    before = state(db, o)
    r = cancel(client, sup.tn, o["order_id"])
    assert r.status_code == 409
    err = r.json()["error"]
    assert err["code"] == "CANNOT_CANCEL" and msg in err["message"] and err["details"]["order_status"] == status
    assert state(db, o) == before


@pytest.mark.parametrize("reason", ["", "    ", "ab", "x" * 256])
def test_F5_11_ly_do_huy_bat_buoc(client, db, sup, reason):
    o = place_and_pay(client, sup.t_cg, (sup.sua_da, 1))
    r = cancel(client, sup.tn, o["order_id"], reason)
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"
    assert state(db, o) == ("PAID", ["WAITING"], "SUCCESS")


@pytest.mark.parametrize("who", ["pc", "admin", "tn_hd"])
def test_F5_12_phan_quyen_huy(client, db, sup, who):
    o = place_and_pay(client, sup.t_cg, (sup.sua_da, 1))
    r = cancel(client, getattr(sup, who), o["order_id"])
    assert r.status_code == 403 and r.json()["error"]["code"] == "FORBIDDEN"
    assert state(db, o)[0] == "PAID"


def test_F5_13_khong_ton_tai_hoac_chua_dang_nhap(client, db, sup):
    assert cancel(client, sup.tn, 999_999).json()["error"]["code"] == "ORDER_NOT_FOUND"
    o = place_and_pay(client, sup.t_cg, (sup.sua_da, 1))
    assert client.post(f"/api/staff/orders/{o['order_id']}/cancel", json={"reason": "Khách đổi ý"}).status_code == 401


def test_F5_14_cong_thanh_toan_tu_choi_hoan_tien(client, db, sup):
    calls = []

    class Failing:
        def refund(self, ref, amount):
            calls.append((ref, amount))
            return ChargeResult(False, ref, "từ chối")

    o = place_and_pay(client, sup.t_cg, (sup.tra_dao, 1))
    app.dependency_overrides[get_payment_gateway] = lambda: Failing()
    try:
        r = cancel(client, sup.tn, o["order_id"])
    finally:
        del app.dependency_overrides[get_payment_gateway]
    assert r.status_code == 502 and r.json()["error"]["code"] == "REFUND_FAILED"
    ref = db.scalar(select(Payment.transaction_ref).where(Payment.order_id == o["order_id"]))
    assert calls == [(ref, 36000)]
    assert state(db, o) == ("PAID", ["WAITING"], "SUCCESS")  # không đổi gì


def test_F5_15_huy_don_thanh_vien_khong_phat_sinh_diem(client, db, sup):
    cust = f.customer(db, points=7)
    o = place_and_pay(client, sup.t_cg, (sup.tra_dao, 3))
    db.get(Order, o["order_id"]).customer_id = cust.id
    db.flush()
    assert cancel(client, sup.tn, o["order_id"]).status_code == 200
    assert db.scalar(select(func.count()).select_from(LoyaltyTransaction)) == 0
    db.refresh(cust)
    assert cust.loyalty_points == 7
    assert view(client, o)["points_earned"] is None


def test_F5_16_realtime_bar_va_khach_nhan_su_kien_huy(client, db, sup):
    a = place_and_pay(client, sup.t_cg, (sup.sua_da, 1))
    b = place_and_pay(client, sup.t_cg2, (sup.banh, 1))
    with client.websocket_connect(f"/ws/bar/{sup.cg.id}?token={token(sup.pc)}") as bar, \
            client.websocket_connect(f"/ws/order/{a['order_id']}?token={a['access_token']}") as wa, \
            client.websocket_connect(f"/ws/order/{b['order_id']}?token={b['access_token']}") as wb:
        assert wa.receive_json()["type"] == "ORDER_SNAPSHOT"
        assert wb.receive_json()["data"]["queue_position"] == 2
        cancel(client, sup.tn, a["order_id"], "Khách phải đi gấp")
        evt = bar.receive_json()
        assert evt["type"] == "ORDER_CANCELLED" and evt["data"] == {"order_id": a["order_id"], "order_code": a["order_code"]}
        evt = wa.receive_json()
        assert evt["type"] == "ORDER_CANCELLED"
        assert evt["data"]["status"] == "CANCELLED" and evt["data"]["cancel_reason"] == "Khách phải đi gấp"
        evt = wb.receive_json()  # đơn phía sau tiến lên
        assert evt["type"] == "QUEUE_POSITION" and evt["data"] == {"order_id": b["order_id"], "queue_position": 1}
