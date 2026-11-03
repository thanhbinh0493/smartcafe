"""Đánh giá offline mô hình gợi ý món (II.2 Mục 2.5).

Chia đơn đã hoàn tất theo thời gian: 80% đầu để "học" (bán chạy, sở thích, luật kết hợp), 20% sau để kiểm tra.
Với mỗi đơn kiểm tra: ẩn ngẫu nhiên 1 món, các món còn lại coi là giỏ hàng, gợi ý tại đúng thời điểm đơn được
thanh toán (chỉ dùng dữ liệu trước thời điểm đó) rồi xem món bị ẩn có nằm trong top 5 không → Hit Rate@5.
So sánh: chỉ Bán chạy (baseline), công thức ẩn danh, công thức thành viên (trên đơn của thành viên).
Thêm: "Thường gọi kèm" Hit Rate@2 trên đơn có ≥ 2 món. Chạy trong 1 giao dịch rồi rollback (không đổi dữ liệu).

    python -m scripts.evaluate_recommender [--limit 600] [--seed 7]
"""
import argparse
import random
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models import Branch, Order, OrderItem
from app.modules.recommend.service import recommend
from app.modules.recommend.training import rebuild_rules
from app.modules.recommend.weather import Weather

WEATHER = Weather(31.0, "mock")


@dataclass
class Score:
    hits: int = 0
    total: int = 0

    @property
    def rate(self) -> float:
        return self.hits / self.total if self.total else 0.0

    def add(self, hit: bool) -> None:
        self.total += 1
        self.hits += int(hit)


@dataclass
class Report:
    train_orders: int
    test_orders: int
    split_at: str
    scores: dict[str, Score] = field(default_factory=dict)
    rules: int = 0


def evaluate(db: Session, limit: int | None = None, seed: int = 7) -> Report:
    rng = random.Random(seed)
    orders = db.execute(
        select(Order.id, Order.branch_id, Order.customer_id, Order.paid_at)
        .where(Order.status == "COMPLETED").order_by(Order.paid_at)
    ).all()
    if len(orders) < 50:
        raise SystemExit("Cần ít nhất 50 đơn hoàn tất (chạy scripts.seed_orders trước).")
    cut = int(len(orders) * 0.8)
    split_at = orders[cut].paid_at
    test = orders[cut:]
    if limit and len(test) > limit:
        test = rng.sample(test, limit)
    baskets: dict[int, list[int]] = {}
    for oid, mid in db.execute(select(OrderItem.order_id, OrderItem.menu_item_id)
                               .where(OrderItem.order_id.in_([o.id for o in test]))):
        baskets.setdefault(oid, []).append(mid)

    rep = Report(train_orders=cut, test_orders=len(test), split_at=split_at.isoformat(timespec="minutes"))
    rep.rules = sum(rebuild_rules(db, split_at).values())  # luật chỉ học từ phần train
    branches = {b.id: b for b in db.scalars(select(Branch))}
    keys = ["POPULAR (tất cả đơn)", "ẨN DANH (tất cả đơn)", "POPULAR (đơn thành viên)",
            "ẨN DANH (đơn thành viên)", "THÀNH VIÊN (đơn thành viên)", "THƯỜNG GỌI KÈM @2 (đơn ≥ 2 món)"]
    rep.scores = {k: Score() for k in keys}
    for o in test:
        items = list(dict.fromkeys(baskets.get(o.id, [])))
        if not items:
            continue
        hidden = rng.choice(items)
        cart = [i for i in items if i != hidden]
        b = branches[o.branch_id]

        def hit(mode: str, customer_id=None) -> bool:
            res = recommend(db, b, customer_id, cart, now=o.paid_at, weather=WEATHER, mode=mode)
            return hidden in [r.item.id for r in res.items]

        pop, anon = hit("POPULAR"), hit("ANONYMOUS")
        rep.scores[keys[0]].add(pop)
        rep.scores[keys[1]].add(anon)
        if o.customer_id:
            rep.scores[keys[2]].add(pop)
            rep.scores[keys[3]].add(anon)
            res = recommend(db, b, o.customer_id, cart, now=o.paid_at, weather=WEATHER)
            rep.scores[keys[4]].add(hidden in [r.item.id for r in res.items])
        if cart:
            res = recommend(db, b, None, cart, now=o.paid_at, weather=WEATHER, mode="ANONYMOUS")
            rep.scores[keys[5]].add(hidden in [r.item.id for r in res.also_bought])
    return rep


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="số đơn kiểm tra tối đa (lấy mẫu ngẫu nhiên)")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    with SessionLocal() as db:
        try:
            rep = evaluate(db, a.limit, a.seed)
        finally:
            db.rollback()
    print(f"Đơn train: {rep.train_orders} | đơn kiểm tra: {rep.test_orders} | mốc chia: {rep.split_at} | "
          f"luật học từ train: {rep.rules}")
    print(f"{'Cấu hình':<36} {'Số đơn':>7} {'Trúng':>6} {'Hit Rate':>9}")
    for k, s in rep.scores.items():
        print(f"{k:<36} {s.total:>7} {s.hits:>6} {s.rate:>8.1%}")


if __name__ == "__main__":
    main()
