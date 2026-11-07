# BIÊN BẢN HỌP TUẦN 05

## 1. THÀNH PHẦN
| Thành viên | Vai trò | Có mặt |
|:---|:---|:---:|
| Nguyễn Thanh Bình (A) | PM / Team Lead (chủ trì) | ✔ |
| Nguyễn Trường Thiên (B) | Backend Developer | ✔ |
| Lê Minh Sơn (C) | AI Specialist | ✔ |
| Ngô Duy Đô (D) | Tester / QA, thư ký | ✔ |
| Nguyễn Quang Tú (E) | Frontend Developer | ✔ |

## 2. NGÀY HỌP
Tuần 05 (19/10/2026 – 25/10/2026). Hình thức: họp nhóm. Thư ký: Ngô Duy Đô (D).

## 3. NỘI DUNG
| Mã | Ngày | Nội dung thay đổi / thảo luận | Lý do | Ảnh hưởng (tài liệu, module, người) | Người đề xuất |
|:---|:---|:---|:---|:---|:---|
| CR-29 | 19/10/2026 | Chốt thứ tự code: **F0** Nền tảng → **F1** QR & menu → **F2** Đặt món & thanh toán → **F3** Màn hình Bar → **F4** OTP & tích điểm → **F5** Thu ngân hỗ trợ → **F6** Quản trị → **F7** AI gợi ý → **F8** Báo cáo & dashboard. Mã nguồn đặt tại `2.San_pham/smartcafe/`, biên bản kiểm thử tại `1.Bao_cao/Kiem_thu/` | Làm trước mạch đầu-cuối chính để sớm có bản demo; luồng sau dùng lại dữ liệu và API của luồng trước | README thiết kế (D26), IV.3 Mục 1.1 (đổi `2.San_pham/source/` → `2.San_pham/smartcafe/`); B, C, E, D | Nguyễn Thanh Bình (A) |
| CR-30 | 19/10/2026 | Dùng kho GitHub `thanhbinh0493/smartcafe` làm nơi lưu trữ và review chung toàn bộ project (tài liệu + mã nguồn) thay cho gửi file nén; thêm `README.md` ở thư mục gốc giới thiệu dự án và giai đoạn hiện tại | Cả nhóm cùng review, có lịch sử thay đổi, luôn dùng bản mới nhất | Toàn bộ thư mục project; `README.md` gốc; cả nhóm | Nguyễn Thanh Bình (A) |
| CR-31 | 23/10/2026 | Chốt P13: chỉ gắn nhãn khuyến mãi khi giá KM **thấp hơn** giá đang bán; nếu không thì bán giá thường và không hiện nhãn KM | Tránh khách hiểu nhầm là đang được giảm giá | README thiết kế (D27), III.1 UC03; biên bản kiểm thử F1 Mục 7; module menu (đã cài ở F1), dashboard F8 (doanh thu KM) | Nguyễn Thanh Bình (A) |
| CR-32 | 24/10/2026 | Sửa cấu trúc bảng `orders`: giữ mã đơn ngắn `CG-0142` (đếm lại mỗi ngày), thêm cột `order_date` và ràng buộc UNIQUE trên 2 cột (order_code, order_date) thay cho UNIQUE trên riêng `order_code` | Phát hiện khi code F2: UC05 đếm lại mã đơn mỗi ngày nhưng schema đặt `order_code` UNIQUE toàn bảng → sang ngày thứ 2 sẽ trùng mã và lỗi | README thiết kế (D28), `schema.sql`, IV.1 (lược đồ + từ điển dữ liệu), ERD (`IV_erd.puml` + PNG), migration `0002`; B | Nguyễn Thanh Bình (A) |
| CR-33 | 25/10/2026 | Chốt P14: **bỏ popup chi tiết món W01a**; bấm "+" trên menu là thêm ngay, số lượng và ghi chú chỉnh trong giỏ hàng W02 | Đạt NFR-U2 (đặt 2 món trong 5 lần chạm; giữ popup thì cần ≥ 7 lần) | README thiết kế (D29), IV.2 (sitemap); biên bản kiểm thử F2 Mục 7; frontend W01, W02 (đã cài ở F2); E | Nguyễn Thanh Bình (A) |

## 4. HÌNH ẢNH / VIDEOS
(Bổ sung ảnh chụp buổi họp nếu có.)

## 5. KẾT LUẬN
**Quyết định:**
- Thông qua CR-29: thứ tự luồng F0 → F8, vị trí mã nguồn và biên bản kiểm thử (D26).
- Thông qua CR-30: dùng kho GitHub chung cho toàn bộ project.
- Thông qua CR-31: chỉ gắn nhãn KM khi giá KM thấp hơn giá đang bán (D27).
- Thông qua CR-32: mã đơn ngắn + UNIQUE (order_code, order_date) (D28).
- Thông qua CR-33: bỏ popup W01a, chỉnh số lượng và ghi chú trong giỏ hàng (D29).

**Việc cần làm:**
| Việc | Người phụ trách | Hạn |
|:---|:---|:---|
| F4 – Khách thành viên: OTP giả lập, tích điểm, xem điểm | Lê Minh Sơn, Nguyễn Trường Thiên, Nguyễn Quang Tú | 28/10/2026 |
| F5 – Thu ngân hỗ trợ khách: tra cứu, hủy đơn & hoàn tiền giả lập | Nguyễn Trường Thiên, Nguyễn Quang Tú | 29/10/2026 |
| F6 – Quản trị: chi nhánh, nhân viên, danh mục, món + ảnh, menu chi nhánh, bàn & mã QR, khuyến mãi | Nguyễn Trường Thiên, Nguyễn Quang Tú | 30/10/2026 |
| F8 – Báo cáo ngày (job 00:05) + dashboard bán hàng | Nguyễn Trường Thiên, Nguyễn Quang Tú | 31/10/2026 |
| Lập kế hoạch kiểm thử hệ thống và test case: kịch bản xuyên luồng F1 → F8, 29 yêu cầu phi chức năng | Ngô Duy Đô | 02/11/2026 |
