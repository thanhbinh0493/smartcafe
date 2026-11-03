import { act, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { StaffMe } from '../../api/auth'
import type { BarOrder, QueueItem } from '../../api/bar'
import { saveSession } from '../../auth/staffSession'
import { playBeep } from '../../lib/beep'
import { errorBody, FakeWebSocket, installFakeWebSocket, mockFetch, renderApp } from '../../test/utils'

vi.mock('../../lib/beep', () => ({ playBeep: vi.fn(), unlockAudio: vi.fn() }))

const staffOf = (role: StaffMe['role']): StaffMe => ({
  id: 3,
  username: 'pc1_cg',
  full_name: 'Pha chế 1',
  role,
  branch: role === 'ADMIN' ? null : { id: 1, code: 'CG', name: 'SmartCafe Cầu Giấy' },
})

const q = (id: number, orderId: number, code: string, name: string, paid: string, extra: Partial<QueueItem> = {}): QueueItem => ({
  id, order_id: orderId, order_code: code, table_number: '05', paid_at: paid, name, quantity: 1, note: null,
  order_note: null, status: 'WAITING', started_at: null, ...extra,
})

// Giờ server 08:12 (giờ VN). Đơn CG-0001 gọi lúc 08:00 (chờ 12 phút → đỏ), CG-0002 lúc 08:10.
const SERVER_TIME = '2026-11-03T01:12:00Z'
const ITEMS = (): QueueItem[] => [
  q(1, 10, 'CG-0001', 'Cà phê sữa đá', '2026-11-03T01:00:00Z', { quantity: 2, note: 'ít đường', order_note: 'Mang đi' }),
  q(2, 10, 'CG-0001', 'Trà đào cam sả', '2026-11-03T01:00:00Z'),
  q(3, 11, 'CG-0002', 'Bạc xỉu', '2026-11-03T01:10:00Z', { table_number: '12' }),
]
const READY: BarOrder = {
  id: 9, order_code: 'CG-0000', table_number: '03', status: 'READY', is_member: true, total: 94000,
  paid_at: '2026-11-03T00:50:00Z', ready_at: '2026-11-03T01:05:00Z',
  items: [{ id: 90, name: 'Trà gừng', quantity: 1, note: null, status: 'DONE' }],
}

interface State {
  items: QueueItem[]
  ready: BarOrder[]
  fail?: { code: string; message: string }
}

function barBackend(role: StaffMe['role'], state: State) {
  return mockFetch((url, init) => {
    if (url === '/api/auth/me') return { status: 200, body: staffOf(role) }
    if (url === '/api/staff/branches/1/queue')
      return { status: 200, body: { branch_id: 1, server_time: SERVER_TIME, items: state.items } }
    if (url === '/api/staff/branches/1/orders?status=READY') return { status: 200, body: state.ready }
    const m = url.match(/^\/api\/staff\/order-items\/(\d+)\/(start|done|undo)$/)
    if (m && init?.method === 'POST') {
      if (state.fail) return { status: 409, body: errorBody(state.fail.code, state.fail.message) }
      const id = Number(m[1])
      if (m[2] === 'start') state.items = state.items.map((i) => (i.id === id ? { ...i, status: 'PREPARING' } : i))
      if (m[2] === 'done') state.items = state.items.filter((i) => i.id !== id)
      if (m[2] === 'undo') state.items = [...ITEMS().filter((i) => i.id === id).map((i) => ({ ...i, status: 'PREPARING' as const })), ...state.items]
      return { status: 200, body: { item_id: id, item_status: 'PREPARING', order_id: 10, order_status: 'PREPARING' } }
    }
    const c = url.match(/^\/api\/staff\/orders\/(\d+)\/complete$/)
    if (c && init?.method === 'POST') {
      state.ready = state.ready.filter((o) => o.id !== Number(c[1]))
      return { status: 200, body: { order_id: 9, status: 'COMPLETED', completed_at: SERVER_TIME, points_earned: 9 } }
    }
    return { status: 404, body: errorBody('NOT_FOUND', 'Not Found') }
  })
}

async function openBar(role: StaffMe['role'] = 'BARISTA', state: State = { items: ITEMS(), ready: [READY] }) {
  saveSession('tok', staffOf(role), 28800)
  const fetchMock = barBackend(role, state)
  renderApp('/admin/bar')
  await screen.findByText('Hàng đợi pha chế – SmartCafe Cầu Giấy')
  await screen.findByTestId('queue-row-1')
  await waitFor(() => expect(screen.getByTestId('bar-connection')).toHaveTextContent('Trực tuyến'))
  return { fetchMock, state }
}

const posts = (fetchMock: ReturnType<typeof mockFetch>) =>
  fetchMock.mock.calls.filter(([, init]) => init?.method === 'POST').map(([url, init]) => [url, (init?.headers as Record<string, string>).Authorization])

beforeEach(() => {
  installFakeWebSocket()
  vi.mocked(playBeep).mockClear()
})
afterEach(() => vi.useRealTimers())

describe('F3-FE-01..12 W04 – Màn hình quầy Bar (UC17–UC19)', () => {
  it('F3-FE-01 hàng đợi đủ cột, sắp theo giờ gọi, mở WebSocket kênh /ws/bar/1', async () => {
    await openBar()
    const rows = screen.getAllByTestId(/^queue-row-/)
    expect(rows.map((r) => r.dataset.testid)).toEqual(['queue-row-1', 'queue-row-2', 'queue-row-3'])
    const first = within(rows[0])
    for (const text of ['1', '08:00', '12 phút', '05', 'CG-0001', 'Cà phê sữa đá', '2', 'ít đường', 'Đơn: Mang đi'])
      expect(first.getByText(text)).toBeInTheDocument()
    expect(within(rows[2]).getByText('2 phút')).toBeInTheDocument()
    expect(screen.getByText('Chờ pha chế (3 món)')).toBeInTheDocument()
    expect(FakeWebSocket.last().url).toBe('ws://localhost:3000/ws/bar/1?token=tok')
  })

  it('F3-FE-02 món chờ quá 10 phút hiển thị màu đỏ', async () => {
    await openBar()
    expect(screen.getByTestId('queue-row-1')).toHaveAttribute('data-late', 'true')
    expect(screen.getByTestId('queue-row-1')).toHaveClass('text-red-700')
    expect(screen.getByTestId('queue-row-3')).not.toHaveAttribute('data-late')
  })

  it('F3-FE-16 (hồi quy BUG-F3-02) đơn hôm trước còn tồn trùng mã đơn hôm nay → giờ gọi kèm ngày để phân biệt', async () => {
    const old = q(5, 7, 'CG-0002', 'Bạc xỉu', '2026-11-02T01:00:00Z', { table_number: '07' })
    await openBar('BARISTA', { items: [old, ...ITEMS()], ready: [] })
    expect(within(screen.getByTestId('queue-row-5')).getByText('02/11 08:00')).toBeInTheDocument()
    expect(within(screen.getByTestId('queue-row-3')).getByText('08:10')).toBeInTheDocument() // đơn hôm nay: chỉ giờ
  })

  it('F3-FE-03 bấm "Bắt đầu" → gọi API kèm JWT, dòng chuyển "ĐANG PHA" + nút Xong', async () => {
    const { fetchMock } = await openBar()
    await userEvent.click(screen.getByRole('button', { name: 'Bắt đầu Cà phê sữa đá bàn 05' }))
    const row = await screen.findByTestId('queue-row-1')
    await within(row).findByText('ĐANG PHA')
    expect(within(row).getByRole('button', { name: 'Xong Cà phê sữa đá bàn 05' })).toBeInTheDocument()
    expect(posts(fetchMock)).toEqual([['/api/staff/order-items/1/start', 'Bearer tok']])
  })

  it('F3-FE-04 bấm "Xong" → món rời hàng đợi, có nút "Hoàn tác"; bấm Hoàn tác thì món quay lại', async () => {
    const state: State = { items: ITEMS().map((i) => ({ ...i, status: 'PREPARING' as const })), ready: [] }
    const { fetchMock } = await openBar('BARISTA', state)
    await userEvent.click(screen.getByRole('button', { name: 'Xong Cà phê sữa đá bàn 05' }))
    await waitFor(() => expect(screen.queryByTestId('queue-row-1')).not.toBeInTheDocument())
    const undoBar = screen.getByRole('list', { name: 'Hoàn tác' })
    expect(undoBar).toHaveTextContent('Đã xong: Cà phê sữa đá ×2 – bàn 05')
    await userEvent.click(within(undoBar).getByRole('button', { name: 'Hoàn tác' }))
    await screen.findByTestId('queue-row-1')
    expect(screen.queryByRole('list', { name: 'Hoàn tác' })).not.toBeInTheDocument()
    expect(posts(fetchMock).map(([u]) => u)).toEqual([
      '/api/staff/order-items/1/done', '/api/staff/order-items/1/undo',
    ])
  })

  it('F3-FE-05 nút "Hoàn tác" tự ẩn sau 10 giây', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    const state: State = { items: ITEMS().map((i) => ({ ...i, status: 'PREPARING' as const })), ready: [] }
    await openBar('BARISTA', state)
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
    await user.click(screen.getByRole('button', { name: 'Xong Trà đào cam sả bàn 05' }))
    await screen.findByRole('list', { name: 'Hoàn tác' })
    act(() => vi.advanceTimersByTime(9_000))
    expect(screen.getByRole('list', { name: 'Hoàn tác' })).toBeInTheDocument()
    act(() => vi.advanceTimersByTime(1_500))
    expect(screen.queryByRole('list', { name: 'Hoàn tác' })).not.toBeInTheDocument()
  })

  it('F3-FE-06 cột "Có thể lấy": bấm "Đã giao" → đơn biến mất, báo số điểm đã cộng', async () => {
    const { fetchMock } = await openBar()
    const card = screen.getByTestId('ready-9')
    expect(card).toHaveTextContent('CG-0000 · Bàn 03')
    expect(card).toHaveTextContent('(thành viên)')
    expect(card).toHaveTextContent('Trà gừng ×1')
    await userEvent.click(within(card).getByRole('button', { name: 'Đã giao CG-0000' }))
    expect(await screen.findByRole('status')).toHaveTextContent('Đã giao đơn CG-0000 – khách thành viên được cộng 9 điểm')
    await waitFor(() => expect(screen.queryByTestId('ready-9')).not.toBeInTheDocument())
    expect(screen.getByText('Có thể lấy (0)')).toBeInTheDocument()
    expect(posts(fetchMock)).toEqual([['/api/staff/orders/9/complete', 'Bearer tok']])
  })

  it('F3-FE-07 có món mới (QUEUE_ITEM_ADDED) → âm báo, thông báo, tải lại hàng đợi', async () => {
    const { state } = await openBar()
    state.items = [...state.items, q(4, 12, 'CG-0003', 'Matcha latte', '2026-11-03T01:11:00Z')]
    act(() => FakeWebSocket.last().emit('QUEUE_ITEM_ADDED', { order_id: 12, order_code: 'CG-0003' }))
    await screen.findByTestId('queue-row-4')
    expect(playBeep).toHaveBeenCalledTimes(1)
    expect(screen.getByRole('status')).toHaveTextContent('Có món mới – đơn CG-0003')
  })

  it('F3-FE-08 sự kiện khác (pha chế khác vừa thao tác) → tải lại, không kêu', async () => {
    const { state } = await openBar()
    state.items = state.items.filter((i) => i.id !== 3)
    act(() => FakeWebSocket.last().emit('ITEM_UPDATED', { item_id: 3, item_status: 'DONE' }))
    await waitFor(() => expect(screen.queryByTestId('queue-row-3')).not.toBeInTheDocument())
    expect(playBeep).not.toHaveBeenCalled()
  })

  it('F3-FE-09 thao tác bị từ chối (409) → báo lỗi và tải lại', async () => {
    const state: State = { items: ITEMS(), ready: [], fail: { code: 'INVALID_STATE_TRANSITION', message: 'Món này đã được bắt đầu pha' } }
    const { fetchMock } = await openBar('BARISTA', state)
    const before = fetchMock.mock.calls.filter(([u]) => String(u).endsWith('/queue')).length
    await userEvent.click(screen.getByRole('button', { name: 'Bắt đầu Bạc xỉu bàn 12' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Món này đã được bắt đầu pha')
    await waitFor(() => expect(fetchMock.mock.calls.filter(([u]) => String(u).endsWith('/queue')).length).toBe(before + 1))
  })

  it('F3-FE-10 thu ngân: chỉ xem, không có nút Bắt đầu / Xong / Đã giao', async () => {
    await openBar('CASHIER')
    expect(screen.getByText(/Chế độ xem: thu ngân chỉ xem hàng đợi/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^Bắt đầu/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^Đã giao/ })).not.toBeInTheDocument()
    expect(screen.queryByText('Thao tác')).not.toBeInTheDocument()
  })

  it('F3-FE-11 quản trị viên (không thuộc chi nhánh) → thông báo, không gọi API hàng đợi', async () => {
    saveSession('tok', staffOf('ADMIN'), 28800)
    const fetchMock = barBackend('ADMIN', { items: [], ready: [] })
    renderApp('/admin/bar')
    expect(await screen.findByText(/dành cho nhân viên chi nhánh/)).toBeInTheDocument()
    expect(fetchMock.mock.calls.some(([u]) => String(u).includes('/queue'))).toBe(false)
    expect(FakeWebSocket.instances).toHaveLength(0)
  })

  it('F3-FE-12 rớt mạng → báo "Đang kết nối lại", tự kết nối lại và tải lại hàng đợi; bị từ chối (4401) thì không thử lại', async () => {
    const { fetchMock } = await openBar()
    const loads = () => fetchMock.mock.calls.filter(([u]) => String(u).endsWith('/queue')).length
    const before = loads()
    act(() => FakeWebSocket.last().drop())
    expect(screen.getByTestId('bar-connection')).toHaveTextContent('Đang kết nối lại')
    await waitFor(() => expect(FakeWebSocket.instances).toHaveLength(2), { timeout: 3000 })
    await waitFor(() => expect(screen.getByTestId('bar-connection')).toHaveTextContent('Trực tuyến'))
    expect(loads()).toBeGreaterThan(before)
    act(() => FakeWebSocket.last().drop(4401))
    await new Promise((r) => setTimeout(r, 1200))
    expect(FakeWebSocket.instances).toHaveLength(2)
  })
})
