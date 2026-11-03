# THIẾT KẾ HỆ THỐNG – SmartCafe: Phần mềm quản lý chuỗi quán cà phê thông minh

Bộ tài liệu cho các giai đoạn **II (Khảo sát) → III (Phân tích) → IV (Thiết kế)** trong [Project_Plan.md](../Project_Plan.md).

## Mục lục

| Mục | Tài liệu | Người thực hiện / Review |
|:---|:---|:---|
| II.1 | [Khảo sát quy trình quản lý menu, đặt hàng](II.1_Khao_sat_quy_trinh.md) | D / A |
| II.2 | [Nghiên cứu công nghệ AI, IoT](II.2_Nghien_cuu_cong_nghe.md) | C / B |
| III.1 | [Use Case & Sequence Diagram](III.1_Use_Case_Sequence.md) | A / B |
| III.2 | [Yêu cầu phi chức năng & Data Model](III.2_Yeu_cau_phi_chuc_nang_Data_Model.md) | D / C |
| IV.1 | [Thiết kế CSDL (ERD, Schema)](IV.1_Thiet_ke_CSDL.md) + [schema.sql](schema.sql) | B / A |
| IV.2 | [Thiết kế giao diện (wireframe)](IV.2_Thiet_ke_giao_dien.md) | E / D |
| IV.3 | [Kiến trúc & danh sách API](IV.3_Kien_truc_va_API.md) *(bổ sung)* | B / A |

## Các quyết định đã chốt

Chi tiết từng thay đổi xem trong [biên bản họp](../../4.Tai_lieu_khac/Bien_ban_hop/).

