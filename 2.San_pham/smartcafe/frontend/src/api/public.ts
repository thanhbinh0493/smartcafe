import { request } from './client'

export interface TableInfo {
  branch: { id: number; code: string; name: string; address: string }
  table: { id: number; table_number: string }
}

export interface MenuItem {
  id: number
  name: string
  description: string | null
  image_url: string | null
  temperature_type: 'HOT' | 'COLD' | 'BOTH' | 'NONE'
  tags: string[]
  regular_price: number
  sell_price: number
  is_promo: boolean
  promotion_id: number | null
  is_new: boolean
  is_available: boolean
}

export interface MenuCategory {
  id: number
  name: string
  items: MenuItem[]
}

export interface Menu {
  branch_id: number
  categories: MenuCategory[]
}

export const getTable = (qrToken: string) => request<TableInfo>(`/api/public/tables/${encodeURIComponent(qrToken)}`)

export const getMenu = (branchId: number) => request<Menu>(`/api/public/branches/${branchId}/menu`)
