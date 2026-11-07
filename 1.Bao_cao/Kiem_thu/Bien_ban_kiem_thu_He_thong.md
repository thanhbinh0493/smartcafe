# BIÊN BẢN KIỂM THỬ HỆ THỐNG – GIAI ĐOẠN VI (KỊCH BẢN XUYÊN LUỒNG & YÊU CẦU PHI CHỨC NĂNG)

## 1. Thông tin chung
| Mục | Nội dung |
|:---|:---|
| Dự án | SmartCafe – Phần mềm quản lý chuỗi quán cà phê thông minh (Nhóm 8) |
| Giai đoạn | **VI – Kiểm thử hệ thống**, theo [Kế hoạch kiểm thử hệ thống](Ke_hoach_kiem_thu_He_thong.md) (CR-41) |
| Phiên bản | 0.9.0 – nhánh `feature/vi-kiem-thu-he-thong` (tách từ `main` sau khi gộp F8, CR-40), mã nguồn `2.San_pham/smartcafe/` |
| Ngày kiểm thử | 03/11/2026 |
| Người lập biên bản | Ngô Duy Đô (D – Tester / QA) |
| Người duyệt | Nguyễn Thanh Bình (A – PM) – đã duyệt 03/11/2026 (CR-44) |
| Tài liệu căn cứ | [III.1](../Thiet_ke_he_thong/III.1_Use_Case_Sequence.md) UC01–UC20, [III.2](../Thiet_ke_he_thong/III.2_Yeu_cau_phi_chuc_nang_Data_Model.md) NFR, [IV.1–IV.3](../Thiet_ke_he_thong/IV.3_Kien_truc_va_API.md); quyết định D1–D39 |
| Tiền đề | F0 → F8 đạt và được duyệt (9 biên bản luồng, 727 ca) |

## 2. Phạm vi
- **Kịch bản xuyên luồng** "một ngày làm việc" ở chi nhánh Cầu Giấy, 5 trình duyệt chạy cùng lúc: quản trị viên, quản lý, pha chế, thu ngân (tablet) và 3 điện thoại khách. Kịch bản đi qua UC01–UC07, UC13, UC15–UC20, kèm đối soát báo cáo ngày.
- **Toàn bộ 29 yêu cầu phi chức năng** trong III.2:
  - hiệu năng P1–P6;
  - bảo mật S1–S7;
  - độ tin cậy R1–R5;
  - khả dụng U1–U4;
  - bảo trì M1–M5.
- **Hồi quy** toàn bộ F0 → F8 sau khi sửa lỗi: pytest, Vitest và kiểm thử khói SM-01…55.
- **Ngoài phạm vi:** điện thoại thật, cổng thanh toán và SMS thật, bản demo trên cloud (không làm – D40).

## 3. Môi trường & cách chạy
- Laptop demo Windows 10, 8 luồng CPU. Docker Desktop chạy `docker compose` gồm 3 dịch vụ: `postgres:16-alpine`, backend (1 tiến trình uvicorn) và frontend/Nginx ở cổng 8080.
- **CSDL sạch** (`down -v` → `up -d --build`): tự nạp dữ liệu mẫu, gồm 5.004 đơn lịch sử / 60 ngày, 300 thành viên, 32 luật FP-Growth và 180 báo cáo ngày ([logs/ST_moi_truong.txt](logs/ST_moi_truong.txt)).
- Trình duyệt dùng Playwright 1.64 với Microsoft Edge (Chromium) và WebKit (nhân Safari). Mạng 4G được giả lập qua Chrome DevTools Protocol.
- **Lệnh chạy lại toàn bộ:** `bash system_test/chay_tat_ca.sh`, chạy trong `2.San_pham/smartcafe`. Script dựng lại CSDL sạch, chạy 5 bộ ST, kiểm thử khói, pytest và Vitest (có đo độ bao phủ); log ghi vào [logs/](logs/). Hướng dẫn chi tiết ở [system_test/README.md](../../2.San_pham/smartcafe/system_test/README.md).
- Máy phát tải chạy chung laptop với hệ thống, nên số đo hiệu năng là **cận dưới** của năng lực thật.

## 4. Danh sách test case
Mỗi dòng ứng với một lần kiểm tra trong script (`rep.check("ST-xx", ...)`) hoặc một test tự động. Cột "Kết quả đo" chép từ log của lượt chạy chính thức.

