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

## 4. HÌNH ẢNH / VIDEOS
(Bổ sung ảnh chụp buổi họp nếu có.)

## 5. KẾT LUẬN
**Quyết định:**
- Thông qua CR-26: môi trường demo là Docker Desktop trên laptop, cài tại `D:\Docker` (D24).
- Thông qua CR-27: tạm gác P11, A tự hoàn thiện timeline thủ công.
- Thông qua CR-28: code theo từng luồng cốt lõi, mỗi luồng có test tự động + biên bản kiểm thử (D25).
- Thông qua CR-29: thứ tự luồng F0 → F8, vị trí mã nguồn và biên bản kiểm thử (D26).
- Thông qua CR-30: dùng kho GitHub chung cho toàn bộ project.
- Vấn đề còn mở: P12 (bản demo dự phòng trên cloud), P13 (quy tắc gắn nhãn khuyến mãi).

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
