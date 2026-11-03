"""UC15 – Quản lý chương trình khuyến mãi (W07, SD05). Chỉ Quản trị viên (D14).

Quy tắc (UC15, D10, D27):
- end_at > start_at; khi lưu, chương trình phải còn hiệu lực (end_at > hiện tại).
- Giá KM < giá bán hiện tại: KM 1 chi nhánh so với giá chi nhánh (giá riêng nếu có, không thì giá chung);
  KM toàn chuỗi so với giá chung. Nếu chi nhánh đặt giá riêng thấp hơn giá KM thì lúc bán vẫn lấy giá thấp hơn
  và không gắn nhãn KM (D27).
- Không sửa được chương trình đã kết thúc (giữ đúng lịch sử) → 409 PROMOTION_ENDED.
- Khuyến mãi tự có / hết hiệu lực theo thời gian (kiểm tra lúc truy vấn menu), không cần job.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import AppError
from app.models import Branch, BranchMenuItem, MenuItem, Promotion, PromotionItem, Staff
from app.modules.admin.common import ADMIN, get_or_404, publish_menu_updated
from app.modules.admin.schemas import PromoStatus, PromotionIn, PromotionItemOut, PromotionOut
from app.modules.auth.deps import require_roles

router = APIRouter(prefix="/api/staff", tags=["admin – khuyến mãi"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


def promo_status(p: Promotion, now: datetime) -> PromoStatus:
    if p.end_at < now:
        return "ended"
    if p.start_at > now:
        return "upcoming"
    return "running"


def _current_prices(db: Session, branch_id: int | None, item_ids: list[int]) -> dict[int, tuple[str, int]]:
    """{menu_item_id: (tên, giá bán hiện tại)} cho các món chưa xóa."""
    q = select(MenuItem.id, MenuItem.name, MenuItem.base_price).where(
        MenuItem.id.in_(item_ids), MenuItem.is_deleted.is_(False)
    )
    if branch_id is not None:
        q = (
            select(MenuItem.id, MenuItem.name, func.coalesce(BranchMenuItem.price_override, MenuItem.base_price))
            .outerjoin(BranchMenuItem, (BranchMenuItem.menu_item_id == MenuItem.id)
                       & (BranchMenuItem.branch_id == branch_id))
            .where(MenuItem.id.in_(item_ids), MenuItem.is_deleted.is_(False))
        )
    return {i: (n, p) for i, n, p in db.execute(q)}


def _out(db: Session, p: Promotion, now: datetime) -> PromotionOut:
    prices = _current_prices(db, p.branch_id, [i.menu_item_id for i in p.items])
    names = dict(db.execute(select(MenuItem.id, MenuItem.name).where(
        MenuItem.id.in_([i.menu_item_id for i in p.items]))).all())
    items = []
    for i in sorted(p.items, key=lambda x: x.menu_item_id):
        current = prices.get(i.menu_item_id, (None, 0))[1]
        pct = round((current - i.promo_price) * 100 / current) if current > i.promo_price else 0
        items.append(PromotionItemOut(menu_item_id=i.menu_item_id, name=names.get(i.menu_item_id, "?"),
                                      current_price=current, promo_price=i.promo_price, discount_percent=pct))
    branch = db.get(Branch, p.branch_id) if p.branch_id else None
    creator = db.get(Staff, p.created_by)
    return PromotionOut(
        id=p.id, name=p.name, description=p.description, branch_id=p.branch_id,
        branch_name=branch.name if branch else None, start_at=p.start_at, end_at=p.end_at, is_active=p.is_active,
        status=promo_status(p, now), created_by=creator.full_name if creator else "?", items=items,
    )


def _invalid(message: str, errors: list[dict]) -> AppError:
    return AppError(422, "PROMOTION_INVALID", message, {"errors": errors})


def _validate(db: Session, body: PromotionIn, now: datetime) -> None:
    if body.end_at <= body.start_at:
        raise _invalid("Thời gian kết thúc phải sau thời gian bắt đầu", [{"field": "end_at"}])
    if body.end_at <= now:
        raise _invalid("Thời gian kết thúc đã qua, chương trình sẽ không có hiệu lực", [{"field": "end_at"}])
    if body.branch_id is not None:
        b = db.get(Branch, body.branch_id)
        if b is None:
            raise AppError(404, "BRANCH_NOT_FOUND", "Chi nhánh không tồn tại")
    prices = _current_prices(db, body.branch_id, [i.menu_item_id for i in body.items])
    errors = []
    for it in body.items:
        if it.menu_item_id not in prices:
            errors.append({"menu_item_id": it.menu_item_id, "message": "Món không tồn tại hoặc đã bị xóa"})
            continue
        name, current = prices[it.menu_item_id]
        if it.promo_price >= current:
            errors.append({"menu_item_id": it.menu_item_id, "current_price": current,
                           "message": f"Giá KM của '{name}' phải nhỏ hơn giá bán hiện tại {current:,}đ".replace(",", ".")})
    if errors:
        raise _invalid(errors[0]["message"], errors)


def _publish(background: BackgroundTasks, *branch_ids: int | None) -> None:
    targets = set(branch_ids)
    if None in targets:
        publish_menu_updated(background, None, "PROMOTION")
        return
    for b in targets:
        publish_menu_updated(background, b, "PROMOTION")


@router.get("/promotions", response_model=list[PromotionOut])
def list_promotions(
    status_: PromoStatus | None = Query(None, alias="status"),
    branch_id: int | None = Query(None, description="KM áp dụng tại chi nhánh này (gồm cả KM toàn chuỗi)"),
    _: Staff = Depends(require_roles(*ADMIN)),
    db: Session = Depends(get_db),
):
    now = _now()
    q = select(Promotion)
    if status_ == "running":
        q = q.where(Promotion.start_at <= now, Promotion.end_at >= now).order_by(Promotion.end_at)
    elif status_ == "upcoming":
        q = q.where(Promotion.start_at > now).order_by(Promotion.start_at)
    elif status_ == "ended":
        q = q.where(Promotion.end_at < now).order_by(Promotion.end_at.desc())
    else:
        q = q.order_by(Promotion.start_at.desc())
    if branch_id is not None:
        q = q.where(or_(Promotion.branch_id.is_(None), Promotion.branch_id == branch_id))
    return [_out(db, p, now) for p in db.scalars(q.order_by(Promotion.id))]


@router.get("/promotions/{promotion_id}", response_model=PromotionOut)
def get_promotion(promotion_id: int, _: Staff = Depends(require_roles(*ADMIN)), db: Session = Depends(get_db)):
    p = get_or_404(db, Promotion, promotion_id, "PROMOTION_NOT_FOUND", "Chương trình khuyến mãi không tồn tại")
    return _out(db, p, _now())


@router.post("/promotions", response_model=PromotionOut, status_code=status.HTTP_201_CREATED)
def create_promotion(body: PromotionIn, background: BackgroundTasks, admin: Staff = Depends(require_roles(*ADMIN)),
                     db: Session = Depends(get_db)):
    now = _now()
    _validate(db, body, now)
    p = Promotion(
        name=body.name, description=body.description, branch_id=body.branch_id, start_at=body.start_at,
        end_at=body.end_at, is_active=body.is_active, created_by=admin.id,
        items=[PromotionItem(menu_item_id=i.menu_item_id, promo_price=i.promo_price) for i in body.items],
    )
    db.add(p)
    db.commit()
    _publish(background, p.branch_id)
    return _out(db, p, now)


@router.put("/promotions/{promotion_id}", response_model=PromotionOut)
def update_promotion(promotion_id: int, body: PromotionIn, background: BackgroundTasks,
                     _: Staff = Depends(require_roles(*ADMIN)), db: Session = Depends(get_db)):
    now = _now()
    # Khóa dòng: 2 người sửa cùng lúc thì lần lượt, danh sách món không bị trộn
    p = get_or_404(db, Promotion, promotion_id, "PROMOTION_NOT_FOUND", "Chương trình khuyến mãi không tồn tại",
                   lock=True)
    if promo_status(p, now) == "ended":
        raise AppError(409, "PROMOTION_ENDED", "Chương trình đã kết thúc, không sửa được (giữ đúng lịch sử)")
    _validate(db, body, now)
    old_branch = p.branch_id
    p.name, p.description, p.branch_id = body.name, body.description, body.branch_id
    p.start_at, p.end_at, p.is_active = body.start_at, body.end_at, body.is_active
    new_prices = {i.menu_item_id: i.promo_price for i in body.items}
    p.items = [i for i in p.items if i.menu_item_id in new_prices]
    for i in p.items:
        i.promo_price = new_prices.pop(i.menu_item_id)
    db.flush()
    p.items.extend(PromotionItem(menu_item_id=k, promo_price=v) for k, v in new_prices.items())
    db.commit()
    _publish(background, old_branch, p.branch_id)
    return _out(db, p, now)
