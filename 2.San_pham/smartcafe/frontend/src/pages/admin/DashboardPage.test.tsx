import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { Dashboard, Kpi } from '../../api/report'
import { saveSession } from '../../auth/staffSession'
import { initialState, me } from '../../test/adminBackend'
import { errorBody, mockFetch, renderApp } from '../../test/utils'
import { chartData, delta, formatWait, trendClass, vnDate } from './DashboardPage'

const kpi = (k: Partial<Kpi>): Kpi => ({
  revenue: 0, order_count: 0, cancelled_count: 0, avg_order_value: 0, avg_wait_seconds: null,
  member_order_ratio: 0, promo_revenue: 0, recommended_item_ratio: 0, ...k,
})

const DASH: Dashboard = {
  from_date: '2026-10-27', to_date: '2026-11-02', branch_id: null, latest_date: '2026-11-02',
  latest: kpi({ revenue: 18450000, order_count: 412, cancelled_count: 3, avg_order_value: 44782, avg_wait_seconds: 380,
    member_order_ratio: 0.41, promo_revenue: 2100000, recommended_item_ratio: 0.18 }),
  previous: kpi({ revenue: 17373000, order_count: 398, avg_order_value: 43651, avg_wait_seconds: 420,
    member_order_ratio: 0.39, promo_revenue: 2100000, recommended_item_ratio: 0.17 }),
  period: kpi({ revenue: 120000000, order_count: 2800, cancelled_count: 20, promo_revenue: 9000000 }),
  branches: [
    { branch_id: 1, code: 'CG', name: 'SmartCafe Cầu Giấy', kpi: kpi({ revenue: 7120000, order_count: 158, cancelled_count: 2, avg_wait_seconds: 365 }) },
    { branch_id: 2, code: 'HD', name: 'SmartCafe Hà Đông', kpi: kpi({ revenue: 5980000, order_count: 136, cancelled_count: 1, avg_wait_seconds: 430 }) },
  ],
  series: [
    { report_date: '2026-11-02', branch_id: 1, revenue: 7120000, order_count: 158 },
    { report_date: '2026-11-01', branch_id: 1, revenue: 7000000, order_count: 150 },
    { report_date: '2026-11-01', branch_id: 2, revenue: 5000000, order_count: 120 },
  ],
  top_items: [{ menu_item_id: 11, name: 'Cà phê sữa đá', qty: 186 }, { menu_item_id: 21, name: 'Trà đào cam sả', qty: 121 }],
  generated_at: '2026-11-02T17:05:00Z',
}

class RO { observe() {} unobserve() {} disconnect() {} }

beforeEach(() => vi.stubGlobal('ResizeObserver', RO))

function dashBackend(role: 'ADMIN' | 'MANAGER', dash: Dashboard | null = DASH) {
  const st = initialState()
  saveSession('tok', me(role), 28800)
  const calls: string[] = []
  const posts: unknown[] = []
  const empty = { ...DASH, latest: null, previous: null, latest_date: null, branches: [], series: [], top_items: [] }
  mockFetch((url, init) => {
    if (url === '/api/auth/me') return { status: 200, body: me(role) }
    if (url === '/api/staff/branches') return { status: 200, body: role === 'ADMIN' ? st.branches : st.branches.slice(0, 1) }
    if (url.startsWith('/api/staff/reports/daily?')) {
      calls.push(url)
      return { status: 200, body: dash ?? empty }
    }
    if (url === '/api/staff/reports/daily/rebuild') {
      posts.push(JSON.parse(String(init?.body)))
      return { status: 200, body: { report_date: '2026-11-02', branches: 3 } }
    }
    return { status: 404, body: errorBody('NOT_FOUND', url) }
  })
  return { calls, posts }
}

