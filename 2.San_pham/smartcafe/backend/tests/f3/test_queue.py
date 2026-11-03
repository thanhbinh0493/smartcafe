"""F3 – UC17: xem hàng đợi pha chế và cột "Có thể lấy" (GET queue, GET orders?status=READY), phân quyền."""
from datetime import timedelta

import pytest

from app.models import Order
from tests.f2.conftest import place, place_and_pay
from tests.f3.conftest import act, auth, item_ids, make_ready, queue, ready


def test_F3_01_hang_doi_sap_theo_gio_goi_mon_cung_don_lien_nhau(client, db, bar):
    a = place_and_pay(client, bar.t_cg, (bar.sua_da, 2, "ít đường"), (bar.tra_dao, 1), note="Mang đi")
    b = place_and_pay(client, bar.t_cg2, (bar.banh, 1))
    # Đơn a thanh toán SAU đơn b (giờ gọi = paid_at), nên b phải đứng trước dù có id nhỏ hơn
    db.get(Order, a["order_id"]).paid_at = db.get(Order, b["order_id"]).paid_at + timedelta(seconds=30)
    db.flush()
    rows = queue(client, bar.pc, bar.cg)
    assert [(r["order_code"], r["name"]) for r in rows] == [
        ("CG-0002", "Banh croissant"), ("CG-0001", "Ca phe sua da"), ("CG-0001", "Tra dao"),
    ]
    first = rows[1]
    assert first["table_number"] == "05" and first["quantity"] == 2 and first["note"] == "ít đường"
    assert first["order_note"] == "Mang đi" and first["status"] == "WAITING" and first["paid_at"]


def test_F3_02_hang_doi_chi_gom_don_da_thanh_toan_cua_chi_nhanh(client, db, bar):
    place(client, bar.t_cg, (bar.sua_da, 1))                 # chưa thanh toán
    place_and_pay(client, bar.t_hd, (bar.sua_da, 1))         # chi nhánh khác
    o = place_and_pay(client, bar.t_cg, (bar.sua_da, 1), (bar.banh, 1))
    rows = queue(client, bar.pc, bar.cg)
    assert [r["order_id"] for r in rows] == [o["order_id"]] * 2
    body = client.get(f"/api/staff/branches/{bar.cg.id}/queue", headers=auth(bar.pc)).json()
    assert body["branch_id"] == bar.cg.id and body["server_time"]


def test_F3_03_mon_xong_roi_hang_doi_don_xong_het_sang_cot_co_the_lay(client, db, bar):
    o = place_and_pay(client, bar.t_cg, (bar.sua_da, 1), (bar.banh, 1))
    first, second = item_ids(o)
    act(client, bar.pc, first, "start")
    act(client, bar.pc, first, "done")
    assert [r["id"] for r in queue(client, bar.pc, bar.cg)] == [second]
    assert ready(client, bar.pc, bar.cg) == []
    act(client, bar.pc, second, "start")
    act(client, bar.pc, second, "done")
    assert queue(client, bar.pc, bar.cg) == []
    [r] = ready(client, bar.pc, bar.cg)
    assert r["order_code"] == "CG-0001" and r["table_number"] == "05" and r["status"] == "READY"
    assert r["ready_at"] and r["is_member"] is False and r["total"] == 59000
    assert [(i["name"], i["quantity"], i["status"]) for i in r["items"]] == [
        ("Ca phe sua da", 1, "DONE"), ("Banh croissant", 1, "DONE"),
    ]


def test_F3_04_cot_co_the_lay_sap_theo_gio_xong(client, db, bar):
    a = place_and_pay(client, bar.t_cg, (bar.sua_da, 1))
    b = place_and_pay(client, bar.t_cg2, (bar.banh, 1))
    make_ready(client, bar.pc, b)
    make_ready(client, bar.pc, a)
    db.get(Order, a["order_id"]).ready_at = db.get(Order, b["order_id"]).ready_at + timedelta(seconds=5)
    db.flush()
    assert [r["order_code"] for r in ready(client, bar.pc, bar.cg)] == ["CG-0002", "CG-0001"]


@pytest.mark.parametrize("who", ["pc", "ql", "tn", "admin"])
def test_F3_05_nhan_vien_chi_nhanh_va_admin_duoc_xem(client, db, bar, who):
    place_and_pay(client, bar.t_cg, (bar.sua_da, 1))
    assert len(queue(client, getattr(bar, who), bar.cg)) == 1
    assert ready(client, getattr(bar, who), bar.cg) == []


def test_F3_06_khong_xem_duoc_chi_nhanh_khac_va_phai_dang_nhap(client, db, bar):
    url = f"/api/staff/branches/{bar.cg.id}/queue"
    assert client.get(url).json()["error"]["code"] == "UNAUTHORIZED"
    r = client.get(url, headers=auth(bar.pc_hd))
    assert r.status_code == 403 and r.json()["error"]["code"] == "FORBIDDEN"
    r = client.get(f"/api/staff/branches/{bar.cg.id}/orders", headers=auth(bar.pc_hd))
    assert r.status_code == 403
    r = client.get(f"/api/staff/branches/{bar.cg.id}/orders", params={"status": "SAI"}, headers=auth(bar.pc))
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"
