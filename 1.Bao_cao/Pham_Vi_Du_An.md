# TÀI LIỆU THỐNG NHẤT ĐỀ TÀI VÀ PHẠM VI DỰ ÁN

> **Cập nhật 01/11/2026** (biên bản họp Tuần 06, CR-09 → CR-14): bỏ IoT; bổ sung màn hình chào 2 lựa chọn, xác thực SĐT bằng OTP giả lập, tích điểm, chương trình khuyến mãi đơn giản.

## 1. Tên đề tài
**Xây dựng phần mềm quản lý chuỗi quán cà phê thông minh (Tích hợp AI và QR)**

**Tên sản phẩm:** SmartCafe

## 2. Mục tiêu dự án
*   **Về mặt nghiệp vụ:** Cung cấp giải pháp phần mềm giúp các chuỗi cà phê tự động hóa quy trình gọi món, tối ưu hoá quản lý thực đơn, đơn hàng và ứng dụng AI gợi ý món để nâng cao trải nghiệm khách hàng.
*   **Về mặt học tập (Đồ án):** Áp dụng chuẩn quy trình quản lý dự án phần mềm (lập kế hoạch, phân tích, thiết kế, lập trình, kiểm thử) trong vòng 8 tuần làm việc nhóm (21/09 → 16/11/2026, D41).

## 3. Phạm vi dự án (Project Scope)
Để đảm bảo tính khả thi trong 3 tháng, nhóm sẽ giới hạn phạm vi như sau:

**3.1. Các phần Nằm trong phạm vi (In-scope - Sẽ làm):**
*   Quản lý thông tin cốt lõi: Chi nhánh, Nhân viên, Thực đơn, Đơn hàng.
*   Chương trình khuyến mãi đơn giản (giá khuyến mãi theo món, có thời hạn, theo chi nhánh hoặc toàn chuỗi).
*   Báo cáo bán hàng: hệ thống tự tổng hợp hằng ngày, hiển thị trên dashboard đơn giản (doanh thu mỗi ngày của từng chi nhánh và một số chỉ số cơ bản).
*   Luồng khách hàng tự order tại bàn qua mã QR (**kênh gọi món duy nhất**; thu ngân không nhận order tại quầy), có 2 lựa chọn: gọi món ẩn danh hoặc nhập SĐT (xác thực OTP giả lập) để tích điểm.
*   Tích điểm thành viên ở mức **tích và xem điểm**.
*   Tích hợp AI gợi ý món.
*   Màn hình hàng đợi pha chế tại quầy Bar.

**3.2. Các phần Ngoài phạm vi (Out-of-scope - Sẽ không làm để tránh quá tải):**
*   **Thanh toán thực tế:** Không tích hợp cổng thanh toán thật (VNPay, Momo), chỉ làm giao diện giả lập "Thanh toán thành công". Quy tắc "không nhận được thanh toán sau 15 phút thì tự hủy đơn" chỉ được mô tả trong tài liệu nghiệp vụ.
*   **Gọi món tại quầy (POS):** Không làm; mọi đơn đều qua QR.
*   **Quản lý giao hàng phức tạp:** Không tích hợp API của các bên vận chuyển (Ahamove, Grab), chỉ lưu trạng thái đơn hàng (Đang giao/Đã giao).
*   **Kế toán / Tài chính:** Không làm sổ cái kế toán, tính lương nhân sự hay khai báo thuế.
*   **IoT / máy pha chế kết nối:** Không làm (đã đánh giá và loại bỏ, xem II.2). Ghi vào hướng phát triển.
*   **SMS thật:** OTP chỉ giả lập, không tích hợp nhà mạng / dịch vụ SMS.
*   **Đổi điểm, voucher, combo, mua 1 tặng 1:** Không làm; điểm chỉ tích lũy và hiển thị.
*   **Nhận diện khuôn mặt:** Không làm.

## 4. Danh sách Tính năng Cốt lõi (Core Features)

Dựa trên phạm vi đã chốt, hệ thống sẽ bao gồm 3 phân hệ chính:

### Phân hệ 1: Hệ thống Quản trị Trung tâm (Admin Dashboard)
*   **Quản lý danh mục & Thực đơn:** Thêm/sửa/xóa món ăn, giá bán, mô tả.
*   **Quản lý Chi nhánh & Nhân viên:** Tạo mới chi nhánh, phân quyền nhân viên (Quản lý / Thu ngân / Pha chế).
*   **Dashboard bán hàng:** Báo cáo tự tổng hợp lúc 00:05 hằng ngày: doanh thu theo ngày của từng chi nhánh, số đơn, giá trị TB/đơn, thời gian chờ TB, tỉ lệ đơn thành viên, doanh thu khuyến mãi, tỉ lệ món từ gợi ý AI, top 5 món.
*   **Quản lý Khuyến mãi (chỉ Quản trị viên):** Tạo chương trình khuyến mãi (tên, thời gian, phạm vi chi nhánh/toàn chuỗi, danh sách món + giá khuyến mãi).
*   **Màn hình quầy Bar (hàng đợi pha chế):** Hiển thị theo thời gian thực các món khách đã gọi kèm số bàn, giờ gọi, ghi chú; **sắp xếp theo thời gian gọi** để pha chế làm đúng thứ tự; pha chế bấm Bắt đầu / Xong cho từng món và bấm "Đã giao" khi đưa đồ cho khách. Thu ngân chỉ hỗ trợ khách (tra cứu, hủy & hoàn tiền), không nằm trong luồng xử lý đơn.

### Phân hệ 2: Khách hàng & Gọi món (QR Order Web App)
*   **Quét QR Order:** Khách ngồi tại bàn, dùng điện thoại quét mã QR để truy cập menu điện tử (không cần tải app).
*   **Màn hình chào – 2 lựa chọn:** (1) Xem menu ngay, không cần SĐT; (2) Nhập SĐT + mã OTP (giả lập) để tích điểm và nhận gợi ý theo sở thích. Hệ thống không lưu thông tin nhận diện thiết bị của khách.
*   **Tích điểm:** Khách thành viên được cộng điểm khi nhận đồ (1 điểm / 10.000đ; 1 điểm có giá trị 100đ, tương đương hoàn lại 1%), xem tổng điểm và giá trị quy đổi trên menu.
*   **Giỏ hàng & Đặt món:** Thêm món, ghi chú (ít đường, nhiều đá), xác nhận gửi order trực tiếp xuống quầy Bar.
*   **Theo dõi trạng thái:** Khách hàng xem được trạng thái ly nước của mình đang ở bước nào (Đang chờ / Đang pha chế / Có thể lấy).

### Phân hệ 3: Tích hợp AI (Gợi ý món thông minh)
*   **Khách không nhập SĐT:** gợi ý món bán chạy tại chi nhánh, món đang khuyến mãi, món mới; thời tiết là yếu tố phụ.
*   **Khách thành viên (đã xác thực SĐT):** gợi ý theo sở thích (món hay gọi, món tương tự món yêu thích), kết hợp bán chạy, khuyến mãi, thời tiết.
*   **Gợi ý "thường gọi kèm"** trong giỏ hàng bằng luật kết hợp (FP-Growth) khai phá từ lịch sử đơn.