### 4.1. Kịch bản xuyên luồng – `system_test/st_kich_ban.py` ([log](logs/ST_kich_ban_xuyen_luong.txt))
| Mã | Nội dung | Kết quả đo | KQ |
|:---|:---|:---|:---:|
| ST-01 | UC15 → UC02: quản trị viên tạo KM Trà đào cam sả → điện thoại khách **đang mở menu** thấy giá KM ngay (không tải lại) | KM tạo 201; giá KM 26.000đ hiện trên menu | Đạt |
| ST-02 | UC13 → UC02/UC03: quản lý tắt "Còn hàng" Bạc xỉu → khách thấy "Tạm hết" ngay; gợi ý AI không còn món này | Đúng | Đạt |
| ST-03 | Khách ẩn danh chọn món KM + món ở "Gợi ý cho bạn" + món ở "Thường gọi kèm" rồi thanh toán | CG-0001: Trà đào 26.000đ (gắn KM), Xoài đá xay & Bánh mousse gắn `is_recommended`; tổng giỏ = tổng server 114.000đ; 1 lượt gợi ý gắn với đơn | Đạt |
| ST-04 | UC17–UC19 → UC06: pha chế Bắt đầu / Xong / Đã giao trên Bar → khách thấy "Đang pha chế" → "Có thể lấy" realtime | Lịch sử trạng thái PENDING_PAYMENT → PAID → PREPARING → READY → COMPLETED | Đạt |
| ST-05 | UC01/UC07: thành viên SĐT demo xác thực OTP → menu có "Bạn hay gọi" → đặt món → nhận đồ thì được cộng điểm realtime | CG-0002 50.000đ → +5 điểm (133 → 138), 1 giao dịch điểm | Đạt |
| ST-06 | NFR-R4: bấm "Đã giao" lần 2 cho cùng đơn | 409 `INVALID_STATE_TRANSITION`, điểm không đổi | Đạt |
| ST-07 | UC20: thu ngân (tablet) hủy đơn & hoàn tiền → món rời hàng đợi Bar, điện thoại khách báo "Đơn đã hủy – đã hoàn tiền" | Thanh toán CG-0003 → `REFUNDED` | Đạt |
| ST-08 | UC13/UC15: bật lại "Còn hàng", tắt KM → điện thoại trở lại giá thường, đặt lại được Bạc xỉu | Đúng | Đạt |
| ST-09 | UC16: chạy thử job báo cáo cho **hôm nay** trong một transaction rồi rollback, so với dữ liệu đơn của kịch bản | 2 đơn, 1 hủy, doanh thu 164.000đ khớp bảng `orders`; doanh thu KM 76.000đ, đơn thành viên 50%, món từ gợi ý 50% | Đạt |
| ST-10 | UC16: đối soát **mọi dòng** `daily_sales_reports` với bảng `orders` (số đơn, đơn hủy, doanh thu) | 180 dòng (04/09 → 02/11), lệch 0 | Đạt |

### 4.2. Hiệu năng & tải – `system_test/st_hieu_nang.py` ([log](logs/ST_hieu_nang_tai.txt))
Mô hình tải theo **D39**: 50 người dùng ảo vào lệch nhau. Mỗi lượt gồm quét QR → menu → gợi ý (1/5 khách ở Cầu Giấy là thành viên, giỏ hàng ngẫu nhiên 0–2 món) → xem đơn, rồi nghỉ 3–5 giây.
| Mã | Nội dung | Kết quả đo | KQ |
|:---|:---|:---|:---:|
| ST-30 | 50 người dùng đồng thời trong 60 giây: mọi request trả 200 | 3.028 request ≈ 47 req/s, 0 lỗi | Đạt |
| ST-31 | NFR-P2: API đọc (quét QR, menu, xem đơn) p95 ≤ 300 ms | p95 **63 ms** (QR 67, menu 52, xem đơn 70), tối đa 148 ms | Đạt |
| ST-32 | NFR-P3: API gợi ý p95 ≤ 500 ms | p95 **90 ms**, tối đa 160 ms | Đạt |
| ST-38 | Quá tải tham khảo: 50 người nghỉ 0,5–1,5 giây (≈ 3,5 lần tải chuẩn), yêu cầu không lỗi | 9.704 request ≈ 157 req/s, 0 lỗi; p95 đọc 191 ms, gợi ý 209 ms | Đạt |
| ST-33 | NFR-R4 / mã đơn: 20 khách bấm đặt món **cùng lúc** ở 1 chi nhánh | 20/20 đơn, 20 mã khác nhau (CG-0022 … CG-0041) | Đạt |
| ST-34 | NFR-P5: 180 đơn (60/chi nhánh × 3) rải trong 1 "giờ" nén còn 60 giây; tạo + thanh toán p95 ≤ 1 giây | 180/180, p95 173 ms, 0 lỗi | Đạt |
| ST-35 | Hàng đợi Bar có đủ mọi đơn đã trả tiền; pha chế xử lý hết thì hàng đợi trống | Thiếu 0; 203 đơn xử lý trong 22 giây; còn 0 món | Đạt |
| ST-36 | NFR-P6: API dashboard 30 ngày × 3 chi nhánh p95 ≤ 2 giây | p95 17 ms (90 điểm dữ liệu) | Đạt |
| ST-37 | NFR-P6: job tổng hợp 1 ngày ≤ 1 phút | 1 ngày (3 chi nhánh) 86 ms; tính lại cả 60 ngày (180 dòng) 0,93 giây | Đạt |

