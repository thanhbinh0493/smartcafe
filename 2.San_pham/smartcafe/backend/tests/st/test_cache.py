"""Giai đoạn VI – cache trong tiến trình cho API đọc của khách (D38, sửa BUG-ST-06 / NFR-P2, P3).

Kiểm tra: dùng lại kết quả trong thời hạn; mọi thao tác quản trị làm đổi dữ liệu khách nhìn thấy xóa cache ngay;
menu hết hạn đúng lúc KM bắt đầu / kết thúc; tạo đơn vẫn tính giá trực tiếp từ CSDL (NFR-S6)."""
from datetime import timedelta

from sqlalchemy import update

from app.core import cache
from app.models import MenuItem
from app.modules.menu.service import MENU_TTL, menu_ttl
from tests import factories as f
from tests.f2.conftest import Shop, place, shop  # noqa: F401  (fixture shop)
from tests.f3.conftest import auth


def price_of(client, branch, item) -> int:
    menu = client.get(f"/api/public/branches/{branch.id}/menu").json()
    return {i["id"]: i for c in menu["categories"] for i in c["items"]}[item.id]["sell_price"]


def test_ST_90_menu_dung_lai_cache_quan_ly_doi_thi_thay_ngay(client, db, shop):
    ql = f.staff(db, "ql_cg", "MANAGER", shop.cg)
    assert price_of(client, shop.cg, shop.sua_da) == 29000
    # Đổi thẳng trong CSDL (không qua API quản trị) → vẫn trả bản trong cache: chứng tỏ không đọc lại CSDL
    db.execute(update(MenuItem).where(MenuItem.id == shop.sua_da.id).values(base_price=31000))
    db.flush()
    assert price_of(client, shop.cg, shop.sua_da) == 29000
    assert cache.stats["hit"] >= 1
    # Quản lý đặt giá riêng qua API → cache bị xóa, khách thấy ngay giá mới
    r = client.patch(f"/api/staff/branches/{shop.cg.id}/menu/{shop.sua_da.id}", headers=auth(ql),
                     json={"price_override": 33000, "is_available": True})
    assert r.status_code == 200
    assert price_of(client, shop.cg, shop.sua_da) == 33000
    # Hết hàng qua API → gợi ý (dùng chung menu cache) cũng bỏ món ngay
    client.patch(f"/api/staff/branches/{shop.cg.id}/menu/{shop.sua_da.id}", headers=auth(ql),
                 json={"price_override": None, "is_available": False})
    recs = client.get(f"/api/public/branches/{shop.cg.id}/recommendations").json()["items"]
    assert shop.sua_da.id not in [i["menu_item_id"] for i in recs]


def test_ST_91_menu_het_han_dung_luc_khuyen_mai_bat_dau(client, db, shop):
    assert menu_ttl(db) == MENU_TTL                                           # KM hiện tại còn 1 ngày
    f.promo(db, shop.admin, {shop.banh: 20000}, start=timedelta(seconds=5), end=timedelta(hours=1))
    ttl = menu_ttl(db)
    assert 0 < ttl <= 10                                                      # giữ không quá mốc KM bắt đầu


def test_ST_92_khoa_ban_thi_quet_qr_bao_khong_hop_le_ngay(client, db, shop):
    ql = f.staff(db, "ql_cg", "MANAGER", shop.cg)
    assert client.get(f"/api/public/tables/{shop.t_cg.qr_token}").status_code == 200
    assert client.get(f"/api/public/tables/{shop.t_cg.qr_token}").status_code == 200      # lần 2: từ cache
    r = client.put(f"/api/staff/branches/{shop.cg.id}/tables/{shop.t_cg.id}", headers=auth(ql),
                   json={"table_number": "05", "is_active": False})
    assert r.status_code == 200
    assert client.get(f"/api/public/tables/{shop.t_cg.qr_token}").status_code == 404


def test_ST_93_tao_don_luon_tinh_gia_tu_csdl_khong_dung_cache(client, db, shop):
    assert price_of(client, shop.cg, shop.sua_da) == 29000                   # menu đã vào cache
    db.execute(update(MenuItem).where(MenuItem.id == shop.sua_da.id).values(base_price=31000))
    db.flush()
    stale = place(client, shop.t_cg, (shop.sua_da, 1), expected_total=29000)
    assert stale.status_code == 409 and stale.json()["error"]["code"] == "PRICE_CHANGED"
    ok = place(client, shop.t_cg, (shop.sua_da, 1))
    assert ok.status_code == 201 and ok.json()["total"] == 31000


def test_ST_94_xoa_cache_trong_luc_dang_tai_thi_khong_luu_ban_cu():
    calls = []

    def loader():
        calls.append(1)
        cache.invalidate_public()                 # admin vừa đổi dữ liệu trong lúc đang đọc CSDL
        return "bản cũ", 60.0

    assert cache.get("menu", 1, loader) == "bản cũ"
    assert cache.get("menu", 1, lambda: ("bản mới", 60.0)) == "bản mới"     # bản cũ không bị lưu lại
    assert cache.get("menu", 1, lambda: ("không gọi", 60.0)) == "bản mới"


def test_ST_95_hoc_lai_luat_thi_xoa_cache_luat(client, db, shop):
    from app.modules.recommend.service import branch_rules
    from app.modules.recommend.training import rebuild_rules
    assert branch_rules(db, shop.cg.id) == []
    cache.get("rules", shop.cg.id, lambda: (["luật cũ"], 600.0))
    rebuild_rules(db)
    assert cache.get("rules", shop.cg.id, lambda: (["đọc lại"], 600.0)) == ["đọc lại"]
