"""F8 – Job tổng hợp báo cáo ngày (UC16, IV.1 Mục 4.8 + 6)."""
import time as _time
from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.models import DailySalesReport, Order
from app.modules.recommend import scheduler as sched_mod
from app.modules.report.service import Kpi, build_day, build_daily_report, catch_up, combine, top_items
from tests.f8.conftest import YESTERDAY, at


def report(db, branch, d=YESTERDAY) -> DailySalesReport:
    db.expire_all()
    return db.get(DailySalesReport, (branch.id, d))


def test_F8_01_tinh_du_chi_so_cua_ngay(db, shop):
    s = shop
    s.order(s.cg, (s.sua_da, 2, 30000), (s.tra_dao, 1, 30000, True, True), paid_at=at(YESTERDAY, 8), wait_s=240,
            member=True)                                                    # 90.000, KM 30.000, 1/2 dòng gợi ý
    s.order(s.cg, (s.banh, 1, 20000), paid_at=at(YESTERDAY, 9), wait_s=480)  # 20.000
    s.order(s.cg, (s.sua_da, 5, 30000), paid_at=at(YESTERDAY, 10), wait_s=None, status="CANCELLED")
    build_daily_report(db, s.cg.id, YESTERDAY)
    r = report(db, s.cg)
    assert (r.order_count, r.cancelled_count, r.revenue, r.avg_order_value) == (2, 1, 110000, 55000)
    assert r.avg_wait_seconds == 360                                         # (240 + 480) / 2
    assert r.member_order_ratio == Decimal("0.5000")
    assert r.promo_revenue == 30000
    assert r.recommended_item_ratio == Decimal("0.3333")                     # 1 / 3 dòng món của đơn không hủy
    assert r.top_items == [{"menu_item_id": s.sua_da.id, "name": "Cà phê sữa đá", "qty": 2},
                           {"menu_item_id": s.banh.id, "name": "Bánh", "qty": 1},
                           {"menu_item_id": s.tra_dao.id, "name": "Trà đào", "qty": 1}]


def test_F8_02_ngay_theo_gio_viet_nam(db, shop):
    s = shop
    s.order(s.cg, (s.sua_da, 1, 30000), paid_at=at(YESTERDAY, 23, 50))       # 16:50 UTC – vẫn là "hôm qua"
    s.order(s.cg, (s.sua_da, 1, 30000), paid_at=at(YESTERDAY, 0, 10))        # 17:10 UTC hôm kia – vẫn là "hôm qua"
    s.order(s.cg, (s.sua_da, 1, 30000), paid_at=at(YESTERDAY - timedelta(days=1), 23, 59))
    build_daily_report(db, s.cg.id, YESTERDAY)
    assert report(db, s.cg).order_count == 2


def test_F8_03_bo_don_chua_thanh_toan_chi_nhanh_khac_ngay_khong_co_don(db, shop):
    s = shop
    s.order(s.cg, (s.sua_da, 1, 30000), paid_at=None, status="PENDING_PAYMENT")
    s.order(s.cg, (s.sua_da, 1, 30000), paid_at=None, status="CANCELLED")    # tự hủy khi chưa trả tiền
    s.order(s.hd, (s.sua_da, 3, 30000), paid_at=at(YESTERDAY, 9))
    build_day(db, YESTERDAY)
    cg, hd = report(db, s.cg), report(db, s.hd)
    assert (cg.order_count, cg.cancelled_count, cg.revenue, cg.avg_order_value) == (0, 0, 0, 0)
    assert cg.avg_wait_seconds is None and cg.top_items == [] and cg.member_order_ratio == 0
    assert hd.revenue == 90000 and hd.top_items[0]["qty"] == 3


def test_F8_04_chay_lai_cap_nhat_dung_mot_dong(db, shop):
    s = shop
    s.order(s.cg, (s.sua_da, 1, 30000), paid_at=at(YESTERDAY, 8))
    build_daily_report(db, s.cg.id, YESTERDAY)
    first = report(db, s.cg).generated_at
    s.order(s.cg, (s.tra_dao, 2, 40000), paid_at=at(YESTERDAY, 9))
    _time.sleep(0.01)
    build_daily_report(db, s.cg.id, YESTERDAY)
    r = report(db, s.cg)
    assert r.revenue == 110000 and r.order_count == 2
    assert db.scalar(select(func.count()).select_from(DailySalesReport)) == 1
    assert r.generated_at >= first


def test_F8_05_top_5_mon(db, shop):
    from tests import factories as f
    cat = f.category(db, "Khác", 9)
    extra = [f.item(db, cat, f"Món {c}", 10000) for c in "ABCDE"]
    s = shop
    for i, m in enumerate(extra):
        s.order(s.cg, (m, i + 1, 10000), paid_at=at(YESTERDAY, 8))            # A:1 … E:5
    s.order(s.cg, (extra[0], 10, 10000), paid_at=at(YESTERDAY, 9), status="CANCELLED")
    s.order(s.cg, (s.sua_da, 2, 30000), paid_at=at(YESTERDAY, 9))
    build_daily_report(db, s.cg.id, YESTERDAY)
    assert [(t["name"], t["qty"]) for t in report(db, s.cg).top_items] == [
        ("Món E", 5), ("Món D", 4), ("Món C", 3), ("Cà phê sữa đá", 2), ("Món B", 2)]


