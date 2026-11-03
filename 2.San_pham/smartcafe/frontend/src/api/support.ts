import { request } from './client'
import type { ItemStatus, OrderStatus } from './orders'

export interface SupportOrder {
  id: number
  order_code: string
  order_date: string
  table_number: string
  status: OrderStatus
  total: number
  is_member: boolean
  note: string | null
  created_at: string
  paid_at: string | null
  cancelled_at: string | null
  cancel_reason: string | null
  cancelled_by: string | null
  can_cancel: boolean
  payment: {
    method: 'MOCK_EWALLET' | 'MOCK_CARD'
    amount: number
    status: 'SUCCESS' | 'FAILED' | 'REFUNDED'
    transaction_ref: string
    refunded_at: string | null
  } | null
  items: { id: number; name: string; quantity: number; unit_price: number; note: string | null; status: ItemStatus }[]
}

export const searchOrders = (token: string, code = '', table = '') => {
  const q = new URLSearchParams()
  if (code.trim()) q.set('code', code.trim())
  if (table.trim()) q.set('table', table.trim())
  const qs = q.toString()
  return request<SupportOrder[]>(`/api/staff/orders/search${qs ? `?${qs}` : ''}`, { token })
}

export const cancelOrder = (orderId: number, reason: string, token: string) =>
  request<SupportOrder>(`/api/staff/orders/${orderId}/cancel`, {
    method: 'POST',
    token,
    body: JSON.stringify({ reason }),
  })
