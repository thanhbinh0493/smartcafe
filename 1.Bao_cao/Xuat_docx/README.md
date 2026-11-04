# Xuất tài liệu sang Word (.docx)

Bản gốc của mọi tài liệu là các tệp Markdown trong kho. Thư mục này chứa **bản Word sinh tự động** để nộp / in (D42, CR-47). Sửa nội dung thì sửa tệp `.md`, rồi chạy lại công cụ; không sửa trực tiếp tệp `.docx`.

| Tệp | Nội dung | Nguồn |
|:---|:---|:---|
| `Nhom_8_Bao_cao_tong_ket.docx` | Báo cáo tổng kết 10 phần theo mẫu môn học (ngày lập 10/11/2026) – `--chi 0` | `1.Bao_cao/Bao_cao_tong_ket.md` |
| `SmartCafe_1_Phan_tich_Thiet_ke.docx` | Tài liệu phân tích & thiết kế: II.1 → IV.3, Phụ lục A (quyết định D…, vấn đề mở P…), Phụ lục B (`schema.sql`) | `1.Bao_cao/Thiet_ke_he_thong/` |
| `SmartCafe_2_Ho_so_kiem_thu.docx` | Quy ước kiểm thử, kế hoạch kiểm thử hệ thống, biên bản F0 → F8 và kiểm thử hệ thống | `1.Bao_cao/Kiem_thu/` |
| `SmartCafe_3_Huong_dan_su_dung.docx` | Hướng dẫn sử dụng (33 ảnh) | `1.Bao_cao/Huong_dan_su_dung/` |
| `SmartCafe_4_Ke_hoach_Pham_vi.docx` | Phạm vi dự án + kế hoạch (bảng phân công đặt trên trang khổ ngang) | `1.Bao_cao/Pham_Vi_Du_An.md`, `Project_Plan.md` |
| `Bien_ban_hop_Tuan_XX.docx` | Biên bản họp từng tuần (không bìa) | `4.Tai_lieu_khac/Bien_ban_hop/` |

## Định dạng (theo mẫu báo cáo môn học `1.Bao_cao/Nhom_X_Bao_cao.docx`)
- A4; lề trên / dưới 2 cm, trái 3 cm, phải 2 cm; Times New Roman 14, giãn dòng 1,5, căn đều hai bên; số trang ở giữa chân trang.
- Thứ tự: **trang bìa** (từ `1.Bao_cao/Mẫu bìa.docx`) → **thông tin tài liệu + lịch sử phiên bản** → **mục lục tự động** (cấp 1–2) → các chương (mỗi chương sang trang mới, tiêu đề 16pt in đậm căn giữa) → phụ lục.
- Bảng: viền xám mảnh, hàng tiêu đề tô xanh nhạt + in đậm, lặp lại khi sang trang; chữ 12pt (bảng 5–6 cột 11pt, ≥ 7 cột 9,5pt); bề rộng cột tự tính theo nội dung.
- Hình: căn giữa, tối đa rộng 16 cm / cao 13 cm, chú thích in nghiêng "Hình <chương>.<số>: …".
- Mã nguồn: Consolas 9pt; chữ dạng mã trong câu: Consolas 12pt.

## Trang bìa
Điền **một lần** ở `thong_tin_bia.json` (khoa, bộ môn, giảng viên, lớp, họ tên + mã SV 5 thành viên), rồi chạy lại – mọi bìa tự cập nhật. Các ô còn dạng `[ĐIỀN …]` là chưa có thông tin.

## Cách chạy
Cần: pandoc ≥ 2.12, Microsoft Word (cập nhật mục lục, ghép bìa, xuất PDF qua COM), Python có `python-docx`, `pywin32` (`pymupdf` nếu muốn dựng ảnh trang để xem).
```powershell
cd D:\PTIT\HK3\QLDAPM\QLDAPM_Nhom_8
2.San_pham\smartcafe\system_test\.venv\Scripts\python 1.Bao_cao\Xuat_docx\xuat_docx.py            # tất cả (~3 phút)
2.San_pham\smartcafe\system_test\.venv\Scripts\python 1.Bao_cao\Xuat_docx\xuat_docx.py --chi 1,5   # chỉ bộ 1 + biên bản họp
2.San_pham\smartcafe\system_test\.venv\Scripts\python 1.Bao_cao\Xuat_docx\xuat_docx.py --pdf <thư mục>  # thêm bản PDF
```
- `loc_pandoc.lua`: bỏ liên kết nội bộ giữa các tệp `.md`, đánh số hình theo chương, ngắt trang / trang khổ ngang.
- Đóng các tệp `.docx` trong thư mục này trước khi chạy (Word đang mở tệp sẽ không ghi đè được).
