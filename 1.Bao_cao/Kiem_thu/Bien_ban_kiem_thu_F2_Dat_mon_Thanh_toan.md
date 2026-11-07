# BIÊN BẢN KIỂM THỬ – LUỒNG F2: ĐẶT MÓN → THANH TOÁN GIẢ LẬP → THEO DÕI ĐƠN

## 1. Thông tin chung
| Mục | Nội dung |
|:---|:---|
| Dự án | SmartCafe – Phần mềm quản lý chuỗi quán cà phê thông minh (Nhóm 8) |
| Luồng | **F2 – Đặt món & thanh toán giả lập** (khách ẩn danh): UC04, UC05, UC06 – sơ đồ SD03 |
| Phiên bản | 0.2.0 – nhánh `feature/f2-dat-mon`, mã nguồn `2.San_pham/smartcafe/` |
| Ngày kiểm thử | 02/11/2026 |
| Người lập biên bản | Ngô Duy Đô (D – Tester / QA) |
| Người duyệt | Nguyễn Thanh Bình (A – PM) – đã duyệt 03/11/2026 (CR-34) |
| Tài liệu căn cứ | [III.1 UC04–UC06](../Thiet_ke_he_thong/III.1_Use_Case_Sequence.md), SD03, [IV.2 W02, W03](../Thiet_ke_he_thong/IV.2_Thiet_ke_giao_dien.md), [IV.3 API + WebSocket](../Thiet_ke_he_thong/IV.3_Kien_truc_va_API.md), [II.2 Mock Payment](../Thiet_ke_he_thong/II.2_Nghien_cuu_cong_nghe.md), NFR-S6, NFR-R3, NFR-R4, NFR-P4, NFR-U2, NFR-M4; quyết định D22, D27, **D28** |
| Tiền đề | F0, F1 đạt ([F0](Bien_ban_kiem_thu_F0_Nen_tang.md), [F1](Bien_ban_kiem_thu_F1_QR_Menu.md)) |

## 2. Phạm vi
**Trong phạm vi**
- `POST /api/public/orders`: kiểm tra bàn, còn hàng, giới hạn số lượng; **server tự tính giá** (giá chi nhánh / KM, NFR-S6); báo **giá thay đổi** khi tổng khách thấy khác tổng server (UC05 – 3b); chốt `original_price`, `unit_price`, `promotion_id`, `is_recommended`; **mã đơn theo ngày** `CG-0001` (D28) kể cả khi nhiều bàn đặt cùng lúc.
- `POST /api/public/orders/{id}/pay`: thanh toán giả lập qua interface `PaymentGateway` (NFR-M4); thất bại khi số tiền tận cùng 999; thử lại; chống thanh toán 2 lần; lịch sử trạng thái.
- `GET /api/public/orders/{id}?token=`: xem đơn, **vị trí trong hàng đợi**; bảo vệ bằng `access_token`.
- WebSocket `/ws/order/{id}?token=`: ảnh chụp đơn khi kết nối, sự kiện `ORDER_PAID`; kênh `bar:{branch_id}` nhận `QUEUE_ITEM_ADDED` (dùng ở F3).
- Migration `0002` (cột `order_date`, UNIQUE (order_code, order_date)).
- Giao diện: nút "+" và thanh giỏ hàng trên W01; **W02** giỏ hàng & thanh toán; **W03** theo dõi đơn (tự kết nối lại, banner "Có thể lấy" + rung, đơn hủy).

**Ngoài phạm vi**: khách thành viên & "+X điểm" (F4), khối "Thường gọi kèm" (F7), thay đổi trạng thái pha chế (F3 – ở F2 mới kiểm phía khách nhận sự kiện bằng dữ liệu giả lập), hủy đơn & hoàn tiền (F5), job tự hủy đơn sau 15 phút (D22 – chỉ mô tả).

