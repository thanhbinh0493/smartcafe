/** NFR-U4: tiền hiển thị dạng 45.000đ */
export function formatVND(amount: number): string {
  return `${Math.round(amount).toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.')}đ`
}

/** Bỏ dấu tiếng Việt + chữ thường, để tìm "ca phe" ra "Cà phê". */
export function normalizeText(s: string): string {
  return s
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/đ/g, 'd')
    .replace(/Đ/g, 'D')
    .toLowerCase()
    .trim()
}

const TIME_FMT = new Intl.DateTimeFormat('vi-VN', {
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
  timeZone: 'Asia/Ho_Chi_Minh',
})

const DAY_PARTS = new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: '2-digit', timeZone: 'Asia/Ho_Chi_Minh' })
// Tự ghép "dd/MM" vì mỗi bản ICU định dạng vi-VN khác nhau ("02/11" hoặc "02-11")
const DAY_FMT = {
  format: (d: Date) => {
    const p = Object.fromEntries(DAY_PARTS.formatToParts(d).map((x) => [x.type, x.value]))
    return `${p.day}/${p.month}`
  },
}

/** Giờ:phút theo giờ Việt Nam, VD "08:15" (giờ gọi món trên màn hình Bar).
 *  Nếu khác ngày với `today` thì kèm ngày, VD "02/11 08:15": mã đơn đếm lại mỗi ngày (D28) nên đơn hôm trước
 *  còn tồn có thể trùng mã với đơn hôm nay (BUG-F3-02). */
export function formatTime(iso: string, today?: string): string {
  const d = new Date(iso)
  const time = TIME_FMT.format(d)
  if (today && DAY_FMT.format(d) !== DAY_FMT.format(new Date(today))) return `${DAY_FMT.format(d)} ${time}`
  return time
}
