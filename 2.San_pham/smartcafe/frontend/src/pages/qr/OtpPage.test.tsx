import { act, fireEvent, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it } from 'vitest'
import type { OrderView } from '../../api/orders'
import { errorBody, FakeWebSocket, installFakeWebSocket, MENU, mockFetch, renderApp, TABLE } from '../../test/utils'

type Reply = { status: number; body: unknown }
type Call = { url: string; body: Record<string, unknown> | null; auth: string | null }

const SENT = { expires_in: 300, resend_after: 60, phone_masked: '0912 *** 678', demo_code: '482107' }
const inHour = () => new Date(Date.now() + 3600_000).toISOString()
const VERIFIED = () => ({
  customer_token: 'cust-tok', expires_at: inHour(), name: null, phone_masked: '0912 *** 678', loyalty_points: 120,
})
const ME = (points: number) => ({
  name: null, phone_masked: '0912 *** 678', loyalty_points: points, point_value_vnd: 100,
  points_value: points * 100, recent_transactions: [],
})
const CREATED = {
  order_id: 77, order_code: 'CG-0001', access_token: 'tok', status: 'PENDING_PAYMENT',
  subtotal: 58000, discount: 8000, total: 50000, expected_points: 5, items: [],
}
const VIEW: OrderView = {
  id: 77, order_code: 'CG-0001', status: 'PAID', branch_name: 'SmartCafe Cầu Giấy', table_number: '05',
  subtotal: 58000, discount: 8000, total: 50000, queue_position: 1, paid_at: '2026-11-03T10:00:00Z',
  ready_at: null, completed_at: null, cancelled_at: null, cancel_reason: null, expected_points: 5,
  points_earned: null, items: [],
}

/** Backend giả cho luồng thành viên; các API OTP / me / tạo đơn trả lần lượt theo danh sách. */
function memberBackend(opts: { request?: Reply[]; verify?: Reply[]; me?: Reply[]; create?: Reply[] } = {}) {
  const calls: Call[] = []
  mockFetch((url, init) => {
    const headers = (init?.headers ?? {}) as Record<string, string>
    calls.push({ url, body: init?.body ? JSON.parse(String(init.body)) : null, auth: headers.Authorization ?? null })
    if (url === '/api/public/tables/good') return { status: 200, body: TABLE }
    if (url === '/api/public/branches/1/menu') return { status: 200, body: MENU }
    if (url === '/api/public/otp/request') return opts.request?.shift() ?? { status: 200, body: SENT }
    if (url === '/api/public/otp/verify') return opts.verify?.shift() ?? { status: 200, body: VERIFIED() }
    if (url === '/api/public/me') return opts.me?.shift() ?? { status: 200, body: ME(120) }
    if (url === '/api/public/orders') return opts.create?.shift() ?? { status: 201, body: CREATED }
    if (url === '/api/public/orders/77/pay')
      return { status: 200, body: { order_id: 77, status: 'PAID', paid_at: 'x', transaction_ref: 'MOCK-1' } }
    if (url.startsWith('/api/public/orders/77?')) return { status: 200, body: VIEW }
    return { status: 404, body: errorBody('NOT_FOUND', 'Not Found') }
  })
  return calls
}

const otpError = (reason: string, message: string, left = 0): Reply => ({
  status: 400,
  body: { error: { code: 'OTP_INVALID', message, details: { reason, attempts_left: left } } },
})

function saveMember(expiresAt = Date.now() + 3600_000, points = 120) {
  sessionStorage.setItem(
    'smartcafe.member',
    JSON.stringify({ token: 'cust-tok', name: null, phoneMasked: '0912 *** 678', points, expiresAt }),
  )
}

const box = (i: number) => screen.getByRole('textbox', { name: `Số thứ ${i} của mã OTP` })

async function sendPhone(phone = '0912 345 678') {
  await userEvent.type(await screen.findByRole('textbox', { name: 'Số điện thoại' }), phone)
  await userEvent.click(screen.getByRole('button', { name: 'Gửi mã OTP' }))
  await screen.findByRole('heading', { name: 'Nhập mã xác thực' })
}

async function typeCode(code: string) {
  fireEvent.change(box(1), { target: { value: code } }) // dán cả mã vào ô đầu
}

