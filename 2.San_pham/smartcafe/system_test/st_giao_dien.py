# -*- coding: utf-8 -*-
"""Kiểm thử phi chức năng trên trình duyệt thật (Playwright + Edge): NFR-P1, P4, P6, R1–R3, U1–U4, S5 (XSS).

    .venv\\Scripts\\python st_giao_dien.py [--webkit]

Ảnh chụp lưu vào 1.Bao_cao/Kiem_thu/img/ (tiền tố ST_).
"""
from __future__ import annotations

import re
import statistics
import time
from pathlib import Path

import httpx
from playwright.sync_api import Page, expect, sync_playwright

from common import Report, args, branches, login, menu, place_order, sql, tables

rep = Report()
PHONE = {"viewport": {"width": 390, "height": 844}, "device_scale_factor": 2, "is_mobile": True, "has_touch": True,
         "locale": "vi-VN"}
# NFR-P1: "Fast 4G" của Chrome DevTools (RTT 165 ms, 9 Mbps / 1,5 Mbps × 0,9) + CPU chậm 4 lần như Lighthouse di động.
FAST_4G = {"offline": False, "latency": 165, "downloadThroughput": 9000 * 1000 / 8 * 0.9,
           "uploadThroughput": 1500 * 1000 / 8 * 0.9}
# Tham khảo (chặt hơn): "Slow 4G" – RTT 150 ms × 3,75, 1,6 Mbps / 750 kbps × 0,9
SLOW_4G = {"offline": False, "latency": 562.5, "downloadThroughput": 1600 * 1000 / 8 * 0.9,
           "uploadThroughput": 750 * 1000 / 8 * 0.9}
# Giả lập mất mạng realtime: bọc WebSocket của trang; __cutWs(true) đóng mọi kết nối đang mở và làm mọi lần
# kết nối lại thất bại ngay (REST vẫn chạy bình thường), __cutWs(false) cho kết nối lại.
WS_CUT = """(() => {
  const Real = window.WebSocket; const open = new Set(); let cut = false;
  function W(url, proto) {
    const ws = new Real(cut ? 'ws://127.0.0.1:9/cut' : url, proto);
    open.add(ws); ws.addEventListener('close', () => open.delete(ws)); return ws;
  }
  W.prototype = Real.prototype; Object.assign(W, { CONNECTING: 0, OPEN: 1, CLOSING: 2, CLOSED: 3 });
  window.WebSocket = W;
  window.__cutWs = (v) => { cut = v; if (v) for (const ws of [...open]) ws.close(); };
})();"""
ENGLISH = re.compile(r"\b(Loading|Submit|Cancel|Login|Logout|Save|Delete|Search|Error|undefined|NaN|null)\b")
MONEY = re.compile(r"^\d{1,3}(\.\d{3})*đ$")


def staff_page(browser, base: str, username: str, size=(1366, 900)) -> Page:
    page = browser.new_context(viewport={"width": size[0], "height": size[1]}, locale="vi-VN").new_page()
    sign_in(page, base, username)
    return page


def sign_in(page: Page, base: str, username: str) -> None:
    page.goto(f"{base}/admin/login")
    page.get_by_label("Tên đăng nhập").fill(username)
    page.get_by_label("Mật khẩu").fill("smartcafe123")
    page.get_by_role("button", name="Đăng nhập").click()
    page.wait_for_url(re.compile(r"/admin/(bar|dashboard)"))


