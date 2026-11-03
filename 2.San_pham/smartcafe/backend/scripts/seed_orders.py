"""Sinh đơn lịch sử + khách thành viên cho AI gợi ý (F7) và dashboard (F8) – II.2 Mục 2.4, D32.

Mặc định: 60 ngày trước hôm nay, 3 chi nhánh, ~5.000 đơn, 300 khách thành viên (~40% đơn). Quy luật cài sẵn
để mô hình học lại được (có nhiễu ngẫu nhiên):
- mỗi thành viên có 1 chi nhánh quen (80% đơn) và 2–3 món "ruột" (70% món chính chọn trong số đó);
- "Cà phê sữa đá / nóng" hay đi kèm "Bánh croissant bơ"; "Trà đào cam sả" kèm "Bánh mousse chanh dây";
  "Matcha đá xay" kèm "Bánh phô mai nướng";
- ngày nóng (≥ 28°C) bán nhiều đồ lạnh (trà, đá xay, nước ép), ngày mát bán nhiều đồ nóng.
Khách demo **0901000001** (chi nhánh Cầu Giấy) hay gọi Cà phê sữa đá, Bạc xỉu, Bánh croissant bơ.

    python -m scripts.seed_orders            # nạp (bỏ qua nếu đã nạp – đã có khách demo)
    python -m scripts.seed_orders --if-empty # như trên, dùng trong start.sh
"""
import argparse
import random
import secrets
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func, insert, select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models import (
    Branch, BranchMenuItem, Customer, DiningTable, LoyaltyTransaction, MenuItem, Order, OrderItem,
    OrderStatusHistory, Payment, Staff,
)
from app.modules.recommend.training import rebuild_rules
from app.modules.report.service import catch_up

VN = ZoneInfo("Asia/Ho_Chi_Minh")
DEMO_PHONE = "0901000001"
DEMO_FAVORITES = ["Cà phê sữa đá", "Bạc xỉu", "Bánh croissant bơ"]
CO_BUY = {  # món chính -> (món kèm, xác suất)
    "Cà phê sữa đá": ("Bánh croissant bơ", 0.45),
    "Cà phê sữa nóng": ("Bánh croissant bơ", 0.45),
    "Trà đào cam sả": ("Bánh mousse chanh dây", 0.35),
    "Matcha đá xay": ("Bánh phô mai nướng", 0.30),
}
COLD_CATS = ("Trà", "Đá xay", "Nước ép & Sinh tố")


@dataclass
class Params:
    days: int = 60
    orders_per_day: int = 28      # mỗi chi nhánh → ~5.000 đơn / 60 ngày / 3 chi nhánh
    members: int = 300
    member_ratio: float = 0.4
    cancel_ratio: float = 0.04
    recommended_ratio: float = 0.12
    seed: int = 2026


def already_seeded(db: Session) -> bool:
    return db.scalar(select(Customer.id).where(Customer.phone == DEMO_PHONE)) is not None


def _menu(db: Session):
    rows = db.execute(select(MenuItem).where(MenuItem.is_deleted.is_(False), MenuItem.is_active.is_(True))).scalars().all()
    cat_of = {m.id: m.category.name for m in rows}
    return rows, cat_of


