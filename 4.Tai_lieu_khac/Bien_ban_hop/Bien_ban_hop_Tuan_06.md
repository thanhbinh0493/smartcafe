# BIÊN BẢN HỌP TUẦN 06

## 1. THÀNH PHẦN
| Thành viên | Vai trò | Có mặt |
|:---|:---|:---:|
| Nguyễn Thanh Bình (A) | PM / Team Lead (chủ trì) | ✔ |
| Nguyễn Trường Thiên (B) | Backend Developer | ✔ |
| Lê Minh Sơn (C) | AI Specialist | ✔ |
| Ngô Duy Đô (D) | Tester / QA, thư ký | ✔ |
| Nguyễn Quang Tú (E) | Frontend Developer | ✔ |

## 2. NGÀY HỌP
Tuần 06 (26/10/2026 – 01/11/2026). Hình thức: họp nhóm. Thư ký: Ngô Duy Đô (D).

## 3. NỘI DUNG
| Mã | Ngày | Nội dung thay đổi / thảo luận | Lý do | Ảnh hưởng (tài liệu, module, người) | Người đề xuất |
|:---|:---|:---|:---|:---|:---|
| CR-34 | 28/10/2026 | Chốt P15: pha chế "Hoàn tác" món cuối cùng (đơn đã "Có thể lấy") thì **đơn quay lại "Đang pha chế"** (READY → PREPARING, ghi lịch sử, khách thấy lại "Đang pha"). Duyệt kết quả F3, gộp F2 + F3 vào nhánh `main` (local) | Bấm nhầm "Xong" là thao tác hay gặp; nếu không cho hoàn tác thì khách được báo "Có thể lấy" khi đồ chưa pha xong | README thiết kế (D30), III.1 UC18, biểu đồ trạng thái đơn (`III_state_don_hang.puml` + PNG), IV.3; biên bản kiểm thử F3 Mục 7; module bar (đã cài ở F3); B, E | Nguyễn Thanh Bình (A) |
| CR-35 | 29/10/2026 | Chốt P16: **không thu thập tên khách**, thành viên chỉ định danh bằng số điện thoại đã xác thực OTP; bỏ cột `customers.name`, lời chào "Xin chào – X điểm". Duyệt kết quả F4 (84/84 đạt), gộp F4 vào `main` (local) | Số điện thoại đã đủ để tích điểm và gợi ý món; ít dữ liệu cá nhân hơn (NFR-S7) | README thiết kế (D31, P16), `schema.sql`, IV.1, ERD + sơ đồ data model, SD01, wireframe W01 (`.puml` + PNG), III.1 UC02, III.2, IV.2, IV.3; migration `0003`; module customer, frontend W01; biên bản kiểm thử F4 Mục 7; B, C, E | Nguyễn Thanh Bình (A) |
| CR-36 | 30/10/2026 | Duyệt kết quả F5 (53/53 đạt), gộp F5 + D31 vào `main` (local, chưa đẩy GitHub) | F5 đạt đủ điều kiện theo D25 | Nhánh `main`, `feature/f6-quan-tri`; module admin (backend + 7 màn hình Web Admin), `/ws/menu`; biên bản kiểm thử F6; B, E, D | Nguyễn Thanh Bình (A) |
| CR-37 | 31/10/2026 | Duyệt kết quả F6 – Quản trị (230/230 đạt), gộp F6 vào `main` (local) | F6 đạt đủ điều kiện theo D25 | Nhánh `main`, `feature/f7-ai-goi-y`; IV.2, IV.3 (API quản trị); biên bản kiểm thử F7; C, B, E, D | Nguyễn Thanh Bình (A) |
| CR-38 | 31/10/2026 | Chốt P17–P20 cho F7: dữ liệu lịch sử `seed_orders` **tự nạp khi khởi động** + SĐT demo 0901000001 (D32); FP-Growth dùng **mlxtend** (D33); thêm `recommendation_log_id` vào API đặt đơn (D34); thời tiết **giả lập mặc định**, API key tùy chọn (D35) | Theo phương án khuyến nghị: demo được ngay chế độ thành viên, đúng II.2, đo được hiệu quả gợi ý, không phụ thuộc mạng / key khi demo | README thiết kế (D32–D35, P17–P20), II.2 Mục 2.3–2.5, IV.3; `start.sh`, Dockerfile / requirements, `.env.example`; module recommend, API đặt đơn; C, B, E | Nguyễn Thanh Bình (A) |
| CR-39 | 31/10/2026 | Duyệt kết quả F7 – AI gợi ý món (71/71 đạt), gộp F7 vào `main` (local) và code F8 – Báo cáo ngày & dashboard. Phát sinh 2 đề xuất chờ chốt: P21 (bù báo cáo khi khởi động), P22 (cách gộp số liệu "Tất cả chi nhánh") | F7 đạt đủ điều kiện theo D25; laptop demo thường tắt lúc 00:05 | Nhánh `main`, `feature/f8-bao-cao`; README thiết kế (P21, P22), IV.1, IV.2, IV.3; module report, W08; biên bản kiểm thử F8; B, E, D | Nguyễn Thanh Bình (A) |
| CR-40 | 01/11/2026 | Chốt P21: **tự tính bù báo cáo ngày còn thiếu khi backend khởi động** (D36). Chốt P22: dashboard "Tất cả chi nhánh" **giữ cách gộp từ bảng báo cáo** (tỉ lệ món từ gợi ý trung bình theo số đơn, top 5 gộp từ top 5 từng chi nhánh) (D37). Duyệt kết quả F8 (41/41 đạt), gộp F8 vào `main` (local) – hoàn tất giai đoạn Lập trình F0 → F8 | Laptop demo thường tắt lúc 00:05; giữ dashboard chỉ đọc bảng báo cáo, sai lệch nhỏ chấp nhận được | README thiết kế (D36, D37, P21, P22), IV.1; biên bản kiểm thử F8 Mục 7–8; README gốc, README mã nguồn; nhánh `main`; B, E | Nguyễn Thanh Bình (A) |
| CR-41 | 01/11/2026 | Bắt đầu giai đoạn VI – Kiểm thử hệ thống: kịch bản xuyên luồng F1 → F8 trên nhiều thiết bị + kiểm thử toàn bộ yêu cầu phi chức năng (hiệu năng, bảo mật, độ tin cậy, khả dụng, bảo trì); bộ test case lưu cùng các biên bản kiểm thử luồng trong `1.Bao_cao/Kiem_thu/`; bổ sung script sao lưu / khôi phục CSDL (NFR-R5) | Đã xong F0 → F8; theo Project_Plan giai đoạn VI | Kế hoạch + biên bản kiểm thử hệ thống; `system_test/`, `backend/tests/st/`, `scripts/backup_db.ps1`; D, B, E | Nguyễn Thanh Bình (A) |

