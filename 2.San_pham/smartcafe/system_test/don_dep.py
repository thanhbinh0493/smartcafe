# -*- coding: utf-8 -*-
"""Dọn dữ liệu tạm sau một lần chạy kiểm thử hệ thống bị dừng giữa chừng: giao hết các đơn đang chờ ở mọi chi nhánh,
tắt các khuyến mãi tên "KM kiểm thử hệ thống", bật lại "Còn hàng" cho Bạc xỉu ở chi nhánh Cầu Giấy (món kịch bản ST-02 tắt; Bạc xỉu nóng giữ "Tạm hết" như dữ liệu mẫu).

    .venv\\Scripts\\python don_dep.py
"""
import httpx

from common import args, branches, finish_order, login

a = args()
c = httpx.Client(base_url=a.base_url, timeout=15)
admin = login(c, "admin")
for code, b in branches(c, admin).items():
    pc = login(c, f"pc1_{code.lower()}")
    q = c.get(f"/api/staff/branches/{b['id']}/queue", headers=pc).json()["items"]
    for oid in dict.fromkeys(i["order_id"] for i in q):
        finish_order(c, pc, oid, b["id"])
    for o in c.get(f"/api/staff/branches/{b['id']}/orders", params={"status": "READY"}, headers=pc).json():
        c.post(f"/api/staff/orders/{o['id']}/complete", headers=pc)
    print(code, "đã giao", len(set(i["order_id"] for i in q)), "đơn")
for pr in c.get("/api/staff/promotions", headers=admin).json():
    if pr["name"] == "KM kiểm thử hệ thống" and pr["is_active"]:
        body = {k: pr[k] for k in ("name", "description", "branch_id", "start_at", "end_at")}
        body["items"] = [{"menu_item_id": i["menu_item_id"], "promo_price": i["promo_price"]} for i in pr["items"]]
        print("tắt KM", pr["id"], c.put(f"/api/staff/promotions/{pr['id']}", headers=admin, json={**body, "is_active": False}).status_code)
cg = branches(c, admin)["CG"]
ql = login(c, "ql_cg")
for row in c.get(f"/api/staff/branches/{cg['id']}/menu", headers=ql).json():
    if row["name"] == "Bạc xỉu" and not row["is_available"]:
        r = c.patch(f"/api/staff/branches/{cg['id']}/menu/{row['menu_item_id']}", headers=ql, json={"is_available": True})
        print("bật lại", row["name"], r.status_code)