describe('F8-FE-01..06 W08 – Dashboard bán hàng (UC16)', () => {
  it('F8-FE-01 thẻ chỉ số ngày gần nhất kèm thay đổi so với ngày trước', async () => {
    dashBackend('ADMIN')
    renderApp('/admin/dashboard')
    expect(await screen.findByText('Ngày 02/11 (so với ngày trước)')).toBeInTheDocument()
    const card = (l: string) => screen.getByTestId(`kpi-${l}`).textContent
    expect(card('Doanh thu')).toBe('Doanh thu18.450.000đ+6,2%')
    expect(card('Số đơn')).toBe('Số đơn412+3,5%')
    expect(card('Thời gian chờ TB')).toBe('Thời gian chờ TB6 phút 20s-0:40')
    expect(card('Đơn thành viên')).toBe('Đơn thành viên41,0%+2,0 điểm %')
    expect(card('Món từ gợi ý AI')).toBe('Món từ gợi ý AI18,0%+1,0 điểm %')
    expect(card('Đơn hủy')).toBe('Đơn hủy3')
    expect(screen.getByTestId('period')).toHaveTextContent('7 ngày (27/10 – 02/11): doanh thu 120.000.000đ, 2800 đơn, 20 đơn hủy')
    expect(screen.getByText(/Tự động tổng hợp lúc 00:05/)).toHaveTextContent('Cập nhật lần cuối')
  })

  it('F8-FE-02 bảng so sánh chi nhánh và top 5 món', async () => {
    dashBackend('ADMIN')
    renderApp('/admin/dashboard')
    const cmp = within(await screen.findByRole('table', { name: 'So sánh chi nhánh' }))
    expect(cmp.getAllByRole('row').map((r) => r.textContent)).toEqual([
      'Chi nhánhDoanh thuSố đơnHủyChờ TB',
      'SmartCafe Cầu Giấy7.120.000đ15826 phút 05s',
      'SmartCafe Hà Đông5.980.000đ13617 phút 10s',
    ])
    const top = within(screen.getByRole('table', { name: 'Top 5 món' }))
    expect(top.getAllByRole('row').slice(1).map((r) => r.textContent)).toEqual(['1Cà phê sữa đá186', '2Trà đào cam sả121'])
    expect(screen.getByTestId('revenue-chart')).toBeInTheDocument()
  })

  it('F8-FE-03 quản trị viên đổi chi nhánh, đổi 30 ngày: gọi API đúng tham số (đến hôm qua)', async () => {
    const { calls } = dashBackend('ADMIN')
    renderApp('/admin/dashboard')
    await screen.findByText('Ngày 02/11 (so với ngày trước)')
    expect(calls[0]).toBe(`/api/staff/reports/daily?from=${vnDate(7)}&to=${vnDate(1)}`)
    await waitFor(() => expect(within(screen.getByLabelText('Chi nhánh')).getAllByRole('option')).toHaveLength(3))
    await userEvent.selectOptions(screen.getByLabelText('Chi nhánh'), '2')
    await userEvent.selectOptions(screen.getByLabelText('Khoảng thời gian'), '30')
    await waitFor(() => expect(calls.at(-1)).toBe(`/api/staff/reports/daily?from=${vnDate(30)}&to=${vnDate(1)}&branch_id=2`))
  })

  it('F8-FE-04 quản lý: chỉ chi nhánh mình, không có nút tính lại', async () => {
    const { calls } = dashBackend('MANAGER')
    renderApp('/admin/dashboard')
    await screen.findByText('Ngày 02/11 (so với ngày trước)')
    expect(screen.queryByLabelText('Chi nhánh')).not.toBeInTheDocument()
    expect(calls[0]).toContain('&branch_id=1')
    expect(screen.queryByRole('button', { name: 'Tính lại hôm qua' })).not.toBeInTheDocument()
  })

  it('F8-FE-05 quản trị viên bấm "Tính lại hôm qua" → gọi rebuild rồi tải lại', async () => {
    const { calls, posts } = dashBackend('ADMIN')
    renderApp('/admin/dashboard')
    await screen.findByText('Ngày 02/11 (so với ngày trước)')
    await userEvent.click(screen.getByRole('button', { name: 'Tính lại hôm qua' }))
    expect(await screen.findByRole('status')).toHaveTextContent('Đã tính lại báo cáo ngày 02/11 cho 3 chi nhánh.')
    expect(posts).toEqual([{ date: vnDate(1) }])
    await waitFor(() => expect(calls.length).toBe(2))
  })

  it('F8-FE-06 chưa có báo cáo / lỗi API', async () => {
    dashBackend('ADMIN', null)
    renderApp('/admin/dashboard')
    expect(await screen.findByText('Chưa có báo cáo trong khoảng này.')).toBeInTheDocument()
  })

  it('F8-FE-07 lỗi API hiện thông báo', async () => {
    saveSession('tok', me('ADMIN'), 3600)
    mockFetch((url) => (url === '/api/auth/me' ? { status: 200, body: me('ADMIN') }
      : { status: 500, body: errorBody('HTTP_ERROR', 'Máy chủ đang bận') }))
    renderApp('/admin/dashboard')
    expect(await screen.findByRole('alert')).toHaveTextContent('Máy chủ đang bận')
  })
})

describe('F8-FE-08 Hàm tiện ích dashboard', () => {
  it('F8-FE-08 % thay đổi, điểm %, thời gian chờ, dữ liệu biểu đồ, ngày giờ VN', () => {
    expect(delta('amount', 110, 100)).toBe('+10,0%')
    expect(delta('amount', 90, 100)).toBe('-10,0%')
    expect(delta('amount', 5, 0)).toBeNull()
    expect(delta('amount', 0, 0)).toBe('0%')
    expect(delta('amount', 5, undefined)).toBeNull()
    expect(delta('ratio', 0.25, 0.3)).toBe('-5,0 điểm %')
    expect(delta('wait', 400, 380)).toBe('+0:20')
    expect(delta('wait', null, 380)).toBeNull()
    expect(formatWait(380)).toBe('6 phút 20s')
    expect(formatWait(null)).toBe('–')
    expect(chartData(DASH, new Map([[1, 'CG'], [2, 'HD']]))).toEqual([
      { day: '01/11', CG: 7000000, HD: 5000000 }, { day: '02/11', CG: 7120000 }])
    // 2026-11-02 18:00 UTC = 03/11 01:00 giờ VN → "hôm qua" là 02/11
    const now = Date.UTC(2026, 10, 2, 18, 0)
    expect(vnDate(0, now)).toBe('2026-11-03')
    expect(vnDate(1, now)).toBe('2026-11-02')
  })
})

describe('F8-FE-09 Hồi quy BUG-F8-01 – màu xu hướng', () => {
  it('F8-FE-09 thời gian chờ giảm tô xanh, tăng tô đỏ; doanh thu ngược lại; 0 trung tính', async () => {
    expect(trendClass('-0:13', true)).toBe('text-green-700')
    expect(trendClass('+0:02', true)).toBe('text-red-600')
    expect(trendClass('+6,2%')).toBe('text-green-700')
    expect(trendClass('-11,7 điểm %')).toBe('text-red-600')
    expect(trendClass('0%')).toBe('text-stone-500')
    expect(trendClass('+0:00', true)).toBe('text-stone-500')
    dashBackend('ADMIN')
    renderApp('/admin/dashboard')
    await screen.findByText('Ngày 02/11 (so với ngày trước)')
    // DASH: chờ 380s so với 420s hôm trước → -0:40 → tốt → xanh
    expect(within(screen.getByTestId('kpi-Thời gian chờ TB')).getByText('-0:40')).toHaveClass('text-green-700')
  })
})
