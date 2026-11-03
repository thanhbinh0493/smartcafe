"""WebSocket Hub trong bộ nhớ (IV.3 Mục 1: chạy 1 instance nên chưa cần Redis pub/sub).

Kênh: "order:{order_id}" (trang theo dõi đơn của khách), "bar:{branch_id}" (màn hình Bar – F3),
"menu:{branch_id}" (menu khách – MENU_UPDATED khi quản trị đổi món, giá, tình trạng, KM – F6).
Message: {"type": "...", "data": {...}, "ts": "2026-11-20T08:15:00Z"} (IV.3 Mục 2.3).
"""
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket


async def reject(websocket: WebSocket, code: int) -> None:
    """Từ chối kết nối mà client vẫn nhận được mã đóng (4401 / 4403 / 4404).
    Đóng trước khi accept thì uvicorn trả HTTP 403 ở bước bắt tay, trình duyệt chỉ thấy mã 1006 và cứ thử
    kết nối lại mãi (BUG-ST-01), nên phải accept rồi mới close."""
    await websocket.accept()
    await websocket.close(code=code)


def make_message(type_: str, data: dict[str, Any]) -> dict[str, Any]:
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    return {"type": type_, "data": data, "ts": ts}


class Hub:
    def __init__(self) -> None:
        self._channels: dict[str, set[WebSocket]] = defaultdict(set)

    def subscribe(self, channel: str, ws: WebSocket) -> None:
        self._channels[channel].add(ws)

    def unsubscribe(self, channel: str, ws: WebSocket) -> None:
        self._channels[channel].discard(ws)
        if not self._channels[channel]:
            self._channels.pop(channel, None)

    def subscriber_count(self, channel: str) -> int:
        return len(self._channels.get(channel, ()))

    async def publish(self, channel: str, type_: str, data: dict[str, Any]) -> None:
        msg = make_message(type_, data)
        for ws in list(self._channels.get(channel, ())):
            try:
                await ws.send_json(msg)
            except Exception:  # client đã ngắt: bỏ khỏi kênh, client sẽ tự kết nối lại (NFR-R3)
                self.unsubscribe(channel, ws)

    async def publish_prefix(self, prefix: str, type_: str, data: dict[str, Any]) -> None:
        """Gửi tới mọi kênh bắt đầu bằng `prefix` (VD "menu:" khi đổi menu chung / KM toàn chuỗi)."""
        for channel in [c for c in self._channels if c.startswith(prefix)]:
            await self.publish(channel, type_, data)


hub = Hub()
