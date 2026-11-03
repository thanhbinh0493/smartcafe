from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from app.models import Order, OrderItem
from app.modules.report.service import today_vn
from tests import factories as f

VN = ZoneInfo("Asia/Ho_Chi_Minh")
YESTERDAY = today_vn() - timedelta(days=1)


def at(d: date, hh: int, mm: int = 0) -> datetime:
    """Giờ Việt Nam của ngày d → datetime UTC."""
    return datetime.combine(d, time(hh, mm), VN).astimezone(timezone.utc)


class Shop:
    def __init__(self, db):
        self.db = db
        self.cg, self.hd = f.branch(db, "CG"), f.branch(db, "HD")
        self.admin = f.staff(db, "admin", "ADMIN")
        self.ql = f.staff(db, "ql_cg", "MANAGER", self.cg)
        self.tn = f.staff(db, "tn_cg", "CASHIER", self.cg)
        self.pc = f.staff(db, "pc_cg", "BARISTA", self.cg)
        cat = f.category(db, "Cà phê", 1)
        self.sua_da = f.item(db, cat, "Cà phê sữa đá", 30000)
        self.tra_dao = f.item(db, cat, "Trà đào", 40000)
        self.banh = f.item(db, cat, "Bánh", 20000)
        self.promo = f.promo(db, self.admin, {self.tra_dao: 30000})
        self.member = f.customer(db)
        self._n = 0

    def order(self, branch, *lines, paid_at: datetime | None, wait_s: int | None = 300, status="COMPLETED",
              member=False) -> Order:
        """lines: (món, số lượng, đơn giá[, KM?, gợi ý?])"""
        self._n += 1
        t = f.table(self.db, branch, f"T{self._n}")
        items = [OrderItem(menu_item_id=l[0].id, quantity=l[1], original_price=l[2], unit_price=l[2], status="DONE",
                           promotion_id=self.promo.id if len(l) > 3 and l[3] else None,
                           is_recommended=bool(len(l) > 4 and l[4])) for l in lines]
        o = Order(order_code=f"{branch.code}-R{self._n}", order_date=(paid_at or at(YESTERDAY, 8)).astimezone(VN).date(),
                  access_token=f"rep{self._n:010d}", branch_id=branch.id, table_id=t.id,
                  customer_id=self.member.id if member else None, status=status,
                  total_amount=sum(l[1] * l[2] for l in lines), paid_at=paid_at,
                  created_at=paid_at or at(YESTERDAY, 8),
                  ready_at=paid_at + timedelta(seconds=wait_s) if paid_at and wait_s is not None else None,
                  items=items)
        self.db.add(o)
        self.db.flush()
        return o


@pytest.fixture
def shop(db) -> Shop:
    return Shop(db)
