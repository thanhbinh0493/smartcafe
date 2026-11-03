# IV.2. THIẾT KẾ MOCKUP / UI WEB ADMIN VÀ GIAO DIỆN QR

| Thông tin | Nội dung |
|:---|:---|
| Người thực hiện | Thành viên E |
| Người review | Thành viên D |
| Thời gian | 15/10/2026 – 20/10/2026 (review 22/10/2026) |
| Cập nhật | 01/11/2026 – thêm W00, W00a, W07; vẽ lại W04 dạng hàng đợi; bỏ màn hình thiết bị IoT (CR-09 → CR-14) |
| Công cụ | Wireframe low-fidelity bằng PlantUML Salt (trong tài liệu này). Bản hi-fi do Thành viên E dựng trên **Figma** dựa theo wireframe |

## 1. Nguyên tắc thiết kế
- **QR Order (khách):** mobile-first, một tay thao tác được, nút chính cố định ở đáy màn hình. Luồng: Màn hình chào → (OTP) → Menu → Giỏ hàng/Thanh toán → Theo dõi.
- **Web Admin:** bố cục sidebar trái và nội dung bên phải. Menu sidebar thay đổi theo vai trò (RBAC).
- **Màn hình Bar:** chạy toàn màn hình trên tablet/TV. Bên trái là **bảng hàng đợi sắp theo giờ gọi**, bên phải là cột "Có thể lấy". Chữ lớn, có âm báo món mới.
- **Màu trạng thái thống nhất:** Đang chờ = vàng, Đang pha = xanh dương, Có thể lấy = xanh lá, Đã hủy = đỏ, Hoàn tất = xám. Nhãn "Khuyến mãi" = cam, "Mới" = tím.
- **Màu thương hiệu (gợi ý):** nâu cà phê `#6F4E37` làm màu chính, kem `#FDF6EC` làm nền.

## 2. Sơ đồ màn hình (Sitemap)

**QR Order Web App** (`/t/:qrToken`)
| Mã | Màn hình | Use Case |
|:---|:---|:---|
| W00 | Màn hình chào: chọn "Nhập SĐT" hoặc "Xem menu ngay" | UC01 |
| W00a | Nhập SĐT và mã OTP | UC02 |
| W01 | Menu điện tử + khối gợi ý (+ tên và điểm nếu là thành viên) | UC03, UC07 |
| ~~W01a~~ | ~~Chi tiết món (popup: số lượng, ghi chú)~~ – **bỏ theo D29**: bấm "+" trên W01 là thêm ngay, số lượng và ghi chú chỉnh ở W02 | UC04 |
| W02 | Giỏ hàng & thanh toán giả lập | UC04, UC05 |
| W03 | Theo dõi trạng thái đơn | UC06 |

**Web Admin** (`/admin`)
| Mã | Màn hình | Vai trò | Use Case |
|:---|:---|:---|:---|
| A01 | Đăng nhập | Tất cả | UC08 |
| W08 | Tổng quan: dashboard bán hàng (báo cáo ngày) | ADMIN, MANAGER | UC16 |
| A03 | Quản lý chi nhánh | ADMIN | UC11 |
| A04 | Quản lý nhân viên | ADMIN, MANAGER | UC12 |
| A05 | Quản lý danh mục | ADMIN | UC09 |
| W05 | Quản lý món (menu chung) | ADMIN | UC10 |
| W06 | Menu chi nhánh | MANAGER | UC13 |
| A06 | Bàn & mã QR (xem, tải ảnh QR để in) | MANAGER | UC14 |
| W07 | Khuyến mãi (danh sách + tạo/sửa) | ADMIN | UC15 |
| W04 | Màn hình quầy Bar | MANAGER, BARISTA (CASHIER: chỉ tra cứu + hủy đơn) | UC17–UC20 |

Sau khi đăng nhập, màn hình mặc định theo vai trò: ADMIN → W08, MANAGER → W08, BARISTA → W04, CASHIER → W04 (chế độ tra cứu).

## 3. Wireframe các màn hình chính

### W00 – Màn hình chào
![W00](diagrams/png/IV_ui_w00_man_hinh_chao.png)
- Hai lựa chọn được trình bày ngang hàng, mỗi lựa chọn có mô tả lợi ích để khách tự chọn.
- Không ghi nhớ lựa chọn của lần trước (không lưu định danh thiết bị). Lần quét nào cũng hiện màn hình này.

### W00a – Nhập SĐT và OTP
![W00a](diagrams/png/IV_ui_w00a_xac_thuc_otp.png)
- Bước 1 nhập SĐT, kèm dòng giải thích mục đích sử dụng. Bước 2 nhập 6 ô OTP, có đồng hồ đếm ngược hạn mã và nút gửi lại (khóa trong 60 giây).
- Khung **[DEMO]** hiển thị mã OTP giả lập, chỉ xuất hiện khi backend bật `OTP_DEMO_MODE`.

### W01 – Menu điện tử
![W01](diagrams/png/IV_ui_w01_qr_menu.png)
- Thành viên: dòng "Xin chào – X điểm (≈ X×100đ)" (không thu thập tên – D31) và nút Thoát (xóa phiên). Phiên tự hết sau 1 giờ. Khách ẩn danh: thay bằng nút "Nhập SĐT tích điểm".
- Khối **"Gợi ý cho bạn"** dạng thẻ cuộn ngang, mỗi thẻ có lý do gợi ý. Lý do khác nhau theo chế độ (xem chú thích trong ảnh). Món thêm từ khối này được gắn `is_recommended = true`.
- Món KM hiện giá gốc gạch ngang và giá mới. Có tab danh mục **"Khuyến mãi"** để lọc nhanh. Món mới có nhãn [MỚI]. Món hết hàng hiển thị mờ, "Tạm hết".