beforeEach(() => installFakeWebSocket())

describe('F4-FE-01..07 W00a – Nhập SĐT và OTP (UC02)', () => {
  it('F4-FE-01 từ màn hình chào nhập SĐT, gửi mã: hiện SĐT đã che, khung [DEMO], đếm ngược, khóa gửi lại 60 giây', async () => {
    const calls = memberBackend()
    renderApp('/t/good')
    await userEvent.click(await screen.findByRole('button', { name: 'Nhập số điện thoại' }))
    expect(await screen.findByText(/Chỉ dùng để tích điểm/)).toBeInTheDocument()
    await sendPhone()
    expect(calls.find((c) => c.url === '/api/public/otp/request')?.body).toEqual({ phone: '0912 345 678' })
    expect(screen.getByText('0912 *** 678')).toBeInTheDocument()
    expect(screen.getByTestId('demo-code')).toHaveTextContent('482107')
    expect(screen.getByTestId('otp-expiry')).toHaveTextContent('Mã hết hạn sau 05:00')
    expect(screen.getByRole('button', { name: 'Gửi lại mã (sau 60s)' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Xác nhận' })).toBeDisabled() // chưa đủ 6 số
  })

  it('F4-FE-02 SĐT sai định dạng: nút gửi bị khóa khi quá ngắn, lỗi server hiện ra', async () => {
    memberBackend({
      request: [{ status: 422, body: errorBody('VALIDATION_ERROR', 'Số điện thoại không hợp lệ (cần số di động Việt Nam 10 số)') }],
    })
    renderApp('/t/good/otp')
    const input = await screen.findByRole('textbox', { name: 'Số điện thoại' })
    await userEvent.type(input, '0912')
    expect(screen.getByRole('button', { name: 'Gửi mã OTP' })).toBeDisabled()
    await userEvent.type(input, '34567890')
    await userEvent.click(screen.getByRole('button', { name: 'Gửi mã OTP' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Số điện thoại không hợp lệ')
    expect(screen.queryByRole('heading', { name: 'Nhập mã xác thực' })).not.toBeInTheDocument()
  })

  it('F4-FE-03 nhập đúng mã: thành viên, về menu "Xin chào – 120 điểm (≈ 12.000đ)", token chỉ ở sessionStorage', async () => {
    const calls = memberBackend()
    renderApp('/t/good/otp')
    await sendPhone()
    await typeCode('482107')
    expect(box(6)).toHaveValue('7')
    await userEvent.click(screen.getByRole('button', { name: 'Xác nhận' }))
    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent('/t/good/menu'))
    expect(calls.find((c) => c.url === '/api/public/otp/verify')?.body).toEqual({ phone: '0912 345 678', code: '482107' })
    const bar = await screen.findByTestId('member-bar')
    expect(bar).toHaveTextContent('Xin chào – 120 điểm (≈ 12.000đ)')
    expect(screen.queryByRole('link', { name: 'Nhập SĐT tích điểm' })).not.toBeInTheDocument()
    expect(JSON.parse(sessionStorage.getItem('smartcafe.member')!).token).toBe('cust-tok')
    expect(localStorage.length).toBe(0) // không lưu định danh lâu dài (NFR-S7)
  })

  it('F4-FE-04 sai mã: báo số lần còn lại, xóa các ô để nhập lại', async () => {
    memberBackend({ verify: [otpError('WRONG', 'Mã không đúng, bạn còn 4 lần thử', 4)] })
    renderApp('/t/good/otp')
    await sendPhone()
    await typeCode('111111')
    await userEvent.click(screen.getByRole('button', { name: 'Xác nhận' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('còn 4 lần thử')
    for (let i = 1; i <= 6; i++) expect(box(i)).toHaveValue('')
    expect(screen.getByTestId('location')).toHaveTextContent('/t/good/otp')
  })

  it('F4-FE-05 gửi lại mã: bị giới hạn thì báo thời gian chờ và khóa nút theo retry_after', async () => {
    memberBackend({
      request: [
        { status: 200, body: { ...SENT, resend_after: 0 } },
        { status: 429, body: { error: { code: 'OTP_RATE_LIMITED', message: 'Bạn đã yêu cầu quá 5 mã trong 1 giờ, vui lòng thử lại sau 30 phút', details: { retry_after: 1800 } } } },
      ],
    })
    renderApp('/t/good/otp')
    await sendPhone()
    await userEvent.click(screen.getByRole('button', { name: 'Gửi lại mã' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('quá 5 mã')
    expect(screen.getByRole('button', { name: 'Gửi lại mã (sau 1800s)' })).toBeDisabled()
  })

  it('F4-FE-06 gõ từng số tự chuyển ô; Backspace ở ô trống quay về ô trước; mã hết hạn thì báo gửi lại', async () => {
    memberBackend({
      request: [{ status: 200, body: { ...SENT, expires_in: 1 } }],
      verify: [otpError('EXPIRED', 'Mã đã hết hạn, vui lòng bấm "Gửi lại mã"')],
    })
    renderApp('/t/good/otp')
    await sendPhone()
    await userEvent.keyboard('48')
    expect(box(1)).toHaveValue('4')
    expect(box(2)).toHaveValue('8')
    expect(box(3)).toHaveFocus()
    await userEvent.keyboard('{Backspace}')
    expect(box(2)).toHaveFocus()
    await waitFor(() => expect(screen.getByTestId('otp-expiry')).toHaveTextContent('Mã đã hết hạn'), { timeout: 3000 })
    await typeCode('482107')
    await userEvent.click(screen.getByRole('button', { name: 'Xác nhận' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Mã đã hết hạn')
  })

  it('F4-FE-07 nút quay lại: từ bước nhập mã về bước nhập SĐT, từ bước SĐT về màn hình chào', async () => {
    memberBackend()
    renderApp('/t/good/otp')
    await sendPhone()
    await userEvent.click(screen.getByRole('button', { name: 'Quay lại' }))
    expect(await screen.findByRole('textbox', { name: 'Số điện thoại' })).toHaveValue('0912 345 678')
    await userEvent.click(screen.getByRole('button', { name: 'Quay lại' }))
    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent(/^\/t\/good$/))
  })
})

describe('F4-FE-08..11 W01 – Phiên thành viên trên menu (UC07, D18)', () => {
  it('F4-FE-08 mở menu thì cập nhật điểm mới nhất; "Thoát" về chế độ ẩn danh, xóa phiên', async () => {
    saveMember(undefined, 120)
    const calls = memberBackend({ me: [{ status: 200, body: ME(129) }] })
    renderApp('/t/good/menu')
    expect(await screen.findByTestId('member-bar')).toHaveTextContent('129 điểm (≈ 12.900đ)')
    expect(calls.find((c) => c.url === '/api/public/me')?.auth).toBe('Bearer cust-tok')
    await userEvent.click(screen.getByRole('button', { name: 'Thoát' }))
    expect(screen.getByRole('link', { name: 'Nhập SĐT tích điểm' })).toBeInTheDocument()
    expect(screen.queryByText(/Phiên thành viên đã hết hạn/)).not.toBeInTheDocument()
    expect(sessionStorage.getItem('smartcafe.member')).toBeNull()
  })

  it('F4-FE-09 server báo phiên hết hạn (401): về ẩn danh và báo cho khách', async () => {
    saveMember()
    memberBackend({ me: [{ status: 401, body: errorBody('TOKEN_EXPIRED', 'Phiên thành viên đã hết hạn') }] })
    renderApp('/t/good/menu')
    expect(await screen.findByText(/Phiên thành viên đã hết hạn/)).toBeInTheDocument()
    expect(screen.queryByTestId('member-bar')).not.toBeInTheDocument()
    expect(sessionStorage.getItem('smartcafe.member')).toBeNull()
  })

  it('F4-FE-10 phiên tự hết đúng giờ hết hạn khi khách đang ở menu', async () => {
    saveMember(Date.now() + 300)
    memberBackend()
    renderApp('/t/good/menu')
    expect(await screen.findByTestId('member-bar')).toBeInTheDocument()
    expect(await screen.findByText(/Phiên thành viên đã hết hạn/, {}, { timeout: 2000 })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Nhập SĐT tích điểm' })).toBeInTheDocument()
  })

  it('F4-FE-11 phiên đã hết hạn trong sessionStorage (mở lại trang) thì vào thẳng chế độ ẩn danh', async () => {
    saveMember(Date.now() - 1000)
    const calls = memberBackend()
    renderApp('/t/good/menu')
    expect(await screen.findByRole('link', { name: 'Nhập SĐT tích điểm' })).toBeInTheDocument()
    expect(calls.some((c) => c.url === '/api/public/me')).toBe(false)
    expect(sessionStorage.getItem('smartcafe.member')).toBeNull()
  })
})

describe('F4-FE-12..14 W02, W03 – Đặt món thành viên', () => {
  async function toCart() {
    renderApp('/t/good/menu')
    await screen.findByText('Cà phê sữa đá')
    await userEvent.click(screen.getByRole('button', { name: 'Thêm Cà phê sữa đá' }))
    await userEvent.click(screen.getByRole('button', { name: 'Thêm Cà phê sữa đá' }))
    await userEvent.click(screen.getByRole('link', { name: /Giỏ hàng \(2\)/ }))
    await screen.findByRole('heading', { name: 'Giỏ hàng' })
  }

  it('F4-FE-12 giỏ hàng hiện "+5 điểm", đơn gửi kèm customer token', async () => {
    saveMember()
    const calls = memberBackend()
    await toCart()
    expect(screen.getByTestId('cart-points')).toHaveTextContent('Bạn sẽ nhận +5 điểm khi nhận đồ') // 50.000đ
    await userEvent.click(screen.getByRole('button', { name: /Thanh toán & gửi đơn/ }))
    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent('/t/good/orders/77'))
    expect(calls.find((c) => c.url === '/api/public/orders')?.auth).toBe('Bearer cust-tok')
  })

  it('F4-FE-13 khách ẩn danh: không hiện điểm, đơn không gửi token', async () => {
    const calls = memberBackend({ create: [{ status: 201, body: { ...CREATED, expected_points: null } }] })
    await toCart()
    expect(screen.queryByTestId('cart-points')).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /Thanh toán & gửi đơn/ }))
    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent('/t/good/orders/77'))
    expect(calls.find((c) => c.url === '/api/public/orders')?.auth).toBeNull()
  })

  it('F4-FE-14 phiên hết hạn lúc đặt: không tự đặt ẩn danh; báo khách, có link nhập lại SĐT; bấm lại thì đặt ẩn danh', async () => {
    saveMember()
    const calls = memberBackend({
      create: [{ status: 401, body: errorBody('TOKEN_EXPIRED', 'Phiên thành viên đã hết hạn') }],
    })
    await toCart()
    await userEvent.click(screen.getByRole('button', { name: /Thanh toán & gửi đơn/ }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Phiên thành viên đã hết hạn (1 giờ)')
    expect(screen.getByRole('link', { name: 'Nhập lại SĐT' })).toBeInTheDocument()
    expect(screen.queryByTestId('cart-points')).not.toBeInTheDocument()
    expect(screen.getByTestId('location')).toHaveTextContent('/t/good/cart')
    await userEvent.click(screen.getByRole('button', { name: /Thanh toán & gửi đơn/ }))
    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent('/t/good/orders/77'))
    const creates = calls.filter((c) => c.url === '/api/public/orders')
    expect(creates.map((c) => c.auth)).toEqual(['Bearer cust-tok', null])
  })

  it('F4-FE-15 trang theo dõi: "sẽ nhận +5 điểm" khi đang chờ, "được cộng 5 điểm" khi hoàn tất', async () => {
    memberBackend()
    renderApp('/t/good/orders/77?token=tok')
    expect(await screen.findByTestId('expected-points')).toHaveTextContent('bạn sẽ nhận +5 điểm khi nhận đồ')
    await waitFor(() => expect(FakeWebSocket.instances.length).toBeGreaterThan(0))
    act(() =>
      FakeWebSocket.last().emit('ORDER_COMPLETED', {
        ...VIEW, status: 'COMPLETED', completed_at: '2026-11-03T10:10:00Z', points_earned: 5,
      }),
    )
    expect(await screen.findByTestId('points-earned')).toHaveTextContent('Bạn được cộng 5 điểm tích lũy.')
    expect(screen.queryByTestId('expected-points')).not.toBeInTheDocument()
  })
})
