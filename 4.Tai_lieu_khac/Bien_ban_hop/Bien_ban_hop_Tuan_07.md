# BIÊN BẢN HỌP TUẦN 07

## 1. THÀNH PHẦN
| Thành viên | Vai trò | Có mặt |
|:---|:---|:---:|
| Thành viên A | PM / Team Lead (chủ trì) | ✔ |
| Thành viên B | Backend Developer | ✔ |
| Thành viên C | AI Specialist | ✔ |
| Thành viên D | Tester / QA, thư ký | ✔ |
| Thành viên E | Frontend Developer | ✔ |

## 2. NGÀY HỌP
Tuần 07 (02/11/2026 – 08/11/2026). Hình thức: họp nhóm. Thư ký: Thành viên D.

## 3. NỘI DUNG
| Mã | Ngày | Nội dung thay đổi / thảo luận | Lý do | Ảnh hưởng (tài liệu, module, người) | Người đề xuất |
|:---|:---|:---|:---|:---|:---|
| CR-26 | 02/11/2026 | Chốt môi trường chạy và demo: chạy **local trên laptop** bằng Docker Desktop (WSL2) + Docker Compose, cài Docker tại `D:\Docker`; giới hạn WSL2 4 GB RAM / 4 nhân. Không dùng Google Colab (không chạy được web server liên tục, không có Docker và URL cố định). Bản dự phòng trên cloud để mở (P12) | Không tốn chi phí, đúng kiến trúc Docker Compose đã chốt; laptop (i5-10210U, 16 GB RAM, SSD) đủ tải demo; ổ C còn ít dung lượng nên đặt Docker ở ổ D | README thiết kế (D24, P12); máy demo của A; B, E dùng chung cấu hình Docker Compose | A |
| CR-27 | 02/11/2026 | Tạm gác vấn đề timeline (P11): không điều chỉnh mốc lập trình lúc này, A sẽ tự hoàn thiện timeline thủ công sau | Ưu tiên bắt đầu code ngay | README thiết kế (P11 → Hoãn); Project_Plan.md, IV.3 Mục 3 (A cập nhật sau) | A |
| CR-28 | 02/11/2026 | Quy trình code: làm **theo từng luồng nghiệp vụ cốt lõi**, mỗi luồng bắt buộc có **test tự động** và **biên bản kiểm thử** đầy đủ trước khi sang luồng tiếp theo | Đảm bảo chất lượng từng phần, có minh chứng kiểm thử cho báo cáo | README thiết kế (D25); B, C, E (viết test), D (biên bản kiểm thử) | A |
| CR-29 | 02/11/2026 | Chốt thứ tự code: **F0** Nền tảng → **F1** QR & menu → **F2** Đặt món & thanh toán → **F3** Màn hình Bar → **F4** OTP & tích điểm → **F5** Thu ngân hỗ trợ → **F6** Quản trị → **F7** AI gợi ý → **F8** Báo cáo & dashboard. Mã nguồn đặt tại `2.San_pham/smartcafe/`, biên bản kiểm thử tại `1.Bao_cao/Kiem_thu/` | Làm trước mạch đầu-cuối chính để sớm có bản demo; luồng sau dùng lại dữ liệu và API của luồng trước | README thiết kế (D26), IV.3 Mục 1.1 (đổi `2.San_pham/source/` → `2.San_pham/smartcafe/`); B, C, E, D | A |
| CR-30 | 02/11/2026 | Dùng kho GitHub `thanhbinh0493/smartcafe` làm nơi lưu trữ và review chung toàn bộ project (tài liệu + mã nguồn) thay cho gửi file nén; thêm `README.md` ở thư mục gốc giới thiệu dự án và giai đoạn hiện tại | Cả nhóm cùng review, có lịch sử thay đổi, luôn dùng bản mới nhất | Toàn bộ thư mục project; `README.md` gốc; cả nhóm | A |
| CR-31 | 02/11/2026 | Chốt P13: chỉ gắn nhãn khuyến mãi khi giá KM **thấp hơn** giá đang bán; nếu không thì bán giá thường và không hiện nhãn KM | Tránh khách hiểu nhầm là đang được giảm giá | README thiết kế (D27), III.1 UC03; biên bản kiểm thử F1 Mục 7; module menu (đã cài ở F1), dashboard F8 (doanh thu KM) | A |
| CR-32 | 02/11/2026 | Sửa cấu trúc bảng `orders`: giữ mã đơn ngắn `CG-0142` (đếm lại mỗi ngày), thêm cột `order_date` và ràng buộc UNIQUE trên 2 cột (order_code, order_date) thay cho UNIQUE trên riêng `order_code` | Phát hiện khi code F2: UC05 đếm lại mã đơn mỗi ngày nhưng schema đặt `order_code` UNIQUE toàn bảng → sang ngày thứ 2 sẽ trùng mã và lỗi | README thiết kế (D28), `schema.sql`, IV.1 (lược đồ + từ điển dữ liệu), ERD (`IV_erd.puml` + PNG), migration `0002`; B | A |
| CR-33 | 03/11/2026 | Chốt P14: **bỏ popup chi tiết món W01a**; bấm "+" trên menu là thêm ngay, số lượng và ghi chú chỉnh trong giỏ hàng W02 | Đạt NFR-U2 (đặt 2 món trong 5 lần chạm; giữ popup thì cần ≥ 7 lần) | README thiết kế (D29), IV.2 (sitemap); biên bản kiểm thử F2 Mục 7; frontend W01, W02 (đã cài ở F2); E | A |
| CR-34 | 03/11/2026 | Chốt P15: pha chế "Hoàn tác" món cuối cùng (đơn đã "Có thể lấy") thì **đơn quay lại "Đang pha chế"** (READY → PREPARING, ghi lịch sử, khách thấy lại "Đang pha"). Duyệt kết quả F3, gộp F2 + F3 vào nhánh `main` (local) và bắt đầu code F4 | Bấm nhầm "Xong" là thao tác hay gặp; nếu không cho hoàn tác thì khách được báo "Có thể lấy" khi đồ chưa pha xong | README thiết kế (D30), III.1 UC18, biểu đồ trạng thái đơn (`III_state_don_hang.puml` + PNG), IV.3; biên bản kiểm thử F3 Mục 7; module bar (đã cài ở F3); B, E | A |
| CR-35 | 03/11/2026 | Chốt P16: **không thu thập tên khách**, thành viên chỉ định danh bằng số điện thoại đã xác thực OTP; bỏ cột `customers.name`, lời chào "Xin chào – X điểm". Duyệt kết quả F4 (84/84 đạt), gộp F4 vào `main` (local) và bắt đầu code F5 – Thu ngân hỗ trợ | Số điện thoại đã đủ để tích điểm và gợi ý món; ít dữ liệu cá nhân hơn (NFR-S7) | README thiết kế (D31, P16), `schema.sql`, IV.1, ERD + sơ đồ data model, SD01, wireframe W01 (`.puml` + PNG), III.1 UC02, III.2, IV.2, IV.3; migration `0003`; module customer, frontend W01; biên bản kiểm thử F4 Mục 7; B, C, E | A |

