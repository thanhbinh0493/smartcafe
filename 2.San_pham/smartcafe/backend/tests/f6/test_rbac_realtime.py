"""F6 – Ma trận phân quyền (III.1) cho API quản trị + sự kiện MENU_UPDATED trên /ws/menu/{branch_id}."""
import pytest
from starlette.websockets import WebSocketDisconnect

from app.ws.hub import hub
from tests.f6.conftest import call, item_body, staff_body
from tests.f6.test_promotions import promo_body

# (method, url, body) – url/body là hàm của org
ADMIN_ONLY = [
    ("POST", lambda o: "/api/staff/categories", lambda o: {"name": "Mới"}),
    ("PUT", lambda o: f"/api/staff/categories/{o.tea.id}", lambda o: {"name": "Trà"}),
    ("DELETE", lambda o: f"/api/staff/categories/{o.cake.id}", None),
    ("POST", lambda o: "/api/staff/menu-items", lambda o: item_body(o.tea)),
    ("PUT", lambda o: f"/api/staff/menu-items/{o.sua_da.id}", lambda o: item_body(o.coffee, name="X")),
    ("DELETE", lambda o: f"/api/staff/menu-items/{o.sua_da.id}", None),
    ("POST", lambda o: "/api/staff/branches", lambda o: {"code": "TD", "name": "TD", "address": "x"}),
    ("PUT", lambda o: f"/api/staff/branches/{o.cg.id}", lambda o: {"name": "CG", "address": "x"}),
    ("GET", lambda o: "/api/staff/promotions", None),
    ("POST", lambda o: "/api/staff/promotions", lambda o: promo_body(o, branch=o.cg)),
]
ADMIN_MANAGER = [
    ("GET", lambda o: "/api/staff/categories", None),
    ("GET", lambda o: "/api/staff/menu-items", None),
    ("GET", lambda o: "/api/staff/branches", None),
    ("GET", lambda o: "/api/staff/staff", None),
    ("POST", lambda o: "/api/staff/staff", lambda o: staff_body("pc_x", "BARISTA", o.cg)),
    ("GET", lambda o: f"/api/staff/branches/{o.cg.id}/menu", None),
    ("PATCH", lambda o: f"/api/staff/branches/{o.cg.id}/menu/{o.sua_da.id}", lambda o: {"is_available": True}),
    ("GET", lambda o: f"/api/staff/branches/{o.cg.id}/tables", None),
    ("POST", lambda o: f"/api/staff/branches/{o.cg.id}/tables", lambda o: {"table_number": "99"}),
    ("GET", lambda o: f"/api/staff/tables/{o.t_cg.id}/qr.png", None),
]


def _req(client, org, who, method, url, body):
    return call(client, getattr(org, who), method, url(org), **({"json": body(org)} if body else {}))


@pytest.mark.parametrize("who", ["ql", "tn", "pc"])
@pytest.mark.parametrize("method, url, body", ADMIN_ONLY, ids=[f"{m} {i}" for i, (m, *_) in enumerate(ADMIN_ONLY)])
def test_F6_50_chi_quan_tri_vien(client, org, who, method, url, body):
    r = _req(client, org, who, method, url, body)
    assert r.status_code == 403 and r.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.parametrize("method, url, body", ADMIN_ONLY, ids=[f"{m} {i}" for i, (m, *_) in enumerate(ADMIN_ONLY)])
def test_F6_51_quan_tri_vien_duoc_phep(client, org, method, url, body):
    assert _req(client, org, "admin", method, url, body).status_code in (200, 201, 204)


@pytest.mark.parametrize("who, ok", [("admin", True), ("ql", True), ("tn", False), ("pc", False)])
@pytest.mark.parametrize("method, url, body", ADMIN_MANAGER,
                         ids=[f"{m} {i}" for i, (m, *_) in enumerate(ADMIN_MANAGER)])
def test_F6_52_quan_tri_vien_va_quan_ly(client, org, who, ok, method, url, body):
    r = _req(client, org, who, method, url, body)
    assert (r.status_code in (200, 201)) if ok else (r.status_code == 403), r.text


