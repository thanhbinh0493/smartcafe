from datetime import datetime, timedelta, timezone

import pytest

from app.core.config import get_settings
from app.core.security import create_customer_token
from app.models import MenuItem, Order, OrderItem
from app.modules.recommend import weather as wmod
from tests import factories as f

NOW = datetime.now(timezone.utc)


class Cafe:
    """2 chi nhánh, 6 món có tags + loại nóng / lạnh, khách thành viên."""

    def __init__(self, db):
        self.db = db
        self.cg, self.hd = f.branch(db, "CG"), f.branch(db, "HD")
        self.t_cg = f.table(db, self.cg, "01")
        self.t_hd = f.table(db, self.hd, "01")
        self.admin = f.staff(db, "admin", "ADMIN")
        coffee, tea, cake = f.category(db, "Cà phê", 1), f.category(db, "Trà", 2), f.category(db, "Bánh", 3)
        self.sua_da = self.item(coffee, "Cà phê sữa đá", 29000, "COLD", ["coffee", "milk", "sweet"])
        self.sua_nong = self.item(coffee, "Cà phê sữa nóng", 29000, "HOT", ["coffee", "milk", "sweet"])
        self.bac_xiu = self.item(coffee, "Bạc xỉu", 32000, "COLD", ["coffee", "milk", "sweet"])
        self.tra_dao = self.item(tea, "Trà đào cam sả", 45000, "COLD", ["tea", "fruit"])
        self.tra_gung = self.item(tea, "Trà gừng", 35000, "HOT", ["tea", "warm"])
        self.croissant = self.item(cake, "Bánh croissant", 29000, "NONE", ["bakery", "butter"])
        self.member = f.customer(db, "0912345678")

    def item(self, cat, name, price, temp, tags, age_days=100) -> MenuItem:
        m = f.item(self.db, cat, name, price, age_days=age_days)
        m.temperature_type, m.tags = temp, tags
        self.db.flush()
        return m

    def sell(self, branch, *lines, days_ago: float = 1, customer=None, status="COMPLETED") -> Order:
        """Đơn lịch sử đã thanh toán: lines = (món, số lượng)."""
        return make_order(self.db, branch, *lines, paid_at=NOW - timedelta(days=days_ago), customer=customer,
                          status=status)


_seq = [0]


def make_order(db, branch, *lines, paid_at, customer=None, status="COMPLETED") -> Order:
    _seq[0] += 1
    t = f.table(db, branch, f"H{_seq[0]}")
    o = Order(order_code=f"{branch.code}-H{_seq[0]}", order_date=paid_at.date(), access_token=f"tok{_seq[0]:08d}x",
              branch_id=branch.id, table_id=t.id, customer_id=customer.id if customer else None, status=status,
              total_amount=sum(m.base_price * q for m, q in lines), paid_at=paid_at, created_at=paid_at,
              items=[OrderItem(menu_item_id=m.id, quantity=q, original_price=m.base_price, unit_price=m.base_price,
                               status="DONE") for m, q in lines])
    db.add(o)
    db.flush()
    return o


@pytest.fixture
def cafe(db) -> Cafe:
    return Cafe(db)


@pytest.fixture(autouse=True)
def _mock_weather():
    """Mặc định trời nóng 31°C, không key Weather API; test tự đổi khi cần."""
    s = get_settings()
    old = (s.weather_api_key, s.weather_mock_temp_c)
    s.weather_api_key, s.weather_mock_temp_c = "", 31.0
    wmod.clear_cache()
    yield s
    s.weather_api_key, s.weather_mock_temp_c = old
    wmod.clear_cache()


def member_auth(customer) -> dict:
    return {"Authorization": f"Bearer {create_customer_token(customer.id)[0]}"}


def recs(client, branch, cart=None, headers=None) -> dict:
    params = {"cart": ",".join(str(m.id) for m in cart)} if cart else {}
    r = client.get(f"/api/public/branches/{branch.id}/recommendations", params=params, headers=headers or {})
    assert r.status_code == 200, r.text
    return r.json()


def names(items) -> list[str]:
    return [i["name"] for i in items]
