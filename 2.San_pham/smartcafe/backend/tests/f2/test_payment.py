"""F2 – UC05: thanh toán giả lập (SD03 bước 10–17)."""
from sqlalchemy import select

from app.main import app
from app.models import Order, OrderStatusHistory, Payment
from app.modules.payment.gateway import ChargeResult, MockPaymentGateway, get_payment_gateway
from tests import factories as f
from tests.f2.conftest import place


def pay(client, o, method="MOCK_EWALLET", token=None):
    return client.post(f"/api/public/orders/{o['order_id']}/pay",
                       json={"access_token": token or o["access_token"], "method": method})


def test_F2_15_thanh_toan_thanh_cong(client, db, shop):
    o = place(client, shop.t_cg, (shop.sua_da, 2), (shop.tra_dao, 1)).json()
    r = pay(client, o, "MOCK_CARD")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "PAID" and body["paid_at"] and body["transaction_ref"].startswith("MOCK-")
    order = db.get(Order, o["order_id"])
    db.refresh(order)
    assert order.status == "PAID" and order.paid_at is not None
    p = db.scalar(select(Payment).where(Payment.order_id == order.id))
    assert (p.status, p.amount, p.method) == ("SUCCESS", 94000, "MOCK_CARD")
    hist = db.scalars(select(OrderStatusHistory.to_status).where(OrderStatusHistory.order_id == order.id)
                      .order_by(OrderStatusHistory.id)).all()
    assert hist == ["PENDING_PAYMENT", "PAID"]


def test_F2_16_thanh_toan_that_bai_so_tien_duoi_999(client, db, shop):
    """II.2: Mock Payment trả FAILED khi số tiền kết thúc bằng 999. Đơn giữ PENDING_PAYMENT (UC05 – 5a)."""
    cat = f.category(db, "Test", 9)
    odd = f.item(db, cat, "Mon gia le", 29999)
    o = place(client, shop.t_cg, (odd, 1)).json()
    r = pay(client, o)
    assert r.status_code == 402 and r.json()["error"]["code"] == "PAYMENT_FAILED"
    order = db.get(Order, o["order_id"])
    db.refresh(order)
    assert order.status == "PENDING_PAYMENT" and order.paid_at is None
    assert db.scalar(select(Payment.status).where(Payment.order_id == order.id)) == "FAILED"


class FlakyGateway(MockPaymentGateway):
    """Lần 1 thất bại, lần 2 thành công."""

    def __init__(self):
        self.calls = 0

    def charge(self, amount, method, order_code):
        self.calls += 1
        return ChargeResult(self.calls > 1, f"FLAKY-{self.calls}")


def test_F2_17_thu_lai_sau_khi_that_bai(client, db, shop):
    gw = FlakyGateway()
    app.dependency_overrides[get_payment_gateway] = lambda: gw
    o = place(client, shop.t_cg, (shop.sua_da, 1)).json()
    assert pay(client, o).status_code == 402
    r = pay(client, o)
    assert r.status_code == 200 and r.json()["transaction_ref"] == "FLAKY-2"
    rows = db.scalars(select(Payment).where(Payment.order_id == o["order_id"])).all()
    assert len(rows) == 1 and rows[0].status == "SUCCESS" and rows[0].transaction_ref == "FLAKY-2"


def test_F2_18_khong_thanh_toan_hai_lan(client, db, shop):
    o = place(client, shop.t_cg, (shop.sua_da, 1)).json()
    assert pay(client, o).status_code == 200
    r = pay(client, o)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "INVALID_STATE_TRANSITION"
    assert r.json()["error"]["message"] == "Đơn đã được thanh toán"


def test_F2_19_sai_access_token(client, db, shop):
    o = place(client, shop.t_cg, (shop.sua_da, 1)).json()
    r = pay(client, o, token="token-doan-mo")
    assert r.status_code == 404 and r.json()["error"]["code"] == "ORDER_NOT_FOUND"
    assert client.get(f"/api/public/orders/{o['order_id']}", params={"token": "x"}).status_code == 404
    assert client.get(f"/api/public/orders/999999", params={"token": o["access_token"]}).status_code == 404


def test_F2_20_phuong_thuc_khong_hop_le(client, db, shop):
    o = place(client, shop.t_cg, (shop.sua_da, 1)).json()
    r = pay(client, o, method="TIEN_MAT")
    assert r.status_code == 422


def test_F2_21_mock_gateway_quy_tac_999():
    gw = MockPaymentGateway()
    assert gw.charge(94000, "MOCK_EWALLET", "CG-0001").success
    assert gw.charge(1000, "MOCK_CARD", "CG-0001").success
    assert not gw.charge(29999, "MOCK_EWALLET", "CG-0001").success
    assert not gw.charge(999, "MOCK_EWALLET", "CG-0001").success
    refs = {gw.charge(1000, "MOCK_CARD", "x").transaction_ref for _ in range(50)}
    assert len(refs) == 50
    assert gw.refund("MOCK-1", 1000).success
