# SmartCafe – Mã nguồn

Phần mềm quản lý chuỗi quán cà phê thông minh (Tích hợp AI và QR) – Nhóm 8, môn Quản lý dự án phần mềm.
Thiết kế: [1.Bao_cao/Thiet_ke_he_thong/](../../1.Bao_cao/Thiet_ke_he_thong/README.md). Biên bản kiểm thử: [1.Bao_cao/Kiem_thu/](../../1.Bao_cao/Kiem_thu/README.md).

| Thành phần | Công nghệ |
|:---|:---|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 16 |
| Frontend | React 18 + Vite + TypeScript, Tailwind CSS 4, React Router 6 |
| Triển khai | Docker Compose (db, backend, frontend/Nginx) |
| Kiểm thử | pytest + pytest-cov (backend, chạy trên PostgreSQL thật), Vitest + Testing Library (frontend) |

## Tiến độ theo luồng (D26) – nơi theo dõi chính
Cập nhật mỗi khi một luồng xong. Kết quả kiểm thử chi tiết ở [1.Bao_cao/Kiem_thu/](../../1.Bao_cao/Kiem_thu/README.md); vấn đề chờ chốt ở bảng "Vấn đề mở" của [README thiết kế](../../1.Bao_cao/Thiet_ke_he_thong/README.md).

| Luồng | Nội dung | Use case / màn hình | Trạng thái | Biên bản kiểm thử |
|:---|:---|:---|:---|:---|
| F0 | Nền tảng: Docker Compose, CSDL (Alembic), dữ liệu mẫu, đăng nhập nhân viên + RBAC | UC08 · A01 | ✔ Đạt (02/11) | [F0](../../1.Bao_cao/Kiem_thu/Bien_ban_kiem_thu_F0_Nen_tang.md) – 48/48 |
| F1 | Quét QR → màn hình chào → menu chi nhánh | UC01, UC03 · W00, W01 | ✔ Đạt (02/11) | [F1](../../1.Bao_cao/Kiem_thu/Bien_ban_kiem_thu_F1_QR_Menu.md) – 57/57 |
| F2 | Giỏ hàng → đặt món → thanh toán giả lập → theo dõi đơn (realtime) | UC04–UC06 · W02, W03 | ✔ Đạt (02/11) | [F2](../../1.Bao_cao/Kiem_thu/Bien_ban_kiem_thu_F2_Dat_mon_Thanh_toan.md) – 67/67 |
| F3 | Màn hình Bar: hàng đợi pha chế, Bắt đầu / Xong / Hoàn tác / Đã giao (cộng điểm) | UC17–UC19 · W04 | ✔ Đạt (03/11) | [F3](../../1.Bao_cao/Kiem_thu/Bien_ban_kiem_thu_F3_Man_hinh_Bar.md) – 76/76 |
| F4 | Khách thành viên: OTP giả lập, tích điểm, xem điểm | UC02, UC07 · W00a | ✔ Đạt (03/11) | [F4](../../1.Bao_cao/Kiem_thu/Bien_ban_kiem_thu_F4_OTP_Tich_diem.md) – 84/84 |
| F5 | Thu ngân hỗ trợ: tra cứu, hủy đơn & hoàn tiền | UC20 · W04 (tra cứu) | ✔ Đạt (03/11) | [F5](../../1.Bao_cao/Kiem_thu/Bien_ban_kiem_thu_F5_Thu_ngan.md) – 53/53 |
| F6 | Quản trị: danh mục, món, chi nhánh, nhân viên, menu chi nhánh, bàn & QR, khuyến mãi | UC09–UC15 · W05–W07, A03–A06 | ✔ Đạt (03/11) | [F6](../../1.Bao_cao/Kiem_thu/Bien_ban_kiem_thu_F6_Quan_tri.md) – 230/230 |
| F7 | AI gợi ý món (2 chế độ) + "Thường gọi kèm" | UC03 (phần gợi ý) | Chưa làm | |
| F8 | Báo cáo ngày (job 00:05) + dashboard | UC16 · W08 | Chưa làm | |

## 1. Chạy toàn bộ hệ thống (demo)
Yêu cầu: Docker Desktop đang chạy.
```powershell
cd 2.San_pham\smartcafe
copy .env.example .env          # lần đầu
docker compose up -d --build    # db + backend + frontend
```
- Web (khách + admin): http://localhost:8080 — tài liệu API (Swagger): http://localhost:8000/docs
- Lần chạy đầu, backend tự tạo bảng (`alembic upgrade head`) và nạp dữ liệu mẫu (chỉ khi CSDL còn trống).
- Lấy link QR của các bàn: `docker compose exec backend python -m scripts.seed_data --print-qr`
- Điện thoại cùng Wi-Fi: thay `localhost` bằng IP LAN của laptop (xem `ipconfig`), VD `http://192.168.1.10:8080/t/<token>`. In link QR kèm IP: thêm `--base-url http://<IP>:8080`.
- **Khách thành viên (F4):** ở màn hình chào chọn "Nhập số điện thoại", nhập SĐT di động bất kỳ (VD `0912 345 678`); mã OTP giả lập hiện ở khung **[DEMO]** (`OTP_DEMO_MODE=true`). Tắt DEMO thì lấy mã trong log: `docker compose logs backend | findstr "Mock SMS"`. Mỗi SĐT gửi lại sau 60 giây, tối đa 5 mã/giờ.
- Xóa sạch dữ liệu để nạp lại: `docker compose down -v` rồi `up -d` lại.

