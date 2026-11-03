import { act, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { OrderView } from '../../api/orders'
import { errorBody, FakeWebSocket, installFakeWebSocket, mockFetch, renderApp, TABLE } from '../../test/utils'

const line = (id: number, name: string, quantity: number, status: string, note: string | null = null) => ({
  id, menu_item_id: id, name, quantity, original_price: 29000, unit_price: 25000, is_promo: true, note, status,
})

const BASE: OrderView = {
  id: 77, order_code: 'CG-0142', status: 'PAID', branch_name: 'SmartCafe Cầu Giấy', table_number: '05',
  subtotal: 103000, discount: 17000, total: 86000, queue_position: 2, paid_at: '2026-11-02T10:00:00Z',
  ready_at: null, completed_at: null, cancelled_at: null, cancel_reason: null,
  items: [line(1, 'Cà phê sữa đá', 2, 'WAITING', 'ít đường'), line(2, 'Trà đào cam sả', 1, 'WAITING')] as OrderView['items'],
}

function orderBackend(views: OrderView[]) {
  let i = 0
  return mockFetch((url) => {
    if (url === '/api/public/tables/good') return { status: 200, body: TABLE }
    if (url === '/api/public/orders/77?token=tok') return { status: 200, body: views[Math.min(i++, views.length - 1)] }
    if (url.startsWith('/api/public/orders/77')) return { status: 404, body: errorBody('ORDER_NOT_FOUND', 'Không tìm thấy đơn hàng') }
    return { status: 404, body: errorBody('NOT_FOUND', 'Not Found') }
  })
}

const open = async () => {
  renderApp('/t/good/orders/77?token=tok')
  await screen.findByText('Đơn #CG-0142')
  await waitFor(() => expect(screen.queryByTestId('reconnecting')).not.toBeInTheDocument())
}

beforeEach(() => installFakeWebSocket())

describe('F2-FE-10..17 W03 – Theo dõi đơn (UC06)', () => {
  it('F2-FE-10 hiển thị đơn: mã, bàn, đã thanh toán, tiến trình, vị trí hàng đợi, từng món', async () => {
    orderBackend([BASE])
    await open()
    expect(screen.getAllByText('Bàn 05')).toHaveLength(1) // số bàn chỉ hiện 1 lần (BUG-F2-01)
    expect(screen.getByText('✔ Thanh toán thành công – 86.000đ')).toBeInTheDocument()
    expect(screen.getByText('Bạn đang ở vị trí thứ 2 trong hàng đợi pha chế.')).toBeInTheDocument()
    const steps = screen.getByRole('list', { name: 'Tiến trình' }).querySelectorAll('[aria-current="step"]')
    expect([...steps].map((s) => s.textContent)).toEqual(['Đang chờ'])
    expect(screen.getByText('Cà phê sữa đá ×2')).toBeInTheDocument()
    expect(screen.getByText('ít đường')).toBeInTheDocument()
    expect(screen.getAllByText('Đang chờ').length).toBeGreaterThanOrEqual(2)
  })

  it('F2-FE-11 mở WebSocket đúng kênh /ws/order/77?token=tok', async () => {
    orderBackend([BASE])
    await open()
    expect(FakeWebSocket.last().url).toBe('ws://localhost:3000/ws/order/77?token=tok')
  })

  it('F2-FE-12 sự kiện mang đủ dữ liệu đơn -> cập nhật ngay; sự kiện lẻ -> tải lại qua REST', async () => {
    const fetchMock = orderBackend([BASE, { ...BASE, status: 'PREPARING', queue_position: 1,
      items: [line(1, 'Cà phê sữa đá', 2, 'DONE'), line(2, 'Trà đào cam sả', 1, 'PREPARING')] as OrderView['items'] }])
    await open()
    act(() => FakeWebSocket.last().emit('ORDER_SNAPSHOT', { ...BASE, queue_position: 1 }))
    expect(screen.getByText('Bạn đang ở vị trí thứ 1 trong hàng đợi pha chế.')).toBeInTheDocument()
    const before = fetchMock.mock.calls.length
    act(() => FakeWebSocket.last().emit('ITEM_DONE', { order_item_id: 1 }))
    expect(await screen.findByText('✔ Xong')).toBeInTheDocument()
    expect(screen.getByText('Đang pha')).toBeInTheDocument()
    expect(fetchMock.mock.calls.length).toBe(before + 1)
  })

  it('F2-FE-13 đơn chuyển "Có thể lấy": banner xanh + rung điện thoại', async () => {
    const vibrate = vi.fn()
    Object.defineProperty(navigator, 'vibrate', { value: vibrate, configurable: true })
    orderBackend([BASE])
    await open()
    expect(vibrate).not.toHaveBeenCalled()
    act(() => FakeWebSocket.last().emit('ORDER_READY', { ...BASE, status: 'READY', queue_position: null }))
    expect(screen.getByRole('alert')).toHaveTextContent('Đồ uống đã sẵn sàng – mời bạn đến quầy nhận')
    expect(vibrate).toHaveBeenCalledTimes(1)
    const steps = screen.getByRole('list', { name: 'Tiến trình' }).querySelectorAll('[aria-current="step"]')
    expect(steps).toHaveLength(3)
  })

  it('F2-FE-14 đơn bị hủy: "Đơn đã hủy – đã hoàn tiền" và lý do', async () => {
    orderBackend([{ ...BASE, status: 'CANCELLED', queue_position: null, cancel_reason: 'Khách đổi ý' }])
    await open()
    expect(screen.getByRole('alert')).toHaveTextContent('Đơn đã hủy – đã hoàn tiền')
    expect(screen.getByText('Lý do: Khách đổi ý')).toBeInTheDocument()
    expect(screen.queryByRole('list', { name: 'Tiến trình' })).not.toBeInTheDocument()
  })

  it('F2-FE-15 rớt kết nối: báo đang kết nối lại và tự kết nối lại (NFR-R3)', async () => {
    orderBackend([BASE])
    await open()
    expect(FakeWebSocket.instances).toHaveLength(1)
    act(() => FakeWebSocket.last().drop())
    expect(screen.getByTestId('reconnecting')).toBeInTheDocument()
    await waitFor(() => expect(FakeWebSocket.instances).toHaveLength(2), { timeout: 2500 })
    await waitFor(() => expect(screen.queryByTestId('reconnecting')).not.toBeInTheDocument())
  })

  it('F2-FE-16 sai token: báo không tìm thấy đơn; WebSocket bị từ chối thì không thử lại', async () => {
    orderBackend([BASE])
    renderApp('/t/good/orders/77?token=sai')
    expect(await screen.findByRole('alert')).toHaveTextContent('Không tìm thấy đơn hàng')
    act(() => FakeWebSocket.last().drop(4404))
    await new Promise((r) => setTimeout(r, 1200))
    expect(FakeWebSocket.instances).toHaveLength(1)
  })

  it('F2-FE-17 "Gọi thêm món" quay lại menu', async () => {
    orderBackend([BASE])
    await open()
    await userEvent.click(screen.getByRole('link', { name: 'Gọi thêm món' }))
    expect(screen.getByTestId('location')).toHaveTextContent('/t/good/menu')
  })
})

describe('F3-FE-13..14 W03 – cập nhật từ màn hình Bar', () => {
  it('F3-FE-13 QUEUE_POSITION → cập nhật vị trí ngay, không gọi lại REST', async () => {
    const fetchMock = orderBackend([BASE])
    await open()
    const calls = fetchMock.mock.calls.length
    act(() => FakeWebSocket.last().emit('QUEUE_POSITION', { order_id: 77, queue_position: 1 }))
    expect(await screen.findByText('Bạn đang ở vị trí thứ 1 trong hàng đợi pha chế.')).toBeInTheDocument()
    expect(fetchMock.mock.calls.length).toBe(calls)
  })

  it('F3-FE-14 đơn hoàn tất: cảm ơn + số điểm được cộng (khách thành viên)', async () => {
    orderBackend([BASE])
    await open()
    act(() => FakeWebSocket.last().emit('ORDER_COMPLETED', { ...BASE, status: 'COMPLETED', queue_position: null, points_earned: 9 }))
    expect(await screen.findByText('Bạn đã nhận đồ. Cảm ơn bạn!')).toBeInTheDocument()
    expect(screen.getByTestId('points-earned')).toHaveTextContent('Bạn được cộng 9 điểm tích lũy.')
    act(() => FakeWebSocket.last().emit('ORDER_COMPLETED', { ...BASE, status: 'COMPLETED', queue_position: null, points_earned: null }))
    await waitFor(() => expect(screen.queryByTestId('points-earned')).not.toBeInTheDocument())
  })
})
