"""F0 – Phân quyền theo vai trò và chi nhánh (ma trận RBAC, III.1).
Dùng 2 endpoint chỉ có trong test để kiểm tra các dependency dùng chung cho mọi API nhân viên."""
import pytest
from fastapi import APIRouter, Depends

from app.core.security import create_staff_token
from app.main import app
from app.models import Staff
from app.modules.auth.deps import ensure_branch_access, require_roles
from tests import factories as f

router = APIRouter()


@router.post("/_test/barista-action")
def barista_action(staff: Staff = Depends(require_roles("BARISTA", "MANAGER"))):
    return {"ok": True}


@router.get("/_test/branches/{branch_id}/data")
def branch_data(branch_id: int, staff: Staff = Depends(require_roles("ADMIN", "MANAGER", "CASHIER", "BARISTA"))):
    ensure_branch_access(staff, branch_id)
    return {"ok": True}


@pytest.fixture(autouse=True, scope="module")
def _mount_test_routes():
    app.include_router(router)
    yield
    app.router.routes[:] = [r for r in app.router.routes if not getattr(r, "path", "").startswith("/_test")]


def auth(s: Staff) -> dict:
    return {"Authorization": f"Bearer {create_staff_token(s.id, s.role, s.branch_id)}"}


@pytest.mark.parametrize("role,expected", [
    ("BARISTA", 200), ("MANAGER", 200), ("CASHIER", 403), ("ADMIN", 403),
])
def test_F0_26_require_roles_theo_ma_tran_rbac(client, db, role, expected):
    """VD: Bắt đầu/Xong món chỉ BARISTA, MANAGER (III.1)."""
    b = f.branch(db)
    s = f.staff(db, f"u_{role.lower()}", role, None if role == "ADMIN" else b)
    r = client.post("/_test/barista-action", headers=auth(s))
    assert r.status_code == expected
    if expected == 403:
        assert r.json()["error"]["code"] == "FORBIDDEN"


def test_F0_27_nhan_vien_chi_truy_cap_chi_nhanh_cua_minh(client, db):
    cg, hd = f.branch(db, "CG"), f.branch(db, "HD")
    s = f.staff(db, "pc1_cg", "BARISTA", cg)
    assert client.get(f"/_test/branches/{cg.id}/data", headers=auth(s)).status_code == 200
    r = client.get(f"/_test/branches/{hd.id}/data", headers=auth(s))
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "FORBIDDEN"


def test_F0_28_admin_truy_cap_moi_chi_nhanh(client, db):
    cg, hd = f.branch(db, "CG"), f.branch(db, "HD")
    a = f.staff(db, "admin", "ADMIN")
    for b in (cg, hd):
        assert client.get(f"/_test/branches/{b.id}/data", headers=auth(a)).status_code == 200
