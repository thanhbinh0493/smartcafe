/** API dashboard bán hàng (F8 – UC16, W08). */
import { request } from './client'

export interface Kpi {
  revenue: number
  order_count: number
  cancelled_count: number
  avg_order_value: number
  avg_wait_seconds: number | null
  member_order_ratio: number
  promo_revenue: number
  recommended_item_ratio: number
}

export interface Dashboard {
  from_date: string
  to_date: string
  branch_id: number | null
  branches: { branch_id: number; code: string; name: string; kpi: Kpi }[]
  latest_date: string | null
  latest: Kpi | null
  previous: Kpi | null
  period: Kpi
  series: { report_date: string; branch_id: number; revenue: number; order_count: number }[]
  top_items: { menu_item_id: number; name: string; qty: number }[]
  generated_at: string | null
}

export function getDashboard(token: string, opts: { branchId: number | null; from: string; to: string }) {
  const q = new URLSearchParams({ from: opts.from, to: opts.to })
  if (opts.branchId) q.set('branch_id', String(opts.branchId))
  return request<Dashboard>(`/api/staff/reports/daily?${q}`, { token })
}

export const rebuildReport = (token: string, date: string) =>
  request<{ report_date: string; branches: number }>('/api/staff/reports/daily/rebuild', {
    method: 'POST', body: JSON.stringify({ date }), token,
  })
