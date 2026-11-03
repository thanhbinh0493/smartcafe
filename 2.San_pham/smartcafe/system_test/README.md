# Kiểm thử hệ thống (giai đoạn VI)

Bộ script kiểm thử **toàn hệ thống đang chạy bằng `docker compose`**, đi qua Nginx (`http://localhost:8080`) như người dùng thật. Biên bản: [1.Bao_cao/Kiem_thu/Bien_ban_kiem_thu_He_thong.md](../../../1.Bao_cao/Kiem_thu/Bien_ban_kiem_thu_He_thong.md), kế hoạch: [Ke_hoach_kiem_thu_He_thong.md](../../../1.Bao_cao/Kiem_thu/Ke_hoach_kiem_thu_He_thong.md).

| Script | Mã TC | Nội dung |
|:---|:---|:---|
| `st_kich_ban.py` | ST-01…10 | Kịch bản "một ngày làm việc" xuyên F1 → F8 trên 5 thiết bị cùng lúc (khách ẩn danh, khách thành viên, Bar, thu ngân, quản lý / quản trị) + đối soát báo cáo |
| `st_hieu_nang.py` | ST-30…37 | 50 người dùng đồng thời (NFR-P2, P3), 180 đơn/giờ + 20 đơn cùng lúc (NFR-P5), dashboard & job báo cáo (NFR-P6) |
| `st_bao_mat.py` | ST-40…54 | bcrypt, JWT, ma trận RBAC, WebSocket, token ≥ 128 bit, OTP, SQL injection, dữ liệu sai, giá giả, dữ liệu cá nhân (NFR-S1…S7) |
| `st_giao_dien.py` | ST-60…72 | FCP 4G, số lần chạm, 360–430 px, WebKit, độ trễ realtime, màn hình Bar, mất WebSocket, AI lỗi, tiếng Việt, dashboard, XSS (NFR-P1, P4, P6, R1–R3, U1–U4, S5) |
| `st_van_hanh.py` | ST-80…84 | Swagger, Alembic, sao lưu + khôi phục, interface SMS / thanh toán, docker compose + `.env.example` (NFR-R5, M1, M2, M4, M5) |
| `don_dep.py` | – | Dọn dữ liệu tạm nếu một lần chạy bị dừng giữa chừng |

## Cách chạy
```powershell
cd 2.San_pham\smartcafe
docker compose down -v; docker compose up -d --build      # CSDL sạch (tự nạp dữ liệu mẫu + lịch sử)
py -3.11 -m venv system_test\.venv
system_test\.venv\Scripts\pip install -r system_test\requirements.txt
system_test\.venv\Scripts\python -m playwright install webkit   # tùy chọn: kiểm thử nhân Safari (ST-63)
cd system_test
.venv\Scripts\python st_kich_ban.py
.venv\Scripts\python st_bao_mat.py
.venv\Scripts\python st_giao_dien.py --webkit
.venv\Scripts\python st_hieu_nang.py            # --users 50 --seconds 60
.venv\Scripts\python st_van_hanh.py
```
- Cần Microsoft Edge (Playwright dùng `channel="msedge"`) và Docker Desktop (script gọi `docker compose exec` để đọc CSDL).
- SĐT demo `0901000001` chỉ nhận **5 mã OTP / giờ** và gửi lại sau 60 giây (NFR-S4): `st_kich_ban.py` dùng 1 mã; các script khác cấp phiên thành viên trực tiếp hoặc dùng SĐT ngẫu nhiên.
- Script tạo thêm đơn thử vào CSDL demo → trước buổi demo chạy lại `docker compose down -v` rồi `up -d`.

## Sao lưu CSDL trước buổi demo (NFR-R5)
```powershell
powershell -ExecutionPolicy Bypass -File scripts\backup_db.ps1            # → backups\smartcafe_<ngày_giờ>.dump
powershell -ExecutionPolicy Bypass -File scripts\restore_db.ps1 -File backups\smartcafe_<ngày_giờ>.dump
docker compose restart backend
```