## 4. HÌNH ẢNH / VIDEOS
(Bổ sung ảnh chụp buổi họp nếu có.)

## 5. KẾT LUẬN
**Quyết định:**
- Thông qua CR-34: hoàn tác món cuối đưa đơn từ "Có thể lấy" về "Đang pha chế" (D30); F2, F3 được duyệt, gộp vào `main`.
- Thông qua CR-35: không thu thập tên khách, chỉ dùng SĐT (D31); F4 được duyệt, gộp vào `main`.
- Thông qua CR-36: F5 được duyệt, gộp vào `main`.
- Thông qua CR-37: F6 được duyệt, gộp vào `main`.
- Thông qua CR-38: dữ liệu lịch sử tự nạp + SĐT demo (D32), mlxtend (D33), `recommendation_log_id` (D34), thời tiết giả lập mặc định (D35).
- Thông qua CR-39: F7 được duyệt, gộp vào `main`; hoàn thiện F8.
- Thông qua CR-40: tự bù báo cáo khi khởi động (D36), giữ cách gộp số liệu "Tất cả chi nhánh" (D37); F8 được duyệt, gộp vào `main` – hoàn tất lập trình F0 → F8.
- Thông qua CR-41: bắt đầu giai đoạn VI – kiểm thử hệ thống; bổ sung script sao lưu / khôi phục CSDL.

**Việc cần làm:**
| Việc | Người phụ trách | Hạn |
|:---|:---|:---|
| Chạy kiểm thử hệ thống (hiệu năng, bảo mật, giao diện, vận hành), log bug, fix bug, hồi quy F0 → F8 | Ngô Duy Đô, Nguyễn Trường Thiên, Nguyễn Quang Tú | 03/11/2026 |
| Viết Hướng dẫn sử dụng có ảnh chụp màn hình cho khách, pha chế, thu ngân, quản lý, quản trị viên | Ngô Duy Đô | 03/11/2026 |
| Cả nhóm đọc và thử lại các bước của Hướng dẫn sử dụng trên máy demo | Cả nhóm | 05/11/2026 |
| Rà soát, đồng bộ tài liệu II–VII với mã nguồn: thuật ngữ, quyết định D1–D41, sơ đồ PNG, bảng phân công, kế hoạch | Nguyễn Thanh Bình, Ngô Duy Đô | 06/11/2026 |
| Định dạng và hoàn thiện các tài liệu nộp theo mẫu môn học (thiết kế, biên bản kiểm thử, HDSD, biên bản họp) | Ngô Duy Đô | 09/11/2026 |
