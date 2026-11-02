"""F1 – UC03: menu theo chi nhánh (giá chung / giá chi nhánh / giá KM, món mới, tạm hết)."""
from datetime import timedelta

import pytest

from tests import factories as f


@pytest.fixture
def ctx(db):
    cg, hd = f.branch(db, "CG"), f.branch(db, "HD")
    admin = f.staff(db, "admin", "ADMIN")
    coffee = f.category(db, "Coffee", 1)
    return {"db": db, "cg": cg, "hd": hd, "admin": admin, "coffee": coffee}


def get_menu(client, branch):
    r = client.get(f"/api/public/branches/{branch.id}/menu")
    assert r.status_code == 200
    return r.json()


def items_by_name(menu) -> dict:
    return {i["name"]: i for c in menu["categories"] for i in c["items"]}


def test_F1_07_gia_chung_khi_chi_nhanh_khong_cau_hinh(client, ctx):
    f.item(ctx["db"], ctx["coffee"], "Den da", 25000)
    it = items_by_name(get_menu(client, ctx["cg"]))["Den da"]
    assert it["regular_price"] == it["sell_price"] == 25000
    assert it["is_promo"] is False and it["promotion_id"] is None
    assert it["is_available"] is True


def test_F1_08_gia_rieng_chi_ap_dung_cho_chi_nhanh_do(client, ctx):
    m = f.item(ctx["db"], ctx["coffee"], "Sua da", 29000)
    f.branch_item(ctx["db"], ctx["hd"], m, price=27000)
    assert items_by_name(get_menu(client, ctx["hd"]))["Sua da"]["sell_price"] == 27000
    assert items_by_name(get_menu(client, ctx["cg"]))["Sua da"]["sell_price"] == 29000


def test_F1_09_mon_tam_het_van_hien_nhung_danh_dau(client, ctx):
    m = f.item(ctx["db"], ctx["coffee"], "Bac xiu nong", 32000)
    f.branch_item(ctx["db"], ctx["cg"], m, available=False)
    assert items_by_name(get_menu(client, ctx["cg"]))["Bac xiu nong"]["is_available"] is False
    assert items_by_name(get_menu(client, ctx["hd"]))["Bac xiu nong"]["is_available"] is True


def test_F1_10_an_mon_ngung_ban_mon_da_xoa_va_danh_muc_tat(client, ctx):
    db = ctx["db"]
    f.item(db, ctx["coffee"], "Dang ban", 10000)
    f.item(db, ctx["coffee"], "Ngung ban", 10000, is_active=False)
    f.item(db, ctx["coffee"], "Da xoa", 10000, is_deleted=True)
    hidden_cat = f.category(db, "An", 2, is_active=False)
    f.item(db, hidden_cat, "Mon cua danh muc an", 10000)
    names = set(items_by_name(get_menu(client, ctx["cg"])))
    assert names == {"Dang ban"}


@pytest.mark.parametrize("age_days,is_new", [(0, True), (29, True), (31, False), (120, False)])
def test_F1_11_nhan_mon_moi_30_ngay(client, ctx, age_days, is_new):
    f.item(ctx["db"], ctx["coffee"], "Mon", 10000, age_days=age_days)
    assert items_by_name(get_menu(client, ctx["cg"]))["Mon"]["is_new"] is is_new


def test_F1_12_km_toan_chuoi_ap_dung_moi_chi_nhanh(client, ctx):
    m = f.item(ctx["db"], ctx["coffee"], "Tra dao", 45000)
    p = f.promo(ctx["db"], ctx["admin"], {m: 36000})
    for b in (ctx["cg"], ctx["hd"]):
        it = items_by_name(get_menu(client, b))["Tra dao"]
        assert (it["regular_price"], it["sell_price"], it["is_promo"], it["promotion_id"]) == (45000, 36000, True, p.id)


def test_F1_13_km_rieng_chi_nhanh_khong_anh_huong_chi_nhanh_khac(client, ctx):
    m = f.item(ctx["db"], ctx["coffee"], "Sua da", 29000)
    f.promo(ctx["db"], ctx["admin"], {m: 25000}, b=ctx["cg"])
    assert items_by_name(get_menu(client, ctx["cg"]))["Sua da"]["sell_price"] == 25000
    hd_item = items_by_name(get_menu(client, ctx["hd"]))["Sua da"]
    assert hd_item["sell_price"] == 29000 and hd_item["is_promo"] is False


