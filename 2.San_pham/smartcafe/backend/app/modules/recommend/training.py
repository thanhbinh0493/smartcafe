"""Học luật kết hợp "thường gọi kèm" bằng FP-Growth (mlxtend – II.2 Mục 2.4, D33).

- Dữ liệu: các đơn đã thanh toán, không hủy, trong RULES_WINDOW_DAYS ngày (mặc định 60); mỗi đơn = 1 giỏ món.
- Tham số: min_support 0,01; min_confidence 0,2; chỉ giữ lift > 1; luật 1 món → 1 món (bảng association_rules).
- Học riêng từng chi nhánh (branch_id) và toàn chuỗi (branch_id NULL). Thay toàn bộ luật cũ trong 1 giao dịch.
- Chạy hằng đêm bằng APScheduler (scheduler.py) và sau khi nạp dữ liệu mẫu.
"""
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pandas as pd
from mlxtend.frequent_patterns import association_rules, fpgrowth
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core import cache
from app.core.config import get_settings
from app.models import AssociationRule, Branch, Order, OrderItem

log = logging.getLogger("smartcafe.rules")
MIN_TRANSACTIONS = 20  # quá ít đơn thì không học (luật vô nghĩa)


@dataclass(frozen=True)
class MinedRule:
    antecedent_id: int
    consequent_id: int
    support: float
    confidence: float
    lift: float


def mine_rules(baskets: list[set[int]], min_support: float, min_confidence: float) -> list[MinedRule]:
    """FP-Growth trên danh sách giỏ món. Trả luật 1 → 1 có lift > 1."""
    baskets = [b for b in baskets if b]
    if len(baskets) < MIN_TRANSACTIONS:
        return []
    items = sorted({i for b in baskets for i in b})
    df = pd.DataFrame([[i in b for i in items] for b in baskets], columns=items, dtype=bool)
    frequent = fpgrowth(df, min_support=min_support, use_colnames=True, max_len=2)
    if frequent.empty or not (frequent["itemsets"].map(len) == 2).any():
        return []
    rules = association_rules(frequent, metric="confidence", min_threshold=min_confidence)
    out = []
    for _, r in rules.iterrows():
        if len(r["antecedents"]) != 1 or len(r["consequents"]) != 1 or r["lift"] <= 1:
            continue
        out.append(MinedRule(int(next(iter(r["antecedents"]))), int(next(iter(r["consequents"]))),
                             round(float(r["support"]), 4), round(float(r["confidence"]), 4), round(float(r["lift"]), 4)))
    return sorted(out, key=lambda m: (m.antecedent_id, -m.confidence * m.lift, m.consequent_id))


def load_baskets(db: Session, since: datetime, until: datetime) -> dict[int, list[set[int]]]:
    """{branch_id: [giỏ món của từng đơn]}."""
    rows = db.execute(
        select(Order.id, Order.branch_id, OrderItem.menu_item_id)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .where(Order.paid_at.is_not(None), Order.status != "CANCELLED", Order.paid_at >= since, Order.paid_at < until)
    )
    orders: dict[int, tuple[int, set[int]]] = {}
    for oid, bid, mid in rows:
        orders.setdefault(oid, (bid, set()))[1].add(mid)
    by_branch: dict[int, list[set[int]]] = defaultdict(list)
    for bid, basket in orders.values():
        by_branch[bid].append(basket)
    return by_branch


def rebuild_rules(db: Session, now: datetime | None = None) -> dict[str, int]:
    """Học lại toàn bộ luật; trả số luật theo chi nhánh (mã) và 'ALL' (toàn chuỗi). Không commit."""
    s = get_settings()
    now = now or datetime.now(timezone.utc)
    by_branch = load_baskets(db, now - timedelta(days=s.rules_window_days), now)
    codes = dict(db.execute(select(Branch.id, Branch.code)).all())
    db.execute(delete(AssociationRule))
    counts: dict[str, int] = {}
    targets = [(bid, baskets) for bid, baskets in by_branch.items()]
    targets.append((None, [b for baskets in by_branch.values() for b in baskets]))
    for bid, baskets in targets:
        mined = mine_rules(baskets, s.rules_min_support, s.rules_min_confidence)
        db.add_all(AssociationRule(branch_id=bid, antecedent_id=m.antecedent_id, consequent_id=m.consequent_id,
                                   support=m.support, confidence=m.confidence, lift=m.lift, computed_at=now)
                   for m in mined)
        counts["ALL" if bid is None else codes.get(bid, str(bid))] = len(mined)
    db.flush()
    cache.invalidate("rules")
    log.info("Đã học lại luật kết hợp: %s", counts)
    return counts