| # | Ngày | Vấn đề | Quyết định |
|:---|:---|:---|:---|
| D1 | 28/10 | Tính năng AI | **Gợi ý món**, không làm nhận diện khuôn mặt. *(Cập nhật 01/11: gợi ý theo 2 chế độ, xem D9, D13)* |
| D2 | 28/10 | Tech stack | **Python FastAPI + React + PostgreSQL** |
| D3 | 28/10 | Menu đa chi nhánh | **Menu chung** ở trụ sở; chi nhánh được đặt **giá riêng** và bật/tắt **hết hàng** |
| D4 | 28/10 | Tài khoản khách | **Không bắt buộc**. *(Cập nhật 01/11: chọn chế độ ngay khi quét QR, xem D9)* |
| D5 | 28/10 | Thanh toán | **Trả trước trên web (giả lập)**. Đơn chỉ xuống Bar sau khi thanh toán thành công |
| D6 | 28/10 | Khảo sát | Khảo sát **giả định điển hình**, kèm bộ câu hỏi để đối chiếu với quán thật |
| D7 | 28/10 | Sơ đồ | PlantUML, xuất PNG |
| D8 | 01/11 | IoT | **Bỏ hẳn IoT** (máy pha có kết nối ít mẫu, khó cập nhật món mới, phần lớn đồ uống pha tay). Đề tài đổi tên thành "...(Tích hợp AI và QR)". Thay bằng **màn hình hàng đợi pha chế**: món + bàn + giờ gọi + ghi chú, **sắp theo giờ gọi**, pha chế bấm Bắt đầu / Xong |
| D9 | 01/11 | Nhận diện khách | Ngay sau khi quét QR có **2 lựa chọn**: (1) xem menu ngay, ẩn danh; (2) nhập SĐT để **tích điểm** và nhận gợi ý theo sở thích. **Không lưu thông tin thiết bị** (khách có thể đổi điện thoại) |
| D10 | 01/11 | Khuyến mãi | **Chương trình KM đơn giản**: tên, thời gian, phạm vi toàn chuỗi hoặc 1 chi nhánh, danh sách món + giá KM. Không làm voucher, combo, mua 1 tặng 1 |
| D11 | 01/11 | Tích điểm | **Chỉ tích và xem điểm**: cộng khi đơn hoàn tất. Chưa làm đổi điểm |
| D12 | 01/11 | Xác thực SĐT | **OTP giả lập** (6 số, hạn 5 phút, tối đa 5 lần sai); interface sẵn để gắn SMS thật |
| D13 | 01/11 | Thời tiết | **Giữ làm yếu tố phụ** (10% điểm) trong cả 2 chế độ gợi ý |
| D14 | 01/11 | Quyền tạo khuyến mãi | **Chỉ Quản trị viên** tạo/sửa KM (toàn chuỗi hoặc 1 chi nhánh). Quản lý chi nhánh không tạo KM, để đơn giản hóa luồng vận hành |
| D15 | 01/11 | Tỉ lệ tích điểm | **1 điểm / 10.000đ** (trên số tiền thực trả); **1 điểm = 100đ**, tức tỉ lệ hoàn lại 1% |
| D16 | 01/11 | Món mới | Món tạo trong **30 ngày** gần nhất |
| D17 | 01/11 | Phân công | Thành viên C nhận thêm: API OTP + tích điểm, script sinh dữ liệu mẫu |
| D18 | 01/11 | Phiên thành viên | Hết hạn sau **1 giờ** hoặc khi đóng tab (đủ cho một lần ngồi quán và gọi thêm món) |
| D19 | 01/11 | Kênh gọi món & vai trò thu ngân | **Chỉ nhận order qua quét QR** (thu ngân nhận order tại quầy sẽ không biết khách ngồi bàn nào). Thu ngân **không nằm trong luồng xử lý đơn**, chỉ hỗ trợ khách: tra cứu đơn, hủy & hoàn tiền |
| D20 | 01/11 | Xác nhận giao đồ | **Pha chế** giao đồ và bấm "Đã giao" (đơn → Hoàn tất, cộng điểm). Luồng xử lý đơn chỉ còn Khách + Pha chế |
| D21 | 01/11 | Báo cáo bán hàng | **Tự tổng hợp hằng ngày** (job 00:05) vào bảng `daily_sales_reports`; **dashboard đơn giản** (W08): doanh thu mỗi ngày của từng chi nhánh, số đơn, số đơn hủy, giá trị TB/đơn, thời gian chờ TB, tỉ lệ đơn thành viên, doanh thu KM, tỉ lệ món từ gợi ý AI, top 5 món. Ưu tiên nâng lên **Must** |
| D22 | 01/11 | Tự hủy đơn chưa thanh toán | Vì không triển khai thanh toán thật, chỉ **mô tả** quy tắc: không nhận được thanh toán sau 15 phút thì tự hủy (cài đặt job ở mức Could) |
| D23 | 01/11 | Tên sản phẩm | **SmartCafe** |
| D24 | 02/11 | Môi trường chạy & demo | Chạy **local trên laptop** bằng Docker Desktop (WSL2) + Docker Compose; Docker cài tại `D:\Docker` (chương trình `D:\Docker\DockerDesktop`, dữ liệu `D:\Docker\wsl-data`); WSL2 giới hạn 4 GB RAM / 4 nhân. Điện thoại demo truy cập qua cùng mạng Wi-Fi |
| D25 | 02/11 | Quy trình code & kiểm thử | Code **theo từng luồng nghiệp vụ cốt lõi**; mỗi luồng phải có **test tự động** và **biên bản kiểm thử** đầy đủ trước khi chuyển sang luồng tiếp theo |
| D26 | 02/11 | Thứ tự code & vị trí | F0 Nền tảng → F1 QR & menu → F2 Đặt món & thanh toán → F3 Màn hình Bar → F4 OTP & tích điểm → F5 Thu ngân hỗ trợ → F6 Quản trị → F7 AI gợi ý → F8 Báo cáo & dashboard. Mã nguồn: `2.San_pham/smartcafe/`; biên bản kiểm thử: `1.Bao_cao/Kiem_thu/` |
| D27 | 02/11 | Nhãn khuyến mãi | Chỉ gắn nhãn KM (giá gốc gạch ngang, `promotion_id`, tính vào doanh thu KM) khi giá KM **thấp hơn** giá đang bán (giá chi nhánh / giá chung). Nếu không thấp hơn thì bán giá thường, **không hiện nhãn KM**, tránh khách hiểu nhầm |
| D28 | 02/11 | Mã đơn | Giữ mã ngắn `CG-0142` (số thứ tự trong ngày, đếm lại mỗi ngày). Thêm cột `orders.order_date` (ngày tạo đơn, giờ VN) và ràng buộc **UNIQUE (order_code, order_date)** thay cho UNIQUE trên riêng `order_code` (sửa mâu thuẫn giữa UC05 và schema) |
| D29 | 03/11 | Màn hình chi tiết món | **Bỏ popup W01a**: bấm "+" trên menu là thêm món ngay vào giỏ; số lượng và ghi chú từng món chỉnh trong giỏ hàng (W02). Đạt NFR-U2 (đặt 2 món trong 5 lần chạm) |
| D30 | 03/11 | Hoàn tác món cuối của đơn | Pha chế bấm nhầm "Xong" ở **món cuối cùng** (đơn đã "Có thể lấy") rồi bấm "Hoàn tác" trong thời gian cho phép thì món về "Đang pha" và **đơn quay lại "Đang pha chế"** (READY → PREPARING, ghi lịch sử trạng thái, khách thấy lại "Đang pha"). Đơn đã "Đã giao" (COMPLETED) thì không hoàn tác được |
| D31 | 03/11 | Thông tin khách thành viên | **Không thu thập tên**: thành viên chỉ định danh bằng **số điện thoại** đã xác thực OTP. Bỏ cột `customers.name`; lời chào trên menu là "Xin chào – X điểm (≈ Yđ)" |
| D32 | 03/11 | Dữ liệu lịch sử cho AI | Script `seed_orders.py` (≈ 5.000 đơn / 60 ngày / 3 chi nhánh / 300 thành viên, có quy luật cài sẵn) **tự nạp khi khởi động** nếu chưa nạp (như `seed_data`), rồi học luật kết hợp. Có **SĐT demo cố định 0901000001** (Cầu Giấy) đã có lịch sử để demo chế độ thành viên |
| D33 | 03/11 | Thư viện FP-Growth | Dùng **mlxtend** như II.2 (chấp nhận image backend nặng thêm do pandas / scipy / scikit-learn) |
| D34 | 03/11 | Gắn đơn với lần gợi ý | Thêm trường tùy chọn `recommendation_log_id` vào `POST /api/public/orders`; backend gán `recommendation_logs.order_id` (cùng chi nhánh, cùng khách, chưa gắn, trong 2 giờ), sai thì bỏ qua – không làm hỏng việc đặt đơn |
| D35 | 03/11 | Thời tiết | **Mặc định nhiệt độ giả lập** (`WEATHER_MOCK_TEMP_C`, đổi để demo trời nóng / lạnh); có `WEATHER_API_KEY` thì gọi OpenWeatherMap (cache 30 phút), lỗi thì về giả lập |
| D36 | 03/11 | Bù báo cáo ngày khi khởi động | Ngoài job 00:05, **mỗi lần backend khởi động tự tính bù các ngày đã kết thúc còn thiếu trong 60 ngày** (ngày đã có báo cáo thì không tính lại). Quản trị viên vẫn có nút "Tính lại hôm qua" |
| D37 | 03/11 | Số liệu "Tất cả chi nhánh" trên dashboard | Dashboard **chỉ đọc bảng `daily_sales_reports`**: tỉ lệ món từ gợi ý toàn chuỗi = trung bình theo số đơn của các chi nhánh; top 5 món toàn chuỗi gộp từ top 5 từng chi nhánh (chấp nhận gần đúng) |

