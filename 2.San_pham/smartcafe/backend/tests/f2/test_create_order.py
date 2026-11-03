"""F2 – UC04/UC05: tạo đơn, server tự tính giá (NFR-S6), kiểm tra còn hàng, giá thay đổi."""
import pytest
from sqlalchemy import func, select

from app.models import Order, OrderItem, OrderStatusHistory
from tests import factories as f
from tests.f2.conftest import order_body, place


def count_orders(db) -> int:
    return db.scalar(select(func.count()).select_from(Order))


def test_F2_01_tao_don_thanh_cong(client, db, shop):
    r = place(client, shop.t_cg, (shop.sua_da, 2, "ít đường"), (shop.tra_dao, 1))
    assert r.status_code == 201
    o = r.json()
    assert o["status"] == "PENDING_PAYMENT"
    assert o["order_code"] == "CG-0001"
    assert len(o["access_token"]) >= 22
    assert (o["subtotal"], o["discount"], o["total"]) == (29000 * 2 + 45000, 9000, 29000 * 2 + 36000)
    assert o["expected_points"] is None  # khách ẩn danh
    lines = {l["name"]: l for l in o["items"]}
    assert lines["Tra dao"]["unit_price"] == 36000 and lines["Tra dao"]["is_promo"] is True
    assert lines["Ca phe sua da"]["note"] == "ít đường" and lines["Ca phe sua da"]["status"] == "WAITING"

    order = db.get(Order, o["order_id"])
    assert order.table_id == shop.t_cg.id and order.branch_id == shop.cg.id and order.customer_id is None
    tra = next(i for i in order.items if i.menu_item_id == shop.tra_dao.id)
    assert (tra.original_price, tra.unit_price, tra.promotion_id) == (45000, 36000, shop.promo.id)
    hist = db.scalars(select(OrderStatusHistory).where(OrderStatusHistory.order_id == order.id)).all()
    assert [(h.from_status, h.to_status, h.source) for h in hist] == [(None, "PENDING_PAYMENT", "CUSTOMER")]


def test_F2_02_bo_qua_gia_client_gui_len(client, db, shop):
    body = order_body(shop.t_cg, (shop.sua_da, 1))
    body["items"][0]["unit_price"] = 1
    body["total"] = 1
    r = client.post("/api/public/orders", json=body)
    assert r.status_code == 201 and r.json()["total"] == 29000


def test_F2_03_dung_gia_rieng_cua_chi_nhanh(client, db, shop):
    f.branch_item(db, shop.hd, shop.sua_da, price=27000)
    assert place(client, shop.t_hd, (shop.sua_da, 1)).json()["total"] == 27000
    assert place(client, shop.t_cg, (shop.sua_da, 1)).json()["total"] == 29000


def test_F2_04_mon_tam_het(client, db, shop):
    f.branch_item(db, shop.cg, shop.banh, available=False)
    r = place(client, shop.t_cg, (shop.sua_da, 1), (shop.banh, 1))
    assert r.status_code == 409
    err = r.json()["error"]
    assert err["code"] == "ITEM_UNAVAILABLE" and err["details"]["item_ids"] == [shop.banh.id]
    assert "Banh croissant" in err["message"]
    assert count_orders(db) == 0


def test_F2_05_mon_ngung_ban_hoac_khong_ton_tai(client, db, shop):
    shop.banh.is_active = False
    db.flush()
    r = place(client, shop.t_cg, (shop.banh, 1))
    assert r.status_code == 409 and r.json()["error"]["code"] == "ITEM_UNAVAILABLE"
    r = client.post("/api/public/orders", json={"qr_token": shop.t_cg.qr_token, "items": [{"menu_item_id": 999999, "quantity": 1}]})
    assert r.status_code == 409 and r.json()["error"]["details"]["item_ids"] == [999999]


def test_F2_06_qr_sai_hoac_ban_khoa(client, db, shop):
    r = client.post("/api/public/orders", json={"qr_token": "sai", "items": [{"menu_item_id": shop.sua_da.id, "quantity": 1}]})
    assert r.status_code == 404 and r.json()["error"]["code"] == "TABLE_NOT_FOUND"
    shop.t_cg.is_active = False
    db.flush()
    assert place(client, shop.t_cg, (shop.sua_da, 1)).status_code == 404


@pytest.mark.parametrize("mutate", [
    lambda b: b["items"][0].update(quantity=0),
    lambda b: b["items"][0].update(quantity=21),
    lambda b: b.update(items=[]),
    lambda b: b["items"][0].update(note="x" * 256),
    lambda b: b.update(note="x" * 256),
], ids=["sl0", "sl21", "gio_rong", "ghi_chu_mon_256", "ghi_chu_don_256"])
def test_F2_07_du_lieu_khong_hop_le(client, db, shop, mutate):
    body = order_body(shop.t_cg, (shop.sua_da, 1))
    mutate(body)
    r = client.post("/api/public/orders", json=body)
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"
    assert count_orders(db) == 0


def test_F2_08_tong_so_luong_mot_mon_toi_da_20(client, db, shop):
    r = place(client, shop.t_cg, (shop.sua_da, 15, "ít đá"), (shop.sua_da, 6, "nhiều đá"))
    assert r.status_code == 422 and r.json()["error"]["code"] == "QUANTITY_LIMIT"
    assert place(client, shop.t_cg, (shop.sua_da, 15, "ít đá"), (shop.sua_da, 5, "nhiều đá")).status_code == 201


def test_F2_09_tong_tien_khop_thi_tao_don(client, db, shop):
    r = place(client, shop.t_cg, (shop.tra_dao, 1), expected_total=36000)
    assert r.status_code == 201


def test_F2_10_km_vua_het_han_bao_gia_thay_doi(client, db, shop):
    """UC05 – 3b: khách thấy giá KM 36.000 nhưng KM vừa bị tắt -> báo giá mới, không tạo đơn."""
    shop.promo.is_active = False
    db.flush()
    r = place(client, shop.t_cg, (shop.tra_dao, 1), expected_total=36000)
    assert r.status_code == 409
    err = r.json()["error"]
    assert err["code"] == "PRICE_CHANGED" and err["details"]["total"] == 45000
    assert err["details"]["prices"] == [
        {"menu_item_id": shop.tra_dao.id, "regular_price": 45000, "sell_price": 45000, "is_promo": False}
    ]
    assert count_orders(db) == 0


def test_F2_11_ghi_nhan_mon_tu_goi_y(client, db, shop):
    body = order_body(shop.t_cg, (shop.sua_da, 1), (shop.banh, 1))
    body["items"][1]["is_recommended"] = True
    oid = client.post("/api/public/orders", json=body).json()["order_id"]
    flags = dict(db.execute(select(OrderItem.menu_item_id, OrderItem.is_recommended).where(OrderItem.order_id == oid)).all())
    assert flags == {shop.sua_da.id: False, shop.banh.id: True}
