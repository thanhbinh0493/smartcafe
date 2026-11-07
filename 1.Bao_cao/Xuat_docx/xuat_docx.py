# -*- coding: utf-8 -*-
"""Xuất tài liệu Markdown của dự án sang .docx theo mẫu báo cáo môn học (VIII.2, CR-47).

    <venv>\\Scripts\\python 1.Bao_cao\\Xuat_docx\\xuat_docx.py [--chi 1,3] [--pdf]

Cần: pandoc (≥ 2.12), Microsoft Word (cập nhật mục lục + ghép trang bìa qua COM), python-docx, pywin32
(và pymupdf nếu muốn dựng ảnh trang để xem nhanh).

Định dạng theo `1.Bao_cao/Nhom_X_Bao_cao.docx` (mẫu báo cáo môn học): A4, lề trên/dưới 2 cm, trái 3 cm, phải 2 cm,
Times New Roman 14, giãn dòng 1,5, căn đều 2 bên, số trang ở chân trang. Trang bìa lấy từ `1.Bao_cao/Mẫu bìa.docx`,
thông tin bìa ở `thong_tin_bia.json`.

Bộ hồ sơ (D42): 1 Phân tích & Thiết kế · 2 Hồ sơ kiểm thử · 3 Hướng dẫn sử dụng · 4 Kế hoạch & Phạm vi ·
5 Biên bản họp (mỗi tuần 1 file, không bìa).
"""
from __future__ import annotations

import argparse
import copy
import io
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent                         # thư mục gốc kho
BC = ROOT / "1.Bao_cao"
TK = BC / "Thiet_ke_he_thong"
KT = BC / "Kiem_thu"
MAU_BAO_CAO = BC / "Nhom_X_Bao_cao.docx"
MAU_BIA = BC / "Mẫu bìa.docx"
LUA = HERE / "loc_pandoc.lua"
FONT = "Times New Roman"
PHIEN_BAN = "1.0"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------- bộ hồ sơ
BO = [
    {
        "so": 0, "file": "Nhom_8_Bao_cao_tong_ket", "tieu_de": "BÁO CÁO TỔNG KẾT DỰ ÁN",
        "nguoi": "Nguyễn Thanh Bình (A – PM) lập; cả nhóm review",
        "ngay": "10/11/2026",
        "lich_su": "Bản đầy đủ 10 phần theo mẫu báo cáo môn học (CR-48, CR-49) | Nguyễn Thanh Bình (A)",
        "phan": [(BC / "Bao_cao_tong_ket.md", {"bat_dau_tu": "# PHẦN I"})],
    },
    {
        "so": 1, "file": "SmartCafe_1_Phan_tich_Thiet_ke", "tieu_de": "TÀI LIỆU PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG",
        "nguoi": "Nguyễn Thanh Bình (A), Nguyễn Trường Thiên (B), Lê Minh Sơn (C), Ngô Duy Đô (D), Nguyễn Quang Tú (E) – người thực hiện từng chương ghi ở đầu chương",
        "phan": [(TK / "II.1_Khao_sat_quy_trinh.md", {}), (TK / "II.2_Nghien_cuu_cong_nghe.md", {}),
                 (TK / "III.1_Use_Case_Sequence.md", {}), (TK / "III.2_Yeu_cau_phi_chuc_nang_Data_Model.md", {}),
                 (TK / "IV.1_Thiet_ke_CSDL.md", {}), (TK / "IV.2_Thiet_ke_giao_dien.md", {}),
                 (TK / "IV.3_Kien_truc_va_API.md", {}),
                 ("PHU_LUC_QUYET_DINH", {}), ("PHU_LUC_SCHEMA", {})],
    },
    {
        "so": 2, "file": "SmartCafe_2_Ho_so_kiem_thu", "tieu_de": "HỒ SƠ KIỂM THỬ",
        "nguoi": "Ngô Duy Đô (D – Tester / QA) lập; Nguyễn Thanh Bình (A – PM) duyệt",
        "phan": [(KT / "README.md", {"tieu_de": "# QUY ƯỚC VÀ DANH SÁCH BIÊN BẢN KIỂM THỬ"}),
                 (KT / "Ke_hoach_kiem_thu_He_thong.md", {})]
                + [(p, {}) for p in sorted(KT.glob("Bien_ban_kiem_thu_F*.md"))]
                + [(KT / "Bien_ban_kiem_thu_He_thong.md", {})],
    },
    {
        "so": 3, "file": "SmartCafe_3_Huong_dan_su_dung", "tieu_de": "HƯỚNG DẪN SỬ DỤNG",
        "nguoi": "Ngô Duy Đô (D – Tester / QA) lập; Nguyễn Thanh Bình (A – PM) duyệt",
        "phan": [(BC / "Huong_dan_su_dung" / "Huong_dan_su_dung.md", {"nang_cap": True})],
    },
    {
        "so": 4, "file": "SmartCafe_4_Ke_hoach_Pham_vi", "tieu_de": "PHẠM VI VÀ KẾ HOẠCH DỰ ÁN",
        "nguoi": "Nguyễn Thanh Bình (A – PM) lập; cả nhóm review",
        "phan": [(BC / "Pham_Vi_Du_An.md", {}),
                 (BC / "Project_Plan.md", {"bang_ngang": "## Bảng Phân công và Tiến độ chi tiết"})],
    },
]
BIEN_BAN_HOP = sorted((ROOT / "4.Tai_lieu_khac" / "Bien_ban_hop").glob("Bien_ban_hop_Tuan_*.md"))