### 4.3. Bảo mật – `system_test/st_bao_mat.py` ([log](logs/ST_bao_mat.txt)) và `backend/tests/st/test_ws_reject.py`
| Mã | Nội dung | Kết quả đo | KQ |
|:---|:---|:---|:---:|
| ST-40 | NFR-S1: mật khẩu băm bcrypt cost ≥ 10, không lưu dạng rõ (đọc CSDL) | 13/13 tài khoản, cost 12 | Đạt |
| ST-41 | NFR-S2: JWT nhân viên hết hạn sau 8 giờ; JWT khách thành viên (role CUSTOMER) sau 1 giờ | 8 giờ / 60 phút | Đạt |
| ST-42 | NFR-S2: không token / token rác / sửa payload giữ chữ ký cũ / `alg=none` gọi 6 API nhân viên | 24/24 lần → 401 | Đạt |
| ST-43 | NFR-S2: token khách thành viên gọi API nhân viên | 6/6 → 403 | Đạt |
| ST-44 | NFR-S2: ma trận RBAC – 12 thao tác sai vai trò hoặc khác chi nhánh | 12/12 → 403 | Đạt |
| ST-45 | NFR-S2: WebSocket trái phép (Bar không token / token rác / pha chế CG vào Bar HD / sai access_token đơn) – **hồi quy BUG-ST-01** | Mã đóng 4401 / 4401 / 4403 / 4404 tới được client | Đạt |
| ST-55 | (pytest, 5 bộ tham số) server accept rồi mới close kèm mã khi từ chối WebSocket – hồi quy BUG-ST-01 | 5/5 (khi bỏ bản sửa thì 5/5 không đạt) | Đạt |
| ST-46 | NFR-S3: `qr_token` bàn & `access_token` đơn ≥ 128 bit, không trùng | 60 QR + 15 đơn, ngắn nhất 22 ký tự | Đạt |
| ST-47 | NFR-S3: đổi ID đơn trên URL (đơn của người khác, ID ± 1) với access_token của mình | Xem 404 ×3, thanh toán hộ 404 | Đạt |
| ST-48 | NFR-S4: OTP 6 số, lưu băm HMAC-SHA256, hết hạn 5 phút | Đúng (CSDL chỉ có chuỗi băm 64 ký tự hex) | Đạt |
| ST-49 | NFR-S4: gửi lại trong 60 giây; nhập sai 5 lần | Gửi lại → 429; số lần còn lại 4, 3, 2, 1, 0; nhập đúng sau đó → `LOCKED` | Đạt |
| ST-50 | NFR-S4: phản hồi gửi OTP của SĐT đã là thành viên và SĐT mới giống hệt nhau | Cùng khóa, cùng thời hạn | Đạt |
| ST-51 | NFR-S5: 20 request SQL injection (tìm đơn theo mã / bàn, mã QR, SĐT, đăng nhập) | Không lỗi 500, không lộ dữ liệu; bảng orders còn nguyên | Đạt |
| ST-52 | NFR-S5: đặt món với số lượng 0 / âm / 1000 / chữ, giỏ rỗng, món không tồn tại, ghi chú 5.000 ký tự | 422 ×6, 409 ×1; không tạo đơn | Đạt |
| ST-53 | NFR-S6: client gửi `expected_total` giả và `unit_price` = 1đ | 409 `PRICE_CHANGED`; tổng server 50.000đ (đúng) | Đạt |
| ST-54 | NFR-S7: chỉ lưu SĐT sau khi xác thực OTP; không cookie; không cột định danh thiết bị | Trước xác thực 0 dòng, sau 1 dòng; không có Set-Cookie | Đạt |

