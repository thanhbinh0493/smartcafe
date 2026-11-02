"""Nạp dữ liệu mẫu (IV.1 Mục 7): chi nhánh, bàn + QR, nhân viên, danh mục, món, menu chi nhánh, khuyến mãi.
Đơn lịch sử và khách thành viên sẽ do seed_orders.py sinh (F7/F8).

    python -m scripts.seed_data            # nạp (báo lỗi nếu CSDL đã có dữ liệu)
    python -m scripts.seed_data --if-empty # chỉ nạp khi CSDL còn trống (dùng trong start.sh)
    python -m scripts.seed_data --print-qr # in danh sách link QR của các bàn
"""
import argparse
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.security import hash_password
from app.models import (
    Branch, BranchMenuItem, Category, DiningTable, MenuItem, Promotion, PromotionItem, Staff,
)

TABLES_PER_BRANCH = 20

BRANCHES = [
    ("CG", "SmartCafe Cầu Giấy", "122 Xuân Thủy, Cầu Giấy, Hà Nội", "0241234501", 21.036700, 105.782400),
    ("HD", "SmartCafe Hà Đông", "96A Trần Phú, Hà Đông, Hà Nội", "0241234502", 20.980900, 105.787000),
    ("TX", "SmartCafe Thanh Xuân", "235 Nguyễn Trãi, Thanh Xuân, Hà Nội", "0241234503", 20.998600, 105.808300),
]

CATEGORIES = ["Cà phê", "Trà", "Đá xay", "Nước ép & Sinh tố", "Bánh"]

# (danh mục, tên, giá chung, nhiệt độ, tags, là món mới?)
ITEMS = [
    ("Cà phê", "Cà phê đen đá", 25000, "COLD", ["coffee", "strong"], False),
    ("Cà phê", "Cà phê đen nóng", 25000, "HOT", ["coffee", "strong"], False),
    ("Cà phê", "Cà phê sữa đá", 29000, "COLD", ["coffee", "milk", "sweet"], False),
    ("Cà phê", "Cà phê sữa nóng", 29000, "HOT", ["coffee", "milk", "sweet"], False),
    ("Cà phê", "Bạc xỉu", 32000, "COLD", ["coffee", "milk", "sweet"], False),
    ("Cà phê", "Bạc xỉu nóng", 32000, "HOT", ["coffee", "milk", "sweet"], False),
    ("Cà phê", "Cà phê muối", 35000, "COLD", ["coffee", "salty", "cream"], False),
    ("Cà phê", "Cold brew", 45000, "COLD", ["coffee", "strong"], False),
    ("Cà phê", "Americano", 39000, "BOTH", ["coffee", "strong"], False),
    ("Cà phê", "Latte", 45000, "BOTH", ["coffee", "milk"], False),
    ("Cà phê", "Bạc xỉu dừa", 39000, "COLD", ["coffee", "coconut", "sweet"], True),
    ("Trà", "Trà đào cam sả", 45000, "COLD", ["tea", "fruit", "fresh"], False),
    ("Trà", "Trà vải", 42000, "COLD", ["tea", "fruit", "sweet"], False),
    ("Trà", "Trà chanh mật ong", 35000, "BOTH", ["tea", "fresh"], False),
    ("Trà", "Trà sen vàng", 45000, "COLD", ["tea", "milk", "sweet"], False),
    ("Trà", "Trà ô long sữa", 42000, "BOTH", ["tea", "milk"], False),
    ("Trà", "Trà gừng mật ong", 35000, "HOT", ["tea", "warm"], False),
    ("Trà", "Trà dâu tây kem cheese", 49000, "COLD", ["tea", "fruit", "cream"], True),
    ("Đá xay", "Matcha đá xay", 52000, "COLD", ["blended", "matcha", "sweet"], False),
    ("Đá xay", "Cookie đá xay", 52000, "COLD", ["blended", "chocolate", "sweet"], False),
    ("Đá xay", "Cà phê đá xay", 49000, "COLD", ["blended", "coffee", "sweet"], False),
    ("Đá xay", "Socola đá xay", 52000, "COLD", ["blended", "chocolate", "sweet"], False),
    ("Đá xay", "Xoài đá xay", 49000, "COLD", ["blended", "fruit", "fresh"], True),
    ("Nước ép & Sinh tố", "Nước cam ép", 39000, "COLD", ["juice", "fruit", "fresh"], False),
    ("Nước ép & Sinh tố", "Nước ép dưa hấu", 35000, "COLD", ["juice", "fruit", "fresh"], False),
    ("Nước ép & Sinh tố", "Sinh tố bơ", 45000, "COLD", ["smoothie", "fruit", "cream"], False),
    ("Nước ép & Sinh tố", "Sinh tố xoài", 42000, "COLD", ["smoothie", "fruit", "sweet"], False),
    ("Nước ép & Sinh tố", "Sữa chua việt quất", 42000, "COLD", ["yogurt", "fruit"], False),
    ("Bánh", "Bánh croissant bơ", 29000, "NONE", ["bakery", "butter"], False),
    ("Bánh", "Bánh tiramisu", 39000, "NONE", ["bakery", "coffee", "sweet"], False),
    ("Bánh", "Bánh mousse chanh dây", 39000, "NONE", ["bakery", "fruit", "sweet"], False),
    ("Bánh", "Bánh phô mai nướng", 42000, "NONE", ["bakery", "cream"], False),
    ("Bánh", "Bánh mì que pate", 19000, "NONE", ["bakery", "salty"], False),
    ("Bánh", "Bánh chuối nướng", 29000, "NONE", ["bakery", "sweet"], False),
    ("Bánh", "Bánh sừng bò hạnh nhân", 35000, "NONE", ["bakery", "nut"], True),
]


