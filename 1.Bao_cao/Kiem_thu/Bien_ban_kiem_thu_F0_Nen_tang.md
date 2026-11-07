# BIÊN BẢN KIỂM THỬ – LUỒNG F0: NỀN TẢNG

## 1. Thông tin chung
| Mục | Nội dung |
|:---|:---|
| Dự án | SmartCafe – Phần mềm quản lý chuỗi quán cà phê thông minh (Nhóm 8) |
| Luồng | **F0 – Nền tảng**: hạ tầng Docker Compose, CSDL 18 bảng (Alembic), dữ liệu mẫu, đăng nhập nhân viên, phân quyền RBAC, định dạng lỗi |
| Phiên bản | 0.1.0 (bản build 21/10/2026) – mã nguồn `2.San_pham/smartcafe/` |
| Ngày kiểm thử | 21/10/2026 |
| Người lập biên bản | Ngô Duy Đô (D – Tester / QA) |
| Người duyệt | Nguyễn Thanh Bình (A – PM) – đã duyệt 22/10/2026 (trước khi bắt đầu F2) |
| Tài liệu căn cứ | [IV.1 Thiết kế CSDL](../Thiet_ke_he_thong/IV.1_Thiet_ke_CSDL.md), [IV.3 Kiến trúc & API](../Thiet_ke_he_thong/IV.3_Kien_truc_va_API.md), [III.1 Use case + ma trận RBAC](../Thiet_ke_he_thong/III.1_Use_Case_Sequence.md), [III.2 NFR](../Thiet_ke_he_thong/III.2_Yeu_cau_phi_chuc_nang_Data_Model.md) |

## 2. Phạm vi
**Trong phạm vi**
- Migration Alembic `0001` chạy nguyên văn `schema.sql` thiết kế: tạo / xóa / tạo lại 18 bảng và 9 kiểu ENUM; ràng buộc dữ liệu.
- Script dữ liệu mẫu `seed_data.py` (IV.1 Mục 7).
- Bảo mật: băm mật khẩu bcrypt (NFR-S1), JWT nhân viên 8 giờ (NFR-S2), token khách không gọi được API nhân viên.
- API `POST /api/auth/login`, `GET /api/auth/me` (UC08).
- Dependency phân quyền dùng chung: theo vai trò (`require_roles`) và theo chi nhánh (`ensure_branch_access`) – kiểm bằng endpoint giả chỉ có trong test.
- Định dạng lỗi thống nhất (IV.3 Mục 2.4), Swagger `/docs` (NFR-M1), chạy toàn hệ thống bằng `docker compose up` (NFR-M5).
- Giao diện A01 Đăng nhập + điều hướng mặc định theo vai trò (IV.2 Mục 2).

**Ngoài phạm vi** (làm ở luồng sau): CRUD nhân viên/chi nhánh (F6), các màn hình W04 (F3), W08 (F8) – hiện chỉ là trang giữ chỗ.

## 3. Môi trường & cách chạy
| Hạng mục | Giá trị |
|:---|:---|
| Máy | Laptop Lenovo, Intel i5-10210U (4 nhân / 8 luồng), 16 GB RAM, Windows 10 Pro 19045 |
| Hạ tầng | Docker Desktop 29.9.2 (WSL2, giới hạn 4 GB RAM / 4 nhân), Docker Compose v5.6.1 |
| CSDL | PostgreSQL 16.15 (image `postgres:16-alpine`) – test chạy trên CSDL thật `smartcafe_test` (tạo lại mỗi phiên), mỗi test rollback riêng |
| Backend | Python 3.11.9, FastAPI 0.162.0, SQLAlchemy 2.0.55, Alembic 1.20.1, Pydantic 2.14.2, PyJWT 2.15.1, bcrypt 5.0.0 |
| Công cụ test backend | pytest 8.4.2, pytest-cov 7.1.0, httpx 0.28.1 (TestClient) |
| Frontend | Node.js 24.22.2, React 18.3.1, Vite 6.4.5, TypeScript 5.6.3 |
| Công cụ test frontend | Vitest 3.2.7, Testing Library (React 16.3.3, user-event 14.6.8), jsdom 25, @vitest/coverage-v8 |
| Kiểm thử khói / ảnh chụp | `scripts/smoke_test.py` qua Nginx cổng 8080; Playwright 1.64.1 điều khiển Microsoft Edge |

