# BIÊN BẢN HỌP TUẦN 03

## 1. THÀNH PHẦN
| Thành viên | Vai trò | Có mặt |
|:---|:---|:---:|
| Nguyễn Thanh Bình (A) | PM / Team Lead (chủ trì) | ✔ |
| Nguyễn Trường Thiên (B) | Backend Developer | ✔ |
| Lê Minh Sơn (C) | AI Specialist | ✔ |
| Ngô Duy Đô (D) | Tester / QA, thư ký | ✔ |
| Nguyễn Quang Tú (E) | Frontend Developer | ✔ |

## 2. NGÀY HỌP
Tuần 03 (05/10/2026 – 11/10/2026). Hình thức: họp nhóm. Thư ký: Ngô Duy Đô (D).

## 3. NỘI DUNG
| Mã | Ngày | Nội dung thay đổi / thảo luận | Lý do | Ảnh hưởng (tài liệu, module, người) | Người đề xuất |
|:---|:---|:---|:---|:---|:---|
| CR-10 | 05/10/2026 | Ngay sau khi quét QR có **màn hình chào 2 lựa chọn**: (1) không nhập SĐT, xem menu ngay; (2) nhập SĐT để tích điểm và nhận gợi ý theo sở thích. **Không lưu thông tin thiết bị** của khách | Thiết kế cũ chỉ nhập SĐT ở bước giỏ hàng nên lúc mở menu không biết khách là ai để gợi ý theo thói quen; khách có thể đổi điện thoại | UC01, SD01, W00, W01 – B, E | Nguyễn Thanh Bình (A) |
| CR-11 | 05/10/2026 | Bổ sung **chương trình khuyến mãi đơn giản**: tên, thời gian, phạm vi toàn chuỗi / 1 chi nhánh, danh sách món + giá KM. Không làm voucher, combo, mua 1 tặng 1 | Gợi ý cho khách ẩn danh cần dựa trên "món đang khuyến mãi" | UC15, SD05, W07, bảng `promotions`, `promotion_items`; giá trong UC03, UC05 – B, E | Nguyễn Thanh Bình (A) |
| CR-12 | 05/10/2026 | Bổ sung **tích điểm** ở mức chỉ tích và xem điểm (cộng khi đơn hoàn tất); chưa làm đổi điểm | Tạo lý do để khách để lại SĐT; giữ phạm vi "không làm tài chính" | UC07, UC19, SD06, bảng `loyalty_transactions`, `customers.loyalty_points` – B, C | Nguyễn Thanh Bình (A) |
| CR-13 | 05/10/2026 | **Xác thực SĐT bằng OTP giả lập** (6 số, hạn 5 phút, tối đa 5 lần sai, giới hạn gửi lại) | Ngăn người khác nhập SĐT của khách để xem sở thích hoặc tích điểm hộ | UC02, SD01, W00a, bảng `otp_requests`, NFR-S4 – B, E | Nguyễn Thanh Bình (A) |
| CR-14 | 05/10/2026 | Gợi ý món theo **2 chế độ**: ẩn danh (bán chạy + KM + món mới) và thành viên (sở thích + món tương tự + bán chạy + KM); **thời tiết giữ làm yếu tố phụ** (10%) | Phù hợp với CR-10; tài liệu phạm vi gốc có nhắc thời tiết | II.2 (Mục 2), SD02, bảng `recommendation_logs.mode` – C | Nguyễn Thanh Bình (A) |
| CR-15 | 07/10/2026 | **Chỉ Quản trị viên** được tạo/sửa chương trình khuyến mãi; Quản lý chi nhánh không tạo KM (chốt P6) | Đơn giản hóa luồng vận hành | UC15, RBAC (III.1), SD05, W06, W07, API `/api/staff/promotions` – B, E | Nguyễn Thanh Bình (A) |
| CR-16 | 07/10/2026 | Tỉ lệ tích điểm **1 điểm / 10.000đ**; **1 điểm = 100đ**, tức hoàn lại 1% cho khách (chốt P7) | Tỉ lệ dễ hiểu, chi phí khuyến khích thấp | UC19, III.2 quy tắc 5, W01 (hiển thị giá trị quy đổi), cấu hình `POINT_VALUE_VND` – C, E | Nguyễn Thanh Bình (A) |
| CR-17 | 07/10/2026 | "Món mới" = món tạo trong **30 ngày** gần nhất (chốt P8) | Không cần thêm thao tác đánh dấu thủ công | Thuật toán gợi ý (II.2), menu (UC03) – C | Nguyễn Thanh Bình (A) |
| CR-18 | 07/10/2026 | **Lê Minh Sơn (C)** nhận thêm: API OTP, API tích điểm, script sinh dữ liệu mẫu (chốt P9) | C bớt việc sau khi bỏ IoT; cân bằng tải với B | Project_Plan.md (mô tả vai trò C), IV.3 Mục 3 – B, C | Nguyễn Thanh Bình (A) |
| CR-19 | 07/10/2026 | Phiên khách thành viên hết hạn sau **1 giờ** (thay vì 4 giờ đề xuất) (chốt P10) | Một lần ngồi quán không cần lâu đến thế để gọi thêm món; giảm rủi ro người khác dùng lại phiên | UC02, UC06, SD01, NFR-S2, IV.3 – B, E | Nguyễn Thanh Bình (A) |
| CR-20 | 08/10/2026 | Thống nhất **nơi theo dõi vấn đề mở duy nhất**: bảng "Vấn đề mở (Open Issues)" trong `1.Bao_cao/Thiet_ke_he_thong/README.md` | PM cần một nơi theo dõi tập trung | README thiết kế, CLAUDE.md – A | Nguyễn Thanh Bình (A) |
| CR-21 | 09/10/2026 | **Chỉ nhận order qua quét QR**; thu ngân không nhận order tại quầy, **không nằm trong luồng xử lý đơn**, chỉ hỗ trợ khách (tra cứu đơn, hủy & hoàn tiền) (chốt P2) | Nếu thu ngân nhận order tại quầy sẽ không biết khách ngồi bàn nào để lên đơn | Pham_Vi_Du_An.md, II.1, III.1 (tác nhân, UC17, UC20, RBAC), SD06, W04 (chế độ tra cứu cho thu ngân), API tra cứu đơn – B, E | Nguyễn Thanh Bình (A) |
| CR-22 | 09/10/2026 | **Pha chế** giao đồ và bấm "Đã giao" (đơn → Hoàn tất, cộng điểm), thay cho thu ngân | Hệ quả của CR-21; pha chế là người trực tiếp đưa đồ tại quầy Bar | UC19, SD06, sơ đồ trạng thái, quy trình đề xuất, API `/orders/{id}/complete` – B, E | Nguyễn Thanh Bình (A) |
| CR-23 | 09/10/2026 | **Báo cáo bán hàng tự tổng hợp hằng ngày** (job 00:05) + **dashboard đơn giản**: doanh thu mỗi ngày của từng chi nhánh, số đơn, đơn hủy, giá trị TB/đơn, thời gian chờ TB, tỉ lệ đơn thành viên, doanh thu KM, tỉ lệ món từ gợi ý AI, top 5 món. Nâng UC16 từ Could lên **Must** (chốt P3) | PM cần theo dõi doanh thu hằng ngày theo chi nhánh | UC16, bảng mới `daily_sales_reports` (18 bảng), W08, API báo cáo, NFR-P6, mốc 16–18/11 – B, E | Nguyễn Thanh Bình (A) |
| CR-24 | 09/10/2026 | Quy tắc "không nhận được thanh toán sau 15 phút thì tự hủy đơn" chỉ cần **mô tả**; cài đặt job ở mức Could (chốt P4) | Không triển khai thanh toán thật, thanh toán giả lập trả kết quả ngay | UC05, sơ đồ trạng thái, Pham_Vi_Du_An.md – A | Nguyễn Thanh Bình (A) |
| CR-25 | 09/10/2026 | Chốt tên sản phẩm **SmartCafe** (chốt P5) | — | Pham_Vi_Du_An.md, README, wireframe – A, E | Nguyễn Thanh Bình (A) |