# ---------------------------------------------------------------- Markdown
def doc_md(p: Path) -> str:
    return io.open(p, encoding="utf-8").read().replace("\r\n", "\n")


IMG = re.compile(r"(!\[[^\]]*\]\()([^)\s]+)(\))")


def chuan_bi(p: Path, opt: dict) -> str:
    s = doc_md(p)
    # ảnh: đổi đường dẫn tương đối sang tuyệt đối (gộp nhiều file từ nhiều thư mục)
    s = IMG.sub(lambda m: m.group(1) + ((p.parent / m.group(2)).resolve().as_posix()
                                        if not m.group(2).startswith("http") else m.group(2)) + m.group(3), s)
    # bỏ mục "Mục lục" viết tay (đã có mục lục tự động)
    s = re.sub(r"\n## Mục lục\n.*?(?=\n---\n|\n## )", "\n", s, flags=re.S)
    s = re.sub(r"\n---\n", "\n", s)
    if opt.get("bat_dau_tu"):                     # bỏ phần đầu tệp (tiêu đề + bảng thông tin) – đã có trang thông tin tài liệu
        s = s[s.index(opt["bat_dau_tu"]):]
    if opt.get("tieu_de"):
        s = re.sub(r"^# .*$", opt["tieu_de"], s, count=1, flags=re.M)
    if opt.get("nang_cap"):                       # HDSD: tiêu đề H1 là tên tài liệu → bỏ; "##" thành chương
        s = re.sub(r"^# .*\n", "", s, count=1, flags=re.M)
        s = re.sub(r"^(#{2,6}) ", lambda m: m.group(1)[1:] + " ", s, flags=re.M)
    # pandoc chỉ nhận bảng / tiêu đề khi có dòng trống phía trước (GitHub thì không cần)
    out: list[str] = []
    for line in s.split("\n"):
        if out and out[-1].strip() and (
                (line.startswith("|") and not out[-1].startswith("|")) or line.startswith("#")):
            out.append("")
        out.append(line)
    s = "\n".join(out)
    if opt.get("bang_ngang"):                     # bảng rộng sau tiêu đề này: đặt trên trang khổ ngang
        lines = s.split("\n")
        i = lines.index(opt["bang_ngang"])
        j = next(k for k in range(i + 1, len(lines)) if lines[k].startswith("|"))
        while j < len(lines) and lines[j].startswith("|"):
            j += 1
        lines[j:j] = ["", "%%NGANG_KET_THUC%%", ""]
        lines[i:i] = ["%%NGANG_BAT_DAU%%", ""]
        s = "\n".join(lines)
    return s.strip() + "\n\n"


