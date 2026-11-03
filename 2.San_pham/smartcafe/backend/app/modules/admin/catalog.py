"""UC09 – Quản lý danh mục (A05), UC10 – Quản lý món / menu chung (W05).

Quyền (ma trận RBAC – III.1): ADMIN thêm/sửa/xóa; MANAGER chỉ xem.
Mọi thay đổi đẩy MENU_UPDATED tới menu khách của tất cả chi nhánh (menu chung).
"""
import secrets
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, UploadFile, status
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.errors import AppError
from app.models import Category, MenuItem, Staff
from app.modules.admin.common import ADMIN, ADMIN_MANAGER, duplicate, flush_unique, get_or_404, publish_menu_updated
from app.modules.admin.schemas import CategoryIn, CategoryOut, MenuItemIn, MenuItemOut
from app.modules.auth.deps import require_roles

router = APIRouter(prefix="/api/staff", tags=["admin – menu chung"])

DUP_CATEGORY = "Tên danh mục đã tồn tại"
DUP_ITEM = "Đã có món cùng tên trong menu chung"


# ---------- Danh mục ----------
def _category_out(db: Session, c: Category) -> CategoryOut:
    count = db.scalar(select(func.count()).where(MenuItem.category_id == c.id, MenuItem.is_deleted.is_(False)))
    return CategoryOut(id=c.id, name=c.name, sort_order=c.sort_order, is_active=c.is_active, item_count=count or 0)


def _check_category_name(db: Session, name: str, exclude_id: int | None = None) -> None:
    q = select(Category.id).where(func.lower(Category.name) == name.lower())
    if exclude_id is not None:
        q = q.where(Category.id != exclude_id)
    if db.scalar(q) is not None:
        raise duplicate("name", DUP_CATEGORY)


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(_: Staff = Depends(require_roles(*ADMIN_MANAGER)), db: Session = Depends(get_db)):
    rows = db.execute(
        select(Category, func.count(MenuItem.id))
        .outerjoin(MenuItem, and_(MenuItem.category_id == Category.id, MenuItem.is_deleted.is_(False)))
        .group_by(Category.id)
        .order_by(Category.sort_order, Category.id)
    ).all()
    return [
        CategoryOut(id=c.id, name=c.name, sort_order=c.sort_order, is_active=c.is_active, item_count=n)
        for c, n in rows
    ]


@router.post("/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(body: CategoryIn, background: BackgroundTasks,
                    _: Staff = Depends(require_roles(*ADMIN)), db: Session = Depends(get_db)):
    _check_category_name(db, body.name)
    c = Category(name=body.name, sort_order=body.sort_order, is_active=body.is_active)
    db.add(c)
    flush_unique(db, "name", DUP_CATEGORY)
    db.commit()
    publish_menu_updated(background, None, "CATEGORY")
    return _category_out(db, c)


@router.put("/categories/{category_id}", response_model=CategoryOut)
def update_category(category_id: int, body: CategoryIn, background: BackgroundTasks,
                    _: Staff = Depends(require_roles(*ADMIN)), db: Session = Depends(get_db)):
    c = get_or_404(db, Category, category_id, "CATEGORY_NOT_FOUND", "Danh mục không tồn tại")
    _check_category_name(db, body.name, exclude_id=c.id)
    c.name, c.sort_order, c.is_active = body.name, body.sort_order, body.is_active
    flush_unique(db, "name", DUP_CATEGORY)
    db.commit()
    publish_menu_updated(background, None, "CATEGORY")
    return _category_out(db, c)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, background: BackgroundTasks,
                    _: Staff = Depends(require_roles(*ADMIN)), db: Session = Depends(get_db)):
    """Chỉ xóa được danh mục chưa từng có món (kể cả món đã xóa mềm vẫn giữ lịch sử đơn).
    Danh mục còn món: 409 CATEGORY_IN_USE – hãy chuyển món sang danh mục khác hoặc ẩn danh mục."""
    c = get_or_404(db, Category, category_id, "CATEGORY_NOT_FOUND", "Danh mục không tồn tại", lock=True)
    total = db.scalar(select(func.count()).where(MenuItem.category_id == c.id)) or 0
    if total:
        active = db.scalar(
            select(func.count()).where(MenuItem.category_id == c.id, MenuItem.is_deleted.is_(False))
        ) or 0
        msg = (f"Danh mục còn {active} món, hãy chuyển món sang danh mục khác hoặc ẩn danh mục" if active
               else "Danh mục có món đã xóa nằm trong lịch sử đơn, chỉ có thể ẩn danh mục")
        raise AppError(409, "CATEGORY_IN_USE", msg, {"item_count": active})
    db.delete(c)
    db.commit()
    publish_menu_updated(background, None, "CATEGORY")


# ---------- Món ----------
def _item_out(m: MenuItem) -> MenuItemOut:
    return MenuItemOut(
        id=m.id, category_id=m.category_id, category_name=m.category.name, name=m.name,
        description=m.description, base_price=m.base_price, image_url=m.image_url,
        temperature_type=m.temperature_type, tags=list(m.tags or []), is_active=m.is_active, created_at=m.created_at,
    )