## 4. HÌNH ẢNH / VIDEOS
(Bổ sung ảnh chụp buổi họp nếu có.)

## 5. KẾT LUẬN
**Quyết định:**
- Thông qua CR-26: môi trường demo là Docker Desktop trên laptop, cài tại `D:\Docker` (D24).
- Thông qua CR-27: tạm gác P11, A tự hoàn thiện timeline thủ công.
- Thông qua CR-28: code theo từng luồng cốt lõi, mỗi luồng có test tự động + biên bản kiểm thử (D25).
- Thông qua CR-29: thứ tự luồng F0 → F8, vị trí mã nguồn và biên bản kiểm thử (D26).
- Thông qua CR-30: dùng kho GitHub chung cho toàn bộ project.
- Thông qua CR-31: chỉ gắn nhãn KM khi giá KM thấp hơn giá đang bán (D27).
- Thông qua CR-32: mã đơn ngắn + UNIQUE (order_code, order_date) (D28).
- Thông qua CR-33: bỏ popup W01a, chỉnh số lượng và ghi chú trong giỏ hàng (D29).
- Thông qua CR-34: hoàn tác món cuối đưa đơn từ "Có thể lấy" về "Đang pha chế" (D30); F3 được duyệt, gộp F2 + F3 vào `main`, chuyển sang F4.
- Thông qua CR-35: không thu thập tên khách, chỉ dùng SĐT (D31); F4 được duyệt, gộp vào `main`, chuyển sang F5.
- Code tiếp các luồng F3 → F8 trên máy, chưa đẩy lên GitHub cho tới khi PM yêu cầu.
- Vấn đề còn mở: P12 (bản demo dự phòng trên cloud).

**Việc cần làm:**
| Việc | Người phụ trách | Hạn |
|:---|:---|:---|
| Khởi động lại máy, cập nhật WSL, chạy thử Docker (`hello-world`) | A | 03/11/2026 |
| Các thành viên tự cài Docker Desktop trên máy mình để phát triển | B, C, E | 05/11/2026 |
| Chốt P12 (có làm bản demo dự phòng trên cloud không) | A | 08/11/2026 |
| Cập nhật timeline thủ công (Project_Plan.md, IV.3 Mục 3) | A | Chưa ấn định |
| Code F0 (nền tảng) + F1 (QR & menu) kèm test và biên bản kiểm thử | B, E (D lập biên bản) | 08/11/2026 |
| Review biên bản kiểm thử F0, F1 trước khi sang F2 | A, D | 08/11/2026 |
| Đẩy project lên GitHub, mời các thành viên vào kho | A | 03/11/2026 |
| Clone kho, chạy thử theo README mã nguồn, review tài liệu + code | B, C, D, E | 08/11/2026 |
| Code F2 (đặt món & thanh toán giả lập) kèm test + biên bản kiểm thử | B, E (D lập biên bản) | 08/11/2026 |
| Code F3 (màn hình Bar) kèm test + biên bản kiểm thử | B, E (D lập biên bản) | 08/11/2026 |
| Chốt P15 (hoàn tác món cuối) – đã xong (CR-34) | A | 03/11/2026 |
| Code F4 (OTP giả lập & tích điểm) kèm test + biên bản kiểm thử – đã xong, duyệt (CR-35) | C, B, E (D lập biên bản) | 03/11/2026 |
| Code F5 (thu ngân tra cứu, hủy đơn & hoàn tiền giả lập) kèm test + biên bản kiểm thử | B, E (D lập biên bản) | 08/11/2026 |