def phu_luc_quyet_dinh() -> str:
    s = doc_md(TK / "README.md")
    a = s.index("## Các quyết định đã chốt")
    b = s.index("## Sơ đồ")
    body = s[a:b]
    body = body.replace("## Các quyết định đã chốt", "## A.1. Các quyết định đã chốt (D1…)")
    body = re.sub(r"## Vấn đề mở \(Open Issues\)[^\n]*", "## A.2. Vấn đề mở / đề xuất đã xử lý (P…)", body)
    return "# PHỤ LỤC A. CÁC QUYẾT ĐỊNH ĐÃ CHỐT VÀ VẤN ĐỀ MỞ\n\n" + body.strip() + "\n\n"


def phu_luc_schema() -> str:
    sql = doc_md(TK / "schema.sql")
    return ("# PHỤ LỤC B. LƯỢC ĐỒ CƠ SỞ DỮ LIỆU (schema.sql)\n\n"
            "Lược đồ PostgreSQL 16 – 18 bảng, 9 kiểu ENUM (IV.1). Migration Alembic 0001 chạy nguyên văn tệp này; "
            "0002 (mã đơn UNIQUE theo ngày – D28) và 0003 (bỏ `customers.name` – D31) đã phản ánh trong nội dung dưới đây.\n\n"
            "```sql\n" + sql.strip() + "\n```\n\n")


def trang_dau(bo: dict, ds: list[str]) -> str:
    ngay = bo.get("ngay", f"{date.today():%d/%m/%Y}")
    rows = [("Dự án", "SmartCafe – Phần mềm quản lý chuỗi quán cà phê thông minh (tích hợp AI và QR)"),
            ("Tài liệu", bo["tieu_de"]),
            ("Phiên bản", f"{PHIEN_BAN} – ngày {ngay}"),
            ("Người lập / duyệt", bo["nguoi"]),
            ("Nội dung gồm", "; ".join(ds))]
    t = "| Mục | Nội dung |\n|:---|:---|\n" + "\n".join(f"| {a} | {b} |" for a, b in rows)
    lich_su = ("| Phiên bản | Ngày | Nội dung | Người thực hiện |\n|:---|:---|:---|:---|\n"
               f"| 1.0 | {ngay} | " + bo.get("lich_su", "Bản chuẩn hóa đầu tiên sau khi hoàn thành F0 → F8, kiểm thử hệ thống "
                                              "và hướng dẫn sử dụng (CR-46, CR-47) | Nguyễn Thanh Bình (A), Ngô Duy Đô (D)") + " |")
    return ("%%TRANG_BIA%%\n\n**THÔNG TIN TÀI LIỆU**\n\n" + t + "\n\n**LỊCH SỬ PHIÊN BẢN**\n\n" + lich_su
            + "\n\n%%NGAT_TRANG%%\n\n**MỤC LỤC**\n\n%%MUC_LUC%%\n\n")


def tieu_de_phan(md: str) -> str:
    m = re.search(r"^# (.+)$", md, re.M)
    return m.group(1).strip() if m else ""


def pandoc(md_text: str, out: Path, resource: list[Path]) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(md_text)
        src = f.name
    cmd = ["pandoc", src, "-f", "markdown+pipe_tables+strikeout+lists_without_preceding_blankline-yaml_metadata_block-pandoc_title_block-tex_math_dollars",
           # Không dùng Nhom_X_Bao_cao.docx làm --reference-doc: tệp đó khai báo font nhúng nhưng thiếu tệp font,
           # làm hỏng .docx sinh ra. Định dạng của mẫu (khổ giấy, lề, font, giãn dòng) được đặt lại ở dinh_dang().
           "-t", "docx", "-o", str(out), "--lua-filter", str(LUA),
           "--resource-path", os.pathsep.join(str(r) for r in resource)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    os.unlink(src)
    if r.returncode:
        raise RuntimeError(r.stderr)
    if r.stderr.strip():
        print("   pandoc:", r.stderr.strip()[:300])


# ---------------------------------------------------------------- định dạng .docx
def set_font(style, size: float | None = None, bold=None, italic=None, color=RGBColor(0, 0, 0), font=FONT):
    style.font.name = font
    rpr = style.element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.insert(0, rf)
    for k in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(k), font)
    for k in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
        if rf.get(qn(k)) is not None:
            del rf.attrib[qn(k)]
    if size:
        style.font.size = Pt(size)
    if bold is not None:
        style.font.bold = bold
    if italic is not None:
        style.font.italic = italic
    if color is not None:
        style.font.color.rgb = color
        c = rpr.find(qn("w:color"))
        for k in ("w:themeColor", "w:themeShade", "w:themeTint"):   # màu theme (xanh của pandoc) đè lên màu đặt tay
            if c is not None and c.get(qn(k)) is not None:
                del c.attrib[qn(k)]


