from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.enums import change_source, item_status, order_status, payment_method, payment_status


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_code: Mapped[str] = mapped_column(String(20), unique=True)
    access_token: Mapped[str] = mapped_column(String(32), unique=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"))
    table_id: Mapped[int] = mapped_column(ForeignKey("dining_tables.id"))
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"))
    status: Mapped[str] = mapped_column(order_status, server_default="PENDING_PAYMENT")
    total_amount: Mapped[int] = mapped_column(Integer)
    note: Mapped[str | None] = mapped_column(String(255))
    cancel_reason: Mapped[str | None] = mapped_column(String(255))
    cancelled_by: Mapped[int | None] = mapped_column(ForeignKey("staff.id"))
    completed_by: Mapped[int | None] = mapped_column(ForeignKey("staff.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id"))
    promotion_id: Mapped[int | None] = mapped_column(ForeignKey("promotions.id"))
    quantity: Mapped[int] = mapped_column(SmallInteger)
    original_price: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[int] = mapped_column(Integer)
    note: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(item_status, server_default="WAITING")
    is_recommended: Mapped[bool] = mapped_column(Boolean, server_default="false")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    done_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    order: Mapped[Order] = relationship(back_populates="items")


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    from_status: Mapped[str | None] = mapped_column(order_status)
    to_status: Mapped[str] = mapped_column(order_status)
    source: Mapped[str] = mapped_column(change_source)
    staff_id: Mapped[int | None] = mapped_column(ForeignKey("staff.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True)
    method: Mapped[str] = mapped_column(payment_method)
    amount: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(payment_status)
    transaction_ref: Mapped[str] = mapped_column(String(40), unique=True)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
