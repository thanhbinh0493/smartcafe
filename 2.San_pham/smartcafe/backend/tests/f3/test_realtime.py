"""F3 – WebSocket /ws/bar/{branch_id} (màn hình Bar) và sự kiện gửi tới trang theo dõi đơn của khách (SD04)."""
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from starlette.websockets import WebSocketDisconnect

from app.core.config import get_settings
from app.core.security import create_staff_token
from app.ws.hub import hub
from tests import factories as f
from tests.f2.conftest import place_and_pay
from tests.f3.conftest import act, complete, item_ids, make_ready, token


def customer_token() -> str:
    s = get_settings()
    exp = datetime.now(timezone.utc) + timedelta(hours=1)
    return jwt.encode({"sub": "1", "typ": "customer", "exp": exp}, s.jwt_secret, algorithm=s.jwt_algorithm)


def bar_ws(client, branch, tok):
    return client.websocket_connect(f"/ws/bar/{branch.id}?token={tok}")


def order_ws(client, o):
    return client.websocket_connect(f"/ws/order/{o['order_id']}?token={o['access_token']}")


@pytest.mark.parametrize("make_token, code", [
    (lambda b: "khong-hop-le", 4401),
    (lambda b: create_staff_token(999999, "BARISTA", b.cg.id), 4401),   # nhân viên không tồn tại
    (lambda b: token(b.pc_hd), 4403),                                   # pha chế chi nhánh khác
    (lambda b: customer_token(), 4401),                                 # token khách thành viên
])
def test_F3_22_websocket_bar_tu_choi_token_sai_hoac_khac_chi_nhanh(client, db, bar, make_token, code):
    with pytest.raises(WebSocketDisconnect) as e:
        with bar_ws(client, bar.cg, make_token(bar)) as ws:
            ws.receive_json()
    assert e.value.code == code


def test_F3_23_websocket_bar_tu_choi_tai_khoan_bi_khoa(client, db, bar):
    locked = f.staff(db, "pc_khoa", "BARISTA", bar.cg, is_active=False)
    with pytest.raises(WebSocketDisconnect) as e:
        with bar_ws(client, bar.cg, token(locked)) as ws:
            ws.receive_json()
    assert e.value.code == 4401


def test_F3_24_man_hinh_bar_nhan_su_kien_realtime(client, db, bar):
    with bar_ws(client, bar.cg, token(bar.pc)) as ws:
        o = place_and_pay(client, bar.t_cg, (bar.sua_da, 1, "ít đá"))
        evt = ws.receive_json()
        assert evt["type"] == "QUEUE_ITEM_ADDED"
        assert evt["data"]["order_code"] == "CG-0001" and evt["data"]["table_number"] == "05"
        assert evt["data"]["items"][0]["note"] == "ít đá"
        iid = item_ids(o)[0]

        act(client, bar.pc, iid, "start")
        evt = ws.receive_json()
        assert evt["type"] == "ITEM_UPDATED" and evt["data"]["item_status"] == "PREPARING"

        act(client, bar.pc, iid, "done")
        assert ws.receive_json()["type"] == "ITEM_UPDATED"
        evt = ws.receive_json()
        assert evt["type"] == "ORDER_READY" and evt["data"]["status"] == "READY" and evt["data"]["id"] == o["order_id"]

        complete(client, bar.pc, o["order_id"])
        evt = ws.receive_json()
        assert evt == {**evt, "type": "ORDER_COMPLETED", "data": {"order_id": o["order_id"]}}
    assert hub.subscriber_count(f"bar:{bar.cg.id}") == 0


def test_F3_25_thu_ngan_va_quan_ly_ket_noi_duoc_man_hinh_bar(client, db, bar):
    for staff in (bar.tn, bar.ql, bar.admin):
        with bar_ws(client, bar.cg, token(staff)):
            assert hub.subscriber_count(f"bar:{bar.cg.id}") == 1


def test_F3_26_khach_nhan_trang_thai_tung_buoc(client, db, bar):
    o = place_and_pay(client, bar.t_cg, (bar.sua_da, 1), (bar.banh, 1))
    first, second = item_ids(o)
    with order_ws(client, o) as ws:
        assert ws.receive_json()["type"] == "ORDER_SNAPSHOT"
        act(client, bar.pc, first, "start")
        evt = ws.receive_json()
        assert evt["type"] == "ITEM_PREPARING" and evt["data"]["status"] == "PREPARING"
        assert evt["data"]["item_id"] == first and evt["data"]["items"][0]["status"] == "PREPARING"

        act(client, bar.pc, first, "done")
        evt = ws.receive_json()
        assert evt["type"] == "ITEM_DONE" and evt["data"]["items"][0]["status"] == "DONE"

        act(client, bar.pc, second, "start")
        ws.receive_json()
        act(client, bar.pc, second, "done")
        evt = ws.receive_json()
        assert evt["type"] == "ORDER_READY" and evt["data"]["status"] == "READY"
        assert evt["data"]["queue_position"] is None

        complete(client, bar.pc, o["order_id"])
        evt = ws.receive_json()
        assert evt["type"] == "ORDER_COMPLETED" and evt["data"]["status"] == "COMPLETED"


def test_F3_27_cac_don_phia_sau_nhan_vi_tri_hang_doi_moi(client, db, bar):
    a = place_and_pay(client, bar.t_cg, (bar.sua_da, 1))
    b = place_and_pay(client, bar.t_cg2, (bar.banh, 1))
    c = place_and_pay(client, bar.t_cg, (bar.tra_dao, 1))
    with order_ws(client, b) as wb, order_ws(client, c) as wc:
        assert wb.receive_json()["data"]["queue_position"] == 2
        assert wc.receive_json()["data"]["queue_position"] == 3
        make_ready(client, bar.pc, a)  # đơn a xong: các đơn phía sau tiến lên 1 bậc
        evt_b, evt_c = wb.receive_json(), wc.receive_json()
        assert evt_b["type"] == "QUEUE_POSITION" and evt_b["data"] == {"order_id": b["order_id"], "queue_position": 1}
        assert evt_c["type"] == "QUEUE_POSITION" and evt_c["data"] == {"order_id": c["order_id"], "queue_position": 2}
