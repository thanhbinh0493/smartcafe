"""F7 – Gợi ý theo 2 chế độ trên CSDL thật (UC03, SD02) + API, log, xử lý lỗi."""
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models import RecommendationLog
from app.modules.recommend import router as rec_router
from tests import factories as f
from tests.f7.conftest import NOW, member_auth, names, recs


# ---------- Ẩn danh ----------
def test_F7_10_an_danh_ban_chay_7_ngay_tai_chi_nhanh(client, cafe):
    cafe.sell(cafe.cg, (cafe.tra_gung, 5), days_ago=2)
    cafe.sell(cafe.cg, (cafe.bac_xiu, 2), days_ago=3)
    cafe.sell(cafe.cg, (cafe.croissant, 20), days_ago=8)                      # quá 7 ngày: không tính
    cafe.sell(cafe.hd, (cafe.tra_dao, 15), days_ago=1)                        # chi nhánh khác
    cafe.sell(cafe.cg, (cafe.sua_nong, 15), days_ago=1, status="CANCELLED")   # đơn hủy
    r = recs(client, cafe.cg)
    assert r["mode"] == "ANONYMOUS" and r["member_fallback"] is False
    assert r["items"][0] == {**r["items"][0], "name": "Trà gừng", "reason": "Bán chạy tại chi nhánh", "score": 0.45}  # đồ nóng ngày nóng: thời tiết 0
    assert names(r["items"])[1] == "Bạc xỉu"
    assert len(r["items"]) == 5
    hd = recs(client, cafe.hd)
    assert names(hd["items"])[0] == "Trà đào cam sả"


def test_F7_11_khuyen_mai_mon_moi_het_hang_va_mon_trong_gio(client, db, cafe):
    f.promo(db, cafe.admin, {cafe.tra_dao: 36000})                            # giảm 20%
    new = cafe.item(db_cat(db, cafe), "Trà mới", 40000, "BOTH", ["tea"], age_days=3)
    f.branch_item(db, cafe.cg, cafe.bac_xiu, available=False)
    r = recs(client, cafe.cg, cart=[cafe.sua_da])
    by = {i["name"]: i for i in r["items"]}
    assert by["Trà đào cam sả"]["reason"] == "Đang giảm 20%" and by["Trà đào cam sả"]["sell_price"] == 36000
    assert by["Trà mới"]["reason"] == "Món mới" and by["Trà mới"]["is_new"] is True
    assert "Bạc xỉu" not in by and "Cà phê sữa đá" not in by                   # tạm hết / đã trong giỏ
    # Món mới 0,20 + 0,05 (BOTH) > KM 20% 0,10 + 0,10 (đồ lạnh, trời nóng)
    assert names(r["items"])[:2] == ["Trà mới", "Trà đào cam sả"]
    assert new.id in [i["menu_item_id"] for i in r["items"]]


def db_cat(db, cafe):
    from app.models import Category
    return db.scalar(select(Category).where(Category.name == "Trà"))


@pytest.mark.parametrize("temp, first, reason", [(33, "Cà phê sữa đá", "Hợp trời nóng"), (18, "Cà phê sữa nóng", "Hợp trời lạnh")])
def test_F7_12_thoi_tiet_la_yeu_to_phu(client, cafe, _mock_weather, temp, first, reason):
    _mock_weather.weather_mock_temp_c = temp
    r = recs(client, cafe.cg)
    assert r["temp_c"] == temp and r["weather_source"] == "mock"
    # Chưa có đơn nào: chỉ thời tiết phân biệt → món hợp trời đứng đầu
    assert r["items"][0]["name"] == first and r["items"][0]["reason"] == reason
    # Có món bán chạy thì bán chạy (45%) thắng thời tiết (10%)
    cafe.sell(cafe.cg, (cafe.croissant, 1), days_ago=1)
    assert recs(client, cafe.cg)["items"][0]["name"] == "Bánh croissant"


# ---------- Thành viên ----------
def test_F7_13_thanh_vien_theo_so_thich_va_mon_tuong_tu(client, cafe):
    for d in (1, 3, 5, 9):
        cafe.sell(cafe.hd, (cafe.sua_da, 1), (cafe.croissant, 1), days_ago=d, customer=cafe.member)  # chi nhánh khác
    cafe.sell(cafe.cg, (cafe.tra_gung, 2), days_ago=2, customer=cafe.member)
    cafe.sell(cafe.cg, (cafe.tra_dao, 9), days_ago=1)                          # bán chạy nhất CG
    r = recs(client, cafe.cg, headers=member_auth(cafe.member))
    assert r["mode"] == "MEMBER"
    reasons = {i["name"]: i["reason"] for i in r["items"]}
    assert [n for n, x in reasons.items() if x == "Bạn hay gọi"] == ["Cà phê sữa đá", "Bánh croissant"]  # tối đa 2
    assert reasons["Bạc xỉu"] == "Giống món bạn thích" and reasons["Cà phê sữa nóng"] == "Giống món bạn thích"
    assert "Trà gừng" not in reasons or reasons["Trà gừng"] != "Bạn hay gọi"   # món ruột thứ 3 nhường chỗ (đa dạng)
    assert names(recs(client, cafe.cg)["items"])[0] == "Trà đào cam sả"        # khách ẩn danh khác hẳn


