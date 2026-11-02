"""F0 – Băm mật khẩu và JWT (đơn vị)."""
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import get_settings
from app.core.security import create_staff_token, decode_token, hash_password, verify_password


def test_F0_10_bam_va_kiem_tra_mat_khau():
    h = hash_password("matkhau")
    assert h != "matkhau"
    assert verify_password("matkhau", h)
    assert not verify_password("sai", h)


def test_F0_11_hash_hong_khong_gay_loi():
    assert not verify_password("x", "khong-phai-bcrypt")


def test_F0_12_jwt_nhan_vien_chua_dung_thong_tin_va_het_han_8_gio():
    token = create_staff_token(7, "BARISTA", 2)
    p = decode_token(token)
    assert p["sub"] == "7" and p["typ"] == "staff" and p["role"] == "BARISTA" and p["branch_id"] == 2
    assert p["exp"] - p["iat"] == get_settings().staff_token_hours * 3600 == 8 * 3600


def test_F0_13_jwt_sai_chu_ky_bi_tu_choi():
    s = get_settings()
    forged = jwt.encode({"sub": "1", "typ": "staff"}, "khoa-khac-" + "x" * 32, algorithm=s.jwt_algorithm)
    with pytest.raises(jwt.InvalidSignatureError):
        decode_token(forged)


def test_F0_14_jwt_het_han_bi_tu_choi():
    s = get_settings()
    past = datetime.now(timezone.utc) - timedelta(hours=9)
    expired = jwt.encode({"sub": "1", "typ": "staff", "iat": past, "exp": past + timedelta(hours=8)},
                         s.jwt_secret, algorithm=s.jwt_algorithm)
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(expired)
