# -*- coding: utf-8 -*-
"""Kiểm thử hiệu năng & tải (NFR-P2, P3, P5, P6) trên hệ thống chạy bằng docker compose, đi qua Nginx.

    .venv\\Scripts\\python st_hieu_nang.py [--users 50] [--seconds 60]

- ST-30..32: 50 người dùng ảo đồng thời (mặc định), mỗi vòng: quét QR → xem menu → xem gợi ý → xem đơn,
  nghỉ 3–5 giây giữa các vòng – mô hình tải đã chốt cho NFR-P2/P3 (D39). Đo p95 từng nhóm API.
- ST-38: quá tải tham khảo – cùng 50 người nhưng nghỉ 0,5–1,5 giây (≈ 180 request/giây, vượt sức 1 tiến trình):
  yêu cầu không lỗi, chỉ chậm; p95 ghi lại để tham khảo.
- ST-33..35: 180 đơn trong 1 "giờ" nén lại (60 đơn × 3 chi nhánh, NFR-P5), thêm 1 đợt 20 đơn bấm cùng lúc
  ở 1 chi nhánh để kiểm tra mã đơn không trùng; sau đó pha chế xử lý hết.
- ST-36..37: dashboard 30 ngày × 3 chi nhánh, thời gian job tổng hợp 1 ngày và bù 60 ngày.
"""
from __future__ import annotations

import asyncio
import random
import time
from collections import defaultdict
from datetime import date, timedelta

import httpx

from common import DEMO_PHONE, Report, args, branches, finish_order, login, member_token, menu, p95, \
    backend_py, place_order, tables

rep = Report()


async def virtual_user(ac: httpx.AsyncClient, vu: int, deadline: float, ctx: dict, lat: dict, errors: list) -> None:
    rnd = random.Random(vu)
    b = ctx["branches"][vu % len(ctx["branches"])]
    token = rnd.choice(ctx["tokens"][b["id"]])
    order = ctx["orders"][b["id"]]
    member = ctx["member"] if b["code"] == "CG" and vu % 5 == 0 else None    # 1/5 khách ở CG là thành viên
    ids = ctx["item_ids"][b["id"]]
    await asyncio.sleep(rnd.random())                                          # các VU vào lệch nhau
    while time.perf_counter() < deadline:
        cart = ",".join(map(str, rnd.sample(ids, rnd.randint(0, 2))))
        calls = [
            ("Quét QR", "GET", f"/api/public/tables/{token}", None),
            ("Menu", "GET", f"/api/public/branches/{b['id']}/menu", None),
            ("Gợi ý", "GET", f"/api/public/branches/{b['id']}/recommendations" + (f"?cart={cart}" if cart else ""),
             member),
            ("Xem đơn", "GET", f"/api/public/orders/{order['order_id']}?token={order['access_token']}", None),
        ]
        for name, method, url, headers in calls:
            t0 = time.perf_counter()
            try:
                r = await ac.request(method, url, headers=headers or {})
                ms = (time.perf_counter() - t0) * 1000
                lat[name].append(ms)
                if r.status_code != 200:
                    errors.append(f"{name} {r.status_code}")
            except httpx.HTTPError as e:                                       # timeout / mất kết nối
                errors.append(f"{name} {type(e).__name__}")
        think = ctx.get("think", 4.0)          # D39: nghỉ think ± 1 giây; quá tải (think < 2): think × (0,5–1,5)
        await asyncio.sleep(think - 1 + 2 * rnd.random() if think >= 2 else think * (0.5 + rnd.random()))


async def load_reads(base: str, users: int, seconds: int, ctx: dict) -> tuple[dict, list, int]:
    lat: dict[str, list[float]] = defaultdict(list)
    errors: list[str] = []
    limits = httpx.Limits(max_connections=users + 10, max_keepalive_connections=users + 10)
    async with httpx.AsyncClient(base_url=base, timeout=10, limits=limits) as ac:
        deadline = time.perf_counter() + seconds
        await asyncio.gather(*(virtual_user(ac, i, deadline, ctx, lat, errors) for i in range(users)))
    return lat, errors, sum(len(v) for v in lat.values())


async def order_burst(base: str, qr_tokens: list[str], item: dict, n: int) -> list[httpx.Response]:
    async with httpx.AsyncClient(base_url=base, timeout=15) as ac:
        bodies = [{"qr_token": qr_tokens[i % len(qr_tokens)], "items": [{"menu_item_id": item["id"], "quantity": 1}]}
                  for i in range(n)]
        async def one(b: dict) -> httpx.Response:
            r = await ac.post("/api/public/orders", json=b)
            if r.status_code == 201:
                o = r.json()
                await ac.post(f"/api/public/orders/{o['order_id']}/pay",
                              json={"access_token": o["access_token"], "method": "MOCK_EWALLET"})
            return r

        return await asyncio.gather(*(one(b) for b in bodies))


