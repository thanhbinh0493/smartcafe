"""F0 – Ứng dụng khởi động, tài liệu Swagger và định dạng lỗi thống nhất."""


def test_F0_29_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_F0_30_swagger_co_tai_lieu_api(client):
    """NFR-M1: tài liệu API tự sinh tại /docs."""
    assert client.get("/docs").status_code == 200
    paths = client.get("/openapi.json").json()["paths"]
    assert {"/api/auth/login", "/api/auth/me", "/api/public/tables/{qr_token}",
            "/api/public/branches/{branch_id}/menu"} <= set(paths)


def test_F0_31_route_khong_ton_tai_tra_loi_dung_dinh_dang(client):
    r = client.get("/api/khong-co")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"
