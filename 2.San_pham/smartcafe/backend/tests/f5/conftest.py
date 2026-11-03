from datetime import timedelta

import pytest
from sqlalchemy import text

from app.models import Order
from tests import factories as f
from tests.f3.conftest import Bar, auth


class Support(Bar):
    """Bar của F3 + thu ngân chi nhánh HD."""

    def __init__(self, db):
        super().__init__(db)
        self.tn_hd = f.staff(db, "tn_hd", "CASHIER", self.hd)


@pytest.fixture
def sup(db) -> Support:
    return Support(db)


def search(client, staff, **params):
    return client.get("/api/staff/orders/search", params=params, headers=auth(staff))


def cancel(client, staff, order_id: int, reason: str = "Khách gọi nhầm món"):
    return client.post(f"/api/staff/orders/{order_id}/cancel", json={"reason": reason}, headers=auth(staff))


def move_to_yesterday(db, o: dict) -> None:
    """Đơn tồn từ hôm trước: lùi ngày đơn và giờ thanh toán 1 ngày."""
    order = db.get(Order, o["order_id"])
    today = db.scalar(text("SELECT (now() AT TIME ZONE 'Asia/Ho_Chi_Minh')::date"))
    order.order_date = today - timedelta(days=1)
    order.paid_at = order.paid_at - timedelta(days=1)
    db.flush()