async def order_hour(base: str, ctx: dict, per_branch: int, seconds: float) -> tuple[list, list[float], list[str]]:
    """Tạo + thanh toán per_branch đơn mỗi chi nhánh, rải đều trong `seconds` giây (1 giờ nén lại)."""
    created: list[dict] = []
    lat: list[float] = []
    errors: list[str] = []
    total = per_branch * len(ctx["branches"])
    gap = seconds / total

    async def one(ac: httpx.AsyncClient, k: int) -> None:
        await asyncio.sleep(k * gap)
        b = ctx["branches"][k % len(ctx["branches"])]
        rnd = random.Random(1000 + k)
        lines = [{"menu_item_id": i, "quantity": rnd.randint(1, 2)} for i in rnd.sample(ctx["item_ids"][b["id"]], rnd.randint(1, 3))]
        t0 = time.perf_counter()
        r = await ac.post("/api/public/orders", json={"qr_token": rnd.choice(ctx["tokens"][b["id"]]), "items": lines})
        if r.status_code != 201:
            errors.append(f"tạo đơn {r.status_code} {r.text[:80]}")
            return
        o = r.json()
        p = await ac.post(f"/api/public/orders/{o['order_id']}/pay", json={"access_token": o["access_token"], "method": "MOCK_CARD"})
        lat.append((time.perf_counter() - t0) * 1000)
        if p.status_code != 200:
            errors.append(f"thanh toán {p.status_code}")
            return
        created.append({**o, "branch_id": b["id"]})

    async with httpx.AsyncClient(base_url=base, timeout=15) as ac:
        await asyncio.gather(*(one(ac, k) for k in range(total)))
    return created, lat, errors