### W02 – Giỏ hàng & thanh toán
![W02](diagrams/png/IV_ui_w02_gio_hang.png)
- Mỗi món có nút tăng/giảm số lượng và ô ghi chú.
- Khối **"Thường gọi kèm"** dùng luật kết hợp.
- Hiển thị tạm tính, giảm giá KM, tổng cộng, và **"Bạn sẽ nhận +X điểm khi nhận đồ"** (chỉ với thành viên).
- Thanh toán là giả lập: popup "Đang xử lý…" khoảng 1,5 giây rồi báo "Thanh toán thành công".

### W03 – Theo dõi đơn
![W03](diagrams/png/IV_ui_w03_theo_doi_don.png)
- Thanh tiến trình 3 bước, trạng thái từng món, **vị trí trong hàng đợi**, cập nhật qua WebSocket.
- Khi đơn READY: banner xanh lá "Đồ uống đã sẵn sàng – mời bạn đến quầy nhận", kèm rung điện thoại. Khi đơn COMPLETED: hiện "+X điểm".

### W04 – Màn hình quầy Bar (hàng đợi pha chế)
![W04](diagrams/png/IV_ui_w04_man_hinh_bar.png)
- **Bảng hàng đợi** gồm các cột: số thứ tự, **giờ gọi**, số phút đã chờ, **bàn**, mã đơn, **món**, số lượng, **ghi chú**, thao tác. Món **cũ nhất ở trên cùng**; các món cùng đơn đứng liền nhau.
- Mỗi dòng có nút **[Bắt đầu]**, bấm xong đổi thành "ĐANG PHA [Xong]". Bấm "Xong" thì dòng biến mất, có nút "Hoàn tác" trong 10 giây.
- Cột phải **"Có thể lấy"**: các đơn đã xong hết món; **pha chế** giao đồ rồi bấm [Đã giao]. Thu ngân mở màn hình này ở chế độ tra cứu: tìm đơn theo mã/bàn, chỉ có nút [Hủy đơn], không có nút Bắt đầu/Xong/Đã giao.
- Món chờ quá 10 phút hiển thị màu đỏ. Có âm báo khi có món mới.

### W05 – Quản lý món (Quản trị viên)
![W05](diagrams/png/IV_ui_w05_admin_mon.png)
- Form thêm/sửa món (modal) gồm: tên, danh mục, giá gốc, mô tả, ảnh (upload), **loại nóng/lạnh**, **thẻ (tags)**. Hai trường cuối là đầu vào cho AI (thời tiết, món tương tự).

### W06 – Menu chi nhánh (Quản lý chi nhánh)
![W06](diagrams/png/IV_ui_w06_menu_chi_nhanh.png)
- Cho phép chỉnh trực tiếp trên bảng (inline edit). Bật/tắt "Còn hàng" có hiệu lực ngay trên menu khách qua sự kiện `MENU_UPDATED`.

### W07 – Khuyến mãi
![W07](diagrams/png/IV_ui_w07_khuyen_mai.png)
- Danh sách chương trình có 3 tab: Đang chạy / Sắp chạy / Đã kết thúc (không có trong ảnh minh họa).
- Chỉ Quản trị viên truy cập. Form tạo/sửa chọn phạm vi "Toàn chuỗi" hoặc 1 chi nhánh. Cột "Giảm" tự tính %. Báo lỗi nếu giá KM ≥ giá bán hiện tại.

### W08 – Dashboard bán hàng
![W08](diagrams/png/IV_ui_w08_dashboard.png)
- Màn hình "Tổng quan" mặc định của Quản trị viên và Quản lý chi nhánh. Dữ liệu lấy từ `daily_sales_reports`, **tự cập nhật lúc 00:05 hằng ngày**.
- Bộ lọc: chi nhánh (Quản lý chỉ thấy chi nhánh mình), khoảng thời gian 7 / 30 ngày.
- Thẻ chỉ số của ngày gần nhất kèm % thay đổi so với ngày trước; biểu đồ đường doanh thu theo ngày (mỗi chi nhánh 1 đường); bảng so sánh chi nhánh; top 5 món.
- Thư viện biểu đồ gợi ý: Recharts (React).

## 4. Hướng dẫn chuyển sang Figma (cho Thành viên E)
1. Frame mobile 390×844 (iPhone 14) cho W00–W03. Frame desktop 1440×900 cho Web Admin. Màn hình Bar dùng 1280×800 (tablet ngang).
2. Tạo component dùng chung: Button (primary/secondary/danger), Badge trạng thái, Nhãn KM/Mới, Card món, Ô OTP, Dòng hàng đợi (Bar), Table, Modal.
3. Dựng prototype click-through cho 2 luồng demo: (a) ẩn danh W00 → W01 → W02 → W03; (b) thành viên W00 → W00a → W01 → W02 → W03; và W04.
4. Font **Be Vietnam Pro** (hỗ trợ tiếng Việt tốt, có sẵn trên Google Fonts).
