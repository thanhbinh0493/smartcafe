import { act, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it } from 'vitest'
import type { RecItem, Recommendations } from '../../api/recommend'
import { errorBody, FakeWebSocket, installFakeWebSocket, MENU, mockFetch, renderApp, TABLE } from '../../test/utils'

const rec = (id: number, name: string, reason: string, extra: Partial<RecItem> = {}): RecItem => ({
  menu_item_id: id, name, image_url: null, regular_price: 40000, sell_price: 40000, is_promo: false, is_new: false,
  score: 0.5, reason_code: 'POPULAR', reason, ...extra,
})

const ANON: Recommendations = {
  log_id: 501, mode: 'ANONYMOUS', member_fallback: false, temp_c: 31, weather_source: 'mock', degraded: false,
  items: [
    rec(21, 'Trà đào cam sả', 'Đang giảm 20%', { regular_price: 45000, sell_price: 36000, is_promo: true }),
    rec(12, 'Bạc xỉu dừa', 'Món mới', { is_new: true }),
    rec(13, 'Bạc xỉu nóng', 'Bán chạy tại chi nhánh'),      // tạm hết trên menu → không hiện
    rec(22, 'Trà gừng mật ong', 'Hợp trời lạnh'),
  ],
  also_bought: [],
}
const MEMBER: Recommendations = { ...ANON, log_id: 502, mode: 'MEMBER', items: [rec(11, 'Cà phê sữa đá', 'Bạn hay gọi')] }

interface Opts {
  recs?: Recommendations | 'error'
  also?: RecItem[]
}

function backend(o: Opts = {}) {
  const calls: { url: string; auth?: string }[] = []
  const created: unknown[] = []
  const fn = mockFetch((url, init) => {
    const auth = (init?.headers as Record<string, string> | undefined)?.Authorization
    if (url === '/api/public/tables/good') return { status: 200, body: TABLE }
    if (url === '/api/public/branches/1/menu') return { status: 200, body: MENU }
    if (url.startsWith('/api/public/branches/1/recommendations')) {
      calls.push({ url, auth })
      if (o.recs === 'error') return { status: 500, body: errorBody('HTTP_ERROR', 'lỗi') }
      const base = o.recs ?? (auth ? MEMBER : ANON)
      return { status: 200, body: url.includes('cart=') ? { ...base, log_id: 600, also_bought: o.also ?? [] } : base }
    }
    if (url === '/api/public/me') return { status: 200, body: { phone_masked: '0912 *** 678', loyalty_points: 10, point_value_vnd: 100, points_value: 1000, recent_transactions: [] } }
    if (url === '/api/public/orders' && init?.method === 'POST') {
      created.push(JSON.parse(String(init.body)))
      return { status: 201, body: { order_id: 77, order_code: 'CG-0001', access_token: 'tok', status: 'PENDING_PAYMENT', subtotal: 0, discount: 0, total: 0, expected_points: null, items: [] } }
    }
    return { status: 404, body: errorBody('NOT_FOUND', url) }
  })
  return { calls, created, fn }
}

const block = () => within(screen.getByRole('region', { name: 'Gợi ý cho bạn' }))

beforeEach(() => installFakeWebSocket())

