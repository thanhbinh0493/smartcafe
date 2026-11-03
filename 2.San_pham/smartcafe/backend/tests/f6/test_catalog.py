"""F6 – UC09 Danh mục (A05), UC10 Món – menu chung (W05)."""
import pytest

from tests import factories as f
from tests.f2.conftest import place_and_pay
from tests.f6.conftest import call, item_body, public_menu

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 64


# ---------- Danh mục ----------
def test_F6_01_tao_sua_danh_muc_va_dem_so_mon(client, org):
    r = call(client, org.admin, "POST", "/api/staff/categories", json={"name": "  Đá   xay ", "sort_order": 3})
    assert r.status_code == 201, r.text
    cat = r.json()
    assert cat == {**cat, "name": "Đá xay", "sort_order": 3, "is_active": True, "item_count": 0}

    r = call(client, org.admin, "PUT", f"/api/staff/categories/{cat['id']}",
             json={"name": "Đá xay", "sort_order": 0, "is_active": False})
    assert r.status_code == 200 and r.json()["is_active"] is False

    rows = call(client, org.admin, "GET", "/api/staff/categories").json()
    assert [c["name"] for c in rows] == ["Đá xay", "Cà phê", "Trà", "Bánh"]          # theo sort_order
    assert {c["name"]: c["item_count"] for c in rows} == {"Đá xay": 0, "Cà phê": 2, "Trà": 1, "Bánh": 0}


@pytest.mark.parametrize("name", ["Cà phê", "cà PHÊ", "  Cà  phê "])
def test_F6_02_ten_danh_muc_trung_khong_phan_biet_hoa_thuong(client, org, name):
    r = call(client, org.admin, "POST", "/api/staff/categories", json={"name": name})
    assert r.status_code == 409 and r.json()["error"]["code"] == "DUPLICATE_VALUE"
    r = call(client, org.admin, "PUT", f"/api/staff/categories/{org.tea.id}", json={"name": name})
    assert r.status_code == 409


@pytest.mark.parametrize("body", [{"name": ""}, {"name": "   "}, {"name": "x" * 51}, {"name": "A", "sort_order": -1}])
def test_F6_03_danh_muc_du_lieu_khong_hop_le(client, org, body):
    r = call(client, org.admin, "POST", "/api/staff/categories", json=body)
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_F6_04_xoa_danh_muc_trong_va_chan_danh_muc_con_mon(client, db, org):
    empty = f.category(db, "Kem", 4)
    assert call(client, org.admin, "DELETE", f"/api/staff/categories/{empty.id}").status_code == 204

    r = call(client, org.admin, "DELETE", f"/api/staff/categories/{org.coffee.id}")
    assert r.status_code == 409 and r.json()["error"]["code"] == "CATEGORY_IN_USE"
    assert r.json()["error"]["details"]["item_count"] == 2

    # Danh mục chỉ còn món đã xóa mềm: vẫn không xóa được (lịch sử đơn), chỉ ẩn
    call(client, org.admin, "DELETE", f"/api/staff/menu-items/{org.tra_dao.id}")
    r = call(client, org.admin, "DELETE", f"/api/staff/categories/{org.tea.id}")
    assert r.status_code == 409 and "chỉ có thể ẩn" in r.json()["error"]["message"]
    assert call(client, org.admin, "DELETE", "/api/staff/categories/99999").status_code == 404


def test_F6_05_an_danh_muc_thi_menu_khach_khong_con_mon_cua_danh_muc(client, org):
    call(client, org.admin, "PUT", f"/api/staff/categories/{org.tea.id}", json={"name": "Trà", "is_active": False})
    assert "Trà đào cam sả" not in public_menu(client, org.cg)
    assert "Cà phê sữa đá" in public_menu(client, org.cg)


# ---------- Món ----------
def test_F6_06_tao_mon_moi_hien_tren_menu_khach_kem_nhan_moi(client, org):
    r = call(client, org.admin, "POST", "/api/staff/menu-items",
             json=item_body(org.tea, tags=[" Matcha ", "SWEET", "matcha", ""], description="  Matcha Nhật  "))
    assert r.status_code == 201, r.text
    m = r.json()
    assert m == {**m, "name": "Matcha đá xay", "category_name": "Trà", "base_price": 55000,
                 "temperature_type": "COLD", "tags": ["matcha", "sweet"], "description": "Matcha Nhật",
                 "image_url": None, "is_active": True}
    menu = public_menu(client, org.cg)
    assert menu["Matcha đá xay"]["is_new"] is True and menu["Matcha đá xay"]["sell_price"] == 55000
    assert "Matcha đá xay" in public_menu(client, org.hd)                   # menu chung: mọi chi nhánh


def test_F6_07_sua_gia_chung_va_an_hien_mon(client, org):
    body = item_body(org.coffee, name="Cà phê sữa đá", price=32000, temperature_type="BOTH", tags=[])
    r = call(client, org.admin, "PUT", f"/api/staff/menu-items/{org.sua_da.id}", json=body)
    assert r.status_code == 200 and r.json()["base_price"] == 32000
    assert public_menu(client, org.cg)["Cà phê sữa đá"]["regular_price"] == 32000

    call(client, org.admin, "PUT", f"/api/staff/menu-items/{org.sua_da.id}", json={**body, "is_active": False})
    assert "Cà phê sữa đá" not in public_menu(client, org.cg)
    listed = call(client, org.admin, "GET", "/api/staff/menu-items", params={"status": "hidden"}).json()
    assert [m["name"] for m in listed] == ["Cà phê sữa đá"]


