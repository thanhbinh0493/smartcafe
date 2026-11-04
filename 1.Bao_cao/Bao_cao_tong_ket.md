# BÁO CÁO TỔNG KẾT DỰ ÁN

| Thông tin | Nội dung |
|:---|:---|
| Dự án | SmartCafe – Phần mềm quản lý chuỗi quán cà phê thông minh (tích hợp AI và QR) |
| Môn học | Quản lý dự án phần mềm – Nhóm 8 |
| Thời gian dự án | 21/09/2026 → 16/11/2026 (8 tuần, D41) |
| Ngày lập báo cáo | 10/11/2026 (giai đoạn IX – Báo cáo tổng thể dự án) |
| Người lập | Thành viên A – Nguyễn Thanh Bình (PM); cả nhóm review |
| Cấu trúc | Theo mẫu báo cáo môn học `Nhom_X_Bao_cao.docx` (10 phần). Phần IV, VII, VIII viết theo quyết định D43 (CR-48) |

# PHẦN I: GIỚI THIỆU CHUNG VỀ NHÓM

## 1. Các thành viên Nhóm 8

| Ký hiệu | Họ và tên | Mã sinh viên | Vai trò trong dự án |
|:---|:---|:---|:---|
| A | Nguyễn Thanh Bình | [mã SV] | Project Manager / Team Lead, phân tích nghiệp vụ (BA) |
| B | [Thành viên B] | [mã SV] | Backend Developer: API, cơ sở dữ liệu |
| C | [Thành viên C] | [mã SV] | AI Specialist: gợi ý món, OTP & tích điểm, dữ liệu mẫu; hỗ trợ backend |
| D | [Thành viên D] | [mã SV] | Tester / QA, thư ký các buổi họp, tài liệu |
| E | [Thành viên E] | [mã SV] | Frontend Developer: Web Admin, giao diện QR Order |

*Họ tên và mã sinh viên của các thành viên B–E điền theo `1.Bao_cao/Xuat_docx/thong_tin_bia.json`.*

## 2. Phân công các thành viên

| Thành viên | Công việc chính (theo bảng phân công `Nhom_8_Phan_cong.xlsx`) | Review / duyệt |
|:---|:---|:---|
| A | Phạm vi, WBS, kế hoạch; Use Case + Sequence (III.1); chủ trì họp, chốt 44 quyết định (D1–D44) và 49 yêu cầu thay đổi (CR-01 → CR-49); duyệt kết quả từng luồng; chuẩn hóa tài liệu; báo cáo tổng kết; diễn tập demo | Review thiết kế CSDL, kiến trúc & API, khảo sát; duyệt mọi biên bản kiểm thử |
| B | Thiết kế CSDL 18 bảng (IV.1), kiến trúc & API (IV.3); backend các luồng F0 → F8; sửa lỗi kiểm thử hệ thống (cache API đọc, WebSocket) | Review nghiên cứu công nghệ, Use Case |
| C | Nghiên cứu công nghệ (II.2); AI gợi ý món 2 chế độ + FP-Growth (F7); OTP giả lập, tích điểm (F4); script sinh dữ liệu lịch sử `seed_orders.py`, đánh giá Hit Rate@5 | Review NFR & data model (III.2) |
| D | Khảo sát quy trình (II.1); NFR & data model (III.2); lập 10 biên bản kiểm thử, kế hoạch + kiểm thử hệ thống; Hướng dẫn sử dụng; thư ký biên bản họp; xuất tài liệu Word; biên bản nghiệm thu | Review thiết kế giao diện (IV.2) |
| E | Thiết kế giao diện, wireframe W00–W08 (IV.2); frontend QR Order + Web Admin các luồng F1 → F8; slide bảo vệ; diễn tập demo | Review chung các hạng mục "Cả nhóm" |

Không có thành viên nào vắng họp hay không nộp phần việc được giao: mọi buổi họp trong biên bản đều ghi đủ 5 thành viên có mặt; mọi hạng mục trong bảng phân công đến 10/11/2026 đều "Hoàn thành" hoặc đang làm đúng hạn.

## 3. Quá trình họp và làm việc của nhóm
- **Hình thức:** họp nhóm hằng tuần (thứ Hai – Chủ nhật tính là 1 tuần dự án, Tuần 1 bắt đầu 21/09/2026); trao đổi hằng ngày qua kho mã nguồn chung trên GitHub (CR-30) và nhóm chat.
- **Quy tắc biên bản (CR-08):** mọi yêu cầu thay đổi / quyết định đều ghi ngay vào biên bản họp của tuần đó (mã CR tăng dần toàn dự án); tuần không có thay đổi thì không lập biên bản.
- **Thống kê:** 2 biên bản tuần có thay đổi (Tuần 06: CR-01 → CR-25; Tuần 07: CR-26 → CR-49), tổng cộng **49 yêu cầu thay đổi**, sinh ra **44 quyết định** (D1–D44) và **25 vấn đề mở** (P1–P25) – tất cả đã được chốt hoặc hủy, không còn vấn đề mở.
- **Hình ảnh buổi họp:** *(bổ sung ảnh chụp các buổi họp – mục 4 của mỗi biên bản họp).*

