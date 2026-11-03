"""Cấu hình test: chạy trên PostgreSQL thật (CSDL riêng `smartcafe_test`).

- Đầu phiên test: xóa và tạo lại CSDL test, chạy migration Alembic tới head.
- Mỗi test chạy trong 1 transaction và rollback ở cuối, nên các test độc lập với nhau.
Biến môi trường: TEST_DATABASE_URL (mặc định: postgres trong docker compose, cổng 5432 của máy host).
"""
import os

TEST_DB_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://smartcafe:smartcafe@localhost:5432/smartcafe_test"
)
os.environ["DATABASE_URL"] = TEST_DB_URL  # phải đặt trước khi import app (engine tạo lúc import)
os.environ["SCHEDULER_ENABLED"] = "false"  # không chạy job nền trong test (F7)
os.environ["WEATHER_API_KEY"] = ""      # test không gọi Weather API thật

from collections.abc import Iterator  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.db import get_db  # noqa: E402
from app.main import app  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parent.parent


def alembic_config(url: str) -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.attributes["database_url"] = url
    return cfg


def recreate_database(url: str) -> None:
    u = make_url(url)
    admin = create_engine(u.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{u.database}" WITH (FORCE)'))
        conn.execute(text(f'CREATE DATABASE "{u.database}"'))
    admin.dispose()


@pytest.fixture(scope="session")
def engine():
    recreate_database(TEST_DB_URL)
    command.upgrade(alembic_config(TEST_DB_URL), "head")
    eng = create_engine(TEST_DB_URL)
    yield eng
    eng.dispose()


@pytest.fixture
def db(engine) -> Iterator[Session]:
    conn = engine.connect()
    trans = conn.begin()
    session = Session(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False)
    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        conn.close()


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
