# BIÊN BẢN HỌP TUẦN 07

## 1. THÀNH PHẦN
| Thành viên | Vai trò | Có mặt |
|:---|:---|:---:|
| Thành viên A | PM / Team Lead (chủ trì) | ✔ |
| Thành viên B | Backend Developer | ✔ |
| Thành viên C | AI Specialist | ✔ |
| Thành viên D | Tester / QA, thư ký | ✔ |
| Thành viên E | Frontend Developer | ✔ |

## 2. NGÀY HỌP
Tuần 07 (02/11/2026 – 08/11/2026). Hình thức: họp nhóm. Thư ký: Thành viên D.

## 3. NỘI DUNG
| Mã | Ngày | Nội dung thay đổi / thảo luận | Lý do | Ảnh hưởng (tài liệu, module, người) | Người đề xuất |
|:---|:---|:---|:---|:---|:---|
| CR-26 | 02/11/2026 | Chốt môi trường chạy và demo: chạy **local trên laptop** bằng Docker Desktop (WSL2) + Docker Compose, cài Docker tại `D:\Docker`; giới hạn WSL2 4 GB RAM / 4 nhân. Không dùng Google Colab (không chạy được web server liên tục, không có Docker và URL cố định). Bản dự phòng trên cloud để mở (P12) | Không tốn chi phí, đúng kiến trúc Docker Compose đã chốt; laptop (i5-10210U, 16 GB RAM, SSD) đủ tải demo; ổ C còn ít dung lượng nên đặt Docker ở ổ D | README thiết kế (D24, P12); máy demo của A; B, E dùng chung cấu hình Docker Compose | A |
| CR-27 | 02/11/2026 | Tạm gác vấn đề timeline (P11): không điều chỉnh mốc lập trình lúc này, A sẽ tự hoàn thiện timeline thủ công sau | Ưu tiên bắt đầu code ngay | README thiết kế (P11 → Hoãn); Project_Plan.md, IV.3 Mục 3 (A cập nhật sau) | A |
| CR-28 | 02/11/2026 | Quy trình code: làm **theo từng luồng nghiệp vụ cốt lõi**, mỗi luồng bắt buộc có **test tự động** và **biên bản kiểm thử** đầy đủ trước khi sang luồng tiếp theo | Đảm bảo chất lượng từng phần, có minh chứng kiểm thử cho báo cáo | README thiết kế (D25); B, C, E (viết test), D (biên bản kiểm thử) | A |
| CR-29 | 02/11/2026 | Chốt thứ tự code: **F0** Nền tảng → **F1** QR & menu → **F2** Đặt món & thanh toán → **F3** Màn hình Bar → **F4** OTP & tích điểm → **F5** Thu ngân hỗ trợ → **F6** Quản trị → **F7** AI gợi ý → **F8** Báo cáo & dashboard. Mã nguồn đặt tại `2.San_pham/smartcafe/`, biên bản kiểm thử tại `1.Bao_cao/Kiem_thu/` | Làm trước mạch đầu-cuối chính để sớm có bản demo; luồng sau dùng lại dữ liệu và API của luồng trước | README thiết kế (D26), IV.3 Mục 1.1 (đổi `2.San_pham/source/` → `2.San_pham/smartcafe/`); B, C, E, D | A |
| CR-30 | 02/11/2026 | Dùng kho GitHub `thanhbinh0493/smartcafe` làm nơi lưu trữ và review chung toàn bộ project (tài liệu + mã nguồn) thay cho gửi file nén; thêm `README.md` ở thư mục gốc giới thiệu dự án và giai đoạn hiện tại | Cả nhóm cùng review, có lịch sử thay đổi, luôn dùng bản mới nhất | Toàn bộ thư mục project; `README.md` gốc; cả nhóm | A |
| CR-31 | 02/11/2026 | Chốt P13: chỉ gắn nhãn khuyến mãi khi giá KM **thấp hơn** giá đang bán; nếu không thì bán giá thường và không hiện nhãn KM | Tránh khách hiểu nhầm là đang được giảm giá | README thiết kế (D27), III.1 UC03; biên bản kiểm thử F1 Mục 7; module menu (đã cài ở F1), dashboard F8 (doanh thu KM) | A |
| CR-32 | 02/11/2026 | Sửa cấu trúc bảng `orders`: giữ mã đơn ngắn `CG-0142` (đếm lại mỗi ngày), thêm cột `order_date` và ràng buộc UNIQUE trên 2 cột (order_code, order_date) thay cho UNIQUE trên riêng `order_code` | Phát hiện khi code F2: UC05 đếm lại mã đơn mỗi ngày nhưng schema đặt `order_code` UNIQUE toàn bảng → sang ngày thứ 2 sẽ trùng mã và lỗi | README thiết kế (D28), `schema.sql`, IV.1 (lược đồ + từ điển dữ liệu), ERD (`IV_erd.puml` + PNG), migration `0002`; B | A |
| CR-33 | 03/11/2026 | Chốt P14: **bỏ popup chi tiết món W01a**; bấm "+" trên menu là thêm ngay, số lượng và ghi chú chỉnh trong giỏ hàng W02 | Đạt NFR-U2 (đặt 2 món trong 5 lần chạm; giữ popup thì cần ≥ 7 lần) | README thiết kế (D29), IV.2 (sitemap); biên bản kiểm thử F2 Mục 7; frontend W01, W02 (đã cài ở F2); E | A |
| CR-34 | 03/11/2026 | Chốt P15: pha chế "Hoàn tác" món cuối cùng (đơn đã "Có thể lấy") thì **đơn quay lại "Đang pha chế"** (READY → PREPARING, ghi lịch sử, khách thấy lại "Đang pha"). Duyệt kết quả F3, gộp F2 + F3 vào nhánh `main` (local) và bắt đầu code F4 | Bấm nhầm "Xong" là thao tác hay gặp; nếu không cho hoàn tác thì khách được báo "Có thể lấy" khi đồ chưa pha xong | README thiết kế (D30), III.1 UC18, biểu đồ trạng thái đơn (`III_state_don_hang.puml` + PNG), IV.3; biên bản kiểm thử F3 Mục 7; module bar (đã cài ở F3); B, E | A |
| CR-35 | 03/11/2026 | Chốt P16: **không thu thập tên khách**, thành viên chỉ định danh bằng số điện thoại đã xác thực OTP; bỏ cột `customers.name`, lời chào "Xin chào – X điểm". Duyệt kết quả F4 (84/84 đạt), gộp F4 vào `main` (local) và bắt đầu code F5 – Thu ngân hỗ trợ | Số điện thoại đã đủ để tích điểm và gợi ý món; ít dữ liệu cá nhân hơn (NFR-S7) | README thiết kế (D31, P16), `schema.sql`, IV.1, ERD + sơ đồ data model, SD01, wireframe W01 (`.puml` + PNG), III.1 UC02, III.2, IV.2, IV.3; migration `0003`; module customer, frontend W01; biên bản kiểm thử F4 Mục 7; B, C, E | A |
| CR-36 | 03/11/2026 | Duyệt kết quả F5 (53/53 đạt), gộp F5 + D31 vào `main` (local, chưa đẩy GitHub) và bắt đầu code F6 – Quản trị (UC09–UC15) | F5 đạt đủ điều kiện theo D25 | Nhánh `main`, `feature/f6-quan-tri`; module admin (backend + 7 màn hình Web Admin), `/ws/menu`; biên bản kiểm thử F6; B, E, D | A |
| CR-37 | 03/11/2026 | Duyệt kết quả F6 – Quản trị (230/230 đạt), gộp F6 vào `main` (local) và bắt đầu code F7 – AI gợi ý món (2 chế độ + "Thường gọi kèm") | F6 đạt đủ điều kiện theo D25 | Nhánh `main`, `feature/f7-ai-goi-y`; IV.2, IV.3 (API quản trị); biên bản kiểm thử F7; C, B, E, D | A |
| CR-38 | 03/11/2026 | Chốt P17–P20 cho F7: dữ liệu lịch sử `seed_orders` **tự nạp khi khởi động** + SĐT demo 0901000001 (D32); FP-Growth dùng **mlxtend** (D33); thêm `recommendation_log_id` vào API đặt đơn (D34); thời tiết **giả lập mặc định**, API key tùy chọn (D35) | Theo phương án khuyến nghị: demo được ngay chế độ thành viên, đúng II.2, đo được hiệu quả gợi ý, không phụ thuộc mạng / key khi demo | README thiết kế (D32–D35, P17–P20), II.2 Mục 2.3–2.5, IV.3; `start.sh`, Dockerfile / requirements, `.env.example`; module recommend, API đặt đơn; C, B, E | A |
| CR-39 | 03/11/2026 | Duyệt kết quả F7 – AI gợi ý món (71/71 đạt), gộp F7 vào `main` (local) và code F8 – Báo cáo ngày & dashboard. Phát sinh 2 đề xuất chờ chốt: P21 (bù báo cáo khi khởi động), P22 (cách gộp số liệu "Tất cả chi nhánh") | F7 đạt đủ điều kiện theo D25; laptop demo thường tắt lúc 00:05 | Nhánh `main`, `feature/f8-bao-cao`; README thiết kế (P21, P22), IV.1, IV.2, IV.3; module report, W08; biên bản kiểm thử F8; B, E, D | A |
| CR-40 | 03/11/2026 | Chốt P21: **tự tính bù báo cáo ngày còn thiếu khi backend khởi động** (D36). Chốt P22: dashboard "Tất cả chi nhánh" **giữ cách gộp từ bảng báo cáo** (tỉ lệ món từ gợi ý trung bình theo số đơn, top 5 gộp từ top 5 từng chi nhánh) (D37). Duyệt kết quả F8 (41/41 đạt), gộp F8 vào `main` (local) – hoàn tất giai đoạn Lập trình F0 → F8 | Laptop demo thường tắt lúc 00:05; giữ dashboard chỉ đọc bảng báo cáo, sai lệch nhỏ chấp nhận được | README thiết kế (D36, D37, P21, P22), IV.1; biên bản kiểm thử F8 Mục 7–8; README gốc, README mã nguồn; nhánh `main`; B, E | A |
| CR-41 | 03/11/2026 | Bắt đầu giai đoạn VI – Kiểm thử hệ thống: kịch bản xuyên luồng F1 → F8 trên nhiều thiết bị + kiểm thử toàn bộ yêu cầu phi chức năng (hiệu năng, bảo mật, độ tin cậy, khả dụng, bảo trì); bộ test case lưu **Markdown** trong `1.Bao_cao/Kiem_thu/` như các biên bản luồng (cuối kỳ xuất .docx); bổ sung script sao lưu / khôi phục CSDL (NFR-R5) | Đã xong F0 → F8; theo Project_Plan giai đoạn VI | Kế hoạch + biên bản kiểm thử hệ thống; `system_test/`, `backend/tests/st/`, `scripts/backup_db.ps1`; D, B, E | A |
| CR-42 | 03/11/2026 | Chốt P23: **cache trong tiến trình cho API đọc của khách** (menu, quét QR, nhãn đơn, bán chạy, luật FP-Growth), xóa ngay khi quản trị đổi dữ liệu (D38) | Kiểm thử tải: backend 1 tiến trình dùng hết 1 lõi CPU, p95 ~1 giây với 50 khách; giữ kiến trúc 1 tiến trình (WebSocket hub trong bộ nhớ) | README thiết kế (D38, P23), IV.3; module menu, branch, order, recommend, admin; biên bản kiểm thử hệ thống; B, C | A |
| CR-43 | 03/11/2026 | Chốt P24: **mô hình tải của NFR-P2 / P3** = 50 khách đồng thời, mỗi khách thao tác 3–5 giây một lần; giữ ngưỡng p95 ≤ 300 / 500 ms; mức 0,5–1,5 giây/lần chỉ là kiểm thử quá tải tham khảo (yêu cầu không lỗi) (D39) | Sau khi cache vẫn chưa đạt ở mô hình 1 giây/lần (~180 request/giây); mô hình 3–5 giây/lần sát thực tế và vẫn gấp nhiều lần tải 3 chi nhánh × 60 đơn/giờ | README thiết kế (D39, P24), III.2 (NFR-P2, P3); `st_hieu_nang.py`; biên bản kiểm thử hệ thống; D | A |
| CR-44 | 03/11/2026 | Duyệt kết quả giai đoạn VI – Kiểm thử hệ thống (66/66 đạt, hồi quy 664/664), gộp vào `main` (local). Chốt P12: **chỉ demo trên laptop, không làm bản dự phòng trên cloud** (D40). Bắt đầu giai đoạn VII – viết Hướng dẫn sử dụng có ảnh chụp màn hình cho từng vai trò; chụp xong thì dừng môi trường demo | Giai đoạn VI đạt điều kiện; giảm việc không cần thiết, dự phòng bằng sao lưu CSDL (NFR-R5) | README thiết kế (D40, P12); biên bản + kế hoạch kiểm thử hệ thống; `1.Bao_cao/Huong_dan_su_dung/`; `system_test/chup_anh_hdsd.py`; README gốc, README mã nguồn; D, A | A |
| CR-45 | 03/11/2026 | Bỏ giai đoạn "Các rủi ro của dự án"; bắt đầu chuẩn hóa tài liệu. Cập nhật bảng phân công `Nhom_8_Phan_cong.xlsx` theo thực tế đã làm (bỏ IoT, giai đoạn V ghi theo 9 luồng F0 → F8, thêm thiết kế kiến trúc & API, kiểm thử hệ thống, HDSD, diễn tập demo; sửa tiêu đề cột G/H bị đảo, ngày dạng dd/mm/yyyy). **Kết thúc dự án 16/11/2026**, dàn đều các giai đoạn từ 21/09 (D41; chốt P11) | Rút ngắn thời gian, kế hoạch phải khớp sản phẩm thực tế | `Nhom_8_Phan_cong.xlsx`, `Project_Plan.md`, README thiết kế (D41, P11), IV.3 Mục 3, CLAUDE.md, README gốc; cả nhóm | A |
| CR-46 | 04/11/2026 | Chuẩn hóa tài liệu (VIII.1): đồng bộ tài liệu II–VII với mã nguồn và kế hoạch D41 – ngày thực hiện ở đầu các tài liệu II.1–IV.3 theo kế hoạch; III.1 ghi luồng code F0–F8 thay cho "module V.1–V.3", Quản trị viên không dùng màn hình Bar, tự hủy đơn 15 phút chưa cài (D22); IV.2 bỏ phần Figma, thêm bảng đối chiếu wireframe ↔ giao diện thật; IV.3 thêm bảng thông tin + `/api/health`; III.2 sửa danh sách module, script sao lưu; biên bản kiểm thử F0–F8 ghi D lập, A duyệt; HDSD bổ sung bước chọn phương thức thanh toán | Tài liệu phải khớp sản phẩm và kế hoạch trước khi xuất .docx | README thiết kế, II.1, II.2, III.1, III.2, IV.1, IV.2, IV.3; biên bản kiểm thử F0–F8; HDSD; A, D | A |
| CR-47 | 04/11/2026 | Chốt mẫu tài liệu nộp (VIII.2): bản Word sinh tự động từ Markdown theo định dạng mẫu báo cáo môn học, bìa dùng `Mẫu bìa.docx` (thông tin bìa điền 1 lần ở `thong_tin_bia.json`), gom thành 5 bộ hồ sơ (D42). Phát hiện mẫu báo cáo tổng kết cần phần chi phí, giám sát, rủi ro → mở P25 | Nhóm không có mẫu riêng cho tài liệu thiết kế; giữ một nguồn nội dung, tránh sửa tay 2 nơi | README thiết kế (D42, P25); `1.Bao_cao/Xuat_docx/` (công cụ + 6 tệp .docx); D, A | A |