# PHẦN II: GIỚI THIỆU TỔNG QUAN VỀ DỰ ÁN

## 1. Tên dự án
**SmartCafe – Phần mềm quản lý chuỗi quán cà phê thông minh (tích hợp AI và QR).** Tên ban đầu có cả IoT; nhóm bỏ phần IoT ở CR-09 (D8) và đổi tên đề tài.

## 2. Mục đích và mục tiêu
- **Mục đích:** giúp một chuỗi quán cà phê nhỏ (3 chi nhánh) bỏ khâu gọi món tại quầy: khách quét mã QR tại bàn, xem menu, đặt và thanh toán trước trên điện thoại; quầy Bar làm theo hàng đợi; trụ sở quản lý menu, giá, khuyến mãi tập trung và xem báo cáo hằng ngày.
- **Mục tiêu sản phẩm (đo được):**
  - Khách đặt 1 đơn 2 món trong ≤ 6 lần chạm (NFR-U2) – **đạt 5 lần chạm**.
  - Đơn mới lên màn hình Bar ≤ 2 giây (NFR-P4) – **đạt ~0,05 giây**.
  - AI gợi ý món theo 2 chế độ có giải thích lý do; đánh giá offline Hit Rate@5 – **thành viên 48,9% so với 20,4% của cách chỉ gợi ý món bán chạy**.
  - Đáp ứng toàn bộ 29 yêu cầu phi chức năng (III.2) – **đạt 29/29**.
- **Mục tiêu học tập:** áp dụng đầy đủ quy trình quản lý dự án phần mềm (lập kế hoạch, phân tích, thiết kế, lập trình, kiểm thử, chuyển giao, kiểm soát thay đổi) trong 8 tuần làm việc nhóm.

## 3. Phạm vi và quy mô
| Trong phạm vi | Ngoài phạm vi |
|:---|:---|
| Gọi món qua mã QR (ẩn danh hoặc thành viên bằng OTP giả lập), giỏ hàng, thanh toán trả trước giả lập, theo dõi đơn realtime | Gọi món tại quầy (POS), đặt bàn, giao hàng |
| Màn hình Bar: hàng đợi pha chế, Bắt đầu / Xong / Hoàn tác / Đã giao | IoT, máy pha chế kết nối (bỏ – D8) |
| Thu ngân hỗ trợ khách: tra cứu, hủy đơn & hoàn tiền giả lập | Cổng thanh toán, SMS thật |
| Quản trị: chi nhánh, nhân viên & phân quyền, danh mục, món, menu chi nhánh (giá riêng, hết hàng), bàn & mã QR, khuyến mãi | Voucher, combo, đổi điểm, kho nguyên liệu, chấm công |
| AI gợi ý món + "Thường gọi kèm" (FP-Growth); tích điểm | Ứng dụng di động cài đặt, bản demo trên cloud (D40) |
| Báo cáo ngày tự tổng hợp 00:05 + dashboard | Báo cáo realtime trong ngày |

**Quy mô:** 20 use case, 5 vai trò người dùng (khách, pha chế, thu ngân, quản lý chi nhánh, quản trị viên), 18 bảng CSDL, 50 API (gồm 3 kênh WebSocket), 9 luồng code F0 → F8; dữ liệu demo 3 chi nhánh × 20 bàn, 35 món, ~5.000 đơn lịch sử.

## 4. Các đơn vị liên quan
| Bên liên quan | Vai trò / mong đợi |
|:---|:---|
| Giảng viên môn Quản lý dự án phần mềm | Người hướng dẫn, đánh giá và nghiệm thu |
| Nhóm 8 (5 thành viên) | Đội dự án: lập kế hoạch, phân tích, thiết kế, xây dựng, kiểm thử, chuyển giao |
| Chuỗi quán cà phê (giả định: trụ sở + 3 chi nhánh Cầu Giấy, Hà Đông, Thanh Xuân) | Khách hàng của dự án; người dùng là quản trị viên, quản lý chi nhánh, pha chế, thu ngân |
| Khách của quán | Người dùng cuối của giao diện QR Order |
| Dịch vụ bên ngoài | OpenWeatherMap (tùy chọn, mặc định giả lập – D35); cổng thanh toán và SMS (giả lập) |

# PHẦN III: QUẢN LÝ VỀ LẬP KẾ HOẠCH DỰ ÁN

## 1. Kế hoạch tổng thể
Dự án chia 11 giai đoạn trong 8 tuần (D41). Bảng chi tiết từng hạng mục, người thực hiện, người review, ngày bắt đầu – kết thúc – review: [Project_Plan.md](Project_Plan.md) và `2.San_pham/Nhom_8_Phan_cong.xlsx`.

