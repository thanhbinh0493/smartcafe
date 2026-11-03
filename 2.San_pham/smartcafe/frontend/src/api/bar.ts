import { request } from './client'
import type { ItemStatus, OrderStatus } from './orders'

export interface QueueItem {
  id: number
  order_id: number
  order_code: string
  table_number: string
  paid_at: string
  name: string
  quantity: number
  note: string | null
  order_note: string | null
  status: 'WAITING' | 'PREPARING'
  started_at: string | null
}

export interface Queue {
  branch_id: number
  server_time: string
  items: QueueItem[]
}

export interface BarOrder {
  id: number
  order_code: string
  table_number: string
  status: OrderStatus
  is_member: boolean
  total: number
  paid_at: string | null
  ready_at: string | null
  items: { id: number; name: string; quantity: number; note: string | null; status: ItemStatus }[]
}

export interface ItemActionResult {
  item_id: number
  item_status: ItemStatus
  order_id: number
  order_status: OrderStatus
}

export type ItemAction = 'start' | 'done' | 'undo'

export const getQueue = (branchId: number, token: string) =>
  request<Queue>(`/api/staff/branches/${branchId}/queue`, { token })

export const getReadyOrders = (branchId: number, token: string) =>
  request<BarOrder[]>(`/api/staff/branches/${branchId}/orders?status=READY`, { token })

export const itemAction = (itemId: number, action: ItemAction, token: string) =>
  request<ItemActionResult>(`/api/staff/order-items/${itemId}/${action}`, { method: 'POST', token })

export const completeOrder = (orderId: number, token: string) =>
  request<{ order_id: number; status: OrderStatus; completed_at: string; points_earned: number | null }>(
    `/api/staff/orders/${orderId}/complete`,
    { method: 'POST', token },
  )
