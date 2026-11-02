from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.enums import rec_mode


class RecommendationLog(Base):
    __tablename__ = "recommendation_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"))
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"))
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"))
    mode: Mapped[str] = mapped_column(rec_mode)
    context: Mapped[dict] = mapped_column(JSONB)
    items: Mapped[list] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AssociationRule(Base):
    __tablename__ = "association_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    antecedent_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id"))
    consequent_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id"))
    support: Mapped[Decimal] = mapped_column(Numeric(6, 4))
    confidence: Mapped[Decimal] = mapped_column(Numeric(6, 4))
    lift: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DailySalesReport(Base):
    __tablename__ = "daily_sales_reports"

    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), primary_key=True)
    report_date: Mapped[date] = mapped_column(Date, primary_key=True)
    order_count: Mapped[int] = mapped_column(Integer)
    cancelled_count: Mapped[int] = mapped_column(Integer)
    revenue: Mapped[int] = mapped_column(BigInteger)
    avg_order_value: Mapped[int] = mapped_column(Integer)
    avg_wait_seconds: Mapped[int | None] = mapped_column(Integer)
    member_order_ratio: Mapped[Decimal] = mapped_column(Numeric(5, 4))
    promo_revenue: Mapped[int] = mapped_column(BigInteger)
    recommended_item_ratio: Mapped[Decimal] = mapped_column(Numeric(5, 4))
    top_items: Mapped[list] = mapped_column(JSONB)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
