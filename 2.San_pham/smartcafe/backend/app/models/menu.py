from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.enums import temp_type


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    base_price: Mapped[int] = mapped_column(Integer)
    image_url: Mapped[str | None] = mapped_column(String(255))
    temperature_type: Mapped[str] = mapped_column(temp_type, server_default="BOTH")
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    is_deleted: Mapped[bool] = mapped_column(Boolean, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    category: Mapped[Category] = relationship()


class BranchMenuItem(Base):
    __tablename__ = "branch_menu_items"

    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), primary_key=True)
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id"), primary_key=True)
    price_override: Mapped[int | None] = mapped_column(Integer)
    is_available: Mapped[bool] = mapped_column(Boolean, server_default="true")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Promotion(Base):
    __tablename__ = "promotions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(255))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))  # NULL = toàn chuỗi
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_by: Mapped[int] = mapped_column(ForeignKey("staff.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    items: Mapped[list["PromotionItem"]] = relationship(cascade="all, delete-orphan")


class PromotionItem(Base):
    __tablename__ = "promotion_items"

    promotion_id: Mapped[int] = mapped_column(ForeignKey("promotions.id", ondelete="CASCADE"), primary_key=True)
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id"), primary_key=True)
    promo_price: Mapped[int] = mapped_column(Integer)
