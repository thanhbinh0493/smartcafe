# -*- coding: utf-8 -*-
"""Chụp ảnh màn hình cho Hướng dẫn sử dụng (giai đoạn VII) trên hệ thống chạy bằng docker compose (CSDL sạch).

    .venv\\Scripts\\python chup_anh_hdsd.py

Ảnh lưu vào 1.Bao_cao/Huong_dan_su_dung/img/ (K = khách, N = nhân viên). Mỗi ảnh chụp độc lập: một ảnh lỗi
không làm dừng các ảnh khác; cuối cùng in danh sách ảnh lỗi.
"""
from __future__ import annotations

import re
import time
from pathlib import Path

import httpx
from playwright.sync_api import expect, sync_playwright

from common import DEMO_PHONE, ROOT, branches, finish_order, login, menu, place_order, sql, tables

OUT = ROOT.parent.parent / "1.Bao_cao" / "Huong_dan_su_dung" / "img"
BASE = "http://localhost:8080"
PHONE = {"viewport": {"width": 390, "height": 844}, "device_scale_factor": 2, "is_mobile": True, "has_touch": True,
         "locale": "vi-VN"}
done, failed = [], []


def shot(page, name: str, full: bool = True, locator=None) -> None:
    try:
        (locator or page).screenshot(path=OUT / f"{name}.png", **({"full_page": full} if locator is None else {}))
        done.append(name)
    except Exception as e:                                                # noqa: BLE001
        failed.append(f"{name}: {e}")


def step(name: str, fn) -> None:
    try:
        fn()
    except Exception as e:                                                # noqa: BLE001
        failed.append(f"{name}: {str(e)[:200]}")
        print("LỖI", name, str(e)[:300])


def staff_page(browser, username: str, size=(1366, 900)):
    page = browser.new_context(viewport={"width": size[0], "height": size[1]}, locale="vi-VN").new_page()
    page.goto(f"{BASE}/admin/login")
    page.get_by_label("Tên đăng nhập").fill(username)
    page.get_by_label("Mật khẩu").fill("smartcafe123")
    page.get_by_role("button", name="Đăng nhập").click()
    page.wait_for_url(re.compile(r"/admin/(bar|dashboard)"))
    return page