```powershell
docker compose up -d db
cd backend;  .\.venv\Scripts\python -m pytest -v tests/f0 --cov=app
cd frontend; npx vitest run src/pages/admin
cd backend;  .\.venv\Scripts\python -m scripts.smoke_test --qr-token <token>
```

## 4. Danh sách test case

### 4.1. Backend – CSDL & migration (cấp: Tích hợp, PostgreSQL thật)
| Mã TC | Căn cứ | Mô tả / dữ liệu | Kết quả mong đợi | Kết quả thực tế | KQ | Test tự động |
|:---|:---|:---|:---|:---|:---:|:---|
| F0-01 | IV.1, NFR-M2 | `alembic upgrade head` trên CSDL trống | Có đúng 18 bảng + 9 ENUM như `schema.sql` | Đúng 18 bảng, 9 ENUM | Đạt | `test_migration.py::test_F0_01_...` |
| F0-02 | NFR-M2 | upgrade → downgrade base → upgrade | Downgrade xóa sạch bảng + ENUM; upgrade lại thành công | Như mong đợi | Đạt | `test_F0_02_...` |
| F0-03 | IV.1 `chk_staff_branch` | Thêm nhân viên BARISTA không có chi nhánh | Bị CSDL từ chối (IntegrityError) | Bị từ chối | Đạt | `test_F0_03_...` |
| F0-04 | IV.1 | Thêm món giá −1 | Bị CSDL từ chối (CHECK base_price ≥ 0) | Bị từ chối | Đạt | `test_F0_04_...` |

### 4.2. Backend – Dữ liệu mẫu (cấp: Tích hợp)
| Mã TC | Căn cứ | Mô tả / dữ liệu | Kết quả mong đợi | Kết quả thực tế | KQ | Test tự động |
|:---|:---|:---|:---|:---|:---:|:---|
| F0-05 | IV.1 Mục 7 | Chạy `seed()` trên CSDL trống | 3 chi nhánh, 60 bàn, 13 nhân viên, 5 danh mục, 35 món, 3 KM | Đúng số lượng | Đạt | `test_seed.py::test_F0_05_...` |
| F0-06 | IV.1 Mục 7 | Phân bổ vai trò | 1 ADMIN (không chi nhánh), 3 MANAGER, 3 CASHIER, 6 BARISTA | Đúng | Đạt | `test_F0_06_...` |
| F0-07 | NFR-S3 | `qr_token` của 60 bàn | Không trùng, ≥ 22 ký tự (128 bit), không phải số tăng dần | Đúng | Đạt | `test_F0_07_...` |
| F0-08 | NFR-S1 | Mật khẩu nhân viên mẫu | Lưu dạng băm bcrypt (`$2...`), khác mật khẩu gốc, kiểm tra đúng | Đúng | Đạt | `test_F0_08_...` |
| F0-09 | D16, IV.1 Mục 7 | Món tạo trong 30 ngày | Có 3–4 món mới | 4 món | Đạt | `test_F0_09_...` |

### 4.3. Backend – Bảo mật (cấp: Đơn vị)
| Mã TC | Căn cứ | Mô tả / dữ liệu | Kết quả mong đợi | Kết quả thực tế | KQ | Test tự động |
|:---|:---|:---|:---|:---|:---:|:---|
| F0-10 | NFR-S1 | Băm "matkhau", kiểm tra đúng/sai | Đúng → True, sai → False, hash ≠ mật khẩu | Đúng | Đạt | `test_security.py::test_F0_10_...` |
| F0-11 | – | Kiểm tra với chuỗi hash hỏng | Trả False, không ném lỗi | Đúng | Đạt | `test_F0_11_...` |
| F0-12 | NFR-S2 | Tạo JWT cho BARISTA chi nhánh 2 | Payload có sub, typ=staff, role, branch_id; hạn đúng 8 giờ | Đúng | Đạt | `test_F0_12_...` |
| F0-13 | NFR-S2 | JWT ký bằng khóa khác | Bị từ chối (InvalidSignature) | Bị từ chối | Đạt | `test_F0_13_...` |
| F0-14 | NFR-S2 | JWT đã quá hạn | Bị từ chối (ExpiredSignature) | Bị từ chối | Đạt | `test_F0_14_...` |