| Giai đoạn | Thời gian | Kết quả chính | Trạng thái (10/11) |
|:---|:---|:---|:---|
| I. Lập kế hoạch | 21/09 – 24/09 | Phạm vi, WBS, phân công | Hoàn thành |
| II. Khảo sát & nghiên cứu công nghệ | 25/09 – 01/10 | Quy trình hiện trạng / đề xuất (II.1), công nghệ (II.2) | Hoàn thành |
| III. Phân tích | 02/10 – 09/10 | 20 use case, 6 sequence, 29 NFR, data model | Hoàn thành |
| IV. Thiết kế | 10/10 – 19/10 | CSDL 18 bảng, 9 wireframe, kiến trúc & 50 API | Hoàn thành |
| V. Lập trình (F0 → F8) | 20/10 – 31/10 | 9 luồng, mỗi luồng có test + biên bản kiểm thử | Hoàn thành |
| VI. Kiểm thử hệ thống | 01/11 – 03/11 | 66 ca hệ thống, hồi quy 664 ca, 6 lỗi đã sửa | Hoàn thành |
| VII. Đào tạo & chuyển giao | 03/11 – 05/11 | Hướng dẫn sử dụng 33 ảnh | Hoàn thành |
| VIII. Tài liệu dự án (chuẩn hóa) | 04/11 – 09/11 | Đồng bộ tài liệu – mã nguồn; 5 bộ hồ sơ Word | Hoàn thành |
| IX. Báo cáo tổng thể | 10/11 – 12/11 | Báo cáo này | Đang làm |
| X. Slide, biên bản họp, demo | 12/11 – 15/11 | Slide bảo vệ, diễn tập demo | Chuẩn bị |
| XI. Biên bản nghiệm thu | 16/11 | Biên bản nghiệm thu | Chuẩn bị |

**Mốc kiểm soát (milestone):** M1 chốt phạm vi & thiết kế (19/10) → M2 xong 9 luồng, mỗi luồng "Đạt" (31/10) → M3 kiểm thử hệ thống "Đạt" (03/11) → M4 hồ sơ tài liệu hoàn chỉnh (09/11) → M5 nghiệm thu (16/11).

## 2. Chi tiết kế hoạch cho từng bộ phận, nhân sự
- **Phân tích – thiết kế (A, B, D, E):** mỗi tài liệu có 1 người thực hiện và 1 người review khác vai trò (VD CSDL: B làm, A review; giao diện: E làm, D review).
- **Lập trình (B, C, E; D kiểm thử):** code theo **luồng nghiệp vụ** thay vì theo tầng (D25, D26): mỗi luồng gồm API + giao diện + test tự động (pytest trên PostgreSQL thật, Vitest) + kiểm thử khói + biên bản kiểm thử; chỉ sang luồng sau khi luồng trước "Đạt" và PM duyệt.
- **Kiểm thử (D; B, E sửa lỗi):** kế hoạch kiểm thử hệ thống, 5 bộ script kiểm thử tự động trên bản chạy thật, lỗi nào sửa xong cũng có test hồi quy.
- **Tài liệu (A, D):** mọi tài liệu viết bằng Markdown trong kho (một nguồn), xuất Word tự động theo mẫu môn học (D42).

## 3. Quản lý thay đổi và tiến độ
- **Kiểm soát thay đổi:** 49 CR, mỗi CR ghi ngày, nội dung, lý do, ảnh hưởng (tài liệu, module, người) và người đề xuất. Quyết định đã chốt ghi bảng D…; đề xuất chờ chốt ghi một nơi duy nhất – bảng "Vấn đề mở" (CR-20).
- **Điều chỉnh kế hoạch lớn:** bỏ IoT, thêm khuyến mãi / tích điểm / OTP (CR-09 → CR-14, 01/11); kết thúc dự án dời về 16/11 và bỏ giai đoạn rủi ro riêng (CR-45, D41) – phần rủi ro trình bày ở Phần VIII.

# PHẦN IV: QUẢN LÝ CHI PHÍ DỰ ÁN

Dự án là đồ án môn học nên **không phát sinh chi phí tiền mặt**. Để thực hành quản lý chi phí, nhóm lập dự toán theo **công lao động × đơn giá giả định** (D44, CR-49). Mọi con số dưới đây là **giả định**, không phải chi phí thực trả.

## 1. Giả định lập dự toán
| Giả định | Giá trị | Ghi chú |
|:---|:---|:---|
| Thời gian làm việc | Bán thời gian **4 giờ/ngày = 0,5 ngày công** cho mỗi ngày trong khoảng thực hiện của hạng mục | Sinh viên vừa học vừa làm dự án |
| Công trực tiếp | Theo ngày bắt đầu – kết thúc của từng hạng mục trong `Nhom_8_Phan_cong.xlsx`, chia cho mọi người thực hiện của hạng mục | "Cả nhóm" = 5 người |
| Công review | 0,25 ngày công cho mỗi hạng mục người đó review (review "Cả nhóm": 0,125 ngày công / người) | |
| Họp nhóm | 8 buổi × 1 giờ = 1 ngày công / người; thư ký (D) thêm 2 ngày công lập biên bản | |
| Đơn giá | PM (A): **800.000đ / ngày công**; lập trình viên, AI, tester (B, C, D, E): **600.000đ / ngày công** | Mức junior / thực tập tại Hà Nội, do nhóm giả định |
| Hạ tầng, phần mềm | **0đ**: laptop cá nhân; phần mềm mã nguồn mở (Python, FastAPI, React, PostgreSQL, Docker Desktop bản cá nhân, PlantUML); không thuê cloud (D40); OTP, thanh toán, thời tiết dùng giả lập | |
| Dự phòng | 10% tổng chi phí nhân công | Rủi ro trễ hạn, làm lại |