def nav(page, label: str) -> None:
    page.get_by_role("navigation", name="Menu quản trị").get_by_role("link", name=label, exact=True).click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(400)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    c = httpx.Client(base_url=BASE, timeout=15)
    admin_h = login(c, "admin")
    cg = branches(c, admin_h)["CG"]
    tbl = tables(c, admin_h, cg["id"])
    qr = tbl[4]["qr_token"]
    m = menu(c, cg["id"])
    bar_h = login(c, "pc1_cg")

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")

        # ---------- Nhân viên: đăng nhập ----------
        lp = browser.new_context(viewport={"width": 1366, "height": 768}, locale="vi-VN").new_page()
        lp.goto(f"{BASE}/admin/login")
        lp.get_by_label("Tên đăng nhập").fill("pc1_cg")
        shot(lp, "N01_dang_nhap")

        # Màn hình Bar mở sẵn để nhận đơn
        bar = staff_page(browser, "pc1_cg")
        expect(bar.get_by_test_id("bar-connection")).to_have_text("● Trực tuyến", timeout=8000)

        # ---------- Khách ẩn danh ----------
        phone = browser.new_context(**PHONE).new_page()
        order = {}

        def khach():
            phone.goto(f"{BASE}/t/{qr}")
            phone.get_by_role("button", name="Xem menu ngay").wait_for()
            shot(phone, "K01_man_hinh_chao")
            phone.get_by_role("button", name="Xem menu ngay").click()
            phone.get_by_test_id("rec-block").wait_for(timeout=5000)
            phone.wait_for_timeout(500)
            shot(phone, "K02_menu_goi_y", full=False)
            shot(phone, "K03_menu_day_du")
            phone.get_by_role("button", name="Thêm Cà phê sữa đá", exact=True).click()
            phone.get_by_role("button", name="Thêm Trà đào cam sả", exact=True).click()
            phone.get_by_role("link", name=re.compile(r"Giỏ hàng \(2\)")).click()
            phone.get_by_role("heading", name="Giỏ hàng").wait_for()
            phone.get_by_label("Ghi chú Cà phê sữa đá").fill("Ít đá")
            phone.wait_for_timeout(600)
            shot(phone, "K04_gio_hang")
            phone.get_by_role("button", name="Thanh toán & gửi đơn").click()
            phone.get_by_text("✔ Thanh toán thành công").wait_for(timeout=10000)
            phone.wait_for_timeout(500)
            shot(phone, "K05_theo_doi_don_dang_cho")
            order["code"] = phone.locator("h1").first.inner_text().split("#")[-1].strip()
        step("khách ẩn danh", khach)

        # ---------- Pha chế ----------
        def pha_che():
            expect(bar.get_by_role("cell", name=order["code"], exact=True).first).to_be_visible(timeout=4000)
            for o in [(m["Bạc xỉu"], 1), (m["Cà phê đen đá"], 2)]:
                place_order(c, tbl[7]["qr_token"], [o])
            bar.wait_for_timeout(1200)
            shot(bar, "N02_bar_hang_doi")
            t = tbl[4]["table_number"]
            bar.get_by_role("button", name=f"Bắt đầu Cà phê sữa đá bàn {t}").first.click()
            bar.get_by_role("button", name=f"Bắt đầu Trà đào cam sả bàn {t}").first.click()
            bar.wait_for_timeout(600)
            shot(bar, "N03_bar_dang_pha")
            phone.wait_for_timeout(300)
            shot(phone, "K06_theo_doi_don_dang_pha")
            bar.get_by_role("button", name=f"Xong Cà phê sữa đá bàn {t}").first.click()
            bar.wait_for_timeout(500)
            bar.get_by_role("button", name=f"Xong Trà đào cam sả bàn {t}").first.click()
            bar.get_by_role("button", name=f"Đã giao {order['code']}").wait_for(timeout=4000)
            bar.wait_for_timeout(400)
            shot(bar, "N04_bar_co_the_lay_hoan_tac")
            phone.get_by_text("Đồ uống đã sẵn sàng").wait_for(timeout=4000)
            shot(phone, "K07_do_uong_san_sang")
            bar.get_by_role("button", name=f"Đã giao {order['code']}").click()
            phone.get_by_text("Bạn đã nhận đồ").wait_for(timeout=4000)
        step("pha chế", pha_che)

        # ---------- Khách thành viên ----------
        mem = browser.new_context(**PHONE).new_page()

        def thanh_vien():
            mem.goto(f"{BASE}/t/{tbl[5]['qr_token']}")
            mem.get_by_role("button", name="Nhập số điện thoại").click()
            mem.get_by_role("textbox", name="Số điện thoại").fill(DEMO_PHONE)
            shot(mem, "K08_nhap_so_dien_thoai")
            mem.get_by_role("button", name="Gửi mã OTP").click()
            demo = mem.get_by_test_id("demo-code").inner_text()
            mem.get_by_role("textbox", name="Số thứ 1 của mã OTP").click()
            mem.keyboard.type(demo[:4])
            shot(mem, "K09_nhap_ma_otp")
            mem.keyboard.type(demo[4:])
            mem.get_by_role("button", name="Xác nhận").click()
            mem.get_by_test_id("member-bar").wait_for(timeout=5000)
            expect(mem.get_by_test_id("rec-block")).to_contain_text("Bạn hay gọi", timeout=5000)
            mem.wait_for_timeout(500)
            shot(mem, "K10_menu_thanh_vien", full=False)
            mem.get_by_role("button", name="Thêm Cà phê sữa đá", exact=True).click()
            mem.get_by_role("button", name="Thêm Bánh croissant bơ", exact=True).click()
            mem.get_by_role("link", name=re.compile(r"Giỏ hàng \(2\)")).click()
            mem.get_by_test_id("cart-points").wait_for()
            mem.wait_for_timeout(500)
            shot(mem, "K11_gio_hang_thanh_vien")
            mem.get_by_role("button", name="Thanh toán & gửi đơn").click()
            mem.get_by_text("✔ Thanh toán thành công").wait_for(timeout=10000)
            oid = int(re.search(r"/orders/(\d+)", mem.url).group(1))
            finish_order(c, bar_h, oid, cg["id"])
            mem.get_by_test_id("points-earned").wait_for(timeout=5000)
            shot(mem, "K12_duoc_cong_diem")
        step("thành viên", thanh_vien)

        # ---------- Thu ngân ----------
        cashier = staff_page(browser, "tn_cg", (1024, 768))
        third = browser.new_context(**PHONE).new_page()

        def thu_ngan():
            third.goto(f"{BASE}/t/{tbl[6]['qr_token']}")
            third.get_by_role("button", name="Xem menu ngay").click()
            third.get_by_role("button", name="Thêm Trà gừng mật ong", exact=True).click()
            third.get_by_role("link", name="Giỏ hàng (1)").click()
            third.get_by_role("button", name="Thanh toán & gửi đơn").click()
            third.get_by_text("✔ Thanh toán thành công").wait_for(timeout=10000)
            code = third.locator("h1").first.inner_text().split("#")[-1].strip()
            panel = cashier.get_by_role("region", name="Hỗ trợ khách")
            panel.get_by_label("Bàn").fill(tbl[6]["table_number"])
            panel.get_by_role("button", name="Tìm").click()
            panel.locator("li").filter(has_text=code).wait_for(timeout=4000)
            shot(cashier, "N05_thu_ngan_tra_cuu")
            panel.locator("li").filter(has_text=code).get_by_role("button", name=f"Hủy đơn {code}").click()
            dlg = cashier.get_by_role("dialog")
            dlg.get_by_role("button", name="Khách gọi nhầm món").click()
            shot(cashier, "N06_thu_ngan_xac_nhan_huy", full=False)
            dlg.get_by_role("button", name="Xác nhận hủy & hoàn tiền").click()
            expect(panel.get_by_role("status")).to_contain_text(f"Đã hủy đơn {code}")
            third.get_by_text("Đơn đã hủy – đã hoàn tiền").wait_for(timeout=4000)
            shot(third, "K13_don_da_huy_hoan_tien")
        step("thu ngân", thu_ngan)

        # ---------- Quản lý chi nhánh ----------
        ql = staff_page(browser, "ql_cg")

        def quan_ly():
            ql.get_by_text("(so với ngày trước)").wait_for(timeout=8000)
            ql.wait_for_timeout(600)
            shot(ql, "N07_tong_quan_quan_ly")
            nav(ql, "Menu chi nhánh")
            shot(ql, "N08_menu_chi_nhanh", full=False)
            nav(ql, "Bàn & mã QR")
            shot(ql, "N09_ban_va_ma_qr", full=False)
            ql.get_by_role("button", name=f"Xem QR bàn {tbl[0]['table_number']}").click()
            ql.get_by_role("dialog").get_by_role("img").wait_for()
            ql.wait_for_timeout(500)
            shot(ql, "N10_xem_ma_qr", full=False)
            ql.get_by_role("dialog").get_by_role("button", name="Đóng").click()
            nav(ql, "Nhân viên")
            shot(ql, "N11_nhan_vien", full=False)
            nav(ql, "Màn hình Bar")
            ql.get_by_test_id("bar-connection").wait_for()
            ql.wait_for_timeout(600)
            shot(ql, "N12_quan_ly_man_hinh_bar", full=False)
        step("quản lý", quan_ly)

        # ---------- Quản trị viên ----------
        ad = staff_page(browser, "admin")

        def quan_tri():
            ad.get_by_text("(so với ngày trước)").wait_for(timeout=8000)
            ad.wait_for_timeout(800)
            shot(ad, "N13_tong_quan_quan_tri")
            nav(ad, "Chi nhánh")
            shot(ad, "N14_chi_nhanh", full=False)
            nav(ad, "Danh mục")
            shot(ad, "N15_danh_muc", full=False)
            nav(ad, "Món")
            shot(ad, "N16_mon", full=False)
            ad.get_by_role("button", name="+ Thêm món").click()
            dlg = ad.get_by_role("dialog")
            dlg.get_by_label("Tên món").fill("Cà phê dừa")
            dlg.get_by_label("Giá gốc (đ)").fill("45.000")
            ad.wait_for_timeout(300)
            shot(ad, "N17_them_mon", full=False)
            dlg.get_by_role("button", name="Hủy").click()
            nav(ad, "Khuyến mãi")
            shot(ad, "N18_khuyen_mai", full=False)
            ad.get_by_role("button", name="+ Tạo chương trình").click()
            dlg = ad.get_by_role("dialog")
            dlg.get_by_label("Tên chương trình").fill("Giờ vàng trà đào")
            dlg.get_by_label("Chọn món thêm vào chương trình").select_option(label="Trà đào cam sả")
            dlg.get_by_role("button", name="+ Thêm món").click()
            dlg.get_by_label("Giá KM Trà đào cam sả").fill("35000")
            ad.wait_for_timeout(300)
            shot(ad, "N19_tao_khuyen_mai", full=False)
            dlg.get_by_role("button", name="Hủy").click()
            nav(ad, "Nhân viên")
            shot(ad, "N20_nhan_vien_quan_tri", full=False)
        step("quản trị", quan_tri)
        browser.close()

    print("Đã chụp", len(done), "ảnh:", ", ".join(done))
    print("Lỗi:", failed or "không")


if __name__ == "__main__":
    main()
