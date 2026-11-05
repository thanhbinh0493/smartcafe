// Tạo slide thuyết trình bảo vệ – SmartCafe, Nhóm 8 (giai đoạn X).
//   cd 3.Slide/tao_slide && npm install && node tao_slide.js
// Thứ tự phần theo mẫu môn học 3.Slide/Nhom_X_Slide.pptx (16:9). Số liệu lấy từ 1.Bao_cao/Bao_cao_tong_ket.md.
// Họ tên thành viên đọc từ 1.Bao_cao/Xuat_docx/thong_tin_bia.json (điền một lần, chạy lại là cập nhật).
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");
const { applyTheme } = require("./apply_theme.js");

const ROOT = path.resolve(__dirname, "..", "..");
const IMG = path.join(ROOT, "1.Bao_cao", "Huong_dan_su_dung", "img");
const DIA = path.join(ROOT, "1.Bao_cao", "Thiet_ke_he_thong", "diagrams", "png");
const OUT = path.join(ROOT, "3.Slide", "Nhom_8_Slide.pptx");
const TMP = path.join(__dirname, "tmp");
const cfg = JSON.parse(fs.readFileSync(path.join(ROOT, "1.Bao_cao", "Xuat_docx", "thong_tin_bia.json"), "utf8"));

const THEME = {
  name: "SmartCafe Espresso",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "2B1D16", lt1: "FFFFFF", dk2: "4A3226", lt2: "F4EEE9",
    accent1: "6F4E37", accent2: "EA580C", accent3: "15803D", accent4: "B08968",
    accent5: "8A6A55", accent6: "1D4ED8", hlink: "1D4ED8", folHlink: "6F4E37",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in – cùng khổ với mẫu môn học
pres.title = "SmartCafe – Nhóm 8 – Bảo vệ bài tập lớn";
pres.author = "Nhóm 8";
pres.company = "Học viện Công nghệ Bưu chính Viễn thông";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;

// ---------------------------------------------------------------- layout
pres.defineSlideMaster({
  title: "TIEU_DE",
  background: { color: HEX.dk2 },
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: 0.6, y: 1.05, w: 5.2, h: 0.4, fontSize: 12, bold: true, color: C.accent4, charSpacing: 2, margin: 0 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.5, w: 5.4, h: 1.2, fontSize: 48, bold: true, color: C.background1, margin: 0, valign: "top", align: "left" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 2.75, w: 5.2, h: 1.0, fontSize: 18, color: C.background2, margin: 0, valign: "top", align: "left" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "NOI_DUNG",
  background: { color: HEX.lt1 },
  margin: [0.5, 0.5, 0.45, 0.5],
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: 0.5, y: 0.22, w: 7, h: 0.28, fontSize: 10, bold: true, color: C.accent2, charSpacing: 1.5, margin: 0 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.48, w: 9, h: 0.55, fontSize: 24, bold: true, color: C.text2, margin: 0, valign: "middle", align: "left" }, text: "" } },
    { text: { text: "SmartCafe · Nhóm 8", options: { x: 0.5, y: 5.25, w: 4, h: 0.25, fontSize: 9, color: C.accent5, margin: 0 } } },
  ],
  slideNumber: { x: 9.0, y: 5.25, w: 0.5, h: 0.25, fontSize: 9, color: C.accent5, align: "right" },
});

// ---------------------------------------------------------------- tiện ích
async function icon(name, hex, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(fa[name], { color: "#" + hex, size: String(size) }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}
async function crop(file, w, h, name) {
  fs.mkdirSync(TMP, { recursive: true });
  const out = path.join(TMP, name);
  await sharp(file).extract({ left: 0, top: 0, width: w, height: h }).toFile(out);
  return out;
}
function iconCircle(slide, data, x, y, d, fill, label) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill }, objectName: `vong ${label}` });
  const p = d * 0.26;
  slide.addImage({ data, x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p, altText: label });
}
function card(slide, x, y, w, h, name, fill = C.background2) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill }, line: { color: fill }, objectName: name });
}
function content(section, kicker, title) {
  const s = pres.addSlide({ masterName: "NOI_DUNG", sectionTitle: section });
  s.addText(kicker, { placeholder: "kicker" });
  s.addText(title, { placeholder: "title" });
  return s;
}
const T = (text, o) => ({ text, options: o || {} });