@pytest.mark.parametrize("method, url", [
    ("GET", lambda o: f"/api/staff/branches/{o.hd.id}/menu"),
    ("GET", lambda o: f"/api/staff/branches/{o.hd.id}/tables"),
    ("POST", lambda o: f"/api/staff/branches/{o.hd.id}/tables"),
])
def test_F6_53_quan_ly_khong_thao_tac_chi_nhanh_khac(client, org, method, url):
    r = call(client, org.ql, method, url(org), **({"json": {"table_number": "9"}} if method == "POST" else {}))
    assert r.status_code == 403


def test_F6_54_chua_dang_nhap_hoac_token_khach(client, org):
    assert client.get("/api/staff/categories").status_code == 401
    from tests.f3.test_realtime import customer_token
    r = client.get("/api/staff/categories", headers={"Authorization": f"Bearer {customer_token()}"})
    assert r.status_code == 403


# ---------- Realtime MENU_UPDATED ----------
def menu_ws(client, branch):
    return client.websocket_connect(f"/ws/menu/{branch.id}")


def test_F6_55_ws_menu_tu_choi_chi_nhanh_khong_ton_tai_hoac_ngung(client, db, org):
    org.hd.is_active = False
    db.flush()
    for bid in (99999, org.hd.id):
        with pytest.raises(WebSocketDisconnect) as e:
            with client.websocket_connect(f"/ws/menu/{bid}") as ws:
                ws.receive_json()
        assert e.value.code == 4404


def test_F6_56_doi_menu_chi_nhanh_chi_bao_chi_nhanh_do(client, org):
    with menu_ws(client, org.cg) as cg, menu_ws(client, org.hd) as hd:
        call(client, org.ql, "PATCH", f"/api/staff/branches/{org.cg.id}/menu/{org.sua_da.id}",
             json={"is_available": False})
        evt = cg.receive_json()
        assert evt["type"] == "MENU_UPDATED" and evt["data"] == {"branch_id": org.cg.id, "reason": "BRANCH_MENU"}
        # HD không nhận: gửi 1 thay đổi toàn chuỗi để chắc sự kiện kế tiếp của HD là sự kiện đó
        call(client, org.admin, "POST", "/api/staff/categories", json={"name": "Kem"})
        assert hd.receive_json()["data"] == {"branch_id": None, "reason": "CATEGORY"}
        assert cg.receive_json()["data"]["reason"] == "CATEGORY"
    assert hub.subscriber_count(f"menu:{org.cg.id}") == 0


@pytest.mark.parametrize("action, reason", [
    (lambda c, o: call(c, o.admin, "PUT", f"/api/staff/menu-items/{o.sua_da.id}",
                       json=item_body(o.coffee, name="Cà phê sữa đá", price=30000)), "MENU_ITEM"),
    (lambda c, o: call(c, o.admin, "DELETE", f"/api/staff/menu-items/{o.bac_xiu.id}"), "MENU_ITEM"),
    (lambda c, o: call(c, o.admin, "POST", "/api/staff/promotions", json=promo_body(o)), "PROMOTION"),
    (lambda c, o: call(c, o.admin, "POST", "/api/staff/promotions", json=promo_body(o, branch=o.hd)), "PROMOTION"),
    (lambda c, o: call(c, o.admin, "PUT", f"/api/staff/branches/{o.hd.id}",
                       json={"name": "HD", "address": "x", "is_active": True}), "BRANCH"),
], ids=["sua_mon", "xoa_mon", "km_toan_chuoi", "km_chi_nhanh", "sua_chi_nhanh"])
def test_F6_57_menu_khach_nhan_su_kien_khi_quan_tri_thay_doi(client, org, action, reason):
    with menu_ws(client, org.hd) as ws:
        assert action(client, org).status_code in (200, 201, 204)
        evt = ws.receive_json()
        assert evt["type"] == "MENU_UPDATED" and evt["data"]["reason"] == reason
