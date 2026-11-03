"""UC03 – Xem menu theo chi nhánh (phần gợi ý món làm ở F7)."""
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import AppError
from app.models import Branch
from app.modules.menu.service import get_branch_menu
from app.ws.hub import hub

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


# Kênh realtime menu khách (UC03 – Quy tắc): MENU_UPDATED khi quản trị đổi món, giá, tình trạng, khuyến mãi (F6).
# Công khai (menu là thông tin công khai); không nhận dữ liệu từ client.
ws_router = APIRouter(tags=["public"])


@ws_router.websocket("/ws/menu/{branch_id}")
async def menu_socket(websocket: WebSocket, branch_id: int, db: Session = Depends(get_db)):
    def exists() -> bool:
        b = db.get(Branch, branch_id)
        return b is not None and b.is_active

    if not await run_in_threadpool(exists):
        await websocket.close(code=4404)
        return
    await websocket.accept()
    channel = f"menu:{branch_id}"
    hub.subscribe(channel, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        hub.unsubscribe(channel, websocket)
