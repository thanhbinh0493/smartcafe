# KẾ HOẠCH KIỂM THỬ HỆ THỐNG – SmartCafe (Giai đoạn VI)

## 1. Thông tin chung
| Mục | Nội dung |
|:---|:---|
| Dự án | SmartCafe – Phần mềm quản lý chuỗi quán cà phê thông minh (Tích hợp AI và QR) – Nhóm 8 |
| Giai đoạn | VI – Kiểm thử (Project_Plan: Lập test case, Test ứng dụng / log bug / fix bug) |
| Căn cứ | Use case & sequence (III.1), yêu cầu phi chức năng NFR (III.2), thiết kế CSDL / giao diện / API (IV.1–IV.3), quyết định D1–D39 |
| Đầu vào | 9 luồng F0 → F8 đã "Đạt" và được duyệt (biên bản kiểm thử từng luồng, tổng 727 ca) |
| Quyết định liên quan | CR-41 (bắt đầu giai đoạn VI, test case dạng Markdown), CR-42 / D38 (cache API đọc), CR-43 / D39 (mô hình tải NFR-P2/P3) |
| Người lập | Thành viên D (Tester / QA) – duyệt: Thành viên A (PM) |

## 2. Mục tiêu
1. Chứng minh **các luồng phối hợp đúng với nhau** trên hệ thống thật (không chỉ từng luồng riêng lẻ): dữ liệu do quản trị đổi hiện ngay ở điện thoại khách; đơn của khách đi qua Bar, thu ngân, tích điểm và vào báo cáo ngày đúng số liệu.
2. Kiểm thử **đầy đủ yêu cầu phi chức năng** NFR-P1…P6, S1…S7, R1…R5, U1…U4, M1…M5 bằng phép đo / tấn công thử có thể chạy lại.
3. Phát hiện và sửa lỗi còn sót sau kiểm thử từng luồng; mỗi lỗi sửa xong có test hồi quy.
4. Chạy lại toàn bộ test của F0 → F8 (hồi quy) sau khi sửa.

## 3. Phạm vi
| Trong phạm vi | Ngoài phạm vi |
|:---|:---|
| Toàn bộ hệ thống chạy bằng `docker compose` (db, backend, frontend/Nginx) trên laptop demo (D24), truy cập qua cổng 8080 như người dùng thật | Cổng thanh toán / SMS thật (giả lập theo D12, D16) |
| Kịch bản xuyên luồng UC01–UC20 trên nhiều thiết bị cùng lúc | Điện thoại thật (dùng giả lập điện thoại 390×844 của Playwright; Safari iOS kiểm bằng nhân WebKit) |
| 29 yêu cầu phi chức năng của III.2 | Bản demo dự phòng trên cloud (không làm – D40) |
| Hồi quy: pytest, Vitest, kiểm thử khói SM-01…55 | Kiểm thử bảo mật xâm nhập chuyên sâu (fuzzing, quét lỗ hổng tự động) |

## 4. Chiến lược & cấp độ kiểm thử
| Nhóm | Mã TC | Công cụ | Cách làm |
|:---|:---|:---|:---|
| Kịch bản xuyên luồng | ST-01…10 | Playwright + Edge, 5 trình duyệt cùng lúc | "Một ngày làm việc" ở chi nhánh Cầu Giấy: quản trị tạo KM, quản lý tắt món, khách ẩn danh dùng gợi ý AI, khách thành viên tích điểm, pha chế xử lý, thu ngân hủy & hoàn tiền, đối soát báo cáo ngày |
| Hiệu năng & tải | ST-30…38 | `st_hieu_nang.py` (asyncio + httpx) | 50 người dùng ảo, mỗi người 3–5 giây/thao tác (D39); 180 đơn/giờ + 20 đơn cùng lúc; dashboard + job báo cáo; quá tải tham khảo 0,5–1,5 giây/thao tác |
| Bảo mật | ST-40…55 | `st_bao_mat.py` (httpx, websockets, psql) + pytest | Đọc CSDL để kiểm tra băm mật khẩu / OTP / độ dài token; giả mạo JWT; ma trận RBAC; SQL injection; dữ liệu sai; sửa giá phía client; dữ liệu cá nhân |
| Giao diện & độ tin cậy | ST-60…72 | `st_giao_dien.py` (Playwright: Edge + WebKit, CDP giả lập mạng 4G) | FCP; số lần chạm; khổ 360–430px; độ trễ realtime; màn hình Bar; cắt WebSocket; API gợi ý lỗi; tiếng Việt; XSS |
| Vận hành & bảo trì | ST-80…84 | `st_van_hanh.py` | Swagger, Alembic, sao lưu + khôi phục thử, interface SMS / thanh toán, docker compose + `.env.example` |
| Hồi quy lỗi giai đoạn VI | ST-55, ST-90…95, ST-FE-01…03 | pytest, Vitest | Test tự động cho từng lỗi đã sửa và cho cơ chế cache (D38) |
| Hồi quy F0 → F8 | F0-xx … F8-xx, SM-01…55 | pytest, Vitest, `smoke_test.py` | Chạy lại toàn bộ sau khi sửa lỗi |

