"""Tiện ích dùng chung của các API quản trị."""
import re
from typing import Any

from fastapi import BackgroundTasks
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.ws.hub import hub

ADMIN = ("ADMIN",)
ADMIN_MANAGER = ("ADMIN", "MANAGER")
MAX_PRICE = 10_000_000

_SPACES = re.compile(r"\s+")


def clean(s: str) -> str:
    """Bỏ khoảng trắng thừa ở đầu/cuối và giữa các từ."""
    return _SPACES.sub(" ", s).strip()


def get_or_404(db: Session, model: Any, id_: int, code: str, message: str, *, lock: bool = False) -> Any:
    obj = db.get(model, id_, with_for_update=lock)
    if obj is None:
        raise AppError(404, code, message)
    return obj


def duplicate(field: str, message: str) -> AppError:
    return AppError(409, "DUPLICATE_VALUE", message, {"field": field})


def flush_unique(db: Session, field: str, message: str) -> None:
    """Ghi xuống CSDL; nếu vi phạm UNIQUE (hai người tạo cùng lúc) thì trả 409 thay vì 500."""
    try:
        with db.begin_nested():
            db.flush()
    except IntegrityError as e:
        if "unique" in str(e.orig).lower() or "duplicate" in str(e.orig).lower():
            raise duplicate(field, message) from None
        raise


def publish_menu_updated(background: BackgroundTasks, branch_id: int | None, reason: str) -> None:
    """MENU_UPDATED trên /ws/menu/{branch_id} (UC03): menu khách tự tải lại.
    branch_id = None: thay đổi toàn chuỗi (menu chung, KM toàn chuỗi) → gửi mọi chi nhánh."""
    data = {"branch_id": branch_id, "reason": reason}
    if branch_id is None:
        background.add_task(hub.publish_prefix, "menu:", "MENU_UPDATED", data)
    else:
        background.add_task(hub.publish, f"menu:{branch_id}", "MENU_UPDATED", data)
