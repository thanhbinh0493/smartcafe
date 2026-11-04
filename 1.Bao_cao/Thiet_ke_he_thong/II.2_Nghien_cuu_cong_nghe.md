# II.2. NGHIÊN CỨU CÔNG NGHỆ ÁP DỤNG CHO BÀI TOÁN (AI GỢI Ý MÓN; IoT ĐÃ LOẠI BỎ)

| Thông tin | Nội dung |
|:---|:---|
| Người thực hiện | Thành viên C |
| Người review | Thành viên B |
| Thời gian | 25/09/2026 – 30/09/2026 (review 01/10/2026) |
| Cập nhật | 01/11/2026 – bỏ IoT, gợi ý theo 2 chế độ, thêm OTP giả lập (biên bản Tuần 06, CR-09 → CR-14); 04/11/2026 – rà soát, đồng bộ với mã nguồn và kế hoạch D41 (CR-46) |

## 1. Công nghệ nền tảng (đã chốt)

| Thành phần | Công nghệ | Lý do chọn |
|:---|:---|:---|
| Backend | **Python 3.11 + FastAPI**, SQLAlchemy 2, Alembic, Pydantic | Cùng ngôn ngữ với module AI nên gọi trực tiếp, không cần service riêng. Có sẵn WebSocket và tự sinh tài liệu OpenAPI/Swagger cho Frontend |
| Frontend | **React 18 + Vite**, React Router, Axios, TailwindCSS | Một codebase phục vụ cả QR Order (mobile) và Web Admin |
| CSDL | **PostgreSQL 16** | Hỗ trợ ENUM, JSONB (log gợi ý), mảng TEXT[] (tags món) |
| Realtime | **WebSocket** (có sẵn trong FastAPI/Starlette) | Đẩy hàng đợi pha chế xuống màn hình Bar và trạng thái đơn tới khách, không phải polling |
| Xác thực | JWT (python-jose) + bcrypt (passlib) | JWT cho nhân viên (8 giờ) và cho phiên khách thành viên (1 giờ) |
| Triển khai | Docker Compose (db, backend, frontend) | Mọi thành viên chạy demo bằng 1 lệnh |

## 2. Bài toán AI: Gợi ý món (Recommendation)

### 2.1. Yêu cầu
- Ngay sau khi quét QR, khách chọn 1 trong 2 chế độ. Gợi ý **top 5 món** phải phù hợp với chế độ đã chọn:
  - **Ẩn danh** (không nhập SĐT): hệ thống không biết khách là ai, nên gợi ý dựa trên **món bán chạy, món đang khuyến mãi, món mới**.
  - **Thành viên** (đã xác thực SĐT bằng OTP): gợi ý **theo sở thích** dựa trên lịch sử đơn của chính khách đó.
- Khi giỏ hàng đã có món, gợi ý thêm **"Thường gọi kèm"** (dùng cho cả 2 chế độ, vì chỉ cần biết món trong giỏ).
- Gợi ý phải giải thích được lý do: "Bạn hay gọi", "Giống món bạn thích", "Đang giảm 20%", "Món mới", "Bán chạy nhất chi nhánh", "Hợp trời nóng".
- **Không lưu định danh thiết bị** (không cookie lâu dài, không fingerprint). Khách được nhận diện bằng **SĐT đã xác thực**, nên đổi điện thoại vẫn giữ được lịch sử.

### 2.2. So sánh phương án

| Phương án | Mô tả | Ưu | Nhược | Đánh giá |
|:---|:---|:---|:---|:---|
| A. Luật cứng (rule-based) | Nóng thì gợi ý đồ lạnh, lạnh thì gợi ý đồ nóng | Rất dễ | Không học từ dữ liệu | Dùng làm yếu tố phụ (thời tiết) |
| B. Phổ biến (Popularity) | Top món bán chạy theo chi nhánh 7 ngày | Dễ, giải quyết cold-start | Ai cũng nhận gợi ý giống nhau | Thành phần chính của chế độ ẩn danh |
| C. Luật kết hợp (FP-Growth) | Khai phá cặp món hay mua cùng nhau | Kỹ thuật học máy kinh điển, dễ giải thích (support/confidence/lift) | Cần đủ dữ liệu đơn | **Chọn làm "model AI"** cho "Thường gọi kèm" |
| D. Content-based (tags) | Tìm món có thẻ (tags)/danh mục giống món khách yêu thích | Gợi ý được món mới mà khách chưa thử; không cần nhiều khách | Phụ thuộc chất lượng gắn thẻ | **Chọn** cho chế độ thành viên |
| E. Collaborative Filtering | Học từ ma trận khách × món | Cá nhân hóa sâu | Cần nhiều khách thành viên, khó giải thích | Hướng phát triển |
| F. Deep Learning / LLM | — | — | Quá sức so với 4 tuần lập trình | Loại |

