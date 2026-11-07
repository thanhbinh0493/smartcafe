# BIÊN BẢN HỌP TUẦN 01

## 1. THÀNH PHẦN
| Thành viên | Vai trò | Có mặt |
|:---|:---|:---:|
| Nguyễn Thanh Bình (A) | PM / Team Lead (chủ trì) | ✔ |
| Nguyễn Trường Thiên (B) | Backend Developer | ✔ |
| Lê Minh Sơn (C) | AI Specialist | ✔ |
| Ngô Duy Đô (D) | Tester / QA, thư ký | ✔ |
| Nguyễn Quang Tú (E) | Frontend Developer | ✔ |

## 2. NGÀY HỌP
Tuần 01 (21/09/2026 – 27/09/2026). Hình thức: họp nhóm. Thư ký: Ngô Duy Đô (D).

## 3. NỘI DUNG
| Mã | Ngày | Nội dung thay đổi / thảo luận | Lý do | Ảnh hưởng (tài liệu, module, người) | Người đề xuất |
|:---|:---|:---|:---|:---|:---|
| CR-01 | 22/09/2026 | Chốt tính năng AI là **Gợi ý món** (thời tiết + bán chạy + lịch sử khách + luật kết hợp). Bỏ phương án nhận diện khuôn mặt | Tài liệu phạm vi đang để "hoặc"; gợi ý món ít rủi ro, không cần camera, không vướng dữ liệu cá nhân | Pham_Vi_Du_An.md, II.2, module V.3 – C | Nguyễn Thanh Bình (A) |
| CR-02 | 22/09/2026 | Chốt tech stack **Python FastAPI + React + PostgreSQL** | Backend cùng ngôn ngữ với model AI nên dễ tích hợp | II.2, IV.1, IV.3, toàn bộ giai đoạn V – B, C, E | Nguyễn Thanh Bình (A) |
| CR-03 | 23/09/2026 | Menu: **menu chung** do trụ sở quản lý; chi nhánh được đặt giá riêng và bật/tắt hết hàng | Kiểm soát giá toàn chuỗi nhưng vẫn linh hoạt theo chi nhánh | Bảng `branch_menu_items`, UC12, W06 – B, E | Nguyễn Thanh Bình (A) |
| CR-04 | 23/09/2026 | Khách **không bắt buộc tài khoản**, nhập SĐT tùy chọn | Không làm chậm luồng gọi món; SĐT dùng để cá nhân hóa gợi ý | Bảng `customers`, UC06, W02 – B, E | Nguyễn Thanh Bình (A) |
| CR-05 | 24/09/2026 | Thanh toán **trả trước trên web (giả lập)**; đơn chỉ xuống quầy Bar sau khi thanh toán thành công | Phù hợp phạm vi (không tích hợp cổng thật); giảm việc cho thu ngân | Trạng thái đơn, SD02, Mock Payment – B, E | Nguyễn Thanh Bình (A) |
| CR-06 | 25/09/2026 | Khảo sát II.1 làm theo mô hình **giả định điển hình** kèm bộ câu hỏi phỏng vấn | Chưa có quán thực tế để khảo sát | II.1 – D | Nguyễn Thanh Bình (A) |

## 4. HÌNH ẢNH / VIDEOS
(Bổ sung ảnh chụp buổi họp nếu có.)

## 5. KẾT LUẬN
**Quyết định:**
- Thông qua CR-01: Chốt tính năng AI là Gợi ý món (thời tiết + bán chạy + lịch sử khách + luật kết hợp).
- Thông qua CR-02: Chốt tech stack Python FastAPI + React + PostgreSQL.
- Thông qua CR-03: Menu: menu chung do trụ sở quản lý; chi nhánh được đặt giá riêng và bật/tắt hết hàng.
- Thông qua CR-04: Khách không bắt buộc tài khoản, nhập SĐT tùy chọn.
- Thông qua CR-05: Thanh toán trả trước trên web (giả lập); đơn chỉ xuống quầy Bar sau khi thanh toán thành công.
- Thông qua CR-06: Khảo sát II.1 làm theo mô hình giả định điển hình kèm bộ câu hỏi phỏng vấn.

**Việc cần làm:**
| Việc | Người phụ trách | Hạn |
|:---|:---|:---|
| Vẽ Use Case (20 UC), Sequence Diagram 6 luồng chính, sơ đồ trạng thái đơn hàng | Nguyễn Thanh Bình | 06/10/2026 |