def style(doc, name):
    """Tra style theo tên hiển thị hoặc mã style. Không dùng doc.styles[name]: pandoc đặt w:name "Heading 1"
    (viết hoa) còn python-docx tra theo "heading 1" nên không thấy."""
    key = name.replace(" ", "").lower()
    for s in doc.styles:
        if (s.name or "").replace(" ", "").lower() == key or (s.style_id or "").lower() == key:
            return s
    return None


def shade(cell, fill: str) -> None:
    tcpr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:color"), "auto")
    sh.set(qn("w:fill"), fill)
    tcpr.append(sh)


def borders(table) -> None:
    tblpr = table._tbl.tblPr
    old = tblpr.find(qn("w:tblBorders"))
    if old is not None:
        tblpr.remove(old)
    b = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), "4")
        e.set(qn("w:space"), "0")
        e.set(qn("w:color"), "808080")
        b.append(e)
    tblpr.append(b)


def xml_text(el) -> str:
    """Chữ trong 1 phần tử Word (đọc các w:t; itertext() của python-docx trả chữ bị lặp)."""
    return "".join(t.text or "" for t in el.iter(qn("w:t")))


def column_widths(table, total_cm: float, font_pt: float) -> list[float]:
    """Bề rộng cột: mỗi cột tối thiểu vừa từ dài nhất (mã UC16, GET, 02/11/2026… không bị vỡ chữ),
    phần còn lại chia theo lượng chữ của cột."""
    trs = table._tbl.findall(qn("w:tr"))
    ncol = max(len(tr.findall(qn("w:tc"))) for tr in trs)
    char_cm = 0.0185 * font_pt                       # bề rộng trung bình 1 ký tự Times New Roman
    longest = [0] * ncol
    total = [0] * ncol
    for tr in trs:
        for i, tc in enumerate(tr.findall(qn("w:tc"))[:ncol]):
            text = xml_text(tc)
            words = text.split()
            longest[i] = max(longest[i], min(16, max((len(w) for w in words), default=0)))
            total[i] += min(len(text), 300)
    mins = [max(1.2, n * char_cm + 0.4) for n in longest]
    if sum(mins) >= total_cm:
        return [total_cm * m / sum(mins) for m in mins]
    extra = total_cm - sum(mins)
    w = [t ** 0.6 for t in total]
    sw = sum(w) or 1
    return [m + extra * x / sw for m, x in zip(mins, w)]


def format_table(table, text_width_cm: float) -> None:
    trs = table._tbl.findall(qn("w:tr"))
    ncol = max([len(table._tbl.tblGrid.findall(qn("w:gridCol")))] + [len(tr.findall(qn("w:tc"))) for tr in trs])
    grid = table._tbl.tblGrid
    while len(grid.findall(qn("w:gridCol"))) < ncol:     # pandoc bỏ lưới cột ở bảng chứa ảnh
        grid.append(OxmlElement("w:gridCol"))
    size = 12 if ncol <= 4 else 11 if ncol <= 6 else 9.5
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    borders(table)
    tblpr = table._tbl.tblPr
    lay = tblpr.find(qn("w:tblLayout"))
    if lay is None:
        lay = OxmlElement("w:tblLayout")
        tblpr.append(lay)
    lay.set(qn("w:type"), "fixed")
    ww = tblpr.find(qn("w:tblW"))
    if ww is None:
        ww = OxmlElement("w:tblW")
        tblpr.append(ww)
    ww.set(qn("w:type"), "dxa")
    ww.set(qn("w:w"), str(int(text_width_cm * 567)))
    if table._tbl.findall(".//" + qn("w:drawing")):     # bảng ảnh (VD 3 ảnh điện thoại cạnh nhau): chia đều
        widths = [text_width_cm / ncol] * ncol
    else:
        widths = column_widths(table, text_width_cm, size)
    grid = table._tbl.tblGrid
    for i, gc in enumerate(grid.findall(qn("w:gridCol"))):
        if i < len(widths):
            gc.set(qn("w:w"), str(int(widths[i] * 567)))
    for r, row in enumerate(table.rows):
        if r == 0:
            trpr = row._tr.get_or_add_trPr()
            h = OxmlElement("w:tblHeader")
            trpr.append(h)
        for i, cell in enumerate(row.cells[:ncol]):
            cell.width = Cm(widths[i])
            if r == 0:
                shade(cell, "D9E2F3")
            for p in cell.paragraphs:
                pf = p.paragraph_format
                pf.space_before = Pt(1)
                pf.space_after = Pt(1)
                pf.line_spacing = 1.0
                pf.first_line_indent = None
                if r == 0:
                    pf.keep_with_next = True          # hàng tiêu đề không nằm lẻ cuối trang
                if p.alignment not in (WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.CENTER):   # giữ cột số căn phải
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for run in p.runs:
                    run.font.size = Pt(size)
                    if r == 0:
                        run.font.bold = True