### 4.4. Giao diện & độ tin cậy – `system_test/st_giao_dien.py` ([log](logs/ST_giao_dien_trinh_duyet.txt))
| Mã | Nội dung | Kết quả đo | KQ |
|:---|:---|:---|:---:|
| ST-60 | NFR-P1: FCP trang chào sau khi quét QR ≤ 2 giây trên "Fast 4G" (RTT 165 ms, 9 Mbps, CPU chậm 4 lần), 5 lần không cache; không tải mã Web Admin / Recharts – **hồi quy BUG-ST-02** | FCP 780–816 ms; JS 76 KB gzip (1 file); tham khảo "Slow 4G": 1.940–1.952 ms | Đạt |
| ST-61 | NFR-U2: khách ẩn danh đặt đơn 2 món và thanh toán xong trong ≤ 6 lần chạm từ màn hình chào | **5 lần chạm** ([ảnh](img/ST_U2_dat_2_mon_5_cham.png)) | Đạt |
| ST-62 | NFR-U1: 5 màn hình khách ở khổ 360 / 390 / 430 px không tràn ngang | 15/15 | Đạt |
| ST-63 | NFR-U1: nhân WebKit (Safari iOS) – đặt món, thanh toán, theo dõi đơn | Hoạt động, không tràn ngang ([ảnh](img/ST_U1_webkit_theo_doi_don.png)) | Đạt |
| ST-64 | NFR-P4: đơn vừa thanh toán hiện trên hàng đợi Bar ≤ 2 giây | 41–102 ms (5 lần) | Đạt |
| ST-65 | NFR-U3: Bar – chữ ≥ 18px, món chờ > 10 phút tô đỏ, có âm báo khi có món mới – **hồi quy BUG-ST-03** | 18px; món chờ 11 phút tô đỏ; âm báo có ([ảnh](img/ST_U3_man_hinh_bar.png)) | Đạt |
| ST-66 | NFR-P4: pha chế bấm "Xong" → điện thoại hiện "Đồ uống đã sẵn sàng" ≤ 2 giây | 51–59 ms (3 lần) | Đạt |
| ST-67 | NFR-R2: cắt WebSocket của Bar → cảnh báo "Mất kết nối", hàng đợi tự tải lại qua REST – **hồi quy BUG-ST-04** | Cảnh báo có; đơn mới hiện sau 8,6 giây khi không có WebSocket ([ảnh](img/ST_R2_bar_mat_ket_noi.png)) | Đạt |
| ST-68 | NFR-R3: điện thoại mất WebSocket (hiện "Đang kết nối lại…"), có lại kết nối thì đồng bộ trạng thái mới mà không cần tải lại trang | Hiện "sẵn sàng" sau 2,4 giây | Đạt |
| ST-69 | NFR-R1: API gợi ý trả lỗi 500 → menu và giỏ vẫn dùng được, đặt + thanh toán thành công | 3 lần gọi gợi ý lỗi, đơn vẫn thành công, không có thông báo lỗi | Đạt |
| ST-70 | NFR-U4: `lang=vi`, không lẫn chữ tiếng Anh (9 màn hình), giá dạng 45.000đ | 35/35 giá đúng định dạng, 0 chữ tiếng Anh | Đạt |
| ST-71 | NFR-P6: dashboard hiển thị ≤ 2 giây (mở sau đăng nhập; đổi sang 30 ngày × 3 chi nhánh) | 161 ms; 36 ms | Đạt |
| ST-72 | NFR-S5 (XSS): tên món chứa `<img onerror=…>` do quản trị nhập | Hiện như chữ thường, script không chạy, 0 thẻ img chèn vào | Đạt |

