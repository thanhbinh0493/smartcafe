"""F2 – Mã đơn {chi nhánh}-{số thứ tự trong ngày}, UNIQUE (order_code, order_date) (D28, CR-32)."""
from datetime import timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models import Order
from tests.f2.conftest import place


def vn_today(db):
    return db.scalar(text("SELECT (now() AT TIME ZONE 'Asia/Ho_Chi_Minh')::date"))


def raw_order(db, shop, code, day):
    o = Order(order_code=code, order_date=day, access_token=code + str(day), branch_id=shop.cg.id,
              table_id=shop.t_cg.id, total_amount=0)
    db.add(o)
    db.flush()
    return o


def test_F2_12_ma_don_tang_dan_rieng_tung_chi_nhanh(client, db, shop):
    codes = [place(client, t, (shop.sua_da, 1)).json()["order_code"] for t in (shop.t_cg, shop.t_cg2, shop.t_hd, shop.t_cg)]
    assert codes == ["CG-0001", "CG-0002", "HD-0001", "CG-0003"]


def test_F2_13_ma_don_dem_lai_moi_ngay(client, db, shop):
    yesterday = vn_today(db) - timedelta(days=1)
    for n in range(1, 4):
        raw_order(db, shop, f"CG-{n:04d}", yesterday)
    r = place(client, shop.t_cg, (shop.sua_da, 1))
    assert r.json()["order_code"] == "CG-0001"
    assert db.get(Order, r.json()["order_id"]).order_date == vn_today(db)


def test_F2_14_csdl_chan_trung_ma_trong_cung_ngay(db, shop):
    today = vn_today(db)
    raw_order(db, shop, "CG-0001", today - timedelta(days=1))
    raw_order(db, shop, "CG-0001", today)  # khác ngày: hợp lệ
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            raw_order(db, shop, "CG-0001", today)
