import pytest

from app.core.config import get_settings
from tests import factories as f
from tests.f3.conftest import auth


class Org:
    """Dữ liệu chung F6: 2 chi nhánh, nhân viên các vai trò, 2 danh mục, 3 món."""

    def __init__(self, db):
        self.db = db
        self.cg, self.hd = f.branch(db, "CG"), f.branch(db, "HD")
        self.t_cg = f.table(db, self.cg, "05")
        self.admin = f.staff(db, "admin", "ADMIN")
        self.ql = f.staff(db, "ql_cg", "MANAGER", self.cg)
        self.ql_hd = f.staff(db, "ql_hd", "MANAGER", self.hd)
        self.tn = f.staff(db, "tn_cg", "CASHIER", self.cg)
        self.pc = f.staff(db, "pc_cg", "BARISTA", self.cg)
        self.pc_hd = f.staff(db, "pc_hd", "BARISTA", self.hd)
        self.coffee = f.category(db, "Cà phê", 1)
        self.tea = f.category(db, "Trà", 2)
        self.cake = f.category(db, "Bánh", 3)   # danh mục chưa có món
        self.sua_da = f.item(db, self.coffee, "Cà phê sữa đá", 29000)
        self.bac_xiu = f.item(db, self.coffee, "Bạc xỉu", 35000)
        self.tra_dao = f.item(db, self.tea, "Trà đào cam sả", 45000)


@pytest.fixture
def org(db) -> Org:
    return Org(db)


@pytest.fixture(autouse=True)
def _upload_dir(tmp_path):
    """Ảnh món upload trong test ghi vào thư mục tạm, không lẫn vào backend/uploads."""
    s = get_settings()
    old = s.upload_dir
    s.upload_dir = str(tmp_path / "uploads")
    yield tmp_path / "uploads"
    s.upload_dir = old


def call(client, staff, method: str, url: str, **kw):
    return client.request(method, url, headers=auth(staff), **kw)


def public_menu(client, branch) -> dict[str, dict]:
    """Menu khách của chi nhánh: {tên món: item}."""
    r = client.get(f"/api/public/branches/{branch.id}/menu")
    assert r.status_code == 200, r.text
    return {i["name"]: i for c in r.json()["categories"] for i in c["items"]}


def item_body(category, name="Matcha đá xay", price=55000, **kw) -> dict:
    return {"category_id": category.id, "name": name, "base_price": price, "temperature_type": "COLD",
            "tags": ["matcha", "sweet"], **kw}


def staff_body(username="pc_moi", role="BARISTA", branch=None, **kw) -> dict:
    return {"username": username, "full_name": "Nguyễn Văn Mới", "password": "matkhau123", "role": role,
            "branch_id": branch.id if branch else None, **kw}