## Vấn đề mở (Open Issues) – nơi theo dõi duy nhất

Bảng này là **nơi duy nhất** theo dõi các đề xuất và vấn đề chưa chốt. Khi một mục được chốt thì chuyển trạng thái sang "Đã chốt", ghi mã quyết định (D..), đồng thời ghi CR vào biên bản họp của tuần đó.

| # | Ngày mở | Vấn đề / đề xuất | Phương án thay thế | Người chốt | Trạng thái |
|:---|:---|:---|:---|:---|:---|
| P21 | 03/11 | **Bù báo cáo ngày khi backend khởi động**: tự tính các ngày đã kết thúc còn thiếu trong 60 ngày (laptop demo thường tắt lúc 00:05 nên job không chạy, dashboard sẽ trống). Đã cài ở F8 – xem [biên bản kiểm thử F8](../Kiem_thu/Bien_ban_kiem_thu_F8_Bao_cao_Dashboard.md) Mục 7 | Chỉ job 00:05 + quản trị viên bấm "Tính lại" | A | Đã chốt → D36 (tự bù khi khởi động) |
| P22 | 03/11 | Dashboard "Tất cả chi nhánh" gộp từ bảng theo chi nhánh: tỉ lệ món từ gợi ý lấy trung bình theo số đơn (gần đúng), top 5 món gộp từ top 5 từng chi nhánh. Đã cài ở F8 – xem [biên bản kiểm thử F8](../Kiem_thu/Bien_ban_kiem_thu_F8_Bao_cao_Dashboard.md) Mục 7 | Tính top món toàn chuỗi trực tiếp từ `order_items` | A | Đã chốt → D37 (giữ cách gộp từ bảng báo cáo) |
| P17 | 03/11 | Cách nạp dữ liệu lịch sử cho AI (seed_orders.py) vào CSDL demo – phát sinh khi bắt đầu F7 | Chạy tay bằng lệnh | A | Đã chốt → D32 (tự nạp khi CSDL trống + SĐT demo) |
| P18 | 03/11 | Thư viện FP-Growth: mlxtend (II.2) làm image nặng thêm ~80–100 MB | Tự viết FP-Growth | A | Đã chốt → D33 (mlxtend) |
| P19 | 03/11 | Cách gán `recommendation_logs.order_id` (API chưa quy định) | Không gán, chỉ dựa `is_recommended` | A | Đã chốt → D34 (trường `recommendation_log_id`) |
| P20 | 03/11 | Weather API: nhóm chưa có key OpenWeatherMap | Chỉ giả lập | A | Đã chốt → D35 (giả lập mặc định, key tùy chọn) |
| P16 | 03/11 | Khách thành viên **nhập tên (tùy chọn)** sau lần xác thực OTP đầu tiên để lời chào thành "Xin chào <tên>" như wireframe W01. Hiện cột `customers.name` có nhưng không màn hình nào cho nhập, nên chào "Xin chào – X điểm". Phát sinh khi code F4 – xem [biên bản kiểm thử F4](../Kiem_thu/Bien_ban_kiem_thu_F4_OTP_Tich_diem.md) Mục 7 | Không thu thập tên (giữ như hiện tại, ít dữ liệu cá nhân hơn – NFR-S7) | A | Đã chốt → D31 (không thu thập tên) |
| P11 | 01/11 | Mốc lập trình mới ở [IV.3 Mục 3](IV.3_Kien_truc_va_API.md) (giai đoạn V bắt đầu 02/11 thay vì 23/10) | Giữ mốc gốc, tăng nhân lực | A | Hoãn – A tự cập nhật timeline thủ công sau (CR-27) |
| P15 | 03/11 | Bấm nhầm "Xong" ở **món cuối cùng** (đơn đã chuyển "Có thể lấy") rồi bấm "Hoàn tác" thì **đơn quay lại "Đang pha chế"** (READY → PREPARING, ghi lịch sử, khách thấy lại "Đang pha"). Bổ sung chuyển trạng thái này vào biểu đồ trạng thái đơn. Đã cài đặt ở F3 – xem [biên bản kiểm thử F3](../Kiem_thu/Bien_ban_kiem_thu_F3_Man_hinh_Bar.md) Mục 7 | Không cho hoàn tác khi đơn đã "Có thể lấy" | A | Đã chốt → D30 |
| P14 | 03/11 | Gộp W01a (popup chi tiết món) vào W02: bấm "+" trên menu là thêm ngay, số lượng và ghi chú chỉnh trong giỏ hàng – để đạt NFR-U2 (đặt 2 món trong 5 lần chạm; có popup thì ≥ 7). Đã cài đặt ở F2 – xem [biên bản kiểm thử F2](../Kiem_thu/Bien_ban_kiem_thu_F2_Dat_mon_Thanh_toan.md) Mục 7 | Giữ popup W01a đúng wireframe | A | Đã chốt → D29 |
| P13 | 02/11 | Khi giá KM **không thấp hơn** giá đang bán (giá chi nhánh / giá chung) thì bán giá thường và **không gắn nhãn KM** (`promotion_id` = NULL, không tính vào "doanh thu KM"). Đã cài đặt ở F1 – xem [biên bản kiểm thử F1](../Kiem_thu/Bien_ban_kiem_thu_F1_QR_Menu.md) Mục 7 | Vẫn gắn nhãn KM dù không rẻ hơn | A | Đã chốt → D27 |
| P12 | 02/11 | Bản demo dự phòng trên cloud (Azure for Students hoặc Oracle Always Free) phòng khi laptop gặp sự cố lúc nghiệm thu | Chỉ demo local; hoặc dùng laptop thành viên khác | A | **Đang mở** |
| P1 | 28/10 | IoT giao tiếp bằng HTTP REST | — | — | Hủy (D8) |
| P2 | 28/10 | Thu ngân không nhận order tại quầy, chỉ xử lý ngoại lệ | Thêm POS tại quầy | A | Đã chốt → D19, D20 |
| P3 | 28/10 | Báo cáo bán hàng ở mức Could | Nâng lên Must | A | Đã chốt → D21 (dashboard, Must) |
| P4 | 28/10 | Đơn chưa thanh toán sau 15 phút thì tự hủy | — | A | Đã chốt → D22 (chỉ mô tả) |
| P5 | 28/10 | Tên thương hiệu "SmartCafe" | — | A | Đã chốt → D23 |
| P6 | 01/11 | Quản lý chi nhánh được tạo KM cho chi nhánh mình | — | A | Đã chốt → D14 (không cho phép) |
| P7 | 01/11 | 1 điểm / 10.000đ | — | A | Đã chốt → D15 |
| P8 | 01/11 | Món mới = tạo trong 30 ngày | — | A | Đã chốt → D16 |
| P9 | 01/11 | C nhận thêm API OTP, tích điểm, script dữ liệu mẫu | — | A | Đã chốt → D17 |
| P10 | 01/11 | Phiên thành viên 4 giờ | — | A | Đã chốt → D18 (1 giờ) |

## Sơ đồ
- Mã nguồn: [diagrams/src/](diagrams/src/) – ảnh: [diagrams/png/](diagrams/png/) (có thể chèn thẳng vào báo cáo Word).
- Render lại sau khi sửa (cần Java 8+ và [plantuml.jar](https://plantuml.com/download), không cần Graphviz vì sơ đồ dùng layout `smetana`):
  ```bash
  cd 1.Bao_cao/Thiet_ke_he_thong/diagrams
  java -jar plantuml.jar -charset UTF-8 -tpng -o ../png src/*.puml
  ```
- Xem trực tiếp trong VS Code: cài extension *PlantUML* (jebbs.plantuml).
