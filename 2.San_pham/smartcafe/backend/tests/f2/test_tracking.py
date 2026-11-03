"""F2 – UC06: xem đơn, vị trí trong hàng đợi, WebSocket /ws/order/{id}, sự kiện cho màn hình Bar."""
import asyncio

import pytest
from starlette.websockets import WebSocketDisconnect

from app.ws.hub import Hub, hub
from tests.f2.conftest import place, place_and_pay


def view(client, o):
    r = client.get(f"/api/public/orders/{o['order_id']}", params={"token": o["access_token"]})
    assert r.status_code == 200
    return r.json()


def test_F2_22_xem_don(client, db, shop):
    o = place_and_pay(client, shop.t_cg, (shop.sua_da, 2, "ít đường"), (shop.tra_dao, 1))
    v = view(client, o)
    assert v["order_code"] == "CG-0001" and v["status"] == "PAID"
    assert v["branch_name"] == "Chi nhánh CG" and v["table_number"] == "05"
    assert (v["subtotal"], v["discount"], v["total"]) == (103000, 9000, 94000)
    assert [(i["name"], i["quantity"], i["status"]) for i in v["items"]] == [
        ("Ca phe sua da", 2, "WAITING"), ("Tra dao", 1, "WAITING"),
    ]
    assert v["paid_at"] and v["ready_at"] is None and v["cancel_reason"] is None


def test_F2_23_vi_tri_trong_hang_doi(client, db, shop):
    a = place_and_pay(client, shop.t_cg, (shop.sua_da, 1))
    b = place_and_pay(client, shop.t_cg2, (shop.sua_da, 1))
    pending = place(client, shop.t_cg, (shop.banh, 1)).json()
    other = place_and_pay(client, shop.t_hd, (shop.banh, 1))
    c = place_and_pay(client, shop.t_cg, (shop.tra_dao, 1))
    assert [view(client, x)["queue_position"] for x in (a, b, c)] == [1, 2, 3]
    assert view(client, pending)["queue_position"] is None   # chưa thanh toán: chưa vào hàng đợi
    assert view(client, other)["queue_position"] == 1          # chi nhánh khác tính riêng


def test_F2_24_websocket_sai_token_bi_tu_choi(client, db, shop):
    o = place(client, shop.t_cg, (shop.sua_da, 1)).json()
    with pytest.raises(WebSocketDisconnect) as e:
        with client.websocket_connect(f"/ws/order/{o['order_id']}?token=sai") as ws:
            ws.receive_json()
    assert e.value.code == 4404


def test_F2_25_websocket_nhan_anh_chup_va_su_kien_thanh_toan(client, db, shop):
    o = place(client, shop.t_cg, (shop.sua_da, 1)).json()
    with client.websocket_connect(f"/ws/order/{o['order_id']}?token={o['access_token']}") as ws:
        snap = ws.receive_json()
        assert snap["type"] == "ORDER_SNAPSHOT" and snap["data"]["status"] == "PENDING_PAYMENT" and snap["ts"]
        client.post(f"/api/public/orders/{o['order_id']}/pay",
                    json={"access_token": o["access_token"], "method": "MOCK_EWALLET"})
        evt = ws.receive_json()
        assert evt["type"] == "ORDER_PAID"
        assert evt["data"]["status"] == "PAID" and evt["data"]["queue_position"] == 1
    assert hub.subscriber_count(f"order:{o['order_id']}") == 0  # ngắt kết nối thì rời kênh


class FakeSocket:
    def __init__(self, fail=False):
        self.sent, self.fail = [], fail

    async def send_json(self, msg):
        if self.fail:
            raise RuntimeError("đã ngắt")
        self.sent.append(msg)


def test_F2_26_man_hinh_bar_nhan_su_kien_mon_moi(client, db, shop):
    bar = FakeSocket()
    hub.subscribe(f"bar:{shop.cg.id}", bar)
    try:
        o = place_and_pay(client, shop.t_cg, (shop.sua_da, 2, "ít đá"))
    finally:
        hub.unsubscribe(f"bar:{shop.cg.id}", bar)
    assert len(bar.sent) == 1
    msg = bar.sent[0]
    assert msg["type"] == "QUEUE_ITEM_ADDED"
    assert msg["data"]["order_code"] == o["order_code"] and msg["data"]["table_number"] == "05"
    assert msg["data"]["items"][0] | {"id": 0} == {"id": 0, "name": "Ca phe sua da", "quantity": 2, "note": "ít đá", "status": "WAITING"}


def test_F2_27_hub_bo_ket_noi_da_ngat():
    h = Hub()
    ok, dead = FakeSocket(), FakeSocket(fail=True)
    h.subscribe("c", ok)
    h.subscribe("c", dead)
    asyncio.run(h.publish("c", "PING", {"x": 1}))
    assert ok.sent[0]["type"] == "PING" and ok.sent[0]["data"] == {"x": 1} and ok.sent[0]["ts"].endswith("Z")
    assert h.subscriber_count("c") == 1
    asyncio.run(h.publish("khong-ai-nghe", "PING", {}))  # kênh trống không lỗi