## 4. HÌNH ẢNH / VIDEOS
(Bổ sung ảnh chụp buổi họp nếu có.)

## 5. KẾT LUẬN
**Quyết định:**
- Thông qua CR-26: môi trường demo là Docker Desktop trên laptop, cài tại `D:\Docker` (D24).
- Thông qua CR-27: tạm gác P11, A tự hoàn thiện timeline thủ công.
- Thông qua CR-28: code theo từng luồng cốt lõi, mỗi luồng có test tự động + biên bản kiểm thử (D25).
- Thông qua CR-29: thứ tự luồng F0 → F8, vị trí mã nguồn và biên bản kiểm thử (D26).
- Thông qua CR-30: dùng kho GitHub chung cho toàn bộ project.
- Thông qua CR-31: chỉ gắn nhãn KM khi giá KM thấp hơn giá đang bán (D27).
- Thông qua CR-32: mã đơn ngắn + UNIQUE (order_code, order_date) (D28).
- Thông qua CR-33: bỏ popup W01a, chỉnh số lượng và ghi chú trong giỏ hàng (D29).
- Thông qua CR-34: hoàn tác món cuối đưa đơn từ "Có thể lấy" về "Đang pha chế" (D30); F3 được duyệt, gộp F2 + F3 vào `main`, chuyển sang F4.
- Thông qua CR-35: không thu thập tên khách, chỉ dùng SĐT (D31); F4 được duyệt, gộp vào `main`, chuyển sang F5.
- Thông qua CR-36: F5 được duyệt, gộp vào `main`, chuyển sang F6 – Quản trị.
- Thông qua CR-37: F6 được duyệt, gộp vào `main`, chuyển sang F7 – AI gợi ý món.
- Thông qua CR-38: dữ liệu lịch sử tự nạp + SĐT demo (D32), mlxtend (D33), `recommendation_log_id` (D34), thời tiết giả lập mặc định (D35).
- Code tiếp các luồng F3 → F8 trên máy, chưa đẩy lên GitHub cho tới khi PM yêu cầu.
- Thông qua CR-39: F7 được duyệt, gộp vào `main`, code F8.
- Thông qua CR-40: tự bù báo cáo khi khởi động (D36), giữ cách gộp số liệu "Tất cả chi nhánh" (D37); F8 được duyệt, gộp vào `main` – hoàn tất lập trình F0 → F8.
- Thông qua CR-41: bắt đầu giai đoạn VI – kiểm thử hệ thống, test case lưu Markdown.
- Thông qua CR-42: cache trong tiến trình cho API đọc của khách (D38).
- Thông qua CR-43: mô hình tải NFR-P2 / P3 là 50 khách, 3–5 giây/thao tác (D39).
- Thông qua CR-44: giai đoạn VI được duyệt, gộp vào `main`; chỉ demo trên laptop, không làm cloud (D40); bắt đầu giai đoạn VII – Hướng dẫn sử dụng.
- Thông qua CR-45: bỏ giai đoạn rủi ro, kết thúc dự án 16/11/2026, kế hoạch dàn đều 21/09 → 16/11 (D41).
- Thông qua CR-46: tài liệu II–VII đã đồng bộ với mã nguồn và kế hoạch D41.
- Thông qua CR-47: mẫu tài liệu nộp và 5 bộ hồ sơ Word (D42).
- Vấn đề còn mở: P25 (phần chi phí, giám sát, rủi ro trong báo cáo tổng kết).