def main() -> int:
    a = args(lambda ap: (ap.add_argument("--users", type=int, default=50), ap.add_argument("--seconds", type=int, default=60),
                         ap.add_argument("--think", type=float, default=4.0, help="giây nghỉ trung bình giữa 2 lượt")))
    c = httpx.Client(base_url=a.base_url, timeout=30)
    admin = login(c, "admin")
    bs = list(branches(c, admin).values())
    ctx = {"branches": bs, "tokens": {}, "item_ids": {}, "orders": {}}
    for b in bs:
        ctx["tokens"][b["id"]] = [t["qr_token"] for t in tables(c, admin, b["id"])]
        m = menu(c, b["id"])
        ctx["item_ids"][b["id"]] = [i["id"] for i in m.values() if i["is_available"]]
        ctx["orders"][b["id"]] = place_order(c, ctx["tokens"][b["id"]][0], [(next(iter(m.values())), 1)])
    ctx["member"] = member_token(DEMO_PHONE)
    ctx["think"] = a.think

    # ---- NFR-P2 / P3: 50 người dùng đồng thời ----
    print(f"Chạy {a.users} người dùng ảo trong {a.seconds} giây, nghỉ {a.think - 1:g}–{a.think + 1:g} giây/lượt...", flush=True)
    t0 = time.perf_counter()
    lat, errors, n = asyncio.run(load_reads(a.base_url, a.users, a.seconds, ctx))
    dur = time.perf_counter() - t0
    reads = lat["Quét QR"] + lat["Menu"] + lat["Xem đơn"]
    detail = ", ".join(f"{k} p95 {p95(v):.0f} ms (n={len(v)})" for k, v in lat.items())
    print("   " + detail)
    rep.check("ST-30", f"{a.users} người dùng đồng thời (nghỉ {a.think - 1:g}–{a.think + 1:g} giây/lượt): không lỗi (mọi request trả 200)",
              not errors,
              f"{n} request trong {dur:.0f} s ≈ {n / dur:.0f} req/s; lỗi: {len(errors)} {errors[:3]}")
    rep.check("ST-31", "NFR-P2: API đọc (quét QR, menu, xem đơn) p95 ≤ 300 ms", p95(reads) <= 300,
              f"p95 {p95(reads):.0f} ms, max {max(reads):.0f} ms")
    rep.check("ST-32", "NFR-P3: API gợi ý món (ẩn danh + thành viên, có/không giỏ hàng) p95 ≤ 500 ms",
              p95(lat["Gợi ý"]) <= 500, f"p95 {p95(lat['Gợi ý']):.0f} ms, max {max(lat['Gợi ý']):.0f} ms")

    # ---- Quá tải tham khảo: nghỉ 0,5–1,5 giây ----
    print(f"Quá tải tham khảo: {a.users} người dùng, nghỉ 0,5–1,5 giây/lượt, {a.seconds} giây...", flush=True)
    ctx_over = {**ctx, "think": 1.0}
    t0 = time.perf_counter()
    lat2, err2, n2 = asyncio.run(load_reads(a.base_url, a.users, a.seconds, ctx_over))
    dur2 = time.perf_counter() - t0
    reads2 = lat2["Quét QR"] + lat2["Menu"] + lat2["Xem đơn"]
    rep.check("ST-38", f"Quá tải tham khảo ({a.users} người, nghỉ 0,5–1,5 giây ≈ gấp 3,5 lần tải chuẩn): không lỗi, không rớt kết nối "
              "(chỉ chậm hơn)", not err2,
              f"{n2} request ≈ {n2 / dur2:.0f} req/s; p95 đọc {p95(reads2):.0f} ms, gợi ý {p95(lat2['Gợi ý']):.0f} ms; lỗi {len(err2)}")

    # ---- NFR-P5: 60 đơn/giờ/chi nhánh × 3 ----
    cg = next(b for b in bs if b["code"] == "CG")
    burst = asyncio.run(order_burst(a.base_url, ctx["tokens"][cg["id"]], menu(c, cg["id"])["Cà phê sữa đá"], 20))
    codes = [r.json()["order_code"] for r in burst if r.status_code == 201]
    rep.check("ST-33", "20 khách cùng bấm đặt món 1 lúc ở 1 chi nhánh: cả 20 đơn tạo được, mã đơn không trùng",
              len(codes) == 20 and len(set(codes)) == 20, f"{len(codes)} đơn, {len(set(codes))} mã khác nhau "
              f"({min(codes, default='')} … {max(codes, default='')}); mã lỗi: {sorted({r.status_code for r in burst} - {201})}")

    print("Tạo 180 đơn (60 đơn/chi nhánh) rải trong 60 giây...", flush=True)
    created, olat, oerr = asyncio.run(order_hour(a.base_url, ctx, 60, 60))
    per = defaultdict(int)
    for o in created:
        per[o["branch_id"]] += 1
    rep.check("ST-34", "NFR-P5: 180 đơn (60/chi nhánh × 3) tạo + thanh toán thành công, p95 tạo+trả ≤ 1 giây",
              len(created) == 180 and not oerr and p95(olat) <= 1000,
              f"{len(created)} đơn {dict((b['code'], per[b['id']]) for b in bs)}, p95 {p95(olat):.0f} ms; lỗi {oerr[:3]}")

    t0 = time.perf_counter()
    bars = {b["id"]: login(c, f"pc1_{b['code'].lower()}") for b in bs}
    queues = {b["id"]: c.get(f"/api/staff/branches/{b['id']}/queue", headers=bars[b["id"]]).json()["items"] for b in bs}
    in_queue = {o["order_id"] for q in queues.values() for o in q}
    missing = [o["order_code"] for o in created if o["order_id"] not in in_queue]
    done = 0
    for bid, q in queues.items():                      # xử lý mọi đơn đang chờ (gồm cả đơn đợt 20 + đơn mẫu)
        for oid in dict.fromkeys(i["order_id"] for i in q):
            finish_order(c, bars[bid], oid, bid)
            done += 1
    left = sum(len(c.get(f"/api/staff/branches/{b['id']}/queue", headers=bars[b["id"]]).json()["items"]) for b in bs)
    rep.check("ST-35", "Hàng đợi Bar có đủ mọi đơn đã thanh toán; pha chế xử lý hết (Bắt đầu → Xong → Đã giao) "
              "thì hàng đợi trống", not missing and left == 0,
              f"thiếu {missing[:5]}; còn {left} món; xử lý {done} đơn trong {time.perf_counter() - t0:.0f} s")

    # ---- NFR-P6: dashboard + job tổng hợp ----
    to = date.today() - timedelta(days=1)
    times = []
    for _ in range(20):
        t1 = time.perf_counter()
        r = c.get("/api/staff/reports/daily", params={"from": str(to - timedelta(days=29)), "to": str(to)}, headers=admin)
        times.append((time.perf_counter() - t1) * 1000)
    rep.check("ST-36", "NFR-P6: API dashboard 30 ngày × 3 chi nhánh p95 ≤ 2 giây (20 lần)",
              r.status_code == 200 and len(r.json()["series"]) == 90 and p95(times) <= 2000,
              f"p95 {p95(times):.0f} ms, {len(r.json()['series'])} điểm dữ liệu")
    t1 = time.perf_counter()
    rb = c.post("/api/staff/reports/daily/rebuild", json={"date": str(to)}, headers=admin)
    one_day = time.perf_counter() - t1
    out = backend_py(
        "import time\n"
        "from datetime import date, timedelta\n"
        "from app.core.db import SessionLocal\n"
        "from app.modules.report.service import build_day\n"
        "db = SessionLocal(); t = time.perf_counter(); d = date.today()\n"
        "n = sum(build_day(db, d - timedelta(days=k)) for k in range(1, 61))\n"
        "print(n, round(time.perf_counter() - t, 2)); db.rollback(); db.close()\n")
    rows, secs = out.split()
    rep.check("ST-37", "NFR-P6: job tổng hợp 1 ngày (3 chi nhánh) ≤ 1 phút; tính lại cả 60 ngày cũng ≤ 1 phút",
              rb.status_code == 200 and one_day <= 60 and float(secs) <= 60,
              f"1 ngày: {one_day * 1000:.0f} ms (qua API); 60 ngày × 3 chi nhánh = {rows} dòng: {secs} s (chạy thử rồi rollback)")
    return rep.finish()


if __name__ == "__main__":
    raise SystemExit(main())
