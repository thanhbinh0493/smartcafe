# BIÊN BẢN HỌP TUẦN 07

## 1. THÀNH PHẦN
| Thành viên | Vai trò | Có mặt |
|:---|:---|:---:|
| Nguyễn Thanh Bình (A) | PM / Team Lead (chủ trì) | ✔ |
| Nguyễn Trường Thiên (B) | Backend Developer | ✔ |
| Lê Minh Sơn (C) | AI Specialist | ✔ |
| Ngô Duy Đô (D) | Tester / QA, thư ký | ✔ |
| Nguyễn Quang Tú (E) | Frontend Developer | ✔ |

## 2. NGÀY HỌP
Tuần 07 (02/11/2026 – 08/11/2026). Hình thức: họp nhóm. Thư ký: Ngô Duy Đô (D).

## 3. NỘI DUNG
| Mã | Ngày | Nội dung thay đổi / thảo luận | Lý do | Ảnh hưởng (tài liệu, module, người) | Người đề xuất |
|:---|:---|:---|:---|:---|:---|
| CR-42 | 02/11/2026 | Chốt P23: **cache trong tiến trình cho API đọc của khách** (menu, quét QR, nhãn đơn, bán chạy, luật FP-Growth), xóa ngay khi quản trị đổi dữ liệu (D38) | Kiểm thử tải: backend 1 tiến trình dùng hết 1 lõi CPU, p95 ~1 giây với 50 khách; giữ kiến trúc 1 tiến trình (WebSocket hub trong bộ nhớ) | README thiết kế (D38, P23), IV.3; module menu, branch, order, recommend, admin; biên bản kiểm thử hệ thống; B, C | Nguyễn Thanh Bình (A) |
| CR-43 | 03/11/2026 | Chốt P24: **mô hình tải của NFR-P2 / P3** = 50 khách đồng thời, mỗi khách thao tác 3–5 giây một lần; giữ ngưỡng p95 ≤ 300 / 500 ms; mức 0,5–1,5 giây/lần chỉ là kiểm thử quá tải tham khảo (yêu cầu không lỗi) (D39) | Sau khi cache vẫn chưa đạt ở mô hình 1 giây/lần (~180 request/giây); mô hình 3–5 giây/lần sát thực tế và vẫn gấp nhiều lần tải 3 chi nhánh × 60 đơn/giờ | README thiết kế (D39, P24), III.2 (NFR-P2, P3); `st_hieu_nang.py`; biên bản kiểm thử hệ thống; D | Nguyễn Thanh Bình (A) |
| CR-44 | 03/11/2026 | Duyệt kết quả giai đoạn VI – Kiểm thử hệ thống (66/66 đạt, hồi quy 664/664), gộp vào `main` (local). Chốt P12: **chỉ demo trên laptop, không làm bản dự phòng trên cloud** (D40). Bắt đầu giai đoạn VII – viết Hướng dẫn sử dụng có ảnh chụp màn hình cho từng vai trò; chụp xong thì dừng môi trường demo | Giai đoạn VI đạt điều kiện; giảm việc không cần thiết, dự phòng bằng sao lưu CSDL (NFR-R5) | README thiết kế (D40, P12); biên bản + kế hoạch kiểm thử hệ thống; `1.Bao_cao/Huong_dan_su_dung/`; `system_test/chup_anh_hdsd.py`; README gốc, README mã nguồn; D, A | Nguyễn Thanh Bình (A) |
| CR-45 | 04/11/2026 | Bỏ giai đoạn "Các rủi ro của dự án"; bắt đầu chuẩn hóa tài liệu. Cập nhật bảng phân công `Nhom_8_Phan_cong.xlsx` theo thực tế đã làm (bỏ IoT, giai đoạn V ghi theo 9 luồng F0 → F8, thêm thiết kế kiến trúc & API, kiểm thử hệ thống, HDSD, diễn tập demo; sửa tiêu đề cột G/H bị đảo, ngày dạng dd/mm/yyyy). **Kết thúc dự án 16/11/2026**, dàn đều các giai đoạn từ 21/09 (D41; chốt P11) | Rút ngắn thời gian, kế hoạch phải khớp sản phẩm thực tế | `Nhom_8_Phan_cong.xlsx`, `Project_Plan.md`, README thiết kế (D41, P11), IV.3 Mục 3, CLAUDE.md, README gốc; cả nhóm | Nguyễn Thanh Bình (A) |
| CR-46 | 06/11/2026 | Chuẩn hóa tài liệu (VIII.1): đồng bộ tài liệu II–VII với mã nguồn và kế hoạch D41 – ngày thực hiện ở đầu các tài liệu II.1–IV.3 theo kế hoạch; III.1 ghi luồng code F0–F8 thay cho "module V.1–V.3", Quản trị viên không dùng màn hình Bar, tự hủy đơn 15 phút chưa cài (D22); IV.2 bỏ phần Figma, thêm bảng đối chiếu wireframe ↔ giao diện thật; IV.3 thêm bảng thông tin + `/api/health`; III.2 sửa danh sách module, script sao lưu; biên bản kiểm thử F0–F8 ghi D lập, A duyệt; HDSD bổ sung bước chọn phương thức thanh toán | Tài liệu phải khớp sản phẩm và kế hoạch trước khi xuất .docx | README thiết kế, II.1, II.2, III.1, III.2, IV.1, IV.2, IV.3; biên bản kiểm thử F0–F8; HDSD; A, D | Nguyễn Thanh Bình (A) |
| CR-47 | 07/11/2026 | Chốt định dạng tài liệu nộp (VIII.2): theo mẫu báo cáo môn học và mẫu bìa của Học viện, gom thành 5 bộ hồ sơ (D42). Phát hiện mẫu báo cáo tổng kết cần phần chi phí, giám sát, rủi ro → mở P25 | Môn học chỉ có mẫu báo cáo tổng kết và mẫu bìa | README thiết kế (D42, P25); 5 bộ hồ sơ Word; D, A | Nguyễn Thanh Bình (A) |

## 4. HÌNH ẢNH / VIDEOS
(Bổ sung ảnh chụp buổi họp nếu có.)

## 5. KẾT LUẬN
**Quyết định:**
- Thông qua CR-42: cache trong tiến trình cho API đọc của khách (D38).
- Thông qua CR-43: mô hình tải NFR-P2 / P3 là 50 khách, 3–5 giây/thao tác (D39).
- Thông qua CR-44: giai đoạn VI được duyệt, gộp vào `main`; chỉ demo trên laptop, không làm cloud (D40); bắt đầu giai đoạn VII – Hướng dẫn sử dụng.
- Thông qua CR-45: bỏ giai đoạn rủi ro, kết thúc dự án 16/11/2026, kế hoạch dàn đều 21/09 → 16/11 (D41).
- Thông qua CR-46: tài liệu II–VII đã đồng bộ với mã nguồn và kế hoạch D41.
- Thông qua CR-47: định dạng tài liệu nộp theo mẫu môn học, 5 bộ hồ sơ (D42).

**Việc cần làm:**
| Việc | Người phụ trách | Hạn |
|:---|:---|:---|
| Viết báo cáo tổng kết môn học | Nguyễn Thanh Bình | 12/11/2026 |
| Thiết kế slide thuyết trình bảo vệ cuối kỳ | Nguyễn Quang Tú | 14/11/2026 |
| Chuẩn bị và diễn tập demo trên laptop: kịch bản demo, dữ liệu sạch, sao lưu CSDL | Nguyễn Thanh Bình, Nguyễn Quang Tú | 15/11/2026 |
