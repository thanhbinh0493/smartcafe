/** API quản trị (F6 – UC09–UC15, IV.3 Mục 2.2). */
import type { StaffRole } from './auth'
import { ApiError, request } from './client'

const json = (method: string, body: unknown, token: string) => ({ method, body: JSON.stringify(body), token })

// ---------- Danh mục (A05) ----------
export interface Category {
  id: number
  name: string
  sort_order: number
  is_active: boolean
  item_count: number
}
export type CategoryIn = Pick<Category, 'name' | 'sort_order' | 'is_active'>

export const listCategories = (token: string) => request<Category[]>('/api/staff/categories', { token })
export const saveCategory = (token: string, body: CategoryIn, id?: number) =>
  id
    ? request<Category>(`/api/staff/categories/${id}`, json('PUT', body, token))
    : request<Category>('/api/staff/categories', json('POST', body, token))
export const deleteCategory = (token: string, id: number) =>
  request<null>(`/api/staff/categories/${id}`, { method: 'DELETE', token })

// ---------- Món – menu chung (W05) ----------
export type TempType = 'HOT' | 'COLD' | 'BOTH' | 'NONE'
export interface AdminMenuItem {
  id: number
  category_id: number
  category_name: string
  name: string
  description: string | null
  base_price: number
  image_url: string | null
  temperature_type: TempType
  tags: string[]
  is_active: boolean
  created_at: string
}
export type MenuItemIn = Pick<
  AdminMenuItem,
  'category_id' | 'name' | 'description' | 'base_price' | 'temperature_type' | 'tags' | 'is_active'
>

export const listMenuItems = (token: string) => request<AdminMenuItem[]>('/api/staff/menu-items', { token })
export const saveMenuItem = (token: string, body: MenuItemIn, id?: number) =>
  id
    ? request<AdminMenuItem>(`/api/staff/menu-items/${id}`, json('PUT', body, token))
    : request<AdminMenuItem>('/api/staff/menu-items', json('POST', body, token))
export const deleteMenuItem = (token: string, id: number) =>
  request<null>(`/api/staff/menu-items/${id}`, { method: 'DELETE', token })

/** Upload ảnh: không đặt Content-Type để trình duyệt tự thêm boundary của multipart. */
export async function uploadMenuImage(token: string, id: number, file: File): Promise<AdminMenuItem> {
  const form = new FormData()
  form.append('file', file)
  let res: Response
  try {
    res = await fetch(`/api/staff/menu-items/${id}/image`, {
      method: 'POST',
      body: form,
      headers: { Authorization: `Bearer ${token}` },
    })
  } catch {
    throw new ApiError(0, 'NETWORK_ERROR', 'Không kết nối được máy chủ, vui lòng thử lại')
  }
  const body = await res.json().catch(() => null)
  if (!res.ok) {
    const e = body?.error
    throw new ApiError(res.status, e?.code ?? 'HTTP_ERROR', e?.message ?? 'Upload ảnh thất bại', e?.details ?? {})
  }
  return body as AdminMenuItem
}

// ---------- Chi nhánh (A03) ----------
export interface AdminBranch {
  id: number
  code: string
  name: string
  address: string
  phone: string | null
  latitude: number | null
  longitude: number | null
  is_active: boolean
  table_count: number
  staff_count: number
}
export type BranchIn = Omit<AdminBranch, 'id' | 'table_count' | 'staff_count'>

export const listBranches = (token: string) => request<AdminBranch[]>('/api/staff/branches', { token })
export const saveBranch = (token: string, body: BranchIn, id?: number) =>
  id
    ? request<AdminBranch>(`/api/staff/branches/${id}`, json('PUT', body, token))
    : request<AdminBranch>('/api/staff/branches', json('POST', body, token))

// ---------- Nhân viên (A04) ----------
export interface StaffAccount {
  id: number
  username: string
  full_name: string
  role: StaffRole
  branch_id: number | null
  branch_name: string | null
  phone: string | null
  is_active: boolean
  created_at: string
}
export interface StaffIn {
  username?: string
  full_name: string
  phone: string | null
  role: StaffRole
  branch_id: number | null
  is_active: boolean
  password?: string | null
}

export const listStaff = (token: string) => request<StaffAccount[]>('/api/staff/staff', { token })
export const saveStaff = (token: string, body: StaffIn, id?: number) =>
  id
    ? request<StaffAccount>(`/api/staff/staff/${id}`, json('PUT', body, token))
    : request<StaffAccount>('/api/staff/staff', json('POST', body, token))

// ---------- Menu chi nhánh (W06) ----------
export interface BranchMenuRow {
  menu_item_id: number
  name: string
  category_id: number
  category_name: string
  base_price: number
  price_override: number | null
  is_available: boolean
  updated_at: string | null
}

export const getBranchMenu = (token: string, branchId: number) =>
  request<BranchMenuRow[]>(`/api/staff/branches/${branchId}/menu`, { token })
export const patchBranchMenu = (
  token: string,
  branchId: number,
  itemId: number,
  body: { price_override: number | null; is_available: boolean },
) => request<BranchMenuRow>(`/api/staff/branches/${branchId}/menu/${itemId}`, json('PATCH', body, token))

// ---------- Bàn & QR (A06) ----------
export interface DiningTable {
  id: number
  branch_id: number
  table_number: string
  qr_token: string
  qr_url: string
  is_active: boolean
}
export type TableIn = Pick<DiningTable, 'table_number' | 'is_active'>

export const listTables = (token: string, branchId: number) =>
  request<DiningTable[]>(`/api/staff/branches/${branchId}/tables`, { token })
export const saveTable = (token: string, branchId: number, body: TableIn, id?: number) =>
  id
    ? request<DiningTable>(`/api/staff/branches/${branchId}/tables/${id}`, json('PUT', body, token))
    : request<DiningTable>(`/api/staff/branches/${branchId}/tables`, json('POST', body, token))

/** Ảnh QR (PNG) cần JWT nên không dùng thẳng <img src>; tải về dạng Blob. */
export async function fetchQrPng(token: string, tableId: number): Promise<Blob> {
  const res = await fetch(`/api/staff/tables/${tableId}/qr.png`, { headers: { Authorization: `Bearer ${token}` } })
  if (!res.ok) {
    const e = (await res.json().catch(() => null))?.error
    throw new ApiError(res.status, e?.code ?? 'HTTP_ERROR', e?.message ?? 'Không tải được ảnh QR')
  }
  return res.blob()
}

// ---------- Khuyến mãi (W07) ----------
export type PromoStatus = 'running' | 'upcoming' | 'ended'
export interface PromotionItem {
  menu_item_id: number
  name: string
  current_price: number
  promo_price: number
  discount_percent: number
}
export interface Promotion {
  id: number
  name: string
  description: string | null
  branch_id: number | null
  branch_name: string | null
  start_at: string
  end_at: string
  is_active: boolean
  status: PromoStatus
  created_by: string
  items: PromotionItem[]
}
export interface PromotionIn {
  name: string
  description: string | null
  branch_id: number | null
  start_at: string
  end_at: string
  is_active: boolean
  items: { menu_item_id: number; promo_price: number }[]
}

export const listPromotions = (token: string, status: PromoStatus) =>
  request<Promotion[]>(`/api/staff/promotions?status=${status}`, { token })
export const savePromotion = (token: string, body: PromotionIn, id?: number) =>
  id
    ? request<Promotion>(`/api/staff/promotions/${id}`, json('PUT', body, token))
    : request<Promotion>('/api/staff/promotions', json('POST', body, token))