## 2. Tổng dự toán
| Hạng mục | Chi phí (đ) |
|:---|---:|
| Nhân công (90,25 ngày công) | 57.300.000 |
| Hạ tầng, phần mềm, dịch vụ ngoài | 0 |
| Dự phòng 10% | 5.730.000 |
| **Tổng dự toán** | **63.030.000** |

## 3. Chi tiết dự toán theo nhân sự
| Thành viên | Công trực tiếp | Review | Họp + biên bản | Tổng ngày công | Đơn giá (đ) | Thành tiền (đ) |
|:---|---:|---:|---:|---:|---:|---:|
| A – PM | 9,50 | 5,25 | 1,00 | 15,75 | 800.000 | 12.600.000 |
| B – Backend | 21,50 | 1,25 | 1,00 | 23,75 | 600.000 | 14.250.000 |
| C – AI | 10,00 | 1,00 | 1,00 | 12,00 | 600.000 | 7.200.000 |
| D – Tester / QA | 11,50 | 1,00 | 3,00 | 15,50 | 600.000 | 9.300.000 |
| E – Frontend | 21,50 | 0,75 | 1,00 | 23,25 | 600.000 | 13.950.000 |
| **Tổng** | **74,00** | **9,25** | **7,00** | **90,25** | | **57.300.000** |

## 4. Phân bổ công trực tiếp theo giai đoạn
| Giai đoạn | Ngày công | Tỉ lệ | Nhận xét |
|:---|---:|---:|:---|
| I. Lập kế hoạch | 2,0 | 2,7% | |
| II. Khảo sát & nghiên cứu | 5,5 | 7,4% | |
| III. Phân tích | 4,5 | 6,1% | |
| IV. Thiết kế | 6,5 | 8,8% | |
| V. Lập trình F0 → F8 | 36,0 | 48,6% | Chi phí lớn nhất; B và E mỗi người ~15 ngày công |
| VI. Kiểm thử hệ thống | 4,0 | 5,4% | Kiểm thử từng luồng đã tính trong V |
| VII. Đào tạo & chuyển giao | 5,5 | 7,4% | |
| VIII. Chuẩn hóa tài liệu | 4,5 | 6,1% | |
| IX. Báo cáo tổng thể | 1,5 | 2,0% | |
| X. Slide, demo | 3,5 | 4,7% | |
| XI. Nghiệm thu | 0,5 | 0,7% | |
| **Tổng** | **74,0** | **100%** | |

## 5. Kiểm soát chi phí
- **Chi phí thực tế bằng tiền: 0đ** – đúng dự toán hạ tầng; các quyết định giữ chi phí bằng 0: chạy local bằng Docker Desktop (D24), không làm bản cloud (D40), giả lập OTP / thanh toán / thời tiết (D12, D35).
- **Công thực tế so với kế hoạch:** giai đoạn V–VII hoàn thành sớm hơn kế hoạch (ghi chú "thực tế xong 02/11, 03/11" trong bảng phân công) nhờ làm theo luồng có test tự động, nên phần dự phòng 10% không phải dùng tới.

# PHẦN V: QUẢN LÝ NGUỒN NHÂN LỰC

## 1. Danh sách nhân sự tham gia dự án
Xem Phần I.1. Cơ cấu: 1 PM / BA, 1 Backend, 1 AI (kiêm hỗ trợ backend), 1 Tester / QA (kiêm thư ký, tài liệu), 1 Frontend.

## 2. Thông tin, kỹ năng và trách nhiệm từng nhân sự
| Thành viên | Kỹ năng sử dụng trong dự án | Trách nhiệm | Sản phẩm bàn giao |
|:---|:---|:---|:---|
| A | Phân tích nghiệp vụ, UML (PlantUML), lập kế hoạch, kiểm soát thay đổi | Ra quyết định phạm vi / thiết kế, điều phối, duyệt từng luồng | Phạm vi, kế hoạch, III.1, biên bản duyệt, báo cáo tổng kết |
| B | Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL, WebSocket, Docker | Thiết kế CSDL, API, backend; hiệu năng | IV.1, IV.3, `backend/` (~4.300 dòng mã + ~4.700 dòng test) |
| C | Hệ gợi ý, khai phá luật kết hợp (FP-Growth, mlxtend), pandas | Mô hình gợi ý, dữ liệu mẫu, đánh giá mô hình; OTP, tích điểm | II.2, `recommend/`, `seed_orders.py`, `evaluate_recommender.py` |
| D | Kiểm thử (pytest, Vitest, Playwright), viết tài liệu | Kế hoạch & biên bản kiểm thử, kiểm thử hệ thống, HDSD, biên bản họp | II.1, III.2, 10 biên bản kiểm thử, `system_test/`, HDSD |
| E | React, TypeScript, Tailwind CSS, Vite, thiết kế giao diện | Wireframe, giao diện QR Order + Web Admin, slide | IV.2, `frontend/` (~4.800 dòng mã + ~2.200 dòng test) |

## 3. Ma trận trách nhiệm (RACI) các hạng mục chính
R = thực hiện, A = chịu trách nhiệm phê duyệt, C = tham vấn, I = được thông báo.

