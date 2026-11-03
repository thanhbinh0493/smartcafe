# KIỂM THỬ – SmartCafe

Theo quyết định **D25** (CR-28): mỗi luồng code phải có **test tự động** và **biên bản kiểm thử** trước khi sang luồng tiếp theo. Thứ tự luồng theo **D26** (CR-29).

## 1. Danh sách biên bản
| Luồng | Biên bản | Ngày | Tổng TC | Đạt | Không đạt | Lỗi phát hiện | Kết luận |
|:---|:---|:---|:---:|:---:|:---:|:---:|:---|
| F0 – Nền tảng | [Bien_ban_kiem_thu_F0_Nen_tang.md](Bien_ban_kiem_thu_F0_Nen_tang.md) | 02/11/2026 | 48 | 48 | 0 | 2 (đã sửa) | Đạt |
| F1 – Quét QR & menu | [Bien_ban_kiem_thu_F1_QR_Menu.md](Bien_ban_kiem_thu_F1_QR_Menu.md) | 02/11/2026 | 57 | 57 | 0 | 1 (đã sửa) | Đạt |
| F2 – Đặt món & thanh toán | [Bien_ban_kiem_thu_F2_Dat_mon_Thanh_toan.md](Bien_ban_kiem_thu_F2_Dat_mon_Thanh_toan.md) | 02/11/2026 | 67 | 67 | 0 | 2 (đã sửa) | Đạt |
| F3 – Màn hình Bar | [Bien_ban_kiem_thu_F3_Man_hinh_Bar.md](Bien_ban_kiem_thu_F3_Man_hinh_Bar.md) | 03/11/2026 | 76 | 76 | 0 | 2 (đã sửa) | Đạt |
| F4 – OTP & tích điểm | [Bien_ban_kiem_thu_F4_OTP_Tich_diem.md](Bien_ban_kiem_thu_F4_OTP_Tich_diem.md) | 03/11/2026 | 84 | 84 | 0 | 3 (đã sửa) | Đạt |
| F5 – Thu ngân hỗ trợ khách | [Bien_ban_kiem_thu_F5_Thu_ngan.md](Bien_ban_kiem_thu_F5_Thu_ngan.md) | 03/11/2026 | 53 | 53 | 0 | 1 (đã sửa) | Đạt |
| F6 – Quản trị | [Bien_ban_kiem_thu_F6_Quan_tri.md](Bien_ban_kiem_thu_F6_Quan_tri.md) | 03/11/2026 | 230 | 230 | 0 | 1 (đã sửa) | Đạt |

*Tổng TC = số ca kiểm thử đã chạy (test tự động backend + frontend + kiểm thử khói); mỗi bộ tham số của một test được tính là 1 ca.*

## 2. Quy ước
- **Mã test case:** `F<luồng>-<số>` cho backend (hàm `test_F<luồng>_<số>_...` trong `backend/tests/f<luồng>/`), `F<luồng>-FE-<số>` cho frontend (tên trong `describe/it` của file `*.test.tsx`), `SM-<số>` cho kiểm thử khói (`backend/scripts/smoke_test.py`). Mỗi dòng trong biên bản trỏ tới đúng test tự động tương ứng.
- **Mã lỗi:** `BUG-F<luồng>-<số>`. Mức độ: **Nghiêm trọng** (sai dữ liệu / mất tiền / lộ thông tin), **Cao** (chặn chức năng hoặc chặn chạy hệ thống), **Trung bình** (sai hiển thị / trải nghiệm), **Thấp** (cảnh báo, thẩm mỹ).
- **Cấp độ kiểm thử:** Đơn vị (hàm thuần) · Tích hợp (API + PostgreSQL thật) · Giao diện (component React với API giả lập) · Hệ thống (kiểm thử khói qua Nginx trên bản chạy `docker compose`) · Đầu-cuối trên trình duyệt (`E2E-xx`, Playwright + Edge giả lập điện thoại 390×844, từ F2) · Kiểm tra trực quan (ảnh chụp).
- **Hồi quy:** mỗi luồng mới chạy lại toàn bộ test của các luồng trước và ghi kết quả trong Mục 5 của biên bản.
- **Điều kiện "Đạt" của một luồng:** 100% test case đạt; không còn lỗi mức Nghiêm trọng/Cao chưa sửa; mỗi lỗi đã sửa có test hồi quy.
- **Minh chứng:** log chạy test trong [logs/](logs/), ảnh chụp màn hình trong [img/](img/).

## 3. Mẫu biên bản
Mỗi biên bản gồm: **1.** Thông tin chung · **2.** Phạm vi · **3.** Môi trường & cách chạy · **4.** Danh sách test case · **5.** Tổng hợp kết quả & độ bao phủ · **6.** Lỗi phát hiện · **7.** Tồn tại / hạn chế · **8.** Kết luận & xác nhận.