(async () => {
  const I = {};
  for (const [k, n, c] of [
    ["mug", "FaMugHot", HEX.lt1], ["qr", "FaQrcode", HEX.lt1], ["users", "FaUsers", HEX.lt1], ["robot", "FaRobot", HEX.lt1],
    ["clock", "FaClock", HEX.accent2], ["bug", "FaBug", HEX.accent2], ["tags", "FaTags", HEX.accent2],
    ["mobile", "FaMobileAlt", HEX.lt1], ["blender", "FaBlender", HEX.lt1], ["chart", "FaChartLine", HEX.lt1],
    ["check", "FaCheckCircle", HEX.accent3], ["file", "FaFileAlt", HEX.lt1], ["vial", "FaVial", HEX.lt1],
    ["book", "FaBook", HEX.lt1], ["cal", "FaCalendarAlt", HEX.lt1], ["comments", "FaComments", HEX.lt1],
    ["code", "FaCode", HEX.lt1], ["slides", "FaChalkboardTeacher", HEX.lt1], ["db", "FaDatabase", HEX.lt1],
    ["shield", "FaShieldAlt", HEX.lt1], ["arrow", "FaArrowRight", HEX.accent5], ["github", "FaGithub", HEX.lt1],
    ["bolt", "FaBolt", HEX.lt1], ["coins", "FaCoins", HEX.lt1], ["flag", "FaFlagCheckered", HEX.lt1],
  ]) I[k] = await icon(n, c);

  const phone = async (f, n) => crop(path.join(IMG, f), 780, 1560, n);
  const K02 = await phone("K02_menu_goi_y.png", "k02.png");
  const K04 = await phone("K04_gio_hang.png", "k04.png");
  const K07 = await phone("K07_do_uong_san_sang.png", "k07.png");
  const K10 = await phone("K10_menu_thanh_vien.png", "k10.png");
  const N13 = await crop(path.join(IMG, "N13_tong_quan_quan_tri.png"), 1366, 900, "n13.png");

  // ============================================================ 1. Bìa
  pres.addSection({ title: "Mở đầu" });
  let s = pres.addSlide({ masterName: "TIEU_DE", sectionTitle: "Mở đầu" });
  s.addText("BÀI TẬP LỚN · QUẢN LÝ DỰ ÁN PHẦN MỀM", { placeholder: "kicker" });
  s.addText("SmartCafe", { placeholder: "title" });
  s.addText("Phần mềm quản lý chuỗi quán cà phê thông minh – tích hợp AI và QR", { placeholder: "body" });
  s.addText([T("Nhóm " + cfg.nhom, { bold: true, breakLine: true }), T("Giảng viên: " + cfg.giang_vien, { breakLine: true }), T(cfg.noi_nam)],
    { x: 0.6, y: 4.0, w: 5.2, h: 0.95, fontSize: 13, color: C.background2, margin: 0, isTextBox: true, objectName: "thong tin nhom" });
  s.addImage({ path: K02, x: 6.75, y: 0.55, w: 2.25, h: 4.5, altText: "Màn hình menu SmartCafe trên điện thoại" });
  s.addNotes("Giới thiệu đề tài SmartCafe của Nhóm 8: khách quét mã QR tại bàn để gọi món, quầy Bar làm theo hàng đợi, trụ sở quản lý tập trung, có AI gợi ý món. Bài trình bày đi theo các phần của mẫu báo cáo môn học.");

  // ============================================================ 2. Thành viên
  pres.addSection({ title: "Giới thiệu thành viên" });
  s = content("Giới thiệu thành viên", "01 · GIỚI THIỆU THÀNH VIÊN", "Nhóm 8 – 5 thành viên, 5 vai trò");
  const roles = [
    ["A", "PM / Team Lead", "Phân tích nghiệp vụ, kế hoạch, kiểm soát thay đổi", HEX.accent1],
    ["B", "Backend Developer", "API, cơ sở dữ liệu, hiệu năng", HEX.accent5],
    ["C", "AI Specialist", "Gợi ý món, OTP & tích điểm, dữ liệu mẫu", HEX.accent2],
    ["D", "Tester / QA", "Kiểm thử, biên bản, tài liệu, thư ký", HEX.accent3],
    ["E", "Frontend Developer", "QR Order, Web Admin, slide", HEX.accent6],
  ];
  roles.forEach(([k, role, task, col], i) => {
    const x = 0.5 + i * 1.82, y = 1.35;
    card(s, x, y, 1.66, 3.55, `the ${k}`);
    s.addShape(pres.shapes.OVAL, { x: x + 0.43, y: y + 0.3, w: 0.8, h: 0.8, fill: { color: col }, line: { color: col }, objectName: `vong ${k}` });
    s.addText(k, { x: x + 0.43, y: y + 0.3, w: 0.8, h: 0.8, fontSize: 28, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true, fontFace: THEME.headFontFace });
    const m = cfg.thanh_vien[i];
    s.addText([T(m.ho_ten, { bold: true, fontSize: 13, color: C.text1, breakLine: true }), T(role, { fontSize: 11, color: C.accent2, bold: true })],
      { x: x + 0.1, y: y + 1.25, w: 1.46, h: 0.85, align: "center", valign: "top", margin: 0, isTextBox: true });
    s.addText(task, { x: x + 0.12, y: y + 2.15, w: 1.42, h: 1.2, fontSize: 11, color: C.text2, align: "center", valign: "top", margin: 0, isTextBox: true });
  });
  s.addNotes("Mỗi thành viên phụ trách một vai trò; mọi tài liệu và luồng code đều có người review chéo. Toàn bộ buổi họp trong biên bản đều đủ 5 thành viên.");

  // ============================================================ 3. Phân công
  pres.addSection({ title: "Phân công công việc" });
  s = content("Phân công công việc", "02 · PHÂN CÔNG CÔNG VIỆC CÁC THÀNH VIÊN", "Ai làm gì – và ai review");
  const hdr = (t) => T(t, { bold: true, color: HEX.lt1, fill: { color: HEX.accent1 } });
  const rowsPC = [
    ["A", "Phạm vi, WBS, kế hoạch; Use Case + Sequence; chủ trì họp, chốt 44 quyết định / 49 CR; báo cáo tổng kết", "Duyệt mọi biên bản kiểm thử"],
    ["B", "CSDL 18 bảng, kiến trúc & 50 API; backend 9 luồng F0 → F8; tối ưu hiệu năng (cache)", "Review II.2, Use Case"],
    ["C", "Nghiên cứu công nghệ; AI gợi ý 2 chế độ + FP-Growth; OTP, tích điểm; dữ liệu 5.000 đơn", "Review NFR & data model"],
    ["D", "Khảo sát, NFR; 10 biên bản kiểm thử + kiểm thử hệ thống; Hướng dẫn sử dụng; biên bản họp", "Review thiết kế giao diện"],
    ["E", "Wireframe W00–W08; giao diện QR Order + Web Admin 8 luồng; slide, demo", "Review chung"],
  ];
  s.addTable([[hdr("TV"), hdr("Công việc chính"), hdr("Review")], ...rowsPC.map((r) => [T(r[0], { bold: true, align: "center" }), T(r[1]), T(r[2])])],
    { x: 0.5, y: 1.3, w: 9, colW: [0.55, 6.25, 2.2], fontSize: 12, color: HEX.dk1, border: { type: "solid", pt: 0.5, color: "D6C7BC" },
      fill: { color: HEX.lt1 }, valign: "middle", rowH: 0.62, margin: [3, 6, 3, 6] });
  s.addNotes("Bảng phân công chi tiết (người làm, người review, ngày bắt đầu – kết thúc – review) nằm trong file Nhom_8_Phan_cong.xlsx và Project_Plan.");

  // ============================================================ 4–5. Tổng quan
  pres.addSection({ title: "Tổng quan chung dự án" });
  s = content("Tổng quan chung dự án", "03 · TỔNG QUAN CHUNG DỰ ÁN", "Bài toán: bỏ khâu xếp hàng gọi món tại quầy");
  card(s, 0.5, 1.3, 4.1, 3.65, "cot hien trang");
  card(s, 5.4, 1.3, 4.1, 3.65, "cot smartcafe", "EFE6DF");
  s.addText("Hiện trạng (chuỗi 3 chi nhánh)", { x: 0.75, y: 1.45, w: 3.7, h: 0.4, fontSize: 15, bold: true, color: C.text2, margin: 0, isTextBox: true });
  s.addText("Với SmartCafe", { x: 5.65, y: 1.45, w: 3.7, h: 0.4, fontSize: 15, bold: true, color: C.text2, margin: 0, isTextBox: true });
  const pains = [[I.clock, "Giờ cao điểm xếp hàng dài ở quầy thu ngân"], [I.bug, "Ghi sai món, sai ghi chú khi nhận order miệng"], [I.tags, "Khuyến mãi, giá nhập tay từng chi nhánh – trụ sở khó kiểm soát"]];
  pains.forEach(([ic, t], i) => {
    s.addImage({ data: ic, x: 0.8, y: 2.05 + i * 0.95, w: 0.38, h: 0.38, altText: "biểu tượng" });
    s.addText(t, { x: 1.35, y: 1.95 + i * 0.95, w: 3.1, h: 0.6, fontSize: 13, color: C.text1, valign: "middle", margin: 0, isTextBox: true });
  });
  const gains = [[I.qr, HEX.accent1, "Quét QR tại bàn: xem menu, đặt và trả trước trên điện thoại"], [I.blender, HEX.accent2, "Bar làm theo hàng đợi realtime, khách xem trạng thái đơn"], [I.robot, HEX.accent3, "Trụ sở quản lý menu / giá / KM tập trung; AI gợi ý món; báo cáo hằng ngày"]];
  gains.forEach(([ic, col, t], i) => {
    iconCircle(s, ic, 5.65, 1.98 + i * 0.95, 0.5, col, "giải pháp");
    s.addText(t, { x: 6.3, y: 1.95 + i * 0.95, w: 3.05, h: 0.6, fontSize: 13, color: C.text1, valign: "middle", margin: 0, isTextBox: true });
  });
  s.addImage({ data: I.arrow, x: 4.8, y: 2.95, w: 0.4, h: 0.4, altText: "mũi tên" });
  s.addNotes("Khảo sát theo mô hình giả định điển hình của một chuỗi 3 chi nhánh. Ba điểm nghẽn chính dẫn tới ba nhóm tính năng của SmartCafe.");

  s = content("Tổng quan chung dự án", "03 · TỔNG QUAN CHUNG DỰ ÁN", "Phạm vi và quy mô sản phẩm");
  const stats = [["20", "use case"], ["5", "vai trò người dùng"], ["18", "bảng CSDL"], ["50", "API + WebSocket"], ["9", "luồng code F0 → F8"]];
  stats.forEach(([n, l], i) => {
    const x = 0.5 + i * 1.82;
    s.addText(n, { x, y: 1.25, w: 1.66, h: 0.8, fontSize: 44, bold: true, color: C.accent1, align: "center", margin: 0, isTextBox: true, fontFace: THEME.headFontFace });
    s.addText(l, { x, y: 2.02, w: 1.66, h: 0.35, fontSize: 12, color: C.accent5, align: "center", margin: 0, isTextBox: true });
  });
  card(s, 0.5, 2.6, 5.4, 2.35, "trong pham vi");
  card(s, 6.1, 2.6, 3.4, 2.35, "ngoai pham vi", "F3F3F3");
  s.addText("Trong phạm vi", { x: 0.7, y: 2.7, w: 5, h: 0.35, fontSize: 14, bold: true, color: C.accent3, margin: 0, isTextBox: true });
  s.addText([
    T("Gọi món qua QR: ẩn danh hoặc thành viên (OTP giả lập), tích điểm", { bullet: true, breakLine: true }),
    T("Thanh toán trả trước giả lập, theo dõi đơn realtime", { bullet: true, breakLine: true }),
    T("Màn hình Bar, thu ngân hủy đơn & hoàn tiền", { bullet: true, breakLine: true }),
    T("Quản trị menu, giá chi nhánh, khuyến mãi, bàn & QR, nhân viên", { bullet: true, breakLine: true }),
    T("AI gợi ý món + \"thường gọi kèm\"; báo cáo ngày + dashboard", { bullet: true }),
  ], { x: 0.7, y: 3.07, w: 5.05, h: 1.8, fontSize: 12, color: C.text1, margin: 0, paraSpaceAfter: 3, isTextBox: true, valign: "top" });
  s.addText("Ngoài phạm vi", { x: 6.3, y: 2.7, w: 3, h: 0.35, fontSize: 14, bold: true, color: C.accent5, margin: 0, isTextBox: true });
  s.addText([
    T("IoT / máy pha kết nối (D8)", { bullet: true, breakLine: true }),
    T("POS tại quầy, giao hàng", { bullet: true, breakLine: true }),
    T("Cổng thanh toán, SMS thật", { bullet: true, breakLine: true }),
    T("Đổi điểm, voucher, kho", { bullet: true, breakLine: true }),
    T("Bản demo trên cloud (D40)", { bullet: true }),
  ], { x: 6.3, y: 3.07, w: 3.05, h: 1.8, fontSize: 12, color: C.text1, margin: 0, paraSpaceAfter: 3, isTextBox: true, valign: "top" });
  s.addNotes("Dữ liệu demo: 3 chi nhánh × 20 bàn, 35 món, khoảng 5.000 đơn lịch sử để AI và dashboard có số liệu.");

  // ============================================================ 6–7. Kế hoạch
  pres.addSection({ title: "Kế hoạch triển khai dự án" });
  s = content("Kế hoạch triển khai dự án", "04 · KẾ HOẠCH TRIỂN KHAI DỰ ÁN", "11 giai đoạn trong 8 tuần: 21/09 → 16/11/2026");
  const phases = [
    ["I", "Kế hoạch", "21–24/09", 1], ["II", "Khảo sát", "25/09–01/10", 1], ["III", "Phân tích", "02–09/10", 1],
    ["IV", "Thiết kế", "10–19/10", 1], ["V", "Lập trình F0–F8", "20–31/10", 1], ["VI", "Kiểm thử HT", "01–03/11", 1],
    ["VII", "HDSD", "03–05/11", 1], ["VIII", "Chuẩn hóa TL", "04–09/11", 1], ["IX", "Báo cáo", "10–12/11", 1],
    ["X", "Slide, demo", "12–15/11", 2], ["XI", "Nghiệm thu", "16/11", 3],
  ];
  s.addShape(pres.shapes.LINE, { x: 0.75, y: 3.05, w: 8.5, h: 0, line: { color: "CDBBAE", width: 2 }, objectName: "truc thoi gian" });
  phases.forEach(([code, name, d, st], i) => {
    const x = 0.75 + i * 0.85;
    const col = st === 1 ? HEX.accent3 : st === 2 ? HEX.accent2 : "A8A29E";
    s.addShape(pres.shapes.OVAL, { x: x - 0.17, y: 2.88, w: 0.34, h: 0.34, fill: { color: col }, line: { color: HEX.lt1, width: 1.5 }, objectName: `moc ${code}` });
    const up = i % 2 === 0;
    s.addText([T(code, { bold: true, color: col, fontSize: 12, breakLine: true }), T(name, { bold: true, fontSize: 11, color: HEX.dk1, breakLine: true }), T(d, { fontSize: 10, color: HEX.accent5 })],
      { x: x - 0.6, y: up ? 1.75 : 3.32, w: 1.2, h: 1.0, align: "center", valign: up ? "bottom" : "top", margin: 0, isTextBox: true });
  });
  s.addText([T("● ", { color: HEX.accent3 }), T("Hoàn thành   "), T("● ", { color: HEX.accent2 }), T("Đang làm   "), T("● ", { color: "A8A29E" }), T("Kế hoạch")],
    { x: 0.5, y: 4.6, w: 5, h: 0.3, fontSize: 11, color: C.text2, margin: 0, isTextBox: true });
  s.addText("Mốc: M1 thiết kế 19/10 · M2 9 luồng đạt 31/10 · M3 kiểm thử HT 03/11 · M4 hồ sơ 09/11 · M5 nghiệm thu 16/11",
    { x: 0.5, y: 4.88, w: 9, h: 0.3, fontSize: 11, color: C.accent5, margin: 0, isTextBox: true, italic: true });
  s.addNotes("Kế hoạch dàn đều 8 tuần (D41). Giai đoạn V–VII thực tế xong sớm (02–03/11) nhờ làm theo luồng có test tự động.");

  s = content("Kế hoạch triển khai dự án", "04 · KẾ HOẠCH TRIỂN KHAI DỰ ÁN", "Kiểm soát thay đổi: mọi quyết định đều có biên bản");
  [["49", "yêu cầu thay đổi (CR)"], ["44", "quyết định đã chốt (D)"], ["0", "vấn đề mở còn tồn (P1–P25)"]].forEach(([n, l], i) => {
    const x = 0.5 + i * 3.05;
    card(s, x, 1.3, 2.85, 1.35, `so lieu ${i}`);
    s.addText(n, { x, y: 1.36, w: 2.85, h: 0.75, fontSize: 40, bold: true, color: i === 2 ? C.accent3 : C.accent1, align: "center", margin: 0, isTextBox: true, fontFace: THEME.headFontFace });
    s.addText(l, { x, y: 2.1, w: 2.85, h: 0.4, fontSize: 12, color: C.text2, align: "center", margin: 0, isTextBox: true });
  });
  const flow = ["Yêu cầu / đề xuất", "Ghi CR vào biên bản tuần", "Vấn đề mở P… (1 nơi)", "Chốt → quyết định D…", "Cập nhật tài liệu + mã + test"];
  flow.forEach((t, i) => {
    const x = 0.5 + i * 1.82;
    s.addText(t, { shape: pres.shapes.CHEVRON, x, y: 3.15, w: 1.8, h: 0.95, fill: { color: i % 2 ? HEX.accent5 : HEX.accent1 }, line: { color: HEX.lt1 },
      fontSize: 10.5, bold: true, color: C.background1, align: "center", valign: "middle", margin: [2, 10, 2, 24], objectName: `buoc ${i + 1}` });
  });
  s.addText("Thay đổi lớn: bỏ IoT, thêm khuyến mãi / OTP / tích điểm (01/11); kết thúc dự án dời về 16/11 (CR-45)",
    { x: 0.5, y: 4.4, w: 9, h: 0.5, fontSize: 12, color: C.text2, margin: 0, isTextBox: true, italic: true });
  s.addNotes("Quy tắc CR-08: mọi thay đổi ghi ngay vào biên bản tuần. Bảng vấn đề mở là nơi theo dõi duy nhất; khi chốt chuyển thành quyết định và cập nhật mọi tài liệu liên quan.");

  // ============================================================ 8. Chi phí
  pres.addSection({ title: "Quản lý chi phí dự án" });
  s = content("Quản lý chi phí dự án", "05 · QUẢN LÝ CHI PHÍ DỰ ÁN", "Dự toán 63,03 triệu đồng – chi phí tiền mặt 0đ");
  s.addChart(pres.charts.BAR, [{ name: "Chi phí (triệu đồng)", labels: ["A – PM", "B – Backend", "C – AI", "D – Tester", "E – Frontend"], values: [12.6, 14.25, 7.2, 9.3, 13.95] }], {
    x: 0.4, y: 1.2, w: 5.4, h: 3.85, barDir: "bar", chartColors: [HEX.accent1], showValue: true, dataLabelPosition: "outEnd",
    dataLabelFormatCode: "0.00", dataLabelFontSize: 11, valAxisMaxVal: 17, valAxisMinVal: 0, dataLabelColor: HEX.dk1, dataLabelFontFace: "+mn-lt",
    catAxisLabelFontSize: 12, catAxisLabelColor: HEX.dk1, catAxisLabelFontFace: "+mn-lt", valAxisHidden: true,
    valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: false,
    showTitle: true, title: "Chi phí nhân công theo thành viên (triệu đồng)", titleFontSize: 12, titleColor: HEX.dk2, titleFontFace: "+mn-lt", catAxisOrientation: "maxMin",
  });
  card(s, 6.1, 1.25, 3.4, 3.75, "gia dinh chi phi");
  s.addText([
    T("90,25 ngày công", { bold: true, fontSize: 18, color: HEX.accent1, breakLine: true }),
    T("bán thời gian 4 giờ/ngày, theo bảng phân công + review + họp", { fontSize: 11, color: HEX.accent5, breakLine: true }),
    T(" ", { fontSize: 6, breakLine: true }),
    T("Đơn giá giả định", { bold: true, fontSize: 13, breakLine: true }),
    T("PM 800.000đ · thành viên khác 600.000đ / ngày công", { fontSize: 12, breakLine: true }),
    T(" ", { fontSize: 6, breakLine: true }),
    T("Nhân công 57,30 tr + dự phòng 10% 5,73 tr", { fontSize: 12, breakLine: true }),
    T("Hạ tầng 0đ: laptop, mã nguồn mở, không cloud, dịch vụ ngoài giả lập", { fontSize: 12 }),
  ], { x: 6.3, y: 1.4, w: 3.05, h: 3.5, color: HEX.dk1, margin: 0, valign: "top", isTextBox: true });
  s.addNotes("Dự án không phát sinh chi phí thật; nhóm lập dự toán theo công lao động × đơn giá giả định (D44). Giai đoạn lập trình chiếm gần 49% công trực tiếp.");

  // ============================================================ 9. Nhân lực
  pres.addSection({ title: "Quản lý nguồn nhân lực" });
  s = content("Quản lý nguồn nhân lực", "06 · QUẢN LÝ NGUỒN NHÂN LỰC", "Ma trận trách nhiệm RACI");
  const raci = [
    ["Phạm vi, kế hoạch", "R/A", "C", "C", "C", "C"], ["Use case, sequence", "R/A", "C", "I", "C", "I"],
    ["Thiết kế CSDL, API", "A", "R", "C", "I", "C"], ["Thiết kế giao diện", "A", "C", "I", "C", "R"],
    ["Backend F0 → F8", "A", "R", "R", "C", "I"], ["Frontend F1 → F8", "A", "C", "I", "C", "R"],
    ["AI gợi ý món", "A", "C", "R", "C", "C"], ["Kiểm thử, biên bản", "A", "C", "C", "R", "C"],
    ["Hướng dẫn sử dụng", "A", "I", "I", "R", "C"], ["Báo cáo tổng kết", "R/A", "C", "C", "C", "C"], ["Slide, demo", "A", "C", "C", "C", "R"],
  ];
  const cell = (v) => T(v, { align: "center", bold: v.includes("R"), color: v.includes("R") ? HEX.lt1 : HEX.dk1, fill: { color: v.includes("R") ? HEX.accent1 : v === "A" ? "EFE6DF" : HEX.lt1 } });
  s.addTable([[hdr("Hạng mục"), hdr("A"), hdr("B"), hdr("C"), hdr("D"), hdr("E")], ...raci.map((r) => [T(r[0]), ...r.slice(1).map(cell)])],
    { x: 0.5, y: 1.2, w: 6.3, colW: [2.3, 0.8, 0.8, 0.8, 0.8, 0.8], fontSize: 11, color: HEX.dk1, rowH: 0.31, border: { type: "solid", pt: 0.5, color: "D6C7BC" }, valign: "middle", margin: [1, 5, 1, 5] });
  s.addText([
    T("R", { bold: true, color: HEX.accent1 }), T(" thực hiện", { breakLine: true }),
    T("A", { bold: true, color: HEX.accent1 }), T(" chịu trách nhiệm phê duyệt", { breakLine: true }),
    T("C", { bold: true, color: HEX.accent1 }), T(" tham vấn", { breakLine: true }),
    T("I", { bold: true, color: HEX.accent1 }), T(" được thông báo", { breakLine: true }),
    T(" ", { fontSize: 8, breakLine: true }),
    T("Mỗi hạng mục có 1 người thực hiện và người review khác vai trò; PM duyệt mọi cổng chất lượng.", { italic: true, color: HEX.accent5 }),
  ], { x: 7.1, y: 1.3, w: 2.4, h: 3.3, fontSize: 12, color: HEX.dk1, margin: 0, valign: "top", isTextBox: true });
  s.addNotes("C (AI) cùng làm backend ở F4 và F7. D là tester kiêm thư ký và phụ trách tài liệu.");

  // ============================================================ 10–16. Triển khai
  const SEC = "Quá trình triển khai thực thi dự án";
  const K7 = "07 · QUÁ TRÌNH TRIỂN KHAI THỰC THI DỰ ÁN";
  pres.addSection({ title: SEC });
  s = content(SEC, K7, "Phân tích và thiết kế hệ thống");
  s.addImage({ path: path.join(DIA, "IV_kien_truc.png"), x: 0.5, y: 1.25, w: 5.6, h: 5.6 * 787 / 1501, altText: "Sơ đồ kiến trúc hệ thống SmartCafe" });
  s.addText("Hình: kiến trúc hệ thống (IV.3)", { x: 0.5, y: 4.3, w: 5.6, h: 0.3, fontSize: 10, color: C.accent5, italic: true, margin: 0, isTextBox: true });
  s.addText([
    T("Phân tích", { bold: true, color: HEX.accent1, breakLine: true }),
    T("20 use case · 6 sequence · biểu đồ trạng thái đơn · 29 yêu cầu phi chức năng", { breakLine: true }),
    T(" ", { fontSize: 6, breakLine: true }),
    T("Thiết kế", { bold: true, color: HEX.accent1, breakLine: true }),
    T("PostgreSQL 18 bảng · 9 wireframe · 50 API + 3 kênh WebSocket", { breakLine: true }),
    T(" ", { fontSize: 6, breakLine: true }),
    T("Công nghệ", { bold: true, color: HEX.accent1, breakLine: true }),
    T("FastAPI · React + TypeScript · PostgreSQL · WebSocket · Docker Compose; sơ đồ PlantUML", {}),
  ], { x: 6.4, y: 1.3, w: 3.1, h: 3.7, fontSize: 12, color: HEX.dk1, margin: 0, valign: "top", isTextBox: true });
  s.addNotes("Backend là một ứng dụng FastAPI chia module theo nghiệp vụ; WebSocket hub trong bộ nhớ; toàn hệ thống chạy bằng một lệnh docker compose up.");

  s = content(SEC, K7, "Lập trình theo 9 luồng nghiệp vụ");
  s.addChart(pres.charts.BAR, [{ name: "Ca kiểm thử", labels: ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8"], values: [48, 57, 67, 76, 84, 53, 230, 71, 41] }], {
    x: 0.4, y: 1.15, w: 5.9, h: 3.9, barDir: "col", chartColors: [HEX.accent1], showValue: true, dataLabelPosition: "outEnd",
    dataLabelFontSize: 11, dataLabelColor: HEX.dk1, dataLabelFontFace: "+mn-lt", catAxisLabelFontSize: 12, catAxisLabelColor: HEX.dk1,
    catAxisLabelFontFace: "+mn-lt", valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: false,
    showTitle: true, title: "Số ca kiểm thử tự động đạt theo luồng (tổng 727)", titleFontSize: 12, titleColor: HEX.dk2, titleFontFace: "+mn-lt",
  });
  card(s, 6.55, 1.25, 2.95, 3.75, "quy trinh luong");
  s.addText([
    T("Mỗi luồng", { bold: true, fontSize: 14, color: HEX.accent1, breakLine: true }),
    T("API + giao diện", { bullet: { code: "2460" }, breakLine: true }),
    T("Test tự động: pytest trên PostgreSQL thật, Vitest", { bullet: { code: "2461" }, breakLine: true }),
    T("Kiểm thử khói + đầu-cuối trên trình duyệt", { bullet: { code: "2462" }, breakLine: true }),
    T("Biên bản kiểm thử → PM duyệt → gộp main", { bullet: { code: "2463" }, breakLine: true }),
    T(" ", { fontSize: 6, breakLine: true }),
    T("17 lỗi phát hiện, sửa hết, đều có test hồi quy", { bold: true, color: HEX.accent3 }),
  ], { x: 6.7, y: 1.4, w: 2.7, h: 3.5, fontSize: 12, color: HEX.dk1, margin: 0, valign: "top", paraSpaceAfter: 4, isTextBox: true });
  s.addNotes("F0 nền tảng, F1 QR & menu, F2 đặt món & thanh toán, F3 màn hình Bar, F4 OTP & tích điểm, F5 thu ngân, F6 quản trị (nhiều chức năng nhất – 230 ca), F7 AI gợi ý, F8 báo cáo. Độ bao phủ mã: backend 99%, frontend 98,5%.");

  s = content(SEC, K7, "Sản phẩm: gọi món ngay trên điện thoại");
  [[K02, "1. Menu + gợi ý AI"], [K04, "2. Giỏ hàng, thanh toán"], [K07, "3. Đồ uống sẵn sàng"]].forEach(([f, cap], i) => {
    const x = 0.55 + i * 1.95;
    s.addImage({ path: f, x, y: 1.2, w: 1.75, h: 3.5, altText: cap });
    s.addText(cap, { x: x - 0.1, y: 4.75, w: 1.95, h: 0.3, fontSize: 11, bold: true, color: C.text2, align: "center", margin: 0, isTextBox: true });
  });
  card(s, 6.55, 1.25, 2.95, 3.75, "diem noi bat");
  s.addText([
    T("5 lần chạm", { bold: true, fontSize: 22, color: HEX.accent2, breakLine: true }),
    T("để đặt 1 đơn 2 món (yêu cầu ≤ 6)", { fontSize: 11, color: HEX.accent5, breakLine: true }),
    T(" ", { fontSize: 8, breakLine: true }),
    T("0,05 giây", { bold: true, fontSize: 22, color: HEX.accent2, breakLine: true }),
    T("đơn vừa trả tiền hiện trên màn hình Bar", { fontSize: 11, color: HEX.accent5, breakLine: true }),
    T(" ", { fontSize: 8, breakLine: true }),
    T("0,8 giây", { bold: true, fontSize: 22, color: HEX.accent2, breakLine: true }),
    T("trang chào hiện ra trên mạng 4G", { fontSize: 11, color: HEX.accent5 }),
  ], { x: 6.75, y: 1.4, w: 2.6, h: 3.5, color: HEX.dk1, margin: 0, valign: "top", isTextBox: true });
  s.addNotes("Demo trực tiếp: quét QR, xem menu có gợi ý, thêm món, thanh toán giả lập; màn hình Bar nhận đơn ngay; bấm Xong thì điện thoại báo sẵn sàng.");

  s = content(SEC, K7, "Web Admin: màn hình Bar và dashboard bán hàng");
  s.addImage({ path: path.join(IMG, "N02_bar_hang_doi.png"), x: 0.5, y: 1.25, w: 4.4, h: 4.4 * 900 / 1366, altText: "Màn hình Bar" });
  s.addImage({ path: N13, x: 5.1, y: 1.25, w: 4.4, h: 4.4 * 900 / 1366, altText: "Dashboard bán hàng" });
  s.addText([T("Màn hình Bar", { bold: true, breakLine: true }), T("Hàng đợi theo giờ gọi, Bắt đầu / Xong / Hoàn tác / Đã giao, âm báo, món chờ > 10 phút tô đỏ", {})],
    { x: 0.5, y: 4.2, w: 4.4, h: 0.9, fontSize: 12, color: C.text1, margin: 0, valign: "top", isTextBox: true });
  s.addText([T("Dashboard", { bold: true, breakLine: true }), T("Tự tổng hợp 00:05 hằng ngày: doanh thu, số đơn, thời gian chờ, tỉ lệ món từ gợi ý AI", {})],
    { x: 5.1, y: 4.2, w: 4.4, h: 0.9, fontSize: 12, color: C.text1, margin: 0, valign: "top", isTextBox: true });
  s.addNotes("Quản trị viên quản lý chi nhánh, danh mục, món, khuyến mãi, nhân viên; quản lý chi nhánh đặt giá riêng, bật tắt còn hàng, in mã QR bàn.");

  s = content(SEC, K7, "AI gợi ý món: 2 chế độ, luôn giải thích lý do");
  s.addChart(pres.charts.BAR, [{ name: "Hit Rate@5", labels: ["Chỉ món bán chạy", "Công thức ẩn danh", "Công thức thành viên"], values: [0.204, 0.198, 0.489] }], {
    x: 0.4, y: 1.15, w: 5.2, h: 3.9, barDir: "col", chartColors: ["B8A89C", "B8A89C", HEX.accent2], showValue: true, dataLabelPosition: "outEnd",
    dataLabelFormatCode: "0.0%", dataLabelFontSize: 12, dataLabelColor: HEX.dk1, dataLabelFontFace: "+mn-lt", catAxisLabelFontSize: 11,
    catAxisLabelColor: HEX.dk1, catAxisLabelFontFace: "+mn-lt", valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
    valAxisMaxVal: 0.6, valAxisMinVal: 0, showLegend: false, showTitle: true, title: "Hit Rate@5 – đánh giá offline", titleFontSize: 12, titleColor: HEX.dk2, titleFontFace: "+mn-lt",
  });
  s.addImage({ path: K10, x: 5.85, y: 1.2, w: 1.6, h: 3.2, altText: "Menu thành viên với gợi ý Bạn hay gọi" });
  s.addText([
    T("Ẩn danh", { bold: true, color: HEX.accent1, breakLine: true }),
    T("bán chạy, khuyến mãi, món mới, thời tiết", { breakLine: true }),
    T(" ", { fontSize: 6, breakLine: true }),
    T("Thành viên", { bold: true, color: HEX.accent1, breakLine: true }),
    T("\"Bạn hay gọi\", món tương tự, + các yếu tố trên", { breakLine: true }),
    T(" ", { fontSize: 6, breakLine: true }),
    T("Thường gọi kèm", { bold: true, color: HEX.accent1, breakLine: true }),
    T("FP-Growth học lại mỗi đêm 00:30", {}),
  ], { x: 7.6, y: 1.25, w: 1.9, h: 3.6, fontSize: 11, color: HEX.dk1, margin: 0, valign: "top", isTextBox: true });
  s.addText("Gợi ý lỗi không làm hỏng việc đặt món (NFR-R1); API gợi ý p95 90 ms", { x: 5.85, y: 4.6, w: 3.65, h: 0.45, fontSize: 11, italic: true, color: C.accent5, margin: 0, isTextBox: true });
  s.addNotes("Dữ liệu huấn luyện là 5.000 đơn mô phỏng có quy luật cài sẵn. Công thức thành viên đạt 48,9% so với 20,4% của cách chỉ gợi ý món bán chạy.");

  s = content(SEC, K7, "Kiểm thử hệ thống: đạt toàn bộ trên bản chạy thật");
  [["66/66", "ca kiểm thử hệ thống"], ["664", "ca hồi quy F0 → F8 đạt"], ["29/29", "yêu cầu phi chức năng"], ["6", "lỗi tìm ra, đã sửa"]].forEach(([n, l], i) => {
    const x = 0.5 + i * 2.3;
    card(s, x, 1.25, 2.1, 1.3, `kiem thu ${i}`);
    s.addText(n, { x, y: 1.3, w: 2.1, h: 0.7, fontSize: 32, bold: true, color: i === 3 ? C.accent2 : C.accent3, align: "center", margin: 0, isTextBox: true, fontFace: THEME.headFontFace });
    s.addText(l, { x, y: 2.0, w: 2.1, h: 0.4, fontSize: 11, color: C.text2, align: "center", margin: 0, isTextBox: true });
  });
  const groups = [[I.users, "Kịch bản \"một ngày làm việc\" trên 5 trình duyệt cùng lúc"], [I.bolt, "Hiệu năng: 50 khách đồng thời, p95 63 ms"], [I.shield, "Bảo mật: giả mạo JWT, phân quyền, SQL injection, XSS"], [I.mobile, "Mất mạng, AI lỗi, Safari/WebKit, sao lưu – khôi phục"]];
  groups.forEach(([ic, t], i) => {
    const x = 0.5 + (i % 2) * 4.6, y = 2.85 + Math.floor(i / 2) * 1.0;
    iconCircle(s, ic, x, y, 0.55, HEX.accent1, "nhóm kiểm thử");
    s.addText(t, { x: x + 0.7, y, w: 3.75, h: 0.55, fontSize: 12, color: C.text1, valign: "middle", margin: 0, isTextBox: true });
  });
  s.addText("Lỗi đáng chú ý: hiệu năng chưa đạt khi 50 khách → cache API đọc (D38); Bar không tự cập nhật khi mất WebSocket → tải lại mỗi 10 giây",
    { x: 0.5, y: 4.75, w: 9, h: 0.4, fontSize: 11, italic: true, color: C.accent5, margin: 0, isTextBox: true });
  s.addNotes("Kiểm thử hệ thống phát hiện 6 lỗi mà kiểm thử từng luồng không thấy, mỗi lỗi có test hồi quy. Toàn bộ 793 ca (727 + 66) đạt.");

  s = content(SEC, K7, "Giám sát và quản lý rủi ro");
  card(s, 0.5, 1.25, 3.5, 3.8, "cong chat luong");
  s.addText("Cổng chất lượng mỗi luồng", { x: 0.7, y: 1.35, w: 3.2, h: 0.35, fontSize: 14, bold: true, color: C.accent1, margin: 0, isTextBox: true });
  ["Test tự động 100% đạt", "Biên bản kiểm thử (D lập)", "PM duyệt, ghi CR", "Gộp vào nhánh main", "Hồi quy toàn bộ luồng trước"].forEach((t, i) => {
    s.addImage({ data: I.check, x: 0.75, y: 1.88 + i * 0.6, w: 0.3, h: 0.3, altText: "đạt" });
    s.addText(t, { x: 1.2, y: 1.83 + i * 0.6, w: 2.7, h: 0.4, fontSize: 12, color: C.text1, valign: "middle", margin: 0, isTextBox: true });
  });
  const risks = [
    ["IoT không khả thi", "Cao", "Bỏ IoT, đổi tên đề tài (D8)"],
    ["AI không có dữ liệu thật", "Cao", "Sinh 5.000 đơn có quy luật, đánh giá offline"],
    ["Hiệu năng 50 khách", "TB", "Cache API đọc, chốt mô hình tải (D38–D39)"],
    ["Laptop tắt lúc 00:05", "Cao", "Tự tính bù báo cáo khi khởi động (D36)"],
    ["Hỏng laptop ngày demo", "Thấp", "GitHub + sao lưu CSDL, chạy máy khác ~1 phút"],
  ];
  s.addTable([[hdr("Rủi ro đã gặp"), hdr("Mức"), hdr("Xử lý")], ...risks.map((r) => [T(r[0], { bold: true }), T(r[1], { align: "center" }), T(r[2])])],
    { x: 4.25, y: 1.25, w: 5.25, colW: [1.7, 0.6, 2.95], fontSize: 11, color: HEX.dk1, rowH: 0.6, border: { type: "solid", pt: 0.5, color: "D6C7BC" }, valign: "middle", margin: [2, 5, 2, 5] });
  s.addNotes("Nhật ký thực hiện dựa trên biên bản họp và lịch sử commit. Mọi rủi ro đã gặp đều đã xử lý; rủi ro bất khả kháng có phương án dự phòng.");

  // ============================================================ 17–18. Kết quả
  pres.addSection({ title: "Kết quả đạt được" });
  s = content("Kết quả đạt được", "08 · KẾT QUẢ ĐẠT ĐƯỢC", "Đạt mọi mục tiêu đã đặt ra");
  const kpis = [
    [I.flag, "20/20", "use case chạy được cho 5 vai trò"], [I.vial, "793", "ca kiểm thử đạt, 23 lỗi đã sửa"],
    [I.shield, "29/29", "yêu cầu phi chức năng"], [I.robot, "48,9%", "Hit Rate@5 gợi ý thành viên"],
    [I.coins, "0đ", "chi phí tiền mặt"], [I.cal, "8 tuần", "đúng kế hoạch, 0 vấn đề mở"],
  ];
  kpis.forEach(([ic, n, l], i) => {
    const x = 0.5 + (i % 3) * 3.05, y = 1.25 + Math.floor(i / 3) * 1.9;
    card(s, x, y, 2.85, 1.7, `ket qua ${i}`);
    iconCircle(s, ic, x + 0.2, y + 0.25, 0.6, i % 2 ? HEX.accent2 : HEX.accent1, "kết quả");
    s.addText(n, { x: x + 0.95, y: y + 0.18, w: 1.8, h: 0.75, fontSize: 28, bold: true, color: C.text2, valign: "middle", margin: 0, isTextBox: true, fontFace: THEME.headFontFace });
    s.addText(l, { x: x + 0.2, y: y + 1.0, w: 2.5, h: 0.55, fontSize: 12, color: C.text1, valign: "top", margin: 0, isTextBox: true });
  });
  s.addNotes("Tóm tắt kết quả so với mục tiêu ở Phần X báo cáo tổng kết.");

  s = content("Kết quả đạt được", "08 · KẾT QUẢ ĐẠT ĐƯỢC", "Bài học kinh nghiệm và hướng phát triển");
  card(s, 0.5, 1.25, 4.35, 3.8, "bai hoc");
  card(s, 5.15, 1.25, 4.35, 3.8, "huong phat trien", "EFE6DF");
  s.addText("Bài học", { x: 0.7, y: 1.35, w: 4, h: 0.4, fontSize: 15, bold: true, color: C.accent1, margin: 0, isTextBox: true });
  s.addText([
    T("Chia việc theo luồng nghiệp vụ → tích hợp sớm, luôn có bản chạy được", { bullet: true, breakLine: true }),
    T("Ghi CR ngay khi thay đổi → tài liệu, mã, kế hoạch không lệch nhau", { bullet: true, breakLine: true }),
    T("Kiểm thử trên bản chạy thật tìm ra lỗi test từng luồng bỏ sót", { bullet: true, breakLine: true }),
    T("Yêu cầu hiệu năng phải đi kèm mô hình tải cụ thể", { bullet: true }),
  ], { x: 0.7, y: 1.8, w: 4, h: 3.1, fontSize: 13, color: C.text1, margin: 0, paraSpaceAfter: 6, valign: "top", isTextBox: true });
  s.addText("Hướng phát triển", { x: 5.35, y: 1.35, w: 4, h: 0.4, fontSize: 15, bold: true, color: C.accent1, margin: 0, isTextBox: true });
  s.addText([
    T("Đổi điểm, voucher / combo, quản lý kho", { bullet: true, breakLine: true }),
    T("Cổng thanh toán và SMS thật (đã có interface)", { bullet: true, breakLine: true }),
    T("Nhiều tiến trình backend + Redis / LISTEN-NOTIFY", { bullet: true, breakLine: true }),
    T("Collaborative filtering khi có dữ liệu thật; IoT cho chuỗi lớn", { bullet: true, breakLine: true }),
    T("Triển khai cloud có HTTPS", { bullet: true }),
  ], { x: 5.35, y: 1.8, w: 4, h: 3.1, fontSize: 13, color: C.text1, margin: 0, paraSpaceAfter: 6, valign: "top", isTextBox: true });
  s.addNotes("Bài học rút ra từ cách làm theo luồng và kiểm soát thay đổi bằng biên bản; hướng phát triển ghi ở Phần X báo cáo.");

  // ============================================================ 19. Sản phẩm nộp
  pres.addSection({ title: "Sản phẩm nộp" });
  s = content("Sản phẩm nộp", "09 · SẢN PHẨM NỘP", "Bộ sản phẩm nộp");
  const prods = [
    [I.file, "Báo cáo tổng kết", "10 phần theo mẫu môn học"], [I.db, "Phân tích & thiết kế", "II.1 → IV.3, schema.sql"],
    [I.vial, "Hồ sơ kiểm thử", "11 biên bản, kế hoạch"], [I.book, "Hướng dẫn sử dụng", "5 vai trò, 33 ảnh"],
    [I.cal, "Phạm vi & kế hoạch", "Bảng phân công Excel"], [I.comments, "Biên bản họp", "49 yêu cầu thay đổi"],
    [I.github, "Mã nguồn", "GitHub, chạy bằng Docker"], [I.slides, "Slide + demo", "Bản trình bày này"],
  ];
  prods.forEach(([ic, n, l], i) => {
    const x = 0.5 + (i % 4) * 2.3, y = 1.3 + Math.floor(i / 4) * 1.85;
    card(s, x, y, 2.1, 1.65, `san pham ${i}`);
    iconCircle(s, ic, x + 0.75, y + 0.15, 0.6, i % 2 ? HEX.accent5 : HEX.accent1, n);
    s.addText([T(n, { bold: true, fontSize: 13, color: HEX.dk1, breakLine: true }), T(l, { fontSize: 11, color: HEX.accent5 })],
      { x: x + 0.1, y: y + 0.82, w: 1.9, h: 0.75, align: "center", valign: "top", margin: 0, isTextBox: true });
  });
  s.addNotes("Toàn bộ tài liệu Word sinh tự động từ một nguồn Markdown trong kho, theo định dạng mẫu báo cáo môn học.");

  // ============================================================ 20. Cảm ơn
  pres.addSection({ title: "Kết thúc" });
  s = pres.addSlide({ masterName: "TIEU_DE", sectionTitle: "Kết thúc" });
  s.addText("DEMO & HỎI ĐÁP", { placeholder: "kicker" });
  s.addText("Cảm ơn thầy cô và các bạn đã lắng nghe", { x: 0.6, y: 1.5, w: 5.6, h: 1.6, fontSize: 34, bold: true, color: C.background1,
    fontFace: THEME.headFontFace, valign: "top", margin: 0, isTextBox: true });
  s.addText("SmartCafe · Nhóm 8", { x: 0.6, y: 3.3, w: 5.2, h: 0.5, fontSize: 18, color: C.background2, margin: 0, isTextBox: true });
  iconCircle(s, I.mug, 7.0, 1.6, 2.0, HEX.accent1, "cốc cà phê");
  s.addNotes("Chuyển sang demo trực tiếp trên laptop theo kịch bản trong Hướng dẫn sử dụng mục 9.2, sau đó trả lời câu hỏi.");

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("OK", OUT);
})().catch((e) => { console.error(e); process.exit(1); });