**Việc cần làm:**
| Việc | Người phụ trách | Hạn |
|:---|:---|:---|
| Khởi động lại máy, cập nhật WSL, chạy thử Docker (`hello-world`) | A | 03/11/2026 |
| Các thành viên tự cài Docker Desktop trên máy mình để phát triển | B, C, E | 05/11/2026 |
| Chốt P12 (có làm bản demo dự phòng trên cloud không) – đã xong: không làm (CR-44) | A | 03/11/2026 |
| Cập nhật timeline (Project_Plan.md, IV.3 Mục 3, bảng phân công) – đã xong (CR-45) | A | 03/11/2026 |
| Code F0 (nền tảng) + F1 (QR & menu) kèm test và biên bản kiểm thử | B, E (D lập biên bản) | 08/11/2026 |
| Review biên bản kiểm thử F0, F1 trước khi sang F2 | A, D | 08/11/2026 |
| Đẩy project lên GitHub, mời các thành viên vào kho | A | 03/11/2026 |
| Clone kho, chạy thử theo README mã nguồn, review tài liệu + code | B, C, D, E | 08/11/2026 |
| Code F2 (đặt món & thanh toán giả lập) kèm test + biên bản kiểm thử | B, E (D lập biên bản) | 08/11/2026 |
| Code F3 (màn hình Bar) kèm test + biên bản kiểm thử | B, E (D lập biên bản) | 08/11/2026 |
| Chốt P15 (hoàn tác món cuối) – đã xong (CR-34) | A | 03/11/2026 |
| Code F4 (OTP giả lập & tích điểm) kèm test + biên bản kiểm thử – đã xong, duyệt (CR-35) | C, B, E (D lập biên bản) | 03/11/2026 |
| Code F5 (thu ngân tra cứu, hủy đơn & hoàn tiền giả lập) kèm test + biên bản kiểm thử – đã xong, duyệt (CR-36) | B, E (D lập biên bản) | 03/11/2026 |
| Code F6 (quản trị: danh mục, món, chi nhánh, nhân viên, menu chi nhánh, bàn & QR, khuyến mãi) kèm test + biên bản kiểm thử – đã xong, duyệt (CR-37) | B, E (D lập biên bản) | 03/11/2026 |
| Code F7 (AI gợi ý món 2 chế độ + "Thường gọi kèm") kèm test + biên bản kiểm thử – đã xong, duyệt (CR-39) | C, B, E (D lập biên bản) | 03/11/2026 |
| Code F8 (báo cáo ngày + dashboard W08) kèm test + biên bản kiểm thử – đã xong, duyệt (CR-40) | B, E (D lập biên bản) | 03/11/2026 |
| Chốt P21, P22 – đã xong (CR-40) | A | 03/11/2026 |
| Kiểm thử hệ thống (giai đoạn VI) + biên bản; sửa lỗi phát hiện (BUG-ST-01…06) kèm test hồi quy | D, B, E | 03/11/2026 |
| Review biên bản kiểm thử hệ thống, duyệt kết thúc giai đoạn VI – đã xong (CR-44) | A | 03/11/2026 |
| Viết Hướng dẫn sử dụng (giai đoạn VII) kèm ảnh chụp màn hình | D | 03/11/2026 |
| Review Hướng dẫn sử dụng, thử lại các bước trên máy demo | A, cả nhóm | 05/11/2026 |
| Chuẩn hóa tài liệu II–VII theo mã nguồn – đã xong (CR-46) | A, D | 04/11/2026 |
| Xuất tài liệu Markdown sang .docx theo mẫu – đã có công cụ + bản đầu (CR-47); xuất lại sau khi điền thông tin bìa | D | 09/11/2026 |
| Điền thông tin bìa (khoa, bộ môn, giảng viên, lớp, họ tên + mã SV) vào `thong_tin_bia.json` | A | 06/11/2026 |
| Chốt P25 (chi phí, giám sát, rủi ro trong báo cáo tổng kết) | A | 09/11/2026 |
| Báo cáo tổng kết (10–12/11), slide (12–14/11), diễn tập demo (14–15/11), biên bản nghiệm thu (16/11) | A, E, D | 16/11/2026 |
| Sao lưu CSDL bằng `scripts/backup_db.ps1` trước mỗi buổi demo (NFR-R5) | D | Trước mỗi buổi demo |
| Review công thức + trọng số gợi ý, tinh chỉnh theo kết quả Hit Rate@5 (biên bản F7 Mục 4.7) | C | 10/11/2026 |
