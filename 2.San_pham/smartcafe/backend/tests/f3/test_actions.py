"""F3 – UC18: Bắt đầu / Xong / Hoàn tác; chuyển trạng thái đơn PAID → PREPARING → READY; phân quyền thao tác."""
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models import Order, OrderItem, OrderStatusHistory
from tests.f2.conftest import place, place_and_pay
from tests.f3.conftest import act, auth, complete, item_ids, make_ready, queue, ready, view


def history(db, order_id):
    return db.execute(
        select(OrderStatusHistory.from_status, OrderStatusHistory.to_status, OrderStatusHistory.source,
               OrderStatusHistory.staff_id)
        .where(OrderStatusHistory.order_id == order_id).order_by(OrderStatusHistory.id)
    ).all()


def test_F3_07_bat_dau_mon_dau_tien_don_chuyen_dang_pha(client, db, bar):
    o = place_and_pay(client, bar.t_cg, (bar.sua_da, 1), (bar.banh, 1))
    first, second = item_ids(o)
    r = act(client, bar.pc, first, "start")
    assert r.status_code == 200
    assert r.json() == {"item_id": first, "item_status": "PREPARING", "order_id": o["order_id"],
                        "order_status": "PREPARING"}
    assert db.get(OrderItem, first).started_at is not None
    assert history(db, o["order_id"])[-1] == ("PAID", "PREPARING", "STAFF", bar.pc.id)
    # Món thứ 2 bắt đầu: đơn đã PREPARING, không ghi thêm lịch sử
    assert act(client, bar.pc2, second, "start").json()["order_status"] == "PREPARING"
    assert len(history(db, o["order_id"])) == 3  # PENDING_PAYMENT, PAID, PREPARING
    assert [r["status"] for r in queue(client, bar.pc, bar.cg)] == ["PREPARING", "PREPARING"]
    assert view(client, o)["status"] == "PREPARING"


def test_F3_08_bam_xong_mon_cuoi_cung_don_co_the_lay(client, db, bar):
    o = place_and_pay(client, bar.t_cg, (bar.sua_da, 1), (bar.banh, 1))
    first, second = item_ids(o)
    for iid in (first, second):
        act(client, bar.pc, iid, "start")
    r = act(client, bar.pc, first, "done")
    assert r.json()["item_status"] == "DONE" and r.json()["order_status"] == "PREPARING"
    assert db.get(OrderItem, first).done_at is not None
    r = act(client, bar.pc, second, "done")
    assert r.json()["order_status"] == "READY"
    order = db.get(Order, o["order_id"])
    assert order.ready_at is not None
    assert history(db, o["order_id"])[-1] == ("PREPARING", "READY", "STAFF", bar.pc.id)
    v = view(client, o)
    assert v["status"] == "READY" and v["queue_position"] is None and v["ready_at"]
    assert [i["status"] for i in v["items"]] == ["DONE", "DONE"]


@pytest.mark.parametrize("prepare, action, message", [
    (["start"], "start", "Món này đã được bắt đầu pha"),
    ([], "done", "Cần bấm \"Bắt đầu\" trước khi bấm \"Xong\""),
    (["start", "done"], "done", "Món đã xong rồi"),
    ([], "undo", "Không thể hoàn tác: món chưa xong hoặc đơn đã giao / đã hủy"),
    (["start"], "undo", "Không thể hoàn tác: món chưa xong hoặc đơn đã giao / đã hủy"),
])
def test_F3_09_thao_tac_sai_trang_thai_bi_tu_choi(client, db, bar, prepare, action, message):
    o = place_and_pay(client, bar.t_cg, (bar.sua_da, 1), (bar.banh, 1))
    iid = item_ids(o)[0]
    for a in prepare:
        assert act(client, bar.pc, iid, a).status_code == 200
    r = act(client, bar.pc, iid, action)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "INVALID_STATE_TRANSITION" and r.json()["error"]["message"] == message


def test_F3_10_khong_thao_tac_tren_don_chua_thanh_toan_hoac_da_huy(client, db, bar):
    pending = place(client, bar.t_cg, (bar.sua_da, 1)).json()
    r = act(client, bar.pc, item_ids(pending)[0], "start")
    assert r.status_code == 409 and r.json()["error"]["details"]["order_status"] == "PENDING_PAYMENT"
    o = place_and_pay(client, bar.t_cg, (bar.sua_da, 1))
    order = db.get(Order, o["order_id"])
    order.status = "CANCELLED"  # F5 sẽ có API hủy; ở đây giả lập đơn vừa bị thu ngân hủy
    for i in order.items:
        i.status = "CANCELLED"
    db.flush()
    for action in ("start", "done"):
        r = act(client, bar.pc, item_ids(o)[0], action)
        assert r.status_code == 409 and r.json()["error"]["details"]["order_status"] == "CANCELLED"
    assert queue(client, bar.pc, bar.cg) == []