def test_F7_14_don_gan_day_nang_hon_don_cu(client, cafe):
    cafe.sell(cafe.cg, (cafe.tra_gung, 3), days_ago=90, customer=cafe.member)   # 3 × 0,5^3 = 0,375
    cafe.sell(cafe.cg, (cafe.bac_xiu, 1), days_ago=1, customer=cafe.member)     # ≈ 0,98
    items = recs(client, cafe.cg, headers=member_auth(cafe.member))["items"]
    assert names(items)[0] == "Bạc xỉu" and items[0]["reason"] == "Bạn hay gọi"


def test_F7_15_thanh_vien_chua_co_don_dung_cong_thuc_an_danh(client, db, cafe):
    cafe.sell(cafe.cg, (cafe.tra_dao, 4), days_ago=1)
    cafe.sell(cafe.cg, (cafe.sua_da, 1), days_ago=1, customer=cafe.member, status="CANCELLED")  # đơn hủy không tính
    r = recs(client, cafe.cg, headers=member_auth(cafe.member))
    assert r["mode"] == "ANONYMOUS" and r["member_fallback"] is True
    assert names(r["items"]) == names(recs(client, cafe.cg)["items"])
    log = db.scalars(select(RecommendationLog).order_by(RecommendationLog.id.desc())).first()
    assert log.customer_id is None   # lần gọi sau là ẩn danh
    first = db.scalars(select(RecommendationLog).order_by(RecommendationLog.id)).first()
    assert first.customer_id == cafe.member.id and first.mode == "ANONYMOUS" and first.context["member_fallback"] is True


def test_F7_16_token_sai_hoac_het_han_van_goi_y_an_danh(client, cafe):
    r = client.get(f"/api/public/branches/{cafe.cg.id}/recommendations", headers={"Authorization": "Bearer sai"})
    assert r.status_code == 200 and r.json()["mode"] == "ANONYMOUS"
    from tests.f3.conftest import auth
    staff = f.staff(cafe.db, "pc", "BARISTA", cafe.cg)
    assert client.get(f"/api/public/branches/{cafe.cg.id}/recommendations", headers=auth(staff)).json()["mode"] == "ANONYMOUS"


# ---------- API, log, lỗi ----------
def test_F7_17_ghi_recommendation_logs(client, db, cafe):
    r = recs(client, cafe.cg, cart=[cafe.sua_da, cafe.sua_da], headers=member_auth(cafe.member))
    log = db.get(RecommendationLog, r["log_id"])
    assert log.branch_id == cafe.cg.id and log.customer_id == cafe.member.id and log.order_id is None
    assert log.context == {**log.context, "temp_c": 31.0, "weather": "HOT", "weather_source": "mock",
                           "cart": [cafe.sua_da.id]}
    assert 0 <= log.context["hour"] <= 23
    assert [i["menu_item_id"] for i in log.items][:5] == [i["menu_item_id"] for i in r["items"]]
    assert set(log.items[0]) == {"menu_item_id", "score", "reason"}


@pytest.mark.parametrize("params, status", [({"cart": "1,a"}, 422), ({"cart": ",".join(map(str, range(1, 32)))}, 422),
                                            ({"cart": "x" * 301}, 422)])
def test_F7_18_tham_so_cart_khong_hop_le(client, cafe, params, status):
    r = client.get(f"/api/public/branches/{cafe.cg.id}/recommendations", params=params)
    assert r.status_code == status and r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_F7_19_chi_nhanh_khong_ton_tai_hoac_ngung(client, db, cafe):
    assert client.get("/api/public/branches/99999/recommendations").status_code == 404
    cafe.hd.is_active = False
    db.flush()
    r = client.get(f"/api/public/branches/{cafe.hd.id}/recommendations")
    assert r.status_code == 404 and r.json()["error"]["code"] == "BRANCH_NOT_FOUND"


def test_F7_20_service_loi_van_tra_200_rong_menu_van_chay(client, cafe, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("model hỏng")
    monkeypatch.setattr(rec_router.service, "recommend", boom)
    r = client.get(f"/api/public/branches/{cafe.cg.id}/recommendations")
    assert r.status_code == 200
    assert r.json() == {**r.json(), "degraded": True, "items": [], "also_bought": [], "log_id": None}
    assert client.get(f"/api/public/branches/{cafe.cg.id}/menu").status_code == 200   # NFR-R1


def test_F7_21_api_goi_y_nhanh(client, cafe):
    """NFR-P3 (tham khảo, 1 người dùng): p95 ≤ 500 ms."""
    import time
    for d in range(1, 30):
        cafe.sell(cafe.cg, (cafe.sua_da, 1), (cafe.croissant, 1), days_ago=d % 7 + 0.5, customer=cafe.member)
    times = []
    for _ in range(20):
        t = time.perf_counter()
        recs(client, cafe.cg, cart=[cafe.sua_da], headers=member_auth(cafe.member))
        times.append((time.perf_counter() - t) * 1000)
    assert sorted(times)[18] < 500, times


def test_F7_22_cac_don_tuong_lai_khong_lam_lech_khi_danh_gia_lai_qua_khu(db, cafe):
    """Khi đánh giá offline (now = thời điểm quá khứ) chỉ dùng đơn trước thời điểm đó."""
    from app.modules.recommend.service import recommend
    from app.modules.recommend.weather import Weather
    cafe.sell(cafe.cg, (cafe.tra_gung, 5), days_ago=1, customer=cafe.member)
    res = recommend(db, cafe.cg, cafe.member.id, now=NOW - timedelta(days=2), weather=Weather(25, "mock"))
    assert res.mode == "ANONYMOUS" and res.member_fallback