**Tài khoản nhân viên mẫu** (mật khẩu chung `smartcafe123`, đổi bằng `SEED_STAFF_PASSWORD`):

| Vai trò | Tài khoản |
|:---|:---|
| Quản trị viên | `admin` |
| Quản lý chi nhánh | `ql_cg`, `ql_hd`, `ql_tx` |
| Thu ngân | `tn_cg`, `tn_hd`, `tn_tx` |
| Pha chế | `pc1_cg`, `pc2_cg`, `pc1_hd`, … |

Dữ liệu mẫu: 3 chi nhánh (CG Cầu Giấy, HD Hà Đông, TX Thanh Xuân) × 20 bàn; 5 danh mục, 35 món (4 món mới); Hà Đông có giá riêng cho Cà phê sữa đá (27.000đ) và Bạc xỉu (30.000đ); Cầu Giấy tạm hết Bạc xỉu nóng; 3 khuyến mãi (toàn chuỗi "Tuần lễ trà trái cây" đang chạy, riêng Cầu Giấy "Mừng khai trương" đang chạy, "Halloween 2026" đã kết thúc).

## 2. Phát triển trên máy (không đóng gói)
```powershell
docker compose up -d db                         # chỉ chạy PostgreSQL (cổng 5432)

cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\pip install -r requirements-dev.txt
.\.venv\Scripts\alembic upgrade head
.\.venv\Scripts\python -m scripts.seed_data --if-empty
.\.venv\Scripts\uvicorn app.main:app --reload   # http://localhost:8000

cd ..\frontend
npm install
npm run dev                                     # http://localhost:5173 (proxy /api sang 8000)
```

## 3. Chạy kiểm thử
```powershell
# Backend: cần PostgreSQL đang chạy (docker compose up -d db). Test tự tạo CSDL riêng smartcafe_test.
cd backend
.\.venv\Scripts\python -m pytest -v --cov=app --cov=scripts

# Frontend
cd frontend
npm test                # hoặc: npm run test:cov

# Kiểm thử khói trên hệ thống đang chạy (đi qua Nginx cổng 8080)
cd backend
.\.venv\Scripts\python -m scripts.smoke_test --qr-token <token 1 bàn>
```
Quy ước đặt tên test: `test_F<luồng>_<số>_<mô tả>` (backend), `F<luồng>-FE-<số>` (frontend) – trùng mã test case trong biên bản kiểm thử.

## 4. Cấu trúc thư mục
```
backend/
  app/core/        cấu hình, kết nối CSDL, JWT + bcrypt, định dạng lỗi thống nhất
  app/models/      SQLAlchemy models (18 bảng theo schema.sql)
  app/modules/     auth (đăng nhập, RBAC) · branch (tra cứu QR) · menu (giá chi nhánh + KM)
                   order (đặt món, mã đơn theo ngày, theo dõi) · payment (cổng thanh toán giả lập)
                   bar (hàng đợi pha chế, Bắt đầu / Xong / Hoàn tác / Đã giao, cộng điểm, /ws/bar)
                   customer (OTP giả lập + cổng Mock SMS, customer token 1 giờ, xem điểm /me)
                   support (thu ngân tra cứu đơn, hủy & hoàn tiền giả lập)
                   admin (danh mục, món + ảnh, chi nhánh, nhân viên, menu chi nhánh, bàn & ảnh QR, khuyến mãi)
  app/ws/          WebSocket hub (kênh order:{id}, bar:{branch_id})
  alembic/         migration; 0001 chạy nguyên văn schema.sql thiết kế; 0002 mã đơn UNIQUE theo ngày; 0003 bỏ customers.name (D31)
  scripts/         seed_data.py (dữ liệu mẫu), smoke_test.py
  tests/f0 … f6   test theo luồng
frontend/
  src/pages/qr/    W00 màn hình chào, W00a OTP, W01 menu (+ dòng thành viên), W02 giỏ hàng, W03 theo dõi đơn (route /t/:qrToken/...)
  src/auth/        MemberContext (phiên khách thành viên trong sessionStorage, tự hết hạn) · staffSession (phiên nhân viên)
  src/cart/        giỏ hàng (sessionStorage của tab) · src/hooks/useOrderSocket.ts (WebSocket tự kết nối lại)
  src/pages/admin/ A01 đăng nhập, khung Web Admin (route /admin), W04 màn hình quầy Bar (/admin/bar) + khung "Hỗ trợ khách" (SupportPanel); F6: A03–A06, W05–W07 (/admin/branches, staff, categories, menu-items, branch-menu, tables, promotions)
  src/api/         gọi API · src/lib/ định dạng tiền, tìm không dấu
docker-compose.yml · .env.example
```

## 5. Lưu ý kỹ thuật
- `alembic.ini` phải giữ **chỉ ký tự ASCII** (Windows đọc file này bằng bảng mã cp1252).
- Sắp xếp tên món dùng collation ICU `vi-VN-x-icu` vì `postgres:16-alpine` (musl) so sánh `en_US.utf8` theo byte.
- Khách hàng không lưu gì lâu dài trên thiết bị (NFR-S7); phiên nhân viên lưu ở `localStorage` của máy quầy (JWT 8 giờ).
