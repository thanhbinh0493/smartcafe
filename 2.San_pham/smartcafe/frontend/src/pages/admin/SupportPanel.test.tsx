import { act, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { StaffMe } from '../../api/auth'
import type { SupportOrder } from '../../api/support'
import { saveSession } from '../../auth/staffSession'
import { errorBody, FakeWebSocket, installFakeWebSocket, mockFetch, renderApp } from '../../test/utils'

vi.mock('../../lib/beep', () => ({ playBeep: vi.fn(), unlockAudio: vi.fn() }))

const staffOf = (role: StaffMe['role']): StaffMe => ({
  id: 5, username: 'tn_cg', full_name: 'Thu ngân CG', role,
  branch: role === 'ADMIN' ? null : { id: 1, code: 'CG', name: 'SmartCafe Cầu Giấy' },
})

const order = (id: number, code: string, extra: Partial<SupportOrder> = {}): SupportOrder => ({
  id, order_code: code, order_date: '2026-11-03', table_number: '05', status: 'PAID', total: 86000,
  is_member: false, note: null, created_at: '2026-11-03T01:00:00Z', paid_at: '2026-11-03T01:00:00Z',
  cancelled_at: null, cancel_reason: null, cancelled_by: null, can_cancel: true,
  payment: { method: 'MOCK_EWALLET', amount: 86000, status: 'SUCCESS', transaction_ref: 'MOCK-1', refunded_at: null },
  items: [{ id: 1, name: 'Cà phê sữa đá', quantity: 2, unit_price: 25000, note: null, status: 'WAITING' }],
  ...extra,
})

type Reply = { status: number; body: unknown }

function backend(role: StaffMe['role'], opts: { orders?: SupportOrder[]; cancel?: Reply; reloadFails?: boolean } = {}) {
  let orders = opts.orders ?? [order(10, 'CG-0002', { is_member: true }), order(9, 'CG-0001', { table_number: '06', status: 'READY', can_cancel: false })]
  let cancelled = false
  const calls: { url: string; body: unknown; auth?: string }[] = []
  const fetchMock = mockFetch((url, init) => {
    calls.push({ url, body: init?.body ? JSON.parse(String(init.body)) : null, auth: (init?.headers as Record<string, string>)?.Authorization })
    if (url === '/api/auth/me') return { status: 200, body: staffOf(role) }
    if (url === '/api/staff/branches/1/queue') return { status: 200, body: { branch_id: 1, server_time: '2026-11-03T01:12:00Z', items: [] } }
    if (url === '/api/staff/branches/1/orders?status=READY') return { status: 200, body: [] }
    if (url.startsWith('/api/staff/orders/search')) {
      const q = new URL(url, 'http://x').searchParams
      const code = q.get('code') ?? ''
      const table = q.get('table') ?? ''
      // reloadFails: lần tải lại sau khi hủy không về được (mất mạng / chậm) – giao diện vẫn phải đúng
      if (opts.reloadFails && cancelled) return { status: 503, body: errorBody('HTTP_ERROR', 'Không kết nối được máy chủ') }
      return { status: 200, body: orders.filter((o) => o.order_code.includes(code) && (!table || o.table_number === table)) }
    }
    const m = url.match(/^\/api\/staff\/orders\/(\d+)\/cancel$/)
    if (m && init?.method === 'POST') {
      if (opts.cancel) return opts.cancel
      const reason = (JSON.parse(String(init.body)) as { reason: string }).reason
      cancelled = true
      orders = orders.map((o) => (o.id === Number(m[1])
        ? { ...o, status: 'CANCELLED', can_cancel: false, cancel_reason: reason, cancelled_by: 'Thu ngân CG',
            payment: o.payment && { ...o.payment, status: 'REFUNDED', refunded_at: 'x' } }
        : o))
      return { status: 200, body: orders.find((o) => o.id === Number(m[1])) }
    }
    return { status: 404, body: errorBody('NOT_FOUND', 'Not Found') }
  })
  return { calls, fetchMock }
}

async function open(role: StaffMe['role'] = 'CASHIER', opts = {}) {
  saveSession('tok', staffOf(role), 28800)
  const b = backend(role, opts)
  renderApp('/admin/bar')
  await screen.findByRole('region', { name: 'Hỗ trợ khách' })
  await screen.findByTestId('support-10')
  return b
}

const panel = () => within(screen.getByRole('region', { name: 'Hỗ trợ khách' }))

beforeEach(() => installFakeWebSocket())

describe('F5-FE-01..09 W04 – Thu ngân hỗ trợ khách (UC20)', () => {
  it('F5-FE-01 thu ngân mở W04: khung hỗ trợ khách ở trên, tự tải đơn trong ngày; chỉ đơn PAID/PREPARING có nút Hủy', async () => {
    const { calls } = await open()
    expect(calls.find((c) => c.url === '/api/staff/orders/search')?.auth).toBe('Bearer tok')
    expect(panel().getByTestId('support-10')).toHaveTextContent('CG-0002 · Bàn 05Đang chờ(thành viên)')
    expect(panel().getByTestId('support-10')).toHaveTextContent('86.000đ')
    expect(panel().getByTestId('support-10')).toHaveTextContent('Cà phê sữa đá ×2')
    expect(panel().getByRole('button', { name: 'Hủy đơn CG-0002' })).toBeInTheDocument()
    expect(panel().getByTestId('support-9')).toHaveTextContent('Có thể lấy')
    expect(panel().queryByRole('button', { name: 'Hủy đơn CG-0001' })).not.toBeInTheDocument()
    // khung hỗ trợ đứng trước bảng hàng đợi
    const region = screen.getByRole('region', { name: 'Hỗ trợ khách' })
    const queueTitle = screen.getByText(/Chờ pha chế/)
    expect(region.compareDocumentPosition(queueTitle) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  })

  it('F5-FE-02 tìm theo mã đơn và bàn', async () => {
    const { calls } = await open()
    await userEvent.type(panel().getByLabelText('Mã đơn'), '0001')
    await userEvent.click(panel().getByRole('button', { name: 'Tìm' }))
    await waitFor(() => expect(panel().queryByTestId('support-10')).not.toBeInTheDocument())
    expect(panel().getByTestId('support-9')).toBeInTheDocument()
    await userEvent.clear(panel().getByLabelText('Mã đơn'))
    await userEvent.type(panel().getByLabelText('Bàn'), '07')
    await userEvent.click(panel().getByRole('button', { name: 'Tìm' }))
    expect(await panel().findByText('Không tìm thấy đơn phù hợp.')).toBeInTheDocument()
    expect(calls.map((c) => c.url)).toContain('/api/staff/orders/search?code=0001')
    expect(calls.map((c) => c.url)).toContain('/api/staff/orders/search?table=07')
  })

  it('F5-FE-03 hủy đơn: hộp xác nhận nêu số tiền hoàn; lý do bắt buộc ≥ 5 ký tự', async () => {
    const { calls } = await open()
    await userEvent.click(panel().getByRole('button', { name: 'Hủy đơn CG-0002' }))
    const dlg = screen.getByRole('dialog', { name: 'Hủy đơn CG-0002' })
    expect(dlg).toHaveTextContent('hoàn 86.000đ cho khách')
    const confirmBtn = within(dlg).getByRole('button', { name: 'Xác nhận hủy & hoàn tiền' })
    expect(confirmBtn).toBeDisabled()
    await userEvent.type(within(dlg).getByLabelText('Lý do hủy (bắt buộc)'), '  ab ')
    expect(confirmBtn).toBeDisabled()
    await userEvent.click(within(dlg).getByRole('button', { name: 'Khách đổi ý' }))
    expect(within(dlg).getByLabelText('Lý do hủy (bắt buộc)')).toHaveValue('Khách đổi ý')
    await userEvent.click(confirmBtn)
    expect(await screen.findByText('Đã hủy đơn CG-0002 và hoàn 86.000đ cho khách (giả lập).')).toBeInTheDocument()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    const post = calls.find((c) => c.url === '/api/staff/orders/10/cancel')
    expect(post?.body).toEqual({ reason: 'Khách đổi ý' })
    expect(post?.auth).toBe('Bearer tok')
    expect(panel().getByTestId('support-10')).toHaveTextContent('Đã hủy bởi Thu ngân CG – Lý do: Khách đổi ý – đã hoàn tiền')
    expect(panel().queryByRole('button', { name: 'Hủy đơn CG-0002' })).not.toBeInTheDocument()
  })

  it('F5-FE-04 server từ chối (đơn vừa chuyển "Có thể lấy"): hiện lỗi trong hộp thoại, không đóng', async () => {
    await open('CASHIER', {
      cancel: { status: 409, body: errorBody('CANNOT_CANCEL', 'Đồ uống đã pha xong ("Có thể lấy"), không thể hủy') },
    })
    await userEvent.click(panel().getByRole('button', { name: 'Hủy đơn CG-0002' }))
    const dlg = screen.getByRole('dialog')
    await userEvent.type(within(dlg).getByLabelText('Lý do hủy (bắt buộc)'), 'Khách gọi nhầm món')
    await userEvent.click(within(dlg).getByRole('button', { name: 'Xác nhận hủy & hoàn tiền' }))
    expect(await within(dlg).findByRole('alert')).toHaveTextContent('không thể hủy')
    await userEvent.click(within(dlg).getByRole('button', { name: 'Đóng' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('F5-FE-05 sự kiện ORDER_CANCELLED từ màn hình khác: báo pha chế và tải lại danh sách', async () => {
    const { calls } = await open()
    const before = calls.filter((c) => c.url.startsWith('/api/staff/orders/search')).length
    await waitFor(() => expect(FakeWebSocket.instances.length).toBeGreaterThan(0))
    act(() => FakeWebSocket.last().emit('ORDER_CANCELLED', { order_id: 10, order_code: 'CG-0002' }))
    expect(await screen.findByText('Đơn CG-0002 đã bị hủy – bỏ các món của đơn này')).toBeInTheDocument()
    await waitFor(() =>
      expect(calls.filter((c) => c.url.startsWith('/api/staff/orders/search')).length).toBeGreaterThan(before))
  })

  it('F5-FE-06 quản lý chi nhánh: có cả thao tác pha chế và khung hỗ trợ khách (ở dưới)', async () => {
    await open('MANAGER')
    expect(screen.queryByText(/Thu ngân: xem hàng đợi/)).not.toBeInTheDocument()
    expect(panel().getByRole('button', { name: 'Hủy đơn CG-0002' })).toBeInTheDocument()
    const region = screen.getByRole('region', { name: 'Hỗ trợ khách' })
    const queueTitle = screen.getByText(/Chờ pha chế/)
    expect(region.compareDocumentPosition(queueTitle) & Node.DOCUMENT_POSITION_PRECEDING).toBeTruthy()
  })

  it('F5-FE-07 pha chế không thấy khung hỗ trợ khách, không gọi API tra cứu', async () => {
    saveSession('tok', staffOf('BARISTA'), 28800)
    const { calls } = backend('BARISTA')
    renderApp('/admin/bar')
    await screen.findByText('Không có món nào đang chờ.')
    expect(screen.queryByRole('region', { name: 'Hỗ trợ khách' })).not.toBeInTheDocument()
    expect(calls.some((c) => c.url.startsWith('/api/staff/orders/search'))).toBe(false)
  })

  it('F5-FE-08 lỗi khi tra cứu: hiện thông báo', async () => {
    saveSession('tok', staffOf('CASHIER'), 28800)
    mockFetch((url) => {
      if (url === '/api/auth/me') return { status: 200, body: staffOf('CASHIER') }
      if (url === '/api/staff/branches/1/queue') return { status: 200, body: { branch_id: 1, server_time: '2026-11-03T01:12:00Z', items: [] } }
      if (url === '/api/staff/branches/1/orders?status=READY') return { status: 200, body: [] }
      return { status: 403, body: errorBody('FORBIDDEN', 'Vai trò của bạn không được phép thực hiện thao tác này') }
    })
    renderApp('/admin/bar')
    expect(await panel_findAlert()).toHaveTextContent('không được phép')
  })

  it('F5-FE-09 đơn đã hủy từ trước hiển thị lý do, không có nút hủy', async () => {
    await open('CASHIER', {
      orders: [order(10, 'CG-0002', { status: 'CANCELLED', can_cancel: false, cancel_reason: 'Hết nguyên liệu', cancelled_by: 'Quản lý CG',
        payment: { method: 'MOCK_CARD', amount: 86000, status: 'REFUNDED', transaction_ref: 'M', refunded_at: 'x' } })],
    })
    expect(panel().getByTestId('support-10')).toHaveTextContent('Đã hủy bởi Quản lý CG – Lý do: Hết nguyên liệu – đã hoàn tiền')
    expect(panel().queryByRole('button', { name: /Hủy đơn/ })).not.toBeInTheDocument()
  })
})

describe('F5-FE-10 hồi quy BUG-F5-01', () => {
  it('F5-FE-10 hủy xong, dòng đơn đổi ngay sang "Đã hủy" và mất nút Hủy, không phụ thuộc lần tải lại danh sách', async () => {
    await open('CASHIER', { reloadFails: true })
    await userEvent.click(panel().getByRole('button', { name: 'Hủy đơn CG-0002' }))
    const dlg = screen.getByRole('dialog')
    await userEvent.click(within(dlg).getByRole('button', { name: 'Khách gọi nhầm món' }))
    await userEvent.click(within(dlg).getByRole('button', { name: 'Xác nhận hủy & hoàn tiền' }))
    await screen.findByText(/Đã hủy đơn CG-0002/)
    expect(panel().getByTestId('support-10')).toHaveTextContent('Đã hủy bởi Thu ngân CG – Lý do: Khách gọi nhầm món')
    expect(panel().queryByRole('button', { name: 'Hủy đơn CG-0002' })).not.toBeInTheDocument()
  })
})

async function panel_findAlert() {
  const region = await screen.findByRole('region', { name: 'Hỗ trợ khách' })
  return within(region).findByRole('alert')
}
