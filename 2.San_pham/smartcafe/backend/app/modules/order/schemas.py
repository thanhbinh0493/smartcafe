from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

MAX_QTY_PER_ITEM = 20   # UC05: mỗi món tối đa 20 ly/đơn
MAX_LINES = 30


class OrderItemIn(BaseModel):
    menu_item_id: int
    quantity: int = Field(ge=1, le=MAX_QTY_PER_ITEM)
    note: str | None = Field(default=None, max_length=255)
    is_recommended: bool = False


class CreateOrderRequest(BaseModel):
    qr_token: str = Field(min_length=1, max_length=64)
    items: list[OrderItemIn] = Field(min_length=1, max_length=MAX_LINES)
    note: str | None = Field(default=None, max_length=255)
    # Tổng tiền khách đang thấy trên giỏ hàng. Nếu khác tổng server tính lại -> 409 PRICE_CHANGED (UC05 – 3b)
    expected_total: int | None = Field(default=None, ge=0)


class OrderLineOut(BaseModel):
    id: int
    menu_item_id: int
    name: str
    quantity: int
    original_price: int
    unit_price: int
    is_promo: bool
    note: str | None
    status: str


class CreateOrderResponse(BaseModel):
    order_id: int
    order_code: str
    access_token: str
    status: str
    subtotal: int          # tổng theo giá thường
    discount: int          # giảm nhờ khuyến mãi
    total: int
    expected_points: int | None  # chỉ có với khách thành viên (F4)
    items: list[OrderLineOut]


class PayRequest(BaseModel):
    access_token: str = Field(min_length=1, max_length=64)
    method: Literal["MOCK_EWALLET", "MOCK_CARD"]


class PayResponse(BaseModel):
    order_id: int
    status: str
    paid_at: datetime
    transaction_ref: str


class OrderView(BaseModel):
    id: int
    order_code: str
    order_date: date
    status: str
    branch_name: str
    table_number: str
    subtotal: int
    discount: int
    total: int
    queue_position: int | None   # vị trí trong hàng đợi pha chế (chỉ khi PAID / PREPARING)
    created_at: datetime
    paid_at: datetime | None
    ready_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    cancel_reason: str | None
    points_earned: int | None = None  # điểm đã cộng khi đơn hoàn tất (chỉ khách thành viên)
    items: list[OrderLineOut]
