"""API dashboard bán hàng (UC16, W08) – chỉ đọc `daily_sales_reports`.

GET  /api/staff/reports/daily?branch_id=&from=&to=   ADMIN (mọi chi nhánh / tất cả), MANAGER (chi nhánh mình)
POST /api/staff/reports/daily/rebuild {date, branch_id?}  ADMIN – chạy lại job tổng hợp cho 1 ngày đã kết thúc
Mặc định 7 ngày gần nhất đã kết thúc (đến hôm qua); tối đa 92 ngày.
"""
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import AppError
from app.models import Branch, DailySalesReport, Staff
from app.modules.auth.deps import ensure_branch_access, require_roles
from app.modules.report.service import Kpi, build_day, combine, today_vn, top_items

router = APIRouter(prefix="/api/staff/reports", tags=["report"])
MAX_DAYS = 92


class KpiOut(BaseModel):
    revenue: int
    order_count: int
    cancelled_count: int
    avg_order_value: int
    avg_wait_seconds: int | None
    member_order_ratio: float
    promo_revenue: int
    recommended_item_ratio: float


class SeriesPoint(BaseModel):
    report_date: date
    branch_id: int
    revenue: int
    order_count: int


class BranchRow(BaseModel):
    branch_id: int
    code: str
    name: str
    kpi: KpiOut


class TopItem(BaseModel):
    menu_item_id: int
    name: str
    qty: int


class DashboardOut(BaseModel):
    from_date: date
    to_date: date
    branch_id: int | None            # None = tất cả chi nhánh (chỉ quản trị viên)
    branches: list[BranchRow]        # so sánh chi nhánh tại ngày gần nhất
    latest_date: date | None         # ngày gần nhất có báo cáo trong khoảng
    latest: KpiOut | None
    previous: KpiOut | None          # ngày trước ngày gần nhất (để tính % thay đổi)
    period: KpiOut                   # cộng dồn cả khoảng
    series: list[SeriesPoint]        # doanh thu theo ngày của từng chi nhánh
    top_items: list[TopItem]         # top 5 món của ngày gần nhất
    generated_at: datetime | None    # lần tổng hợp gần nhất


class RebuildIn(BaseModel):
    report_date: date = Field(alias="date")
    branch_id: int | None = None


class RebuildOut(BaseModel):
    report_date: date
    branches: int


def _kpi(k: Kpi) -> KpiOut:
    return KpiOut(**k.__dict__)


@router.get("/daily", response_model=DashboardOut)
def daily(
    branch_id: int | None = None,
    from_: date | None = Query(None, alias="from"),
    to: date | None = None,
    staff: Staff = Depends(require_roles("ADMIN", "MANAGER")),
    db: Session = Depends(get_db),
):
    if staff.role != "ADMIN":
        if branch_id is None:
            branch_id = staff.branch_id          # Quản lý: mặc định và chỉ chi nhánh mình
        ensure_branch_access(staff, branch_id)
    yesterday = today_vn() - timedelta(days=1)
    to = min(to or yesterday, yesterday)         # chỉ gồm các ngày đã kết thúc (UC16)
    from_ = from_ or to - timedelta(days=6)
    if from_ > to:
        raise AppError(422, "VALIDATION_ERROR", "Ngày bắt đầu phải trước ngày kết thúc", {"field": "from"})
    if (to - from_).days + 1 > MAX_DAYS:
        raise AppError(422, "VALIDATION_ERROR", f"Khoảng thời gian tối đa {MAX_DAYS} ngày", {"field": "from"})

    bq = select(Branch).order_by(Branch.id)
    if branch_id is not None:
        if db.get(Branch, branch_id) is None:
            raise AppError(404, "BRANCH_NOT_FOUND", "Chi nhánh không tồn tại")
        bq = bq.where(Branch.id == branch_id)
    branches = db.scalars(bq).all()
    ids = [b.id for b in branches]
    # Lấy thêm 1 ngày trước khoảng để so sánh ngày đầu
    rows = db.scalars(select(DailySalesReport).where(
        DailySalesReport.branch_id.in_(ids),
        DailySalesReport.report_date.between(from_ - timedelta(days=1), to),
    ).order_by(DailySalesReport.report_date, DailySalesReport.branch_id)).all()
    in_range = [r for r in rows if r.report_date >= from_]
    latest_date = max((r.report_date for r in in_range), default=None)
    by_day: dict[date, list[DailySalesReport]] = {}
    for r in rows:
        by_day.setdefault(r.report_date, []).append(r)
    latest_rows = by_day.get(latest_date, []) if latest_date else []
    prev_rows = by_day.get(latest_date - timedelta(days=1), []) if latest_date else []
    code = {b.id: b for b in branches}
    return DashboardOut(
        from_date=from_, to_date=to, branch_id=branch_id,
        branches=[BranchRow(branch_id=r.branch_id, code=code[r.branch_id].code, name=code[r.branch_id].name,
                            kpi=_kpi(combine([r]))) for r in latest_rows],
        latest_date=latest_date,
        latest=_kpi(combine(latest_rows)) if latest_rows else None,
        previous=_kpi(combine(prev_rows)) if prev_rows else None,
        period=_kpi(combine(in_range)),
        series=[SeriesPoint(report_date=r.report_date, branch_id=r.branch_id, revenue=r.revenue,
                            order_count=r.order_count) for r in in_range],
        top_items=[TopItem(**t) for t in top_items(latest_rows)],
        generated_at=db.scalar(select(func.max(DailySalesReport.generated_at))
                               .where(DailySalesReport.branch_id.in_(ids))),
    )


@router.post("/daily/rebuild", response_model=RebuildOut)
def rebuild(body: RebuildIn, _: Staff = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)):
    if body.report_date >= today_vn():
        raise AppError(422, "VALIDATION_ERROR", "Chỉ tính lại được ngày đã kết thúc (trước hôm nay)", {"field": "date"})
    if body.branch_id is not None and db.get(Branch, body.branch_id) is None:
        raise AppError(404, "BRANCH_NOT_FOUND", "Chi nhánh không tồn tại")
    n = build_day(db, body.report_date, body.branch_id)
    db.commit()
    return RebuildOut(report_date=body.report_date, branches=n)
