"""F6 – Thao tác quản trị đồng thời qua API thật (mỗi request một kết nối CSDL riêng, không rollback).
Kết quả luôn nhất quán: không lỗi 500, không bản ghi trùng, không trộn dữ liệu của 2 lần sửa."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.main import app
from app.models import BranchMenuItem, Category, DiningTable, PromotionItem, Staff
from tests import factories as f
from tests.f3.conftest import auth
from tests.f6.test_promotions import iso

ROUNDS = 5


class Ids:
    pass


@pytest.fixture
def real(engine):
    """Dữ liệu đã commit; app dùng engine thật (không override get_db). Dọn sạch sau test."""
    with Session(engine) as s:
        o = Ids()
        o.cg = f.branch(s, "CC")
        o.admin, o.admin2 = f.staff(s, "ad_c1", "ADMIN"), f.staff(s, "ad_c2", "ADMIN")
        o.ql, o.ql2 = f.staff(s, "ql_c1", "MANAGER", o.cg), f.staff(s, "ql_c2", "MANAGER", o.cg)
        cat = f.category(s, "Conc", 1)
        o.items = [f.item(s, cat, f"Mon {i}", 50000) for i in range(4)]
        s.commit()
        o.ids = {"cg": o.cg.id, "items": [m.id for m in o.items]}
        o.h = {k: auth(getattr(o, k)) for k in ("admin", "admin2", "ql", "ql2")}
    yield o
    with engine.begin() as c:
        c.execute(text("TRUNCATE promotion_items, promotions, branch_menu_items, dining_tables, staff, "
                       "menu_items, categories, branches RESTART IDENTITY CASCADE"))


def parallel(*calls):
    barrier = Barrier(len(calls))

    def run(call):
        method, url, headers, body = call
        with TestClient(app) as c:
            barrier.wait()
            return c.request(method, url, headers=headers, json=body).status_code

    with ThreadPoolExecutor(len(calls)) as pool:
        return list(pool.map(run, calls))


def test_F6_58_hai_quan_ly_cung_sua_mot_mon_cua_chi_nhanh(engine, real):
    url = f"/api/staff/branches/{real.ids['cg']}/menu/{real.ids['items'][0]}"
    for i in range(ROUNDS):
        a = {"price_override": 40000 + i, "is_available": True}
        b = {"price_override": None, "is_available": False}
        assert parallel(("PATCH", url, real.h["ql"], a), ("PATCH", url, real.h["ql2"], b)) == [200, 200]
        with Session(engine) as s:
            rows = s.scalars(select(BranchMenuItem)).all()
            assert len(rows) == 1                                           # UPSERT: không trùng dòng
            assert (rows[0].price_override, rows[0].is_available) in ((a["price_override"], True), (None, False))


def test_F6_59_hai_nguoi_cung_tao_trung_ten(engine, real):
    for i in range(ROUNDS):
        res = parallel(*[("POST", "/api/staff/categories", real.h[k], {"name": f"Danh mục {i}"}) for k in ("admin", "admin2")])
        assert sorted(res) == [201, 409]
        res = parallel(*[("POST", f"/api/staff/branches/{real.ids['cg']}/tables", real.h[k], {"table_number": f"T{i}"})
                         for k in ("ql", "ql2")])
        assert sorted(res) == [201, 409]
        body = {"username": f"nv_{i}", "full_name": "NV", "password": "matkhau123", "role": "BARISTA"}
        res = parallel(*[("POST", "/api/staff/staff", real.h[k], body) for k in ("ql", "ql2")])
        assert sorted(res) == [201, 409]
    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(Category).where(Category.name.like("Danh mục%"))) == ROUNDS
        assert s.scalar(select(func.count()).select_from(DiningTable)) == ROUNDS
        assert s.scalar(select(func.count()).select_from(Staff).where(Staff.username.like("nv_%"))) == ROUNDS


def test_F6_60_hai_quan_tri_vien_cung_sua_mot_km(engine, real):
    ids = real.ids["items"]

    def body(items):
        return {"name": "KM", "branch_id": None, "start_at": iso(timedelta(hours=-1)), "end_at": iso(timedelta(days=1)),
                "items": [{"menu_item_id": m, "promo_price": 40000} for m in items]}

    url = None
    for _ in range(ROUNDS * 2):
        # Mỗi vòng: KM đang có 1 món [0]; 2 người cùng thay bằng [1, 2] và [2, 3] (bỏ món 0, cùng thêm món 2)
        with TestClient(app) as c:
            if url is None:
                url = f"/api/staff/promotions/{c.post('/api/staff/promotions', headers=real.h['admin'], json=body(ids[:1])).json()['id']}"
            else:
                assert c.put(url, headers=real.h["admin"], json=body(ids[:1])).status_code == 200
        a, b = body(ids[1:3]), body(ids[2:4])
        assert parallel(("PUT", url, real.h["admin"], a), ("PUT", url, real.h["admin2"], b)) == [200, 200]
        pid = int(url.rsplit("/", 1)[-1])
        with Session(engine) as s:
            got = sorted(s.scalars(select(PromotionItem.menu_item_id).where(PromotionItem.promotion_id == pid)))
            assert got in (sorted(ids[1:3]), sorted(ids[2:4]))              # đúng 1 trong 2 bản, không trộn