def is_empty(db: Session) -> bool:
    return (db.scalar(select(func.count()).select_from(Branch)) or 0) == 0


def seed(db: Session, now: datetime | None = None) -> dict[str, int]:
    now = now or datetime.now(timezone.utc)
    pw = hash_password(get_settings().seed_staff_password)

    branches = [
        Branch(code=c, name=n, address=a, phone=p, latitude=lat, longitude=lon)
        for c, n, a, p, lat, lon in BRANCHES
    ]
    db.add_all(branches)
    db.flush()

    for b in branches:
        db.add_all(
            DiningTable(branch_id=b.id, table_number=f"{i:02d}", qr_token=secrets.token_urlsafe(16))
            for i in range(1, TABLES_PER_BRANCH + 1)
        )

    admin = Staff(full_name="Trần Thị An", username="admin", password_hash=pw, role="ADMIN")
    db.add(admin)
    for b in branches:
        c = b.code.lower()
        db.add_all([
            Staff(branch_id=b.id, full_name=f"Quản lý {b.code}", username=f"ql_{c}", password_hash=pw, role="MANAGER"),
            Staff(branch_id=b.id, full_name=f"Thu ngân {b.code}", username=f"tn_{c}", password_hash=pw, role="CASHIER"),
            Staff(branch_id=b.id, full_name=f"Pha chế 1 {b.code}", username=f"pc1_{c}", password_hash=pw, role="BARISTA"),
            Staff(branch_id=b.id, full_name=f"Pha chế 2 {b.code}", username=f"pc2_{c}", password_hash=pw, role="BARISTA"),
        ])

    cats = {name: Category(name=name, sort_order=i) for i, name in enumerate(CATEGORIES, start=1)}
    db.add_all(cats.values())
    db.flush()

    items: dict[str, MenuItem] = {}
    for cat, name, price, temp, tags, is_new in ITEMS:
        created = now - timedelta(days=5) if is_new else now - timedelta(days=120)
        items[name] = MenuItem(
            category_id=cats[cat].id, name=name, base_price=price, temperature_type=temp,
            tags=tags, created_at=created, description=None,
        )
    db.add_all(items.values())
    db.flush()

    cg, hd, _tx = branches
    # Menu chi nhánh: Hà Đông đặt giá riêng 2 món; Cầu Giấy tạm hết 1 món
    db.add_all([
        BranchMenuItem(branch_id=hd.id, menu_item_id=items["Cà phê sữa đá"].id, price_override=27000),
        BranchMenuItem(branch_id=hd.id, menu_item_id=items["Bạc xỉu"].id, price_override=30000),
        BranchMenuItem(branch_id=cg.id, menu_item_id=items["Bạc xỉu nóng"].id, is_available=False),
    ])

    # Khuyến mãi: 1 toàn chuỗi đang chạy, 1 riêng Cầu Giấy đang chạy, 1 đã kết thúc
    db.add_all([
        Promotion(
            name="Tuần lễ trà trái cây", description="Giảm 20% các món trà trái cây",
            branch_id=None, start_at=now - timedelta(days=3), end_at=now + timedelta(days=11), created_by=admin.id,
            items=[
                PromotionItem(menu_item_id=items["Trà đào cam sả"].id, promo_price=36000),
                PromotionItem(menu_item_id=items["Trà vải"].id, promo_price=33600),
            ],
        ),
        Promotion(
            name="Mừng khai trương Cầu Giấy", description="Cà phê sữa đá chỉ 25.000đ",
            branch_id=cg.id, start_at=now - timedelta(days=1), end_at=now + timedelta(days=6), created_by=admin.id,
            items=[PromotionItem(menu_item_id=items["Cà phê sữa đá"].id, promo_price=25000)],
        ),
        Promotion(
            name="Halloween 2026", description="Đã kết thúc",
            branch_id=None, start_at=now - timedelta(days=10), end_at=now - timedelta(days=2), created_by=admin.id,
            items=[PromotionItem(menu_item_id=items["Cookie đá xay"].id, promo_price=39000)],
        ),
    ])
    db.flush()
    return {
        "branches": len(branches),
        "tables": len(branches) * TABLES_PER_BRANCH,
        "staff": 1 + 4 * len(branches),
        "categories": len(cats),
        "menu_items": len(items),
        "promotions": 3,
    }


def print_qr(db: Session, base_url: str) -> None:
    rows = db.execute(
        select(Branch.code, DiningTable.table_number, DiningTable.qr_token)
        .join(Branch, Branch.id == DiningTable.branch_id)
        .order_by(Branch.code, DiningTable.table_number)
    )
    for code, number, token in rows:
        print(f"{code} bàn {number}: {base_url}/t/{token}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--if-empty", action="store_true")
    ap.add_argument("--print-qr", action="store_true")
    ap.add_argument("--base-url", default="http://localhost:8080")
    args = ap.parse_args()

    with SessionLocal() as db:
        if args.print_qr:
            print_qr(db, args.base_url)
            return
        if not is_empty(db):
            if args.if_empty:
                print("[seed] CSDL đã có dữ liệu, bỏ qua.")
                return
            raise SystemExit("[seed] CSDL đã có dữ liệu. Xóa dữ liệu trước khi nạp lại.")
        counts = seed(db)
        db.commit()
        print("[seed] Đã nạp:", counts)


if __name__ == "__main__":
    main()
