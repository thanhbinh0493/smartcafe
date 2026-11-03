"""Mã đơn không trùng trong cùng ngày: thêm orders.order_date, UNIQUE (order_code, order_date) (D28)

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-02
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE orders ADD COLUMN order_date DATE NOT NULL "
        "DEFAULT ((now() AT TIME ZONE 'Asia/Ho_Chi_Minh')::date)"
    )
    op.execute("ALTER TABLE orders DROP CONSTRAINT orders_order_code_key")
    op.execute("ALTER TABLE orders ADD CONSTRAINT uq_orders_code_date UNIQUE (order_code, order_date)")
    op.execute("CREATE INDEX idx_orders_branch_date ON orders(branch_id, order_date)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_orders_branch_date")
    op.execute("ALTER TABLE orders DROP CONSTRAINT uq_orders_code_date")
    op.execute("ALTER TABLE orders ADD CONSTRAINT orders_order_code_key UNIQUE (order_code)")
    op.execute("ALTER TABLE orders DROP COLUMN order_date")
