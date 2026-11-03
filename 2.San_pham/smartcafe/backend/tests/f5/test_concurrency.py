"""F5 – Hủy đơn đồng thời với thao tác của pha chế / thu ngân khác (mỗi bên một kết nối CSDL thật).
Kết quả luôn nhất quán: hoặc đơn bị hủy (mọi món CANCELLED, đã hoàn tiền), hoặc pha chế thắng (đơn READY,
thanh toán giữ nguyên). Hoàn tiền chỉ gọi cổng thanh toán đúng 1 lần."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Order, OrderItem, Payment, Staff
from app.modules.bar import service as bar
from app.modules.order.schemas import CreateOrderRequest, OrderItemIn
from app.modules.order.service import create_order, pay_order
from app.modules.payment.gateway import ChargeResult, MockPaymentGateway
from app.modules.support import service as support
from tests import factories as f

ROUNDS = 5


class CountingGateway(MockPaymentGateway):
    def __init__(self):
        self.refunds = 0

    def refund(self, ref, amount):
        self.refunds += 1
        return ChargeResult(True, ref)


@pytest.fixture
def setup(engine):
    with Session(engine) as s:
        b = f.branch(s, "CC")
        qr = f.table(s, b, "01").qr_token
        menu_id = f.item(s, f.category(s, "Conc", 1), "Mon", 30000).id
        ids = {r: f.staff(s, u, r, b).id for u, r in (("pc", "BARISTA"), ("tn", "CASHIER"), ("ql", "MANAGER"))}
        s.commit()

    def new_order(started: bool) -> tuple[int, int]:
        with Session(engine) as s:
            res = create_order(s, CreateOrderRequest(qr_token=qr, items=[OrderItemIn(menu_item_id=menu_id, quantity=1)]))
            pay_order(s, res.order_id, res.access_token, "MOCK_CARD", MockPaymentGateway())
            s.commit()
            if started:
                bar.start_item(s, res.items[0].id, s.get(Staff, ids["BARISTA"]))
                s.commit()
            return res.order_id, res.items[0].id

    yield new_order, ids
    with engine.begin() as c:
        c.execute(text("TRUNCATE order_status_history, order_items, payments, orders, staff, dining_tables, "
                       "menu_items, categories, branches RESTART IDENTITY CASCADE"))


def parallel(engine, calls):
    barrier = Barrier(len(calls))

    def worker(call):
        fn, staff_id = call
        with Session(engine) as s:
            staff = s.get(Staff, staff_id)
            barrier.wait()
            try:
                fn(s, staff)
                s.commit()
                return "ok"
            except AppError as e:
                s.rollback()
                return e.code

    with ThreadPoolExecutor(len(calls)) as pool:
        return list(pool.map(worker, calls))


def snapshot(engine, order_id):
    with Session(engine) as s:
        o = s.get(Order, order_id)
        items = s.scalars(select(OrderItem.status).where(OrderItem.order_id == order_id)).all()
        pay = s.scalar(select(Payment.status).where(Payment.order_id == order_id))
        return o.status, list(items), pay


def test_F5_17_huy_va_xong_mon_cuoi_cung_luc(engine, setup):
    new_order, ids = setup
    outcomes = set()
    for _ in range(ROUNDS):
        order_id, item_id = new_order(started=True)
        gw = CountingGateway()
        res = parallel(engine, [
            (lambda s, st: support.cancel_order(s, order_id, "Khách đổi ý", st, gw), ids["CASHIER"]),
            (lambda s, st: bar.done_item(s, item_id, st), ids["BARISTA"]),
        ])
        snap = snapshot(engine, order_id)
        if res == ["ok", "INVALID_STATE_TRANSITION"]:     # thu ngân thắng
            assert snap == ("CANCELLED", ["CANCELLED"], "REFUNDED") and gw.refunds == 1
        elif res == ["CANNOT_CANCEL", "ok"]:               # pha chế thắng: đơn đã "Có thể lấy"
            assert snap == ("READY", ["DONE"], "SUCCESS") and gw.refunds == 0
        else:
            pytest.fail(f"kết quả không nhất quán: {res} {snap}")
        outcomes.add(tuple(res))
    assert outcomes  # mỗi vòng đều nhất quán (thứ tự thắng tùy lịch của CSDL)


def test_F5_18_hai_thu_ngan_cung_huy_chi_hoan_tien_1_lan(engine, setup):
    new_order, ids = setup
    order_id, _ = new_order(started=False)
    gw = CountingGateway()
    res = parallel(engine, [
        (lambda s, st: support.cancel_order(s, order_id, "Khách đổi ý", st, gw), ids["CASHIER"]),
        (lambda s, st: support.cancel_order(s, order_id, "Khách đổi ý", st, gw), ids["MANAGER"]),
    ])
    assert sorted(res) == ["CANNOT_CANCEL", "ok"]
    assert gw.refunds == 1
    assert snapshot(engine, order_id) == ("CANCELLED", ["CANCELLED"], "REFUNDED")
