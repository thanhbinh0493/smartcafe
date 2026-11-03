"""GET /api/public/branches/{id}/recommendations?cart=1,5 (UC03, SD02).

- Customer token tùy chọn. Token sai / hết hạn thì gợi ý như khách ẩn danh (không chặn menu – NFR-R1);
  việc báo hết phiên do API đặt đơn / /me đảm nhiệm như F4.
- Mỗi lần gợi ý ghi 1 dòng recommendation_logs (mode, context, items); trả `log_id` để client gửi kèm khi đặt đơn
  (`recommendation_log_id` – D34).
- Service gợi ý lỗi bất kỳ: trả danh sách rỗng + `degraded: true`, khách vẫn đặt món bình thường (NFR-R1).
"""
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import AppError
from app.models import Branch, RecommendationLog
from app.modules.customer.deps import _customer_from, bearer
from app.modules.recommend import service
from app.modules.recommend.service import Rec

router = APIRouter(prefix="/api/public", tags=["public"])
log = logging.getLogger("smartcafe.recommend")
MAX_CART = 30


class RecItemOut(BaseModel):
    menu_item_id: int
    name: str
    image_url: str | None
    regular_price: int
    sell_price: int
    is_promo: bool
    is_new: bool
    score: float
    reason_code: str
    reason: str


class RecommendationsOut(BaseModel):
    log_id: int | None
    mode: str                 # ANONYMOUS | MEMBER
    member_fallback: bool     # thành viên chưa có lịch sử → công thức ẩn danh
    temp_c: float | None
    weather_source: str | None
    degraded: bool = False
    items: list[RecItemOut]
    also_bought: list[RecItemOut]


def _out(r: Rec) -> RecItemOut:
    it = r.item
    return RecItemOut(menu_item_id=it.id, name=it.name, image_url=it.image_url, regular_price=it.regular_price,
                      sell_price=it.sell_price, is_promo=it.is_promo, is_new=it.is_new, score=r.score,
                      reason_code=r.reason_code, reason=r.reason)


def optional_customer_id(cred: HTTPAuthorizationCredentials | None = Depends(bearer),
                         db: Session = Depends(get_db)) -> int | None:
    if cred is None:
        return None
    try:
        return _customer_from(cred.credentials, db).id
    except AppError:
        return None


def parse_cart(cart: str | None) -> list[int]:
    if not cart:
        return []
    ids = []
    for part in cart.split(","):
        part = part.strip()
        if not part.isdigit():
            raise AppError(422, "VALIDATION_ERROR", "Tham số cart phải là danh sách mã món, VD cart=1,5")
        if int(part) not in ids:
            ids.append(int(part))
    if len(ids) > MAX_CART:
        raise AppError(422, "VALIDATION_ERROR", f"Giỏ hàng tối đa {MAX_CART} món")
    return ids


@router.get("/branches/{branch_id}/recommendations", response_model=RecommendationsOut)
def recommendations(
    branch_id: int,
    cart: str | None = Query(None, max_length=300, description="Mã các món trong giỏ, VD 1,5"),
    customer_id: int | None = Depends(optional_customer_id),
    db: Session = Depends(get_db),
) -> RecommendationsOut:
    branch = db.get(Branch, branch_id)
    if branch is None or not branch.is_active:
        raise AppError(404, "BRANCH_NOT_FOUND", "Chi nhánh không tồn tại hoặc đã ngừng hoạt động")
    cart_ids = parse_cart(cart)
    try:
        res = service.recommend(db, branch, customer_id, cart_ids)
    except Exception:
        log.exception("Gợi ý món lỗi – trả danh sách rỗng (NFR-R1)")
        return RecommendationsOut(log_id=None, mode="MEMBER" if customer_id else "ANONYMOUS", member_fallback=False,
                                  temp_c=None, weather_source=None, degraded=True, items=[], also_bought=[])

    now = datetime.now(timezone.utc)
    entry = RecommendationLog(
        branch_id=branch.id, customer_id=customer_id, mode=res.mode,
        context={"temp_c": res.weather.temp_c, "weather": res.weather.kind, "weather_source": res.weather.source,
                 "hour": now.astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).hour, "cart": cart_ids, "member_fallback": res.member_fallback},
        items=[{"menu_item_id": r.item.id, "score": r.score, "reason": r.reason_code} for r in res.items]
              + [{"menu_item_id": r.item.id, "score": r.score, "reason": "CO_BUY"} for r in res.also_bought],
    )
    db.add(entry)
    db.commit()
    return RecommendationsOut(
        log_id=entry.id, mode=res.mode, member_fallback=res.member_fallback, temp_c=res.weather.temp_c,
        weather_source=res.weather.source, items=[_out(r) for r in res.items],
        also_bought=[_out(r) for r in res.also_bought],
    )
