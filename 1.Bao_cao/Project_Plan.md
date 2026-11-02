# Kế hoạch Dự án: Phần mềm quản lý chuỗi quán cà phê thông minh (Đồ án Môn học)

Dự án kéo dài 3 tháng (12 tuần), bắt đầu từ **21/09/2026** và kết thúc dự kiến vào **21/12/2026**. 
Vì là đồ án môn học, phần **Lập trình** sẽ được tinh gọn, tập trung vào 3 module "ăn điểm" nhất: Quản lý cốt lõi, Quét mã QR đặt hàng, và Tích hợp một model AI nhỏ (gợi ý món).

> Cập nhật 01/11/2026 (biên bản Tuần 06): bỏ phần IoT khỏi phạm vi; bổ sung khuyến mãi, tích điểm, OTP giả lập.

## Phân công nhân sự
1. **Bạn (Thành viên A)**: Project Manager (PM) / Team Lead, Phân tích nghiệp vụ.
2. **Thành viên B**: Backend Developer (Làm API Core, Database).
3. **Thành viên C**: AI Specialist (Làm model AI gợi ý món; API OTP và tích điểm; script sinh dữ liệu mẫu).
4. **Thành viên D**: Tester, QA, Hỗ trợ viết tài liệu & báo cáo.
5. **Thành viên E**: Frontend Developer (Làm Web Admin, Giao diện QR Order).

## Bảng Phân công và Tiến độ chi tiết

| STT | Tên công việc | Chi tiết công việc | Người thực hiện | Người Review | Ngày bắt đầu | Ngày kết thúc | Thời gian Review | Trạng thái | Ghi chú |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| **I** | **Lập kế hoạch dự án** | | **Cả nhóm** | **Cả nhóm** | **21/09/2026**| **25/09/2026**| | | |
| 1 | | Thống nhất đề tài, phạm vi, tính năng cốt lõi sẽ làm | Bạn (A) | Cả nhóm | 21/09/2026 | 22/09/2026 | 23/09/2026 | Hoàn thành | |
| 2 | | Lập WBS, phân công công việc, chốt timeline | Bạn (A) | Cả nhóm | 24/09/2026 | 25/09/2026 | 25/09/2026 | Hoàn thành | |
| **II** | **Khảo sát và thu thập thông tin**| | | | **26/09/2026**| **02/10/2026**| | | |
| 1 | | Khảo sát quy trình quản lý menu, đặt hàng cơ bản | Thành viên D | Bạn (A) | 26/09/2026 | 29/09/2026 | 30/09/2026 | Đang làm | |
| 2 | | Nghiên cứu công nghệ AI, IoT áp dụng cho bài toán | Thành viên C | Thành viên B | 26/09/2026 | 01/10/2026 | 02/10/2026 | Đang làm | |
| **III** | **Phân tích** | | | | **03/10/2026**| **12/10/2026**| | | |
| 1 | | Vẽ Use Case, Sequence Diagram cho các luồng chính | Bạn (A) | Thành viên B | 03/10/2026 | 07/10/2026 | 08/10/2026 | Chuẩn bị | Trọng tâm báo cáo |
| 2 | | Phân tích yêu cầu phi chức năng & Data Model | Thành viên D | Thành viên C | 08/10/2026 | 11/10/2026 | 12/10/2026 | Chuẩn bị | |
| **IV** | **Thiết kế** | | | | **13/10/2026**| **22/10/2026**| | | |
| 1 | | Thiết kế CSDL (ERD, Relational Schema) | Thành viên B | Bạn (A) | 13/10/2026 | 16/10/2026 | 17/10/2026 | Chuẩn bị | |
| 2 | | Thiết kế Mockup/UI Web Admin & Giao diện QR | Thành viên E | Thành viên D | 15/10/2026 | 20/10/2026 | 22/10/2026 | Chuẩn bị | Figma |
| **V** | **Lập trình** | (Tập trung 3 Module cốt lõi) | | | **23/10/2026**| **25/11/2026**| | | |
| 1 | | Backend: Xây dựng API Quản lý Menu, Đơn hàng | Thành viên B | Bạn (A) | 23/10/2026 | 15/11/2026 | 16/11/2026 | Chuẩn bị | Module chính 1 |
| 2 | | Frontend: Làm Web Admin và Giao diện Khách Order | Thành viên E | Thành viên B | 25/10/2026 | 18/11/2026 | 20/11/2026 | Chuẩn bị | Module chính 2 |
| 3 | | AI: Viết model gợi ý món (2 chế độ ẩn danh / thành viên) | Thành viên C | Thành viên B | 25/10/2026 | 20/11/2026 | 22/11/2026 | Chuẩn bị | Module chính 3 |
| 4 | | Tích hợp hệ thống, ráp API vào Frontend & AI | B, C, E | Bạn (A) | 21/11/2026 | 25/11/2026 | 25/11/2026 | Chuẩn bị | |
| **VI** | **Kiểm thử** | | | | **26/11/2026**| **02/12/2026**| | | |
| 1 | | Lập Test Case cho 3 module chính | Thành viên D | Bạn (A) | 26/11/2026 | 28/11/2026 | 29/11/2026 | Chuẩn bị | |
| 2 | | Test ứng dụng, Log bug và Fix bug | D, B, E | Bạn (A) | 29/11/2026 | 02/12/2026 | 02/12/2026 | Chuẩn bị | |
| **VII**| **Đào tạo và Chuyển giao** | (Làm HDSD cơ bản) | | | **03/12/2026**| **05/12/2026**| | | |
| 1 | | Viết tài liệu Hướng dẫn sử dụng | Thành viên D | Bạn (A) | 03/12/2026 | 04/12/2026 | 05/12/2026 | Chuẩn bị | |
| **VIII**|**Các rủi ro của dự án** | | | | **06/12/2026**| **07/12/2026**| | | |
| 1 | | Liệt kê rủi ro (Trễ tiến độ, model AI không chạy...) | Bạn (A) | Cả nhóm | 06/12/2026 | 06/12/2026 | 07/12/2026 | Chuẩn bị | |
| **IX** | **Các tài liệu của Dự án** | | | | **08/12/2026**| **12/12/2026**| | | |
| 1 | | Format và chuẩn hóa toàn bộ tài liệu BTL | Bạn (A), D | Cả nhóm | 08/12/2026 | 11/12/2026 | 12/12/2026 | Chuẩn bị | |
| **X** | **Báo cáo tổng thể dự án**| | | | **13/12/2026**| **16/12/2026**| | | |
| 1 | | Viết báo cáo tổng kết môn học | Bạn (A) | Cả nhóm | 13/12/2026 | 15/12/2026 | 16/12/2026 | Chuẩn bị | Nộp BTL |
| **XI** | **Slide, Biên bản họp** | | | | **17/12/2026**| **20/12/2026**| | | |
| 1 | | Ghi chép biên bản các cuộc họp nhóm | Thành viên D | Bạn (A) | Làm suốt kỳ | Làm suốt kỳ | - | Đang làm | |
| 2 | | Thiết kế Slide thuyết trình bảo vệ cuối kỳ | Thành viên E | Cả nhóm | 17/12/2026 | 19/12/2026 | 20/12/2026 | Chuẩn bị | |
| **XII**| **Các mẫu Biên bản** | (Hình thức) | | | **21/12/2026**| **21/12/2026**| | | |
| 1 | | Viết biên bản nghiệm thu (cho đủ Form môn học) | Thành viên D | Bạn (A) | 21/12/2026 | 21/12/2026 | 21/12/2026 | Chuẩn bị | |