### 2.3. Phương án chọn: chấm điểm kết hợp theo 2 chế độ

Mọi thành phần đều được chuẩn hóa về khoảng 0..1. Chỉ xét các món **còn bán** tại chi nhánh.

**Chế độ ẩn danh:**
```
score(i) = 0.45 * Popular(i)   # tỉ lệ số lượng bán 7 ngày tại chi nhánh
         + 0.25 * Promo(i)     # = mức giảm (%) / 50%, tối đa 1; 0 nếu không có KM đang hiệu lực
         + 0.20 * New(i)       # 1 nếu món được tạo trong 30 ngày gần nhất
         + 0.10 * Weather(i)   # 1 nếu hợp thời tiết, 0.5 nếu BOTH/NONE, 0 nếu ngược
```

**Chế độ thành viên:**
```
score(i) = 0.40 * Personal(i)  # tần suất khách đã gọi món i (có trọng số thời gian: đơn gần đây nặng hơn)
         + 0.20 * Similar(i)   # độ tương đồng Jaccard giữa tags của món i và tags của 3 món khách gọi nhiều nhất
         + 0.15 * Popular(i)
         + 0.15 * Promo(i)
         + 0.10 * Weather(i)
```
- Khách thành viên **chưa có đơn nào** (mới đăng ký) thì dùng công thức ẩn danh.
- **Weather:** nhiệt độ ≥ 28°C ưu tiên `COLD`; ≤ 22°C ưu tiên `HOT`; ở giữa thì trung tính.
- **Đa dạng:** top 5 có tối đa 2 món "Bạn hay gọi", để luôn còn chỗ cho món khách chưa thử.
- **"Thường gọi kèm"** (giỏ hàng): lấy các luật `antecedent ∈ giỏ`, sắp theo `confidence × lift`, bỏ món đã có trong giỏ, lấy top 2.
- Lý do hiển thị = thành phần đóng góp nhiều điểm nhất.
- Trọng số là giá trị khởi đầu, sẽ tinh chỉnh bằng đánh giá offline (Mục 2.5).
- *Cài đặt (F7):* Popular tính trên đơn đã thanh toán, không hủy, chuẩn hóa theo món bán nhiều nhất; Personal tính trên đơn của khách ở mọi chi nhánh, chu kỳ bán rã 30 ngày; Similar **không so món với chính nó** và nhãn "Giống món bạn thích" chỉ dành cho món khách chưa gọi; không gợi ý món đã có trong giỏ. Luật kết hợp 1 món → 1 món, học riêng từng chi nhánh + toàn chuỗi, luật của chi nhánh được ưu tiên. Số liệu bán chạy và luật kết hợp được giữ trong cache của backend (bán chạy 60 giây, luật tới lần học lại – D38), nên gợi ý API phản hồi p95 ~90 ms với 50 khách đồng thời ([biên bản kiểm thử hệ thống](../Kiem_thu/Bien_ban_kiem_thu_He_thong.md)).

### 2.4. Dữ liệu và huấn luyện
- **Dữ liệu:** script `seed_orders.py` sinh khoảng 5.000 đơn giả lập trong 60 ngày cho 3 chi nhánh, ~40% đơn thuộc khoảng 300 khách thành viên (SĐT 0901000001…0901000300; **0901000001** là khách demo ở Cầu Giấy). Tự nạp khi backend khởi động lần đầu (D32). Script có cài sẵn quy luật để mô hình học lại được: mỗi khách có 2–3 món "ruột", "cà phê sữa thường đi kèm bánh croissant", "trời nóng bán nhiều trà, đá xay".
- **Huấn luyện luật kết hợp:** thư viện `mlxtend` (FP-Growth), `min_support = 0.01`, `min_confidence = 0.2`, chỉ giữ luật `lift > 1`. Chạy **hằng đêm lúc 00:30** bằng APScheduler (và ngay sau khi nạp dữ liệu mẫu), ghi vào bảng `association_rules` (D33).
- **Thời tiết:** mặc định nhiệt độ **giả lập** `WEATHER_MOCK_TEMP_C` (31°C); có `WEATHER_API_KEY` thì gọi OpenWeatherMap (gói miễn phí), cache 30 phút theo chi nhánh, lỗi / chậm quá 2 giây thì về giả lập (D35).