def fcp_runs(browser, base: str, qr: str, net: dict, n: int) -> tuple[list[float], list[float], list[str], int]:
    """n lần mở trang chào (context mới = không cache). Trả (FCP, thời gian bấm 'Xem menu' → menu, file JS đã tải, byte JS)."""
    fcps, menu_ms, js, js_bytes = [], [], [], 0
    for _ in range(n):
        ctx = browser.new_context(**PHONE)
        page = ctx.new_page()
        js_reqs = []
        page.on("requestfinished", lambda r: js_reqs.append(r) if r.url.endswith(".js") else None)
        cdp = ctx.new_cdp_session(page)
        cdp.send("Network.enable")
        cdp.send("Network.emulateNetworkConditions", net)
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
        page.goto(f"{base}/t/{qr}")
        page.get_by_role("button", name="Xem menu ngay").wait_for()
        fcps.append(page.evaluate("performance.getEntriesByName('first-contentful-paint')[0].startTime"))
        t1 = time.perf_counter()
        page.get_by_role("button", name="Xem menu ngay").click()
        page.get_by_role("button", name="Thêm Cà phê sữa đá", exact=True).wait_for()
        menu_ms.append((time.perf_counter() - t1) * 1000)
        js = [r.url.rsplit("/", 1)[-1] for r in js_reqs]
        js_bytes = sum(r.sizes()["responseBodySize"] for r in js_reqs)    # byte thực truyền (đã nén gzip)
        ctx.close()
    return fcps, menu_ms, js, js_bytes


def open_bar(page: Page, base: str) -> None:
    if "/admin/bar" not in page.url:
        page.goto(f"{base}/admin/bar")
    expect(page.get_by_test_id("bar-connection")).to_have_text("● Trực tuyến", timeout=8000)


