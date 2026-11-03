"""Giai đoạn VI – hồi quy BUG-ST-01: WebSocket từ chối kết nối phải accept rồi mới close,
để trình duyệt nhận được mã 4401 / 4403 / 4404 (đóng trước accept thì uvicorn trả HTTP 403, client chỉ thấy 1006).

TestClient: nếu server close trước accept thì `websocket_connect(...).__enter__` ném WebSocketDisconnect ngay;
nếu accept rồi close thì vào được khối `with` và message đầu tiên nhận được là websocket.close kèm mã."""
import pytest

from tests.f2.conftest import place
from tests.f3.conftest import bar, token  # noqa: F401  (fixture bar)


def first_message_after_accept(client, url: str) -> dict:
    with client.websocket_connect(url) as ws:            # ném lỗi nếu server không accept (lỗi cũ)
        return ws.receive()


@pytest.mark.parametrize("make_url, code", [
    (lambda b, o: f"/ws/bar/{b.cg.id}?token=khong-hop-le", 4401),
    (lambda b, o: f"/ws/bar/{b.cg.id}", 4401),                                   # thiếu token
    (lambda b, o: f"/ws/bar/{b.hd.id}?token={token(b.pc)}", 4403),            # pha chế chi nhánh khác
    (lambda b, o: f"/ws/order/{o['order_id']}?token=sai", 4404),
    (lambda b, o: "/ws/menu/999999", 4404),
], ids=["bar-token-sai", "bar-thieu-token", "bar-khac-chi-nhanh", "don-sai-token", "menu-chi-nhanh-khong-co"])
def test_ST_55_websocket_tu_choi_van_gui_ma_dong(client, db, bar, make_url, code):
    o = place(client, bar.t_cg, (bar.sua_da, 1)).json()
    msg = first_message_after_accept(client, make_url(bar, o))
    assert msg["type"] == "websocket.close"
    assert msg["code"] == code
