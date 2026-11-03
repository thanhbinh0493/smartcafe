"""F6 – UC11 Chi nhánh (A03), UC13 Menu chi nhánh (W06), UC14 Bàn & mã QR (A06)."""
import io

import pytest
import qrcode
from PIL import Image, ImageFont

from app.models import DiningTable
from app.modules.admin import branches as br
from tests import factories as f
from tests.f2.conftest import place
from tests.f6.conftest import call, public_menu

BRANCH = {"code": "td", "name": "SmartCafe Thủ Đức", "address": "1 Võ Văn Ngân", "phone": "028 3896 1234",
          "latitude": 10.85, "longitude": 106.77}


# ---------- Chi nhánh ----------
def test_F6_15_tao_chi_nhanh_ma_viet_hoa(client, org):
    r = call(client, org.admin, "POST", "/api/staff/branches", json=BRANCH)
    assert r.status_code == 201, r.text
    b = r.json()
    assert b == {**b, "code": "TD", "name": "SmartCafe Thủ Đức", "is_active": True, "table_count": 0,
                 "staff_count": 0, "latitude": 10.85}
    r = call(client, org.admin, "POST", "/api/staff/branches", json={**BRANCH, "code": "CG"})
    assert r.status_code == 409 and r.json()["error"]["details"]["field"] == "code"


@pytest.mark.parametrize("patch", [{"code": "C"}, {"code": "CG-1"}, {"code": "X" * 11}, {"name": ""},
                                   {"address": " "}, {"phone": "abc"}, {"latitude": 91}, {"longitude": -181}])
def test_F6_16_chi_nhanh_du_lieu_khong_hop_le(client, org, patch):
    r = call(client, org.admin, "POST", "/api/staff/branches", json={**BRANCH, **patch})
    assert r.status_code == 422


def test_F6_17_sua_chi_nhanh_khong_doi_ma_va_ngung_hoat_dong(client, org):
    body = {"name": "CG mới", "address": "122 Xuân Thủy", "phone": None, "is_active": False, "code": "ZZ"}
    r = call(client, org.admin, "PUT", f"/api/staff/branches/{org.cg.id}", json=body)
    assert r.status_code == 200
    assert r.json() == {**r.json(), "code": "CG", "name": "CG mới", "is_active": False, "table_count": 1}
    # Ngừng hoạt động: quét QR bàn của chi nhánh báo không hợp lệ (UC01-2a), menu khách 404
    assert client.get(f"/api/public/tables/{org.t_cg.qr_token}").status_code == 404
    assert client.get(f"/api/public/branches/{org.cg.id}/menu").status_code == 404
    assert call(client, org.admin, "PUT", "/api/staff/branches/99999", json=body).status_code == 404


def test_F6_18_quan_ly_chi_thay_chi_nhanh_minh(client, org):
    assert [b["code"] for b in call(client, org.admin, "GET", "/api/staff/branches").json()] == ["CG", "HD"]
    rows = call(client, org.ql, "GET", "/api/staff/branches").json()
    assert [b["code"] for b in rows] == ["CG"] and rows[0]["staff_count"] == 3


# ---------- Menu chi nhánh ----------
def test_F6_19_menu_chi_nhanh_liet_ke_gia_chung_va_gia_rieng(client, db, org):
    f.branch_item(db, org.cg, org.tra_dao, price=39000)
    f.branch_item(db, org.cg, org.bac_xiu, available=False)
    rows = {r["name"]: r for r in call(client, org.ql, "GET", f"/api/staff/branches/{org.cg.id}/menu").json()}
    assert list(rows) == ["Bạc xỉu", "Cà phê sữa đá", "Trà đào cam sả"]
    assert rows["Trà đào cam sả"] == {**rows["Trà đào cam sả"], "base_price": 45000, "price_override": 39000,
                                      "is_available": True, "category_name": "Trà"}
    assert rows["Bạc xỉu"]["is_available"] is False
    assert rows["Cà phê sữa đá"] == {**rows["Cà phê sữa đá"], "price_override": None, "is_available": True,
                                     "updated_at": None}


