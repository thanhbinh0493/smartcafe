# BIÊN BẢN HỌP TUẦN 06

## 1. THÀNH PHẦN
| Thành viên | Vai trò | Có mặt |
|:---|:---|:---:|
| Nguyễn Thanh Bình (A) | PM / Team Lead (chủ trì) | ✔ |
| Nguyễn Trường Thiên (B) | Backend Developer | ✔ |
| Lê Minh Sơn (C) | AI/IoT Specialist | ✔ |
| Ngô Duy Đô (D) | Tester / QA, thư ký | ✔ |
| Nguyễn Quang Tú (E) | Frontend Developer | ✔ |

## 2. NGÀY HỌP
Tuần 06 (26/10/2026 – 01/11/2026). Hình thức: họp nhóm. Thư ký: Ngô Duy Đô (D).

## 3. NỘI DUNG
| Mã | Ngày | Nội dung thay đổi / thảo luận | Lý do | Ảnh hưởng (tài liệu, module, người) | Người đề xuất |
|:---|:---|:---|:---|:---|:---|
| CR-01 | 28/10/2026 | Chốt tính năng AI là **Gợi ý món** (thời tiết + bán chạy + lịch sử khách + luật kết hợp). Bỏ phương án nhận diện khuôn mặt | Tài liệu phạm vi đang để "hoặc"; gợi ý món ít rủi ro, không cần camera, không vướng dữ liệu cá nhân | Pham_Vi_Du_An.md, II.2, module V.3 – C | A |
| CR-02 | 28/10/2026 | Chốt tech stack **Python FastAPI + React + PostgreSQL** | Backend cùng ngôn ngữ với model AI nên dễ tích hợp | II.2, IV.1, IV.3, toàn bộ giai đoạn V – B, C, E | A |
| CR-03 | 28/10/2026 | Menu: **menu chung** do trụ sở quản lý; chi nhánh được đặt giá riêng và bật/tắt hết hàng | Kiểm soát giá toàn chuỗi nhưng vẫn linh hoạt theo chi nhánh | Bảng `branch_menu_items`, UC12, W06 – B, E | A |
| CR-04 | 28/10/2026 | Khách **không bắt buộc tài khoản**, nhập SĐT tùy chọn | Không làm chậm luồng gọi món; SĐT dùng để cá nhân hóa gợi ý | Bảng `customers`, UC06, W02 – B, E | A |
| CR-05 | 28/10/2026 | Thanh toán **trả trước trên web (giả lập)**; đơn chỉ xuống quầy Bar sau khi thanh toán thành công | Phù hợp phạm vi (không tích hợp cổng thật); giảm việc cho thu ngân | Trạng thái đơn, SD02, Mock Payment – B, E | A |
| CR-06 | 28/10/2026 | Khảo sát II.1 làm theo mô hình **giả định điển hình** kèm bộ câu hỏi phỏng vấn | Chưa có quán thực tế để khảo sát | II.1 – D | A |
| CR-07 | 28/10/2026 | Sơ đồ vẽ bằng **PlantUML**, xuất PNG để chèn báo cáo | Quản lý được dạng văn bản, ký hiệu UML chuẩn | Thư mục `diagrams/` – A, D | A |
| CR-08 | 01/11/2026 | Quy định quy trình: **mọi yêu cầu thay đổi được ghi vào biên bản họp tuần** (file `.md`, cuối kỳ xuất `.docx`); tạo CLAUDE.md cho dự án | Đảm bảo truy vết thay đổi, phục vụ mục XI.1 của kế hoạch | CLAUDE.md, thư mục `Bien_ban_hop/` – A, D | A |
| CR-09 | 01/11/2026 | **Bỏ hẳn IoT** (máy pha chế giả lập). Đổi tên đề tài thành "...(Tích hợp AI và QR)". Vấn đề P7 được giải quyết bằng **màn hình hàng đợi pha chế**: hiển thị món, bàn, giờ gọi, ghi chú, **sắp theo thời gian gọi**; pha chế bấm Bắt đầu / Xong | Máy pha có kết nối ít mẫu trên thị trường; khó tùy biến món mới và áp dụng cho toàn bộ chi nhánh; phần lớn đồ uống pha tay | Pham_Vi_Du_An.md, Project_Plan.md (vai trò C, task V.3), II.1, II.2 (Mục 3), III.1 (bỏ 4 UC IoT), III.2, IV.1 (bỏ 3 bảng), IV.2 (W04 vẽ lại), IV.3, schema.sql – B, C, E | A |
| CR-10 | 01/11/2026 | Ngay sau khi quét QR có **màn hình chào 2 lựa chọn**: (1) không nhập SĐT, xem menu ngay; (2) nhập SĐT để tích điểm và nhận gợi ý theo sở thích. **Không lưu thông tin thiết bị** của khách | Thiết kế cũ chỉ nhập SĐT ở bước giỏ hàng nên lúc mở menu không biết khách là ai để gợi ý theo thói quen; khách có thể đổi điện thoại | UC01, SD01, W00, W01 – B, E | A |
| CR-11 | 01/11/2026 | Bổ sung **chương trình khuyến mãi đơn giản**: tên, thời gian, phạm vi toàn chuỗi / 1 chi nhánh, danh sách món + giá KM. Không làm voucher, combo, mua 1 tặng 1 | Gợi ý cho khách ẩn danh cần dựa trên "món đang khuyến mãi" | UC15, SD05, W07, bảng `promotions`, `promotion_items`; giá trong UC03, UC05 – B, E | A |
| CR-12 | 01/11/2026 | Bổ sung **tích điểm** ở mức chỉ tích và xem điểm (cộng khi đơn hoàn tất); chưa làm đổi điểm | Tạo lý do để khách để lại SĐT; giữ phạm vi "không làm tài chính" | UC07, UC19, SD06, bảng `loyalty_transactions`, `customers.loyalty_points` – B, C | A |
| CR-13 | 01/11/2026 | **Xác thực SĐT bằng OTP giả lập** (6 số, hạn 5 phút, tối đa 5 lần sai, giới hạn gửi lại) | Ngăn người khác nhập SĐT của khách để xem sở thích hoặc tích điểm hộ | UC02, SD01, W00a, bảng `otp_requests`, NFR-S4 – B, E | A |
| CR-14 | 01/11/2026 | Gợi ý món theo **2 chế độ**: ẩn danh (bán chạy + KM + món mới) và thành viên (sở thích + món tương tự + bán chạy + KM); **thời tiết giữ làm yếu tố phụ** (10%) | Phù hợp với CR-10; tài liệu phạm vi gốc có nhắc thời tiết | II.2 (Mục 2), SD02, bảng `recommendation_logs.mode` – C | A |
| CR-15 | 01/11/2026 | **Chỉ Quản trị viên** được tạo/sửa chương trình khuyến mãi; Quản lý chi nhánh không tạo KM (chốt P6) | Đơn giản hóa luồng vận hành | UC15, RBAC (III.1), SD05, W06, W07, API `/api/staff/promotions` – B, E | A |
| CR-16 | 01/11/2026 | Tỉ lệ tích điểm **1 điểm / 10.000đ**; **1 điểm = 100đ**, tức hoàn lại 1% cho khách (chốt P7) | Tỉ lệ dễ hiểu, chi phí khuyến khích thấp | UC19, III.2 quy tắc 5, W01 (hiển thị giá trị quy đổi), cấu hình `POINT_VALUE_VND` – C, E | A |
| CR-17 | 01/11/2026 | "Món mới" = món tạo trong **30 ngày** gần nhất (chốt P8) | Không cần thêm thao tác đánh dấu thủ công | Thuật toán gợi ý (II.2), menu (UC03) – C | A |
| CR-18 | 01/11/2026 | **Lê Minh Sơn (C)** nhận thêm: API OTP, API tích điểm, script sinh dữ liệu mẫu (chốt P9) | C bớt việc sau khi bỏ IoT; cân bằng tải với B | Project_Plan.md (mô tả vai trò C), IV.3 Mục 3 – B, C | A |
| CR-19 | 01/11/2026 | Phiên khách thành viên hết hạn sau **1 giờ** (thay vì 4 giờ đề xuất) (chốt P10) | Một lần ngồi quán không cần lâu đến thế để gọi thêm món; giảm rủi ro người khác dùng lại phiên | UC02, UC06, SD01, NFR-S2, IV.3 – B, E | A |
| CR-20 | 01/11/2026 | Thống nhất **nơi theo dõi vấn đề mở duy nhất**: bảng "Vấn đề mở (Open Issues)" trong `1.Bao_cao/Thiet_ke_he_thong/README.md` | PM cần một nơi theo dõi tập trung | README thiết kế, CLAUDE.md – A | A |
| CR-21 | 01/11/2026 | **Chỉ nhận order qua quét QR**; thu ngân không nhận order tại quầy, **không nằm trong luồng xử lý đơn**, chỉ hỗ trợ khách (tra cứu đơn, hủy & hoàn tiền) (chốt P2) | Nếu thu ngân nhận order tại quầy sẽ không biết khách ngồi bàn nào để lên đơn | Pham_Vi_Du_An.md, II.1, III.1 (tác nhân, UC17, UC20, RBAC), SD06, W04 (chế độ tra cứu cho thu ngân), API tra cứu đơn – B, E | A |
| CR-22 | 01/11/2026 | **Pha chế** giao đồ và bấm "Đã giao" (đơn → Hoàn tất, cộng điểm), thay cho thu ngân | Hệ quả của CR-21; pha chế là người trực tiếp đưa đồ tại quầy Bar | UC19, SD06, sơ đồ trạng thái, quy trình đề xuất, API `/orders/{id}/complete` – B, E | A |
| CR-23 | 01/11/2026 | **Báo cáo bán hàng tự tổng hợp hằng ngày** (job 00:05) + **dashboard đơn giản**: doanh thu mỗi ngày của từng chi nhánh, số đơn, đơn hủy, giá trị TB/đơn, thời gian chờ TB, tỉ lệ đơn thành viên, doanh thu KM, tỉ lệ món từ gợi ý AI, top 5 món. Nâng UC16 từ Could lên **Must** (chốt P3) | PM cần theo dõi doanh thu hằng ngày theo chi nhánh | UC16, bảng mới `daily_sales_reports` (18 bảng), W08, API báo cáo, NFR-P6, mốc 16–18/11 – B, E | A |
| CR-24 | 01/11/2026 | Quy tắc "không nhận được thanh toán sau 15 phút thì tự hủy đơn" chỉ cần **mô tả**; cài đặt job ở mức Could (chốt P4) | Không triển khai thanh toán thật, thanh toán giả lập trả kết quả ngay | UC05, sơ đồ trạng thái, Pham_Vi_Du_An.md – A | A |
| CR-25 | 01/11/2026 | Chốt tên sản phẩm **SmartCafe** (chốt P5) | — | Pham_Vi_Du_An.md, README, wireframe – A, E | A |

