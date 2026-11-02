# CLAUDE.md – Đồ án QLDAPM Nhóm 8

## Dự án
**SmartCafe – Phần mềm quản lý chuỗi quán cà phê thông minh (Tích hợp AI và QR)** – đồ án môn Quản lý dự án phần mềm, PTIT.
- Thời gian: 21/09/2026 → 21/12/2026 (12 tuần + tuần nghiệm thu).
- Người dùng làm việc với Claude là **Thành viên A – PM / Team Lead**.
- Nhân sự: A (PM, BA) · B (Backend: API, DB) · C (AI, hỗ trợ Backend) · D (Tester/QA, tài liệu) · E (Frontend: Web Admin, QR Order).

## Tài liệu nguồn (đọc trước khi làm)
| File | Nội dung |
|:---|:---|
| [1.Bao_cao/Project_Plan.md](1.Bao_cao/Project_Plan.md) | Kế hoạch, WBS, phân công, timeline 12 giai đoạn |
| [1.Bao_cao/Pham_Vi_Du_An.md](1.Bao_cao/Pham_Vi_Du_An.md) | Phạm vi in-scope / out-of-scope, tính năng cốt lõi |
| [1.Bao_cao/Thiet_ke_he_thong/README.md](1.Bao_cao/Thiet_ke_he_thong/README.md) | Mục lục thiết kế II–IV, **các quyết định đã chốt (D1…)** và bảng **Vấn đề mở (P…)** |
| [4.Tai_lieu_khac/Bien_ban_hop/](4.Tai_lieu_khac/Bien_ban_hop/) | Biên bản họp hằng tuần |
| [2.San_pham/smartcafe/README.md](2.San_pham/smartcafe/README.md) | **Mã nguồn**: cách chạy, tài khoản mẫu, chạy test, tiến độ theo luồng F0–F8 |
| [1.Bao_cao/Kiem_thu/README.md](1.Bao_cao/Kiem_thu/README.md) | Quy ước + danh sách **biên bản kiểm thử** theo luồng |

## Quyết định đã chốt (tóm tắt – chi tiết ở README thiết kế)
- Stack: **Python FastAPI + React (Vite) + PostgreSQL 16**, realtime bằng WebSocket, Docker Compose.
- Menu chung toàn chuỗi + chi nhánh đặt giá riêng / bật tắt hết hàng. **Khuyến mãi đơn giản** (giá KM theo món, có thời hạn, toàn chuỗi hoặc 1 chi nhánh), **chỉ Quản trị viên** được tạo.
- Quét QR xong có **2 lựa chọn**: ẩn danh, hoặc nhập SĐT + **OTP giả lập** để **tích điểm** (1 điểm / 10.000đ, 1 điểm = 100đ; chỉ tích và xem, chưa đổi điểm). Phiên thành viên **1 giờ**. **Không lưu định danh thiết bị.**
- AI = **gợi ý món**: ẩn danh thì theo bán chạy + KM + món mới; thành viên thì theo sở thích + món tương tự; thời tiết là yếu tố phụ; "thường gọi kèm" bằng FP-Growth.
- Thanh toán **trả trước, giả lập**. Quy tắc tự hủy đơn chưa thanh toán sau 15 phút chỉ cần mô tả.
- **Chỉ gọi món qua QR** (không có POS tại quầy). Luồng xử lý đơn chỉ gồm Khách + Pha chế: pha chế làm theo hàng đợi (sắp theo giờ gọi), bấm Bắt đầu / Xong, giao đồ và bấm "Đã giao". **Thu ngân không nằm trong luồng**, chỉ hỗ trợ khách (tra cứu, hủy & hoàn tiền).
- **Dashboard bán hàng** đơn giản, số liệu tự tổng hợp hằng ngày lúc 00:05 (bảng `daily_sales_reports`).
- **Không có IoT** (đã bỏ).
- Code theo luồng **F0 → F8** (D26): F0 Nền tảng, F1 QR & menu, F2 Đặt món & thanh toán, F3 Màn hình Bar, F4 OTP & tích điểm, F5 Thu ngân, F6 Quản trị, F7 AI gợi ý, F8 Báo cáo. Môi trường demo: Docker Desktop local trên laptop (D24).

## Code & kiểm thử (D25)
- Mã nguồn: `2.San_pham/smartcafe/` (`backend/` FastAPI, `frontend/` React+Vite+TS+Tailwind, `docker-compose.yml`).
- **Mỗi luồng bắt buộc**: test tự động (pytest trên PostgreSQL thật + Vitest) **và** biên bản kiểm thử `1.Bao_cao/Kiem_thu/Bien_ban_kiem_thu_F<n>_<Ten>.md` theo mẫu trong `1.Bao_cao/Kiem_thu/README.md` (mã TC `F<n>-xx`, `F<n>-FE-xx`, `SM-xx`; lỗi `BUG-F<n>-xx`; log ở `logs/`, ảnh ở `img/`). Lỗi sửa xong phải có test hồi quy. Chỉ sang luồng sau khi luồng trước "Đạt" và người dùng duyệt.
- Môi trường máy: Docker tại `D:\Docker` (thêm `D:\Docker\DockerDesktop\resources\bin` vào PATH của phiên nếu cần); Python 3.11 gọi bằng `py -3.11` (venv backend: `backend\.venv`); Node 24 ở `D:\Dev\nodejs`. Mạng Wi-Fi nhà có thể mất IPv4 (dùng 4G khi tải gói).
- Lưu ý kỹ thuật: `alembic.ini` chỉ ASCII (Windows đọc cp1252); sắp xếp tên tiếng Việt dùng `COLLATE "vi-VN-x-icu"` (postgres alpine so sánh theo byte); chụp ảnh giao diện mobile bằng Playwright + Edge (`channel="msedge"`), không dùng `msedge --screenshot` (bị cắt lề).

