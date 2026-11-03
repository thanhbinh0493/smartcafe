"""F4 – UC02 bước 1–2: gửi OTP giả lập, giới hạn gửi (NFR-S4), không lộ SĐT đã là thành viên."""
import logging
from datetime import timedelta

from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.security import hash_otp
from app.models import Customer, OtpRequest
from app.modules.customer.sms import get_sms_sender
from app.main import app
from tests import factories as f
from tests.f4.conftest import PHONE, request_otp


def test_F4_06_gui_otp_thanh_cong(client, db, clock):
    r = request_otp(client, "0912 345 678")
    assert r.status_code == 200
    body = r.json()
    assert body["expires_in"] == 300 and body["resend_after"] == 60
    assert body["phone_masked"] == "0912 *** 678"
    code = body["demo_code"]
    assert len(code) == 6 and code.isdigit()

    otp = db.scalar(select(OtpRequest).where(OtpRequest.phone == PHONE))  # lưu SĐT đã chuẩn hóa
    assert otp.code_hash == hash_otp(PHONE, code) and code not in otp.code_hash
    assert otp.expires_at - otp.created_at == timedelta(minutes=5)
    assert otp.attempts == 0 and otp.verified_at is None
    # Chưa xác thực thì chưa lưu khách (NFR-S7)
    assert db.scalar(select(func.count()).select_from(Customer)) == 0


def test_F4_07_sdt_sai_dinh_dang(client, db):
    r = request_otp(client, "12345")
    assert r.status_code == 422
    err = r.json()["error"]
    assert err["code"] == "VALIDATION_ERROR" and "Số điện thoại không hợp lệ" in err["message"]
    assert db.scalar(select(func.count()).select_from(OtpRequest)) == 0


def test_F4_08_gui_lai_truoc_60_giay(client, db, clock):
    assert request_otp(client).status_code == 200
    clock.advance(seconds=45)
    r = request_otp(client)
    assert r.status_code == 429
    err = r.json()["error"]
    assert err["code"] == "OTP_RATE_LIMITED" and err["details"]["retry_after"] == 15
    assert "15 giây" in err["message"]
    clock.advance(seconds=15)
    assert request_otp(client).status_code == 200


def test_F4_09_toi_da_5_ma_moi_gio(client, db, clock):
    for _ in range(5):
        assert request_otp(client).status_code == 200
        clock.advance(seconds=61)
    r = request_otp(client)  # mã thứ 6 trong vòng 1 giờ
    assert r.status_code == 429
    err = r.json()["error"]
    assert err["code"] == "OTP_RATE_LIMITED" and "quá 5 mã" in err["message"]
    # Mã đầu tiên gửi lúc t0, hiện tại t0 + 305 giây → còn 3600 - 305 = 3295 giây
    assert err["details"]["retry_after"] == 3295
    clock.advance(seconds=3295)
    assert request_otp(client).status_code == 200


def test_F4_10_gioi_han_tinh_rieng_tung_sdt(client, db, clock):
    assert request_otp(client, "0912345678").status_code == 200
    assert request_otp(client, "0987654321").status_code == 200


def test_F4_11_khong_lo_sdt_da_la_thanh_vien(client, db, clock):
    f.customer(db, "0987654321", points=120)
    a = request_otp(client, "0912345678").json()
    b = request_otp(client, "0987654321").json()
    assert set(a) == set(b)
    for k in ("expires_in", "resend_after"):
        assert a[k] == b[k]


def test_F4_12_tat_demo_mode_khong_tra_ma(client, db, clock, monkeypatch):
    monkeypatch.setattr(get_settings(), "otp_demo_mode", False)
    r = request_otp(client)
    assert r.status_code == 200 and r.json()["demo_code"] is None


def test_F4_13_gui_qua_cong_sms_gia_lap_log_che_sdt(client, db, clock, caplog):
    sent = []

    class Spy:
        def send_otp(self, phone, code):
            sent.append((phone, code))

    app.dependency_overrides[get_sms_sender] = lambda: Spy()
    r = request_otp(client)
    del app.dependency_overrides[get_sms_sender]
    assert sent == [(PHONE, r.json()["demo_code"])]

    # Bản giả lập mặc định ghi "tin nhắn" ra log backend (SD01) với SĐT đã che
    logging.getLogger("smartcafe.sms").disabled = False  # alembic fileConfig ở fixture engine tắt logger cũ
    caplog.set_level(logging.INFO, logger="smartcafe.sms")
    clock.advance(seconds=61)
    code = request_otp(client).json()["demo_code"]
    assert "0912 *** 678" in caplog.text and code in caplog.text and PHONE not in caplog.text
