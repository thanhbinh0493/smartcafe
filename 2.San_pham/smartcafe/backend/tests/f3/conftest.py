import pytest

from app.core.security import create_staff_token
from tests import factories as f
from tests.f2.conftest import Shop, place_and_pay


class Bar(Shop):
    """Shop của F2 + nhân viên 2 chi nhánh."""

    def __init__(self, db):
        super().__init__(db)
        self.pc = f.staff(db, "pc1_cg", "BARISTA", self.cg)
        self.pc2 = f.staff(db, "pc2_cg", "BARISTA", self.cg)
        self.ql = f.staff(db, "ql_cg", "MANAGER", self.cg)
        self.tn = f.staff(db, "tn_cg", "CASHIER", self.cg)
        self.pc_hd = f.staff(db, "pc1_hd", "BARISTA", self.hd)


@pytest.fixture
def bar(db) -> Bar:
    return Bar(db)


def auth(staff) -> dict:
    return {"Authorization": f"Bearer {create_staff_token(staff.id, staff.role, staff.branch_id)}"}


def token(staff) -> str:
    return create_staff_token(staff.id, staff.role, staff.branch_id)


def queue(client, staff, branch) -> list[dict]:
    r = client.get(f"/api/staff/branches/{branch.id}/queue", headers=auth(staff))
    assert r.status_code == 200, r.text
    return r.json()["items"]


def ready(client, staff, branch) -> list[dict]:
    r = client.get(f"/api/staff/branches/{branch.id}/orders", params={"status": "READY"}, headers=auth(staff))
    assert r.status_code == 200, r.text
    return r.json()


def act(client, staff, item_id: int, action: str):
    return client.post(f"/api/staff/order-items/{item_id}/{action}", headers=auth(staff))


def complete(client, staff, order_id: int):
    return client.post(f"/api/staff/orders/{order_id}/complete", headers=auth(staff))


def view(client, o) -> dict:
    return client.get(f"/api/public/orders/{o['order_id']}", params={"token": o["access_token"]}).json()


def item_ids(o) -> list[int]:
    return [i["id"] for i in o["items"]]


def make_ready(client, staff, o) -> None:
    for iid in item_ids(o):
        assert act(client, staff, iid, "start").status_code == 200
        assert act(client, staff, iid, "done").status_code == 200


__all__ = ["place_and_pay"]
