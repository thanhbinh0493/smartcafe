# BIÊN BẢN KIỂM THỬ – LUỒNG F1: QUÉT QR → MÀN HÌNH CHÀO → MENU

## 1. Thông tin chung
| Mục | Nội dung |
|:---|:---|
| Dự án | SmartCafe – Phần mềm quản lý chuỗi quán cà phê thông minh (Nhóm 8) |
| Luồng | **F1 – Quét QR & xem menu (khách ẩn danh)**: UC01, UC03 (chưa gồm khối gợi ý món – F7) |
| Phiên bản | 0.1.0 (bản build 02/11/2026) – mã nguồn `2.San_pham/smartcafe/` |
| Ngày kiểm thử | 02/11/2026 |
| Người lập biên bản | Thành viên A (PM) |
| Người review | Thành viên D (Tester/QA) – *chờ review* |
| Tài liệu căn cứ | [III.1 UC01, UC03](../Thiet_ke_he_thong/III.1_Use_Case_Sequence.md), [IV.1 truy vấn menu](../Thiet_ke_he_thong/IV.1_Thiet_ke_CSDL.md), [IV.2 W00, W01](../Thiet_ke_he_thong/IV.2_Thiet_ke_giao_dien.md), [IV.3 API public](../Thiet_ke_he_thong/IV.3_Kien_truc_va_API.md), quyết định D3, D10, D14, D16 |
| Tiền đề | Luồng F0 đạt ([biên bản F0](Bien_ban_kiem_thu_F0_Nen_tang.md)) |

## 2. Phạm vi
**Trong phạm vi**
- `GET /api/public/tables/{qr_token}`: xác định chi nhánh + bàn; ngoại lệ mã sai / bàn khóa / chi nhánh ngừng hoạt động (UC01 – 2a).
- `GET /api/public/branches/{id}/menu`: menu theo danh mục với **giá bán = MIN(giá KM đang hiệu lực, giá chi nhánh / giá chung)**; KM toàn chuỗi và KM riêng chi nhánh; nhãn MỚI (30 ngày); "Tạm hết"; ẩn món ngừng bán / đã xóa / danh mục tắt; thứ tự hiển thị.
- Giao diện **W00** (màn hình chào, 2 lựa chọn), **W01** (menu: tìm kiếm không dấu, tab danh mục, tab "Khuyến mãi", giá gạch ngang, nhãn MỚI, Tạm hết, báo lỗi + thử lại), màn hình QR không hợp lệ.
- Không lưu định danh khách trên thiết bị (NFR-S7); định dạng tiền `45.000đ` (NFR-U4); bố cục điện thoại 390px (NFR-U1).

**Ngoài phạm vi**: khối "Gợi ý cho bạn" (F7), nút thêm món & giỏ hàng (F2), nhập SĐT + OTP (F4 – hiện là trang giữ chỗ), cập nhật menu realtime `MENU_UPDATED` (F6).