## 5. Ma trận truy vết yêu cầu → test case
| Yêu cầu | Test case |
|:---|:---|
| UC01, UC03 (quét QR, menu, cập nhật realtime) | ST-01, ST-02, ST-08, ST-60, ST-62 |
| UC02, UC07 (OTP, tích điểm, xem điểm) | ST-05, ST-06, ST-48–50 |
| UC03 – gợi ý AI, "Thường gọi kèm" | ST-02, ST-03, ST-05, ST-32, ST-69 |
| UC04–UC06 (giỏ, thanh toán, theo dõi đơn) | ST-03, ST-04, ST-61, ST-66, ST-68 |
| UC13, UC15 (menu chi nhánh, khuyến mãi) | ST-01, ST-02, ST-08 |
| UC16 (báo cáo ngày, dashboard) | ST-09, ST-10, ST-36, ST-37, ST-71 |
| UC17–UC19 (Bar) | ST-04, ST-05, ST-35, ST-64, ST-65, ST-67 |
| UC20 (thu ngân hủy & hoàn tiền) | ST-07 |
| NFR-P1 / P2 / P3 / P4 / P5 / P6 | ST-60 / ST-31, ST-38 / ST-32 / ST-64, ST-66 / ST-33–35 / ST-36, ST-37, ST-71 |
| NFR-S1 / S2 / S3 / S4 / S5 / S6 / S7 | ST-40 / ST-41–45, ST-55 / ST-46, ST-47 / ST-48–50 / ST-51, ST-52, ST-72 / ST-53, ST-93 / ST-54 |
| NFR-R1 / R2 / R3 / R4 / R5 | ST-69 / ST-67 / ST-68 / ST-06, ST-33 / ST-82 |
| NFR-U1 / U2 / U3 / U4 | ST-62, ST-63 / ST-61 / ST-65 / ST-70 |
| NFR-M1 / M2 / M3 / M4 / M5 | ST-80 / ST-81 / độ bao phủ pytest (Mục 5 biên bản) / ST-83 / ST-84 |

## 6. Môi trường
- Laptop demo Windows 10, 8 luồng CPU; Docker Desktop (`D:\Docker`), `postgres:16-alpine`, backend 1 tiến trình uvicorn, Nginx.
- Trình duyệt: Microsoft Edge (Chromium) qua Playwright, WebKit của Playwright (nhân Safari).
- Dữ liệu: CSDL sạch (`docker compose down -v` → `up -d --build`): dữ liệu mẫu (3 chi nhánh, 60 bàn, 13 nhân viên, 35 món, 3 KM) + lịch sử `seed_orders` (5.004 đơn / 60 ngày, 300 thành viên, SĐT demo 0901000001) + 180 báo cáo ngày đã bù khi khởi động (D36).
- Máy phát tải chạy chung laptop với hệ thống (kết quả hiệu năng là cận dưới).

## 7. Tiêu chí
| Tiêu chí | Nội dung |
|:---|:---|
| Bắt đầu | F0 → F8 "Đạt" và được duyệt; hệ thống dựng được từ CSDL sạch |
| Tạm dừng | Có lỗi mức Cao chặn kịch bản xuyên luồng → sửa xong mới chạy tiếp |
| Kết thúc ("Đạt") | 100% ST đạt; hồi quy F0 → F8 100% đạt; không còn lỗi Nghiêm trọng / Cao; mỗi lỗi đã sửa có test hồi quy; vấn đề cần PM chốt đã ghi vào bảng Vấn đề mở |

## 8. Phân công & lịch
| Việc | Người thực hiện | Review | Thời gian |
|:---|:---|:---|:---|
| Lập kế hoạch + test case, viết script | D | A | 03/11/2026 |
| Chạy kiểm thử, ghi lỗi | D | A | 03/11/2026 |
| Sửa lỗi backend / frontend + test hồi quy | B, E (C: phần gợi ý) | D | 03/11/2026 |
| Chạy lại toàn bộ (hồi quy) + lập biên bản | D | A | 03/11/2026 |
| PM duyệt kết thúc giai đoạn VI | A | – | trước 08/11/2026 |

*Giai đoạn VI trong Project_Plan dự kiến 26/11 → 02/12/2026; làm sớm vì giai đoạn V đã xong (timeline do A cập nhật – P11).*

## 9. Rủi ro kiểm thử
| Rủi ro | Cách xử lý |
|:---|:---|
| Giới hạn OTP 5 mã/giờ/SĐT làm kịch bản chạy lại bị chặn | Chỉ kịch bản xuyên luồng dùng OTP của SĐT demo; script khác cấp phiên thành viên trực tiếp hoặc dùng SĐT ngẫu nhiên; chờ đủ 60 giây giữa các lần |
| Dữ liệu thử làm bẩn CSDL demo | Mỗi lượt chính thức chạy trên CSDL sạch; `don_dep.py` dọn khi bị dừng giữa chừng; trước demo `docker compose down -v` |
| Máy phát tải chung laptop làm sai lệch số đo | Ghi rõ trong biên bản; số đo là cận dưới của năng lực thật |
