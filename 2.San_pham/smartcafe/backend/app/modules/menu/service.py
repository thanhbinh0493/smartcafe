"""Tính giá bán theo chi nhánh (UC03, D3 + D10):
    giá thường = COALESCE(price_override của chi nhánh, base_price)
    giá bán    = MIN(giá KM thấp nhất đang hiệu lực, giá thường)
KM hiệu lực: is_active AND now() BETWEEN start_at AND end_at AND (toàn chuỗi OR đúng chi nhánh).
Chỉ coi là "đang khuyến mãi" khi giá KM thấp hơn giá thường; khi đó mới gắn promotion_id.

Hàm này được dùng lại ở F2 (tạo đơn) để server luôn tự tính giá (NFR-S6) – tạo đơn luôn đọc thẳng CSDL.
Màn hình khách (menu, gợi ý) dùng `cached_branch_menu` (D38): hết hạn sau MENU_TTL giây hoặc đúng lúc một
khuyến mãi bắt đầu / kết thúc, và bị xóa ngay khi quản trị đổi menu (admin.common.publish_menu_updated).
"""
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core import cache
from app.core.config import get_settings

MENU_TTL = 60.0
# Giây tới mốc bắt đầu / kết thúc gần nhất của một KM đang bật (lúc đó giá bán đổi)
NEXT_PROMO_CHANGE_SQL = text(
    """
    SELECT extract(epoch FROM min(t) - now()) FROM (
        SELECT start_at AS t FROM promotions WHERE is_active AND start_at > now()
        UNION ALL SELECT end_at FROM promotions WHERE is_active AND end_at > now()
    ) x
    """
)

MENU_SQL = text(
    """
    SELECT m.id, m.name, m.description, m.image_url, m.temperature_type, m.tags,
           c.id AS category_id, c.name AS category_name, c.sort_order AS category_sort,
           COALESCE(b.price_override, m.base_price)            AS regular_price,
           p.promo_price, p.promotion_id,
           COALESCE(b.is_available, TRUE)                      AS is_available,
           m.created_at >= now() - make_interval(days => :new_days) AS is_new
    FROM menu_items m
    JOIN categories c             ON c.id = m.category_id AND c.is_active
    LEFT JOIN branch_menu_items b ON b.menu_item_id = m.id AND b.branch_id = :branch_id
    LEFT JOIN LATERAL (
        SELECT pi.promo_price, pi.promotion_id
        FROM promotion_items pi
        JOIN promotions pr ON pr.id = pi.promotion_id
        WHERE pi.menu_item_id = m.id
          AND pr.is_active AND now() BETWEEN pr.start_at AND pr.end_at
          AND (pr.branch_id IS NULL OR pr.branch_id = :branch_id)
        ORDER BY pi.promo_price, pi.promotion_id
        LIMIT 1
    ) p ON TRUE
    WHERE m.is_active AND NOT m.is_deleted
    -- Collation ICU tiếng Việt: postgres:16-alpine (musl) so sánh en_US.utf8 theo byte (BUG-F1-01)
    ORDER BY c.sort_order, c.id, m.name COLLATE "vi-VN-x-icu"
    """
)


@dataclass(frozen=True)
class PricedItem:
    id: int
    name: str
    description: str | None
    image_url: str | None
    temperature_type: str
    tags: list[str]
    category_id: int
    category_name: str
    regular_price: int
    sell_price: int
    promotion_id: int | None
    is_available: bool
    is_new: bool

    @property
    def is_promo(self) -> bool:
        return self.promotion_id is not None


def apply_promo(regular_price: int, promo_price: int | None, promotion_id: int | None) -> tuple[int, int | None]:
    """Trả (giá bán, promotion_id áp dụng). KM chỉ áp dụng khi rẻ hơn giá thường."""
    if promo_price is not None and promo_price < regular_price:
        return promo_price, promotion_id
    return regular_price, None


def get_branch_menu(db: Session, branch_id: int) -> list[PricedItem]:
    rows = db.execute(MENU_SQL, {"branch_id": branch_id, "new_days": get_settings().new_item_days}).mappings()
    items: list[PricedItem] = []
    for r in rows:
        sell_price, promo_id = apply_promo(r["regular_price"], r["promo_price"], r["promotion_id"])
        items.append(
            PricedItem(
                id=r["id"], name=r["name"], description=r["description"], image_url=r["image_url"],
                temperature_type=r["temperature_type"], tags=list(r["tags"] or []),
                category_id=r["category_id"], category_name=r["category_name"],
                regular_price=r["regular_price"], sell_price=sell_price, promotion_id=promo_id,
                is_available=r["is_available"], is_new=r["is_new"],
            )
        )
    return items


def menu_ttl(db: Session) -> float:
    """Thời gian được giữ menu trong cache: MENU_TTL, nhưng không vượt qua mốc đổi giá KM gần nhất."""
    nxt = db.scalar(NEXT_PROMO_CHANGE_SQL)
    return MENU_TTL if nxt is None else max(0.0, min(MENU_TTL, float(nxt)))


def cached_branch_menu(db: Session, branch_id: int) -> list[PricedItem]:
    return cache.get("menu", branch_id, lambda: (get_branch_menu(db, branch_id), menu_ttl(db)))
