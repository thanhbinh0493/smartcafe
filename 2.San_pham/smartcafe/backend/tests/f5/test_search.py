"""F5 – UC20: thu ngân tra cứu đơn theo mã / bàn để hỗ trợ khách."""
import pytest

from tests import factories as f
from tests.f2.conftest import place, place_and_pay
from tests.f3.conftest import auth, complete, make_ready
from tests.f5.conftest import cancel, move_to_yesterday, search


def codes(r) -> list[str]:
    assert r.status_code == 200, r.text
    return [o["order_code"] for o in r.json()]


def test_F5_01_khong_loc_tra_don_trong_ngay_cua_chi_nhanh(client, db, sup):
    a = place_and_pay(client, sup.t_cg, (sup.sua_da, 1))
    b = place_and_pay(client, sup.t_cg2, (sup.tra_dao, 2))
    place(client, sup.t_cg, (sup.banh, 1))                  # chưa thanh toán: không hiện
    place_and_pay(client, sup.t_hd, (sup.sua_da, 1))        # chi nhánh khác: không hiện
    # mới thanh toán trước
    assert codes(search(client, sup.tn)) == [b["order_code"], a["order_code"]]


def test_F5_02_loc_theo_ma_don_va_ban(client, db, sup):
    a = place_and_pay(client, sup.t_cg, (sup.sua_da, 1))    # CG-0001, bàn 05
    b = place_and_pay(client, sup.t_cg2, (sup.tra_dao, 1))  # CG-0002, bàn 06
    assert codes(search(client, sup.tn, code="0002")) == [b["order_code"]]
    assert codes(search(client, sup.tn, code="cg-0001")) == [a["order_code"]]  # không phân biệt hoa thường
    assert codes(search(client, sup.tn, table="06")) == [b["order_code"]]
    assert codes(search(client, sup.tn, code="0001", table="06")) == []
    assert codes(search(client, sup.tn, code="9999")) == []


def test_F5_03_gom_don_ton_hom_truoc_con_do(client, db, sup):
    stale = place_and_pay(client, sup.t_cg, (sup.sua_da, 1))
    done_old = place_and_pay(client, sup.t_cg, (sup.banh, 1))
    make_ready(client, sup.pc, done_old)
    complete(client, sup.pc, done_old["order_id"])
    move_to_yesterday(db, stale)                            # hôm qua, vẫn chờ pha → cần thấy để hủy
    move_to_yesterday(db, done_old)                         # hôm qua, đã giao → không cần hiện
    today_done = place_and_pay(client, sup.t_cg2, (sup.tra_dao, 1))
    make_ready(client, sup.pc, today_done)
    complete(client, sup.pc, today_done["order_id"])        # hôm nay, đã giao → vẫn tra cứu được
    got = codes(search(client, sup.tn))
    assert stale["order_code"] in got and today_done["order_code"] in got
    assert len(got) == 2


def test_F5_04_du_thong_tin_de_ho_tro(client, db, sup):
    cust = f.customer(db)
    o = place_and_pay(client, sup.t_cg, (sup.sua_da, 2, "ít đá"), (sup.tra_dao, 1), method="MOCK_CARD")
    from app.models import Order
    db.get(Order, o["order_id"]).customer_id = cust.id
    db.flush()
    row = search(client, sup.tn, code=o["order_code"]).json()[0]
    assert row["table_number"] == "05" and row["status"] == "PAID" and row["total"] == 29000 * 2 + 36000
    assert row["is_member"] is True and row["can_cancel"] is True and row["cancel_reason"] is None
    assert row["payment"]["method"] == "MOCK_CARD" and row["payment"]["status"] == "SUCCESS"
    assert row["payment"]["transaction_ref"].startswith("MOCK-") and row["payment"]["refunded_at"] is None
    assert [(i["name"], i["quantity"], i["note"], i["status"]) for i in row["items"]] == [
        ("Ca phe sua da", 2, "ít đá", "WAITING"), ("Tra dao", 1, None, "WAITING")]


@pytest.mark.parametrize("who, status", [("tn", 200), ("ql", 200), ("pc", 403), ("admin", 403)])
def test_F5_05_phan_quyen_tra_cuu(client, db, sup, who, status):
    r = search(client, getattr(sup, who))
    assert r.status_code == status
    if status == 403:
        assert r.json()["error"]["code"] == "FORBIDDEN"


def test_F5_06_tra_cuu_can_dang_nhap_va_chi_trong_chi_nhanh(client, db, sup):
    place_and_pay(client, sup.t_cg, (sup.sua_da, 1))
    assert client.get("/api/staff/orders/search").status_code == 401
    assert codes(search(client, sup.tn_hd)) == []           # thu ngân HD không thấy đơn CG
    r = client.get("/api/staff/orders/search", params={"code": "x" * 21}, headers=auth(sup.tn))
    assert r.status_code == 422


def test_F5_07_don_da_huy_hien_ly_do_va_nguoi_huy(client, db, sup):
    o = place_and_pay(client, sup.t_cg, (sup.sua_da, 1))
    cancel(client, sup.tn, o["order_id"], "Khách đổi ý")
    row = search(client, sup.ql, code=o["order_code"]).json()[0]
    assert row["status"] == "CANCELLED" and row["can_cancel"] is False
    assert row["cancel_reason"] == "Khách đổi ý" and row["cancelled_by"] == "TN_CG" and row["cancelled_at"]
    assert row["payment"]["status"] == "REFUNDED" and row["payment"]["refunded_at"]
