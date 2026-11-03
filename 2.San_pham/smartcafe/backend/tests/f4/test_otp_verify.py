"""F4 – UC02 bước 3–4: xác thực OTP, tạo khách khi SĐT mới, các ngoại lệ 4a / 4b."""
import pytest
from sqlalchemy import func, select

from app.core.security import decode_token
from app.models import Customer, OtpRequest
from tests import factories as f
from tests.f4.conftest import PHONE, request_otp, verify, wrong


def latest_otp(db) -> OtpRequest:
    db.expire_all()
    return db.scalar(select(OtpRequest).where(OtpRequest.phone == PHONE).order_by(OtpRequest.id.desc()))


def test_F4_14_xac_thuc_dung_tao_khach_moi(client, db, clock):
    code = request_otp(client).json()["demo_code"]
    r = verify(client, code)
    assert r.status_code == 200
    body = r.json()
    assert body["loyalty_points"] == 0 and body["name"] is None and body["phone_masked"] == "0912 *** 678"
    assert body["expires_at"]
    cust = db.scalar(select(Customer).where(Customer.phone == PHONE))
    assert cust is not None and cust.last_verified_at is not None
    p = decode_token(body["customer_token"])
    assert p["typ"] == "customer" and p["sub"] == str(cust.id)
    assert latest_otp(db).verified_at is not None


def test_F4_15_khach_cu_giu_nguyen_diem(client, db, clock):
    old = f.customer(db, PHONE, points=120)
    code = request_otp(client).json()["demo_code"]
    body = verify(client, code).json()
    assert body["loyalty_points"] == 120
    assert decode_token(body["customer_token"])["sub"] == str(old.id)
    assert db.scalar(select(func.count()).select_from(Customer)) == 1


def test_F4_16_sai_ma_bao_so_lan_con_lai(client, db, clock):
    code = request_otp(client).json()["demo_code"]
    r = verify(client, wrong(code))
    assert r.status_code == 400
    err = r.json()["error"]
    assert err["code"] == "OTP_INVALID" and err["details"] == {"reason": "WRONG", "attempts_left": 4}
    assert "còn 4 lần" in err["message"]
    assert latest_otp(db).attempts == 1  # số lần sai được lưu dù request lỗi
    assert db.scalar(select(func.count()).select_from(Customer)) == 0
    assert verify(client, code).status_code == 200  # nhập lại đúng vẫn được


def test_F4_17_sai_5_lan_huy_ma(client, db, clock):
    code = request_otp(client).json()["demo_code"]
    for left in (4, 3, 2, 1):
        assert verify(client, wrong(code)).json()["error"]["details"]["attempts_left"] == left
    err = verify(client, wrong(code)).json()["error"]
    assert err["details"]["reason"] == "LOCKED" and "yêu cầu mã mới" in err["message"]
    # Mã đã bị hủy: nhập đúng cũng không được, số lần thử không tăng thêm
    r = verify(client, code)
    assert r.status_code == 400 and r.json()["error"]["details"]["reason"] == "LOCKED"
    assert latest_otp(db).attempts == 5
    # Yêu cầu mã mới thì dùng được
    clock.advance(seconds=60)
    assert verify(client, request_otp(client).json()["demo_code"]).status_code == 200


def test_F4_18_ma_het_han_sau_5_phut(client, db, clock):
    code = request_otp(client).json()["demo_code"]
    clock.advance(seconds=299)
    assert verify(client, wrong(code)).json()["error"]["details"]["reason"] == "WRONG"  # còn hạn
    clock.advance(seconds=1)  # đúng 5 phút
    r = verify(client, code)
    assert r.status_code == 400 and r.json()["error"]["details"]["reason"] == "EXPIRED"
    assert "hết hạn" in r.json()["error"]["message"]


def test_F4_19_ma_da_dung_khong_dung_lai_duoc(client, db, clock):
    code = request_otp(client).json()["demo_code"]
    assert verify(client, code).status_code == 200
    r = verify(client, code)
    assert r.status_code == 400 and r.json()["error"]["details"]["reason"] == "NOT_FOUND"


def test_F4_20_ma_moi_thay_ma_cu(client, db, clock):
    old = request_otp(client).json()["demo_code"]
    clock.advance(seconds=60)
    new = request_otp(client).json()["demo_code"]
    if old != new:
        assert verify(client, old).json()["error"]["details"]["reason"] == "WRONG"
    assert verify(client, new).status_code == 200


def test_F4_21_chua_yeu_cau_ma(client, db, clock):
    r = verify(client, "123456")
    assert r.status_code == 400 and r.json()["error"]["details"]["reason"] == "NOT_FOUND"


def test_F4_22_ma_sai_dinh_dang(client, db, clock):
    request_otp(client)
    for bad in ("12345", "1234567", "12a456", ""):
        r = verify(client, bad)
        assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"
    assert latest_otp(db).attempts == 0  # sai định dạng không tính là một lần thử


def test_F4_23_sdt_nhieu_cach_viet(client, db, clock):
    code = request_otp(client, "+84 912 345 678").json()["demo_code"]
    assert verify(client, code, "0912.345.678").status_code == 200
    assert db.scalar(select(Customer.phone)) == PHONE


def test_F4_24_ma_cua_sdt_khac_khong_dung_duoc(client, db, clock):
    other = request_otp(client, "0987654321").json()["demo_code"]
    mine = request_otp(client, PHONE).json()["demo_code"]
    if other == mine:
        pytest.skip("2 mã ngẫu nhiên trùng nhau (xác suất 1/10^6)")
    r = verify(client, other, PHONE)
    assert r.status_code == 400 and r.json()["error"]["details"]["reason"] == "WRONG"
