# SmartCafe – Đồ án Quản lý dự án phần mềm, Nhóm 8 (PTIT)

## Dự án là gì
**SmartCafe** là phần mềm quản lý chuỗi quán cà phê thông minh, tích hợp AI và QR, cho chuỗi 3 chi nhánh (Cầu Giấy, Hà Đông, Thanh Xuân).

- **Khách hàng** quét mã QR tại bàn để xem menu, gọi món và thanh toán (giả lập). Sau khi quét, khách chọn gọi món **ẩn danh**, hoặc **nhập số điện thoại + OTP** (giả lập) để **tích điểm** (1 điểm / 10.000đ).
- **AI gợi ý món**: khách ẩn danh được gợi ý theo món bán chạy, khuyến mãi, món mới; khách thành viên được gợi ý theo sở thích; có thêm "thường gọi kèm" (FP-Growth) và yếu tố thời tiết.
- **Pha chế** làm theo hàng đợi trên **màn hình Bar** (sắp theo giờ gọi), bấm Bắt đầu / Xong / Đã giao. **Thu ngân** chỉ hỗ trợ khách (tra cứu, hủy đơn & hoàn tiền).
- **Quản trị**: menu chung toàn chuỗi + giá riêng / hết hàng theo chi nhánh, khuyến mãi, nhân viên, bàn & mã QR, **dashboard bán hàng** tự tổng hợp hằng ngày.
- **Công nghệ**: Python FastAPI · React (Vite) · PostgreSQL 16 · WebSocket · Docker Compose.

Thời gian thực hiện: 21/09/2026 → 21/12/2026. Nhân sự: A (PM, BA) · B (Backend) · C (AI) · D (Tester/QA) · E (Frontend).

## Đang ở giai đoạn nào (cập nhật 03/11/2026)
| Giai đoạn | Trạng thái |
|:---|:---|
| Khởi tạo, xác định phạm vi | ✔ Xong |
| Phân tích & thiết kế hệ thống (II–IV: quy trình, công nghệ, use case, sequence, CSDL 18 bảng, giao diện, kiến trúc & API) | ✔ Xong |
| Lập trình (V) – theo 9 luồng F0 → F8 | ✔ Xong (03/11) |
| ├ F0 Nền tảng (Docker Compose, CSDL, dữ liệu mẫu, đăng nhập nhân viên, phân quyền) | ✔ Xong, đã kiểm thử – Đạt |
| ├ F1 Quét QR → màn hình chào → menu chi nhánh | ✔ Xong, đã kiểm thử – Đạt |
| ├ F2 Đặt món → thanh toán giả lập → theo dõi đơn | ✔ Xong, đã kiểm thử – Đạt |
| ├ F3 Màn hình Bar (hàng đợi pha chế, giao đồ, cộng điểm) | ✔ Xong, đã kiểm thử – Đạt |
| ├ F4 Khách thành viên: OTP giả lập, tích điểm, xem điểm | ✔ Xong, đã kiểm thử – Đạt |
| ├ F5 Thu ngân hỗ trợ khách: tra cứu, hủy đơn & hoàn tiền | ✔ Xong, đã kiểm thử – Đạt |
| ├ F6 Quản trị: danh mục, món, chi nhánh, nhân viên, menu chi nhánh, bàn & QR, khuyến mãi | ✔ Xong, đã kiểm thử – Đạt |
| ├ F7 AI gợi ý món (2 chế độ + "thường gọi kèm") | ✔ Xong, đã kiểm thử – Đạt |
| └ F8 Báo cáo ngày & dashboard bán hàng | ✔ Xong, đã kiểm thử – Đạt |
| Kiểm thử hệ thống (VI) – kịch bản xuyên luồng + toàn bộ yêu cầu phi chức năng | **Chờ PM duyệt** – [biên bản](1.Bao_cao/Kiem_thu/Bien_ban_kiem_thu_He_thong.md) |
| Hướng dẫn sử dụng, triển khai, nghiệm thu | Chưa làm |

Tiến độ chi tiết từng luồng: [2.San_pham/smartcafe/README.md](2.San_pham/smartcafe/README.md#tiến-độ-theo-luồng-d26--nơi-theo-dõi-chính).

Timeline chi tiết của giai đoạn lập trình đang được PM cập nhật lại.
