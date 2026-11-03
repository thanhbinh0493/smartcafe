/** API gợi ý món (F7 – UC03, SD02). */
import { request } from './client'
import type { MenuItem } from './public'

export interface RecItem {
  menu_item_id: number
  name: string
  image_url: string | null
  regular_price: number
  sell_price: number
  is_promo: boolean
  is_new: boolean
  score: number
  reason_code: string
  reason: string
}

export interface Recommendations {
  log_id: number | null
  mode: 'ANONYMOUS' | 'MEMBER'
  member_fallback: boolean
  temp_c: number | null
  weather_source: string | null
  degraded: boolean
  items: RecItem[]
  also_bought: RecItem[]
}

export const getRecommendations = (branchId: number, cart: number[] = [], customerToken?: string | null) =>
  request<Recommendations>(
    `/api/public/branches/${branchId}/recommendations${cart.length ? `?cart=${cart.join(',')}` : ''}`,
    { token: customerToken },
  )

/** Đổi món gợi ý thành dạng món menu để thêm vào giỏ. */
export const recToMenuItem = (r: RecItem): MenuItem => ({
  id: r.menu_item_id, name: r.name, description: null, image_url: r.image_url, temperature_type: 'NONE', tags: [],
  regular_price: r.regular_price, sell_price: r.sell_price, is_promo: r.is_promo, promotion_id: null,
  is_new: r.is_new, is_available: true,
})

/** Lần gợi ý gần nhất khách đã xem (gửi kèm khi đặt đơn – D34). Chỉ giữ trong sessionStorage của tab. */
const key = (qrToken: string) => `smartcafe.reclog.${qrToken}`

export function rememberLog(qrToken: string, logId: number | null): void {
  try {
    if (logId) sessionStorage.setItem(key(qrToken), String(logId))
  } catch {
    /* storage bị chặn: bỏ qua, chỉ mất số liệu đánh giá */
  }
}

export function lastLog(qrToken: string): number | undefined {
  try {
    const v = Number(sessionStorage.getItem(key(qrToken)))
    return Number.isInteger(v) && v > 0 ? v : undefined
  } catch {
    return undefined
  }
}
