"""Gợi ý món theo 2 chế độ + "Thường gọi kèm" (UC03, SD02, II.2 Mục 2.3).

Mọi thành phần chuẩn hóa về 0..1, chỉ xét món còn bán tại chi nhánh:
    Ẩn danh:    0.45 Popular + 0.25 Promo + 0.20 New + 0.10 Weather
    Thành viên: 0.40 Personal + 0.20 Similar + 0.15 Popular + 0.15 Promo + 0.10 Weather
- Popular  = số lượng bán 7 ngày tại chi nhánh / số lượng của món bán chạy nhất.
- Promo    = mức giảm / 50%, tối đa 1 (chỉ khi KM thật sự rẻ hơn – D27).
- New      = 1 nếu món tạo trong 30 ngày (D16).
- Weather  = 1 hợp trời, 0,5 trung tính / BOTH / NONE, 0 ngược (weather.py).
- Personal = tổng số lượng khách đã gọi, mỗi đơn nhân 0,5^(tuổi đơn / 30 ngày), chia cho món cao nhất.
- Similar  = Jaccard lớn nhất giữa tags của món và tags của 3 món khách gọi nhiều nhất (không so món với chính nó).
  Nhãn "Giống món bạn thích" chỉ dành cho món khách chưa từng gọi; món đã gọi thì là "Bạn hay gọi".
Thành viên chưa có đơn nào → dùng công thức ẩn danh. Top 5 có tối đa 2 món "Bạn hay gọi".
Lý do hiển thị = thành phần đóng góp nhiều điểm nhất. Món đã có trong giỏ không gợi ý lại.
"""
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.core import cache
from app.core.config import get_settings
from app.models import AssociationRule, Branch, Order, OrderItem
from app.modules.menu.service import PricedItem, cached_branch_menu, get_branch_menu
from app.modules.recommend.weather import Weather, get_weather, weather_score

TOP_N = 5
MAX_PERSONAL = 2
CO_BUY_N = 2

WEIGHTS: dict[str, dict[str, float]] = {
    "ANONYMOUS": {"popular": 0.45, "promo": 0.25, "new": 0.20, "weather": 0.10},
    "MEMBER": {"personal": 0.40, "similar": 0.20, "popular": 0.15, "promo": 0.15, "weather": 0.10},
    "POPULAR": {"popular": 1.0},  # baseline cho đánh giá offline (II.2 Mục 2.5)
}


@dataclass
class Rec:
    item: PricedItem
    score: float
    reason_code: str
    reason: str
    components: dict[str, float] = field(default_factory=dict)


@dataclass
class Result:
    mode: str                     # ANONYMOUS | MEMBER (công thức đã dùng)
    items: list[Rec]
    also_bought: list[Rec]
    weather: Weather
    member_fallback: bool = False  # thành viên chưa có lịch sử → công thức ẩn danh


# ---------- Thành phần điểm (hàm thuần, dễ kiểm thử) ----------
def promo_score(regular: int, sell: int) -> float:
    if regular <= 0 or sell >= regular:
        return 0.0
    return min(1.0, (regular - sell) / regular / 0.5)


def jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def normalize(values: dict[int, float]) -> dict[int, float]:
    top = max(values.values(), default=0)
    return {k: v / top for k, v in values.items()} if top > 0 else {}


def reason_text(code: str, item: PricedItem, w: Weather) -> str:
    if code == "PROMO":
        return f"Đang giảm {round((item.regular_price - item.sell_price) * 100 / item.regular_price)}%"
    if code == "WEATHER":
        return {"HOT": "Hợp trời nóng", "COLD": "Hợp trời lạnh"}.get(w.kind, "Gợi ý hôm nay")
    return {"PERSONAL": "Bạn hay gọi", "SIMILAR": "Giống món bạn thích", "POPULAR": "Bán chạy tại chi nhánh",
            "NEW": "Món mới"}[code]


def rank(candidates: list[PricedItem], comps: dict[int, dict[str, float]], mode: str, w: Weather,
         top_n: int = TOP_N) -> list[Rec]:
    weights = WEIGHTS[mode]
    recs = []
    for it in candidates:
        c = comps.get(it.id, {})
        contrib = {k: weights[k] * c.get(k, 0.0) for k in weights}
        score = sum(contrib.values())
        # Lý do: thành phần đóng góp nhiều nhất; bằng nhau thì theo thứ tự trọng số (II.2)
        code = max(weights, key=lambda k: (contrib[k], weights[k])).upper()
        if code == "SIMILAR" and c.get("personal", 0) > 0:
            code = "PERSONAL"  # món khách đã gọi: "Bạn hay gọi" đúng hơn "Giống món bạn thích"
        recs.append(Rec(it, round(score, 4), code, reason_text(code, it, w), {k: round(v, 4) for k, v in c.items()}))
    recs.sort(key=lambda r: (-r.score, -r.components.get("popular", 0), r.item.id))
    out, personal = [], 0
    for r in recs:
        if r.reason_code == "PERSONAL":
            if personal >= MAX_PERSONAL:
                continue  # đa dạng: luôn còn chỗ cho món khách chưa thử
            personal += 1
        out.append(r)
        if len(out) == top_n:
            break
    return out


# ---------- Dữ liệu ----------
def _sold(db: Session):
    """Đơn đã thanh toán, không tính đơn hủy."""
    return and_(Order.paid_at.is_not(None), Order.status != "CANCELLED")


def popular_counts(db: Session, branch_id: int, now: datetime, days: int | None = None) -> dict[int, float]:
    days = days or get_settings().rec_popular_days
    rows = db.execute(
        select(OrderItem.menu_item_id, func.sum(OrderItem.quantity))
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.branch_id == branch_id, _sold(db), Order.paid_at >= now - timedelta(days=days), Order.paid_at < now)
        .group_by(OrderItem.menu_item_id)
    )
    return {mid: float(q) for mid, q in rows}