@pytest.mark.parametrize("start,end,active", [
    (timedelta(days=-10), timedelta(days=-1), True),   # đã kết thúc
    (timedelta(days=1), timedelta(days=5), True),      # chưa bắt đầu
    (timedelta(days=-1), timedelta(days=1), False),    # đang trong thời hạn nhưng bị tắt
])
def test_F1_14_km_het_han_chua_bat_dau_hoac_bi_tat_khong_ap_dung(client, ctx, start, end, active):
    m = f.item(ctx["db"], ctx["coffee"], "Cookie", 52000)
    f.promo(ctx["db"], ctx["admin"], {m: 39000}, start=start, end=end, is_active=active)
    it = items_by_name(get_menu(client, ctx["cg"]))["Cookie"]
    assert it["sell_price"] == 52000 and it["is_promo"] is False


def test_F1_15_nhieu_km_cung_luc_lay_gia_thap_nhat(client, ctx):
    m = f.item(ctx["db"], ctx["coffee"], "Tra vai", 42000)
    f.promo(ctx["db"], ctx["admin"], {m: 38000})
    best = f.promo(ctx["db"], ctx["admin"], {m: 33600}, b=ctx["cg"])
    it = items_by_name(get_menu(client, ctx["cg"]))["Tra vai"]
    assert it["sell_price"] == 33600 and it["promotion_id"] == best.id


def test_F1_16_km_ket_hop_gia_chi_nhanh_lay_gia_thap_hon(client, ctx):
    db = ctx["db"]
    m = f.item(db, ctx["coffee"], "Bac xiu", 32000)
    f.branch_item(db, ctx["hd"], m, price=28000)
    f.promo(db, ctx["admin"], {m: 30000})
    hd_item = items_by_name(get_menu(client, ctx["hd"]))["Bac xiu"]
    assert (hd_item["regular_price"], hd_item["sell_price"], hd_item["is_promo"]) == (28000, 28000, False)
    cg_item = items_by_name(get_menu(client, ctx["cg"]))["Bac xiu"]
    assert (cg_item["regular_price"], cg_item["sell_price"], cg_item["is_promo"]) == (32000, 30000, True)


def test_F1_17_danh_muc_theo_thu_tu_mon_theo_ten(client, ctx):
    db = ctx["db"]
    cake = f.category(db, "Cake", 2)
    f.item(db, cake, "B cake", 10000)
    f.item(db, ctx["coffee"], "Z coffee", 10000)
    f.item(db, ctx["coffee"], "A coffee", 10000)
    menu = get_menu(client, ctx["cg"])
    assert [c["name"] for c in menu["categories"]] == ["Coffee", "Cake"]
    assert [i["name"] for i in menu["categories"][0]["items"]] == ["A coffee", "Z coffee"]


def test_F1_22_sap_xep_ten_mon_theo_tieng_viet(client, ctx):
    """BUG-F1-01: postgres:16-alpine (musl) so sánh theo byte nên 'Cold brew' đứng trước 'Cà phê', 'Trà vải' trước 'Trà đào'."""
    for name in ["Trà vải", "Cold brew", "Trà đào cam sả", "Cà phê muối", "Americano", "Bạc xỉu"]:
        f.item(ctx["db"], ctx["coffee"], name, 10000)
    names = [i["name"] for i in get_menu(client, ctx["cg"])["categories"][0]["items"]]
    assert names == ["Americano", "Bạc xỉu", "Cà phê muối", "Cold brew", "Trà đào cam sả", "Trà vải"]


def test_F1_18_chi_nhanh_khong_ton_tai_hoac_ngung_hoat_dong(client, db):
    closed = f.branch(db, "XX", is_active=False)
    for bid in (999999, closed.id):
        r = client.get(f"/api/public/branches/{bid}/menu")
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "BRANCH_NOT_FOUND"


def test_F1_19_menu_rong(client, ctx):
    assert get_menu(client, ctx["cg"]) == {"branch_id": ctx["cg"].id, "categories": []}