def test_F6_20_dat_gia_rieng_va_het_hang_co_hieu_luc_ngay_tren_menu_khach(client, org):
    url = f"/api/staff/branches/{org.cg.id}/menu/{org.tra_dao.id}"
    r = call(client, org.ql, "PATCH", url, json={"price_override": 39000, "is_available": True})
    assert r.status_code == 200 and r.json()["price_override"] == 39000 and r.json()["updated_at"]
    assert public_menu(client, org.cg)["Trà đào cam sả"]["regular_price"] == 39000
    assert public_menu(client, org.hd)["Trà đào cam sả"]["regular_price"] == 45000      # chi nhánh khác giữ giá chung

    call(client, org.ql, "PATCH", url, json={"price_override": None, "is_available": False})
    item = public_menu(client, org.cg)["Trà đào cam sả"]
    assert item["regular_price"] == 45000 and item["is_available"] is False
    # Khách đặt món vừa tạm hết: bị từ chối (UC05-3a)
    r = place(client, org.t_cg, (org.tra_dao, 1))
    assert r.status_code == 409 and r.json()["error"]["code"] == "ITEM_UNAVAILABLE"


@pytest.mark.parametrize("body", [{"price_override": -1}, {"price_override": 10_000_001}, {"is_available": "x"}])
def test_F6_21_menu_chi_nhanh_du_lieu_khong_hop_le(client, org, body):
    r = call(client, org.ql, "PATCH", f"/api/staff/branches/{org.cg.id}/menu/{org.tra_dao.id}", json=body)
    assert r.status_code == 422


def test_F6_22_menu_chi_nhanh_mon_khong_ton_tai_hoac_khac_chi_nhanh(client, db, org):
    hidden = f.item(db, org.tea, "Trà ẩn", 30000, is_active=False)
    for item_id in (99999, hidden.id):
        r = call(client, org.ql, "PATCH", f"/api/staff/branches/{org.cg.id}/menu/{item_id}", json={})
        assert r.status_code == 404 and r.json()["error"]["code"] == "MENU_ITEM_NOT_FOUND"
    r = call(client, org.ql, "PATCH", f"/api/staff/branches/{org.hd.id}/menu/{org.tra_dao.id}", json={})
    assert r.status_code == 403
    r = call(client, org.admin, "PATCH", f"/api/staff/branches/{org.hd.id}/menu/{org.tra_dao.id}",
             json={"is_available": False})
    assert r.status_code == 200                                                         # ADMIN: mọi chi nhánh
    assert call(client, org.admin, "GET", "/api/staff/branches/99999/menu").status_code == 404


# ---------- Bàn & QR ----------
def test_F6_23_them_ban_sinh_qr_token_ngau_nhien(client, org):
    r = call(client, org.ql, "POST", f"/api/staff/branches/{org.cg.id}/tables", json={"table_number": " 12 "})
    assert r.status_code == 201, r.text
    t = r.json()
    assert t["table_number"] == "12" and t["is_active"] is True
    assert len(t["qr_token"]) >= 22 and str(t["id"]) not in t["qr_token"]                # NFR-S3
    assert t["qr_url"] == f"http://localhost:8080/t/{t['qr_token']}"
    # Khách quét được ngay
    assert client.get(f"/api/public/tables/{t['qr_token']}").json()["table"]["table_number"] == "12"
    r = call(client, org.ql, "POST", f"/api/staff/branches/{org.cg.id}/tables", json={"table_number": "05"})
    assert r.status_code == 409
    # Số bàn trùng ở chi nhánh khác thì được
    assert call(client, org.ql_hd, "POST", f"/api/staff/branches/{org.hd.id}/tables",
                json={"table_number": "05"}).status_code == 201


@pytest.mark.parametrize("number", ["", "A B", "x" * 11, "05/1"])
def test_F6_24_so_ban_khong_hop_le(client, org, number):
    r = call(client, org.ql, "POST", f"/api/staff/branches/{org.cg.id}/tables", json={"table_number": number})
    assert r.status_code == 422


