"""Báo cáo bán hàng theo ngày (UC16, D21, IV.1 Mục 4.8 + Mục 6).

- `build_daily_report(db, branch_id, d)`: tổng hợp các đơn có `paid_at` thuộc ngày d (giờ Việt Nam) rồi UPSERT vào
  `daily_sales_reports` – chạy lại được cho một ngày bất kỳ. Ngày không có đơn vẫn có 1 dòng toàn số 0 (biểu đồ liền mạch).
- Doanh thu = Σ total_amount các đơn đã thanh toán, không hủy; đơn chưa thanh toán (paid_at NULL) không tính.
- `catch_up`: bù các ngày đã kết thúc còn thiếu báo cáo (laptop demo thường tắt lúc 00:05).
- Dashboard (W08) chỉ đọc bảng này, không có số liệu realtime trong ngày.
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models import Branch, DailySalesReport

VN = ZoneInfo("Asia/Ho_Chi_Minh")
CATCH_UP_DAYS = 60

UPSERT = text("""
INSERT INTO daily_sales_reports (branch_id, report_date, order_count, cancelled_count, revenue, avg_order_value,
                                 avg_wait_seconds, member_order_ratio, promo_revenue, recommended_item_ratio,
                                 top_items, generated_at)
SELECT :branch_id, :d,
       COUNT(*) FILTER (WHERE o.status <> 'CANCELLED'),
       COUNT(*) FILTER (WHERE o.status =  'CANCELLED'),
       COALESCE(SUM(o.total_amount) FILTER (WHERE o.status <> 'CANCELLED'), 0),
       COALESCE(ROUND(AVG(o.total_amount) FILTER (WHERE o.status <> 'CANCELLED')), 0)::INT,
       ROUND(AVG(EXTRACT(EPOCH FROM o.ready_at - o.paid_at)) FILTER (WHERE o.status <> 'CANCELLED'))::INT,
       COALESCE(AVG((o.customer_id IS NOT NULL)::INT) FILTER (WHERE o.status <> 'CANCELLED'), 0),
       (SELECT COALESCE(SUM(oi.quantity * oi.unit_price), 0) FROM order_items oi JOIN orders o2 ON o2.id = oi.order_id
         WHERE o2.branch_id = :branch_id AND o2.status <> 'CANCELLED' AND oi.promotion_id IS NOT NULL
           AND (o2.paid_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::DATE = :d),
       (SELECT COALESCE(AVG(oi.is_recommended::INT), 0) FROM order_items oi JOIN orders o2 ON o2.id = oi.order_id
         WHERE o2.branch_id = :branch_id AND o2.status <> 'CANCELLED'
           AND (o2.paid_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::DATE = :d),
       COALESCE((
         SELECT jsonb_agg(t ORDER BY t.qty DESC, t.name) FROM (
           SELECT oi.menu_item_id, m.name, SUM(oi.quantity)::INT AS qty
           FROM order_items oi JOIN orders o3 ON o3.id = oi.order_id JOIN menu_items m ON m.id = oi.menu_item_id
           WHERE o3.branch_id = :branch_id AND o3.status <> 'CANCELLED'
             AND (o3.paid_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::DATE = :d
           GROUP BY oi.menu_item_id, m.name
           ORDER BY qty DESC, m.name LIMIT 5) t), '[]'::jsonb),
       now()
FROM orders o
WHERE o.branch_id = :branch_id
  AND o.paid_at IS NOT NULL
  AND (o.paid_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::DATE = :d
ON CONFLICT (branch_id, report_date) DO UPDATE
SET order_count = EXCLUDED.order_count, cancelled_count = EXCLUDED.cancelled_count,
    revenue = EXCLUDED.revenue, avg_order_value = EXCLUDED.avg_order_value,
    avg_wait_seconds = EXCLUDED.avg_wait_seconds, member_order_ratio = EXCLUDED.member_order_ratio,
    promo_revenue = EXCLUDED.promo_revenue, recommended_item_ratio = EXCLUDED.recommended_item_ratio,
    top_items = EXCLUDED.top_items, generated_at = now()
""")


def today_vn(now: datetime | None = None) -> date:
    return (now or datetime.now(timezone.utc)).astimezone(VN).date()


def build_daily_report(db: Session, branch_id: int, d: date) -> None:
    db.execute(UPSERT, {"branch_id": branch_id, "d": d})


def build_day(db: Session, d: date, branch_id: int | None = None) -> int:
    """Tổng hợp ngày d cho 1 chi nhánh hoặc mọi chi nhánh. Trả số chi nhánh đã tính. Không commit."""
    ids = [branch_id] if branch_id else db.scalars(select(Branch.id).order_by(Branch.id)).all()
    for bid in ids:
        build_daily_report(db, bid, d)
    return len(ids)


def catch_up(db: Session, now: datetime | None = None, days: int = CATCH_UP_DAYS) -> int:
    """Tính các (chi nhánh, ngày) đã kết thúc trong `days` ngày qua mà chưa có báo cáo. Trả số dòng đã tính."""
    end = today_vn(now) - timedelta(days=1)
    start = end - timedelta(days=days - 1)
    have = set(db.execute(select(DailySalesReport.branch_id, DailySalesReport.report_date)
                          .where(DailySalesReport.report_date.between(start, end))).tuples())
    n = 0
    for bid in db.scalars(select(Branch.id).order_by(Branch.id)).all():
        d = start
        while d <= end:
            if (bid, d) not in have:
                build_daily_report(db, bid, d)
                n += 1
            d += timedelta(days=1)
    return n


# ---------- Đọc cho dashboard ----------
@dataclass
class Kpi:
    revenue: int = 0
    order_count: int = 0
    cancelled_count: int = 0
    avg_order_value: int = 0
    avg_wait_seconds: int | None = None
    member_order_ratio: float = 0.0
    promo_revenue: int = 0
    recommended_item_ratio: float = 0.0


def combine(rows: list[DailySalesReport]) -> Kpi:
    """Gộp nhiều dòng (nhiều chi nhánh / nhiều ngày): cộng tổng; tỉ lệ và thời gian chờ lấy trung bình
    có trọng số theo số đơn (gần đúng cho tỉ lệ món từ gợi ý vì bảng không lưu số dòng món)."""
    k = Kpi()
    if not rows:
        return k
    k.revenue = sum(r.revenue for r in rows)
    k.order_count = sum(r.order_count for r in rows)
    k.cancelled_count = sum(r.cancelled_count for r in rows)
    k.promo_revenue = sum(r.promo_revenue for r in rows)
    if k.order_count:
        k.avg_order_value = round(k.revenue / k.order_count)
        k.member_order_ratio = round(sum(float(r.member_order_ratio) * r.order_count for r in rows) / k.order_count, 4)
        k.recommended_item_ratio = round(
            sum(float(r.recommended_item_ratio) * r.order_count for r in rows) / k.order_count, 4)
        waited = [r for r in rows if r.avg_wait_seconds is not None and r.order_count]
        w = sum(r.order_count for r in waited)
        k.avg_wait_seconds = round(sum(r.avg_wait_seconds * r.order_count for r in waited) / w) if w else None
    return k


def top_items(rows: list[DailySalesReport], n: int = 5) -> list[dict]:
    """Top món của ngày: gộp top 5 từng chi nhánh (gần đúng khi xem 'Tất cả chi nhánh')."""
    acc: dict[int, dict] = {}
    for r in rows:
        for it in r.top_items or []:
            cur = acc.setdefault(it["menu_item_id"], {"menu_item_id": it["menu_item_id"], "name": it["name"], "qty": 0})
            cur["qty"] += it["qty"]
    return sorted(acc.values(), key=lambda x: (-x["qty"], x["name"]))[:n]
