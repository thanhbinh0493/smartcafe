"""F2 – Kịch bản demo trên dữ liệu mẫu: bàn 05 Cầu Giấy gọi 2 Cà phê sữa đá + 1 Trà đào cam sả."""
from sqlalchemy import select

from app.models import Branch, DiningTable, MenuItem
from scripts.seed_data import seed


def test_F2_28_dat_va_thanh_toan_tren_du_lieu_mau(client, db):
    seed(db)
    table = db.scalar(select(DiningTable).join(Branch).where(Branch.code == "CG", DiningTable.table_number == "05"))
    ids = dict(db.execute(select(MenuItem.name, MenuItem.id)).all())
    body = {"qr_token": table.qr_token, "expected_total": 86000, "items": [
        {"menu_item_id": ids["Cà phê sữa đá"], "quantity": 2, "note": "ít đường"},
        {"menu_item_id": ids["Trà đào cam sả"], "quantity": 1},
    ]}
    o = client.post("/api/public/orders", json=body).json()
    # Cà phê sữa đá: KM riêng CG 25.000 (gốc 29.000); Trà đào: KM toàn chuỗi 36.000 (gốc 45.000)
    assert (o["subtotal"], o["discount"], o["total"]) == (103000, 17000, 86000)
    assert o["order_code"] == "CG-0001"
    r = client.post(f"/api/public/orders/{o['order_id']}/pay", json={"access_token": o["access_token"], "method": "MOCK_EWALLET"})
    assert r.json()["status"] == "PAID"
