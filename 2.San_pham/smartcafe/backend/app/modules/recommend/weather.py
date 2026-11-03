"""Thời tiết cho gợi ý món (II.2 Mục 2.3 – yếu tố phụ 10%, D13, D35).

- Có WEATHER_API_KEY: gọi OpenWeatherMap theo tọa độ chi nhánh, cache 30 phút / chi nhánh.
- Không có key, chi nhánh không có tọa độ, hoặc API lỗi / chậm (> 2 giây): dùng nhiệt độ giả lập WEATHER_MOCK_TEMP_C.
Không bao giờ ném lỗi ra ngoài (NFR-R1).
"""
import json
import logging
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass

from app.core.config import get_settings

log = logging.getLogger("smartcafe.weather")
API_URL = "https://api.openweathermap.org/data/2.5/weather"
HOT_C, COLD_C = 28.0, 22.0


@dataclass(frozen=True)
class Weather:
    temp_c: float
    source: str  # "api" | "mock"

    @property
    def kind(self) -> str:
        """HOT (≥ 28°C → ưu tiên đồ lạnh), COLD (≤ 22°C → ưu tiên đồ nóng), MILD (trung tính)."""
        if self.temp_c >= HOT_C:
            return "HOT"
        if self.temp_c <= COLD_C:
            return "COLD"
        return "MILD"


_cache: dict[int, tuple[float, Weather]] = {}


def clear_cache() -> None:
    _cache.clear()


def _fetch(lat: float, lon: float, key: str) -> float:
    q = urllib.parse.urlencode({"lat": lat, "lon": lon, "units": "metric", "appid": key})
    with urllib.request.urlopen(f"{API_URL}?{q}", timeout=2) as r:  # noqa: S310 – URL cố định
        return float(json.load(r)["main"]["temp"])


def get_weather(branch_id: int, lat: float | None, lon: float | None) -> Weather:
    s = get_settings()
    mock = Weather(s.weather_mock_temp_c, "mock")
    if not s.weather_api_key or lat is None or lon is None:
        return mock
    now = time.monotonic()
    hit = _cache.get(branch_id)
    if hit and now - hit[0] < s.weather_cache_minutes * 60:
        return hit[1]
    try:
        w = Weather(round(_fetch(lat, lon, s.weather_api_key), 1), "api")
    except Exception as e:  # mạng lỗi, key sai, dữ liệu lạ
        log.warning("Weather API lỗi (%s), dùng nhiệt độ giả lập", e)
        return mock
    _cache[branch_id] = (now, w)
    return w


def weather_score(temperature_type: str, w: Weather) -> float:
    """1 nếu hợp thời tiết, 0,5 nếu BOTH / NONE hoặc trời trung tính, 0 nếu ngược."""
    if temperature_type in ("BOTH", "NONE") or w.kind == "MILD":
        return 0.5
    want = "COLD" if w.kind == "HOT" else "HOT"
    return 1.0 if temperature_type == want else 0.0
