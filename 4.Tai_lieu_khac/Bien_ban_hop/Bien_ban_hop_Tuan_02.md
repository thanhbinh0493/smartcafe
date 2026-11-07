# BIÊN BẢN HỌP TUẦN 02

## 1. THÀNH PHẦN
| Thành viên | Vai trò | Có mặt |
|:---|:---|:---:|
| Nguyễn Thanh Bình (A) | PM / Team Lead (chủ trì) | ✔ |
| Nguyễn Trường Thiên (B) | Backend Developer | ✔ |
| Lê Minh Sơn (C) | AI Specialist | ✔ |
| Ngô Duy Đô (D) | Tester / QA, thư ký | ✔ |
| Nguyễn Quang Tú (E) | Frontend Developer | ✔ |

## 2. NGÀY HỌP
Tuần 02 (28/09/2026 – 04/10/2026). Hình thức: họp nhóm. Thư ký: Ngô Duy Đô (D).

## 3. NỘI DUNG
| Mã | Ngày | Nội dung thay đổi / thảo luận | Lý do | Ảnh hưởng (tài liệu, module, người) | Người đề xuất |
|:---|:---|:---|:---|:---|:---|
| CR-07 | 29/09/2026 | Sơ đồ vẽ bằng **PlantUML**, xuất PNG để chèn báo cáo | Quản lý được dạng văn bản, ký hiệu UML chuẩn | Thư mục `diagrams/` – A, D | Nguyễn Thanh Bình (A) |
| CR-08 | 30/09/2026 | Quy định quy trình: **mọi yêu cầu thay đổi được ghi vào biên bản họp tuần**; tạo CLAUDE.md cho dự án | Đảm bảo truy vết thay đổi, phục vụ mục XI.1 của kế hoạch | CLAUDE.md, thư mục `Bien_ban_hop/` – A, D | Nguyễn Thanh Bình (A) |
| CR-09 | 01/10/2026 | **Bỏ hẳn IoT** (máy pha chế giả lập). Đổi tên đề tài thành "...(Tích hợp AI và QR)". Vấn đề P7 được giải quyết bằng **màn hình hàng đợi pha chế**: hiển thị món, bàn, giờ gọi, ghi chú, **sắp theo thời gian gọi**; pha chế bấm Bắt đầu / Xong | Máy pha có kết nối ít mẫu trên thị trường; khó tùy biến món mới và áp dụng cho toàn bộ chi nhánh; phần lớn đồ uống pha tay | Pham_Vi_Du_An.md, Project_Plan.md (vai trò C, task V.3), II.1, II.2 (Mục 3), III.1 (bỏ 4 UC IoT), III.2, IV.1 (bỏ 3 bảng), IV.2 (W04 vẽ lại), IV.3, schema.sql – B, C, E | Nguyễn Thanh Bình (A) |

## 4. HÌNH ẢNH / VIDEOS
(Bổ sung ảnh chụp buổi họp nếu có.)

## 5. KẾT LUẬN
**Quyết định:**
- Thông qua CR-07: Sơ đồ vẽ bằng PlantUML, xuất PNG để chèn báo cáo.
- Thông qua CR-08: Quy định quy trình: mọi yêu cầu thay đổi được ghi vào biên bản họp tuần; tạo CLAUDE.md cho dự án.
- Thông qua CR-09: Bỏ hẳn IoT (máy pha chế giả lập).

**Việc cần làm:**
| Việc | Người phụ trách | Hạn |
|:---|:---|:---|
| Phân tích yêu cầu phi chức năng (29 NFR) & mô hình dữ liệu khái niệm | Ngô Duy Đô | 08/10/2026 |
| Thiết kế CSDL: ERD, lược đồ quan hệ 18 bảng (schema.sql) | Nguyễn Trường Thiên | 13/10/2026 |
