# Kế hoạch Dự án: Phần mềm quản lý chuỗi quán cà phê thông minh (Đồ án Môn học)

Dự án kéo dài **8 tuần**, từ **21/09/2026** đến **16/11/2026** (D41, CR-45). 
Vì là đồ án môn học, phần **Lập trình** được tinh gọn và làm theo **9 luồng F0 → F8** (D26): mỗi luồng gồm backend + frontend + test tự động + biên bản kiểm thử, xong luồng này mới sang luồng sau. Các module chính: quản lý cốt lõi (menu, chi nhánh, khuyến mãi, nhân viên), gọi món qua mã QR, màn hình Bar, AI gợi ý món, báo cáo bán hàng.

> Cập nhật 01/11/2026 (biên bản Tuần 06): bỏ phần IoT khỏi phạm vi; bổ sung khuyến mãi, tích điểm, OTP giả lập.
> Cập nhật 03/11/2026 (biên bản Tuần 07, CR-45): kết thúc dự án dời về 16/11/2026, các giai đoạn dàn đều trong 8 tuần; giai đoạn Lập trình ghi theo 9 luồng F0 → F8; bỏ giai đoạn "Các rủi ro của dự án"; bảng chi tiết dưới đây sinh từ [2.San_pham/Nhom_8_Phan_cong.xlsx](../2.San_pham/Nhom_8_Phan_cong.xlsx).

## Phân công nhân sự
1. **Thành viên A – Nguyễn Thanh Bình**: Project Manager (PM) / Team Lead, Phân tích nghiệp vụ.
2. **Thành viên B**: Backend Developer (Làm API Core, Database).
3. **Thành viên C**: AI Specialist (Làm model AI gợi ý món; API OTP và tích điểm; script sinh dữ liệu mẫu).
4. **Thành viên D**: Tester, QA, Hỗ trợ viết tài liệu & báo cáo.
5. **Thành viên E**: Frontend Developer (Làm Web Admin, Giao diện QR Order).

## Bảng Phân công và Tiến độ chi tiết