### 4.5. Vận hành & bảo trì – `system_test/st_van_hanh.py` ([log](logs/ST_van_hanh.txt))
| Mã | Nội dung | Kết quả đo | KQ |
|:---|:---|:---|:---:|
| ST-80 | NFR-M1: Swagger `/docs` tự sinh; backend chia module theo nghiệp vụ | 38 đường dẫn API, 10 nhóm; 11 module | Đạt |
| ST-81 | NFR-M2: CSDL ở đúng migration mới nhất (1 head) | `0003 (head)` | Đạt |
| ST-82 | NFR-R5: `scripts/backup_db.ps1` sao lưu (pg_dump); khôi phục vào CSDL tạm → số dòng 11 bảng chính khớp | 854 KB; orders 5.227 → 5.227; lệch 0 | Đạt |
| ST-83 | NFR-M4: SMS và cổng thanh toán đi qua interface (Protocol), bản giả lập là một cài đặt | `SmsSender`, `PaymentGateway` | Đạt |
| ST-84 | NFR-M5: chạy toàn hệ thống bằng `docker compose`; có `.env.example` | 3/3 dịch vụ chạy; 19 biến | Đạt |
| – | NFR-M3: độ bao phủ unit test service Order và Recommend ≥ 60% | `order/service.py` 99%, `recommend/service.py` 100% (Mục 5) | Đạt |

### 4.6. Test hồi quy cho lỗi và thay đổi của giai đoạn VI
| Mã | Vị trí | Nội dung | KQ |
|:---|:---|:---|:---:|
| ST-FE-01 | `BarPage.test.tsx` | BUG-ST-04: mất WebSocket → "Mất kết nối", tải lại hàng đợi mỗi 10 giây, đơn mới vẫn hiện (khi bỏ bản sửa: không đạt) | Đạt |
| ST-FE-02 | `BarPage.test.tsx` | BUG-ST-03: chữ hàng đợi và cột "Có thể lấy" `text-lg` (18px) (khi bỏ bản sửa: không đạt) | Đạt |
| ST-FE-03 | `AdminPages2.test.tsx` | BUG-ST-05: `/ws/menu` rớt đúng lúc quản lý tắt món → kết nối lại thì tự tải lại menu (khi bỏ bản sửa: không đạt) | Đạt |
| ST-90 | `tests/st/test_cache.py` | D38: menu dùng lại cache (sửa thẳng CSDL vẫn trả bản cũ); quản lý đổi giá / hết hàng qua API → menu và gợi ý thấy ngay | Đạt |
| ST-91 | 〃 | Cache menu hết hạn đúng lúc một KM bắt đầu (không giữ quá mốc đổi giá) | Đạt |
| ST-92 | 〃 | Khóa bàn → quét QR báo không hợp lệ ngay, dù kết quả quét trước đó đã nằm trong cache | Đạt |
| ST-93 | 〃 | NFR-S6: tạo đơn luôn tính giá từ CSDL, không dùng menu trong cache (giá cũ → `PRICE_CHANGED`) | Đạt |
| ST-94 | 〃 | Cache bị xóa trong lúc đang tải → không lưu lại bản cũ (chống ghi đè do đua) | Đạt |
| ST-95 | 〃 | Học lại luật FP-Growth → xóa cache luật | Đạt |

## 5. Tổng hợp kết quả & độ bao phủ
| Nhóm | Số ca | Đạt | Không đạt |
|:---|:---:|:---:|:---:|
| Kịch bản xuyên luồng ST-01…10 | 10 | 10 | 0 |
| Hiệu năng & tải ST-30…38 | 9 | 9 | 0 |
| Bảo mật ST-40…54 + ST-55 (5 bộ tham số) | 20 | 20 | 0 |
| Giao diện & độ tin cậy ST-60…72 | 13 | 13 | 0 |
| Vận hành & bảo trì ST-80…84 | 5 | 5 | 0 |
| Hồi quy giai đoạn VI ST-FE-01…03, ST-90…95 | 9 | 9 | 0 |
| **Tổng kiểm thử hệ thống** | **66** | **66** | **0** |
| Hồi quy backend F0 → F8 (pytest, PostgreSQL thật) – [log](logs/ST_hoi_quy_backend_toan_bo.txt) | 481 | 481 | 0 |
| Hồi quy frontend F0 → F8 (Vitest) – [log](logs/ST_hoi_quy_frontend_vitest.txt) | 128 | 128 | 0 |
| Hồi quy kiểm thử khói SM-01…55 – [log](logs/ST_hoi_quy_smoke_test.txt) | 55 | 55 | 0 |

