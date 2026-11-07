# BIÊN BẢN HỌP TUẦN 04

## 1. THÀNH PHẦN
| Thành viên | Vai trò | Có mặt |
|:---|:---|:---:|
| Nguyễn Thanh Bình (A) | PM / Team Lead (chủ trì) | ✔ |
| Nguyễn Trường Thiên (B) | Backend Developer | ✔ |
| Lê Minh Sơn (C) | AI Specialist | ✔ |
| Ngô Duy Đô (D) | Tester / QA, thư ký | ✔ |
| Nguyễn Quang Tú (E) | Frontend Developer | ✔ |

## 2. NGÀY HỌP
Tuần 04 (12/10/2026 – 18/10/2026). Hình thức: họp nhóm. Thư ký: Ngô Duy Đô (D).

## 3. NỘI DUNG
| Mã | Ngày | Nội dung thay đổi / thảo luận | Lý do | Ảnh hưởng (tài liệu, module, người) | Người đề xuất |
|:---|:---|:---|:---|:---|:---|
| CR-26 | 15/10/2026 | Chốt môi trường chạy và demo: chạy **local trên laptop** bằng Docker Desktop (WSL2) + Docker Compose, cài Docker tại `D:\Docker`; giới hạn WSL2 4 GB RAM / 4 nhân. Không dùng Google Colab (không chạy được web server liên tục, không có Docker và URL cố định). Bản dự phòng trên cloud để mở (P12) | Không tốn chi phí, đúng kiến trúc Docker Compose đã chốt; laptop (i5-10210U, 16 GB RAM, SSD) đủ tải demo; ổ C còn ít dung lượng nên đặt Docker ở ổ D | README thiết kế (D24, P12); máy demo của A; B, E dùng chung cấu hình Docker Compose | Nguyễn Thanh Bình (A) |
| CR-27 | 17/10/2026 | Tạm gác vấn đề timeline (P11): không điều chỉnh mốc lập trình lúc này, A sẽ tự hoàn thiện timeline thủ công sau | Ưu tiên bắt đầu code ngay | README thiết kế (P11 → Hoãn); Project_Plan.md, IV.3 Mục 3 (A cập nhật sau) | Nguyễn Thanh Bình (A) |
| CR-28 | 18/10/2026 | Quy trình code: làm **theo từng luồng nghiệp vụ cốt lõi**, mỗi luồng bắt buộc có **test tự động** và **biên bản kiểm thử** đầy đủ trước khi sang luồng tiếp theo | Đảm bảo chất lượng từng phần, có minh chứng kiểm thử cho báo cáo | README thiết kế (D25); B, C, E (viết test), D (biên bản kiểm thử) | Nguyễn Thanh Bình (A) |

## 4. HÌNH ẢNH / VIDEOS
(Bổ sung ảnh chụp buổi họp nếu có.)

## 5. KẾT LUẬN
**Quyết định:**
- Thông qua CR-26: môi trường demo là Docker Desktop trên laptop, cài tại `D:\Docker` (D24).
- Thông qua CR-27: tạm gác P11, A tự hoàn thiện timeline thủ công.
- Thông qua CR-28: code theo từng luồng cốt lõi, mỗi luồng có test tự động + biên bản kiểm thử (D25).

**Việc cần làm:**
| Việc | Người phụ trách | Hạn |
|:---|:---|:---|
| F0 – Nền tảng: Docker Compose, CSDL + Alembic, dữ liệu mẫu, đăng nhập nhân viên, phân quyền | Nguyễn Trường Thiên | 21/10/2026 |
| F1 – Quét QR → màn hình chào → menu chi nhánh (giá riêng, khuyến mãi) | Nguyễn Trường Thiên, Nguyễn Quang Tú | 23/10/2026 |
| F2 – Giỏ hàng → đặt món → thanh toán giả lập → theo dõi đơn realtime | Nguyễn Trường Thiên, Nguyễn Quang Tú | 25/10/2026 |
| F3 – Màn hình Bar: hàng đợi pha chế, Bắt đầu / Xong / Hoàn tác / Đã giao | Nguyễn Trường Thiên, Nguyễn Quang Tú | 27/10/2026 |
| F7 – AI gợi ý món 2 chế độ (ẩn danh / thành viên) + "Thường gọi kèm" (FP-Growth), job học luật hằng đêm | Lê Minh Sơn, Nguyễn Trường Thiên, Nguyễn Quang Tú | 30/10/2026 |
