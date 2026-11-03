import { render } from '@testing-library/react'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { vi } from 'vitest'
import App from '../App'
import type { Menu, TableInfo } from '../api/public'

type Handler = (url: string, init?: RequestInit) => { status: number; body: unknown }

/** Giả lập fetch: handler nhận URL, trả {status, body}. */
export function mockFetch(handler: Handler) {
  const fn = vi.fn(async (url: string, init?: RequestInit) => {
    const { status, body } = handler(url, init)
    if (status === 204) return new Response(null, { status }) // 204 không được có nội dung
    return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
  })
  vi.stubGlobal('fetch', fn)
  return fn
}

export function errorBody(code: string, message: string) {
  return { error: { code, message, details: {} } }
}

function LocationProbe() {
  const loc = useLocation()
  return <div data-testid="location">{loc.pathname}</div>
}

export function renderApp(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <App />
      <LocationProbe />
    </MemoryRouter>,
  )
}

export const TABLE: TableInfo = {
  branch: { id: 1, code: 'CG', name: 'SmartCafe Cầu Giấy', address: '122 Xuân Thủy' },
  table: { id: 5, table_number: '05' },
}

const base = { description: null, image_url: null, temperature_type: 'COLD' as const, tags: [], promotion_id: null }

export const MENU: Menu = {
  branch_id: 1,
  categories: [
    {
      id: 1,
      name: 'Cà phê',
      items: [
        { ...base, id: 11, name: 'Cà phê sữa đá', regular_price: 29000, sell_price: 25000, is_promo: true, promotion_id: 2, is_new: false, is_available: true },
        { ...base, id: 12, name: 'Bạc xỉu dừa', regular_price: 39000, sell_price: 39000, is_promo: false, is_new: true, is_available: true },
        { ...base, id: 13, name: 'Bạc xỉu nóng', regular_price: 32000, sell_price: 32000, is_promo: false, is_new: false, is_available: false },
      ],
    },
    {
      id: 2,
      name: 'Trà',
      items: [
        { ...base, id: 21, name: 'Trà đào cam sả', regular_price: 45000, sell_price: 36000, is_promo: true, promotion_id: 1, is_new: false, is_available: true },
        { ...base, id: 22, name: 'Trà gừng mật ong', regular_price: 35000, sell_price: 35000, is_promo: false, is_new: false, is_available: true },
      ],
    },
  ],
}

/** WebSocket giả: test tự đẩy message (emit) hoặc làm rớt kết nối (drop). */
export class FakeWebSocket {
  static instances: FakeWebSocket[] = []
  onopen: ((ev: unknown) => void) | null = null
  onmessage: ((ev: { data: string }) => void) | null = null
  onclose: ((ev: { code: number }) => void) | null = null
  closed = false

  constructor(public url: string) {
    FakeWebSocket.instances.push(this)
    setTimeout(() => !this.closed && this.onopen?.({}), 0)
  }

  static last(): FakeWebSocket {
    return FakeWebSocket.instances[FakeWebSocket.instances.length - 1]
  }

  emit(type: string, data: unknown) {
    this.onmessage?.({ data: JSON.stringify({ type, data, ts: '2026-11-02T10:00:00Z' }) })
  }

  drop(code = 1006) {
    this.closed = true
    this.onclose?.({ code })
  }

  send() {}

  close() {
    if (!this.closed) this.drop(1000)
  }
}

export function installFakeWebSocket() {
  FakeWebSocket.instances = []
  vi.stubGlobal('WebSocket', FakeWebSocket)
}

/** Backend giả cho luồng QR: qr_token "good" hợp lệ, còn lại không hợp lệ. */
export function qrBackend(menu: Menu = MENU) {
  return mockFetch((url) => {
    if (url === '/api/public/tables/good') return { status: 200, body: TABLE }
    if (url.startsWith('/api/public/tables/'))
      return { status: 404, body: errorBody('TABLE_NOT_FOUND', 'Mã QR không hợp lệ, vui lòng gọi nhân viên') }
    if (url === '/api/public/branches/1/menu') return { status: 200, body: menu }
    return { status: 404, body: errorBody('NOT_FOUND', 'Not Found') }
  })
}