| STT | Tên công việc | Chi tiết công việc | Người thực hiện | Người Review | Ngày bắt đầu | Ngày kết thúc | Thời gian Review | Trạng thái | Ghi chú |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| **I** | **Lập kế hoạch dự án** |  | Cả nhóm | Cả nhóm | **21/09/2026** | **24/09/2026** |  |  |  |
| 1 |  | Thống nhất đề tài, phạm vi in-scope / out-of-scope, tính năng cốt lõi | Nguyễn Thanh Bình | Cả nhóm | 21/09/2026 | 22/09/2026 | 23/09/2026 | Hoàn thành | Pham_Vi_Du_An.md |
| 2 |  | Lập WBS, phân công công việc, chốt timeline | Nguyễn Thanh Bình | Cả nhóm | 23/09/2026 | 24/09/2026 | 24/09/2026 | Hoàn thành | Project_Plan.md, bảng phân công này |
| **II** | **Khảo sát và nghiên cứu công nghệ** |  |  |  | **25/09/2026** | **01/10/2026** |  |  |  |
| 1 |  | Khảo sát quy trình bán hàng của quán cà phê: hiện trạng và quy trình đề xuất (gọi món qua QR, không POS tại quầy) | Thành viên D | Nguyễn Thanh Bình | 25/09/2026 | 29/09/2026 | 30/09/2026 | Hoàn thành | II.1 |
| 2 |  | Nghiên cứu công nghệ: FastAPI, React, PostgreSQL, WebSocket, gợi ý món & FP-Growth, OTP giả lập | Thành viên C | Thành viên B | 25/09/2026 | 30/09/2026 | 01/10/2026 | Hoàn thành | II.2; bỏ IoT (D8) |
| **III** | **Phân tích** |  |  |  | **02/10/2026** | **09/10/2026** |  |  |  |
| 1 |  | Vẽ Use Case (20 UC), Sequence Diagram 6 luồng chính, sơ đồ trạng thái đơn hàng | Nguyễn Thanh Bình | Thành viên B | 02/10/2026 | 06/10/2026 | 07/10/2026 | Hoàn thành | III.1 – trọng tâm báo cáo |
| 2 |  | Phân tích yêu cầu phi chức năng (29 NFR) & mô hình dữ liệu khái niệm | Thành viên D | Thành viên C | 05/10/2026 | 08/10/2026 | 09/10/2026 | Hoàn thành | III.2 |
| **IV** | **Thiết kế** |  |  |  | **10/10/2026** | **19/10/2026** |  |  |  |
| 1 |  | Thiết kế CSDL: ERD, lược đồ quan hệ 18 bảng (schema.sql) | Thành viên B | Nguyễn Thanh Bình | 10/10/2026 | 13/10/2026 | 14/10/2026 | Hoàn thành | IV.1 |
| 2 |  | Thiết kế giao diện: sitemap, wireframe W00–W08 (QR Order + Web Admin) | Thành viên E | Thành viên D | 12/10/2026 | 16/10/2026 | 17/10/2026 | Hoàn thành | IV.2 – wireframe PlantUML |
| 3 |  | Thiết kế kiến trúc hệ thống và danh sách API, kênh WebSocket | Thành viên B | Nguyễn Thanh Bình | 15/10/2026 | 18/10/2026 | 19/10/2026 | Hoàn thành | IV.3 |
| **V** | **Lập trình** | (Theo 9 luồng F0 → F8 – D26; mỗi luồng có test tự động + biên bản kiểm thử do Thành viên D lập) |  |  | **20/10/2026** | **31/10/2026** |  |  |  |
| 1 |  | F0 – Nền tảng: Docker Compose, CSDL + Alembic, dữ liệu mẫu, đăng nhập nhân viên, phân quyền | Thành viên B | Nguyễn Thanh Bình | 20/10/2026 | 21/10/2026 | 22/10/2026 | Hoàn thành | 48/48 ca đạt; thực tế xong 02/11 |
| 2 |  | F1 – Quét QR → màn hình chào → menu chi nhánh (giá riêng, khuyến mãi) | Thành viên B, Thành viên E | Nguyễn Thanh Bình | 22/10/2026 | 23/10/2026 | 24/10/2026 | Hoàn thành | 57/57 ca đạt; thực tế xong 02/11 |
| 3 |  | F2 – Giỏ hàng → đặt món → thanh toán giả lập → theo dõi đơn realtime | Thành viên B, Thành viên E | Nguyễn Thanh Bình | 23/10/2026 | 25/10/2026 | 26/10/2026 | Hoàn thành | 67/67 ca đạt; thực tế xong 02/11 |
| 4 |  | F3 – Màn hình Bar: hàng đợi pha chế, Bắt đầu / Xong / Hoàn tác / Đã giao | Thành viên B, Thành viên E | Nguyễn Thanh Bình | 25/10/2026 | 27/10/2026 | 28/10/2026 | Hoàn thành | 76/76 ca đạt; thực tế xong 03/11 |
| 5 |  | F4 – Khách thành viên: OTP giả lập, tích điểm, xem điểm | Thành viên C, Thành viên B, Thành viên E | Nguyễn Thanh Bình | 26/10/2026 | 28/10/2026 | 29/10/2026 | Hoàn thành | 84/84 ca đạt; thực tế xong 03/11 |
| 6 |  | F5 – Thu ngân hỗ trợ khách: tra cứu, hủy đơn & hoàn tiền giả lập | Thành viên B, Thành viên E | Nguyễn Thanh Bình | 28/10/2026 | 29/10/2026 | 30/10/2026 | Hoàn thành | 53/53 ca đạt; thực tế xong 03/11 |
| 7 |  | F6 – Quản trị: chi nhánh, nhân viên, danh mục, món + ảnh, menu chi nhánh, bàn & mã QR, khuyến mãi | Thành viên B, Thành viên E | Nguyễn Thanh Bình | 26/10/2026 | 30/10/2026 | 31/10/2026 | Hoàn thành | 230/230 ca đạt; thực tế xong 03/11 |
| 8 |  | F7 – AI gợi ý món 2 chế độ (ẩn danh / thành viên) + "Thường gọi kèm" (FP-Growth), job học luật hằng đêm | Thành viên C, Thành viên B, Thành viên E | Nguyễn Thanh Bình | 22/10/2026 | 30/10/2026 | 31/10/2026 | Hoàn thành | 71/71 ca đạt; Hit Rate@5 thành viên 48,9%; thực tế xong 03/11 |
| 9 |  | F8 – Báo cáo ngày (job 00:05) + dashboard bán hàng | Thành viên B, Thành viên E | Nguyễn Thanh Bình | 30/10/2026 | 31/10/2026 | 01/11/2026 | Hoàn thành | 41/41 ca đạt; thực tế xong 03/11 |
| **VI** | **Kiểm thử hệ thống** |  |  |  | **01/11/2026** | **03/11/2026** |  |  |  |
| 1 |  | Lập kế hoạch kiểm thử hệ thống và test case: kịch bản xuyên luồng F1 → F8, 29 yêu cầu phi chức năng | Thành viên D | Nguyễn Thanh Bình | 01/11/2026 | 02/11/2026 | 02/11/2026 | Hoàn thành | Ke_hoach_kiem_thu_He_thong.md; thực tế làm 03/11 |
| 2 |  | Chạy kiểm thử hệ thống (hiệu năng, bảo mật, giao diện, vận hành), log bug, fix bug, hồi quy F0 → F8 | Thành viên D, Thành viên B, Thành viên E | Nguyễn Thanh Bình | 02/11/2026 | 03/11/2026 | 03/11/2026 | Hoàn thành | 66/66 ca đạt; 6 lỗi đã sửa; hồi quy 664/664; thực tế làm 03/11 |
| **VII** | **Đào tạo và Chuyển giao** | (Hướng dẫn sử dụng) |  |  | **03/11/2026** | **05/11/2026** |  |  |  |
| 1 |  | Viết Hướng dẫn sử dụng có ảnh chụp màn hình cho khách, pha chế, thu ngân, quản lý, quản trị viên | Thành viên D | Nguyễn Thanh Bình | 03/11/2026 | 03/11/2026 | 05/11/2026 | Hoàn thành | Huong_dan_su_dung.md – 33 ảnh |
| 2 |  | Cả nhóm đọc và thử lại các bước của Hướng dẫn sử dụng trên máy demo | Cả nhóm | Nguyễn Thanh Bình | 04/11/2026 | 05/11/2026 | 05/11/2026 | Chuẩn bị |  |
| **VIII** | **Các tài liệu của Dự án** | (Chuẩn hóa tài liệu) |  |  | **04/11/2026** | **09/11/2026** |  |  |  |
| 1 |  | Rà soát, đồng bộ tài liệu II–VII với mã nguồn: thuật ngữ, quyết định D1–D41, sơ đồ PNG, bảng phân công, kế hoạch | Nguyễn Thanh Bình, Thành viên D | Cả nhóm | 04/11/2026 | 06/11/2026 | 07/11/2026 | Đang làm |  |
| 2 |  | Xuất các tài liệu Markdown sang .docx theo mẫu môn học (thiết kế, biên bản kiểm thử, HDSD, biên bản họp) | Thành viên D | Nguyễn Thanh Bình | 07/11/2026 | 09/11/2026 | 09/11/2026 | Chuẩn bị |  |
| **IX** | **Báo cáo tổng thể dự án** |  |  |  | **10/11/2026** | **12/11/2026** |  |  |  |
| 1 |  | Viết báo cáo tổng kết môn học | Nguyễn Thanh Bình | Cả nhóm | 10/11/2026 | 12/11/2026 | 12/11/2026 | Chuẩn bị | Nộp BTL |
| **X** | **Slide, Biên bản họp, Demo** |  |  |  | **12/11/2026** | **15/11/2026** |  |  |  |
| 1 |  | Ghi chép biên bản các cuộc họp nhóm | Thành viên D | Nguyễn Thanh Bình | Làm suốt kỳ | Làm suốt kỳ | - | Đang làm | Biên bản Tuần 06, 07 |
| 2 |  | Thiết kế slide thuyết trình bảo vệ cuối kỳ | Thành viên E | Cả nhóm | 12/11/2026 | 14/11/2026 | 14/11/2026 | Chuẩn bị |  |
| 3 |  | Chuẩn bị và diễn tập demo trên laptop: kịch bản demo, dữ liệu sạch, sao lưu CSDL | Nguyễn Thanh Bình, Thành viên E | Cả nhóm | 14/11/2026 | 15/11/2026 | 15/11/2026 | Chuẩn bị | Chỉ demo trên laptop (D40) |
| **XI** | **Các mẫu Biên bản** | (Hình thức) |  |  | **16/11/2026** | **16/11/2026** |  |  |  |
| 1 |  | Viết biên bản nghiệm thu (cho đủ form môn học) | Thành viên D | Nguyễn Thanh Bình | 16/11/2026 | 16/11/2026 | 16/11/2026 | Chuẩn bị | Kết thúc dự án 16/11/2026 |