def seed_orders(db: Session, now: datetime | None = None, p: Params | None = None) -> dict[str, int]:
    p = p or Params()
    rng = random.Random(p.seed)
    now = now or datetime.now(timezone.utc)
    today = now.astimezone(VN).date()
    items, cat_of = _menu(db)
    by_name = {m.name: m for m in items}
    mains = [m for m in items if cat_of[m.id] != "Bánh"]
    created_of = {m.id: m.created_at for m in items}
    cakes = [m for m in items if cat_of[m.id] == "Bánh"]
    branches = db.scalars(select(Branch).where(Branch.is_active.is_(True)).order_by(Branch.id)).all()
    tables = defaultdict(list)
    for t in db.scalars(select(DiningTable).where(DiningTable.is_active.is_(True))):
        tables[t.branch_id].append(t.id)
    overrides = {(b, m): pr for b, m, pr in db.execute(
        select(BranchMenuItem.branch_id, BranchMenuItem.menu_item_id, BranchMenuItem.price_override)) if pr is not None}
    baristas = defaultdict(list)
    for s in db.scalars(select(Staff).where(Staff.role == "BARISTA")):
        baristas[s.branch_id].append(s.id)

    # Khách thành viên: chi nhánh quen + 2–3 món ruột
    created = now - timedelta(days=p.days + 1)
    customers = []
    for i in range(1, p.members + 1):
        phone = f"0901{i:06d}"
        if i == 1:
            fav = [by_name[n].id for n in DEMO_FAVORITES if n in by_name]
            home = branches[0].id
        else:
            fav = [m.id for m in rng.sample(mains, rng.choice((2, 3)))]
            home = rng.choice(branches).id
        customers.append({"phone": phone, "created_at": created, "last_verified_at": created, "fav": fav, "home": home})
    ids = _bulk_returning(db, Customer, [{k: c[k] for k in ("phone", "created_at", "last_verified_at")}
                                         for c in customers], Customer.phone)
    for c in customers:
        c["id"] = ids[c["phone"]]

    # Số thứ tự mã đơn tiếp nối đơn đã có trong ngày (D28)
    seq = defaultdict(int, {(b, d): n for b, d, n in db.execute(
        select(Order.branch_id, Order.order_date, func.count()).group_by(Order.branch_id, Order.order_date))})

    orders, lines_by_order, points = [], [], defaultdict(int)
    for day_back in range(p.days, 0, -1):
        d: date = today - timedelta(days=day_back)
        temp = rng.uniform(20, 35)            # nhiệt độ giả lập của ngày
        hot = temp >= 28
        for b in branches:
            n = max(1, int(rng.gauss(p.orders_per_day, p.orders_per_day * 0.15)))
            # Khách demo có lịch sử đều đặn (~1 đơn / 2 ngày ở chi nhánh quen) để demo chế độ thành viên
            demo = customers[0]
            slots = [None] * n + ([demo] if b.id == demo["home"] and rng.random() < 0.5 else [])
            for forced in slots:
                member = forced
                if forced is None and rng.random() < p.member_ratio:
                    member = rng.choice(customers)
                    if member["home"] != b.id and rng.random() < 0.8:
                        # 80% đơn của khách ở chi nhánh quen: đổi sang khách khác của chi nhánh này
                        local = [c for c in customers if c["home"] == b.id]
                        member = rng.choice(local) if local else member
                if forced is None and member and member["phone"] == DEMO_PHONE:
                    member = None  # đơn của khách demo chỉ sinh theo lịch ở trên
                paid_local = datetime.combine(d, time(7, 0), VN) + timedelta(seconds=rng.randint(0, 15 * 3600))
                paid = paid_local.astimezone(timezone.utc)
                # Chỉ bán món đã có vào ngày đó (món mới tạo 5 ngày trước không có trong đơn cũ hơn)
                day_mains = [m for m in mains if m.created_at <= paid] or mains
                day_cakes = [m for m in cakes if m.created_at <= paid]
                fav = [f for f in member["fav"] if created_of[f] <= paid] if member else []
                basket = _basket(rng, {**member, "fav": fav} if fav else None, day_mains, day_cakes, by_name,
                                 cat_of, hot, paid)
                seq[(b.id, d)] += 1
                cancelled = rng.random() < p.cancel_ratio
                lines = []
                for mid in basket:
                    price = overrides.get((b.id, mid), next(m.base_price for m in items if m.id == mid))
                    lines.append({"menu_item_id": mid, "quantity": 2 if rng.random() < 0.15 else 1,
                                  "original_price": price, "unit_price": price,
                                  "status": "CANCELLED" if cancelled else "DONE",
                                  "is_recommended": rng.random() < p.recommended_ratio})
                total = sum(l["unit_price"] * l["quantity"] for l in lines)
                ready = paid + timedelta(seconds=rng.randint(180, 720))
                done = ready + timedelta(seconds=rng.randint(30, 240))
                staff = rng.choice(baristas[b.id]) if baristas[b.id] else None
                orders.append({
                    "order_code": f"{b.code}-{seq[(b.id, d)]:04d}", "order_date": d,
                    "access_token": secrets.token_urlsafe(16), "branch_id": b.id,
                    "table_id": rng.choice(tables[b.id]), "customer_id": member["id"] if member else None,
                    "status": "CANCELLED" if cancelled else "COMPLETED", "total_amount": total,
                    "created_at": paid - timedelta(seconds=40), "paid_at": paid,
                    "ready_at": None if cancelled else ready, "completed_at": None if cancelled else done,
                    "cancelled_at": paid + timedelta(seconds=120) if cancelled else None,
                    "cancel_reason": "Khách đổi ý" if cancelled else None,
                    "completed_by": None if cancelled else staff,
                })
                for l in lines:
                    l["started_at"] = None if cancelled else paid + timedelta(seconds=60)
                    l["done_at"] = None if cancelled else ready
                lines_by_order.append(lines)

    by_token = _bulk_returning(db, Order, orders, Order.access_token)
    order_ids = [by_token[o["access_token"]] for o in orders]
    item_rows, hist, pays, loyalty = [], [], [], []
    for oid, o, lines in zip(order_ids, orders, lines_by_order):
        item_rows += [{**l, "order_id": oid} for l in lines]
        steps = [(None, "PENDING_PAYMENT", "CUSTOMER", o["created_at"]), ("PENDING_PAYMENT", "PAID", "CUSTOMER", o["paid_at"])]
        if o["status"] == "CANCELLED":
            steps.append(("PAID", "CANCELLED", "STAFF", o["cancelled_at"]))
        else:
            steps += [("PAID", "PREPARING", "STAFF", o["paid_at"] + timedelta(seconds=60)),
                      ("PREPARING", "READY", "STAFF", o["ready_at"]), ("READY", "COMPLETED", "STAFF", o["completed_at"])]
        hist += [{"order_id": oid, "from_status": f, "to_status": t, "source": s, "created_at": at} for f, t, s, at in steps]
        pays.append({"order_id": oid, "method": "MOCK_EWALLET", "amount": o["total_amount"],
                     "status": "REFUNDED" if o["status"] == "CANCELLED" else "SUCCESS",
                     "transaction_ref": f"SEED-{oid}-{secrets.token_hex(4)}", "paid_at": o["paid_at"],
                     "refunded_at": o["cancelled_at"]})
        if o["customer_id"] and o["status"] == "COMPLETED" and o["total_amount"] // 10_000 > 0:
            pts = o["total_amount"] // 10_000           # D15: 1 điểm / 10.000đ
            points[o["customer_id"]] += pts
            loyalty.append({"customer_id": o["customer_id"], "order_id": oid, "points": pts, "type": "EARN",
                            "created_at": o["completed_at"]})
    for table, rows in ((OrderItem, item_rows), (OrderStatusHistory, hist), (Payment, pays), (LoyaltyTransaction, loyalty)):
        _bulk(db, table, rows)
    for cid, pts in points.items():
        db.get(Customer, cid).loyalty_points = pts
    db.flush()
    rules = rebuild_rules(db, now)
    reports = catch_up(db, now, days=p.days)  # IV.1 Mục 7: dashboard có sẵn số liệu các ngày lịch sử
    return {"customers": len(customers), "orders": len(orders), "order_items": len(item_rows),
            "rules": sum(rules.values()), "daily_reports": reports}