describe('F7-FE-01..05 W01 – khối "Gợi ý cho bạn" (UC03, 2 chế độ)', () => {
  it('F7-FE-01 khách ẩn danh: thẻ gợi ý kèm lý do, giá KM gạch giá gốc; không gửi token; bỏ món tạm hết', async () => {
    const { calls } = backend()
    renderApp('/t/good/menu')
    await screen.findByRole('region', { name: 'Gợi ý cho bạn' })
    const cards = block().getAllByRole('listitem')
    expect(cards.map((c) => c.textContent)).toEqual([
      expect.stringContaining('Trà đào cam sảĐang giảm 20%45.000đ36.000đ'),
      expect.stringContaining('Bạc xỉu dừaMón mới'),
      expect.stringContaining('Trà gừng mật ongHợp trời lạnh'),
    ])
    expect(calls[0]).toEqual({ url: '/api/public/branches/1/recommendations', auth: undefined })
    expect(sessionStorage.getItem('smartcafe.reclog.good')).toBe('501')
  })

  it('F7-FE-02 khách thành viên: gọi kèm customer token, hiện "Bạn hay gọi"', async () => {
    sessionStorage.setItem('smartcafe.member', JSON.stringify({ token: 'cust-tok', phoneMasked: '0912 *** 678', points: 10, expiresAt: Date.now() + 3600_000 }))
    const { calls } = backend()
    renderApp('/t/good/menu')
    await screen.findByRole('region', { name: 'Gợi ý cho bạn' })
    expect(await block().findByText('Bạn hay gọi')).toBeInTheDocument()
    expect(calls[0].auth).toBe('Bearer cust-tok')
  })

  it('F7-FE-03 thêm món từ khối gợi ý → giỏ đánh dấu is_recommended, đơn gửi kèm recommendation_log_id', async () => {
    const { created } = backend()
    renderApp('/t/good/menu')
    await userEvent.click(await screen.findByRole('button', { name: 'Thêm Trà đào cam sả (gợi ý)' }))
    await userEvent.click(screen.getByRole('button', { name: 'Thêm Trà gừng mật ong' }))    // thêm từ menu thường
    await userEvent.click(screen.getByRole('link', { name: /Giỏ hàng \(2\)/ }))
    await userEvent.click(await screen.findByRole('button', { name: /Thanh toán & gửi đơn/ }))
    await waitFor(() => expect(created).toHaveLength(1))
    expect(created[0]).toMatchObject({
      recommendation_log_id: 600,          // lần gợi ý gần nhất (trang giỏ hàng)
      items: [{ menu_item_id: 21, quantity: 1, is_recommended: true }, { menu_item_id: 22, quantity: 1, is_recommended: false }],
    })
  })

  it('F7-FE-04 API gợi ý lỗi: ẩn khối, menu vẫn dùng được (NFR-R1); ẩn khối khi lọc danh mục / tìm món', async () => {
    backend({ recs: 'error' })
    renderApp('/t/good/menu')
    await screen.findByText('Trà gừng mật ong')
    expect(screen.queryByRole('region', { name: 'Gợi ý cho bạn' })).not.toBeInTheDocument()
  })

  it('F7-FE-05 chỉ hiện ở tab "Tất cả" và khi không tìm kiếm; MENU_UPDATED thì tải lại gợi ý', async () => {
    const { calls } = backend()
    renderApp('/t/good/menu')
    await screen.findByRole('region', { name: 'Gợi ý cho bạn' })
    await userEvent.click(screen.getByRole('button', { name: 'Trà' }))
    expect(screen.queryByRole('region', { name: 'Gợi ý cho bạn' })).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Tất cả' }))
    await userEvent.type(screen.getByLabelText('Tìm món'), 'tra')
    expect(screen.queryByRole('region', { name: 'Gợi ý cho bạn' })).not.toBeInTheDocument()
    const ws = FakeWebSocket.instances.find((w) => w.url.endsWith('/ws/menu/1'))!
    const before = calls.length
    act(() => ws.emit('MENU_UPDATED', { branch_id: 1, reason: 'PROMOTION' }))
    await waitFor(() => expect(calls.length).toBe(before + 1))
  })
})

describe('F7-FE-06..07 W02 – "Thường gọi kèm" (luật kết hợp)', () => {
  const croissant = rec(31, 'Bánh croissant bơ', 'Thường gọi kèm Cà phê sữa đá', { sell_price: 29000, regular_price: 29000, reason_code: 'CO_BUY' })

  it('F7-FE-06 giỏ có Cà phê sữa đá → gọi API kèm cart, hiện món kèm + lý do; thêm vào giỏ là món gợi ý, gọi lại với giỏ mới', async () => {
    const { calls } = backend({ also: [croissant] })
    renderApp('/t/good/menu')
    await userEvent.click(await screen.findByRole('button', { name: 'Thêm Cà phê sữa đá' }))
    await userEvent.click(screen.getByRole('link', { name: /Giỏ hàng \(1\)/ }))
    const also = within(await screen.findByRole('region', { name: 'Thường gọi kèm' }))
    expect(also.getByText('Thường gọi kèm Cà phê sữa đá')).toBeInTheDocument()
    expect(calls.at(-1)!.url).toBe('/api/public/branches/1/recommendations?cart=11')
    await userEvent.click(also.getByRole('button', { name: 'Thêm Bánh croissant bơ (gợi ý)' }))
    expect(await screen.findByTestId('cart-line-31')).toHaveTextContent('Bánh croissant bơ')
    await waitFor(() => expect(calls.at(-1)!.url).toBe('/api/public/branches/1/recommendations?cart=11,31'))
    const line = JSON.parse(sessionStorage.getItem('smartcafe.cart.good')!).find((l: { menu_item_id: number }) => l.menu_item_id === 31)
    expect(line).toMatchObject({ is_recommended: true, sell_price: 29000 })
  })

  it('F7-FE-07 không có luật phù hợp / API lỗi: không hiện khối', async () => {
    backend({ also: [] })
    renderApp('/t/good/menu')
    await userEvent.click(await screen.findByRole('button', { name: 'Thêm Cà phê sữa đá' }))
    await userEvent.click(screen.getByRole('link', { name: /Giỏ hàng \(1\)/ }))
    await screen.findByTestId('cart-line-11')
    expect(screen.queryByRole('region', { name: 'Thường gọi kèm' })).not.toBeInTheDocument()
  })
})
