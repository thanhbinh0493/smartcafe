import pytest

from tests import factories as f


class Shop:
    """Dữ liệu chung cho F2: 2 chi nhánh, 3 món, 1 KM toàn chuỗi."""

    def __init__(self, db):
        self.db = db
        self.cg, self.hd = f.branch(db, "CG"), f.branch(db, "HD")
        self.t_cg, self.t_cg2, self.t_hd = f.table(db, self.cg, "05"), f.table(db, self.cg, "06"), f.table(db, self.hd, "01")
        self.admin = f.staff(db, "admin", "ADMIN")
        cat = f.category(db, "Coffee", 1)
        self.sua_da = f.item(db, cat, "Ca phe sua da", 29000)
        self.tra_dao = f.item(db, cat, "Tra dao", 45000)
        self.banh = f.item(db, cat, "Banh croissant", 30000)
        self.promo = f.promo(db, self.admin, {self.tra_dao: 36000})


@pytest.fixture
def shop(db) -> Shop:
    return Shop(db)


def order_body(table, *lines, **extra) -> dict:
    """lines: (item, quantity[, note])"""
    items = [{"menu_item_id": l[0].id, "quantity": l[1], **({"note": l[2]} if len(l) > 2 else {})} for l in lines]
    return {"qr_token": table.qr_token, "items": items, **extra}


def place(client, table, *lines, **extra):
    return client.post("/api/public/orders", json=order_body(table, *lines, **extra))


def place_and_pay(client, table, *lines, method="MOCK_EWALLET", **extra) -> dict:
    o = place(client, table, *lines, **extra).json()
    r = client.post(f"/api/public/orders/{o['order_id']}/pay", json={"access_token": o["access_token"], "method": method})
    assert r.status_code == 200, r.text
    return o