| Hạng mục | A | B | C | D | E |
|:---|:---:|:---:|:---:|:---:|:---:|
| Phạm vi, kế hoạch | R/A | C | C | C | C |
| Use case, sequence | R/A | C | I | C | I |
| Thiết kế CSDL, API | A | R | C | I | C |
| Thiết kế giao diện | A | C | I | C | R |
| Backend F0 → F8 | A | R | R (F4, F7) | C | I |
| Frontend F1 → F8 | A | C | I | C | R |
| AI gợi ý món | A | C | R | C | C |
| Kiểm thử, biên bản kiểm thử | A | C | C | R | C |
| Hướng dẫn sử dụng | A | I | I | R | C |
| Báo cáo tổng kết | R/A | C | C | C | C |
| Slide, demo | A | C | C | C | R |

# PHẦN VI: QUÁ TRÌNH TRIỂN KHAI, THỰC THI DỰ ÁN

Chi tiết từng bước nằm trong các bộ hồ sơ đi kèm (Phần IX); phần này tóm tắt kết quả.

## 1. Khảo sát và thu thập thông tin
Khảo sát theo **mô hình giả định điển hình** của một chuỗi 3 chi nhánh kèm bộ câu hỏi phỏng vấn (CR-06): mô tả quy trình hiện trạng (gọi món tại quầy, menu giấy, khuyến mãi nhập tay từng chi nhánh) và các điểm nghẽn (xếp hàng giờ cao điểm, sai món, trụ sở không kiểm soát giá / khuyến mãi), từ đó đề xuất quy trình gọi món qua QR. Nghiên cứu công nghệ so sánh 6 phương án AI và quyết định loại bỏ IoT. *(Hồ sơ 1 – Chương II.1, II.2.)*

## 2. Phân tích
20 use case trên 3 phân hệ (QR Order, Quản trị, Vận hành quầy), ma trận phân quyền 4 vai trò nhân viên, đặc tả chi tiết các use case chính, biểu đồ trạng thái đơn hàng và 6 sequence diagram; 29 yêu cầu phi chức năng có cách đo cụ thể; mô hình dữ liệu khái niệm. *(Hồ sơ 1 – III.1, III.2.)*

## 3. Thiết kế
CSDL PostgreSQL 18 bảng / 9 kiểu ENUM (`schema.sql`), 9 wireframe màn hình (PlantUML Salt), kiến trúc client – server dạng modular monolith (FastAPI + React + PostgreSQL + WebSocket, Docker Compose), danh sách 50 API. *(Hồ sơ 1 – IV.1 → IV.3, Phụ lục B.)*

## 4. Lập trình
Code theo 9 luồng nghiệp vụ; mỗi luồng chỉ "Đạt" khi 100% ca kiểm thử đạt và không còn lỗi Nghiêm trọng / Cao (D25).

| Luồng | Nội dung | Ca kiểm thử | Lỗi phát hiện (đã sửa) |
|:---|:---|---:|---:|
| F0 | Nền tảng: Docker Compose, CSDL + Alembic, dữ liệu mẫu, đăng nhập, phân quyền | 48 | 2 |
| F1 | Quét QR → màn hình chào → menu chi nhánh | 57 | 1 |
| F2 | Giỏ hàng → đặt món → thanh toán giả lập → theo dõi đơn realtime | 67 | 2 |
| F3 | Màn hình Bar: hàng đợi, Bắt đầu / Xong / Hoàn tác / Đã giao | 76 | 2 |
| F4 | OTP giả lập, tích điểm, xem điểm | 84 | 3 |
| F5 | Thu ngân: tra cứu, hủy đơn & hoàn tiền | 53 | 1 |
| F6 | Quản trị: chi nhánh, nhân viên, danh mục, món, menu chi nhánh, bàn & QR, khuyến mãi | 230 | 1 |
| F7 | AI gợi ý món 2 chế độ + "Thường gọi kèm" (FP-Growth) | 71 | 4 |
| F8 | Báo cáo ngày (job 00:05) + dashboard | 41 | 1 |
| **Tổng** | | **727** | **17** |

**Quy mô mã nguồn:** backend ~4.300 dòng, frontend ~4.800 dòng, script dữ liệu / đánh giá ~1.000 dòng; test tự động ~8.500 dòng (pytest, Vitest, kiểm thử hệ thống). Kho mã nguồn: GitHub `thanhbinh0493/smartcafe` (CR-30).

## 5. Kiểm thử
- **Kiểm thử từng luồng:** 727 ca (Phần VI.4), độ bao phủ mã backend 99%, frontend 98,5%.
- **Kiểm thử hệ thống (giai đoạn VI):** 66 ca trên bản chạy thật – kịch bản "một ngày làm việc" xuyên luồng trên 5 trình duyệt cùng lúc, hiệu năng & tải, bảo mật (giả mạo JWT, phân quyền, SQL injection, XSS…), giao diện & độ tin cậy (mất mạng, AI lỗi, Safari / WebKit), vận hành (sao lưu – khôi phục). Phát hiện và sửa **6 lỗi** (BUG-ST-01 → 06); chạy lại toàn bộ 664 ca hồi quy đều đạt. **29/29 yêu cầu phi chức năng đạt.**
- *(Hồ sơ 2 – Hồ sơ kiểm thử.)*

