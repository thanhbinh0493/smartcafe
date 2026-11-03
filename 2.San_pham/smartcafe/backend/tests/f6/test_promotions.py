"""F6 – UC15 Quản lý chương trình khuyến mãi (W07, SD05)."""
from datetime import datetime, timedelta, timezone

import pytest

from tests import factories as f
from tests.f2.conftest import place
from tests.f6.conftest import call, public_menu


def iso(delta: timedelta) -> str:
    return (datetime.now(timezone.utc) + delta).isoformat()


def promo_body(org, *items, branch=None, start=timedelta(hours=-1), end=timedelta(days=7), **kw) -> dict:
    items = items or ((org.tra_dao, 36000),)
    return {"name": "Tuần lễ trà đào", "description": "Giảm 20%", "branch_id": branch.id if branch else None,
            "start_at": iso(start), "end_at": iso(end), "is_active": True,
            "items": [{"menu_item_id": m.id, "promo_price": p} for m, p in items], **kw}


def create(client, org, body):
    return call(client, org.admin, "POST", "/api/staff/promotions", json=body)


def test_F6_39_tao_km_mot_chi_nhanh_co_hieu_luc_ngay_tren_menu(client, org):
    r = create(client, org, promo_body(org, branch=org.cg))
    assert r.status_code == 201, r.text
    p = r.json()
    assert p == {**p, "status": "running", "branch_name": "Chi nhánh CG", "created_by": "ADMIN", "is_active": True}
    assert p["items"] == [{"menu_item_id": org.tra_dao.id, "name": "Trà đào cam sả", "current_price": 45000,
                           "promo_price": 36000, "discount_percent": 20}]
    item = public_menu(client, org.cg)["Trà đào cam sả"]
    assert item["sell_price"] == 36000 and item["is_promo"] and item["promotion_id"] == p["id"]
    assert public_menu(client, org.hd)["Trà đào cam sả"]["is_promo"] is False            # chỉ CN Cầu Giấy
    # Đơn đặt món chốt giá KM, tính vào giảm giá
    o = place(client, org.t_cg, (org.tra_dao, 2)).json()
    assert o["discount"] == 18000 and o["total"] == 72000


def test_F6_40_km_toan_chuoi_ap_dung_moi_chi_nhanh(client, org):
    p = create(client, org, promo_body(org, (org.sua_da, 25000))).json()
    assert p["branch_id"] is None and p["branch_name"] is None
    for b in (org.cg, org.hd):
        assert public_menu(client, b)["Cà phê sữa đá"]["sell_price"] == 25000


def test_F6_41_km_sap_chay_chua_ap_dung(client, org):
    p = create(client, org, promo_body(org, start=timedelta(days=1), end=timedelta(days=3))).json()
    assert p["status"] == "upcoming"
    assert public_menu(client, org.cg)["Trà đào cam sả"]["is_promo"] is False


@pytest.mark.parametrize("kw, field", [
    ({"start": timedelta(days=2), "end": timedelta(days=1)}, "end_at"),           # kết thúc trước bắt đầu
    ({"start": timedelta(days=1), "end": timedelta(days=1)}, "end_at"),           # bằng nhau
    ({"start": timedelta(days=-3), "end": timedelta(days=-1)}, "end_at"),         # đã qua
])
def test_F6_42_thoi_gian_khong_hop_le(client, org, kw, field):
    r = create(client, org, promo_body(org, **kw))
    assert r.status_code == 422 and r.json()["error"]["code"] == "PROMOTION_INVALID"
    assert r.json()["error"]["details"]["errors"][0]["field"] == field


def test_F6_43_gia_km_phai_nho_hon_gia_ban_hien_tai(client, db, org):
    r = create(client, org, promo_body(org, (org.tra_dao, 45000), (org.sua_da, 20000)))
    err = r.json()["error"]
    assert r.status_code == 422 and err["code"] == "PROMOTION_INVALID"
    assert err["details"]["errors"] == [{"menu_item_id": org.tra_dao.id, "current_price": 45000,
                                         "message": "Giá KM của 'Trà đào cam sả' phải nhỏ hơn giá bán hiện tại 45.000đ"}]
    # KM 1 chi nhánh so với giá riêng của chi nhánh đó
    f.branch_item(db, org.cg, org.tra_dao, price=39000)
    assert create(client, org, promo_body(org, (org.tra_dao, 40000), branch=org.cg)).status_code == 422
    assert create(client, org, promo_body(org, (org.tra_dao, 40000), branch=org.hd)).status_code == 201
    # KM toàn chuỗi so với giá chung
    assert create(client, org, promo_body(org, (org.tra_dao, 40000))).status_code == 201