def test_F3_11_hoan_tac_trong_10_giay(client, db, bar):
    o = place_and_pay(client, bar.t_cg, (bar.sua_da, 1), (bar.banh, 1))
    first, _ = item_ids(o)
    act(client, bar.pc, first, "start")
    act(client, bar.pc, first, "done")
    r = act(client, bar.pc, first, "undo")
    assert r.status_code == 200 and r.json()["item_status"] == "PREPARING" and r.json()["order_status"] == "PREPARING"
    assert db.get(OrderItem, first).done_at is None
    assert first in [x["id"] for x in queue(client, bar.pc, bar.cg)]  # quay lại đúng vị trí trong hàng đợi


def test_F3_12_hoan_tac_mon_cuoi_don_quay_lai_hang_doi(client, db, bar):
    """P15: món cuối bấm nhầm "Xong" làm đơn READY; Hoàn tác thì đơn READY → PREPARING."""
    o = place_and_pay(client, bar.t_cg, (bar.sua_da, 1))
    make_ready(client, bar.pc, o)
    assert len(ready(client, bar.pc, bar.cg)) == 1
    r = act(client, bar.pc, item_ids(o)[0], "undo")
    assert r.json()["order_status"] == "PREPARING"
    assert db.get(Order, o["order_id"]).ready_at is None
    assert history(db, o["order_id"])[-1] == ("READY", "PREPARING", "STAFF", bar.pc.id)
    assert ready(client, bar.pc, bar.cg) == []
    assert view(client, o)["queue_position"] == 1


def test_F3_13_qua_thoi_gian_hoan_tac(client, db, bar):
    o = place_and_pay(client, bar.t_cg, (bar.sua_da, 1), (bar.banh, 1))
    first, _ = item_ids(o)
    act(client, bar.pc, first, "start")
    act(client, bar.pc, first, "done")
    item = db.get(OrderItem, first)
    item.done_at = item.done_at - timedelta(seconds=16)  # 10 giây + 5 giây bù trễ mạng đã hết
    db.flush()
    r = act(client, bar.pc, first, "undo")
    assert r.status_code == 409 and r.json()["error"]["code"] == "UNDO_EXPIRED"
    item.done_at = item.done_at + timedelta(seconds=4)  # còn trong 15 giây
    db.flush()
    assert act(client, bar.pc, first, "undo").status_code == 200


def test_F3_14_khong_hoan_tac_sau_khi_da_giao(client, db, bar):
    o = place_and_pay(client, bar.t_cg, (bar.sua_da, 1))
    make_ready(client, bar.pc, o)
    complete(client, bar.pc, o["order_id"])
    r = act(client, bar.pc, item_ids(o)[0], "undo")
    assert r.status_code == 409 and r.json()["error"]["details"]["order_status"] == "COMPLETED"


@pytest.mark.parametrize("who, status, code", [
    ("tn", 403, "FORBIDDEN"),        # thu ngân chỉ xem (UC17)
    ("admin", 403, "FORBIDDEN"),     # quản trị viên không thao tác ở quầy
    ("pc_hd", 403, "FORBIDDEN"),     # pha chế chi nhánh khác
    ("ql", 200, None),               # quản lý chi nhánh được thao tác
])
def test_F3_15_phan_quyen_thao_tac(client, db, bar, who, status, code):
    o = place_and_pay(client, bar.t_cg, (bar.sua_da, 1))
    r = act(client, getattr(bar, who), item_ids(o)[0], "start")
    assert r.status_code == status
    if code:
        assert r.json()["error"]["code"] == code
        assert db.get(OrderItem, item_ids(o)[0]).status == "WAITING"


def test_F3_16_mon_hoac_don_khong_ton_tai(client, db, bar):
    r = client.post("/api/staff/order-items/999999/start", headers=auth(bar.pc))
    assert r.status_code == 404 and r.json()["error"]["code"] == "ITEM_NOT_FOUND"
    r = client.post("/api/staff/orders/999999/complete", headers=auth(bar.pc))
    assert r.status_code == 404 and r.json()["error"]["code"] == "ORDER_NOT_FOUND"
    assert client.post("/api/staff/order-items/1/start").status_code == 401
