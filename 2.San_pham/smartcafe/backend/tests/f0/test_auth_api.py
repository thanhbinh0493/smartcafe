"""F0 – API đăng nhập nhân viên (UC08) và /api/auth/me."""
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import get_settings
from app.core.security import create_staff_token
from tests import factories as f


def login(client, username, password=f.PASSWORD):
    return client.post("/api/auth/login", json={"username": username, "password": password})


def test_F0_15_dang_nhap_thanh_cong_tra_token_va_thong_tin(client, db):
    b = f.branch(db, "CG")
    f.staff(db, "pc1_cg", "BARISTA", b)
    r = login(client, "pc1_cg")
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 8 * 3600
    assert body["staff"]["role"] == "BARISTA"
    assert body["staff"]["branch"] == {"id": b.id, "code": "CG", "name": "Chi nhánh CG"}
    assert body["access_token"]


def test_F0_16_admin_dang_nhap_khong_co_chi_nhanh(client, db):
    f.staff(db, "admin", "ADMIN")
    r = login(client, "admin")
    assert r.status_code == 200
    assert r.json()["staff"]["branch"] is None


def test_F0_17_sai_mat_khau_va_sai_ten_cung_mot_thong_bao(client, db):
    f.staff(db, "admin", "ADMIN")
    r1 = login(client, "admin", "sai-mat-khau")
    r2 = login(client, "khong_ton_tai")
    assert r1.status_code == r2.status_code == 401
    assert r1.json() == r2.json()
    assert r1.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_F0_18_tai_khoan_bi_khoa_khong_dang_nhap_duoc(client, db):
    b = f.branch(db)
    f.staff(db, "tn_cg", "CASHIER", b, is_active=False)
    r = login(client, "tn_cg")
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "ACCOUNT_LOCKED"


def test_F0_19_du_lieu_dang_nhap_rong_tra_loi_validation_dung_dinh_dang(client):
    r = client.post("/api/auth/login", json={"username": "", "password": ""})
    assert r.status_code == 422
    err = r.json()["error"]
    assert err["code"] == "VALIDATION_ERROR"
    assert set(err) == {"code", "message", "details"}


def test_F0_20_me_tra_thong_tin_nguoi_dang_nhap(client, db):
    b = f.branch(db)
    s = f.staff(db, "ql_cg", "MANAGER", b)
    token = login(client, "ql_cg").json()["access_token"]
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["id"] == s.id and r.json()["role"] == "MANAGER"


def test_F0_21_me_khong_co_token(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHORIZED"


def test_F0_22_me_token_rac(client):
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer abc.def.ghi"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHORIZED"


def test_F0_23_me_token_het_han(client, db):
    s = f.staff(db, "admin", "ADMIN")
    st = get_settings()
    past = datetime.now(timezone.utc) - timedelta(hours=9)
    token = jwt.encode({"sub": str(s.id), "typ": "staff", "role": "ADMIN", "iat": past,
                        "exp": past + timedelta(hours=8)}, st.jwt_secret, algorithm=st.jwt_algorithm)
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "TOKEN_EXPIRED"


def test_F0_24_token_khach_khong_goi_duoc_api_nhan_vien(client, db):
    """NFR-S2: JWT khách thành viên (typ=customer) không được dùng cho API nhân viên."""
    st = get_settings()
    now = datetime.now(timezone.utc)
    token = jwt.encode({"sub": "1", "typ": "customer", "iat": now, "exp": now + timedelta(hours=1)},
                       st.jwt_secret, algorithm=st.jwt_algorithm)
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "FORBIDDEN"


def test_F0_25_tai_khoan_bi_khoa_sau_khi_da_co_token(client, db):
    b = f.branch(db)
    s = f.staff(db, "pc2_cg", "BARISTA", b)
    token = create_staff_token(s.id, s.role, s.branch_id)
    s.is_active = False
    db.flush()
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