## 6. Cài đặt và triển khai
- Toàn hệ thống chạy bằng một lệnh `docker compose up -d` (PostgreSQL, backend, frontend / Nginx) trên **laptop demo** (D24, D40); lần chạy đầu tự tạo CSDL, nạp dữ liệu mẫu và lịch sử ~5.000 đơn, học luật gợi ý, tính báo cáo 60 ngày.
- Demo bằng điện thoại thật qua Wi-Fi: đổi `PUBLIC_BASE_URL` thành IP laptop, in lại mã QR.
- Sao lưu / khôi phục CSDL trước mỗi buổi demo: `scripts/backup_db.ps1`, `restore_db.ps1` (NFR-R5).

## 7. Đào tạo và chuyển giao công nghệ
- **Hướng dẫn sử dụng** cho 5 vai trò (khách, pha chế, thu ngân, quản lý, quản trị viên), 33 ảnh chụp từ hệ thống thật, kèm khởi động hệ thống, chuẩn bị buổi demo, xử lý sự cố, câu hỏi thường gặp. *(Hồ sơ 3.)*
- **Chuyển giao kỹ thuật:** README mã nguồn (cách chạy, tài khoản mẫu, chạy test), Swagger `/docs` tự sinh, `.env.example`, toàn bộ test tự động chạy lại được.

# PHẦN VII: GIÁM SÁT, THEO DÕI VÀ KIỂM SOÁT DỰ ÁN

## 1. Nhật ký thực hiện dự án
Nhật ký dựa trên biên bản họp (49 CR) và lịch sử commit của kho mã nguồn.

| Thời điểm | Sự kiện chính | Nguồn |
|:---|:---|:---|
| 21/09 – 19/10 | Lập kế hoạch, khảo sát, phân tích, thiết kế (giai đoạn I–IV) | Bảng phân công |
| 28/10 (Tuần 06) | Chốt AI = gợi ý món, stack FastAPI + React + PostgreSQL, menu chung + giá chi nhánh, thanh toán trả trước giả lập, PlantUML | CR-01 → CR-07 |
| 01/11 (Tuần 06) | Bỏ IoT; thêm màn hình chào 2 lựa chọn, OTP giả lập, tích điểm, khuyến mãi, gợi ý 2 chế độ, dashboard báo cáo ngày; thu ngân chỉ hỗ trợ khách; quy tắc biên bản và nơi theo dõi vấn đề mở | CR-08 → CR-25 |
| 02/11 (Tuần 07) | Chốt môi trường demo local; quy trình code theo luồng + biên bản kiểm thử; thứ tự F0 → F8; kho GitHub chung; F0, F1, F2 đạt | CR-26 → CR-32 |
| 03/11 (Tuần 07) | F3 → F8 đạt và được duyệt; kiểm thử hệ thống đạt (cache API đọc, mô hình tải); Hướng dẫn sử dụng; chỉ demo trên laptop; kế hoạch kết thúc 16/11 | CR-33 → CR-45 |
| 04/11 (Tuần 07) | Đồng bộ tài liệu với mã nguồn; mẫu tài liệu nộp + 5 bộ hồ sơ Word; chốt cách viết phần chi phí / giám sát / rủi ro | CR-46 → CR-49 |
| 10/11 → 16/11 | Báo cáo tổng kết, slide, diễn tập demo, nghiệm thu | Kế hoạch |

## 2. Nhật ký giám sát chất lượng
Mỗi luồng / giai đoạn đi qua một **cổng kiểm soát**: test tự động 100% đạt → biên bản kiểm thử (Thành viên D lập) → PM duyệt (ghi CR) → gộp vào nhánh `main`.

| Cổng | Ngày duyệt | Kết quả kiểm thử | Hồi quy các luồng trước | Quyết định |
|:---|:---|:---|:---|:---|
| F0, F1 | 02/11 | 48 + 57 ca đạt | – | Sang F2 |
| F2, F3 | 03/11 | 67 + 76 ca đạt | 105 → 172 ca đạt | CR-34 |
| F4 | 03/11 | 84 ca đạt | 236 ca đạt | CR-35 |
| F5 | 03/11 | 53 ca đạt | 297 ca đạt | CR-36 |
| F6 | 03/11 | 230 ca đạt | 342 ca đạt | CR-37 |
| F7 | 03/11 | 71 ca đạt | 563 ca đạt | CR-39 |
| F8 | 03/11 | 41 ca đạt | 629 ca đạt | CR-40 |
| Kiểm thử hệ thống | 03/11 | 66 ca đạt | 664 ca đạt | CR-44 |

## 3. Chỉ số theo dõi
| Chỉ số | Kế hoạch | Thực tế (10/11) |
|:---|:---|:---|
| Tiến độ giai đoạn I–VIII | Xong trước 09/11 | Xong; giai đoạn V–VII xong sớm (02–03/11) |
| Ca kiểm thử đạt | 100% mỗi luồng | 727/727 + 66/66 hệ thống |
| Lỗi Nghiêm trọng / Cao còn mở | 0 | 0 (23 lỗi phát hiện, đã sửa hết, đều có test hồi quy) |
| Yêu cầu phi chức năng | 29/29 | 29/29 |
| Vấn đề mở chưa chốt | 0 trước khi nghiệm thu | 0 (P1–P25 đã chốt / hủy) |
| Tài liệu khớp mã nguồn | 100% | Danh sách API 50/50, CSDL 18/18 bảng, sơ đồ 15/15 lời gọi API (CR-46) |