## 4. HÌNH ẢNH / VIDEOS
(Bổ sung ảnh chụp buổi họp nếu có.)

## 5. KẾT LUẬN
**Quyết định:**
- Thông qua CR-01 → CR-25.
- Hoàn thành bộ tài liệu thiết kế giai đoạn II–IV tại `1.Bao_cao/Thiet_ke_he_thong/` (khảo sát, công nghệ, Use Case, Sequence, yêu cầu phi chức năng, ERD, schema, wireframe, kiến trúc & API), đã cập nhật theo CR-09 → CR-25: 20 use case, 6 sơ đồ Sequence, 18 bảng CSDL, 10 wireframe.
- P2 → P10 đã chốt (CR-15 → CR-25). P1 hủy (CR-09).
- Vấn đề **còn mở** (theo dõi tại bảng "Vấn đề mở" trong README thiết kế): P11 – mốc lập trình mới (giai đoạn V bắt đầu 02/11).

**Việc cần làm:**
| Việc | Người phụ trách | Hạn |
|:---|:---|:---|
| Review tài liệu thiết kế II–IV | B, C, D, E (theo bảng review trong Project_Plan) | 04/11/2026 |
| Chốt mốc lập trình mới (P11) | A | 04/11/2026 |
| Làm dashboard bán hàng + job báo cáo ngày (bổ sung việc do CR-23) | B (API, job), E (W08) | 18/11/2026 |
| Thông báo cho cả nhóm về việc bỏ IoT và đổi tên đề tài; xác nhận với giảng viên nếu cần | A | 03/11/2026 || Chạy thử `schema.sql` trên PostgreSQL thật, chuyển sang Alembic | B | 05/11/2026 |
| Dựng skeleton backend + Docker Compose; skeleton frontend | B, E | 08/11/2026 |
| Chuyển wireframe sang Figma | E | 08/11/2026 |
| Cập nhật trạng thái các giai đoạn II–IV trong Project_Plan.md (đang trễ so với kế hoạch) | A | 03/11/2026 |