CHUNK = 1000


def _bulk(db: Session, table, rows: list[dict]) -> None:
    """INSERT nhiều dòng trong 1 câu lệnh (VALUES (...), (...)) theo lô 1.000 dòng: Postgres chạy trong Docker
    nên mỗi lượt gọi tốn vài ms – ghi từng dòng (executemany) 35.000 dòng mất ~4 phút, theo lô chỉ vài giây."""
    for i in range(0, len(rows), CHUNK):
        db.execute(insert(table).values(rows[i:i + CHUNK]))


def _bulk_returning(db: Session, model, rows: list[dict], key) -> dict:
    """Như _bulk, trả {giá trị cột khóa duy nhất: id} (không dựa vào thứ tự dòng RETURNING)."""
    ids: dict = {}
    for i in range(0, len(rows), CHUNK):
        ids.update(db.execute(insert(model).values(rows[i:i + CHUNK]).returning(key, model.id)).tuples().all())
    return ids


def _basket(rng, member, mains, cakes, by_name, cat_of, hot: bool, paid: datetime) -> list[int]:
    """1–3 món: 1 món chính (+ có thể 1 món chính nữa), món kèm theo quy luật, đôi khi 1 bánh ngẫu nhiên."""
    def pick_main() -> int:
        if member and rng.random() < 0.7:
            return rng.choice(member["fav"])
        weights = []
        for m in mains:
            cold = m.temperature_type == "COLD" or cat_of[m.id] in COLD_CATS
            w = 1.0
            if hot:
                w = 2.2 if cold else (0.4 if m.temperature_type == "HOT" else 1.0)
            elif m.temperature_type == "HOT":
                w = 2.0
            weights.append(w)
        return rng.choices(mains, weights)[0].id

    basket = [pick_main()]
    if rng.random() < 0.25:
        basket.append(pick_main())
    name_of = {m.id: m.name for m in mains + cakes}
    for mid in list(basket):
        rule = CO_BUY.get(name_of.get(mid, ""))
        if rule and rule[0] in by_name and by_name[rule[0]].created_at <= paid and rng.random() < rule[1]:
            basket.append(by_name[rule[0]].id)
    if rng.random() < 0.1 and cakes:
        basket.append(rng.choice(cakes).id)
    return list(dict.fromkeys(basket))  # bỏ trùng, giữ thứ tự


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--if-empty", action="store_true", help="bỏ qua nếu đã nạp (đã có khách demo)")
    ap.parse_args()
    with SessionLocal() as db:
        if already_seeded(db):
            print("[seed_orders] Đã có dữ liệu đơn lịch sử, bỏ qua.")
            return
        if db.scalar(select(func.count()).select_from(Branch)) == 0:
            raise SystemExit("[seed_orders] Chưa có chi nhánh / menu: chạy scripts.seed_data trước.")
        counts = seed_orders(db)
        db.commit()
        print("[seed_orders] Đã nạp:", counts)


if __name__ == "__main__":
    main()
