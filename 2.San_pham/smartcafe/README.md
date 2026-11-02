# SmartCafe – Mã nguồn

Phần mềm quản lý chuỗi quán cà phê thông minh (Tích hợp AI và QR) – Nhóm 8, môn Quản lý dự án phần mềm.
Thiết kế: [1.Bao_cao/Thiet_ke_he_thong/](../../1.Bao_cao/Thiet_ke_he_thong/README.md). Biên bản kiểm thử: [1.Bao_cao/Kiem_thu/](../../1.Bao_cao/Kiem_thu/README.md).

| Thành phần | Công nghệ |
|:---|:---|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 16 |
| Frontend | React 18 + Vite + TypeScript, Tailwind CSS 4, React Router 6 |
| Triển khai | Docker Compose (db, backend, frontend/Nginx) |
| Kiểm thử | pytest + pytest-cov (backend, chạy trên PostgreSQL thật), Vitest + Testing Library (frontend) |

## Tiến độ theo luồng (D26)
| Luồng | Nội dung | Trạng thái |
|:---|:---|:---|
| F0 | Nền tảng: Docker Compose, 18 bảng (Alembic), dữ liệu mẫu, đăng nhập nhân viên + RBAC | ✔ Xong, đã kiểm thử |
| F1 | Quét QR → màn hình chào (W00) → menu chi nhánh (W01) | ✔ Xong, đã kiểm thử |
| F2 | Giỏ hàng → đặt món → thanh toán giả lập → theo dõi đơn | Chưa làm |
| F3 | Màn hình Bar (hàng đợi pha chế, Đã giao) | Chưa làm |
| F4–F8 | OTP & tích điểm, thu ngân, quản trị, AI gợi ý, báo cáo | Chưa làm |

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
  alembic/         migration; 0001 chạy nguyên văn schema.sql thiết kế
  scripts/         seed_data.py (dữ liệu mẫu), smoke_test.py
  tests/f0, f1     test theo luồng
frontend/
  src/pages/qr/    W00 màn hình chào, W01 menu (route /t/:qrToken)
  src/pages/admin/ A01 đăng nhập, khung Web Admin (route /admin)
  src/api/         gọi API · src/lib/ định dạng tiền, tìm không dấu
docker-compose.yml · .env.example
```

## 5. Lưu ý kỹ thuật
- `alembic.ini` phải giữ **chỉ ký tự ASCII** (Windows đọc file này bằng bảng mã cp1252).
- Sắp xếp tên món dùng collation ICU `vi-VN-x-icu` vì `postgres:16-alpine` (musl) so sánh `en_US.utf8` theo byte.
- Khách hàng không lưu gì lâu dài trên thiết bị (NFR-S7); phiên nhân viên lưu ở `localStorage` của máy quầy (JWT 8 giờ).
