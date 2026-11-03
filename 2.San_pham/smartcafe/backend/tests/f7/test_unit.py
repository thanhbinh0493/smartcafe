"""F7 – Hàm thuần: thành phần điểm, thời tiết, xếp hạng (II.2 Mục 2.3)."""
from dataclasses import replace

import pytest

from app.modules.menu.service import PricedItem
from app.modules.recommend import weather as wmod
from app.modules.recommend.service import WEIGHTS, jaccard, normalize, promo_score, rank
from app.modules.recommend.weather import Weather, get_weather, weather_score

HOT, COLD, MILD = Weather(31, "mock"), Weather(18, "mock"), Weather(25, "mock")


def item(i: int, **kw) -> PricedItem:
    base = dict(id=i, name=f"Món {i}", description=None, image_url=None, temperature_type="BOTH", tags=[],
                category_id=1, category_name="C", regular_price=40000, sell_price=40000, promotion_id=None,
                is_available=True, is_new=False)
    return PricedItem(**{**base, **kw})


@pytest.mark.parametrize("regular, sell, expected", [
    (45000, 36000, 0.4), (40000, 20000, 1.0), (40000, 10000, 1.0), (40000, 40000, 0.0), (40000, 45000, 0.0), (0, 0, 0.0),
])
def test_F7_01_promo_score_bang_muc_giam_chia_50_phan_tram(regular, sell, expected):
    assert promo_score(regular, sell) == pytest.approx(expected)


def test_F7_02_jaccard_va_chuan_hoa():
    assert jaccard({"a", "b"}, {"b", "c"}) == pytest.approx(1 / 3)
    assert jaccard({"a"}, {"a"}) == 1 and jaccard(set(), {"a"}) == 0
    assert normalize({1: 2, 2: 8, 3: 0}) == {1: 0.25, 2: 1.0, 3: 0.0}
    assert normalize({}) == {} and normalize({1: 0}) == {}


@pytest.mark.parametrize("temp, kind", [(35, "HOT"), (28, "HOT"), (27.9, "MILD"), (22.1, "MILD"), (22, "COLD"), (15, "COLD")])
def test_F7_03_nguong_nhiet_do(temp, kind):
    assert Weather(temp, "mock").kind == kind


@pytest.mark.parametrize("w, temp_type, expected", [
    (HOT, "COLD", 1), (HOT, "HOT", 0), (HOT, "BOTH", 0.5), (HOT, "NONE", 0.5),
    (COLD, "HOT", 1), (COLD, "COLD", 0), (MILD, "COLD", 0.5), (MILD, "HOT", 0.5),
])
def test_F7_04_diem_thoi_tiet(w, temp_type, expected):
    assert weather_score(temp_type, w) == expected


def test_F7_05_thoi_tiet_gia_lap_va_api_co_cache(monkeypatch, _mock_weather):
    s = _mock_weather
    assert get_weather(1, 21.0, 105.0) == Weather(31.0, "mock")               # không có key
    s.weather_api_key = "k"
    calls = []
    monkeypatch.setattr(wmod, "_fetch", lambda lat, lon, key: calls.append((lat, lon, key)) or 19.46)
    clock = [1000.0]
    monkeypatch.setattr(wmod.time, "monotonic", lambda: clock[0])
    assert get_weather(1, 21.0, 105.0) == Weather(19.5, "api")
    clock[0] += 29 * 60
    assert get_weather(1, 21.0, 105.0).source == "api" and len(calls) == 1      # cache 30 phút
    clock[0] += 2 * 60
    get_weather(1, 21.0, 105.0)
    assert len(calls) == 2                                                      # hết cache thì gọi lại
    assert get_weather(2, None, None) == Weather(31.0, "mock")                 # chi nhánh chưa có tọa độ

    def boom(*_):
        raise TimeoutError("chậm")
    monkeypatch.setattr(wmod, "_fetch", boom)
    assert get_weather(3, 21.0, 105.0) == Weather(31.0, "mock")                # API lỗi: giả lập (NFR-R1)


def test_F7_06_ly_do_la_thanh_phan_dong_gop_nhieu_nhat():
    items = [item(1), item(2, sell_price=30000), item(3, is_new=True), item(4, temperature_type="COLD")]
    comps = {1: {"popular": 1.0, "weather": 0.5}, 2: {"promo": 0.5, "weather": 0.5}, 3: {"new": 1.0, "weather": 0.5},
             4: {"weather": 1.0}}
    out = rank(items, comps, "ANONYMOUS", HOT)
    assert [(r.item.id, r.reason) for r in out] == [
        (1, "Bán chạy tại chi nhánh"), (3, "Món mới"), (2, "Đang giảm 25%"), (4, "Hợp trời nóng")]
    assert out[0].score == pytest.approx(0.45 + 0.05)
    assert sum(WEIGHTS["ANONYMOUS"].values()) == pytest.approx(1) and sum(WEIGHTS["MEMBER"].values()) == pytest.approx(1)


def test_F7_07_top_5_toi_da_2_mon_ban_hay_goi():
    items = [item(i) for i in range(1, 9)]
    comps = {i: {"personal": 1.0 - i * 0.05} for i in range(1, 6)} | {i: {"popular": 0.5} for i in (6, 7, 8)}
    out = rank(items, comps, "MEMBER", MILD)
    assert len(out) == 5
    assert [r.item.id for r in out if r.reason_code == "PERSONAL"] == [1, 2]
    assert [r.item.id for r in out][2:] == [6, 7, 8]


def test_F7_08_mon_da_goi_khong_gan_nhan_giong_mon_ban_thich():
    items = [item(1), item(2)]
    comps = {1: {"personal": 0.2, "similar": 1.0}, 2: {"similar": 1.0}}
    out = {r.item.id: r.reason for r in rank(items, comps, "MEMBER", MILD)}
    assert out == {1: "Bạn hay gọi", 2: "Giống món bạn thích"}


def test_F7_09_bang_diem_thi_xep_theo_ban_chay_roi_ma_mon():
    items = [replace(item(3)), item(1), item(2)]
    comps = {1: {"promo": 0.4}, 2: {"promo": 0.4}, 3: {"promo": 0.4}}
    assert [r.item.id for r in rank(items, comps, "ANONYMOUS", MILD)] == [1, 2, 3]