### 4.4. Backend – API đăng nhập UC08 (cấp: Tích hợp)
| Mã TC | Căn cứ | Mô tả / dữ liệu | Kết quả mong đợi | Kết quả thực tế | KQ | Test tự động |
|:---|:---|:---|:---|:---|:---:|:---|
| F0-15 | UC08 | Đăng nhập `pc1_cg` đúng mật khẩu | 200; token bearer, `expires_in`=28800, thông tin vai trò + chi nhánh | Đúng | Đạt | `test_auth_api.py::test_F0_15_...` |
| F0-16 | UC08 | Đăng nhập `admin` | 200; `branch` = null | Đúng | Đạt | `test_F0_16_...` |
| F0-17 | Bảo mật | Sai mật khẩu / sai tên đăng nhập | Cùng 401 `INVALID_CREDENTIALS`, cùng nội dung (không lộ tài khoản tồn tại) | Hai phản hồi giống hệt | Đạt | `test_F0_17_...` |
| F0-18 | UC12 | Tài khoản đã khóa đăng nhập | 403 `ACCOUNT_LOCKED` | Đúng | Đạt | `test_F0_18_...` |
| F0-19 | NFR-S5, IV.3 2.4 | Tên đăng nhập / mật khẩu rỗng | 422 `VALIDATION_ERROR`, đúng cấu trúc `{code, message, details}` | Đúng | Đạt | `test_F0_19_...` |
| F0-20 | IV.3 | `GET /api/auth/me` với token hợp lệ | 200, đúng người đăng nhập | Đúng | Đạt | `test_F0_20_...` |
| F0-21 | NFR-S2 | `/me` không gửi token | 401 `UNAUTHORIZED` | Đúng | Đạt | `test_F0_21_...` |
| F0-22 | NFR-S2 | `/me` với token rác | 401 `UNAUTHORIZED` | Đúng | Đạt | `test_F0_22_...` |
| F0-23 | NFR-S2 | `/me` với token hết hạn | 401 `TOKEN_EXPIRED` | Đúng | Đạt | `test_F0_23_...` |
| F0-24 | NFR-S2 | `/me` với JWT khách thành viên (typ=customer) | 403 `FORBIDDEN` | Đúng | Đạt | `test_F0_24_...` |
| F0-25 | UC12 | Token cấp xong thì tài khoản bị khóa | 401 – token cũ không còn dùng được | Đúng | Đạt | `test_F0_25_...` |

### 4.5. Backend – Phân quyền RBAC (cấp: Tích hợp)
| Mã TC | Căn cứ | Mô tả / dữ liệu | Kết quả mong đợi | Kết quả thực tế | KQ | Test tự động |
|:---|:---|:---|:---|:---|:---:|:---|
| F0-26a…d | Ma trận RBAC (III.1) | Thao tác "Bắt đầu/Xong món" (chỉ BARISTA, MANAGER) gọi bởi 4 vai trò | BARISTA 200, MANAGER 200, CASHIER 403, ADMIN 403 | Đúng cả 4 | Đạt | `test_rbac.py::test_F0_26_...[4 tham số]` |
| F0-27 | NFR-S2 | Pha chế Cầu Giấy truy cập dữ liệu Cầu Giấy / Hà Đông | CG 200; HD 403 `FORBIDDEN` | Đúng | Đạt | `test_F0_27_...` |
| F0-28 | RBAC | Quản trị viên truy cập 2 chi nhánh | Cả hai 200 | Đúng | Đạt | `test_F0_28_...` |