def toc_field(paragraph) -> None:
    paragraph.text = ""
    r = paragraph.add_run()
    b = OxmlElement("w:fldChar")
    b.set(qn("w:fldCharType"), "begin")
    t = OxmlElement("w:instrText")
    t.set(qn("xml:space"), "preserve")
    t.text = 'TOC \\o "1-2" \\h \\z \\u'
    s = OxmlElement("w:fldChar")
    s.set(qn("w:fldCharType"), "separate")
    txt = OxmlElement("w:t")
    txt.text = "Mục lục sẽ được cập nhật khi mở bằng Word (chuột phải → Update Field)."
    e = OxmlElement("w:fldChar")
    e.set(qn("w:fldCharType"), "end")
    for el in (b, t, s, txt, e):
        r._r.append(el)


def page_number_footer(section) -> None:
    f = section.footer
    f.is_linked_to_previous = False
    p = f.paragraphs[0] if f.paragraphs else f.add_paragraph()
    for r in list(p.runs):
        r._r.getparent().remove(r._r)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    for kind, text in (("begin", None), (None, "PAGE"), ("separate", None), (None, None), ("end", None)):
        if kind:
            fc = OxmlElement("w:fldChar")
            fc.set(qn("w:fldCharType"), kind)
            run._r.append(fc)
        elif text:
            it = OxmlElement("w:instrText")
            it.set(qn("xml:space"), "preserve")
            it.text = text
            run._r.append(it)
        else:
            t = OxmlElement("w:t")
            t.text = "1"
            run._r.append(t)
    run.font.name = FONT
    run.font.size = Pt(12)


