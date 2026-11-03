import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it } from 'vitest'
import type { OrderView } from '../../api/orders'
import { errorBody, installFakeWebSocket, MENU, mockFetch, renderApp, TABLE } from '../../test/utils'

type Reply = { status: number; body: unknown }
interface Calls {
  create: Record<string, unknown>[]
  pay: Record<string, unknown>[]
}

const CREATED = {
  order_id: 77, order_code: 'CG-0001', access_token: 'tok', status: 'PENDING_PAYMENT',
  subtotal: 103000, discount: 17000, total: 86000, expected_points: null, items: [],
}

const VIEW: OrderView = {
  id: 77, order_code: 'CG-0001', status: 'PAID', branch_name: 'SmartCafe Cầu Giấy', table_number: '05',
  subtotal: 103000, discount: 17000, total: 86000, queue_position: 1, paid_at: '2026-11-02T10:00:00Z',
  ready_at: null, completed_at: null, cancelled_at: null, cancel_reason: null, items: [],
}

/** Backend giả cho cả luồng đặt món; create/pay trả lần lượt theo danh sách. */
function shopBackend(createReplies: Reply[] = [], payReplies: Reply[] = []) {
  const calls: Calls = { create: [], pay: [] }
  mockFetch((url, init) => {
    if (url === '/api/public/tables/good') return { status: 200, body: TABLE }
    if (url === '/api/public/branches/1/menu') return { status: 200, body: MENU }
    if (url === '/api/public/orders' && init?.method === 'POST') {
      calls.create.push(JSON.parse(String(init.body)))
      return createReplies.shift() ?? { status: 201, body: CREATED }
    }
    if (url === '/api/public/orders/77/pay') {
      calls.pay.push(JSON.parse(String(init?.body)))
      return payReplies.shift() ?? { status: 200, body: { order_id: 77, status: 'PAID', paid_at: 'x', transaction_ref: 'MOCK-1' } }
    }
    if (url.startsWith('/api/public/orders/77?')) return { status: 200, body: VIEW }
    return { status: 404, body: errorBody('NOT_FOUND', 'Not Found') }
  })
  return calls
}

const add = async (name: string, times = 1) => {
  for (let i = 0; i < times; i++) await userEvent.click(screen.getByRole('button', { name: `Thêm ${name}` }))
}

/** Vào menu, thêm 2 Cà phê sữa đá (KM 25.000, gốc 29.000) + 1 Trà đào (KM 36.000, gốc 45.000), mở giỏ. */
async function fillCart() {
  renderApp('/t/good/menu')
  await screen.findByText('Cà phê sữa đá')
  await add('Cà phê sữa đá', 2)
  await add('Trà đào cam sả')
  await userEvent.click(screen.getByRole('link', { name: /Giỏ hàng \(3\)/ }))
  await screen.findByRole('heading', { name: 'Giỏ hàng' })
  expect(screen.getAllByText('Bàn 05')).toHaveLength(1) // số bàn chỉ hiện 1 lần (BUG-F2-01)
}

beforeEach(() => installFakeWebSocket())

describe('F2-FE-01..02 W01 – thêm món vào giỏ (UC04)', () => {
  it('F2-FE-01 bấm "+" tăng số lượng, hiện thanh giỏ hàng; món tạm hết không có nút thêm', async () => {
    shopBackend()
    renderApp('/t/good/menu')
    await screen.findByText('Cà phê sữa đá')
    expect(screen.queryByRole('link', { name: /Giỏ hàng/ })).not.toBeInTheDocument()
    await add('Cà phê sữa đá')
    expect(screen.getByTestId('qty-11')).toHaveTextContent('1')
    await add('Cà phê sữa đá')
    expect(screen.getByTestId('qty-11')).toHaveTextContent('2')
    expect(screen.getByRole('link', { name: /Giỏ hàng \(2\)/ })).toHaveTextContent('50.000đ')
    expect(screen.queryByRole('button', { name: 'Thêm Bạc xỉu nóng' })).not.toBeInTheDocument()
  })

  it('F2-FE-02 giỏ giữ trong sessionStorage của tab, không ghi localStorage (NFR-S7)', async () => {
    shopBackend()
    const { unmount } = renderApp('/t/good/menu')
    await screen.findByText('Cà phê sữa đá')
    await add('Trà đào cam sả')
    unmount()
    expect(JSON.parse(sessionStorage.getItem('smartcafe.cart.good')!)).toHaveLength(1)
    expect(localStorage.length).toBe(0)
    renderApp('/t/good/menu')
    expect(await screen.findByRole('link', { name: /Giỏ hàng \(1\)/ })).toBeInTheDocument()
  })
})