## 4. HÌNH ẢNH / VIDEOS
(Bổ sung ảnh chụp buổi họp nếu có.)

## 5. KẾT LUẬN
**Quyết định:**
- Thông qua CR-10: Ngay sau khi quét QR có màn hình chào 2 lựa chọn: (1) không nhập SĐT, xem menu ngay; (2) nhập SĐT để tích điểm và nhận gợi ý theo sở thích.
- Thông qua CR-11: Bổ sung chương trình khuyến mãi đơn giản: tên, thời gian, phạm vi toàn chuỗi / 1 chi nhánh, danh sách món + giá KM. Không làm voucher, combo, mua 1 tặng 1.
- Thông qua CR-12: Bổ sung tích điểm ở mức chỉ tích và xem điểm (cộng khi đơn hoàn tất); chưa làm đổi điểm.
- Thông qua CR-13: Xác thực SĐT bằng OTP giả lập (6 số, hạn 5 phút, tối đa 5 lần sai, giới hạn gửi lại).
- Thông qua CR-14: Gợi ý món theo 2 chế độ: ẩn danh (bán chạy + KM + món mới) và thành viên (sở thích + món tương tự + bán chạy + KM); thời tiết giữ làm yếu tố phụ (10%).
- Thông qua CR-15: Chỉ Quản trị viên được tạo/sửa chương trình khuyến mãi; Quản lý chi nhánh không tạo KM (chốt P6).
- Thông qua CR-16: Tỉ lệ tích điểm 1 điểm / 10.000đ; 1 điểm = 100đ, tức hoàn lại 1% cho khách (chốt P7).
- Thông qua CR-17: "Món mới" = món tạo trong 30 ngày gần nhất (chốt P8).
- Thông qua CR-18: Lê Minh Sơn (C) nhận thêm: API OTP, API tích điểm, script sinh dữ liệu mẫu (chốt P9).
- Thông qua CR-19: Phiên khách thành viên hết hạn sau 1 giờ (thay vì 4 giờ đề xuất) (chốt P10).
- Thông qua CR-20: Thống nhất nơi theo dõi vấn đề mở duy nhất: bảng "Vấn đề mở (Open Issues)" trong `1.Bao_cao/Thiet_ke_he_thong/README.md`.
- Thông qua CR-21: Chỉ nhận order qua quét QR; thu ngân không nhận order tại quầy, không nằm trong luồng xử lý đơn, chỉ hỗ trợ khách (tra cứu đơn, hủy & hoàn tiền) (chốt P2).
- Thông qua CR-22: Pha chế giao đồ và bấm "Đã giao" (đơn → Hoàn tất, cộng điểm), thay cho thu ngân.
- Thông qua CR-23: Báo cáo bán hàng tự tổng hợp hằng ngày (job 00:05) + dashboard đơn giản: doanh thu mỗi ngày của từng chi nhánh, số đơn, đơn hủy, giá trị TB/đơn, thời gian chờ T….
- Thông qua CR-24: Quy tắc "không nhận được thanh toán sau 15 phút thì tự hủy đơn" chỉ cần mô tả; cài đặt job ở mức Could (chốt P4).
- Thông qua CR-25: Chốt tên sản phẩm SmartCafe (chốt P5).

**Việc cần làm:**
| Việc | Người phụ trách | Hạn |
|:---|:---|:---|
| Thiết kế giao diện: sitemap, wireframe W00–W08 (QR Order + Web Admin) | Nguyễn Quang Tú | 16/10/2026 |
| Thiết kế kiến trúc hệ thống và danh sách API, kênh WebSocket | Nguyễn Trường Thiên | 18/10/2026 |
