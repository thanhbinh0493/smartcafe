"""F3 – Nhiều pha chế bấm cùng lúc (mỗi người một kết nối CSDL thật): trạng thái không bị ghi đè sai,
đơn chỉ chuyển READY / COMPLETED và chỉ cộng điểm đúng 1 lần. Dữ liệu được commit nên test tự dọn sạch."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Customer, LoyaltyTransaction, Order, OrderStatusHistory, Staff
from app.modules.bar import service
from app.modules.order.schemas import CreateOrderRequest, OrderItemIn
from app.modules.order.service import create_order, pay_order
from app.modules.payment.gateway import MockPaymentGateway
from tests import factories as f

N = 6


@pytest.fixture
def committed(engine):
    with Session(engine) as s:
        b = f.branch(s, "CC")
        qr = f.table(s, b, "01").qr_token
        cat = f.category(s, "Conc", 1)
        menu_ids = [f.item(s, cat, f"Mon {i}", 20000).id for i in range(N)]
        staff_ids = [f.staff(s, f"pc{i}", "BARISTA", b).id for i in range(N)]
        cust_id = f.customer(s, "0900000001").id
        res = create_order(s, CreateOrderRequest(
            qr_token=qr, items=[OrderItemIn(menu_item_id=m, quantity=1) for m in menu_ids]), customer_id=cust_id)
        pay_order(s, res.order_id, res.access_token, "MOCK_CARD", MockPaymentGateway())
        s.commit()
        item_ids = [i.id for i in res.items]
    yield res.order_id, item_ids, staff_ids, cust_id
    with engine.begin() as c:
        c.execute(text("TRUNCATE loyalty_transactions, customers, order_status_history, order_items, payments, orders, "
                       "staff, dining_tables, menu_items, categories, branches RESTART IDENTITY CASCADE"))


def run_parallel(engine, calls):
    """Chạy song song; mỗi lời gọi một Session riêng, cùng xuất phát qua Barrier. Trả list 'ok' | mã lỗi."""
    barrier = Barrier(len(calls))

    def worker(call):
        fn, staff_id, arg = call
        with Session(engine) as s:
            staff = s.get(Staff, staff_id)
            barrier.wait()
            try:
                fn(s, arg, staff)
                s.commit()
                return "ok"
            except AppError as e:
                s.rollback()
                return e.code

    with ThreadPoolExecutor(len(calls)) as pool:
        return list(pool.map(worker, calls))


def test_F3_28_nhieu_pha_che_bam_dong_thoi(engine, committed):
    order_id, item_ids, staff_ids, cust_id = committed
    # 1) Cả 6 người cùng bấm "Bắt đầu" một món: chỉ 1 người thành công
    res = run_parallel(engine, [(service.start_item, sid, item_ids[0]) for sid in staff_ids])
    assert sorted(res) == ["INVALID_STATE_TRANSITION"] * (N - 1) + ["ok"]

    # 2) Mỗi người bắt đầu rồi bấm "Xong" một món khác nhau cùng lúc: đơn chỉ chuyển READY đúng 1 lần
    run_parallel(engine, [(service.start_item, sid, iid) for sid, iid in zip(staff_ids[1:], item_ids[1:])])
    res = run_parallel(engine, [(service.done_item, sid, iid) for sid, iid in zip(staff_ids, item_ids)])
    assert res == ["ok"] * N

    # 3) Cả 6 người cùng bấm "Đã giao": chỉ 1 lần thành công, điểm cộng 1 lần
    res = run_parallel(engine, [(service.complete_order, sid, order_id) for sid in staff_ids])
    assert sorted(res) == ["INVALID_STATE_TRANSITION"] * (N - 1) + ["ok"]

    with Session(engine) as s:
        assert s.get(Order, order_id).status == "COMPLETED"
        steps = s.scalars(select(OrderStatusHistory.to_status).where(OrderStatusHistory.order_id == order_id)
                          .order_by(OrderStatusHistory.id)).all()
        assert steps == ["PENDING_PAYMENT", "PAID", "PREPARING", "READY", "COMPLETED"]
        assert s.get(Customer, cust_id).loyalty_points == 12  # 120.000đ → 12 điểm, đúng 1 lần
        assert s.scalar(select(func.count()).select_from(LoyaltyTransaction)) == 1
