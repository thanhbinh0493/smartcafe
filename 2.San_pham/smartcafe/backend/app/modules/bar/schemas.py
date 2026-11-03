from datetime import datetime

from pydantic import BaseModel


class QueueItemOut(BaseModel):
    """Một dòng của hàng đợi pha chế (W04): từng món chưa xong."""
    id: int
    order_id: int
    order_code: str
    table_number: str
    paid_at: datetime          # "giờ gọi" = giờ thanh toán của đơn
    name: str
    quantity: int
    note: str | None
    order_note: str | None
    status: str                # WAITING | PREPARING
    started_at: datetime | None


class QueueOut(BaseModel):
    branch_id: int
    server_time: datetime      # để màn hình Bar tính số phút đã chờ đúng giờ server
    items: list[QueueItemOut]


class BarOrderItemOut(BaseModel):
    id: int
    name: str
    quantity: int
    note: str | None
    status: str


class BarOrderOut(BaseModel):
    """Đơn ở cột "Có thể lấy" (READY)."""
    id: int
    order_code: str
    table_number: str
    status: str
    is_member: bool
    total: int
    paid_at: datetime | None
    ready_at: datetime | None
    items: list[BarOrderItemOut]


class ItemActionOut(BaseModel):
    item_id: int
    item_status: str
    order_id: int
    order_status: str


class CompleteOut(BaseModel):
    order_id: int
    status: str
    completed_at: datetime
    points_earned: int | None   # None: khách ẩn danh
