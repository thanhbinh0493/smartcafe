from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

REASON_MIN, REASON_MAX = 5, 255


class CancelIn(BaseModel):
    reason: str = Field(max_length=REASON_MAX)

    @field_validator("reason")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if len(v) < REASON_MIN:
            raise ValueError(f"Lý do hủy cần ít nhất {REASON_MIN} ký tự")
        return v


class SupportItemOut(BaseModel):
    id: int
    name: str
    quantity: int
    unit_price: int
    note: str | None
    status: str


class SupportPaymentOut(BaseModel):
    method: str
    amount: int
    status: str                # SUCCESS | FAILED | REFUNDED
    transaction_ref: str
    refunded_at: datetime | None


class SupportOrderOut(BaseModel):
    """Đơn hiển thị cho thu ngân khi hỗ trợ khách (UC20)."""
    id: int
    order_code: str
    order_date: date
    table_number: str
    status: str
    total: int
    is_member: bool
    note: str | None
    created_at: datetime
    paid_at: datetime | None
    cancelled_at: datetime | None
    cancel_reason: str | None
    cancelled_by: str | None   # họ tên nhân viên đã hủy
    can_cancel: bool           # chỉ PAID / PREPARING
    payment: SupportPaymentOut | None
    items: list[SupportItemOut]
