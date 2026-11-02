"""Tạo 18 bảng + 9 kiểu ENUM theo schema.sql (IV.1)

Revision ID: 0001
Revises:
Create Date: 2026-11-02
"""
from pathlib import Path

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parent.parent / "sql" / "0001_initial_schema.sql"

TABLES = [
    "association_rules", "daily_sales_reports", "recommendation_logs", "loyalty_transactions",
    "payments", "order_status_history", "order_items", "orders", "otp_requests", "customers",
    "dining_tables", "promotion_items", "promotions", "branch_menu_items", "menu_items",
    "categories", "staff", "branches",
]
ENUMS = [
    "rec_mode", "loyalty_type", "payment_status", "payment_method", "change_source",
    "item_status", "order_status", "temp_type", "staff_role",
]


def upgrade() -> None:
    # Chạy nguyên văn ở mức driver (không qua text() để tránh hiểu nhầm dấu ':' trong comment là tham số)
    op.get_bind().exec_driver_sql(SQL_FILE.read_text(encoding="utf-8"))


def downgrade() -> None:
    for t in TABLES:
        op.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
    for e in ENUMS:
        op.execute(f"DROP TYPE IF EXISTS {e}")
