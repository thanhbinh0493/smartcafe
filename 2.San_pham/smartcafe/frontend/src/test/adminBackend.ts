/** Backend giả có trạng thái cho các màn hình quản trị (F6). */
import type { AdminBranch, AdminMenuItem, BranchMenuRow, Category, DiningTable, Promotion, StaffAccount } from '../api/admin'
import type { StaffMe, StaffRole } from '../api/auth'
import { saveSession } from '../auth/staffSession'
import { errorBody, mockFetch } from './utils'

export const CG = { id: 1, code: 'CG', name: 'SmartCafe Cầu Giấy' }
export const HD = { id: 2, code: 'HD', name: 'SmartCafe Hà Đông' }

export const me = (role: StaffRole, id = 1): StaffMe => ({
  id, username: role === 'ADMIN' ? 'admin' : 'ql_cg', full_name: role === 'ADMIN' ? 'Trần Thị A' : 'Lê Văn Q', role,
  branch: role === 'ADMIN' ? null : CG,
})

const item = (id: number, category_id: number, name: string, base_price: number, extra: Partial<AdminMenuItem> = {}): AdminMenuItem => ({
  id, category_id, category_name: category_id === 1 ? 'Cà phê' : 'Trà', name, description: null, base_price,
  image_url: null, temperature_type: 'COLD', tags: [], is_active: true, created_at: '2026-10-01T00:00:00Z', ...extra,
})

export interface AdminState {
  categories: Category[]
  items: AdminMenuItem[]
  branches: AdminBranch[]
  staff: StaffAccount[]
  branchMenu: BranchMenuRow[]
  tables: DiningTable[]
  promotions: Promotion[]
  /** Trả lỗi cho request khớp "METHOD url" */
  fail?: Record<string, { status: number; code: string; message: string }>
}

export function initialState(): AdminState {
  const items = [
    item(11, 1, 'Cà phê sữa đá', 29000),
    item(12, 1, 'Bạc xỉu', 35000),
    item(21, 2, 'Trà đào cam sả', 45000),
    item(22, 2, 'Croissant', 30000, { is_active: false }),
  ]
  return {
    categories: [
      { id: 1, name: 'Cà phê', sort_order: 1, is_active: true, item_count: 2 },
      { id: 2, name: 'Trà', sort_order: 2, is_active: true, item_count: 2 },
    ],
    items,
    branches: [
      { ...CG, address: '122 Xuân Thủy', phone: null, latitude: 21.03, longitude: 105.78, is_active: true, table_count: 2, staff_count: 4 },
      { ...HD, address: '10 Quang Trung', phone: null, latitude: null, longitude: null, is_active: true, table_count: 0, staff_count: 1 },
    ],
    staff: [
      { id: 1, username: 'admin', full_name: 'Trần Thị A', role: 'ADMIN', branch_id: null, branch_name: null, phone: null, is_active: true, created_at: '' },
      { id: 2, username: 'ql_cg', full_name: 'Lê Văn Q', role: 'MANAGER', branch_id: 1, branch_name: CG.name, phone: null, is_active: true, created_at: '' },
      { id: 3, username: 'pc1_cg', full_name: 'Pha chế 1', role: 'BARISTA', branch_id: 1, branch_name: CG.name, phone: null, is_active: true, created_at: '' },
      { id: 4, username: 'ql_hd', full_name: 'Quản lý HD', role: 'MANAGER', branch_id: 2, branch_name: HD.name, phone: null, is_active: true, created_at: '' },
    ],
    branchMenu: items.filter((i) => i.is_active).map((i) => ({
      menu_item_id: i.id, name: i.name, category_id: i.category_id, category_name: i.category_name, base_price: i.base_price,
      price_override: i.id === 21 ? 39000 : null, is_available: i.id !== 12, updated_at: null,
    })),
    tables: [
      { id: 5, branch_id: 1, table_number: '05', qr_token: 'tok05', qr_url: 'http://localhost:8080/t/tok05', is_active: true },
      { id: 6, branch_id: 1, table_number: '06', qr_token: 'tok06', qr_url: 'http://localhost:8080/t/tok06', is_active: false },
    ],
    promotions: [],
  }
}

type Res = { status: number; body: unknown }

