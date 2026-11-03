"""F6 – UC12 Quản lý nhân viên & phân quyền (A04)."""
import pytest

from tests.f3.conftest import auth
from tests.f6.conftest import call, staff_body


def login(client, username, password):
    return client.post("/api/auth/login", json={"username": username, "password": password})


def put_body(s, **kw) -> dict:
    return {"full_name": s.full_name, "phone": s.phone, "role": s.role, "branch_id": s.branch_id,
            "is_active": s.is_active, **kw}


def test_F6_29_admin_tao_nhan_vien_dang_nhap_duoc_ngay(client, db, org):
    r = call(client, org.admin, "POST", "/api/staff/staff",
             json=staff_body(" PC_Moi ", "BARISTA", org.cg, phone="0912 345 678"))
    assert r.status_code == 201, r.text
    s = r.json()
    assert s == {**s, "username": "pc_moi", "role": "BARISTA", "branch_id": org.cg.id,
                 "branch_name": "Chi nhánh CG", "is_active": True, "phone": "0912 345 678"}
    assert "password" not in s and "password_hash" not in s
    r = login(client, "pc_moi", "matkhau123")
    assert r.status_code == 200 and r.json()["staff"]["branch"]["code"] == "CG"
    from app.models import Staff
    assert db.get(Staff, s["id"]).password_hash.startswith("$2b$12$")                   # NFR-S1: bcrypt


def test_F6_30_quy_tac_vai_tro_va_chi_nhanh(client, org):
    def create(**kw):
        return call(client, org.admin, "POST", "/api/staff/staff", json={**staff_body(), **kw})

    assert create(username="ad2", role="ADMIN", branch_id=None).status_code == 201
    r = create(username="ad3", role="ADMIN", branch_id=org.cg.id)
    assert r.status_code == 422 and r.json()["error"]["details"]["field"] == "branch_id"
    r = create(username="pc3", role="BARISTA", branch_id=None)
    assert r.status_code == 422 and r.json()["error"]["details"]["field"] == "branch_id"
    assert create(username="pc4", branch_id=99999).status_code == 404
    r = create(username="TN_CG", branch_id=org.cg.id)                                                          # trùng (không phân biệt hoa thường)
    assert r.status_code == 409 and r.json()["error"]["details"]["field"] == "username"


@pytest.mark.parametrize("patch", [{"username": "ab"}, {"username": "có dấu"}, {"username": "a" * 51},
                                   {"password": "1234567"}, {"full_name": " "}, {"role": "OWNER"},
                                   {"phone": "abc"}])
def test_F6_31_nhan_vien_du_lieu_khong_hop_le(client, org, patch):
    r = call(client, org.admin, "POST", "/api/staff/staff", json={**staff_body(branch=org.cg), **patch})
    assert r.status_code == 422


def test_F6_32_quan_ly_chi_tao_thu_ngan_pha_che_chi_nhanh_minh(client, org):
    r = call(client, org.ql, "POST", "/api/staff/staff", json=staff_body("tn_moi", "CASHIER", None))
    assert r.status_code == 201 and r.json()["branch_id"] == org.cg.id                   # mặc định chi nhánh mình
    for role, branch in (("MANAGER", org.cg), ("ADMIN", None), ("BARISTA", org.hd)):
        r = call(client, org.ql, "POST", "/api/staff/staff", json=staff_body("x_" + role.lower(), role, branch))
        assert r.status_code == 403, role


