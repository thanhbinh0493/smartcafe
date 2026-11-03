# -*- coding: utf-8 -*-
"""Kiểm thử hệ thống – kịch bản "một ngày làm việc" xuyên các luồng F1 → F8 trên 5 thiết bị cùng lúc
(Playwright + Edge): điện thoại khách ẩn danh, điện thoại khách thành viên, màn hình Bar (pha chế),
tablet thu ngân, laptop quản lý / quản trị.

    .venv\\Scripts\\python st_kich_ban.py

Kết thúc: chạy thử job báo cáo cho HÔM NAY trong 1 transaction rồi rollback để đối chiếu số liệu của chính
kịch bản (không ghi báo cáo cho ngày chưa kết thúc).
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from playwright.sync_api import expect, sync_playwright

from common import DEMO_PHONE, Report, args, backend_py, branches, login, menu, sql, tables

rep = Report()
PHONE = {"viewport": {"width": 390, "height": 844}, "device_scale_factor": 2, "is_mobile": True, "has_touch": True,
         "locale": "vi-VN"}
VN = timezone(timedelta(hours=7))


def staff(browser, base, username, size):
    page = browser.new_context(viewport={"width": size[0], "height": size[1]}, locale="vi-VN").new_page()
    page.goto(f"{base}/admin/login")
    page.get_by_label("Tên đăng nhập").fill(username)
    page.get_by_label("Mật khẩu").fill("smartcafe123")
    page.get_by_role("button", name="Đăng nhập").click()
    page.wait_for_url(re.compile(r"/admin/(bar|dashboard)"))
    return page


def money(text: str) -> int:
    return int(re.sub(r"\D", "", text))


def pay_from_cart(phone) -> tuple[str, int]:
    phone.get_by_role("button", name="Thanh toán & gửi đơn").click()
    phone.get_by_text("✔ Thanh toán thành công").wait_for(timeout=10000)
    code = phone.locator("h1").first.inner_text().split("#")[-1].strip()
    return code, int(re.search(r"/orders/(\d+)", phone.url).group(1))


def main() -> int:
    a = args()
    base, img = a.base_url, Path(a.img)
    c = httpx.Client(base_url=base, timeout=15)
    admin = login(c, "admin")
    cg = branches(c, admin)["CG"]
    tbl = tables(c, admin, cg["id"])
    qr1, qr2, qr3 = tbl[2]["qr_token"], tbl[3]["qr_token"], tbl[4]["qr_token"]
    start = datetime.now(timezone.utc)
    m = menu(c, cg["id"])

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        manager = staff(browser, base, "ql_cg", (1366, 900))
        bar = staff(browser, base, "pc1_cg", (1366, 900))
        bar.goto(f"{base}/admin/bar")
        expect(bar.get_by_test_id("bar-connection")).to_have_text("● Trực tuyến", timeout=8000)
        cashier = staff(browser, base, "tn_cg", (1024, 768))
        cashier.goto(f"{base}/admin/bar")
        anon = browser.new_context(**PHONE).new_page()
        anon.goto(f"{base}/t/{qr1}")
        anon.get_by_role("button", name="Xem menu ngay").click()
        anon.get_by_role("button", name="Thêm Bạc xỉu", exact=True).wait_for()

        # ST-01: quản trị viên tạo KM → khách đang mở menu thấy ngay
        tra = m["Trà đào cam sả"]
        promo_price = tra["sell_price"] - 10000
        now = datetime.now(VN)
        pr = c.post("/api/staff/promotions", headers=admin, json={
            "name": "KM kiểm thử hệ thống", "description": "ST-01", "branch_id": cg["id"], "is_active": True,
            "start_at": (now - timedelta(minutes=1)).isoformat(), "end_at": (now + timedelta(hours=3)).isoformat(),
            "items": [{"menu_item_id": tra["id"], "promo_price": promo_price}]})
        card = anon.locator("li[data-testid^=menu-item]").filter(has=anon.get_by_text("Trà đào cam sả", exact=True)).first
        try:
            expect(card).to_contain_text(f"{promo_price:,}đ".replace(",", "."), timeout=4000)
            seen = True
        except AssertionError:
            seen = False
        rep.check("ST-01", "UC15→UC02: quản trị viên tạo khuyến mãi → điện thoại khách đang mở menu thấy giá KM ngay (không tải lại)",
                  pr.status_code == 201 and seen, f"KM {pr.status_code}, giá KM {promo_price}")

        # ST-02: quản lý tắt "Còn hàng" Bạc xỉu → khách thấy "Tạm hết", AI không gợi ý món này
        manager.goto(f"{base}/admin/branch-menu")
        row = manager.get_by_role("row").filter(has=manager.get_by_label("Còn hàng Bạc xỉu", exact=True))
        row.get_by_label("Còn hàng Bạc xỉu", exact=True).uncheck()
        row.get_by_role("button", name="Lưu Bạc xỉu").click()
        expect(manager.get_by_role("status")).to_contain_text('Đã lưu "Bạc xỉu"')
        bx = anon.locator("li[data-testid^=menu-item]").filter(has=anon.get_by_text("Bạc xỉu", exact=True)).first
        expect(bx.get_by_role("button", name="Thêm Bạc xỉu", exact=True)).to_have_count(0, timeout=4000)
        recs = c.get(f"/api/public/branches/{cg['id']}/recommendations").json()
        rep.check("ST-02", "UC13→UC02/UC03: quản lý tắt 'Còn hàng' Bạc xỉu → khách thấy hết hàng ngay, gợi ý AI không còn món này",
                  "Tạm hết" in bx.inner_text() and all(r["name"] != "Bạc xỉu" for r in recs["items"]))

        # ST-03: khách ẩn danh chọn món KM + 1 món từ "Gợi ý cho bạn" + 1 món từ "Thường gọi kèm", thanh toán
        anon.get_by_role("button", name="Thêm Trà đào cam sả", exact=True).click()
        rec_block = anon.get_by_test_id("rec-block")
        rec_btn = rec_block.get_by_role("button", name=re.compile(r"\(gợi ý\)$")).first
        rec_name = rec_btn.get_attribute("aria-label").removeprefix("Thêm ").removesuffix(" (gợi ý)")
        rec_btn.click()
        anon.get_by_role("link", name=re.compile(r"Giỏ hàng \(2\)")).click()
        anon.get_by_role("heading", name="Giỏ hàng").wait_for()
        co = anon.get_by_test_id("also-bought").get_by_role("button", name=re.compile(r"\(gợi ý\)$"))
        co_name = None
        if co.count():
            co_name = co.first.get_attribute("aria-label").removeprefix("Thêm ").removesuffix(" (gợi ý)")
            co.first.click()
        total_ui = money(anon.get_by_test_id("cart-total").inner_text())
        anon.screenshot(path=img / "ST_01_gio_hang_km_goi_y.png", full_page=True)
        code_a, oid_a = pay_from_cart(anon)
        lines = sql(f"SELECT mi.name, oi.unit_price, oi.quantity, oi.is_recommended, oi.promotion_id IS NOT NULL "
                    f"FROM order_items oi JOIN menu_items mi ON mi.id = oi.menu_item_id WHERE oi.order_id = {oid_a}")
        by = {r[0]: r for r in lines}
        log = sql(f"SELECT count(*) FROM recommendation_logs WHERE order_id = {oid_a}")[0][0]
        total_db = int(sql(f"SELECT total_amount FROM orders WHERE id = {oid_a}")[0][0])
        rep.check("ST-03", "UC02→UC04: đơn ẩn danh có món KM (đúng giá KM, gắn promotion_id), món từ gợi ý (is_recommended, "
                  "gắn recommendation_log), tổng tiền giỏ = tổng server",
                  int(by["Trà đào cam sả"][1]) == promo_price and by["Trà đào cam sả"][4] == "t"
                  and by[rec_name][3] == "t" and (co_name is None or by[co_name][3] == "t")
                  and int(log) >= 1 and total_ui == total_db,
                  f"{code_a}: {[(r[0], r[1], 'gợi ý' if r[3] == 't' else '', 'KM' if r[4] == 't' else '') for r in lines]}; "
                  f"tổng {total_db}; log gợi ý gắn đơn: {log}")

        # ST-04: Bar nhận đơn, pha chế làm, khách thấy từng bước
        expect(bar.get_by_role("cell", name=code_a, exact=True).first).to_be_visible(timeout=3000)
        steps = []
        n_items = len(lines)
        tno = re.escape(tbl[2]["table_number"])
        starts = bar.get_by_role("button", name=re.compile(r"^Bắt đầu .* bàn " + tno + "$"))
        dones = bar.get_by_role("button", name=re.compile(r"^Xong .* bàn " + tno + "$"))
        for i in range(n_items):
            starts.first.click()
            expect(starts).to_have_count(n_items - i - 1, timeout=3000)     # chờ món vừa bấm chuyển "ĐANG PHA"
            if i == 0:
                expect(anon.get_by_text("Đang pha chế").first).to_be_visible(timeout=3000)
                steps.append("Đang pha chế")
        for i in range(n_items):
            dones.first.click()
            expect(dones).to_have_count(n_items - i - 1, timeout=3000)
        anon.get_by_text("Đồ uống đã sẵn sàng – mời bạn đến quầy nhận").wait_for(timeout=4000)
        steps.append("Có thể lấy")
        bar.get_by_role("button", name=f"Đã giao {code_a}").click()
        expect(bar.get_by_role("status")).to_contain_text(f"Đã giao đơn {code_a}")
        status_a = sql(f"SELECT status FROM orders WHERE id = {oid_a}")[0][0]
        hist = [r[0] for r in sql(f"SELECT to_status FROM order_status_history WHERE order_id = {oid_a} ORDER BY id")]
        rep.check("ST-04", "UC17–UC19→UC06: pha chế Bắt đầu / Xong / Đã giao trên Bar → khách thấy 'Đang pha chế' → "
                  "'Có thể lấy' realtime; lịch sử trạng thái đầy đủ", status_a == "COMPLETED"
                  and hist[-4:] == ["PAID", "PREPARING", "READY", "COMPLETED"], f"{steps}; lịch sử {hist}")

        # ST-05: khách thành viên (SĐT demo) – OTP, "Bạn hay gọi", đặt, nhận điểm
        # NFR-S4 chỉ cho gửi lại mã sau 60 giây: nếu SĐT demo vừa được dùng (lần chạy trước) thì chờ cho đủ
        last = sql(f"SELECT extract(epoch FROM now() - max(created_at)) FROM otp_requests WHERE phone = '{DEMO_PHONE}'")
        last = last[0][0] if last else None
        if last and float(last) < 61:
            time.sleep(61 - float(last))
        mem = browser.new_context(**PHONE).new_page()
        mem.goto(f"{base}/t/{qr2}")
        mem.get_by_role("button", name="Nhập số điện thoại").click()
        mem.get_by_role("textbox", name="Số điện thoại").fill(DEMO_PHONE)
        mem.get_by_role("button", name="Gửi mã OTP").click()
        demo = mem.get_by_test_id("demo-code").inner_text()
        mem.get_by_role("textbox", name="Số thứ 1 của mã OTP").click()
        mem.keyboard.type(demo)
        mem.get_by_role("button", name="Xác nhận").click()
        member_bar = mem.get_by_test_id("member-bar")
        member_bar.wait_for(timeout=5000)
        pts_before = int(re.search(r"(\d+) điểm", member_bar.inner_text()).group(1))
        rec = mem.get_by_test_id("rec-block")
        expect(rec).to_contain_text("Bạn hay gọi", timeout=5000)
        mem.screenshot(path=img / "ST_05_thanh_vien_ban_hay_goi.png", full_page=True)
        mem.get_by_role("button", name="Thêm Cà phê sữa đá", exact=True).click()
        mem.get_by_role("button", name="Thêm Cà phê sữa đá", exact=True).click()
        mem.get_by_role("link", name=re.compile(r"Giỏ hàng \(2\)")).click()
        total_m = money(mem.get_by_test_id("cart-total").inner_text())
        code_m, oid_m = pay_from_cart(mem)
        expect(bar.get_by_role("cell", name=code_m, exact=True).first).to_be_visible(timeout=3000)
        for verb in ("Bắt đầu", "Xong"):
            btn = bar.get_by_role("button", name=f"{verb} Cà phê sữa đá bàn {tbl[3]['table_number']}")
            btn.first.click()
            expect(btn).to_have_count(0, timeout=3000)
        bar.get_by_role("button", name=f"Đã giao {code_m}").click()
        earned = mem.get_by_test_id("points-earned")
        earned.wait_for(timeout=4000)
        expect_pts = total_m // 10000
        pts_db = int(sql(f"SELECT loyalty_points FROM customers WHERE phone = '{DEMO_PHONE}'")[0][0])
        tx = sql(f"SELECT points FROM loyalty_transactions WHERE order_id = {oid_m}")
        rep.check("ST-05", "UC01/UC07→UC02→UC19: thành viên xác thực OTP, menu có 'Bạn hay gọi', đặt món, nhận đồ thì "
                  "được cộng điểm (1 điểm/10.000đ) realtime đúng 1 lần",
                  str(expect_pts) in earned.inner_text()
                  and pts_db == pts_before + expect_pts and tx == [[str(expect_pts)]],
                  f"{code_m} {total_m}đ → +{expect_pts} điểm; điểm {pts_before} → {pts_db}")
        mem.screenshot(path=img / "ST_05_duoc_cong_diem.png", full_page=True)
        again = c.post(f"/api/staff/orders/{oid_m}/complete", headers=login(c, "pc1_cg"))
        rep.check("ST-06", "NFR-R4: bấm 'Đã giao' lần 2 cho cùng đơn → bị từ chối, không cộng điểm 2 lần",
                  again.status_code == 409 and int(sql(f"SELECT loyalty_points FROM customers WHERE phone = '{DEMO_PHONE}'")[0][0]) == pts_db,
                  f"{again.status_code} {again.json()['error']['code']}")

        # ST-07: khách thứ 3 đặt nhầm → thu ngân hủy & hoàn tiền; Bar + khách nhận realtime
        third = browser.new_context(**PHONE).new_page()
        third.goto(f"{base}/t/{qr3}")
        third.get_by_role("button", name="Xem menu ngay").click()
        third.get_by_role("button", name="Thêm Cà phê đen đá", exact=True).click()
        third.get_by_role("link", name="Giỏ hàng (1)").click()
        code_c, oid_c = pay_from_cart(third)
        expect(bar.get_by_role("cell", name=code_c, exact=True).first).to_be_visible(timeout=3000)
        panel = cashier.get_by_role("region", name="Hỗ trợ khách")
        panel.get_by_label("Mã đơn").fill(code_c.split("-")[-1])
        panel.get_by_role("button", name="Tìm").click()
        panel.locator("li").filter(has_text=code_c).get_by_role("button", name=f"Hủy đơn {code_c}").click()
        dlg = cashier.get_by_role("dialog")
        dlg.get_by_role("button", name="Khách gọi nhầm món").click()
        dlg.get_by_role("button", name="Xác nhận hủy & hoàn tiền").click()
        expect(panel.get_by_role("status")).to_contain_text(f"Đã hủy đơn {code_c}")
        expect(third.get_by_text("Đơn đã hủy – đã hoàn tiền")).to_be_visible(timeout=3000)
        expect(bar.get_by_role("cell", name=code_c, exact=True)).to_have_count(0, timeout=3000)
        pay = sql(f"SELECT status FROM payments WHERE order_id = {oid_c}")
        rep.check("ST-07", "UC20: thu ngân hủy đơn & hoàn tiền → món rời hàng đợi Bar, điện thoại khách báo đã hoàn tiền; "
                  "thanh toán chuyển REFUNDED", pay and pay[0][0] == "REFUNDED", f"{code_c}: {pay}")

        # ST-08: dọn – bật lại Bạc xỉu, tắt KM
        anon.goto(f"{base}/t/{qr1}/menu")                                 # khách quay lại menu ("Gọi thêm món")
        bx.wait_for(timeout=5000)
        row.get_by_label("Còn hàng Bạc xỉu", exact=True).check()
        row.get_by_role("button", name="Lưu Bạc xỉu").click()
        expect(bx.get_by_role("button", name="Thêm Bạc xỉu", exact=True)).to_be_visible(timeout=4000)
        if pr.status_code == 201:
            body = {k: v for k, v in pr.json().items() if k in ("name", "description", "branch_id", "start_at", "end_at")}
            body["items"] = [{"menu_item_id": i["menu_item_id"], "promo_price": i["promo_price"]} for i in pr.json()["items"]]
            off = c.put(f"/api/staff/promotions/{pr.json()['id']}", headers=admin, json={**body, "is_active": False})
            expect(card).not_to_contain_text("Giá gốc", timeout=4000)
            rep.check("ST-08", "UC13/UC15: bật lại 'Còn hàng', tắt KM → điện thoại khách trở lại giá thường, đặt lại được Bạc xỉu",
                      off.status_code == 200 and tra["sell_price"] == menu(c, cg["id"])["Trà đào cam sả"]["sell_price"])
        anon.screenshot(path=img / "ST_08_menu_tro_lai.png", full_page=True)
        browser.close()

    # ST-09: báo cáo ngày – chạy job cho HÔM NAY trong transaction rồi rollback, đối chiếu đúng các đơn của kịch bản
    out = backend_py(
        "import json\n"
        "from sqlalchemy import select\n"
        "from app.core.db import SessionLocal\n"
        "from app.models.analytics import DailySalesReport as R\n"
        "from app.modules.report.service import build_daily_report, today_vn\n"
        f"db = SessionLocal(); d = today_vn(); build_daily_report(db, {cg['id']}, d)\n"
        f"r = db.scalar(select(R).where(R.branch_id == {cg['id']}, R.report_date == d))\n"
        "cols = ('order_count', 'cancelled_count', 'revenue', 'promo_revenue', 'member_order_ratio', 'recommended_item_ratio')\n"
        "print(json.dumps({k: float(getattr(r, k)) for k in cols}))\n"
        "db.rollback(); db.close()\n")
    rpt = json.loads(out)
    exp = sql(f"SELECT count(*) FILTER (WHERE status <> 'CANCELLED'), count(*) FILTER (WHERE status = 'CANCELLED'), "
              f"coalesce(sum(total_amount) FILTER (WHERE status <> 'CANCELLED'), 0) FROM orders "
              f"WHERE branch_id = {cg['id']} AND paid_at IS NOT NULL AND (paid_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::date = "
              f"(now() AT TIME ZONE 'Asia/Ho_Chi_Minh')::date")[0]
    keys = {k: rpt[k] for k in rpt if k in ("order_count", "cancelled_count", "revenue", "promo_revenue",
                                             "member_order_ratio", "recommended_item_ratio")}
    rep.check("ST-09", "UC16: job báo cáo ngày (chạy thử cho hôm nay rồi rollback) khớp dữ liệu đơn: số đơn, đơn hủy, doanh thu; "
              "doanh thu KM, tỉ lệ thành viên, tỉ lệ món từ gợi ý > 0 nhờ các đơn của kịch bản",
              int(rpt["order_count"]) == int(exp[0]) and int(rpt["cancelled_count"]) == int(exp[1])
              and int(rpt["revenue"]) == int(exp[2]) and float(rpt["promo_revenue"]) > 0
              and float(rpt["member_order_ratio"]) > 0 and float(rpt["recommended_item_ratio"]) > 0, json.dumps(keys))

    # ST-10: đối soát toàn bộ 60 ngày lịch sử × 3 chi nhánh
    diff = sql("""
        WITH o AS (
          SELECT branch_id, (paid_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::date AS d,
                 count(*) FILTER (WHERE status <> 'CANCELLED') AS n,
                 count(*) FILTER (WHERE status = 'CANCELLED') AS cn,
                 coalesce(sum(total_amount) FILTER (WHERE status <> 'CANCELLED'), 0) AS rev
          FROM orders WHERE paid_at IS NOT NULL GROUP BY 1, 2)
        SELECT r.branch_id, r.report_date, r.order_count, coalesce(o.n, 0), r.revenue, coalesce(o.rev, 0)
        FROM daily_sales_reports r LEFT JOIN o ON o.branch_id = r.branch_id AND o.d = r.report_date
        WHERE r.order_count <> coalesce(o.n, 0) OR r.revenue <> coalesce(o.rev, 0)
           OR r.cancelled_count <> coalesce(o.cn, 0)""")
    total = sql("SELECT count(*), min(report_date), max(report_date) FROM daily_sales_reports")[0]
    rep.check("ST-10", "UC16: đối soát mọi dòng daily_sales_reports với bảng orders (số đơn, đơn hủy, doanh thu) – không lệch",
              not diff and int(total[0]) >= 180, f"{total[0]} dòng ({total[1]} → {total[2]}), lệch: {diff[:3]}")
    print(f"(bắt đầu kịch bản {start.astimezone(VN):%H:%M:%S})")
    return rep.finish()


if __name__ == "__main__":
    raise SystemExit(main())