/** Đăng nhập sẵn với vai trò `role`, cài backend giả. Trả hàm fetch mock + trạng thái để kiểm tra. */
export function adminBackend(role: StaffRole, state: AdminState = initialState(), meId?: number) {
  const staff = me(role, meId ?? (role === 'ADMIN' ? 1 : 2))
  saveSession('tok', staff, 28800)
  const fetchMock = mockFetch((url, init): Res => {
    const method = init?.method ?? 'GET'
    const body = init?.body && typeof init.body === 'string' ? JSON.parse(init.body) : undefined
    const key = `${method} ${url}`
    const f = state.fail?.[key]
    if (f) return { status: f.status, body: errorBody(f.code, f.message) }
    if (url === '/api/auth/me') return { status: 200, body: staff }

    if (key === 'GET /api/staff/categories') return { status: 200, body: state.categories }
    if (key === 'POST /api/staff/categories') {
      const c = { id: 100 + state.categories.length, item_count: 0, ...body }
      state.categories = [...state.categories, c]
      return { status: 201, body: c }
    }
    let m = url.match(/^\/api\/staff\/categories\/(\d+)$/)
    if (m && method === 'PUT') {
      state.categories = state.categories.map((c) => (c.id === Number(m![1]) ? { ...c, ...body } : c))
      return { status: 200, body: state.categories.find((c) => c.id === Number(m![1])) }
    }
    if (m && method === 'DELETE') {
      state.categories = state.categories.filter((c) => c.id !== Number(m![1]))
      return { status: 204, body: null }
    }

    if (key === 'GET /api/staff/menu-items') return { status: 200, body: state.items }
    if (key === 'POST /api/staff/menu-items') {
      const it = item(200 + state.items.length, body.category_id, body.name, body.base_price, body)
      state.items = [...state.items, it]
      return { status: 201, body: it }
    }
    m = url.match(/^\/api\/staff\/menu-items\/(\d+)(\/image)?$/)
    if (m) {
      const id = Number(m[1])
      if (m[2]) {
        state.items = state.items.map((i) => (i.id === id ? { ...i, image_url: `/api/uploads/menu/${id}-abc.png` } : i))
        return { status: 200, body: state.items.find((i) => i.id === id) }
      }
      if (method === 'PUT') {
        state.items = state.items.map((i) => (i.id === id ? { ...i, ...body } : i))
        return { status: 200, body: state.items.find((i) => i.id === id) }
      }
      if (method === 'DELETE') {
        state.items = state.items.filter((i) => i.id !== id)
        return { status: 204, body: null }
      }
    }

    if (key === 'GET /api/staff/branches') return { status: 200, body: role === 'ADMIN' ? state.branches : state.branches.slice(0, 1) }
    if (key === 'POST /api/staff/branches') {
      const b = { id: 10 + state.branches.length, table_count: 0, staff_count: 0, ...body }
      state.branches = [...state.branches, b]
      return { status: 201, body: b }
    }
    m = url.match(/^\/api\/staff\/branches\/(\d+)$/)
    if (m && method === 'PUT') {
      state.branches = state.branches.map((b) => (b.id === Number(m![1]) ? { ...b, ...body, code: b.code } : b))
      return { status: 200, body: state.branches.find((b) => b.id === Number(m![1])) }
    }

    if (key === 'GET /api/staff/staff') return { status: 200, body: state.staff }
    if (key === 'POST /api/staff/staff') {
      const branch = state.branches.find((b) => b.id === body.branch_id)
      const s = { id: 50 + state.staff.length, created_at: '', branch_name: branch?.name ?? null, ...body }
      delete s.password
      state.staff = [...state.staff, s]
      return { status: 201, body: s }
    }
    m = url.match(/^\/api\/staff\/staff\/(\d+)$/)
    if (m && method === 'PUT') {
      const { password: _p, ...rest } = body
      state.staff = state.staff.map((s) => (s.id === Number(m![1]) ? { ...s, ...rest } : s))
      return { status: 200, body: state.staff.find((s) => s.id === Number(m![1])) }
    }

    m = url.match(/^\/api\/staff\/branches\/(\d+)\/menu(?:\/(\d+))?$/)
    if (m && method === 'GET') return { status: 200, body: state.branchMenu }
    if (m && method === 'PATCH') {
      const id = Number(m[2])
      state.branchMenu = state.branchMenu.map((r) => (r.menu_item_id === id ? { ...r, ...body, updated_at: '2026-11-03T05:00:00Z' } : r))
      return { status: 200, body: state.branchMenu.find((r) => r.menu_item_id === id) }
    }

    m = url.match(/^\/api\/staff\/branches\/(\d+)\/tables(?:\/(\d+))?$/)
    if (m && method === 'GET') return { status: 200, body: state.tables.filter((t) => t.branch_id === Number(m![1])) }
    if (m && method === 'POST') {
      const id = 100 + state.tables.length
      const t = { id, branch_id: Number(m[1]), qr_token: `tok${id}`, qr_url: `http://localhost:8080/t/tok${id}`, ...body }
      state.tables = [...state.tables, t]
      return { status: 201, body: t }
    }
    if (m && method === 'PUT') {
      state.tables = state.tables.map((t) => (t.id === Number(m![2]) ? { ...t, ...body } : t))
      return { status: 200, body: state.tables.find((t) => t.id === Number(m![2])) }
    }
    if (/^\/api\/staff\/tables\/\d+\/qr\.png$/.test(url)) return { status: 200, body: 'PNG' }

    m = url.match(/^\/api\/staff\/promotions\?status=(\w+)$/)
    if (m) return { status: 200, body: state.promotions.filter((p) => p.status === m![1]) }
    if (key === 'POST /api/staff/promotions' || /^PUT \/api\/staff\/promotions\/\d+$/.test(key)) {
      const id = method === 'POST' ? 300 + state.promotions.length : Number(url.split('/').pop())
      const branch = state.branches.find((b) => b.id === body.branch_id)
      const p: Promotion = {
        id, name: body.name, description: body.description, branch_id: body.branch_id, branch_name: branch?.name ?? null,
        start_at: body.start_at, end_at: body.end_at, is_active: body.is_active, created_by: 'Trần Thị A',
        status: new Date(body.start_at) > new Date() ? 'upcoming' : 'running',
        items: body.items.map((i: { menu_item_id: number; promo_price: number }) => ({
          ...i, name: state.items.find((x) => x.id === i.menu_item_id)?.name ?? '?', current_price: 0, discount_percent: 0,
        })),
      }
      state.promotions = [...state.promotions.filter((x) => x.id !== id), p]
      return { status: method === 'POST' ? 201 : 200, body: p }
    }
    return { status: 404, body: errorBody('NOT_FOUND', `Không có ${key}`) }
  })
  return { fetchMock, state }
}

/** Các request ghi (không phải GET) đã gửi: [METHOD url, body]. */
export function writes(fetchMock: ReturnType<typeof mockFetch>) {
  return fetchMock.mock.calls
    .filter(([, init]) => init?.method && init.method !== 'GET')
    .map(([url, init]) => [`${init!.method} ${url}`, typeof init!.body === 'string' ? JSON.parse(init!.body) : init!.body])
}