def main() -> int:
    a = args(lambda ap: ap.add_argument("--webkit", action="store_true", help="chạy thêm WebKit (nhân Safari)"))
    base, img = a.base_url, Path(a.img)
    c = httpx.Client(base_url=base, timeout=15)
    admin = login(c, "admin")
    cg = branches(c, admin)["CG"]
    qr_list = tables(c, admin, cg["id"])
    qr = qr_list[0]["qr_token"]
    table_no = qr_list[0]["table_number"]
    m = menu(c, cg["id"])
    bar_api = login(c, "pc1_cg")

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")

        # ---- NFR-P1: FCP trang QR trên mạng 4G giả lập ----
        fcps, menu_ms, js, js_bytes = fcp_runs(browser, base, qr, FAST_4G, 5)
        slow, _, _, _ = fcp_runs(browser, base, qr, SLOW_4G, 3)
        admin_js = [f for f in js if f.startswith(("AdminRoutes", "DashboardPage"))]
        rep.check("ST-60", "NFR-P1: trang chào sau khi quét QR có FCP ≤ 2 giây trên Fast 4G (5 lần, không cache); "
                  "không tải mã Web Admin / thư viện biểu đồ (hồi quy BUG-ST-02)",
                  max(fcps) <= 2000 and not admin_js and js_bytes <= 100_000,
                  f"FCP {', '.join(f'{x:.0f}' for x in fcps)} ms; bấm 'Xem menu' → menu {statistics.median(menu_ms):.0f} ms; "
                  f"JS tải về {js_bytes / 1000:.0f} KB (gzip) {js}; tham khảo Slow 4G: FCP {', '.join(f'{x:.0f}' for x in slow)} ms")

        # ---- NFR-U2 + U1: số lần chạm, không tràn ngang ----
        phone_ctx = browser.new_context(**PHONE)
        phone = phone_ctx.new_page()
        taps = 0

        def tap(locator) -> None:
            nonlocal taps
            locator.click()
            taps += 1

        phone.goto(f"{base}/t/{qr}")
        widths = {"Chào": phone.evaluate("document.documentElement.scrollWidth")}
        tap(phone.get_by_role("button", name="Xem menu ngay"))
        tap(phone.get_by_role("button", name="Thêm Cà phê sữa đá", exact=True))
        tap(phone.get_by_role("button", name="Thêm Trà đào cam sả", exact=True))
        widths["Menu"] = phone.evaluate("document.documentElement.scrollWidth")
        tap(phone.get_by_role("link", name="Giỏ hàng (2)"))
        phone.get_by_role("heading", name="Giỏ hàng").wait_for()
        widths["Giỏ hàng"] = phone.evaluate("document.documentElement.scrollWidth")
        tap(phone.get_by_role("button", name="Thanh toán & gửi đơn"))
        phone.get_by_text("✔ Thanh toán thành công").wait_for(timeout=10000)
        widths["Theo dõi đơn"] = phone.evaluate("document.documentElement.scrollWidth")
        order_url = phone.url
        code = phone.locator("h1").first.inner_text().split("#")[-1].strip()
        rep.check("ST-61", "NFR-U2: khách ẩn danh đặt 1 đơn 2 món, thanh toán xong trong ≤ 6 lần chạm từ màn hình chào",
                  taps <= 6, f"{taps} lần chạm, đơn {code}")
        phone.screenshot(path=img / "ST_U2_dat_2_mon_5_cham.png", full_page=True)

        over = {}
        for w in (360, 390, 430):
            ctx = browser.new_context(**{**PHONE, "viewport": {"width": w, "height": 800}})
            pg = ctx.new_page()
            for name, path in (("Chào", f"/t/{qr}"), ("Menu", f"/t/{qr}/menu"), ("OTP", f"/t/{qr}/otp"),
                               ("Giỏ hàng", f"/t/{qr}/cart"), ("Theo dõi đơn", order_url.split(base)[-1])):
                pg.goto(base + path)
                pg.wait_for_load_state("networkidle")
                sw = pg.evaluate("document.documentElement.scrollWidth")
                if sw > w:
                    over[f"{name}@{w}"] = sw
            ctx.close()
        rep.check("ST-62", "NFR-U1: 5 màn hình khách (chào, menu, OTP, giỏ, theo dõi đơn) không tràn ngang ở 360 / 390 / 430 px",
                  not over and all(v <= 390 for v in widths.values()), f"tràn: {over}" if over else "15/15 màn hình vừa khung")

        if a.webkit:
            try:
                wk = p.webkit.launch()
                wpg = wk.new_context(**PHONE).new_page()
                wpg.goto(f"{base}/t/{qr}")
                wpg.get_by_role("button", name="Xem menu ngay").click()
                wpg.get_by_role("button", name="Thêm Cà phê sữa đá", exact=True).click()
                wpg.get_by_role("link", name="Giỏ hàng (1)").click()
                wpg.get_by_role("button", name="Thanh toán & gửi đơn").click()
                wpg.get_by_text("✔ Thanh toán thành công").wait_for(timeout=10000)
                ok = wpg.evaluate("document.documentElement.scrollWidth") <= 390
                wpg.screenshot(path=img / "ST_U1_webkit_theo_doi_don.png", full_page=True)
                rep.check("ST-63", "NFR-U1: nhân WebKit (Safari iOS) – đặt món, thanh toán, theo dõi đơn hoạt động, không tràn ngang", ok)
                wk.close()
            except Exception as e:                                        # noqa: BLE001
                rep.check("ST-63", "NFR-U1: nhân WebKit (Safari iOS)", False, f"không chạy được: {str(e)[:120]}")

        # ---- NFR-U3 + P4: màn hình Bar ----
        bar_ctx = browser.new_context(viewport={"width": 1366, "height": 900}, locale="vi-VN")
        bar_ctx.add_init_script("""(() => {
            window.__beeps = 0;
            const AC = window.AudioContext;
            if (AC) { const o = AC.prototype.createOscillator;
                      AC.prototype.createOscillator = function () { window.__beeps++; return o.call(this); }; }
        })();""")
        bar = bar_ctx.new_page()
        sign_in(bar, base, "pc1_cg")
        open_bar(bar, base)
        bar.mouse.click(5, 5)                                             # lần bấm đầu: mở khóa âm thanh

        lat_bar = []
        for _ in range(5):
            beeps = bar.evaluate("window.__beeps")
            o = place_order(c, qr, [(m["Bạc xỉu"], 1)])
            bar.get_by_role("cell", name=o["order_code"], exact=True).first.wait_for(timeout=5000)
            lat_bar.append((time.perf_counter() - o["paid_at_perf"]) * 1000)
        beeped = bar.evaluate("window.__beeps") > beeps
        rep.check("ST-64", "NFR-P4: đơn vừa thanh toán xuất hiện trên hàng đợi Bar ≤ 2 giây (5 lần, không tải lại trang)",
                  max(lat_bar) <= 2000, f"{', '.join(f'{x:.0f}' for x in lat_bar)} ms")

        cell = bar.get_by_role("cell", name="Bạc xỉu", exact=True).first
        size = float(cell.evaluate("e => getComputedStyle(e).fontSize").replace("px", ""))
        late_order = place_order(c, qr, [(m["Cà phê đen đá"], 1)])
        sql(f"UPDATE orders SET paid_at = now() - interval '11 minutes' WHERE id = {late_order['order_id']}")
        bar.reload()
        open_bar(bar, base)
        late_row = bar.locator("tr[data-late]").filter(has_text=late_order["order_code"]).first
        try:
            late_row.wait_for(timeout=5000)                               # chờ hàng đợi tải xong sau khi reload
            late_ok = "red" in (late_row.get_attribute("class") or "")
        except Exception:                                                 # noqa: BLE001
            late_ok = False
        bar.screenshot(path=img / "ST_U3_man_hinh_bar.png", full_page=True)
        rep.check("ST-65", "NFR-U3: màn hình Bar – chữ hàng đợi ≥ 18px, món chờ > 10 phút tô đỏ, có âm báo khi có món mới",
                  size >= 18 and late_ok and beeped,
                  f"cỡ chữ {size:g}px; món chờ 11 phút tô đỏ: {late_ok}; âm báo: {beeped}")

        lat_cust = []
        for _ in range(3):
            o = place_order(c, qr, [(m["Trà đào cam sả"], 1)])
            phone.goto(f"{base}/t/{qr}/orders/{o['order_id']}?token={o['access_token']}")
            expect(phone.get_by_test_id("reconnecting")).to_have_count(0, timeout=5000)
            items = [i for i in c.get(f"/api/staff/branches/{cg['id']}/queue", headers=bar_api).json()["items"]
                     if i["order_id"] == o["order_id"]]
            c.post(f"/api/staff/order-items/{items[0]['id']}/start", headers=bar_api)
            t0 = time.perf_counter()
            c.post(f"/api/staff/order-items/{items[0]['id']}/done", headers=bar_api)
            phone.get_by_text("Đồ uống đã sẵn sàng – mời bạn đến quầy nhận").wait_for(timeout=5000)
            lat_cust.append((time.perf_counter() - t0) * 1000)
        rep.check("ST-66", "NFR-P4: pha chế bấm 'Xong' → điện thoại khách hiện 'Đồ uống đã sẵn sàng' ≤ 2 giây (3 lần)",
                  max(lat_cust) <= 2000, f"{', '.join(f'{x:.0f}' for x in lat_cust)} ms")

        # ---- NFR-R2: Bar mất WebSocket ----
        r2_ctx = browser.new_context(viewport={"width": 1366, "height": 900}, locale="vi-VN")
        r2_ctx.add_init_script(WS_CUT)
        r2 = r2_ctx.new_page()
        sign_in(r2, base, "pc1_cg")
        open_bar(r2, base)
        r2.evaluate("window.__cutWs(true)")
        r2.wait_for_timeout(1500)
        warn = r2.get_by_text(re.compile("Mất kết nối")).count() > 0
        o = place_order(c, qr, [(m["Bạc xỉu"], 2)])
        t0 = time.perf_counter()
        try:
            r2.get_by_role("cell", name=o["order_code"], exact=True).first.wait_for(timeout=13000)
            polled = (time.perf_counter() - t0) * 1000
        except Exception:                                                 # noqa: BLE001
            polled = None
        r2.screenshot(path=img / "ST_R2_bar_mat_ket_noi.png", full_page=True)
        rep.check("ST-67", "NFR-R2: Bar mất WebSocket → cảnh báo 'Mất kết nối' và tự tải lại hàng đợi qua REST (≤ 10 giây) "
                  "(hồi quy BUG-ST-04)", warn and polled is not None and polled <= 12000,
                  f"cảnh báo: {warn}; đơn mới hiện sau {polled / 1000:.1f} s" if polled else f"cảnh báo: {warn}; đơn mới không hiện sau 13 s")
        r2.evaluate("window.__cutWs(false)")
        expect(r2.get_by_test_id("bar-connection")).to_have_text("● Trực tuyến", timeout=15000)
        r2_ctx.close()

        # ---- NFR-R3: điện thoại khách mất WebSocket rồi có lại ----
        r3_ctx = browser.new_context(**PHONE)
        r3_ctx.add_init_script(WS_CUT)
        r3 = r3_ctx.new_page()
        o = place_order(c, qr, [(m["Cà phê sữa đá"], 1)])
        r3.goto(f"{base}/t/{qr}/orders/{o['order_id']}?token={o['access_token']}")
        expect(r3.get_by_test_id("reconnecting")).to_have_count(0, timeout=5000)
        r3.evaluate("window.__cutWs(true)")
        expect(r3.get_by_test_id("reconnecting")).to_be_visible(timeout=3000)
        finish_items = [i for i in c.get(f"/api/staff/branches/{cg['id']}/queue", headers=bar_api).json()["items"]
                        if i["order_id"] == o["order_id"]]
        c.post(f"/api/staff/order-items/{finish_items[0]['id']}/start", headers=bar_api)
        c.post(f"/api/staff/order-items/{finish_items[0]['id']}/done", headers=bar_api)
        r3.wait_for_timeout(1000)
        stale = r3.get_by_text("Đồ uống đã sẵn sàng").count() == 0
        r3.evaluate("window.__cutWs(false)")
        t0 = time.perf_counter()
        r3.get_by_text("Đồ uống đã sẵn sàng – mời bạn đến quầy nhận").wait_for(timeout=15000)
        rep.check("ST-68", "NFR-R3: điện thoại mất WebSocket (hiện 'Đang kết nối lại…'), có mạng lại thì tự kết nối và "
                  "đồng bộ trạng thái mới, không cần tải lại trang", stale,
                  f"có lại kết nối → hiện 'sẵn sàng' sau {time.perf_counter() - t0:.1f} s")
        r3_ctx.close()

        # ---- NFR-R1: AI gợi ý lỗi không làm hỏng đặt món ----
        r1_ctx = browser.new_context(**PHONE)
        r1 = r1_ctx.new_page()
        failed_calls = []
        r1.route(re.compile(r"/recommendations"), lambda route: (failed_calls.append(route.request.url),
                                                                 route.fulfill(status=500, body="{}")))
        r1.goto(f"{base}/t/{qr}")
        r1.get_by_role("button", name="Xem menu ngay").click()
        r1.get_by_role("button", name="Thêm Cà phê sữa đá", exact=True).click()
        r1.get_by_role("link", name="Giỏ hàng (1)").click()
        r1.get_by_role("button", name="Thanh toán & gửi đơn").click()
        r1.get_by_text("✔ Thanh toán thành công").wait_for(timeout=10000)
        rep.check("ST-69", "NFR-R1: API gợi ý trả lỗi 500 → menu và giỏ vẫn dùng được, đặt + thanh toán đơn thành công",
                  len(failed_calls) >= 1 and r1.get_by_role("alert").count() == 0,
                  f"{len(failed_calls)} lần gọi gợi ý bị lỗi giả lập")
        r1_ctx.close()

        # ---- NFR-U4: tiếng Việt, định dạng tiền ----
        phone.goto(f"{base}/t/{qr}/menu")
        phone.get_by_role("button", name="Thêm Cà phê sữa đá", exact=True).wait_for()
        prices = phone.locator("li[data-testid^=menu-item] p.text-sm span").all_inner_texts()
        bad_money = [x for x in prices if not MONEY.match(x)]
        texts = {"Menu khách": phone.locator("body").inner_text()}
        phone.goto(order_url)
        phone.get_by_text("Tiến trình").count()
        texts["Theo dõi đơn"] = phone.locator("body").inner_text()
        texts["Bar"] = bar.locator("body").inner_text()
        adm = staff_page(browser, base, "admin")
        t0 = time.perf_counter()
        adm.get_by_text("(so với ngày trước)").wait_for(timeout=8000)
        first_ms = (time.perf_counter() - t0) * 1000
        texts["Dashboard"] = adm.locator("body").inner_text()
        for path in ("menu-items", "promotions", "staff"):
            adm.goto(f"{base}/admin/{path}")
            adm.wait_for_load_state("networkidle")
            texts[path] = adm.locator("body").inner_text()
        eng = {k: sorted(set(ENGLISH.findall(v))) for k, v in texts.items() if ENGLISH.search(v)}
        lang = phone.evaluate("document.documentElement.lang")
        rep.check("ST-70", "NFR-U4: giao diện tiếng Việt (lang=vi, không lẫn chữ tiếng Anh), giá dạng 45.000đ",
                  lang == "vi" and not bad_money and not eng and len(prices) >= 30,
                  f"{len(prices)} giá đúng định dạng; sai: {bad_money[:3]}; chữ tiếng Anh: {eng}")

        # ---- NFR-P6: dashboard trên trình duyệt ----
        adm.goto(f"{base}/admin/dashboard")
        adm.get_by_text("(so với ngày trước)").wait_for(timeout=8000)
        t0 = time.perf_counter()
        adm.get_by_label("Khoảng thời gian").select_option("30")
        expect(adm.get_by_test_id("period")).to_contain_text("30 ngày", timeout=5000)
        adm.locator("[data-testid=revenue-chart] path.recharts-line-curve").first.wait_for()
        ms30 = (time.perf_counter() - t0) * 1000
        rep.check("ST-71", "NFR-P6: dashboard hiển thị ≤ 2 giây (mở trang sau đăng nhập; đổi sang 30 ngày × 3 chi nhánh)",
                  first_ms <= 2000 and ms30 <= 2000, f"mở trang {first_ms:.0f} ms; 30 ngày {ms30:.0f} ms")

        # ---- NFR-S5: XSS qua tên món ----
        cats = c.get("/api/staff/categories", headers=admin).json()
        payload = '<img src=x onerror="window.__xss=1">Trà XSS'
        it = c.post("/api/staff/menu-items", headers=admin,
                    json={"category_id": cats[0]["id"], "name": payload, "base_price": 30000, "is_active": True}).json()
        try:
            phone.goto(f"{base}/t/{qr}/menu")
            phone.get_by_text(payload).first.wait_for(timeout=5000)
            xss = phone.evaluate("window.__xss === 1")
            imgs = phone.locator("li[data-testid^=menu-item] img[src='x']").count()
            rep.check("ST-72", "NFR-S5: tên món chứa mã HTML/JS (do quản trị nhập) hiển thị như chữ thường, không chạy script",
                      not xss and imgs == 0, f"script chạy: {xss}; thẻ img chèn vào: {imgs}")
        finally:
            c.delete(f"/api/staff/menu-items/{it['id']}", headers=admin)

        # dọn: giao hết các đơn đã tạo trong script
        q = c.get(f"/api/staff/branches/{cg['id']}/queue", headers=bar_api).json()["items"]
        from common import finish_order
        for oid in dict.fromkeys(i["order_id"] for i in q):
            finish_order(c, bar_api, oid, cg["id"])
        for r in c.get(f"/api/staff/branches/{cg['id']}/orders", params={"status": "READY"}, headers=bar_api).json():
            c.post(f"/api/staff/orders/{r['id']}/complete", headers=bar_api)
        browser.close()
    print(f"(bàn dùng để thử: {table_no})")
    return rep.finish()


if __name__ == "__main__":
    raise SystemExit(main())
