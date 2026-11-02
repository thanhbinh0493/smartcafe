"""F0 – Script nạp dữ liệu mẫu (IV.1 Mục 7)."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.security import verify_password
from app.models import Branch, Category, DiningTable, MenuItem, Promotion, Staff
from scripts.seed_data import is_empty, seed


def count(db, model) -> int:
    return db.scalar(select(func.count()).select_from(model))


def test_F0_05_seed_dung_so_luong_theo_thiet_ke(db):
    assert is_empty(db)
    result = seed(db)
    assert result == {"branches": 3, "tables": 60, "staff": 13, "categories": 5, "menu_items": 35, "promotions": 3}
    assert count(db, Branch) == 3
    assert count(db, DiningTable) == 60
    assert count(db, Staff) == 13
    assert count(db, Category) == 5
    assert count(db, MenuItem) == 35
    assert count(db, Promotion) == 3
    assert not is_empty(db)


def test_F0_06_seed_phan_bo_vai_tro_nhan_vien(db):
    seed(db)
    roles = dict(db.execute(select(Staff.role, func.count()).group_by(Staff.role)).all())
    assert roles == {"ADMIN": 1, "MANAGER": 3, "CASHIER": 3, "BARISTA": 6}
    admin = db.scalar(select(Staff).where(Staff.role == "ADMIN"))
    assert admin.branch_id is None


def test_F0_07_seed_qr_token_ngau_nhien_du_dai_va_khong_trung(db):
    """NFR-S3: qr_token >= 128 bit, không dùng ID tăng dần."""
    seed(db)
    tokens = list(db.scalars(select(DiningTable.qr_token)))
    assert len(tokens) == len(set(tokens)) == 60
    assert all(len(t) >= 22 for t in tokens)  # token_urlsafe(16) = 128 bit = 22 ký tự
    assert not any(t.isdigit() for t in tokens)


def test_F0_08_seed_mat_khau_duoc_bam_bcrypt(db):
    """NFR-S1: không lưu mật khẩu dạng rõ."""
    seed(db)
    s = db.scalar(select(Staff).where(Staff.username == "pc1_cg"))
    pw = get_settings().seed_staff_password
    assert s.password_hash != pw
    assert s.password_hash.startswith("$2")
    assert verify_password(pw, s.password_hash)


def test_F0_09_seed_co_3_den_4_mon_moi(db):
    seed(db)
    since = datetime.now(timezone.utc) - timedelta(days=30)
    new_count = db.scalar(select(func.count()).select_from(MenuItem).where(MenuItem.created_at >= since))
    assert 3 <= new_count <= 4