### 4.6. Backend – Ứng dụng (cấp: Tích hợp)
| Mã TC | Căn cứ | Mô tả / dữ liệu | Kết quả mong đợi | Kết quả thực tế | KQ | Test tự động |
|:---|:---|:---|:---|:---|:---:|:---|
| F0-29 | NFR-M5 | `GET /api/health` | `{"status":"ok"}` | Đúng | Đạt | `test_app.py::test_F0_29_...` |
| F0-30 | NFR-M1 | `/docs`, `/openapi.json` | Swagger mở được; có đủ 4 endpoint F0+F1 | Đúng | Đạt | `test_F0_30_...` |
| F0-31 | IV.3 2.4 | Gọi route không tồn tại | 404 `NOT_FOUND` theo định dạng lỗi thống nhất | Đúng | Đạt | `test_F0_31_...` |

### 4.7. Frontend – A01 Đăng nhập (cấp: Giao diện, API giả lập)
| Mã TC | Căn cứ | Mô tả / dữ liệu | Kết quả mong đợi | Kết quả thực tế | KQ | Test tự động |
|:---|:---|:---|:---|:---|:---:|:---|
| F0-FE-01a…d | IV.2 Mục 2 | Đăng nhập lần lượt BARISTA, CASHIER, MANAGER, ADMIN | BARISTA/CASHIER → `/admin/bar` (W04); MANAGER/ADMIN → `/admin/dashboard` (W08); hiện tên người dùng; lưu phiên | Đúng cả 4 | Đạt | `LoginPage.test.tsx` F0-FE-01 |
| F0-FE-02 | UC08 | Sai mật khẩu | Hiện "Tên đăng nhập hoặc mật khẩu không đúng"; không lưu phiên | Đúng | Đạt | F0-FE-02 |
| F0-FE-03 | NFR-S2 | Chưa đăng nhập mà mở `/admin/bar` | Chuyển về `/admin/login` | Đúng | Đạt | F0-FE-03 |
| F0-FE-04 | NFR-S2 | Có phiên nhưng server báo token hết hạn (401) | Xóa phiên, về trang đăng nhập | Đúng | Đạt | F0-FE-04 |
| F0-FE-05 | NFR-S2 | Phiên lưu trên máy đã quá hạn 8 giờ | Bị bỏ qua (coi như chưa đăng nhập) | Đúng | Đạt | F0-FE-05 |
| F0-FE-06 | UC08 | Bấm "Đăng xuất" | Xóa phiên, về trang đăng nhập | Đúng | Đạt | F0-FE-06 |

### 4.8. Kiểm thử khói trên hệ thống chạy thật (cấp: Hệ thống, `docker compose up` + Nginx)
| Mã TC | Mô tả | Kết quả mong đợi | Kết quả thực tế | KQ |
|:---|:---|:---|:---|:---:|
| SM-01 | `GET /api/health` qua Nginx :8080 | 200 ok | 200 ok | Đạt |
| SM-02 | Mở `/admin/login` (SPA) | Nginx trả `index.html` | Đúng | Đạt |
| SM-04 | Đăng nhập `admin` / mật khẩu mẫu | 200, vai trò ADMIN | Đúng | Đạt |
| SM-05 | `/api/auth/me` với token vừa cấp | 200, `admin` | Đúng | Đạt |
| SM-06 | Đăng nhập sai mật khẩu | 401 `INVALID_CREDENTIALS` | Đúng | Đạt |
| – | Khởi động lần đầu: migration + nạp dữ liệu mẫu | Log "Running upgrade -> 0001", "[seed] Đã nạp: ..." | Đúng | Đạt |
| – | Khởi động lại backend | Không nạp trùng dữ liệu ("[seed] CSDL đã có dữ liệu, bỏ qua"); vẫn 3 chi nhánh, 13 nhân viên, 35 món | Đúng | Đạt |

Ảnh minh chứng: [A01 Đăng nhập](img/F0_A01_dang_nhap.png) · [Pha chế đăng nhập → W04 (giữ chỗ)](img/F0_A01_sau_dang_nhap_pha_che.png)