## 4. Công cụ kiểm soát
- **Biên bản họp + mã CR** cho mọi thay đổi; **bảng quyết định D…** và **bảng vấn đề mở P…** duy nhất trong README thiết kế.
- **Git:** mỗi luồng một nhánh `feature/...`, chỉ gộp vào `main` sau khi duyệt.
- **Bảng phân công Excel** = bảng kế hoạch trong `Project_Plan.md` (sinh từ cùng một nguồn).

# PHẦN VIII: QUẢN LÝ RỦI RO CỦA DỰ ÁN

Thang đánh giá: Xác suất (Thấp / Trung bình / Cao) × Ảnh hưởng (Thấp / Trung bình / Cao).

## 1. Các rủi ro truyền thống
| Rủi ro | Xác suất | Ảnh hưởng | Biện pháp phòng ngừa / ứng phó | Kết quả |
|:---|:---|:---|:---|:---|
| Trễ tiến độ do vừa học vừa làm | Cao | Cao | Chia nhỏ theo luồng, mỗi luồng có tiêu chí "Đạt" rõ ràng; ưu tiên Must trước | Không trễ; giai đoạn V–VII xong sớm |
| Thay đổi yêu cầu liên tục | Cao | Trung bình | Mọi thay đổi ghi CR + phân tích ảnh hưởng, cập nhật mọi tài liệu liên quan | 49 CR được kiểm soát, tài liệu vẫn khớp mã nguồn |
| Thành viên vắng / không hoàn thành phần việc | Trung bình | Cao | Phân công có người review chéo; theo dõi qua biên bản họp | Không xảy ra |
| Tích hợp giữa các phần (backend – frontend – AI) lỗi muộn | Trung bình | Cao | Tích hợp ngay trong từng luồng, test đầu-cuối trên trình duyệt từ F2 | Không còn bước "tích hợp cuối" |
| Chất lượng kém, lỗi lọt đến buổi demo | Trung bình | Cao | Test tự động mỗi luồng, kiểm thử hệ thống, hồi quy toàn bộ sau mỗi sửa lỗi | 23 lỗi được bắt và sửa trước nghiệm thu |

## 2. Các rủi ro của dự án (đã nhận diện và xử lý)
| Rủi ro | Xác suất | Ảnh hưởng | Biện pháp | Trạng thái |
|:---|:---|:---|:---|:---|
| Phần IoT không khả thi (máy pha có kết nối ít mẫu, đắt, đồ uống phần lớn pha tay) | Cao | Cao | Đánh giá lại, **bỏ IoT** (D8), đổi tên đề tài; ghi vào hướng phát triển | Đã xử lý (CR-09) |
| Mô hình AI không có dữ liệu thật để học | Cao | Cao | Script sinh ~5.000 đơn có quy luật cài sẵn (D32), đánh giá offline Hit Rate@5 | Đã xử lý: thành viên 48,9% so với 20,4% |
| Hiệu năng không đạt với 50 khách đồng thời (backend 1 tiến trình) | Trung bình | Trung bình | Phát hiện ở kiểm thử hệ thống (BUG-ST-06); cache API đọc (D38), chốt mô hình tải thực tế (D39) | Đã xử lý: p95 63 / 90 ms |
| Giới hạn OTP (5 mã/giờ) chặn buổi demo khi thử nhiều lần | Trung bình | Thấp | Nhiều SĐT demo có sẵn lịch sử (0901000001 → 0901000300); HDSD hướng dẫn dùng SĐT khác | Đã xử lý |
| Laptop demo tắt lúc 00:05 nên không có báo cáo ngày | Cao | Trung bình | Tự tính bù báo cáo còn thiếu khi khởi động (D36) | Đã xử lý |
| Mất kết nối realtime (Wi-Fi yếu) làm màn hình Bar không thấy đơn mới | Trung bình | Cao | Cảnh báo "Mất kết nối", tự tải lại qua REST mỗi 10 giây (BUG-ST-04), tự kết nối lại | Đã xử lý |
| Wi-Fi nhà mất IPv4 khi tải gói / Docker | Trung bình | Thấp | Dùng 4G khi cài đặt; demo không cần Internet (mọi dịch vụ ngoài đều giả lập) | Đã xử lý |
| Dữ liệu demo hỏng do thao tác thử trước buổi bảo vệ | Trung bình | Trung bình | `docker compose down -v` để dữ liệu sạch + sao lưu / khôi phục CSDL (NFR-R5) | Đã chuẩn bị |

## 3. Các rủi ro bất khả kháng
| Rủi ro | Ảnh hưởng | Phương án dự phòng |
|:---|:---|:---|
| Laptop demo hỏng / mất điện ngày bảo vệ | Không demo được | Mã nguồn trên GitHub, chạy được trên máy thành viên khác bằng `docker compose up` (~1 phút) + bản sao lưu CSDL; không làm bản cloud (D40) |
| Thành viên ốm / có việc đột xuất | Thiếu người thuyết trình | Mọi thành viên nắm luồng demo qua HDSD + diễn tập 14–15/11 |
| Sự cố mạng tại phòng bảo vệ | Điện thoại không quét QR được | Demo trên trình duyệt laptop (giả lập điện thoại) – hệ thống không phụ thuộc Internet |

