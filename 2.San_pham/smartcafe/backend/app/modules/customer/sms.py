"""Cổng gửi SMS (D12). Hiện chỉ có bản giả lập; gắn nhà cung cấp SMS thật bằng cách thay get_sms_sender."""
import logging
from typing import Protocol

from app.modules.customer.phone import mask_phone

log = logging.getLogger("smartcafe.sms")


class SmsSender(Protocol):
    def send_otp(self, phone: str, code: str) -> None: ...


class MockSmsSender:
    """Không gửi SMS thật: ghi "tin nhắn" ra log backend (SD01), SĐT được che.
    Khi OTP_DEMO_MODE tắt, người demo lấy mã bằng `docker compose logs backend`."""

    def send_otp(self, phone: str, code: str) -> None:
        log.info("[Mock SMS] Gửi tới %s: Mã xác thực SmartCafe của bạn là %s (hiệu lực 5 phút)", mask_phone(phone), code)


_sender = MockSmsSender()


def get_sms_sender() -> SmsSender:
    return _sender
