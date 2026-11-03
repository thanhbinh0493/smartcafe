"""Hàm tạo dữ liệu nhanh cho test."""
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import (
    Branch, BranchMenuItem, Category, Customer, DiningTable, MenuItem, Promotion, PromotionItem, Staff,
)

PASSWORD = "secret123"
_PW_HASH = hash_password(PASSWORD)


def now() -> datetime:
    return datetime.now(timezone.utc)


def branch(db: Session, code: str = "CG", is_active: bool = True) -> Branch:
    b = Branch(code=code, name=f"Chi nhánh {code}", address=f"Địa chỉ {code}", is_active=is_active)
    db.add(b)
    db.flush()
    return b


def table(db: Session, b: Branch, number: str = "05", is_active: bool = True) -> DiningTable:
    t = DiningTable(branch_id=b.id, table_number=number, qr_token=secrets.token_urlsafe(16), is_active=is_active)
    db.add(t)
    db.flush()
    return t


def staff(db: Session, username: str, role: str, b: Branch | None = None, is_active: bool = True) -> Staff:
    s = Staff(
        username=username, full_name=username.upper(), role=role, password_hash=_PW_HASH,
        branch_id=b.id if b else None, is_active=is_active,
    )
    db.add(s)
    db.flush()
    return s


def category(db: Session, name: str = "Cà phê", sort_order: int = 1, is_active: bool = True) -> Category:
    c = Category(name=name, sort_order=sort_order, is_active=is_active)
    db.add(c)
    db.flush()
    return c


def item(
    db: Session, c: Category, name: str, price: int, *, age_days: int = 100,
    is_active: bool = True, is_deleted: bool = False,
) -> MenuItem:
    m = MenuItem(
        category_id=c.id, name=name, base_price=price, is_active=is_active, is_deleted=is_deleted,
        created_at=now() - timedelta(days=age_days),
    )
    db.add(m)
    db.flush()
    return m


def branch_item(db: Session, b: Branch, m: MenuItem, price: int | None = None, available: bool = True) -> None:
    db.add(BranchMenuItem(branch_id=b.id, menu_item_id=m.id, price_override=price, is_available=available))
    db.flush()


def promo(
    db: Session, creator: Staff, prices: dict[MenuItem, int], *, b: Branch | None = None,
    start: timedelta = timedelta(days=-1), end: timedelta = timedelta(days=1), is_active: bool = True,
) -> Promotion:
    p = Promotion(
        name="KM test", branch_id=b.id if b else None, start_at=now() + start, end_at=now() + end,
        is_active=is_active, created_by=creator.id,
        items=[PromotionItem(menu_item_id=m.id, promo_price=v) for m, v in prices.items()],
    )
    db.add(p)
    db.flush()
    return p


def customer(db: Session, phone: str = "0912345678", points: int = 0) -> Customer:
    c = Customer(phone=phone, name=None, loyalty_points=points)
    db.add(c)
    db.flush()
    return c
