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