def test_F6_25_sua_so_ban_giu_ma_qr_khoa_ban(client, db, org):
    other = f.table(db, org.cg, "06")
    url = f"/api/staff/branches/{org.cg.id}/tables/{org.t_cg.id}"
    r = call(client, org.ql, "PUT", url, json={"table_number": "5a", "is_active": True})
    assert r.status_code == 200 and r.json()["table_number"] == "5A" and r.json()["qr_token"] == org.t_cg.qr_token
    assert call(client, org.ql, "PUT", url, json={"table_number": "06"}).status_code == 409

    call(client, org.ql, "PUT", url, json={"table_number": "5A", "is_active": False})
    assert client.get(f"/api/public/tables/{org.t_cg.qr_token}").status_code == 404     # UC01-2a
    rows = call(client, org.ql, "GET", f"/api/staff/branches/{org.cg.id}/tables").json()
    assert [(t["table_number"], t["is_active"]) for t in rows] == [("06", True), ("5A", False)]
    # Bàn của chi nhánh khác / sai chi nhánh trên URL
    assert call(client, org.ql, "PUT", f"/api/staff/branches/{org.hd.id}/tables/{other.id}",
                json={"table_number": "07"}).status_code == 403
    assert call(client, org.admin, "PUT", f"/api/staff/branches/{org.hd.id}/tables/{other.id}",
                json={"table_number": "07"}).status_code == 404


def test_F6_26_sap_xep_ban_theo_so(client, db, org):
    for n in ("10", "2", "1"):
        f.table(db, org.cg, n)
    rows = call(client, org.ql, "GET", f"/api/staff/branches/{org.cg.id}/tables").json()
    assert [t["table_number"] for t in rows] == ["1", "2", "05", "10"]


def test_F6_27_anh_qr_de_in_doc_duoc_dung_url(client, db, org):
    r = call(client, org.ql, "GET", f"/api/staff/tables/{org.t_cg.id}/qr.png")
    assert r.status_code == 200 and r.headers["content-type"] == "image/png"
    assert 'filename="QR_CG_Ban_05.png"' in r.headers["content-disposition"]
    img = Image.open(io.BytesIO(r.content)).convert("L")
    assert img.height > img.width                                                        # có dòng chữ bên dưới
    # Đối chiếu từng ô của mã QR trong ảnh với ma trận QR của URL bàn (box 10px, viền 4 ô)
    expected = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=0)
    expected.add_data(f"http://localhost:8080/t/{org.t_cg.qr_token}")
    expected.make(fit=True)
    matrix = expected.get_matrix()
    assert img.width == (len(matrix) + 8) * 10
    for r_, row in enumerate(matrix):
        for c_, dark in enumerate(row):
            assert (img.getpixel((40 + c_ * 10 + 5, 40 + r_ * 10 + 5)) < 128) == dark


def test_F6_28_anh_qr_kiem_tra_quyen(client, db, org):
    t_hd = db.get(DiningTable, f.table(db, org.hd, "01").id)
    assert call(client, org.ql, "GET", f"/api/staff/tables/{t_hd.id}/qr.png").status_code == 403
    assert call(client, org.admin, "GET", f"/api/staff/tables/{t_hd.id}/qr.png").status_code == 200
    assert call(client, org.ql, "GET", "/api/staff/tables/99999/qr.png").status_code == 404
    assert client.get(f"/api/staff/tables/{org.t_cg.id}/qr.png").status_code == 401


def _glyph(font, ch: str):
    m = font.getmask(ch)
    return m.size, bytes(m)


def test_F6_61_hoi_quy_BUG_F6_01_chu_duoi_ma_qr_co_dau_tieng_viet():
    """Phông dùng cho dòng "CG · Bàn 05" phải có chữ tiếng Việt (không vẽ ra ô vuông như phông mặc định)."""
    font = br.label_font()
    assert font is not None, "máy chạy test / Docker phải có ít nhất 1 phông trong LABEL_FONTS"
    tofu = _glyph(font, "\ue000")                        # ký tự riêng, không phông nào có → ô vuông
    for ch in "àạươđÀĐ":
        assert _glyph(font, ch) != tofu, ch
    # Phông mặc định của Pillow (nguyên nhân lỗi) đúng là không có "à"
    default = ImageFont.load_default(size=40)
    assert _glyph(default, "à") == _glyph(default, "\ue000")


def test_F6_62_khong_co_phong_tieng_viet_thi_bo_dau_thay_vi_o_vuong(monkeypatch):
    monkeypatch.setattr(br, "LABEL_FONTS", ["/khong/co/phong.ttf"])
    assert br.label_font() is None
    assert br.ascii_fold("CG · Bàn 05 – Đống Đa") == "CG - Ban 05 – Dong Da"
    png = br.render_qr_png("http://x/t/abc", "CG · Bàn 05")
    assert Image.open(io.BytesIO(png)).format == "PNG"
