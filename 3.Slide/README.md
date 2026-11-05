# Slide thuyết trình bảo vệ

| Tệp | Nội dung |
|:---|:---|
| `Nhom_X_Slide.pptx` | Mẫu của môn học (10 slide tiêu đề – thứ tự phần trình bày) |
| `Nhom_8_Slide.pptx` | **Slide bảo vệ của nhóm** – 20 slide, 16:9, theo đúng thứ tự phần của mẫu; có ghi chú cho người thuyết trình (speaker notes) ở từng slide |
| `tao_slide/` | Công cụ sinh slide (`tao_slide.js`, pptxgenjs) – số liệu lấy từ báo cáo tổng kết, họ tên thành viên lấy từ `1.Bao_cao/Xuat_docx/thong_tin_bia.json` |

## Bố cục (khoảng 20 phút + demo)
| Phần (theo mẫu) | Slide |
|:---|:---|
| Mở đầu | 1 – Bìa |
| 01 Giới thiệu thành viên | 2 |
| 02 Phân công công việc | 3 |
| 03 Tổng quan dự án | 4 – bài toán & giải pháp · 5 – phạm vi, quy mô |
| 04 Kế hoạch triển khai | 6 – dòng thời gian 11 giai đoạn · 7 – kiểm soát thay đổi |
| 05 Chi phí | 8 – dự toán 63,03 triệu đồng (biểu đồ theo thành viên) |
| 06 Nhân lực | 9 – ma trận RACI |
| 07 Quá trình triển khai | 10 – phân tích & thiết kế · 11 – lập trình 9 luồng · 12 – sản phẩm trên điện thoại · 13 – Web Admin · 14 – AI gợi ý · 15 – kiểm thử hệ thống · 16 – giám sát & rủi ro |
| 08 Kết quả | 17 – kết quả so với mục tiêu · 18 – bài học, hướng phát triển |
| 09 Sản phẩm nộp | 19 |
| Kết thúc | 20 – Cảm ơn, demo & hỏi đáp |

Thiết kế: tông màu cà phê (nâu `#6F4E37`, điểm nhấn cam `#EA580C` – màu nhãn khuyến mãi của ứng dụng), tiêu đề Cambria, nội dung Calibri; ảnh chụp lấy từ Hướng dẫn sử dụng.

## Sinh lại slide
```powershell
cd 3.Slide\tao_slide
npm install          # lần đầu (Node ≥ 18)
node tao_slide.js    # → 3.Slide\Nhom_8_Slide.pptx
```
Sau khi điền họ tên thành viên, giảng viên vào `thong_tin_bia.json` thì chạy lại để cập nhật slide 1 và 2.