def dinh_dang(path: Path, bia: bool) -> None:
    doc = Document(str(path))
    sec = doc.sections[0]
    sec.orientation = WD_ORIENT.PORTRAIT
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.top_margin = sec.bottom_margin = Cm(2)
    sec.left_margin, sec.right_margin = Cm(3), Cm(2)
    text_w = 21 - 3 - 2
    page_number_footer(sec)

    normal = doc.styles["Normal"]
    set_font(normal, 14)
    normal.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(4)
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for name in ("Body Text", "First Paragraph", "Compact"):
        st = style(doc, name)
        if st is not None:
            set_font(st, 14)
            st.paragraph_format.space_before = Pt(0)
            st.paragraph_format.space_after = Pt(4)
            st.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
            st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for name, size, b, i, before, after in (("Heading 1", 16, True, False, 0, 12), ("Heading 2", 14, True, False, 12, 6),
                                             ("Heading 3", 14, True, True, 10, 4), ("Heading 4", 14, False, True, 8, 4)):
        st = style(doc, name)
        if st is not None:
            set_font(st, size, bold=b, italic=i)
            pf = st.paragraph_format
            pf.space_before, pf.space_after = Pt(before), Pt(after)
            pf.keep_with_next = True
            pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
            pf.line_spacing = 1.15
            if name == "Heading 1":
                pf.page_break_before = True
                pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    st = style(doc, "Source Code")
    if st is not None:
        set_font(st, 9, font="Consolas")
    st = style(doc, "Verbatim Char")
    if st is not None:
        set_font(st, 12, font="Consolas")
    st = style(doc, "Source Code")
    if st is not None:
        st.paragraph_format.line_spacing = 1.0
        st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for name in ("Image Caption", "Table Caption", "Caption"):
        st = style(doc, name)
        if st is not None:
            set_font(st, 12, italic=True)
            st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            st.paragraph_format.space_after = Pt(10)
    for name in ("Captioned Figure", "Figure"):
        st = style(doc, name)
        if st is not None:
            st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            st.paragraph_format.keep_with_next = True
    st = style(doc, "Block Text")
    if st is not None:
        set_font(st, 13, italic=True)
    for name in ("Hyperlink",):
        st = style(doc, name)
        if st is not None:
            st.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
    for name in ("TOC Heading", "toc 1", "toc 2"):
        st = style(doc, name)
        if st is not None:
            set_font(st, 13)

    # khổ giấy các section (bảng rộng có thể nằm trong section khổ ngang – %%NGANG_...%%)
    for s in doc.sections[1:]:
        if s.orientation == WD_ORIENT.LANDSCAPE:
            s.page_width, s.page_height = Cm(29.7), Cm(21)
            s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = Cm(2)
        else:
            s.orientation = WD_ORIENT.PORTRAIT
            s.page_width, s.page_height = Cm(21), Cm(29.7)
            s.top_margin = s.bottom_margin = Cm(2)
            s.left_margin, s.right_margin = Cm(3), Cm(2)
    width_of = {}
    pending = []
    for el in doc.element.body.iterchildren():
        if el.tag == qn("w:tbl"):
            pending.append(el)
        elif el.tag == qn("w:p"):
            sp = el.find(qn("w:pPr") + "/" + qn("w:sectPr"))
            if sp is not None:
                sz = sp.find(qn("w:pgSz"))
                land = sz is not None and sz.get(qn("w:orient")) == "landscape"
                for tb in pending:
                    width_of[tb] = (29.7 - 4) if land else text_w
                pending = []
    for t in doc.tables:
        format_table(t, width_of.get(t._tbl, text_w))
    for el in doc.element.body.iter(qn("w:t")):         # "\|" trong bảng Markdown (thoát ký tự) → "|"
        if el.text and "\\|" in el.text:
            el.text = el.text.replace("\\|", "|")

    for p in doc.paragraphs:
        txt = p.text.strip()
        if txt == "%%MUC_LUC%%":
            toc_field(p)
        elif txt in ("THÔNG TIN TÀI LIỆU", "LỊCH SỬ PHIÊN BẢN", "MỤC LỤC") and p.runs and p.runs[0].bold:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.size = Pt(16)
        elif txt == "%%TRANG_BIA%%" and not bia:
            p._p.getparent().remove(p._p)
    # ảnh: không vượt bề rộng trang
    for shape in doc.inline_shapes:
        maxw = Cm(text_w)
        tc = shape._inline.getparent()
        while tc is not None and tc.tag != qn("w:tc"):
            tc = tc.getparent()
        if tc is not None:                    # ảnh trong ô bảng: vừa bề rộng 1 cột
            ncol = max(1, len(tc.getparent().findall(qn("w:tc"))))   # số ô của hàng chứa ảnh
            maxw = Cm(text_w / ncol - 0.4)
        if shape.width > maxw:
            ratio = maxw / shape.width
            shape.width = int(shape.width * ratio)
            shape.height = int(shape.height * ratio)
        maxh = Cm(13)                         # ảnh dọc (điện thoại) không chiếm trọn 1 trang
        if shape.height > maxh:
            ratio = maxh / shape.height
            shape.width = int(shape.width * ratio)
            shape.height = int(shape.height * ratio)
    doc.save(str(path))


# ---------------------------------------------------------------- trang bìa
def set_text(par, text: str) -> None:
    runs = par.runs
    if not runs:
        par.add_run(text)
        return
    runs[0].text = text
    for r in runs[1:]:
        r.text = ""