# PHẦN IX: SẢN PHẨM NỘP

## 1. Báo cáo dự án
- **Báo cáo tổng kết** (tài liệu này) – `Nhom_8_Bao_cao_tong_ket.docx`.
- **Hồ sơ 1 – Tài liệu phân tích & thiết kế hệ thống** – `SmartCafe_1_Phan_tich_Thiet_ke.docx`: khảo sát, nghiên cứu công nghệ, use case & sequence, NFR & data model, CSDL, giao diện, kiến trúc & API; phụ lục quyết định (D1–D44) và `schema.sql`.
- **Hồ sơ 2 – Hồ sơ kiểm thử** – `SmartCafe_2_Ho_so_kiem_thu.docx`: quy ước, kế hoạch kiểm thử hệ thống, 10 biên bản kiểm thử.
- **Hồ sơ 3 – Hướng dẫn sử dụng** – `SmartCafe_3_Huong_dan_su_dung.docx`.

## 2. Slide thuyết trình
`3.Slide/` – slide bảo vệ cuối kỳ (Thành viên E, 12–14/11).

## 3. Căn cứ, tài liệu liên quan (kèm theo)
- **Mã nguồn** `2.San_pham/smartcafe/` (kho GitHub `thanhbinh0493/smartcafe`): backend, frontend, test tự động, script kiểm thử hệ thống, `docker-compose.yml`.
- **Biên bản họp** từng tuần – `Bien_ban_hop_Tuan_06.docx`, `Bien_ban_hop_Tuan_07.docx`.
- Biên bản nghiệm thu (16/11).

## 4. Kế hoạch của dự án
- **Hồ sơ 4 – Phạm vi & kế hoạch dự án** – `SmartCafe_4_Ke_hoach_Pham_vi.docx`.
- Bảng phân công – `2.San_pham/Nhom_8_Phan_cong.xlsx`.

# PHẦN X: KẾT QUẢ ĐẠT ĐƯỢC

## 1. Kết quả so với mục tiêu
| Mục tiêu | Kết quả |
|:---|:---|
| Sản phẩm chạy được đầy đủ 20 use case cho 5 vai trò | Đạt – 9 luồng F0 → F8 "Đạt", kịch bản xuyên luồng 10/10 |
| Gọi món nhanh qua QR | 5 lần chạm cho 1 đơn 2 món; trang chào hiện sau ~0,8 giây trên mạng 4G giả lập |
| Realtime giữa khách – quầy Bar | Đơn lên Bar ~0,05 giây; khách thấy "sẵn sàng" ~0,06 giây |
| AI gợi ý món có giải thích, 2 chế độ | Hit Rate@5: thành viên 48,9% (baseline 20,4%); gợi ý p95 90 ms |
| Yêu cầu phi chức năng | 29/29 đạt (hiệu năng, bảo mật, độ tin cậy, khả dụng, bảo trì) |
| Chất lượng | 793 ca kiểm thử đạt (727 + 66), 23 lỗi phát hiện và sửa hết, độ bao phủ 99% / 98,5% |
| Quản lý dự án | Đúng kế hoạch 8 tuần; 49 CR, 44 quyết định, 0 vấn đề mở; tài liệu khớp mã nguồn |
| Chi phí | 0đ chi phí tiền mặt; dự toán nhân công 63,03 triệu đồng (giả định) |

## 2. Bài học kinh nghiệm
- **Chia việc theo luồng nghiệp vụ** (thay vì backend / frontend riêng) giúp phát hiện lỗi tích hợp sớm và luôn có sản phẩm chạy được để demo.
- **Ghi mọi thay đổi thành CR ngay khi phát sinh** giúp tài liệu, mã nguồn và kế hoạch không lệch nhau dù yêu cầu thay đổi nhiều (bỏ IoT, thêm khuyến mãi / OTP / tích điểm).
- **Kiểm thử hệ thống trên bản chạy thật** tìm ra lỗi mà test từng luồng không thấy (mã đóng WebSocket, hiệu năng khi nhiều người dùng, mất kết nối).
- **Một nguồn tài liệu** (Markdown trong kho, xuất Word tự động) tránh việc sửa hai nơi.
- **Cần thống nhất mô hình tải ngay từ khi viết yêu cầu hiệu năng** – "50 người dùng đồng thời" phải đi kèm tần suất thao tác (D39).

## 3. Hướng phát triển
- Đổi điểm tích lũy, voucher / combo; quản lý kho nguyên liệu.
- Kết nối cổng thanh toán và SMS thật (đã có interface – NFR-M4); tự hủy đơn chưa thanh toán sau 15 phút (D22).
- Chạy nhiều tiến trình backend với Redis pub/sub hoặc PostgreSQL LISTEN/NOTIFY khi số quán tăng.
- Mô hình gợi ý collaborative filtering khi có đủ dữ liệu thật; tích hợp máy pha chế kết nối (IoT) cho các chuỗi lớn.
- Bản triển khai trên cloud có HTTPS.
