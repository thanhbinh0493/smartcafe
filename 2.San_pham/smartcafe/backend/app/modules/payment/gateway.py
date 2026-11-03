"""Cổng thanh toán (NFR-M4): logic nghiệp vụ chỉ gọi qua interface PaymentGateway,
để có thể thay MockPaymentGateway bằng cổng thật (VNPay/MoMo) mà không sửa module đơn hàng."""
import secrets
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ChargeResult:
    success: bool
    transaction_ref: str
    message: str = ""


class PaymentGateway(Protocol):
    def charge(self, amount: int, method: str, order_code: str) -> ChargeResult: ...

    def refund(self, transaction_ref: str, amount: int) -> ChargeResult: ...


class MockPaymentGateway:
    """II.2 Mục 4: luôn thành công, trừ khi số tiền kết thúc bằng 999 thì thất bại (để demo luồng lỗi)."""

    def charge(self, amount: int, method: str, order_code: str) -> ChargeResult:
        ref = f"MOCK-{secrets.token_hex(8).upper()}"
        if amount % 1000 == 999:
            return ChargeResult(False, ref, "Giao dịch bị từ chối (giả lập)")
        return ChargeResult(True, ref)

    def refund(self, transaction_ref: str, amount: int) -> ChargeResult:
        return ChargeResult(True, transaction_ref)


_gateway: PaymentGateway = MockPaymentGateway()


def get_payment_gateway() -> PaymentGateway:
    return _gateway