## Quy tắc làm việc
- Viết tài liệu bằng **tiếng Việt có dấu**.
- **Làm rõ trước khi làm**: không tự quyết các thành phần quan trọng (phạm vi, công nghệ, quy tắc nghiệp vụ, cấu trúc dữ liệu). Hỏi người dùng, đưa phương án khuyến nghị.
- Sơ đồ dùng **PlantUML**: mã nguồn ở `diagrams/src/*.puml`, xuất PNG ra `diagrams/png/`. Dùng `!pragma layout smetana` cho sơ đồ cần layout (máy không có Graphviz), không dùng emoji trong sơ đồ (render ra ô vuông). Lệnh render ở README thiết kế. `plantuml.jar` không nằm trong repo, cần tải về (Java 8 có sẵn).
- Sửa file hàng loạt bằng script Python: **viết script ra file** (công cụ Write, UTF-8) rồi chạy, **không** truyền tiếng Việt qua heredoc của shell (Git Bash trên Windows có thể đổi bảng mã làm chuỗi không khớp). Sao lưu trước khi chạy.
- **Vấn đề mở / đề xuất chờ chốt** chỉ được theo dõi ở **một nơi**: bảng "Vấn đề mở (Open Issues)" trong README thiết kế. Đề xuất mới thì thêm dòng P.. "Đang mở"; khi người dùng chốt thì chuyển sang "Đã chốt → D..", thêm dòng D.. vào bảng quyết định và ghi CR vào biên bản tuần.
- Khi một quyết định thay đổi, cập nhật **mọi tài liệu bị ảnh hưởng** (README thiết kế, các file II–IV, `schema.sql`, `.puml` + render lại PNG) để giữ nhất quán.

## BẮT BUỘC: Ghi biên bản họp cho mọi yêu cầu thay đổi
Mọi **yêu cầu thay đổi / quyết định** của người dùng (đổi phạm vi, thiết kế, công nghệ, phân công, timeline, chốt/bác đề xuất…) được coi là nội dung đã thống nhất trong **cuộc họp nhóm của tuần đó** và phải được ghi vào biên bản.

**Cách tính tuần:** tuần dự án, thứ 2 → Chủ nhật, **Tuần 1 bắt đầu 21/09/2026**.
Số tuần = `(ngày − 21/09/2026) // 7 + 1`. Ví dụ: 26/10–01/11/2026 = Tuần 6; 02/11–08/11 = Tuần 7.

**File:** `4.Tai_lieu_khac/Bien_ban_hop/Bien_ban_hop_Tuan_XX.md` (XX hai chữ số). Mỗi tuần một file; tuần không có thay đổi thì không tạo file.

**Quy trình (ngay trong lượt đó, không đợi cuối tuần):**
1. Xác định tuần theo ngày hiện tại. Nếu chưa có file tuần đó thì tạo từ mẫu bên dưới.
2. Thêm một dòng vào mục **3. Nội dung**, mã thay đổi tăng dần toàn dự án (`CR-01`, `CR-02`…; tra số cuối ở các biên bản trước).
3. Cập nhật mục **5. Kết luận** (quyết định + việc cần làm, người phụ trách, hạn).
4. Cuối câu trả lời, báo ngắn: "Đã ghi vào biên bản Tuần XX (CR-YY)."
- Câu hỏi thuần túy, giải thích, hoặc việc thực hiện theo quyết định đã có **không** phải yêu cầu thay đổi → không ghi.
- Không chắc một yêu cầu có phải thay đổi không → hỏi người dùng.
- Mục "Thành phần" dùng ký hiệu A–E như Project_Plan.md (người dùng có thể bổ sung tên thật sau).

**Mẫu biên bản** (theo mẫu `4.Tai_lieu_khac/Group_X_Bien_ban_hop_Lan1.docx`):
```markdown
# BIÊN BẢN HỌP TUẦN XX

## 1. THÀNH PHẦN
| Thành viên | Vai trò | Có mặt |
|:---|:---|:---:|
| Thành viên A | PM / Team Lead (chủ trì) | ✔ |
| Thành viên B | Backend Developer | ✔ |
| Thành viên C | AI Specialist | ✔ |
| Thành viên D | Tester / QA, thư ký | ✔ |
| Thành viên E | Frontend Developer | ✔ |

## 2. NGÀY HỌP
Tuần XX (dd/mm/yyyy – dd/mm/yyyy). Hình thức: họp nhóm. Thư ký: Thành viên D.

## 3. NỘI DUNG
| Mã | Ngày | Nội dung thay đổi / thảo luận | Lý do | Ảnh hưởng (tài liệu, module, người) | Người đề xuất |
|:---|:---|:---|:---|:---|:---|

## 4. HÌNH ẢNH / VIDEOS
(Bổ sung ảnh chụp buổi họp nếu có.)

## 5. KẾT LUẬN
**Quyết định:**
-
**Việc cần làm:**
| Việc | Người phụ trách | Hạn |
|:---|:---|:---|
```
Cuối kỳ (giai đoạn IX/XI) các biên bản `.md` sẽ được xuất sang `.docx` theo mẫu trên.
