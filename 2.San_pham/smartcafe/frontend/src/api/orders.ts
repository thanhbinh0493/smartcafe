import { request } from './client'

export type OrderStatus = 'PENDING_PAYMENT' | 'PAID' | 'PREPARING' | 'READY' | 'COMPLETED' | 'CANCELLED'
export type ItemStatus = 'WAITING' | 'PREPARING' | 'DONE' | 'CANCELLED'
export type PaymentMethod = 'MOCK_EWALLET' | 'MOCK_CARD'

export interface OrderLine {
  id: number
  menu_item_id: number
  name: string
  quantity: number
  original_price: number
  unit_price: number
  is_promo: boolean
  note: string | null
  status: ItemStatus
}

export interface CreateOrderInput {
  qr_token: string
  items: { menu_item_id: number; quantity: number; note?: string; is_recommended?: boolean }[]
  expected_total: number
}

export interface CreatedOrder {
  order_id: number
  order_code: string
  access_token: string
  status: OrderStatus
  subtotal: number
  discount: number
  total: number
  expected_points: number | null
  items: OrderLine[]
}

export interface OrderView {
  id: number
  order_code: string
  status: OrderStatus
  branch_name: string
  table_number: string
  subtotal: number
  discount: number
  total: number
  queue_position: number | null
  paid_at: string | null
  ready_at: string | null
  completed_at: string | null
  cancelled_at: string | null
  cancel_reason: string | null
  points_earned?: number | null // chỉ có khi đơn hoàn tất và là khách thành viên
  items: OrderLine[]
}

/** details của lỗi PRICE_CHANGED */
export interface PriceChange {
  menu_item_id: number
  regular_price: number
  sell_price: number
  is_promo: boolean
}

export const createOrder = (body: CreateOrderInput) =>
  request<CreatedOrder>('/api/public/orders', { method: 'POST', body: JSON.stringify(body) })

export const payOrder = (orderId: number, accessToken: string, method: PaymentMethod) =>
  request<{ order_id: number; status: OrderStatus; paid_at: string; transaction_ref: string }>(
    `/api/public/orders/${orderId}/pay`,
    { method: 'POST', body: JSON.stringify({ access_token: accessToken, method }) },
  )

export const getOrder = (orderId: number, token: string) =>
  request<OrderView>(`/api/public/orders/${orderId}?token=${encodeURIComponent(token)}`)
