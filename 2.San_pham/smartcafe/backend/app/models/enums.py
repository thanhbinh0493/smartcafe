"""Kiểu liệt kê PostgreSQL (đã tạo trong migration 0001, nên create_type=False)."""
from sqlalchemy.dialects.postgresql import ENUM

STAFF_ROLES = ("ADMIN", "MANAGER", "CASHIER", "BARISTA")
TEMP_TYPES = ("HOT", "COLD", "BOTH", "NONE")
ORDER_STATUSES = ("PENDING_PAYMENT", "PAID", "PREPARING", "READY", "COMPLETED", "CANCELLED")
ITEM_STATUSES = ("WAITING", "PREPARING", "DONE", "CANCELLED")
CHANGE_SOURCES = ("CUSTOMER", "STAFF", "SYSTEM")
PAYMENT_METHODS = ("MOCK_EWALLET", "MOCK_CARD")
PAYMENT_STATUSES = ("SUCCESS", "FAILED", "REFUNDED")
LOYALTY_TYPES = ("EARN", "ADJUST")
REC_MODES = ("ANONYMOUS", "MEMBER")

staff_role = ENUM(*STAFF_ROLES, name="staff_role", create_type=False)
temp_type = ENUM(*TEMP_TYPES, name="temp_type", create_type=False)
order_status = ENUM(*ORDER_STATUSES, name="order_status", create_type=False)
item_status = ENUM(*ITEM_STATUSES, name="item_status", create_type=False)
change_source = ENUM(*CHANGE_SOURCES, name="change_source", create_type=False)
payment_method = ENUM(*PAYMENT_METHODS, name="payment_method", create_type=False)
payment_status = ENUM(*PAYMENT_STATUSES, name="payment_status", create_type=False)
loyalty_type = ENUM(*LOYALTY_TYPES, name="loyalty_type", create_type=False)
rec_mode = ENUM(*REC_MODES, name="rec_mode", create_type=False)
