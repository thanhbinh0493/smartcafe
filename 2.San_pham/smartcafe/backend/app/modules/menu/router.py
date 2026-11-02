"""UC03 – Xem menu theo chi nhánh (phần gợi ý món làm ở F7)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import AppError
from app.models import Branch
from app.modules.menu.service import get_branch_menu

router = APIRouter(prefix="/api/public", tags=["public"])


class MenuItemOut(BaseModel):
    id: int
    name: str
    description: str | None
    image_url: str | None
    temperature_type: str
    tags: list[str]
    regular_price: int
    sell_price: int
    is_promo: bool
    promotion_id: int | None
    is_new: bool
    is_available: bool


class CategoryOut(BaseModel):
    id: int
    name: str
    items: list[MenuItemOut]


class MenuResponse(BaseModel):
    branch_id: int
    categories: list[CategoryOut]


@router.get("/branches/{branch_id}/menu", response_model=MenuResponse)
def branch_menu(branch_id: int, db: Session = Depends(get_db)) -> MenuResponse:
    branch = db.get(Branch, branch_id)
    if branch is None or not branch.is_active:
        raise AppError(404, "BRANCH_NOT_FOUND", "Chi nhánh không tồn tại hoặc đã ngừng hoạt động")

    categories: dict[int, CategoryOut] = {}
    for it in get_branch_menu(db, branch_id):
        cat = categories.setdefault(it.category_id, CategoryOut(id=it.category_id, name=it.category_name, items=[]))
        cat.items.append(
            MenuItemOut(
                id=it.id, name=it.name, description=it.description, image_url=it.image_url,
                temperature_type=it.temperature_type, tags=it.tags,
                regular_price=it.regular_price, sell_price=it.sell_price,
                is_promo=it.is_promo, promotion_id=it.promotion_id,
                is_new=it.is_new, is_available=it.is_available,
            )
        )
    return MenuResponse(branch_id=branch_id, categories=list(categories.values()))