def test_F6_08_xoa_mem_mon_van_giu_lich_su_don(client, db, org):
    o = place_and_pay(client, org.t_cg, (org.bac_xiu, 2))
    assert call(client, org.admin, "DELETE", f"/api/staff/menu-items/{org.bac_xiu.id}").status_code == 204
    db.refresh(org.bac_xiu)
    assert org.bac_xiu.is_deleted and not org.bac_xiu.is_active
    assert "Bạc xỉu" not in public_menu(client, org.cg)
    names = [m["name"] for m in call(client, org.admin, "GET", "/api/staff/menu-items").json()]
    assert "Bạc xỉu" not in names
    # Đơn cũ vẫn xem được đầy đủ
    v = client.get(f"/api/public/orders/{o['order_id']}", params={"token": o["access_token"]}).json()
    assert v["items"][0]["name"] == "Bạc xỉu"
    # Đã xóa thì không sửa / xóa lại được; tạo món mới trùng tên món đã xóa thì được
    assert call(client, org.admin, "PUT", f"/api/staff/menu-items/{org.bac_xiu.id}",
                json=item_body(org.coffee, name="Bạc xỉu")).status_code == 404
    assert call(client, org.admin, "DELETE", f"/api/staff/menu-items/{org.bac_xiu.id}").status_code == 404
    assert call(client, org.admin, "POST", "/api/staff/menu-items",
                json=item_body(org.coffee, name="Bạc xỉu")).status_code == 201


@pytest.mark.parametrize("patch, field", [
    ({"name": ""}, "name"),
    ({"name": "x" * 101}, "name"),
    ({"base_price": -1}, "base_price"),
    ({"base_price": 10_000_001}, "base_price"),
    ({"temperature_type": "WARM"}, "temperature_type"),
    ({"tags": ["x" * 31]}, "tags"),
    ({"tags": [f"t{i}" for i in range(11)]}, "tags"),
])
def test_F6_09_mon_du_lieu_khong_hop_le(client, org, patch, field):
    r = call(client, org.admin, "POST", "/api/staff/menu-items", json={**item_body(org.tea), **patch})
    assert r.status_code == 422
    assert any(field in e["loc"] for e in r.json()["error"]["details"]["errors"])


def test_F6_10_mon_trung_ten_hoac_sai_danh_muc(client, org):
    r = call(client, org.admin, "POST", "/api/staff/menu-items", json=item_body(org.tea, name="trà ĐÀO cam sả"))
    assert r.status_code == 409 and r.json()["error"]["details"]["field"] == "name"
    r = call(client, org.admin, "PUT", f"/api/staff/menu-items/{org.sua_da.id}",
             json=item_body(org.coffee, name="Bạc xỉu"))
    assert r.status_code == 409
    r = call(client, org.admin, "POST", "/api/staff/menu-items", json={**item_body(org.tea), "category_id": 99999})
    assert r.status_code == 404 and r.json()["error"]["code"] == "CATEGORY_NOT_FOUND"


def test_F6_11_loc_danh_sach_mon(client, org):
    def names(**params):
        return [m["name"] for m in call(client, org.ql, "GET", "/api/staff/menu-items", params=params).json()]

    assert names() == ["Bạc xỉu", "Cà phê sữa đá", "Trà đào cam sả"]       # theo danh mục, tên tiếng Việt
    assert names(category_id=org.tea.id) == ["Trà đào cam sả"]
    assert names(status="active") == names()
    assert call(client, org.ql, "GET", "/api/staff/menu-items", params={"status": "x"}).status_code == 422


@pytest.mark.parametrize("data, ext", [(PNG, "png"), (JPG, "jpg"), (WEBP, "webp")], ids=["png", "jpg", "webp"])
def test_F6_12_upload_anh_mon(client, org, _upload_dir, data, ext):
    r = call(client, org.admin, "POST", f"/api/staff/menu-items/{org.sua_da.id}/image",
             files={"file": ("anh.bin", data, "application/octet-stream")})
    assert r.status_code == 200, r.text
    url = r.json()["image_url"]
    assert url.startswith(f"/api/uploads/menu/{org.sua_da.id}-") and url.endswith(f".{ext}")
    assert (_upload_dir / "menu" / url.rsplit("/", 1)[-1]).read_bytes() == data
    assert public_menu(client, org.cg)["Cà phê sữa đá"]["image_url"] == url


def test_F6_13_upload_anh_moi_xoa_anh_cu(client, org, _upload_dir):
    def up(data):
        return call(client, org.admin, "POST", f"/api/staff/menu-items/{org.sua_da.id}/image",
                    files={"file": ("a.png", data, "image/png")}).json()["image_url"]

    first = up(PNG)
    second = up(JPG)
    assert first != second
    assert [p.name for p in (_upload_dir / "menu").iterdir()] == [second.rsplit("/", 1)[-1]]


@pytest.mark.parametrize("data, status", [
    (b"GIF89a" + b"\x00" * 10, 422),                       # sai định dạng
    (b"<script>alert(1)</script>", 422),                   # đổi đuôi .png nhưng không phải ảnh
    (PNG + b"\x00" * (2 * 1024 * 1024), 413),              # quá 2 MB
], ids=["gif", "khong_phai_anh", "qua_2MB"])
def test_F6_14_upload_anh_khong_hop_le(client, org, _upload_dir, data, status):
    r = call(client, org.admin, "POST", f"/api/staff/menu-items/{org.sua_da.id}/image",
             files={"file": ("anh.png", data, "image/png")})
    assert r.status_code == status and r.json()["error"]["code"] == "INVALID_IMAGE"
    assert not (_upload_dir / "menu").exists() or not any((_upload_dir / "menu").iterdir())