def _get_item(db: Session, item_id: int) -> MenuItem:
    m = db.get(MenuItem, item_id)
    if m is None or m.is_deleted:
        raise AppError(404, "MENU_ITEM_NOT_FOUND", "Món không tồn tại hoặc đã bị xóa")
    return m


def _check_item(db: Session, body: MenuItemIn, exclude_id: int | None = None) -> None:
    get_or_404(db, Category, body.category_id, "CATEGORY_NOT_FOUND", "Danh mục không tồn tại")
    q = select(MenuItem.id).where(func.lower(MenuItem.name) == body.name.lower(), MenuItem.is_deleted.is_(False))
    if exclude_id is not None:
        q = q.where(MenuItem.id != exclude_id)
    if db.scalar(q) is not None:
        raise duplicate("name", DUP_ITEM)


@router.get("/menu-items", response_model=list[MenuItemOut])
def list_items(
    category_id: int | None = None,
    status_: str = Query("all", alias="status", pattern="^(all|active|hidden)$"),
    _: Staff = Depends(require_roles(*ADMIN_MANAGER)),
    db: Session = Depends(get_db),
):
    q = select(MenuItem).join(Category).where(MenuItem.is_deleted.is_(False))
    if category_id is not None:
        q = q.where(MenuItem.category_id == category_id)
    if status_ != "all":
        q = q.where(MenuItem.is_active.is_(status_ == "active"))
    q = q.order_by(Category.sort_order, Category.id, MenuItem.name.collate("vi-VN-x-icu"))
    return [_item_out(m) for m in db.scalars(q)]


@router.post("/menu-items", response_model=MenuItemOut, status_code=status.HTTP_201_CREATED)
def create_item(body: MenuItemIn, background: BackgroundTasks,
                _: Staff = Depends(require_roles(*ADMIN)), db: Session = Depends(get_db)):
    _check_item(db, body)
    m = MenuItem(**body.model_dump())
    db.add(m)
    db.flush()
    db.commit()
    db.refresh(m)
    publish_menu_updated(background, None, "MENU_ITEM")
    return _item_out(m)


@router.put("/menu-items/{item_id}", response_model=MenuItemOut)
def update_item(item_id: int, body: MenuItemIn, background: BackgroundTasks,
                _: Staff = Depends(require_roles(*ADMIN)), db: Session = Depends(get_db)):
    m = _get_item(db, item_id)
    _check_item(db, body, exclude_id=m.id)
    for k, v in body.model_dump().items():
        setattr(m, k, v)
    db.flush()
    db.commit()
    db.refresh(m)
    publish_menu_updated(background, None, "MENU_ITEM")
    return _item_out(m)


@router.delete("/menu-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, background: BackgroundTasks,
                _: Staff = Depends(require_roles(*ADMIN)), db: Session = Depends(get_db)):
    """Xóa mềm (giữ lịch sử đơn – III.2 Mục 2.2): món biến mất khỏi menu chung, menu chi nhánh và KM."""
    m = _get_item(db, item_id)
    m.is_deleted, m.is_active = True, False
    db.commit()
    publish_menu_updated(background, None, "MENU_ITEM")


# ---------- Ảnh món ----------
_MAGIC = (
    (b"\xff\xd8\xff", "jpg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
)


def _image_ext(data: bytes) -> str | None:
    for magic, ext in _MAGIC:
        if data.startswith(magic):
            return ext
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def upload_root() -> Path:
    return Path(get_settings().upload_dir)


@router.post("/menu-items/{item_id}/image", response_model=MenuItemOut)
def upload_image(item_id: int, background: BackgroundTasks, file: UploadFile = File(...),
                 _: Staff = Depends(require_roles(*ADMIN)), db: Session = Depends(get_db)):
    """Ảnh JPG / PNG / WEBP tối đa 2 MB. Kiểm tra theo nội dung file (magic bytes), không tin đuôi file / content-type."""
    m = _get_item(db, item_id)
    limit = get_settings().max_image_bytes
    data = file.file.read(limit + 1)
    if len(data) > limit:
        raise AppError(413, "INVALID_IMAGE", f"Ảnh tối đa {limit // (1024 * 1024)} MB", {"max_bytes": limit})
    ext = _image_ext(data)
    if ext is None:
        raise AppError(422, "INVALID_IMAGE", "Chỉ nhận ảnh JPG, PNG hoặc WEBP")
    folder = upload_root() / "menu"
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{m.id}-{secrets.token_hex(6)}.{ext}"  # tên mới mỗi lần để trình duyệt không dùng ảnh cũ trong cache
    (folder / name).write_bytes(data)
    old = m.image_url
    m.image_url = f"/api/uploads/menu/{name}"
    db.commit()
    if old and old.startswith("/api/uploads/menu/"):
        (folder / old.rsplit("/", 1)[-1]).unlink(missing_ok=True)
    publish_menu_updated(background, None, "MENU_ITEM")
    return _item_out(m)