def test_F6_33_quan_ly_chi_xem_va_sua_nhan_vien_chi_nhanh_minh(client, org):
    rows = call(client, org.ql, "GET", "/api/staff/staff").json()
    assert {s["username"] for s in rows} == {"ql_cg", "tn_cg", "pc_cg"}
    # Tham số branch_id của chi nhánh khác bị bỏ qua
    rows = call(client, org.ql, "GET", "/api/staff/staff", params={"branch_id": org.hd.id}).json()
    assert {s["username"] for s in rows} == {"ql_cg", "tn_cg", "pc_cg"}

    r = call(client, org.ql, "PUT", f"/api/staff/staff/{org.pc.id}", json=put_body(org.pc, role="CASHIER"))
    assert r.status_code == 200 and r.json()["role"] == "CASHIER"
    for target in (org.pc_hd, org.ql_hd, org.admin):
        assert call(client, org.ql, "PUT", f"/api/staff/staff/{target.id}", json=put_body(target)).status_code == 403
    r = call(client, org.ql, "PUT", f"/api/staff/staff/{org.tn.id}", json=put_body(org.tn, role="MANAGER"))
    assert r.status_code == 403
    r = call(client, org.ql, "PUT", f"/api/staff/staff/{org.tn.id}", json=put_body(org.tn, branch_id=org.hd.id))
    assert r.status_code == 403


def test_F6_34_admin_loc_danh_sach(client, org):
    rows = call(client, org.admin, "GET", "/api/staff/staff").json()
    assert rows[0]["username"] == "admin" and len(rows) == 6                            # ADMIN (trụ sở) đứng đầu
    rows = call(client, org.admin, "GET", "/api/staff/staff", params={"branch_id": org.hd.id, "role": "BARISTA"})
    assert [s["username"] for s in rows.json()] == ["pc_hd"]


def test_F6_35_khoa_tai_khoan_co_hieu_luc_ngay(client, org):
    headers = auth(org.pc)
    assert client.get("/api/auth/me", headers=headers).status_code == 200
    r = call(client, org.ql, "PUT", f"/api/staff/staff/{org.pc.id}", json=put_body(org.pc, is_active=False))
    assert r.status_code == 200 and r.json()["is_active"] is False
    assert client.get("/api/auth/me", headers=headers).status_code == 401                # token cũ hết dùng được
    r = login(client, "pc_cg", "secret123")
    assert r.status_code == 403 and r.json()["error"]["code"] == "ACCOUNT_LOCKED"
    call(client, org.ql, "PUT", f"/api/staff/staff/{org.pc.id}", json=put_body(org.pc, is_active=True))
    assert login(client, "pc_cg", "secret123").status_code == 200


def test_F6_36_dat_lai_mat_khau(client, org):
    r = call(client, org.ql, "PUT", f"/api/staff/staff/{org.tn.id}", json=put_body(org.tn, password="moi12345"))
    assert r.status_code == 200
    assert login(client, "tn_cg", "secret123").status_code == 401
    assert login(client, "tn_cg", "moi12345").status_code == 200
    # Không gửi mật khẩu = giữ nguyên
    call(client, org.ql, "PUT", f"/api/staff/staff/{org.tn.id}", json=put_body(org.tn, full_name="Tên mới"))
    assert login(client, "tn_cg", "moi12345").status_code == 200


@pytest.mark.parametrize("who, patch", [
    ("admin", {"is_active": False}), ("admin", {"role": "MANAGER"}),
    ("ql", {"is_active": False}), ("ql", {"role": "CASHIER"}), ("ql", {"branch_id": "hd"}),
])
def test_F6_37_khong_tu_khoa_tu_doi_vai_tro_cua_minh(client, org, who, patch):
    me = getattr(org, who)
    if patch.get("branch_id") == "hd":
        patch = {"branch_id": org.hd.id}
    if patch.get("role") == "MANAGER":
        patch = {**patch, "branch_id": org.cg.id}
    r = call(client, me, "PUT", f"/api/staff/staff/{me.id}", json=put_body(me, **patch))
    assert r.status_code == 409 and r.json()["error"]["code"] == "CANNOT_MODIFY_SELF"


def test_F6_38_tu_sua_ten_va_mat_khau_cua_minh(client, org):
    r = call(client, org.ql, "PUT", f"/api/staff/staff/{org.ql.id}",
             json=put_body(org.ql, full_name="Lê Văn Q", password="moi12345"))
    assert r.status_code == 200 and r.json()["full_name"] == "Lê Văn Q"
    assert login(client, "ql_cg", "moi12345").status_code == 200
    assert call(client, org.admin, "PUT", "/api/staff/staff/99999", json=put_body(org.tn)).status_code == 404