### 2.5. Đánh giá mô hình (đưa vào báo cáo)
- **Offline:** chia đơn theo thời gian (80% train / 20% test). Với mỗi đơn test, ẩn 1 món rồi kiểm tra món đó có trong top 5 không. Tính **Hit Rate@5**, so sánh 3 cấu hình: chỉ Popular (baseline), công thức ẩn danh, công thức thành viên (chỉ trên đơn của thành viên).
- **Online (demo):** dựa vào `order_items.is_recommended` và `recommendation_logs.mode` (log được gắn với đơn qua `recommendation_log_id` – D34), tính tỉ lệ món được thêm từ khối gợi ý theo từng chế độ.
- **Kết quả lần đầu (03/11/2026, dữ liệu mô phỏng, script `evaluate_recommender.py`):** Hit Rate@5 – baseline Bán chạy 20,9%, công thức ẩn danh 19,8%, **công thức thành viên 48,9%** (trên đơn thành viên, baseline 20,4%); "Thường gọi kèm" Hit Rate@2 15,1%. Chi tiết: [biên bản kiểm thử F7](../Kiem_thu/Bien_ban_kiem_thu_F7_AI_goi_y.md) Mục 4.7.

## 3. IoT: đánh giá và quyết định LOẠI BỎ

### 3.1. Phương án đã cân nhắc
Máy pha chế kết nối mạng tự gửi tín hiệu "pha xong" để đổi trạng thái đơn, nhân viên không cần bấm nút (bản đầu: giả lập bằng script Python giao tiếp HTTP).

### 3.2. Lý do loại bỏ (biên bản Tuần 06, CR-09)
| # | Lý do |
|:---|:---|
| 1 | **Phần lớn menu được pha tay** (trà, đá xay, matcha, bánh). Máy chỉ báo được cho vài món espresso, nên không giải quyết được vấn đề P7 cho cả đơn |
| 2 | Máy pha có kết nối (IoT) **ít mẫu trên thị trường, giá cao**, thường khóa theo hệ sinh thái của hãng |
| 3 | Công thức nằm trên máy, **khó tùy biến món mới** và khó đồng bộ thay đổi cho toàn bộ chi nhánh |
| 4 | Ở mức giả lập, phần IoT không đem lại giá trị thực khi demo, lại tốn công tích hợp (3 bảng, 4 use case, 1 simulator) |

### 3.3. Phương án thay thế
**Màn hình hàng đợi pha chế** tại quầy Bar: hiển thị các món khách đã gọi kèm **bàn, giờ gọi, ghi chú**, **sắp theo thời gian gọi** (cũ nhất ở trên). Pha chế bấm "Bắt đầu" và "Xong" cho từng món, trạng thái được đẩy realtime tới khách. Cách này áp dụng cho mọi loại đồ uống, không phụ thuộc thiết bị. Thêm món mới chỉ cần cập nhật menu trên Web Admin.

IoT được ghi vào **hướng phát triển** (VD: kết nối máy espresso chuyên dụng của các chuỗi lớn).

## 4. Các dịch vụ giả lập
- **Mock Payment Service:** luôn trả `SUCCESS`, trừ khi số tiền kết thúc bằng `999` thì trả `FAILED` để demo luồng lỗi. Interface `charge()` và `refund()` giữ giống cổng thật (VNPay/Momo) để dễ thay sau này.
- **Mock SMS Service (OTP):** sinh mã 6 số. Ở chế độ demo (`OTP_DEMO_MODE=true`), mã được ghi ra log backend và trả về trong response để giao diện hiện khung "[DEMO] Mã OTP". Interface `send(phone, message)` có thể thay bằng dịch vụ SMS thật (ngoài phạm vi). Các quy tắc bảo mật vẫn áp dụng đầy đủ: mã lưu dạng băm, hết hạn sau 5 phút, tối đa 5 lần nhập sai, gửi lại sau 60 giây, tối đa 5 mã/giờ/SĐT.

## 5. Rủi ro công nghệ và cách giảm thiểu

| Rủi ro | Mức | Giảm thiểu |
|:---|:---|:---|
| Dữ liệu giả lập quá "đẹp" khiến kết quả AI thiếu thuyết phục | TB | Thêm nhiễu ngẫu nhiên vào seed; báo cáo rõ đây là dữ liệu mô phỏng |
| Ít khách thành viên nên chế độ cá nhân hóa yếu | TB | Fallback về công thức ẩn danh; seed đủ lịch sử cho khoảng 300 thành viên |
| Weather API lỗi khi demo | Thấp | Thời tiết giả lập; thời tiết chỉ chiếm 10% điểm |
| WebSocket mất kết nối trên mạng di động | TB | Client tự kết nối lại và tải lại trạng thái qua REST |
| Lạm dụng OTP (spam gửi mã) | Thấp (giả lập) | Giới hạn tần suất theo SĐT |
| Thành viên chưa quen FastAPI/React | Cao | Tuần đầu giai đoạn V làm skeleton chung (B, E); có tài liệu Swagger |
