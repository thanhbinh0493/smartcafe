"""F2 – Nhiều bàn đặt đơn cùng lúc: mã đơn không trùng, liên tục (khóa advisory theo chi nhánh).
Test này dùng nhiều kết nối thật song song nên dữ liệu được commit, và tự dọn sạch ở cuối."""
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.order.schemas import CreateOrderRequest, OrderItemIn
from app.modules.order.service import create_order
from tests import factories as f

N = 12


@pytest.fixture
def committed_shop(engine):
    with Session(engine) as s:
        b = f.branch(s, "CC")
        tables = [f.table(s, b, f"{i:02d}").qr_token for i in range(N)]
        item_id = f.item(s, f.category(s, "Conc", 1), "Mon", 10000).id
        s.commit()
    yield tables, item_id
    with engine.begin() as c:
        c.execute(text("TRUNCATE order_status_history, order_items, payments, orders, dining_tables, "
                       "menu_items, categories, branches RESTART IDENTITY CASCADE"))


def test_F2_29_dat_don_dong_thoi_khong_trung_ma(engine, committed_shop):
    tables, item_id = committed_shop

    def one(qr: str) -> str:
        with Session(engine) as s:
            res = create_order(s, CreateOrderRequest(qr_token=qr, items=[OrderItemIn(menu_item_id=item_id, quantity=1)]))
            s.commit()
            return res.order_code

    with ThreadPoolExecutor(max_workers=N) as pool:
        codes = list(pool.map(one, tables))
    assert sorted(codes) == [f"CC-{i:04d}" for i in range(1, N + 1)]