- **Độ bao phủ:** backend 99% (2.677 câu lệnh, `app/core/cache.py` 100%); frontend 98,5% câu lệnh, 92,3% nhánh.
- Vitest chạy kèm đo độ bao phủ 3 lần liên tiếp, đều 131/131.
- **Theo yêu cầu phi chức năng:** 29/29 NFR có ca kiểm thử và đều đạt. NFR-P2/P3 đạt theo mô hình tải đã chốt ở D39; ca quá tải ST-38 không có lỗi.

## 6. Lỗi phát hiện
| Mã lỗi | Mức độ | Mô tả | Nguyên nhân | Cách sửa | Test hồi quy |
|:---|:---|:---|:---|:---|:---|
| BUG-ST-01 | Thấp | WebSocket bị từ chối (token sai / hết hạn, khác chi nhánh, sai mã đơn) thì trình duyệt chỉ nhận mã 1006, không nhận 4401 / 4403 / 4404. Màn hình Bar có token hết hạn cứ thử kết nối lại mãi | Server gọi `close()` trước `accept()` nên uvicorn trả HTTP 403 ở bước bắt tay. TestClient của F2/F3 vẫn thấy mã đóng nên test luồng không phát hiện được | Thêm `hub.reject()`: accept rồi mới close kèm mã (dùng cho `/ws/bar`, `/ws/order`, `/ws/menu`) | ST-55, ST-45 |
| BUG-ST-02 | Trung bình | Trang QR của khách tải cả Web Admin và thư viện biểu đồ Recharts (gói JS 677 KB). Trên 4G chậm, FCP 1,95–2,11 giây, sát và có lần vượt ngưỡng 2 giây | Mọi trang nằm chung một gói JS; từ F8 thêm Recharts | Tách gói: Web Admin (`AdminRoutes`) và Dashboard tải lazy. Gói của khách còn 202 KB (76 KB gzip). Test nạp sẵn module lazy (`src/test/setup.ts`) | ST-60 |
| BUG-ST-03 | Trung bình | NFR-U3: chữ hàng đợi Bar chỉ 14px, yêu cầu ≥ 18px | Bảng hàng đợi dùng `text-sm` | Bảng hàng đợi và cột "Có thể lấy" đổi sang `text-lg` (18px) | ST-FE-02, ST-65 |
| BUG-ST-04 | Trung bình | NFR-R2: Bar mất WebSocket chỉ hiện "Đang kết nối lại…", không tải lại hàng đợi qua REST; nếu WebSocket bị chặn lâu thì đơn mới không hiện | Chỉ tải lại khi kết nối lại thành công | Khi mất kết nối: nhãn "● Mất kết nối" + dải cảnh báo, tải lại hàng đợi qua REST mỗi 10 giây (`POLL_MS`) | ST-FE-01, ST-67 |
| BUG-ST-05 | Trung bình | NFR-R3: menu khách không đồng bộ lại sau khi `/ws/menu` kết nối lại, nên bỏ lỡ thay đổi menu / giá / hết hàng xảy ra lúc mất mạng | `MenuPage` không truyền `onOpen` cho `useSocket` (trang Bar và trang theo dõi đơn đã có) | Mỗi lần kết nối (lại) tải lại menu và gợi ý | ST-FE-03 |
| BUG-ST-06 | Trung bình | NFR-P2/P3: 50 khách thao tác ~1 giây/lần thì p95 ≈ 1 giây (đọc 992 ms, gợi ý 982 ms). Backend dùng hết 1 lõi CPU, ~85 req/s | Backend 1 tiến trình (WebSocket hub trong bộ nhớ); mỗi lượt khách tốn ~36 ms CPU, đọc lại menu / bán chạy / luật / nhãn đơn từ CSDL mỗi request | **D38**: cache trong tiến trình (menu, quét QR, nhãn đơn, bán chạy, luật), xóa ngay khi quản trị đổi dữ liệu; menu trả JSON dựng sẵn; xem đơn tải món 1 lần. Thông lượng tăng lên 140–157 req/s. **D39**: chốt mô hình tải 3–5 giây/thao tác (P23, P24) | ST-30…32, ST-38, ST-90…95 |