## 5. Tổng hợp kết quả
| Nhóm | Số ca | Đạt | Không đạt |
|:---|:---:|:---:|:---:|
| Backend (pytest, `tests/f0`) | 34 | 34 | 0 |
| Frontend (Vitest, A01) | 9 | 9 | 0 |
| Kiểm thử khói (SM) | 5 | 5 | 0 |
| **Tổng** | **48** | **48** | **0** |

**Độ bao phủ mã** (đo chung cả F0 + F1, log: [logs/F0_F1_backend_pytest.txt](logs/F0_F1_backend_pytest.txt), [logs/F0_F1_frontend_vitest.txt](logs/F0_F1_frontend_vitest.txt)):
| Phần | Câu lệnh | Ghi chú |
|:---|:---:|:---|
| Backend `app/` | ~99% | Chỉ `core/db.py::get_db` (69%) không chạy vì test thay bằng phiên có rollback |
| Backend `scripts/seed_data.py` | 68% | Phần CLI (`--print-qr`, `main`) được kiểm bằng chạy thật trong container |
| Backend toàn bộ (kể cả `smoke_test.py` 0%) | 88% | `smoke_test.py` là công cụ kiểm thử, không phải mã sản phẩm |
| Frontend `src/` | 99,1% (nhánh 92,9%) | |

## 6. Lỗi phát hiện
| Mã lỗi | Mức độ | Mô tả | Phát hiện bởi | Nguyên nhân | Cách sửa | Kiểm tra lại | Trạng thái |
|:---|:---|:---|:---|:---|:---|:---|:---|
| BUG-F0-01 | Cao | Chạy test lần đầu: 54/64 test lỗi `UnicodeDecodeError: 'charmap'` khi Alembic đọc cấu hình | Lần chạy pytest đầu tiên | `alembic.ini` có chú thích tiếng Việt; trên Windows `configparser` đọc file bằng bảng mã cp1252 | Chuyển `alembic.ini` về chỉ ký tự ASCII; ghi chú quy ước trong file và README mã nguồn | Chạy lại toàn bộ: 64/64 đạt | Đã đóng |
| BUG-F0-02 | Cao | Container backend dừng ngay khi khởi động: `ModuleNotFoundError: No module named 'app'` | Kiểm thử hệ thống (`docker compose up`) | Lệnh CLI `alembic` không thêm thư mục làm việc vào `sys.path` (pytest thì có, nên test đơn vị không phát hiện) | Thêm `prepend_sys_path = .` vào `alembic.ini` | Container khởi động, migrate + seed thành công; SM-01…10 đạt | Đã đóng |

## 7. Tồn tại / hạn chế
- Cảnh báo (mức Thấp) khi chạy test: Starlette khuyến nghị thay `httpx` bằng `httpx2` cho TestClient. Không ảnh hưởng kết quả; theo dõi khi nâng cấp thư viện.
- Phân quyền mới được kiểm qua endpoint giả trong test; các API nhân viên thật sẽ dùng chung dependency này và được kiểm lại ở F3, F5, F6, F8.
- Chưa có giới hạn số lần đăng nhập sai (chống dò mật khẩu) – thiết kế chưa yêu cầu; đề xuất xem xét ở F6.
- `schema.sql` (IV.1) **đã chạy thành công trên PostgreSQL 16 thật** qua migration `0001` – đóng việc "chạy thử schema.sql" của giai đoạn IV (thiết kế CSDL).

## 8. Kết luận
**Luồng F0: ĐẠT.** 48/48 ca kiểm thử đạt, 2 lỗi mức Cao đã sửa và kiểm tra lại. Đủ điều kiện làm nền cho các luồng tiếp theo.

| Vai trò | Họ tên | Ngày | Ký xác nhận |
|:---|:---|:---|:---|
| Người lập (Tester / QA) | Ngô Duy Đô (D) | 21/10/2026 | |
| PM duyệt | Nguyễn Thanh Bình (A) | 22/10/2026 | |
