"""Cache trong tiến trình cho các API đọc của khách (giai đoạn VI – NFR-P2/P3, BUG-ST-06, quyết định D38).

Backend chạy 1 tiến trình (WebSocket hub nằm trong bộ nhớ), nên cache đặt ngay trong tiến trình là đủ và luôn
nhất quán: mọi thao tác quản trị làm đổi menu / giá / còn hàng / khuyến mãi / bàn đều gọi `invalidate_public()`
(cùng chỗ phát MENU_UPDATED), khách không thấy dữ liệu cũ.

Chống ghi đè dữ liệu cũ: mỗi lần xóa cache tăng `generation`; một lần tải chỉ được lưu nếu trong lúc tải không có
lần xóa nào (tránh trường hợp đọc CSDL trước khi admin commit rồi ghi vào cache sau khi cache vừa bị xóa).
"""
from __future__ import annotations

import threading
import time
from typing import Any, Callable, Hashable

_lock = threading.Lock()
_generation = 0
_store: dict[tuple[str, Hashable], tuple[float, Any]] = {}
stats = {"hit": 0, "miss": 0}


def get(name: str, key: Hashable, loader: Callable[[], tuple[Any, float]]) -> Any:
    """Lấy giá trị đã cache, hoặc gọi `loader()` → (giá trị, số giây còn hiệu lực) rồi lưu lại."""
    k = (name, key)
    now = time.monotonic()
    with _lock:
        hit = _store.get(k)
        if hit is not None and hit[0] > now:
            stats["hit"] += 1
            return hit[1]
        gen = _generation
    stats["miss"] += 1
    value, ttl = loader()
    with _lock:
        if gen == _generation and ttl > 0:
            _store[k] = (time.monotonic() + ttl, value)
    return value


def invalidate(name: str | None = None) -> None:
    """Xóa 1 loại cache (name) hoặc toàn bộ."""
    global _generation
    with _lock:
        _generation += 1
        for k in [k for k in _store if name is None or k[0] == name]:
            del _store[k]


def invalidate_public() -> None:
    """Dữ liệu khách nhìn thấy đã đổi (menu, giá, còn hàng, KM, chi nhánh, bàn)."""
    invalidate()
