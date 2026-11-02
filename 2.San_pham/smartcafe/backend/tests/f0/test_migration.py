"""F0 – Migration Alembic chạy đúng schema.sql trên PostgreSQL 16 thật (CSDL riêng để test cả downgrade)."""
import pytest
from alembic import command
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

from tests.conftest import TEST_DB_URL, alembic_config, recreate_database

MIG_URL = make_url(TEST_DB_URL).set(database="smartcafe_test_mig").render_as_string(hide_password=False)

EXPECTED_TABLES = {
    "branches", "staff", "categories", "menu_items", "branch_menu_items", "promotions", "promotion_items",
    "dining_tables", "customers", "otp_requests", "orders", "order_items", "order_status_history",
    "payments", "loyalty_transactions", "recommendation_logs", "daily_sales_reports", "association_rules",
}
EXPECTED_ENUMS = {
    "staff_role", "temp_type", "order_status", "item_status", "change_source",
    "payment_method", "payment_status", "loyalty_type", "rec_mode",
}


@pytest.fixture(scope="module")
def mig_engine():
    recreate_database(MIG_URL)
    eng = create_engine(MIG_URL)
    yield eng
    eng.dispose()


def _enums(eng) -> set[str]:
    with eng.connect() as c:
        return set(c.execute(text("SELECT typname FROM pg_type WHERE typtype = 'e'")).scalars())


def _tables(eng) -> set[str]:
    return set(inspect(eng).get_table_names()) - {"alembic_version"}


def test_F0_01_upgrade_tao_du_18_bang_va_9_enum(mig_engine):
    command.upgrade(alembic_config(MIG_URL), "head")
    assert _tables(mig_engine) == EXPECTED_TABLES
    assert _enums(mig_engine) == EXPECTED_ENUMS


def test_F0_02_downgrade_xoa_sach_roi_upgrade_lai_duoc(mig_engine):
    cfg = alembic_config(MIG_URL)
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")
    assert _tables(mig_engine) == set()
    assert _enums(mig_engine) == set()
    command.upgrade(cfg, "head")
    assert _tables(mig_engine) == EXPECTED_TABLES


def test_F0_03_rang_buoc_admin_khong_thuoc_chi_nhanh(mig_engine):
    """chk_staff_branch: ADMIN phải có branch_id NULL, vai trò khác bắt buộc có chi nhánh."""
    command.upgrade(alembic_config(MIG_URL), "head")
    with mig_engine.connect() as c:
        tx = c.begin()
        with pytest.raises(IntegrityError):
            c.execute(text(
                "INSERT INTO staff (full_name, username, password_hash, role, branch_id) "
                "VALUES ('x', 'barista_no_branch', 'h', 'BARISTA', NULL)"
            ))
        tx.rollback()


def test_F0_04_rang_buoc_gia_khong_am(mig_engine):
    command.upgrade(alembic_config(MIG_URL), "head")
    with mig_engine.connect() as c:
        tx = c.begin()
        cat_id = c.execute(text("INSERT INTO categories (name) VALUES ('T') RETURNING id")).scalar_one()
        with pytest.raises(IntegrityError):
            c.execute(text(
                "INSERT INTO menu_items (category_id, name, base_price) VALUES (:c, 'Am', -1)"
            ), {"c": cat_id})
        tx.rollback()