def tao_bia(tieu_de: str, out: Path, cfg: dict) -> None:
    doc = Document(str(MAU_BIA))
    pars = doc.paragraphs
    mon = None
    for p in pars:
        t = p.text.strip()
        if t.startswith("KHOA "):
            set_text(p, cfg["khoa"])
        elif t.startswith("BỘ MÔN"):
            if cfg.get("bo_mon", "").strip():
                set_text(p, cfg["bo_mon"])
            else:                                    # không ghi bộ môn → bỏ hẳn dòng này
                p._p.getparent().remove(p._p)
        elif t == "THỰC HÀNH TIN HỌC CƠ SỞ":
            set_text(p, cfg["mon_hoc"])
            mon = p
        elif t.startswith("Hà Nội"):
            set_text(p, cfg["noi_nam"])
    if mon is None:
        raise RuntimeError("Không thấy dòng tên môn học trong Mẫu bìa.docx")
    # thêm tên tài liệu + đề tài dưới tên môn học
    p_tl = copy.deepcopy(mon._p)
    mon._p.addnext(p_tl)
    p_dt = copy.deepcopy(mon._p)
    p_tl.addnext(p_dt)
    from docx.text.paragraph import Paragraph
    tl, dt = Paragraph(p_tl, mon._parent), Paragraph(p_dt, mon._parent)
    set_text(tl, tieu_de)
    for r in tl.runs:
        r.font.size = Pt(20)
    set_text(dt, "Đề tài: " + cfg["de_tai"])
    for r in dt.runs:
        r.font.size = Pt(14)
        r.font.bold = False
        r.font.italic = True
    for r in mon.runs:
        r.font.size = Pt(18)

    t = doc.tables[0]
    rows = t.rows
    labels = [("Giảng viên hướng dẫn", ": " + cfg["giang_vien"]), ("Nhóm", ": " + cfg["nhom"]),
              ("Lớp", ": " + cfg.get("lop", "")), ("Thành viên", ":")]
    for row, (a, b) in zip(rows[:4], labels):
        set_text(row.cells[0].paragraphs[0], a)
        set_text(row.cells[1].paragraphs[0], b)
    tmpl = rows[4]._tr
    dau = 4                                             # chỉ số dòng thành viên đầu tiên
    if not cfg.get("lop", "").strip():                  # môn quản lý theo nhóm → không ghi lớp
        tr_lop = rows[2]._tr
        tr_lop.getparent().remove(tr_lop)
        dau = 3
    members = cfg["thanh_vien"]
    prev = tmpl
    for k, m in enumerate(members):
        tr = tmpl if k == 0 else copy.deepcopy(tmpl)
        if k:
            prev.addnext(tr)
        prev = tr
    for k, m in enumerate(members):
        row = t.rows[dau + k]
        set_text(row.cells[0].paragraphs[0], "   " + m["ho_ten"])
        set_text(row.cells[1].paragraphs[0], ": " + m["ma_sv"])
        for c in row.cells:
            for r in c.paragraphs[0].runs:
                r.font.bold = False
    # Bìa được chèn vào tài liệu có giãn dòng 1,5 + căn đều: đặt cứng giãn dòng / căn lề để giữ đúng bố cục mẫu
    for p in doc.paragraphs:
        pf = p.paragraph_format
        if pf.line_spacing is None:
            pf.line_spacing = 1.15
        if pf.space_after is None:
            pf.space_after = Pt(0)
        if pf.space_before is None:
            pf.space_before = Pt(0)
        if p.alignment is None:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for row in t.rows:
        for c in row.cells:
            for p in c.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.line_spacing = 1.1
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.space_before = Pt(0)
    # bỏ các đoạn trống sau dòng "Hà Nội – năm" (dễ đẩy sang trang 2)
    last = next(p for p in doc.paragraphs if p.text.strip().startswith("Hà Nội"))
    nxt = last._p.getnext()
    while nxt is not None:
        after_n = nxt.getnext()
        if nxt.tag == qn("w:p") and not xml_text(nxt).strip() and not nxt.findall(".//" + qn("w:drawing")):
            nxt.getparent().remove(nxt)
        nxt = after_n
    # bớt dòng trống sau bảng để bìa vẫn vừa 1 trang
    body = doc.element.body
    after = t._tbl.getnext()
    removed = 0
    while after is not None and removed < len(members) - 1:
        nxt = after.getnext()
        if after.tag == qn("w:p") and not xml_text(after).strip() and not after.findall(".//" + qn("w:drawing")):
            body.remove(after)
            removed += 1
        after = nxt
    doc.save(str(out))


