"""F8 – API dashboard W08 (GET /api/staff/reports/daily) và chạy lại báo cáo (POST .../rebuild)."""
import time
from datetime import timedelta

import pytest

from app.modules.report.service import build_day, today_vn
from tests.f3.conftest import auth
from tests.f8.conftest import YESTERDAY, at

D1, D2 = YESTERDAY, YESTERDAY - timedelta(days=1)


@pytest.fixture
def data(db, shop):
    s = shop
    s.order(s.cg, (s.sua_da, 2, 30000), paid_at=at(D2, 8), wait_s=300)                   # CG hôm kia 60.000
    s.order(s.cg, (s.sua_da, 3, 30000), paid_at=at(D1, 8), wait_s=200, member=True)      # CG hôm qua 90.000
    s.order(s.cg, (s.tra_dao, 1, 30000, True), paid_at=at(D1, 9), wait_s=400)            #            30.000 (KM)
    s.order(s.hd, (s.tra_dao, 2, 40000), paid_at=at(D1, 10), wait_s=600)                 # HD hôm qua 80.000
    s.order(s.hd, (s.banh, 1, 20000), paid_at=at(D1, 11), status="CANCELLED", wait_s=None)
    for d in (D1, D2, D1 - timedelta(days=7)):
        build_day(db, d)
    return s


def get(client, staff, **params):
    return client.get("/api/staff/reports/daily", params=params, headers=auth(staff))


def test_F8_10_quan_tri_vien_xem_tat_ca_chi_nhanh_7_ngay(client, data):
    r = get(client, data.admin)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["from_date"] == str(D1 - timedelta(days=6)) and j["to_date"] == str(D1) and j["branch_id"] is None
    assert j["latest_date"] == str(D1)
    assert j["latest"] == {"revenue": 200000, "order_count": 3, "cancelled_count": 1, "avg_order_value": 66667,
                           "avg_wait_seconds": 400, "member_order_ratio": 0.3333, "promo_revenue": 30000,
                           "recommended_item_ratio": 0.0}
    assert j["previous"]["revenue"] == 60000 and j["previous"]["order_count"] == 1
    assert j["period"]["revenue"] == 260000                                  # ngày D1-7 nằm ngoài khoảng
    assert [(b["code"], b["kpi"]["revenue"], b["kpi"]["cancelled_count"]) for b in j["branches"]] == [
        ("CG", 120000, 0), ("HD", 80000, 1)]
    series = {(p["report_date"], p["branch_id"]): p["revenue"] for p in j["series"]}
    assert series[(str(D2), data.cg.id)] == 60000 and series[(str(D2), data.hd.id)] == 0
    assert [t["name"] for t in j["top_items"]] == ["Cà phê sữa đá", "Trà đào"]          # gộp 2 chi nhánh
    assert [t["qty"] for t in j["top_items"]] == [3, 3]
    assert j["generated_at"]


def test_F8_11_loc_chi_nhanh_va_khoang_30_ngay(client, data):
    j = get(client, data.admin, branch_id=data.hd.id, **{"from": str(D1 - timedelta(days=29)), "to": str(D1)}).json()
    assert j["branch_id"] == data.hd.id and [b["code"] for b in j["branches"]] == ["HD"]
    assert j["latest"]["revenue"] == 80000 and j["latest"]["avg_wait_seconds"] == 600
    assert j["period"]["revenue"] == 80000 and {p["branch_id"] for p in j["series"]} == {data.hd.id}
    assert j["previous"]["revenue"] == 0                                     # HD hôm kia không có đơn


def test_F8_12_quan_ly_chi_xem_chi_nhanh_minh(client, data):
    j = get(client, data.ql).json()
    assert j["branch_id"] == data.cg.id and j["latest"]["revenue"] == 120000
    assert get(client, data.ql, branch_id=data.hd.id).status_code == 403
    for st in (data.tn, data.pc):
        assert get(client, st).status_code == 403
    assert client.get("/api/staff/reports/daily").status_code == 401


@pytest.mark.parametrize("params, field", [
    ({"from": str(D1), "to": str(D2)}, "from"),
    ({"from": str(D1 - timedelta(days=92)), "to": str(D1)}, "from"),
])
def test_F8_13_khoang_thoi_gian_khong_hop_le(client, data, params, field):
    r = get(client, data.admin, **params)
    assert r.status_code == 422 and r.json()["error"]["details"]["field"] == field


def test_F8_14_chi_gom_ngay_da_ket_thuc_va_chi_nhanh_khong_ton_tai(client, data):
    j = get(client, data.admin, to=str(today_vn() + timedelta(days=3))).json()
    assert j["to_date"] == str(D1)                                           # hôm nay / tương lai bị cắt về hôm qua
    assert get(client, data.admin, branch_id=99999).status_code == 404
    empty = get(client, data.admin, **{"from": str(D1 - timedelta(days=40)), "to": str(D1 - timedelta(days=30))}).json()
    assert empty["latest"] is None and empty["series"] == [] and empty["period"]["revenue"] == 0


def test_F8_15_quan_tri_vien_chay_lai_bao_cao(client, db, data):
    s = data
    s.order(s.cg, (s.banh, 5, 20000), paid_at=at(D1, 15))                     # đơn bổ sung sau khi đã tổng hợp
    assert get(client, s.admin).json()["latest"]["revenue"] == 200000
    r = client.post("/api/staff/reports/daily/rebuild", json={"date": str(D1), "branch_id": s.cg.id}, headers=auth(s.admin))
    assert r.status_code == 200 and r.json() == {"report_date": str(D1), "branches": 1}
    assert get(client, s.admin).json()["latest"]["revenue"] == 300000
    r = client.post("/api/staff/reports/daily/rebuild", json={"date": str(D1)}, headers=auth(s.admin))
    assert r.json()["branches"] == 2


@pytest.mark.parametrize("who, body, status", [
    ("admin", {"date": "today"}, 422), ("admin", {"date": "future"}, 422), ("admin", {"date": "x"}, 422),
    ("admin", {"date": "d1", "branch_id": 99999}, 404), ("ql", {"date": "d1"}, 403),
])
def test_F8_16_chay_lai_khong_hop_le(client, data, who, body, status):
    dates = {"today": str(today_vn()), "future": str(today_vn() + timedelta(days=1)), "d1": str(D1), "x": "31/10"}
    body = {**body, "date": dates[body["date"]]}
    r = client.post("/api/staff/reports/daily/rebuild", json=body, headers=auth(getattr(data, who)))
    assert r.status_code == status


def test_F8_17_dashboard_30_ngay_3_chi_nhanh_duoi_2_giay(client, db, shop):
    """NFR-P6 (tham khảo, 1 người dùng)."""
    from tests import factories as f
    tx = f.branch(db, "TX")
    for i in range(30):
        for b in (shop.cg, shop.hd, tx):
            shop.order(b, (shop.sua_da, 1, 30000), paid_at=at(D1 - timedelta(days=i), 9))
    from app.modules.report.service import catch_up
    catch_up(db, days=30)
    t0 = time.perf_counter()
    j = get(client, shop.admin, **{"from": str(D1 - timedelta(days=29)), "to": str(D1)}).json()
    assert (time.perf_counter() - t0) < 2
    assert len(j["series"]) == 90 and j["period"]["order_count"] == 90