describe('F2-FE-03..09 W02 – Giỏ hàng & thanh toán (UC04, UC05)', () => {
  it('F2-FE-03 hiển thị tạm tính, khuyến mãi, tổng; tăng/giảm/xóa món', async () => {
    shopBackend()
    await fillCart()
    expect(screen.getByText('Tạm tính').nextSibling).toHaveTextContent('103.000đ')
    expect(screen.getByText('Khuyến mãi').nextSibling).toHaveTextContent('-17.000đ')
    expect(screen.getByTestId('cart-total')).toHaveTextContent('86.000đ')

    await userEvent.click(screen.getByRole('button', { name: 'Bớt Cà phê sữa đá' }))
    expect(screen.getByLabelText('Số lượng Cà phê sữa đá')).toHaveTextContent('1')
    expect(screen.getByTestId('cart-total')).toHaveTextContent('61.000đ')
    await userEvent.click(screen.getByRole('button', { name: 'Bớt Cà phê sữa đá' }))
    expect(screen.queryByTestId('cart-line-11')).not.toBeInTheDocument()
    await userEvent.click(within(screen.getByTestId('cart-line-21')).getByRole('button', { name: 'Xóa' }))
    expect(screen.getByText('Giỏ hàng trống.')).toBeInTheDocument()
  })

  it('F2-FE-04 mỗi món tối đa 20 ly', async () => {
    shopBackend()
    await fillCart()
    const plus = screen.getByRole('button', { name: 'Thêm Trà đào cam sả' })
    for (let i = 0; i < 25; i++) if (!(plus as HTMLButtonElement).disabled) await userEvent.click(plus)
    expect(screen.getByLabelText('Số lượng Trà đào cam sả')).toHaveTextContent('20')
    expect(plus).toBeDisabled()
  })

  it('F2-FE-05 đặt & thanh toán thành công -> sang trang theo dõi đơn, xóa giỏ', async () => {
    const calls = shopBackend()
    await fillCart()
    await userEvent.type(screen.getByLabelText('Ghi chú Cà phê sữa đá'), 'ít đường')
    await userEvent.click(screen.getByLabelText('Thẻ ngân hàng'))
    await userEvent.click(screen.getByRole('button', { name: /Thanh toán & gửi đơn/ }))

    expect(await screen.findByText('Đơn #CG-0001')).toBeInTheDocument()
    expect(screen.getByTestId('location')).toHaveTextContent('/t/good/orders/77')
    expect(calls.create[0]).toEqual({
      qr_token: 'good',
      expected_total: 86000,
      items: [
        { menu_item_id: 11, quantity: 2, note: 'ít đường', is_recommended: false },
        { menu_item_id: 21, quantity: 1, is_recommended: false },
      ],
    })
    expect(calls.pay).toEqual([{ access_token: 'tok', method: 'MOCK_CARD' }])
    expect(sessionStorage.getItem('smartcafe.cart.good')).toBeNull()
  })

  it('F2-FE-06 món vừa hết: báo lỗi, đánh dấu món, chặn thanh toán tới khi bỏ món', async () => {
    shopBackend([{ status: 409, body: { error: { code: 'ITEM_UNAVAILABLE', message: 'Món Trà đào cam sả đã tạm hết, vui lòng bỏ khỏi giỏ hàng', details: { item_ids: [21] } } } }])
    await fillCart()
    const submit = screen.getByRole('button', { name: /Thanh toán & gửi đơn/ })
    await userEvent.click(submit)
    expect(await screen.findByRole('alert')).toHaveTextContent('Món Trà đào cam sả đã tạm hết')
    expect(within(screen.getByTestId('cart-line-21')).getByText('Tạm hết')).toBeInTheDocument()
    expect(submit).toBeDisabled()
    await userEvent.click(within(screen.getByTestId('cart-line-21')).getByRole('button', { name: 'Xóa' }))
    expect(screen.getByRole('button', { name: /Thanh toán & gửi đơn/ })).toBeEnabled()
  })

  it('F2-FE-07 giá thay đổi: cập nhật giá mới, báo khách xác nhận lại rồi gửi đúng tổng mới', async () => {
    const calls = shopBackend([{
      status: 409,
      body: { error: { code: 'PRICE_CHANGED', message: 'Giá một số món vừa thay đổi, vui lòng kiểm tra lại giỏ hàng', details: {
        total: 95000, prices: [{ menu_item_id: 21, regular_price: 45000, sell_price: 45000, is_promo: false }] } } },
    }])
    await fillCart()
    await userEvent.click(screen.getByRole('button', { name: /Thanh toán & gửi đơn/ }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Tổng mới: 95.000đ')
    expect(screen.getByTestId('cart-total')).toHaveTextContent('95.000đ')
    await userEvent.click(screen.getByRole('button', { name: /Thanh toán & gửi đơn/ }))
    await screen.findByText('Đơn #CG-0001')
    expect(calls.create.map((c) => c.expected_total)).toEqual([86000, 95000])
  })

  it('F2-FE-08 thanh toán thất bại: báo lỗi, "Thử thanh toán lại" dùng lại đơn cũ', async () => {
    const calls = shopBackend([], [{ status: 402, body: errorBody('PAYMENT_FAILED', 'Thanh toán không thành công, vui lòng thử lại') }])
    await fillCart()
    await userEvent.click(screen.getByRole('button', { name: /Thanh toán & gửi đơn/ }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Thanh toán không thành công')
    await userEvent.click(screen.getByRole('button', { name: /Thử thanh toán lại/ }))
    await screen.findByText('Đơn #CG-0001')
    expect(calls.create).toHaveLength(1)
    expect(calls.pay).toHaveLength(2)
  })

  it('F2-FE-09 hiện "Đang xử lý thanh toán..." trong lúc chờ', async () => {
    let release: () => void = () => {}
    const gate = new Promise<void>((r) => (release = r))
    shopBackend()
    const original = globalThis.fetch
    globalThis.fetch = (async (url: string, init?: RequestInit) => {
      if (String(url).endsWith('/pay')) await gate
      return original(url, init)
    }) as typeof fetch
    await fillCart()
    await userEvent.click(screen.getByRole('button', { name: /Thanh toán & gửi đơn/ }))
    expect(await screen.findByRole('status')).toHaveTextContent('Đang xử lý thanh toán...')
    release()
    await waitFor(() => expect(screen.queryByRole('status')).not.toBeInTheDocument())
  })
})