# ---------------------------------------------------------------- Word: ghép bìa, cập nhật mục lục, PDF
def word_hoan_thien(body: Path, bia: Path | None, out_docx: Path, out_pdf: Path | None) -> int:
    import win32com.client as win32
    word = win32.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        doc = word.Documents.Open(str(body))
        if bia is not None:
            rng = doc.Content
            f = rng.Find
            f.ClearFormatting()
            if f.Execute("%%TRANG_BIA%%"):
                rng.Text = ""
                rng.InsertBreak(2)                         # wdSectionBreakNextPage: bìa là section 1
                start = doc.Range(0, 0)
                start.InsertFile(str(bia))
                s1, s2 = doc.Sections(1), doc.Sections(2)
                s2.Footers(1).LinkToPrevious = False
                s1.Footers(1).Range.Text = ""
                s1.PageSetup.TopMargin = 85.05             # 3 cm – theo Mẫu bìa
                s1.PageSetup.BottomMargin = 70.9           # 2,5 cm
                s2.Footers(1).PageNumbers.RestartNumberingAtSection = True
                s2.Footers(1).PageNumbers.StartingNumber = 1
                # đoạn trống thừa trước ngắt section
                last = s1.Range.Paragraphs.Last
                if not last.Range.Text.strip() and s1.Range.Paragraphs.Count > 3:
                    pass
        for toc in doc.TablesOfContents:
            toc.Update()
        doc.Fields.Update()
        for toc in doc.TablesOfContents:
            toc.Update()
        doc.SaveAs2(str(out_docx), FileFormat=16)
        pages = doc.ComputeStatistics(2)
        if out_pdf is not None:
            doc.ExportAsFixedFormat(str(out_pdf), 17)
        doc.Close(False)
        return pages
    finally:
        word.Quit()


# ---------------------------------------------------------------- chạy
def xuat_bo(bo: dict, cfg: dict, tmp: Path, pdf_dir: Path | None) -> None:
    parts, names, res = [], [], {HERE}
    for src, opt in bo["phan"]:
        if src == "PHU_LUC_QUYET_DINH":
            md = phu_luc_quyet_dinh()
        elif src == "PHU_LUC_SCHEMA":
            md = phu_luc_schema()
        else:
            md = chuan_bi(src, opt)
            res.add(src.parent)
        parts.append(md)
        names.append(tieu_de_phan(md))
    text = trang_dau(bo, names) + "\n".join(parts)
    body = tmp / f"{bo['file']}_than.docx"
    pandoc(text, body, sorted(res))
    dinh_dang(body, bia=True)
    bia = tmp / f"bia_{bo['so']}.docx"
    tao_bia(bo["tieu_de"], bia, cfg)
    out = HERE / f"{bo['file']}.docx"
    pages = word_hoan_thien(body, bia, out, (pdf_dir / f"{bo['file']}.pdf") if pdf_dir else None)
    print(f"OK {out.name}: {pages} trang")


def xuat_bien_ban(p: Path, tmp: Path, pdf_dir: Path | None) -> None:
    md = chuan_bi(p, {})
    body = tmp / (p.stem + "_than.docx")
    pandoc(md, body, [p.parent])
    dinh_dang(body, bia=False)
    doc = Document(str(body))
    st = style(doc, "Heading 1")
    st.paragraph_format.page_break_before = False
    doc.save(str(body))
    out = HERE / (p.stem + ".docx")
    pages = word_hoan_thien(body, None, out, (pdf_dir / (p.stem + ".pdf")) if pdf_dir else None)
    print(f"OK {out.name}: {pages} trang")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chi", help="chỉ xuất các bộ số (VD 1,3; 0 = báo cáo tổng kết; 5 = biên bản họp)")
    ap.add_argument("--pdf", help="thư mục ghi thêm bản PDF để xem nhanh")
    a = ap.parse_args()
    chon = {int(x) for x in a.chi.split(",")} if a.chi else {0, 1, 2, 3, 4, 5}
    cfg = json.load(io.open(HERE / "thong_tin_bia.json", encoding="utf-8"))
    pdf_dir = Path(a.pdf).resolve() if a.pdf else None
    if pdf_dir:
        pdf_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        for bo in BO:
            if bo["so"] in chon:
                xuat_bo(bo, cfg, tmp, pdf_dir)
        if 5 in chon:
            for p in BIEN_BAN_HOP:
                xuat_bien_ban(p, tmp, pdf_dir)


if __name__ == "__main__":
    main()