def personal_counts(db: Session, customer_id: int, now: datetime) -> dict[int, float]:
    """Mọi chi nhánh (khách đổi chi nhánh vẫn giữ sở thích), đơn gần đây nặng hơn."""
    half = get_settings().rec_personal_half_life_days
    rows = db.execute(
        select(OrderItem.menu_item_id, OrderItem.quantity, Order.paid_at)
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.customer_id == customer_id, _sold(db), Order.paid_at < now)
    )
    out: dict[int, float] = defaultdict(float)
    for mid, qty, paid in rows:
        age = max(0.0, (now - paid).total_seconds() / 86400)
        out[mid] += qty * 0.5 ** (age / half)
    return dict(out)


def components(menu: list[PricedItem], popular: dict[int, float], personal: dict[int, float] | None,
               w: Weather) -> dict[int, dict[str, float]]:
    pop = normalize(popular)
    comps = {
        it.id: {"popular": pop.get(it.id, 0.0), "promo": promo_score(it.regular_price, it.sell_price),
                "new": 1.0 if it.is_new else 0.0, "weather": weather_score(it.temperature_type, w)}
        for it in menu
    }
    if personal:
        pers = normalize(personal)
        tags = {it.id: set(it.tags) for it in menu}
        favorites = sorted(personal, key=lambda k: (-personal[k], k))[:3]
        for it in menu:
            comps[it.id]["personal"] = pers.get(it.id, 0.0)
            comps[it.id]["similar"] = max(
                (jaccard(tags[it.id], tags[f]) for f in favorites if f in tags and f != it.id), default=0.0)
    return comps


def co_buy(db: Session, branch_id: int, cart: list[int], menu: dict[int, PricedItem], w: Weather,
           top_n: int = CO_BUY_N) -> list[Rec]:
    """"Thường gọi kèm": luật antecedent ∈ giỏ, sắp theo confidence × lift, bỏ món đã có trong giỏ / tạm hết.
    Ưu tiên luật của chi nhánh; luật toàn chuỗi dùng khi chi nhánh chưa có luật cho cặp món đó."""
    if not cart:
        return []
    rules = [r for r in branch_rules(db, branch_id) if r.antecedent_id in cart]
    best: dict[int, tuple[bool, float, AssociationRule]] = {}
    for r in rules:
        it = menu.get(r.consequent_id)
        if it is None or not it.is_available or r.consequent_id in cart:
            continue
        key = (r.branch_id is not None, float(r.confidence) * float(r.lift))
        cur = best.get(r.consequent_id)
        if cur is None or key > cur[:2]:
            best[r.consequent_id] = (*key, r)
    picked = sorted(best.values(), key=lambda x: (-x[0], -x[1], x[2].consequent_id))[:top_n]
    out = []
    for _, s, r in picked:
        ante = menu.get(r.antecedent_id)
        reason = f"Thường gọi kèm {ante.name}" if ante else "Thường gọi kèm"
        out.append(Rec(menu[r.consequent_id], round(s, 4), "CO_BUY", reason,
                       {"confidence": float(r.confidence), "lift": float(r.lift)}))
    return out


POPULAR_TTL = 60.0   # số liệu bán chạy 30 ngày: trễ tối đa 1 phút là chấp nhận được (D38)
RULES_TTL = 600.0    # luật chỉ đổi khi học lại (00:30) – rebuild_rules xóa cache


@dataclass(frozen=True)
class RuleRow:
    branch_id: int | None
    antecedent_id: int
    consequent_id: int
    confidence: float
    lift: float


def branch_rules(db: Session, branch_id: int) -> list[RuleRow]:
    """Luật của chi nhánh + luật toàn chuỗi (cache tới lần học lại)."""
    def load():
        rows = db.scalars(select(AssociationRule).where(
            or_(AssociationRule.branch_id == branch_id, AssociationRule.branch_id.is_(None)))).all()
        return [RuleRow(r.branch_id, r.antecedent_id, r.consequent_id, float(r.confidence), float(r.lift))
                for r in rows], RULES_TTL
    return cache.get("rules", branch_id, load)


def recommend(db: Session, branch: Branch, customer_id: int | None = None, cart: list[int] | None = None,
              now: datetime | None = None, weather: Weather | None = None, mode: str | None = None) -> Result:
    live = now is None            # gọi từ API: dùng cache; test truyền `now` cố định thì tính trực tiếp
    now = now or datetime.now(timezone.utc)
    cart = cart or []
    w = weather or get_weather(branch.id, float(branch.latitude) if branch.latitude is not None else None,
                               float(branch.longitude) if branch.longitude is not None else None)
    menu = cached_branch_menu(db, branch.id) if live else get_branch_menu(db, branch.id)
    menu_by_id = {it.id: it for it in menu}
    candidates = [it for it in menu if it.is_available and it.id not in cart]

    personal = personal_counts(db, customer_id, now) if customer_id else {}
    fallback = bool(customer_id) and not personal
    if mode is None:
        mode = "MEMBER" if personal else "ANONYMOUS"
    popular = (cache.get("popular", branch.id, lambda: (popular_counts(db, branch.id, now), POPULAR_TTL)) if live
               else popular_counts(db, branch.id, now))
    comps = components(menu, popular, personal or None, w)
    return Result(mode=mode, items=rank(candidates, comps, mode, w), also_bought=co_buy(db, branch.id, cart, menu_by_id, w),
                  weather=w, member_fallback=fallback)
