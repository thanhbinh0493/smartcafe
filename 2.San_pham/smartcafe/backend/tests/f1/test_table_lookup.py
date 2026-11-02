"""F1 – UC01: quét QR, xác định chi nhánh và bàn."""
from tests import factories as f


def test_F1_01_qr_hop_le_tra_chi_nhanh_va_ban(client, db):
    b = f.branch(db, "CG")
    t = f.table(db, b, "05")
    r = client.get(f"/api/public/tables/{t.qr_token}")
    assert r.status_code == 200
    assert r.json() == {
        "branch": {"id": b.id, "code": "CG", "name": "Chi nhánh CG", "address": "Địa chỉ CG"},
        "table": {"id": t.id, "table_number": "05"},
    }


def test_F1_02_qr_khong_ton_tai(client, db):
    r = client.get("/api/public/tables/khong-ton-tai-123")
    assert r.status_code == 404
    assert r.json()["error"] == {
        "code": "TABLE_NOT_FOUND", "message": "Mã QR không hợp lệ, vui lòng gọi nhân viên", "details": {},
    }


def test_F1_03_ban_bi_khoa(client, db):
    t = f.table(db, f.branch(db), is_active=False)
    r = client.get(f"/api/public/tables/{t.qr_token}")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "TABLE_NOT_FOUND"


def test_F1_04_chi_nhanh_ngung_hoat_dong(client, db):
    t = f.table(db, f.branch(db, is_active=False))
    r = client.get(f"/api/public/tables/{t.qr_token}")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "TABLE_NOT_FOUND"


def test_F1_05_khong_lo_qr_token_trong_phan_hoi(client, db):
    """NFR-S3: response không trả lại qr_token của bàn khác / của chính bàn."""
    t = f.table(db, f.branch(db))
    assert t.qr_token not in client.get(f"/api/public/tables/{t.qr_token}").text