## 3. Môi trường & cách chạy
Giống [biên bản F0 – Mục 3](Bien_ban_kiem_thu_F0_Nen_tang.md#3-môi-trường--cách-chạy). Bổ sung: thư viện `websockets` (đi kèm `uvicorn[standard]`) cho kiểm thử khói WebSocket; Playwright 1.64.1 + Microsoft Edge giả lập iPhone 14 (390×844) cho kiểm thử đầu-cuối trên trình duyệt.
```powershell
cd backend;  .\.venv\Scripts\python -m pytest -v tests/f2
cd frontend; npx vitest run src/pages/qr/CartPage.test.tsx src/pages/qr/OrderPage.test.tsx
cd backend;  .\.venv\Scripts\python -m scripts.smoke_test --qr-token <token>
```

## 4. Danh sách test case

### 4.1. Backend – Tạo đơn UC04/UC05 (cấp: Tích hợp, PostgreSQL thật)
| Mã TC | Căn cứ | Mô tả / dữ liệu | Kết quả mong đợi | Kết quả thực tế | KQ | Test tự động |
|:---|:---|:---|:---|:---|:---:|:---|
| F2-01 | UC05, SD03 | Bàn CG-05 đặt 2 Cà phê sữa đá (29.000, ghi chú "ít đường") + 1 Trà đào (KM 45.000 → 36.000) | 201; PENDING_PAYMENT; mã `CG-0001`; `access_token` ≥ 22 ký tự; tạm tính 103.000, giảm 9.000, tổng 94.000; chốt giá gốc/giá bán/KM từng món; món WAITING; lịch sử `NULL → PENDING_PAYMENT` (CUSTOMER) | Đúng | Đạt | `test_create_order.py::test_F2_01_...` |
| F2-02 | NFR-S6 | Client gửi kèm `unit_price: 1`, `total: 1` | Bỏ qua, tổng do server tính (29.000) | Đúng | Đạt | `test_F2_02_...` |
| F2-03 | D3 | HD đặt giá riêng 27.000 | Đơn HD 27.000, đơn CG 29.000 | Đúng | Đạt | `test_F2_03_...` |
| F2-04 | UC05 – 3a | Có món CG đặt "Tạm hết" | 409 `ITEM_UNAVAILABLE`, `item_ids`, thông báo có tên món; **không tạo đơn** | Đúng | Đạt | `test_F2_04_...` |
| F2-05 | UC05 – 3a | Món ngừng bán / mã món không tồn tại | 409 `ITEM_UNAVAILABLE` | Đúng | Đạt | `test_F2_05_...` |
| F2-06 | UC01 – 2a | QR sai / bàn bị khóa | 404 `TABLE_NOT_FOUND` | Đúng | Đạt | `test_F2_06_...` |
| F2-07a…e | UC05 quy tắc, NFR-S5 | Số lượng 0; số lượng 21; giỏ rỗng; ghi chú món 256 ký tự; ghi chú đơn 256 ký tự | 422 `VALIDATION_ERROR`, không tạo đơn | Đúng cả 5 | Đạt | `test_F2_07_...[5 tham số]` |
| F2-08 | UC05 quy tắc | Cùng 1 món tách 2 dòng 15 + 6 ly (ghi chú khác nhau); sau đó 15 + 5 | 21 ly → 422 `QUANTITY_LIMIT`; 20 ly → 201 | Đúng | Đạt | `test_F2_08_...` |
| F2-09 | UC05 – 3b | `expected_total` = tổng server | 201 | Đúng | Đạt | `test_F2_09_...` |
| F2-10 | UC05 – 3b | Khách thấy 36.000 (KM) nhưng KM vừa bị tắt | 409 `PRICE_CHANGED`, `details.total` = 45.000 + giá mới từng món; không tạo đơn | Đúng | Đạt | `test_F2_10_...` |
| F2-11 | IV.1 (`is_recommended`) | Gửi 1 món có `is_recommended: true` | Lưu đúng cờ từng món (đo hiệu quả AI ở F8) | Đúng | Đạt | `test_F2_11_...` |

### 4.2. Backend – Mã đơn theo ngày (D28, CR-32)
| Mã TC | Mô tả / dữ liệu | Kết quả mong đợi | Kết quả thực tế | KQ | Test tự động |
|:---|:---|:---|:---|:---:|:---|
| F2-12 | Đặt lần lượt CG, CG, HD, CG | `CG-0001`, `CG-0002`, `HD-0001`, `CG-0003` (đếm riêng từng chi nhánh) | Đúng | Đạt | `test_order_code.py::test_F2_12_...` |
| F2-13 | Hôm qua đã có CG-0001…0003; hôm nay đặt đơn đầu | Mã `CG-0001`, `order_date` = hôm nay (giờ VN) | Đúng | Đạt | `test_F2_13_...` |
| F2-14 | Chèn trực tiếp 2 đơn `CG-0001` cùng ngày / khác ngày | Khác ngày: hợp lệ; cùng ngày: CSDL từ chối (UNIQUE) | Đúng | Đạt | `test_F2_14_...` |
| F2-29 | **12 bàn đặt đơn đồng thời** (12 kết nối CSDL song song) | 12 mã `CC-0001…0012`, không trùng, không lỗi | Đúng. *Đối chứng: tạm bỏ khóa advisory → test báo lỗi `UniqueViolation`, chứng minh test phát hiện được lỗi tranh chấp* | Đạt | `test_concurrency.py::test_F2_29_...` |

### 4.3. Backend – Thanh toán giả lập UC05 (SD03 bước 10–17)
| Mã TC | Căn cứ | Mô tả / dữ liệu | Kết quả mong đợi | Kết quả thực tế | KQ | Test tự động |
|:---|:---|:---|:---|:---|:---:|:---|
| F2-15 | UC05, NFR-R4 | Thanh toán thẻ (MOCK_CARD) đơn 94.000 | 200, PAID, `paid_at`, `transaction_ref` `MOCK-…`; `payments` SUCCESS đúng số tiền & phương thức; lịch sử `PENDING_PAYMENT → PAID` | Đúng | Đạt | `test_payment.py::test_F2_15_...` |
| F2-16 | II.2, UC05 – 5a | Đơn 29.999đ (tận cùng 999) | 402 `PAYMENT_FAILED`; đơn vẫn PENDING_PAYMENT, chưa có `paid_at`; lưu bản ghi FAILED | Đúng | Đạt | `test_F2_16_...` |
| F2-17 | UC05 – 5a | Cổng thanh toán lần 1 lỗi, lần 2 thành công (giả lập qua interface) | Lần 2 thành công; chỉ 1 bản ghi `payments` (SUCCESS, mã giao dịch lần 2) | Đúng | Đạt | `test_F2_17_...` |
| F2-18 | NFR-R4 | Thanh toán lần 2 cho đơn đã PAID | 409 `INVALID_STATE_TRANSITION` "Đơn đã được thanh toán"; không trừ tiền 2 lần | Đúng | Đạt | `test_F2_18_...` |
| F2-19 | UC06 bảo mật | Sai `access_token` khi thanh toán / xem đơn; đúng token nhưng sai mã đơn | 404 `ORDER_NOT_FOUND` (không lộ đơn có tồn tại) | Đúng | Đạt | `test_F2_19_...` |
| F2-20 | NFR-S5 | Phương thức `TIEN_MAT` | 422 | Đúng | Đạt | `test_F2_20_...` |
| F2-21 | II.2, NFR-M4 | `MockPaymentGateway`: 94.000, 1.000 / 29.999, 999; 50 lần lấy mã giao dịch; hoàn tiền | Thành công / thất bại đúng quy tắc 999; 50 mã khác nhau; refund thành công | Đúng | Đạt | `test_F2_21_...` |

### 4.4. Backend – Theo dõi đơn UC06 & realtime
| Mã TC | Căn cứ | Mô tả / dữ liệu | Kết quả mong đợi | Kết quả thực tế | KQ | Test tự động |
|:---|:---|:---|:---|:---|:---:|:---|
| F2-22 | UC06 | Xem đơn đã thanh toán | Đúng mã, trạng thái, chi nhánh, bàn, tạm tính / giảm / tổng, từng món + trạng thái | Đúng | Đạt | `test_tracking.py::test_F2_22_...` |
| F2-23 | UC06, W03 | CG: 3 đơn đã thanh toán + 1 đơn chưa thanh toán; HD: 1 đơn | Vị trí CG lần lượt 1, 2, 3; đơn chưa thanh toán = không có vị trí; HD tính riêng = 1 | Đúng | Đạt | `test_F2_23_...` |
| F2-24 | UC06 bảo mật | Mở WebSocket với token sai | Bị đóng với mã 4404 | Đúng | Đạt | `test_F2_24_...` |
| F2-25 | UC06, NFR-R3 | Mở WebSocket đúng token rồi thanh toán | Nhận ngay `ORDER_SNAPSHOT` (PENDING_PAYMENT), sau đó `ORDER_PAID` (PAID, vị trí 1); ngắt thì rời kênh | Đúng | Đạt | `test_F2_25_...` |
| F2-26 | SD03 bước 15 | Màn hình Bar (kênh `bar:CG`) khi có đơn được thanh toán | Nhận 1 sự kiện `QUEUE_ITEM_ADDED` gồm mã đơn, bàn, món, số lượng, ghi chú | Đúng | Đạt | `test_F2_26_...` |
| F2-27 | NFR-R3 | Hub gửi tới 1 kết nối sống + 1 kết nối đã ngắt; gửi vào kênh không ai nghe | Kết nối sống nhận đúng định dạng `{type, data, ts}`; kết nối chết bị loại; kênh trống không lỗi | Đúng | Đạt | `test_F2_27_...` |
| F2-28 | Kịch bản demo | Dữ liệu mẫu: bàn CG-05 đặt 2 Cà phê sữa đá + 1 Trà đào, `expected_total` 86.000 | Tạm tính 103.000, giảm 17.000, tổng 86.000, `CG-0001`; thanh toán → PAID | Đúng | Đạt | `test_order_seed.py::test_F2_28_...` |

### 4.5. Frontend – W01 thêm món, W02 giỏ hàng & thanh toán (cấp: Giao diện, API giả lập)
| Mã TC | Căn cứ | Mô tả | Kết quả mong đợi | Kết quả thực tế | KQ |
|:---|:---|:---|:---|:---|:---:|
| F2-FE-01 | UC04 | Bấm "+" Cà phê sữa đá 2 lần | Huy hiệu số lượng 1 → 2; thanh "Giỏ hàng (2) – 50.000đ"; món Tạm hết không có nút "+" | Đúng | Đạt |
| F2-FE-02 | SD03, NFR-S7 | Thêm món, đóng rồi mở lại trang | Giỏ còn (sessionStorage của tab); `localStorage` rỗng | Đúng | Đạt |
| F2-FE-03 | W02 | Giỏ 2 Cà phê sữa đá + 1 Trà đào; bớt; xóa | Tạm tính 103.000 / KM −17.000 / tổng 86.000; bớt 1 → 61.000; bớt về 0 thì mất dòng; xóa hết → "Giỏ hàng trống." | Đúng | Đạt |
| F2-FE-04 | UC05 quy tắc | Bấm "+" 25 lần | Dừng ở 20, nút "+" bị khóa | Đúng | Đạt |
| F2-FE-05 | UC05, SD03 | Ghi chú "ít đường", chọn "Thẻ ngân hàng", bấm "Thanh toán & gửi đơn" | Gửi đúng nội dung (qr_token, expected_total 86.000, món, ghi chú); thanh toán MOCK_CARD; sang W03 `/orders/77`; giỏ bị xóa | Đúng | Đạt |
| F2-FE-06 | UC05 – 3a | Server báo món vừa hết | Thông báo tên món; dòng món viền đỏ + "Tạm hết"; nút thanh toán khóa tới khi xóa món | Đúng | Đạt |
| F2-FE-07 | UC05 – 3b | Server báo giá thay đổi (tổng mới 95.000) | Cập nhật giá trong giỏ, cảnh báo "Tổng mới: 95.000đ"; lần gửi sau dùng `expected_total` 95.000 | Đúng | Đạt |
| F2-FE-08 | UC05 – 5a | Thanh toán lần 1 thất bại | Báo lỗi; nút đổi thành "Thử thanh toán lại"; thử lại **không tạo đơn mới** (1 lần tạo, 2 lần thanh toán) | Đúng | Đạt |
| F2-FE-09 | W02 | Trong lúc chờ thanh toán | Hiện hộp "Đang xử lý thanh toán..." rồi tự tắt | Đúng | Đạt |

### 4.6. Frontend – W03 Theo dõi đơn (cấp: Giao diện, WebSocket giả lập)
| Mã TC | Căn cứ | Mô tả | Kết quả mong đợi | Kết quả thực tế | KQ |
|:---|:---|:---|:---|:---|:---:|
| F2-FE-10 | UC06, W03 | Mở trang đơn đã thanh toán | Mã đơn; số bàn chỉ hiện 1 lần; "✔ Thanh toán thành công – 86.000đ"; bước "Đang chờ"; "vị trí thứ 2"; món + ghi chú + trạng thái | Đúng (sau khi sửa BUG-F2-01) | Đạt |
| F2-FE-11 | IV.3 2.3 | Kênh WebSocket | Mở `ws://…/ws/order/77?token=tok` | Đúng | Đạt |
| F2-FE-12 | UC06 | Sự kiện có đủ dữ liệu đơn / sự kiện lẻ `ITEM_DONE` | Cập nhật ngay; sự kiện lẻ thì tải lại qua REST (đúng 1 lần) và hiện "✔ Xong", "Đang pha" | Đúng | Đạt |
| F2-FE-13 | UC06 bước 3 | Đơn chuyển READY | Banner "Đồ uống đã sẵn sàng – mời bạn đến quầy nhận"; **rung điện thoại** đúng 1 lần; 3/3 bước | Đúng | Đạt |
| F2-FE-14 | UC06 ngoại lệ | Đơn bị hủy, lý do "Khách đổi ý" | "Đơn đã hủy – đã hoàn tiền", "Lý do: Khách đổi ý"; ẩn tiến trình | Đúng | Đạt |
| F2-FE-15 | NFR-R3 | Rớt kết nối WebSocket | Hiện "Đang kết nối lại..."; tự mở kết nối mới sau ~1 giây; hết cảnh báo | Đúng | Đạt |
| F2-FE-16 | UC06 bảo mật | Link sai token | "Không tìm thấy đơn hàng"; WebSocket bị từ chối (4404) thì **không** thử lại | Đúng | Đạt |
| F2-FE-17 | W03 | Bấm "Gọi thêm món" | Về `/t/<qr>/menu` | Đúng | Đạt |

### 4.7. Kiểm thử hệ thống: kiểm thử khói qua Nginx (log: [logs/F2_smoke_test.txt](logs/F2_smoke_test.txt))
| Mã TC | Mô tả | Kết quả mong đợi | Kết quả thực tế | KQ |
|:---|:---|:---|:---|:---:|
| – | Nâng cấp CSDL demo đang có dữ liệu từ 0001 lên 0002 | Log "Running upgrade 0001 -> 0002"; dữ liệu cũ giữ nguyên | Đúng | Đạt |
| SM-11 | Tạo đơn bàn CG-05 trên dữ liệu mẫu | 201, tổng do server tính = 86.000 | `CG-0001`, 86.000 | Đạt |
| SM-12 | Mở WebSocket qua Nginx (`/ws/` proxy) | Nhận `ORDER_SNAPSHOT` PENDING_PAYMENT | Đúng | Đạt |
| SM-13 | Thanh toán giả lập | PAID | Đúng | Đạt |
| SM-14 | Thời gian từ lúc gọi thanh toán tới khi trang theo dõi nhận `ORDER_PAID` (NFR-P4 ≤ 2 giây) | ≤ 2.000 ms | **54 ms** | Đạt |
| SM-15 | Xem đơn | PAID, có vị trí hàng đợi | Vị trí 1 | Đạt |
| SM-16 | Sai `access_token` | 404 | Đúng | Đạt |
| SM-01…10 | Hồi quy F0, F1 | Như biên bản F0, F1 | 10/10 đạt | Đạt |

### 4.8. Kiểm thử đầu-cuối trên trình duyệt (Edge giả lập iPhone 14 – log: [logs/F2_e2e_trinh_duyet.txt](logs/F2_e2e_trinh_duyet.txt))
Kịch bản: quét QR bàn CG-05 → "Xem menu ngay" → thêm Cà phê sữa đá, Trà đào → giỏ hàng → ghi chú "ít đường" → thanh toán → theo dõi đơn.
| Mã TC | Mô tả | Kết quả mong đợi | Kết quả thực tế | KQ |
|:---|:---|:---|:---|:---:|
| E2E-01 | Tổng tiền giỏ | 61.000đ (25.000 + 36.000) | Đúng | Đạt |
| E2E-02 | W02 ở 390px | Không tràn ngang | `scrollWidth` = 390 | Đạt |
| E2E-03 | Sau thanh toán | Sang W03, đơn PAID | Đúng | Đạt |
| E2E-04 | **NFR-U2**: số lần chạm từ màn hình chào tới khi đặt xong đơn 2 món | ≤ 6 | **5 lần** | Đạt |
| E2E-05 | W03 kết nối WebSocket thật qua Nginx | Không hiện "Đang kết nối lại" | Đúng | Đạt |
| E2E-06 | W03 hiện vị trí trong hàng đợi | Có | Đúng | Đạt |
| E2E-07 | W03 ở 390px | Không tràn ngang | Đúng | Đạt |
| E2E-08 | Tải lại trang theo dõi | Vẫn xem được đơn | Đúng | Đạt |
| E2E-09 | Mở lại giỏ sau khi đặt | "Giỏ hàng trống." | Đúng | Đạt |
| E2E-10 | Mở link theo dõi ở trình duyệt khác | Xem được (nhờ token trên link) | Đúng | Đạt |
| E2E-11 | Link theo dõi sai token | "Không tìm thấy đơn hàng" | Đúng | Đạt |

Ảnh minh chứng: [W01 đã thêm món](img/F2_W01_da_them_mon.png) · [W02 giỏ hàng](img/F2_W02_gio_hang.png) · [W02 đang xử lý](img/F2_W02_dang_xu_ly.png) · [W03 theo dõi đơn](img/F2_W03_theo_doi_don.png)

## 5. Tổng hợp kết quả
| Nhóm | Số ca | Đạt | Không đạt |
|:---|:---:|:---:|:---:|
| Backend (pytest, `tests/f2`) | 33 | 33 | 0 |
| Frontend (Vitest, W01/W02/W03) | 17 | 17 | 0 |
| Kiểm thử khói (SM-11…16) | 6 | 6 | 0 |
| Kiểm thử đầu-cuối trên trình duyệt (E2E) | 11 | 11 | 0 |
| **Tổng F2** | **67** | **67** | **0** |
| *Hồi quy F0 + F1 (backend 65, frontend 30, SM-01…10)* | *105* | *105* | *0* |

**Độ bao phủ mã** (log: [logs/F2_backend_pytest.txt](logs/F2_backend_pytest.txt), [logs/F2_frontend_vitest.txt](logs/F2_frontend_vitest.txt)):
| Phần | Câu lệnh | Ghi chú |
|:---|:---:|:---|
| `app/modules/order` (router, service, schemas) | **100%** | NFR-M3 yêu cầu service Order ≥ 60% |
| `app/modules/payment`, `app/ws/hub.py` | 100% | |
| Backend toàn bộ | 89% | Phần chưa phủ: `get_db` (thay bằng phiên rollback khi test), CLI của script seed, `smoke_test.py` (công cụ) |
| Frontend toàn bộ | 99,0% (nhánh 92,5%) | `CartPage` 100%, `OrderPage` 99%, `CartContext` 97% (nhánh trình duyệt chặn storage) |

## 6. Lỗi phát hiện
| Mã lỗi | Mức độ | Mô tả | Phát hiện bởi | Nguyên nhân | Cách sửa | Kiểm tra lại | Trạng thái |
|:---|:---|:---|:---|:---|:---|:---|:---|
| BUG-F2-02 | Cao (lỗi thiết kế) | Mã đơn đếm lại mỗi ngày (UC05) nhưng `orders.order_code` UNIQUE toàn bảng → **từ ngày thứ 2 mọi đơn đầu ngày đều lỗi** | Rà soát thiết kế trước khi code F2 | Mâu thuẫn giữa đặc tả UC05 và `schema.sql` | PM chốt (CR-32, D28): thêm `order_date`, UNIQUE (order_code, order_date); migration 0002; cập nhật schema.sql, IV.1, ERD | F2-12, F2-13, F2-14, F2-29 đạt; migration nâng cấp CSDL demo thành công | Đã đóng |
| BUG-F2-01 | Thấp | Số bàn hiện 2 lần trên W03 (thanh tiêu đề + cạnh mã đơn) và W02 ("Giỏ hàng – Bàn 05") | Test F2-FE-10 báo "Found multiple elements"; ảnh chụp W02 | Tiêu đề trang lặp lại thông tin đã có trên thanh tiêu đề chung | Bỏ số bàn khỏi tiêu đề W02, W03 | Thêm kiểm tra "số bàn chỉ hiện 1 lần" vào F2-FE-03…09 và F2-FE-10; 47/47 đạt | Đã đóng |

## 7. Tồn tại / ghi chú
- **P14 – PM đã chốt ngày 03/11/2026 (D29, CR-33):** màn hình W01a (popup chi tiết món: số lượng, ghi chú) trong thiết kế **được gộp vào W02**: bấm "+" trên menu là thêm ngay, số lượng và ghi chú chỉnh ở giỏ hàng. Lý do: đạt NFR-U2 với 5 lần chạm (nếu có popup thì cần ≥ 7 lần).
- **Demo luồng thanh toán thất bại:** quy tắc "số tiền tận cùng 999" không xảy ra với dữ liệu mẫu (giá chẵn trăm). Đã kiểm bằng test tự động (F2-16, F2-17, F2-FE-08). Muốn demo trực tiếp cần một món giá dạng 29.999đ (tạo ở F6 hoặc thêm vào dữ liệu mẫu).
- Đơn PENDING_PAYMENT bị bỏ dở hiện vẫn nằm trong CSDL; quy tắc tự hủy sau 15 phút chỉ **mô tả** (D22), không ảnh hưởng hàng đợi Bar (chỉ tính đơn đã thanh toán).
- API `POST /api/public/orders` nhận thêm `expected_total` để phát hiện giá thay đổi và trả thêm `subtotal`, `discount`, `items`; bổ sung mã lỗi `QUANTITY_LIMIT`, `ORDER_NOT_FOUND`; WebSocket bổ sung sự kiện `ORDER_SNAPSHOT`, `ORDER_PAID` – đã cập nhật [IV.3](../Thiet_ke_he_thong/IV.3_Kien_truc_va_API.md).
- Ghi chú cấp đơn (`note` của đơn) có trong API nhưng W02 chưa có ô nhập (thiết kế W02 chỉ có ghi chú từng món).
- Sự kiện `QUEUE_ITEM_ADDED` đã phát lên kênh `bar:{branch_id}`; màn hình Bar nhận và hiển thị sẽ kiểm ở F3.

## 8. Kết luận
**Luồng F2: ĐẠT.** 67/67 ca kiểm thử đạt, hồi quy F0 + F1 105/105 đạt; 1 lỗi thiết kế mức Cao (mã đơn) và 1 lỗi giao diện mức Thấp đã sửa, đều có test hồi quy. Đủ điều kiện chuyển sang **F3 – Màn hình Bar**.

| Vai trò | Họ tên | Ngày | Ký xác nhận |
|:---|:---|:---|:---|
| Người lập (Tester / QA) | Ngô Duy Đô (D) | 02/11/2026 | |
| PM duyệt | Nguyễn Thanh Bình (A) | 03/11/2026 | |
