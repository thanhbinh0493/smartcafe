from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import get_settings
from app.modules.customer import service as customer_service
from tests.f3.conftest import Bar

PHONE = "0912345678"


class Clock:
    """Đồng hồ giả cho service OTP: test tự tua thời gian (60 giây, 5 phút, 1 giờ)."""

    def __init__(self):
        self.t = datetime.now(timezone.utc)

    def __call__(self) -> datetime:
        return self.t

    def advance(self, **kw) -> None:
        self.t += timedelta(**kw)


@pytest.fixture
def clock(monkeypatch) -> Clock:
    c = Clock()
    monkeypatch.setattr(customer_service, "_now", c)
    return c


@pytest.fixture
def shop(db) -> Bar:
    return Bar(db)


def request_otp(client, phone: str = PHONE):
    return client.post("/api/public/otp/request", json={"phone": phone})


def verify(client, code: str, phone: str = PHONE):
    return client.post("/api/public/otp/verify", json={"phone": phone, "code": code})


def login(client, phone: str = PHONE) -> dict:
    """Gửi mã + xác thực đúng (chế độ demo trả mã) → body của /otp/verify."""
    r = request_otp(client, phone)
    assert r.status_code == 200, r.text
    v = verify(client, r.json()["demo_code"], phone)
    assert v.status_code == 200, v.text
    return v.json()


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def expired_customer_token(customer_id: int) -> str:
    s = get_settings()
    past = datetime.now(timezone.utc) - timedelta(minutes=61)
    payload = {"sub": str(customer_id), "typ": "customer", "role": "CUSTOMER", "iat": past,
               "exp": past + timedelta(minutes=60)}
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_algorithm)


def wrong(code: str) -> str:
    return f"{(int(code) + 1) % 1_000_000:06d}"
