from datetime import datetime

from pydantic import BaseModel, Field


class OtpRequestIn(BaseModel):
    phone: str = Field(min_length=1, max_length=20)


class OtpRequestOut(BaseModel):
    expires_in: int              # giây tới khi mã hết hạn
    resend_after: int            # giây tới khi được gửi lại
    phone_masked: str
    demo_code: str | None = None  # chỉ có khi OTP_DEMO_MODE bật (khung [DEMO] ở W00a)


class OtpVerifyIn(BaseModel):
    phone: str = Field(min_length=1, max_length=20)
    code: str = Field(pattern=r"^\d{6}$")


class OtpVerifyOut(BaseModel):
    customer_token: str
    expires_at: datetime         # phiên thành viên hết hạn (1 giờ – D18)
    phone_masked: str
    loyalty_points: int


class LoyaltyTxOut(BaseModel):
    order_code: str | None
    points: int
    type: str
    created_at: datetime


class CustomerMe(BaseModel):
    phone_masked: str
    loyalty_points: int
    point_value_vnd: int         # giá trị 1 điểm (100đ)
    points_value: int            # loyalty_points × point_value_vnd
    recent_transactions: list[LoyaltyTxOut]
