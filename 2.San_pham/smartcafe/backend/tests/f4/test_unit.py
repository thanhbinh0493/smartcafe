"""F4 – Hàm thuần: chuẩn hóa / che SĐT, băm OTP, customer token 1 giờ."""
import jwt
import pytest

from app.core.security import create_customer_token, decode_token, hash_otp
from app.modules.customer.phone import mask_phone, normalize_phone


@pytest.mark.parametrize("raw", [
    "0912345678", "0912 345 678", "0912.345.678", "0912-345-678", "+84912345678", "84912345678", "+84 912 345 678",
])
def test_F4_01_chuan_hoa_sdt_hop_le(raw):
    assert normalize_phone(raw) == "0912345678"


@pytest.mark.parametrize("raw", [
    "", "abc", "091234567", "09123456789", "0212345678", "0112345678", "1912345678", "+1 912345678", "09123456a8",
])
def test_F4_02_sdt_khong_hop_le(raw):
    assert normalize_phone(raw) is None


def test_F4_03_che_sdt():
    assert mask_phone("0912345678") == "0912 *** 678"


def test_F4_04_bam_otp_khong_luu_ma_ro():
    h = hash_otp("0912345678", "482107")
    assert "482107" not in h and len(h) == 64
    assert h == hash_otp("0912345678", "482107")
    assert h != hash_otp("0987654321", "482107")  # cùng mã, khác SĐT → khác băm
    assert h != hash_otp("0912345678", "482108")


def test_F4_05_customer_token_1_gio():
    token, exp = create_customer_token(7)
    p = decode_token(token)
    assert (p["sub"], p["typ"], p["role"]) == ("7", "customer", "CUSTOMER")
    assert p["exp"] - p["iat"] == 3600
    assert int(exp.timestamp()) == p["exp"]
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(token + "x")