## 3. Môi trường & cách chạy
Giống [biên bản F0 – Mục 3](Bien_ban_kiem_thu_F0_Nen_tang.md#3-môi-trường--cách-chạy). Ảnh chụp: Playwright 1.64.1 + Microsoft Edge, giả lập iPhone 14 (390×844, tỉ lệ điểm ảnh 2, cảm ứng).
```powershell
cd backend;  .\.venv\Scripts\python -m pytest -v tests/f1
cd frontend; npx vitest run src/lib src/pages/qr
```

## 4. Danh sách test case

### 4.1. Backend – UC01 Quét QR (cấp: Tích hợp)
| Mã TC | Căn cứ | Mô tả / dữ liệu | Kết quả mong đợi | Kết quả thực tế | KQ | Test tự động |
|:---|:---|:---|:---|:---|:---:|:---|
| F1-01 | UC01 | QR của bàn 05 chi nhánh CG | 200; `branch {id, code, name, address}`, `table {id, table_number}` | Đúng | Đạt | `test_table_lookup.py::test_F1_01_...` |
| F1-02 | UC01 – 2a | QR không tồn tại | 404 `TABLE_NOT_FOUND`, "Mã QR không hợp lệ, vui lòng gọi nhân viên" | Đúng | Đạt | `test_F1_02_...` |
| F1-03 | UC01 – 2a | QR của bàn bị khóa | 404 `TABLE_NOT_FOUND` | Đúng | Đạt | `test_F1_03_...` |
| F1-04 | UC01 tiền điều kiện | QR của bàn thuộc chi nhánh ngừng hoạt động | 404 `TABLE_NOT_FOUND` | Đúng | Đạt | `test_F1_04_...` |
| F1-05 | NFR-S3 | Nội dung phản hồi | Không chứa `qr_token` | Đúng | Đạt | `test_F1_05_...` |

### 4.2. Backend – Quy tắc giá (cấp: Đơn vị)
| Mã TC | Căn cứ | Giá thường / giá KM | Kết quả mong đợi (giá bán, KM áp dụng) | KQ | Test tự động |
|:---|:---|:---|:---|:---:|:---|
| F1-06a | D10 | 45.000 / không có | 45.000, không | Đạt | `test_pricing_unit.py::test_F1_06_apply_promo[...]` |
| F1-06b | D10 | 45.000 / 36.000 | 36.000, có | Đạt | 〃 |
| F1-06c | D10 | 45.000 / 45.000 | 45.000, **không** (không giảm thì không gắn nhãn KM) | Đạt | 〃 |
| F1-06d | D3 + D10 | 27.000 (giá chi nhánh) / 29.000 | 27.000, không | Đạt | 〃 |
| F1-06e | D10 | 45.000 / 0 | 0, có | Đạt | 〃 |

### 4.3. Backend – UC03 Menu chi nhánh (cấp: Tích hợp)
| Mã TC | Căn cứ | Mô tả / dữ liệu | Kết quả mong đợi | Kết quả thực tế | KQ | Test tự động |
|:---|:---|:---|:---|:---|:---:|:---|
| F1-07 | D3 | Món 25.000, chi nhánh không cấu hình | Giá thường = giá bán = 25.000; không KM; còn hàng | Đúng | Đạt | `test_menu_api.py::test_F1_07_...` |
| F1-08 | D3 | HD đặt giá riêng 27.000 cho món 29.000 | HD 27.000; CG vẫn 29.000 | Đúng | Đạt | `test_F1_08_...` |
| F1-09 | D3 | CG đặt "Tạm hết" | CG `is_available=false` (vẫn hiển thị); HD còn hàng | Đúng | Đạt | `test_F1_09_...` |
| F1-10 | IV.1 | Món ngừng bán, món đã xóa mềm, món thuộc danh mục bị tắt | Không xuất hiện trong menu | Chỉ còn món đang bán | Đạt | `test_F1_10_...` |
| F1-11a…d | D16 | Món tạo cách đây 0 / 29 / 31 / 120 ngày | `is_new` = true / true / false / false | Đúng | Đạt | `test_F1_11_...[4 tham số]` |
| F1-12 | D10 | KM toàn chuỗi 45.000 → 36.000 | Áp dụng ở mọi chi nhánh, trả đúng `promotion_id` | Đúng | Đạt | `test_F1_12_...` |
| F1-13 | D10 | KM riêng CG 29.000 → 25.000 | CG 25.000; HD 29.000, không KM | Đúng | Đạt | `test_F1_13_...` |
| F1-14a…c | D10 | KM đã kết thúc / chưa bắt đầu / đang trong hạn nhưng bị tắt | Không áp dụng (52.000) | Đúng cả 3 | Đạt | `test_F1_14_...[3 tham số]` |
| F1-15 | D10 | 2 KM cùng lúc: toàn chuỗi 38.000, riêng CG 33.600 | Lấy giá thấp nhất 33.600 và đúng KM đó | Đúng | Đạt | `test_F1_15_...` |
| F1-16 | D3 + D10 | Giá chung 32.000, HD giá riêng 28.000, KM toàn chuỗi 30.000 | HD 28.000 (không KM); CG 30.000 (có KM) | Đúng | Đạt | `test_F1_16_...` |
| F1-17 | IV.1 | 2 danh mục `sort_order` 1, 2; món tên ASCII | Danh mục theo `sort_order`, món theo tên | Đúng | Đạt | `test_F1_17_...` |
| F1-22 | NFR-U4, **BUG-F1-01** | Tên tiếng Việt: Trà vải, Cold brew, Trà đào cam sả, Cà phê muối, Americano, Bạc xỉu | Americano → Bạc xỉu → Cà phê muối → Cold brew → Trà đào cam sả → Trà vải | Ban đầu **sai**; sau sửa đúng | Đạt | `test_F1_22_...` (test hồi quy) |
| F1-18 | UC03 | Chi nhánh không tồn tại / ngừng hoạt động | 404 `BRANCH_NOT_FOUND` | Đúng | Đạt | `test_F1_18_...` |
| F1-19 | UC03 | Chi nhánh chưa có món | 200, `categories: []` | Đúng | Đạt | `test_F1_19_...` |

### 4.4. Backend – Kịch bản trên dữ liệu mẫu (cấp: Tích hợp)
| Mã TC | Mô tả | Kết quả mong đợi | Kết quả thực tế | KQ | Test tự động |
|:---|:---|:---|:---|:---:|:---|
| F1-20 | Quét QR bàn 12 chi nhánh TX rồi mở menu | Đúng TX – bàn 12; 35 món; 5 danh mục đúng thứ tự Cà phê, Trà, Đá xay, Nước ép & Sinh tố, Bánh | Đúng | Đạt | `test_menu_seed.py::test_F1_20_...` |
| F1-21 | Giá theo kịch bản demo | Cà phê sữa đá: CG 25.000 (KM riêng), HD 27.000 (giá riêng, không KM), TX 29.000; Trà đào 36.000 và Trà vải 33.600 ở cả 3 CN; Cookie đá xay không KM (Halloween đã hết); Bạc xỉu nóng chỉ tạm hết ở CG; đúng 4 món MỚI | Đúng toàn bộ | Đạt | `test_F1_21_...` |

### 4.5. Frontend – W00, W01 (cấp: Giao diện, API giả lập)
| Mã TC | Căn cứ | Mô tả | Kết quả mong đợi | Kết quả thực tế | KQ |
|:---|:---|:---|:---|:---|:---:|
| F1-FE-01a…e | NFR-U4 | `formatVND` 0 / 500 / 45000 / 33600 / 1234567 | `0đ`, `500đ`, `45.000đ`, `33.600đ`, `1.234.567đ` | Đúng | Đạt |
| F1-FE-02 | W01 | Chuẩn hóa tìm kiếm "Cà Phê Sữa Đá" | `ca phe sua da` (bỏ dấu, đ→d) | Đúng | Đạt |
| F1-FE-03 | UC01, W00 | Mở `/t/<qr hợp lệ>` | Lời chào, tên chi nhánh, "Bàn 05", 2 nút "Nhập số điện thoại" / "Xem menu ngay" | Đúng | Đạt |
| F1-FE-04 | UC01 – 4a | Bấm "Xem menu ngay" | Sang `/t/<qr>/menu`, hiện menu | Đúng | Đạt |
| F1-FE-05 | UC01 – 4b | Bấm "Nhập số điện thoại" | Sang `/t/<qr>/otp` | Đúng | Đạt |
| F1-FE-06 | UC01 – 2a | Mở QR sai | "Mã QR không hợp lệ, vui lòng gọi nhân viên"; không hiện nút gọi món | Đúng | Đạt |
| F1-FE-17 | NFR-R1 | Mất mạng khi quét QR | "Có lỗi xảy ra" + "Không kết nối được máy chủ, vui lòng thử lại" | Đúng | Đạt |
| F1-FE-07 | NFR-S7, D9 | Đi hết W00 → W01 | `localStorage` rỗng, không có cookie | Đúng | Đạt |
| F1-FE-08 | UC03 | Thứ tự danh mục | Cà phê, Trà | Đúng | Đạt |
| F1-FE-09 | UC03 | Món KM 29.000 → 25.000 | Giá gốc trong thẻ `<del>` (gạch ngang) + giá bán; món thường chỉ 1 giá | Đúng | Đạt |
| F1-FE-10 | UC03 | Nhãn | Đúng 1 nhãn "MỚI"; món hết hàng có "Tạm hết" và làm mờ | Đúng | Đạt |
| F1-FE-11 | IV.2 W01 | Bấm tab "Khuyến mãi" | Chỉ còn món đang KM | Đúng | Đạt |
| F1-FE-12 | W01 | Bấm tab "Trà" rồi "Tất cả" | Chỉ món Trà, sau đó hiện lại tất cả | Đúng | Đạt |
| F1-FE-13 | W01 | Gõ "bac xiu"; sau đó gõ "pizza" | Ra 2 món Bạc xỉu (tìm không dấu); "Không tìm thấy món phù hợp." | Đúng | Đạt |
| F1-FE-14 | W01 | Menu không có món KM | Không hiện tab "Khuyến mãi" | Đúng | Đạt |
| F1-FE-15 | NFR-R1 | Lần tải menu đầu lỗi 500 | Báo lỗi + nút "Thử lại"; bấm thì tải được menu | Đúng | Đạt |
| F1-FE-16 | UC01 quy tắc | Bấm "Nhập SĐT tích điểm" trên menu | Sang `/t/<qr>/otp` | Đúng | Đạt |

### 4.6. Kiểm thử khói & kiểm tra trực quan (cấp: Hệ thống)
| Mã TC | Mô tả | Kết quả mong đợi | Kết quả thực tế | KQ |
|:---|:---|:---|:---|:---:|
| SM-03 | Mở link QR `/t/<token>` qua Nginx | Trả SPA `index.html` | Đúng | Đạt |
| SM-07 | Tra cứu QR thật của bàn CG-05 | Chi nhánh Cầu Giấy, bàn 05 | Đúng | Đạt |
| SM-08 | Menu chi nhánh trên dữ liệu mẫu | 35 món, 5 danh mục | Đúng | Đạt |
| SM-09 | Thời gian phản hồi API menu (1 request, tham khảo NFR-P2 ≤ 300 ms) | < 300 ms | 59 ms | Đạt |
| SM-10 | QR giả mạo | 404 `TABLE_NOT_FOUND` | Đúng | Đạt |
| VIS-01 | W00 ở 390×844 | Đủ nội dung, không tràn ngang (`scrollWidth` = 390) | Đúng – [ảnh](img/F1_W00_man_hinh_chao.png) | Đạt |
| VIS-02 | W01 ở 390×844 | Không tràn ngang; đúng giá, nhãn, Tạm hết, thứ tự tiếng Việt | Đúng – [menu](img/F1_W01_menu_CG.png), [tab KM](img/F1_W01_tab_khuyen_mai_CG.png), [tìm không dấu](img/F1_W01_tim_khong_dau.png) | Đạt (sau khi sửa BUG-F1-01) |
| VIS-03 | QR không hợp lệ | Thông báo rõ ràng | Đúng – [ảnh](img/F1_QR_khong_hop_le.png) | Đạt |

*VIS-xx là kiểm tra bằng mắt trên ảnh chụp, không tính vào tổng số ca tự động ở Mục 5.*

## 5. Tổng hợp kết quả
| Nhóm | Số ca | Đạt | Không đạt |
|:---|:---:|:---:|:---:|
| Backend (pytest, `tests/f1`) | 31 | 31 | 0 |
| Frontend (Vitest, `src/lib`, `src/pages/qr`) | 21 | 21 | 0 |
| Kiểm thử khói (SM) | 5 | 5 | 0 |
| **Tổng** | **57** | **57** | **0** |

**Độ bao phủ mã** (chung F0 + F1): module `app/modules/branch` và `app/modules/menu` **100%**; frontend `src/pages/qr` **100%** câu lệnh (nhánh 94%), `src/lib/format.ts` 100%. Log: [logs/F0_F1_backend_pytest.txt](logs/F0_F1_backend_pytest.txt), [logs/F0_F1_frontend_vitest.txt](logs/F0_F1_frontend_vitest.txt), [logs/F0_F1_smoke_test.txt](logs/F0_F1_smoke_test.txt).

## 6. Lỗi phát hiện
| Mã lỗi | Mức độ | Mô tả | Phát hiện bởi | Nguyên nhân | Cách sửa | Kiểm tra lại | Trạng thái |
|:---|:---|:---|:---|:---|:---|:---|:---|
| BUG-F1-01 | Trung bình | Món sắp sai thứ tự tiếng Việt: "Cold brew" đứng trước "Cà phê muối", "Trà vải" trước "Trà đào cam sả" | Kiểm tra trực quan ảnh chụp W01 (test F1-17 dùng tên ASCII nên không bắt được) | Image `postgres:16-alpine` dùng musl: collation `en_US.utf8` thực chất so sánh theo byte, chữ có dấu (à, đ…) xếp sau z | `ORDER BY ... m.name COLLATE "vi-VN-x-icu"` (collation ICU có sẵn trong PostgreSQL 16) | Thêm test hồi quy **F1-22** (chạy trước khi sửa: không đạt; sau khi sửa: đạt); 65/65 test backend đạt; chụp lại W01 đúng thứ tự | Đã đóng |

## 7. Tồn tại / ghi chú
- **Cách hiểu quy tắc giá cần PM xác nhận:** khi giá KM **không thấp hơn** giá đang bán (giá chi nhánh hoặc giá chung), hệ thống bán theo giá thường và **không gắn nhãn KM / `promotion_id`** (F1-06c, F1-06d, F1-16). Giá bán vẫn đúng công thức `LEAST` của D10; khác biệt chỉ ở việc có hiện "đang khuyến mãi" hay không (ảnh hưởng chỉ số "doanh thu KM" của dashboard F8).
- Khi 2 KM cùng mức giá thấp nhất, hệ thống chọn KM có `id` nhỏ hơn để kết quả ổn định.
- Ảnh món chưa có (dữ liệu mẫu để trống `image_url`), giao diện hiện biểu tượng thay thế. Upload ảnh làm ở F6.
- Chưa đo NFR-P1 (tải trang ≤ 2 giây trên 4G bằng Lighthouse) và NFR-P2 với 50 người dùng đồng thời – sẽ đo ở giai đoạn kiểm thử hiệu năng (VI). Gói JS sau nén gzip hiện 58 KB.
- Ảnh chụp bằng Edge headless mặc định bị cắt lề phải (Edge headless ép độ rộng cửa sổ tối thiểu lớn hơn 390px) – là hạn chế của công cụ chụp, không phải lỗi giao diện; đã chụp lại bằng Playwright giả lập thiết bị và xác nhận `scrollWidth` = 390.

## 8. Kết luận
**Luồng F1: ĐẠT.** 57/57 ca kiểm thử tự động đạt, 3/3 kiểm tra trực quan đạt; 1 lỗi mức Trung bình đã sửa và có test hồi quy. Đủ điều kiện chuyển sang **F2 – Đặt món & thanh toán giả lập** (dùng lại hàm tính giá `get_branch_menu` / `apply_promo` để server tự tính tiền theo NFR-S6).

| Vai trò | Họ tên | Ngày | Ký xác nhận |
|:---|:---|:---|:---|
| Người lập | Thành viên A | 02/11/2026 | |
| Tester/QA review | Thành viên D | | |
