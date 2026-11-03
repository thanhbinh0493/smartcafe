"""F4 – Nhiều request OTP cùng lúc (mỗi request một kết nối CSDL thật): không vượt giới hạn gửi,
không vượt 5 lần thử, 1 mã chỉ đăng nhập được 1 lần và chỉ tạo 1 khách. Dữ liệu được commit nên test tự dọn."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Customer, OtpRequest
from app.modules.customer import service
from app.modules.customer.sms import MockSmsSender

PHONE = "0900000099"
N = 8


@pytest.fixture
def clean(engine):
    yield
    with engine.begin() as c:
        c.execute(text("TRUNCATE otp_requests, loyalty_transactions, customers RESTART IDENTITY CASCADE"))


def run_parallel(engine, fn):
    barrier = Barrier(N)

    def worker(_):
        with Session(engine) as s:
            barrier.wait()
            try:
                res = fn(s)
                s.commit()
                return "ok", res
            except service.VerifyFailure as e:
                s.commit()
                return e.error.details.get("reason"), None
            except AppError as e:
                s.rollback()
                return e.code if e.code != "OTP_INVALID" else e.details.get("reason"), None

    with ThreadPoolExecutor(N) as ex:
        return list(ex.map(worker, range(N)))


def test_F4_33_gui_otp_dong_thoi_chi_1_ma(engine, clean):
    results = run_parallel(engine, lambda s: service.request_otp(s, PHONE, MockSmsSender()))
    kinds = sorted(k for k, _ in results)
    assert kinds.count("ok") == 1 and kinds.count("OTP_RATE_LIMITED") == N - 1
    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(OtpRequest)) == 1


def test_F4_34_doan_ma_dong_thoi_khong_vuot_5_lan(engine, clean):
    with Session(engine) as s:
        code = service.request_otp(s, PHONE, MockSmsSender()).demo_code
        s.commit()
    bad = f"{(int(code) + 1) % 1_000_000:06d}"
    results = run_parallel(engine, lambda s: service.verify_otp(s, PHONE, bad))
    kinds = [k for k, _ in results]
    assert kinds.count("WRONG") == 4 and kinds.count("LOCKED") == N - 4
    with Session(engine) as s:
        assert s.scalar(select(OtpRequest.attempts)) == 5
        with pytest.raises(AppError):  # mã đúng cũng không dùng được nữa
            service.verify_otp(s, PHONE, code)


def test_F4_35_dung_ma_dong_thoi_chi_1_lan_1_khach(engine, clean):
    with Session(engine) as s:
        code = service.request_otp(s, PHONE, MockSmsSender()).demo_code
        s.commit()
    results = run_parallel(engine, lambda s: service.verify_otp(s, PHONE, code))
    kinds = [k for k, _ in results]
    assert kinds.count("ok") == 1 and kinds.count("NOT_FOUND") == N - 1
    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(Customer)) == 1