*Diễn biến khi kiểm thử (không phải lỗi phần mềm):*
- *ST-08 trượt ở lần chạy đầu vì chính script: khi Bạc xỉu bật lại, thẻ gợi ý "Bạc xỉu" nằm phía trên dòng menu nên bị chọn nhầm. Đã giới hạn locator trong dòng menu. Trong lúc điều tra lỗi này, đọc mã nguồn phát hiện ra BUG-ST-05.*
- *Một lần chạy lại kịch bản bị chặn OTP: SĐT demo đã dùng đủ 5 mã trong 1 giờ, hoặc gửi lại chưa đủ 60 giây. Đây là đúng NFR-S4. Script đã được sửa để tự chờ 60 giây, và lượt chính thức chạy trên CSDL sạch.*
- *Với script thử mất mạng, cách chặn bằng `route_web_socket` của Playwright làm treo trình duyệt khi đóng kết nối ngay trong handler. Đã thay bằng cách bọc `window.WebSocket`; REST vẫn chạy bình thường.*

## 7. Tồn tại / ghi chú
- **Năng lực 1 tiến trình:** khoảng 140–157 req/s, đo trên laptop phát tải chung máy (ST-38). Tải gấp khoảng 3,5 lần mô hình D39 vẫn không lỗi, chỉ chậm hơn (p95 ~200 ms). Nếu cần hơn nữa thì chạy nhiều tiến trình và chuyển WebSocket hub sang Redis pub/sub hoặc PostgreSQL LISTEN/NOTIFY; đây là hướng mở rộng đã ghi ở IV.3.
- **Độ trễ cache (D38):** số liệu "bán chạy" dùng cho gợi ý trễ tối đa 60 giây. Menu, giá, còn hàng, KM, bàn và chi nhánh cập nhật ngay vì quản trị đổi là cache bị xóa. Tạo đơn luôn tính giá từ CSDL.
- **Hiệu năng khi tải tăng đột biến:** p95 đạt yêu cầu nhưng giá trị lớn nhất có lúc tới ~150 ms. Một lượt đo trước đó (khi máy đang chạy tác vụ khác) có giá trị lớn nhất 1,6 giây.
- **NFR-U1:** kiểm thử trên khung giả lập điện thoại của Edge và nhân WebKit, chưa thử Safari trên iPhone thật. Nên thử 1 lần bằng điện thoại thật qua Wi-Fi (`PUBLIC_BASE_URL` = IP laptop) trước buổi nghiệm thu.
- **NFR-P1:** đo bằng giả lập mạng của Chrome DevTools Protocol, không phải Lighthouse. Ở "Slow 4G" (chặt hơn yêu cầu), FCP khoảng 1,94–1,95 giây, vẫn dưới 2 giây.
- **`.env.example`:** đã có 19 biến cấu hình chính. Một số biến tinh chỉnh (`RULES_*`, `REC_*`, `REPORT_JOB_*`, `UPLOAD_DIR`, `CORS_ORIGINS`…) chưa có, nhưng đều có giá trị mặc định hợp lý trong `config.py`.
- **`JWT_SECRET` mặc định** trong `.env.example` là `change-me-please…`. Bắt buộc đổi nếu demo trên mạng ngoài máy cá nhân (ghi chú có sẵn trong file).
- **Port 8000 mở ra host** để xem Swagger. Khi demo trên mạng chung thì chỉ nên mở 8080.
- **Dữ liệu demo:** các script ST tạo thêm ~230 đơn thử. Trước buổi demo chạy `docker compose down -v` → `up -d`, rồi sao lưu bằng `scripts/backup_db.ps1` (NFR-R5).
- **P12** đã chốt → D40 (CR-44): chỉ demo trên laptop, không làm bản dự phòng trên cloud.

## 8. Kết luận
**Giai đoạn VI – Kiểm thử hệ thống: ĐẠT.**
- 66/66 ca kiểm thử hệ thống đạt.
- Hồi quy F0 → F8 đạt 664/664 (481 backend + 128 frontend + 55 kiểm thử khói).
- 29/29 yêu cầu phi chức năng đạt.
- Phát hiện 6 lỗi (1 Thấp, 5 Trung bình), tất cả đã sửa và có test hồi quy; không còn lỗi Nghiêm trọng hay Cao.
- PM đã chốt P23 → D38 (cache API đọc) và P24 → D39 (mô hình tải), ghi ở CR-42, CR-43.
- PM đã duyệt (CR-44); nhánh `feature/vi-kiem-thu-he-thong` đã gộp vào `main`.

| Vai trò | Họ tên | Ngày | Ký xác nhận |
|:---|:---|:---|:---|
| Người lập (Tester / QA) | Ngô Duy Đô (D) | 03/11/2026 | |
| PM duyệt | Nguyễn Thanh Bình (A) | 03/11/2026 | |
