"""F1 – Kiểm tra tích hợp trên bộ dữ liệu mẫu (kịch bản demo thực tế)."""
from sqlalchemy import select

from app.models import Branch, DiningTable
from scripts.seed_data import seed


def menu_of(client, db, code):
    b = db.scalar(select(Branch).where(Branch.code == code))
    menu = client.get(f"/api/public/branches/{b.id}/menu").json()
    return {i["name"]: i for c in menu["categories"] for i in c["items"]}, menu


def test_F1_20_quet_qr_ban_bat_ky_roi_mo_menu(client, db):
    seed(db)
    t = db.scalar(select(DiningTable).join(Branch).where(Branch.code == "TX", DiningTable.table_number == "12"))
    info = client.get(f"/api/public/tables/{t.qr_token}").json()
    assert info["branch"]["code"] == "TX" and info["table"]["table_number"] == "12"
    items, menu = menu_of(client, db, "TX")
    assert len(items) == 35
    assert [c["name"] for c in menu["categories"]] == ["Cà phê", "Trà", "Đá xay", "Nước ép & Sinh tố", "Bánh"]


def test_F1_21_gia_tren_du_lieu_mau_dung_kich_ban(client, db):
    seed(db)
    cg, _ = menu_of(client, db, "CG")
    hd, _ = menu_of(client, db, "HD")
    tx, _ = menu_of(client, db, "TX")
    # KM riêng Cầu Giấy
    assert (cg["Cà phê sữa đá"]["sell_price"], cg["Cà phê sữa đá"]["is_promo"]) == (25000, True)
    # Hà Đông giá riêng 27.000đ, không có KM Cầu Giấy
    assert (hd["Cà phê sữa đá"]["sell_price"], hd["Cà phê sữa đá"]["is_promo"]) == (27000, False)
    assert tx["Cà phê sữa đá"]["sell_price"] == 29000
    # KM toàn chuỗi
    for m in (cg, hd, tx):
        assert m["Trà đào cam sả"]["sell_price"] == 36000
        assert m["Trà vải"]["sell_price"] == 33600
        assert m["Cookie đá xay"]["is_promo"] is False  # KM Halloween đã kết thúc
    # Tạm hết chỉ ở Cầu Giấy
    assert cg["Bạc xỉu nóng"]["is_available"] is False
    assert hd["Bạc xỉu nóng"]["is_available"] is True
    # 4 món mới
    assert {n for n, i in cg.items() if i["is_new"]} == {
        "Bạc xỉu dừa", "Trà dâu tây kem cheese", "Xoài đá xay", "Bánh sừng bò hạnh nhân",
    }