def test_F6_44_km_toan_chuoi_khong_gan_nhan_khi_chi_nhanh_re_hon(client, db, org):
    """D27: chi nhánh đặt giá riêng 35.000 < giá KM toàn chuỗi 40.000 → bán giá chi nhánh, không nhãn KM."""
    f.branch_item(db, org.cg, org.tra_dao, price=35000)
    create(client, org, promo_body(org, (org.tra_dao, 40000)))
    cg, hd = public_menu(client, org.cg)["Trà đào cam sả"], public_menu(client, org.hd)["Trà đào cam sả"]
    assert (cg["sell_price"], cg["is_promo"]) == (35000, False)
    assert (hd["sell_price"], hd["is_promo"]) == (40000, True)


@pytest.mark.parametrize("patch", [
    {"name": ""}, {"items": []}, {"items": [{"menu_item_id": 1, "promo_price": -1}]},
    {"start_at": "2026-11-20 08:00"},                                     # thiếu múi giờ
    {"description": "x" * 256},
], ids=["ten_rong", "khong_mon", "gia_am", "thieu_mui_gio", "mo_ta_dai"])
def test_F6_45_du_lieu_khong_hop_le(client, org, patch):
    r = create(client, org, {**promo_body(org), **patch})
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_F6_46_mon_trung_hoac_khong_ton_tai(client, org):
    r = create(client, org, promo_body(org, (org.tra_dao, 30000), (org.tra_dao, 31000)))
    assert r.status_code == 422
    body = promo_body(org)
    body["items"].append({"menu_item_id": 99999, "promo_price": 1000})
    r = create(client, org, body)
    assert r.status_code == 422 and r.json()["error"]["details"]["errors"][0]["menu_item_id"] == 99999
    assert create(client, org, promo_body(org, branch=org.cg) | {"branch_id": 99999}).status_code == 404


def test_F6_47_sua_km_dang_chay_thay_danh_sach_mon(client, org):
    p = create(client, org, promo_body(org, (org.tra_dao, 36000), (org.sua_da, 25000))).json()
    body = promo_body(org, (org.tra_dao, 30000), (org.bac_xiu, 30000), name="Tuần lễ đổi món")
    r = call(client, org.admin, "PUT", f"/api/staff/promotions/{p['id']}", json=body)
    assert r.status_code == 200, r.text
    assert r.json()["name"] == "Tuần lễ đổi món"
    assert [(i["name"], i["promo_price"]) for i in r.json()["items"]] == [("Bạc xỉu", 30000), ("Trà đào cam sả", 30000)]
    menu = public_menu(client, org.cg)
    assert menu["Trà đào cam sả"]["sell_price"] == 30000 and menu["Cà phê sữa đá"]["is_promo"] is False


def test_F6_48_tat_km_va_khong_sua_km_da_ket_thuc(client, db, org):
    p = create(client, org, promo_body(org)).json()
    r = call(client, org.admin, "PUT", f"/api/staff/promotions/{p['id']}", json=promo_body(org, is_active=False))
    assert r.status_code == 200 and r.json()["is_active"] is False
    assert public_menu(client, org.cg)["Trà đào cam sả"]["is_promo"] is False

    ended = f.promo(db, org.admin, {org.sua_da: 20000}, start=timedelta(days=-5), end=timedelta(days=-1))
    r = call(client, org.admin, "PUT", f"/api/staff/promotions/{ended.id}", json=promo_body(org))
    assert r.status_code == 409 and r.json()["error"]["code"] == "PROMOTION_ENDED"
    assert call(client, org.admin, "PUT", "/api/staff/promotions/99999", json=promo_body(org)).status_code == 404


def test_F6_49_danh_sach_theo_tab_dang_chay_sap_chay_da_ket_thuc(client, db, org):
    running = f.promo(db, org.admin, {org.sua_da: 20000})
    upcoming = f.promo(db, org.admin, {org.sua_da: 20000}, b=org.hd, start=timedelta(days=1), end=timedelta(days=2))
    ended = f.promo(db, org.admin, {org.sua_da: 20000}, start=timedelta(days=-5), end=timedelta(days=-1))

    def ids(**params):
        return [p["id"] for p in call(client, org.admin, "GET", "/api/staff/promotions", params=params).json()]

    assert ids(status="running") == [running.id]
    assert ids(status="upcoming") == [upcoming.id]
    assert ids(status="ended") == [ended.id]
    assert set(ids()) == {running.id, upcoming.id, ended.id}
    assert set(ids(branch_id=org.cg.id)) == {running.id, ended.id}                      # toàn chuỗi + đúng CN
    assert call(client, org.admin, "GET", "/api/staff/promotions", params={"status": "x"}).status_code == 422
    one = call(client, org.admin, "GET", f"/api/staff/promotions/{upcoming.id}").json()
    assert one["status"] == "upcoming" and one["branch_name"] == "Chi nhánh HD"
    assert call(client, org.admin, "GET", "/api/staff/promotions/99999").status_code == 404