def test_F8_06_bu_ngay_con_thieu(db, shop):
    s = shop
    s.order(s.cg, (s.sua_da, 1, 30000), paid_at=at(YESTERDAY, 8))
    build_daily_report(db, s.cg.id, YESTERDAY - timedelta(days=2))          # đã có sẵn 1 ngày
    db.execute(DailySalesReport.__table__.update().values(revenue=999)
               .where(DailySalesReport.report_date == YESTERDAY - timedelta(days=2)))
    n = catch_up(db, days=5)
    assert n == 2 * 5 - 1                                                    # 2 chi nhánh × 5 ngày, trừ 1 ngày đã có
    rows = db.scalars(select(DailySalesReport)).all()
    assert {r.report_date for r in rows} == {YESTERDAY - timedelta(days=i) for i in range(5)}
    assert report(db, s.cg, YESTERDAY - timedelta(days=2)).revenue == 999   # ngày đã có không tính lại
    assert report(db, s.cg).revenue == 30000
    assert catch_up(db, days=5) == 0
    assert db.scalar(select(func.max(DailySalesReport.report_date))) == YESTERDAY   # không tính hôm nay


def test_F8_07_gop_chi_so_nhieu_dong():
    def r(**kw):
        base = dict(revenue=0, order_count=0, cancelled_count=0, promo_revenue=0, avg_wait_seconds=None,
                    member_order_ratio=Decimal(0), recommended_item_ratio=Decimal(0), top_items=[])
        return DailySalesReport(**{**base, **kw})
    k = combine([r(revenue=100000, order_count=2, cancelled_count=1, promo_revenue=10, avg_wait_seconds=300,
                   member_order_ratio=Decimal("0.5"), recommended_item_ratio=Decimal("0.1")),
                 r(revenue=300000, order_count=6, avg_wait_seconds=500, member_order_ratio=Decimal("0.25"),
                   recommended_item_ratio=Decimal("0.3")),
                 r()])                                                       # ngày không có đơn
    assert k == Kpi(revenue=400000, order_count=8, cancelled_count=1, avg_order_value=50000, avg_wait_seconds=450,
                    member_order_ratio=0.3125, promo_revenue=10, recommended_item_ratio=0.25)
    assert combine([]) == Kpi() and combine([r()]).avg_wait_seconds is None
    t = top_items([r(top_items=[{"menu_item_id": 1, "name": "A", "qty": 3}, {"menu_item_id": 2, "name": "B", "qty": 1}]),
                   r(top_items=[{"menu_item_id": 2, "name": "B", "qty": 4}])])
    assert t == [{"menu_item_id": 2, "name": "B", "qty": 5}, {"menu_item_id": 1, "name": "A", "qty": 3}]


def test_F8_08_job_00_05_va_bu_khi_khoi_dong(monkeypatch, _settings):
    _settings.scheduler_enabled = True
    ran = []
    monkeypatch.setattr(sched_mod, "catch_up_job", lambda: ran.append(1))  # job 1 lần: chạy ngay rồi tự xóa khỏi lịch
    try:
        sch = sched_mod.start_scheduler()
        for _ in range(50):
            if ran:
                break
            _time.sleep(0.05)
        assert ran == [1]                                                    # bù báo cáo ngay khi khởi động
        jobs = {j.id: j for j in sch.get_jobs()}
        assert set(jobs) == {"daily_report", "rebuild_rules"}
        trig = str(jobs["daily_report"].trigger)
        assert "hour='0'" in trig and "minute='5'" in trig
        assert str(jobs["daily_report"].trigger.timezone) == "Asia/Ho_Chi_Minh"
        sch.shutdown(wait=False)
    finally:
        _settings.scheduler_enabled = False
    monkeypatch.undo()
    calls = []
    monkeypatch.setattr(sched_mod, "build_day", lambda db, d: calls.append(d))
    sched_mod.report_job()
    assert calls == [YESTERDAY]                                              # tổng hợp ngày hôm qua

    def boom(*a, **k):
        raise RuntimeError("CSDL lỗi")
    monkeypatch.setattr(sched_mod, "build_day", boom)
    monkeypatch.setattr(sched_mod, "catch_up", boom)
    sched_mod.report_job()
    sched_mod.catch_up_job()                                                 # lỗi không làm sập backend


@pytest.fixture
def _settings():
    from app.core.config import get_settings
    return get_settings()


def test_F8_09_hieu_nang_job_va_seed(db):
    """NFR-P6: job tổng hợp ≤ 1 phút. seed_orders tự tạo báo cáo cho các ngày lịch sử, doanh thu khớp với đơn."""
    from scripts.seed_data import seed
    from scripts.seed_orders import Params, seed_orders
    seed(db)
    t0 = _time.perf_counter()
    counts = seed_orders(db, p=Params(days=20, orders_per_day=25, members=40))
    assert counts["daily_reports"] == 20 * 3
    t0 = _time.perf_counter()
    db.execute(DailySalesReport.__table__.delete())
    assert catch_up(db, days=60) == 60 * 3
    assert _time.perf_counter() - t0 < 60
    total = db.scalar(select(func.sum(DailySalesReport.revenue)))
    orders = db.scalar(select(func.sum(Order.total_amount)).where(Order.status != "CANCELLED", Order.paid_at.is_not(None)))
    assert total == orders
