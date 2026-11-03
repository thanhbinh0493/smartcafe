import { act, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { Promotion } from '../../api/admin'
import { adminBackend, initialState, writes } from '../../test/adminBackend'
import { FakeWebSocket, installFakeWebSocket, MENU, mockFetch, renderApp, TABLE } from '../../test/utils'
import { discountPercent, toLocalInput } from './PromotionsPage'

beforeEach(() => {
  installFakeWebSocket()
  vi.spyOn(window, 'confirm').mockReturnValue(true)
})

const dialog = () => within(screen.getByRole('dialog'))

describe('F6-FE-12..15 A04 – Nhân viên (UC12)', () => {
  it('F6-FE-12 Quản lý: chỉ gán được Thu ngân / Pha chế, chi nhánh cố định; chỉ sửa được tài khoản cấp dưới', async () => {
    const { fetchMock } = adminBackend('MANAGER')
    renderApp('/admin/staff')
    await screen.findByText('pc1_cg')
    expect(screen.getByRole('button', { name: 'Sửa pc1_cg' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sửa ql_cg' })).toBeInTheDocument()     // chính mình
    expect(screen.queryByRole('button', { name: 'Sửa admin' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Sửa ql_hd' })).not.toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: '+ Thêm nhân viên' }))
    const d = dialog()
    expect(within(d.getByLabelText('Vai trò')).getAllByRole('option').map((o) => o.textContent)).toEqual(['Thu ngân', 'Pha chế'])
    expect(d.getByLabelText('Chi nhánh')).toBeDisabled()
    await userEvent.type(d.getByLabelText('Tên đăng nhập'), 'pc2_cg')
    await userEvent.type(d.getByLabelText('Họ tên'), 'Pha chế 2')
    await userEvent.type(d.getByLabelText('Mật khẩu'), 'matkhau123')
    await userEvent.click(d.getByRole('button', { name: 'Lưu' }))
    expect(await screen.findByRole('status')).toHaveTextContent('Đã lưu tài khoản "pc2_cg".')
    expect(writes(fetchMock)).toEqual([['POST /api/staff/staff', {
      username: 'pc2_cg', full_name: 'Pha chế 2', phone: null, role: 'BARISTA', branch_id: 1, is_active: true, password: 'matkhau123',
    }]])
  })

  it('F6-FE-13 khóa tài khoản và đặt lại mật khẩu; để trống mật khẩu thì giữ nguyên', async () => {
    const { fetchMock } = adminBackend('MANAGER')
    renderApp('/admin/staff')
    await userEvent.click(await screen.findByRole('button', { name: 'Sửa pc1_cg' }))
    await userEvent.click(dialog().getByLabelText(/Cho phép đăng nhập/))
    await userEvent.click(dialog().getByRole('button', { name: 'Lưu' }))
    await screen.findByText('Đã khóa')
    await userEvent.click(screen.getByRole('button', { name: 'Sửa pc1_cg' }))
    await userEvent.type(dialog().getByLabelText('Đặt lại mật khẩu'), '123')
    await userEvent.click(dialog().getByRole('button', { name: 'Lưu' }))
    expect(dialog().getByRole('alert')).toHaveTextContent('Mật khẩu tối thiểu 8 ký tự')
    await userEvent.type(dialog().getByLabelText('Đặt lại mật khẩu'), '45678')
    await userEvent.click(dialog().getByRole('button', { name: 'Lưu' }))
    await screen.findByRole('status')
    expect(writes(fetchMock).map(([, b]) => [(b as { is_active: boolean }).is_active, (b as { password: string | null }).password]))
      .toEqual([[false, null], [false, '12345678']])
  })

  it('F6-FE-14 tự sửa tài khoản của mình: không đổi được vai trò, không tự khóa', async () => {
    adminBackend('MANAGER')
    renderApp('/admin/staff')
    await userEvent.click(await screen.findByRole('button', { name: 'Sửa ql_cg' }))
    expect(dialog().getByLabelText('Vai trò')).toBeDisabled()
    expect(dialog().getByLabelText(/Cho phép đăng nhập/)).toBeDisabled()
    expect(dialog().getByText('Bạn không thể tự khóa hoặc tự đổi vai trò, chi nhánh của mình.')).toBeInTheDocument()
  })

  it('F6-FE-15 Quản trị viên: chọn đủ 4 vai trò, chọn chi nhánh; vai trò Quản trị viên thuộc trụ sở; lọc theo chi nhánh', async () => {
    const { fetchMock } = adminBackend('ADMIN')
    renderApp('/admin/staff')
    await screen.findByText('ql_hd')
    await userEvent.selectOptions(screen.getByLabelText('Lọc chi nhánh'), '2')
    expect(screen.queryByText('pc1_cg')).not.toBeInTheDocument()
    expect(screen.getByText('ql_hd')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: '+ Thêm nhân viên' }))
    const d = dialog()
    expect(within(d.getByLabelText('Vai trò')).getAllByRole('option')).toHaveLength(4)
    await userEvent.type(d.getByLabelText('Tên đăng nhập'), 'ql_td')
    await userEvent.type(d.getByLabelText('Họ tên'), 'Quản lý TD')
    await userEvent.type(d.getByLabelText('Mật khẩu'), 'matkhau123')
    await userEvent.selectOptions(d.getByLabelText('Vai trò'), 'MANAGER')
    await userEvent.selectOptions(d.getByLabelText('Chi nhánh làm việc'), '2')
    await userEvent.selectOptions(d.getByLabelText('Vai trò'), 'ADMIN')
    expect(d.getByLabelText('Chi nhánh')).toHaveValue('Trụ sở')
    await userEvent.selectOptions(d.getByLabelText('Vai trò'), 'MANAGER')
    await userEvent.click(d.getByRole('button', { name: 'Lưu' }))
    await screen.findByRole('status')
    expect(writes(fetchMock)[0][1]).toMatchObject({ role: 'MANAGER', branch_id: 2 })
  })
})

describe('F6-FE-16..17 W06 – Menu chi nhánh (UC13)', () => {
  it('F6-FE-16 sửa giá chi nhánh, bật/tắt còn hàng trên bảng; nút Lưu chỉ bật khi có thay đổi', async () => {
    const { fetchMock } = adminBackend('MANAGER')
    renderApp('/admin/branch-menu')
    await screen.findByText('SmartCafe Cầu Giấy')
    const row = within(await screen.findByTestId('bm-11'))
    expect(row.getByRole('button', { name: 'Lưu Cà phê sữa đá' })).toBeDisabled()
    expect(within(screen.getByTestId('bm-21')).getByLabelText('Giá chi nhánh Trà đào cam sả')).toHaveValue('39000')
    await userEvent.type(row.getByLabelText('Giá chi nhánh Cà phê sữa đá'), '27.000')
    await userEvent.click(row.getByLabelText('Còn hàng Cà phê sữa đá'))
    await userEvent.click(row.getByRole('button', { name: 'Lưu Cà phê sữa đá' }))
    expect(await screen.findByRole('status')).toHaveTextContent('Đã lưu "Cà phê sữa đá" – menu khách đã được cập nhật.')
    // Xóa giá riêng = dùng lại giá chung (gửi null)
    const tra = within(screen.getByTestId('bm-21'))
    await userEvent.clear(tra.getByLabelText('Giá chi nhánh Trà đào cam sả'))
    await userEvent.click(tra.getByRole('button', { name: 'Lưu Trà đào cam sả' }))
    await waitFor(() => expect(writes(fetchMock)).toHaveLength(2))
    expect(writes(fetchMock)).toEqual([
      ['PATCH /api/staff/branches/1/menu/11', { price_override: 27000, is_available: false }],
      ['PATCH /api/staff/branches/1/menu/21', { price_override: null, is_available: true }],
    ])
  })

  it('F6-FE-17 lọc "Chỉ hiện món hết hàng"; giá không hợp lệ báo ngay trên dòng; Quản trị viên chọn chi nhánh', async () => {
    const { fetchMock } = adminBackend('ADMIN')
    renderApp('/admin/branch-menu')
    expect(await screen.findByLabelText('Chọn chi nhánh')).toHaveValue('1')
    await screen.findByTestId('bm-11')
    await userEvent.click(screen.getByLabelText('Chỉ hiện món hết hàng'))
    expect(screen.getAllByTestId(/^bm-/).map((r) => r.dataset.testid)).toEqual(['bm-12'])
    await userEvent.click(screen.getByLabelText('Chỉ hiện món hết hàng'))
    const row = within(screen.getByTestId('bm-11'))
    await userEvent.type(row.getByLabelText('Giá chi nhánh Cà phê sữa đá'), 'abc')
    await userEvent.click(row.getByRole('button', { name: 'Lưu Cà phê sữa đá' }))
    expect(row.getByRole('alert')).toHaveTextContent('Giá không hợp lệ')
    await userEvent.selectOptions(screen.getByLabelText('Chọn chi nhánh'), '2')
    await waitFor(() => expect(fetchMock.mock.calls.some(([u]) => u === '/api/staff/branches/2/menu')).toBe(true))
    expect(writes(fetchMock)).toEqual([])
  })
})

describe('F6-FE-18..19 A06 – Bàn & mã QR (UC14)', () => {
  it('F6-FE-18 thêm bàn, đổi số / khóa bàn; số bàn sai định dạng không gửi', async () => {
    const { fetchMock } = adminBackend('MANAGER')
    renderApp('/admin/tables')
    await screen.findByText('tok05', { exact: false })
    expect(screen.getByText('Đã khóa')).toBeInTheDocument()                          // bàn 06
    await userEvent.type(screen.getByLabelText('Số bàn mới'), '1 2')
    await userEvent.click(screen.getByRole('button', { name: '+ Thêm bàn' }))
    expect(screen.getByRole('alert')).toHaveTextContent('Số bàn 1–10 ký tự')
    await userEvent.clear(screen.getByLabelText('Số bàn mới'))
    await userEvent.type(screen.getByLabelText('Số bàn mới'), '12')
    await userEvent.click(screen.getByRole('button', { name: '+ Thêm bàn' }))
    expect(await screen.findByRole('status')).toHaveTextContent('Đã thêm bàn 12.')
    await userEvent.click(screen.getByRole('button', { name: 'Sửa bàn 05' }))
    await userEvent.click(dialog().getByLabelText(/Đang dùng/))
    await userEvent.click(dialog().getByRole('button', { name: 'Lưu' }))
    await screen.findByText('Đã lưu bàn 05.')
    expect(writes(fetchMock)).toEqual([
      ['POST /api/staff/branches/1/tables', { table_number: '12', is_active: true }],
      ['PUT /api/staff/branches/1/tables/5', { table_number: '05', is_active: false }],
    ])
  })

  it('F6-FE-19 xem QR: tải ảnh kèm JWT, có nút tải PNG; "In tất cả" chỉ gồm bàn đang dùng', async () => {
    vi.stubGlobal('URL', Object.assign(URL, { createObjectURL: vi.fn(() => 'blob:qr'), revokeObjectURL: vi.fn() }))
    const { fetchMock } = adminBackend('MANAGER')
    renderApp('/admin/tables')
    await userEvent.click(await screen.findByRole('button', { name: 'Xem QR bàn 05' }))
    expect(await dialog().findByRole('img', { name: 'QR bàn 05' })).toHaveAttribute('src', 'blob:qr')
    expect(dialog().getByRole('link', { name: 'Tải ảnh PNG' })).toHaveAttribute('download', 'QR_Ban_05.png')
    const call = fetchMock.mock.calls.find(([u]) => u === '/api/staff/tables/5/qr.png')!
    expect(call[1]?.headers).toEqual({ Authorization: 'Bearer tok' })
    await userEvent.click(dialog().getByRole('button', { name: 'Đóng' }))
    await userEvent.click(screen.getByRole('button', { name: 'In tất cả mã QR (1)' }))
    const sheet = within(screen.getByRole('dialog', { name: 'In mã QR' }))
    expect(await sheet.findAllByRole('img')).toHaveLength(1)
  })
})

describe('F6-FE-20..23 W07 – Khuyến mãi (UC15)', () => {
  const promo = (extra: Partial<Promotion>): Promotion => ({
    id: 1, name: 'Tuần lễ trà đào', description: null, branch_id: 1, branch_name: 'SmartCafe Cầu Giấy',
    start_at: '2026-11-02T00:00:00Z', end_at: '2026-11-15T16:59:00Z', is_active: true, status: 'running', created_by: 'Trần Thị A',
    items: [{ menu_item_id: 21, name: 'Trà đào cam sả', current_price: 45000, promo_price: 36000, discount_percent: 20 }], ...extra,
  })

  it('F6-FE-20 3 tab Đang chạy / Sắp chạy / Đã kết thúc; KM đã kết thúc chỉ xem, không sửa', async () => {
    const state = initialState()
    state.promotions = [promo({}), promo({ id: 2, name: 'KM cũ', status: 'ended', is_active: false })]
    adminBackend('ADMIN', state)
    renderApp('/admin/promotions')
    const running = await screen.findByTestId('promo-1')
    expect(running).toHaveTextContent('SmartCafe Cầu Giấy')
    expect(running).toHaveTextContent('Trà đào cam sả 36.000đ (-20%)')
    await userEvent.click(screen.getByRole('tab', { name: 'Đã kết thúc' }))
    expect(await screen.findByTestId('promo-2')).toHaveTextContent('Đã tắt')
    await userEvent.click(screen.getByRole('button', { name: 'Xem KM cũ' }))
    expect(dialog().getByLabelText('Tên chương trình')).toBeDisabled()
    expect(dialog().queryByRole('button', { name: 'Lưu chương trình' })).not.toBeInTheDocument()
    expect(dialog().getByText('Chương trình đã kết thúc, không sửa được để giữ đúng lịch sử.')).toBeInTheDocument()
  })

  it('F6-FE-21 tạo KM 1 chi nhánh: so với giá chi nhánh, tự tính % giảm, gửi giờ dạng ISO', async () => {
    const { fetchMock } = adminBackend('ADMIN')
    renderApp('/admin/promotions')
    await userEvent.click(await screen.findByRole('button', { name: '+ Tạo chương trình' }))
    const d = dialog()
    await userEvent.type(d.getByLabelText('Tên chương trình'), 'Tuần lễ trà đào')
    await userEvent.selectOptions(await d.findByLabelText('Áp dụng tại'), '1')
    await waitFor(() => expect(fetchMock.mock.calls.some(([u]) => u === '/api/staff/branches/1/menu')).toBe(true))
    await waitFor(() => expect(within(d.getByLabelText('Chọn món thêm vào chương trình')).getAllByRole('option').length).toBeGreaterThan(1))
    await userEvent.selectOptions(d.getByLabelText('Chọn món thêm vào chương trình'), '21')
    await userEvent.click(d.getByRole('button', { name: '+ Thêm món' }))
    expect(await d.findByText('39.000đ')).toBeInTheDocument()                    // giá riêng CN Cầu Giấy
    await userEvent.type(d.getByLabelText('Giá KM Trà đào cam sả'), '40000')
    await userEvent.click(d.getByRole('button', { name: 'Lưu chương trình' }))
    expect(d.getByRole('alert')).toHaveTextContent('phải nhỏ hơn giá bán hiện tại 39.000đ')
    await userEvent.clear(d.getByLabelText('Giá KM Trà đào cam sả'))
    await userEvent.type(d.getByLabelText('Giá KM Trà đào cam sả'), '31200')
    expect(d.getByText('20%')).toBeInTheDocument()
    await userEvent.clear(d.getByLabelText('Bắt đầu'))
    await userEvent.type(d.getByLabelText('Bắt đầu'), '2026-11-02T00:00')
    await userEvent.clear(d.getByLabelText('Kết thúc'))
    await userEvent.type(d.getByLabelText('Kết thúc'), '2099-11-15T23:59')
    await userEvent.click(d.getByRole('button', { name: 'Lưu chương trình' }))
    expect(await screen.findByRole('status')).toHaveTextContent('Đã lưu chương trình "Tuần lễ trà đào".')
    const [[key, body]] = writes(fetchMock)
    expect(key).toBe('POST /api/staff/promotions')
    expect(body).toEqual({
      name: 'Tuần lễ trà đào', description: null, branch_id: 1, is_active: true,
      start_at: new Date('2026-11-02T00:00').toISOString(), end_at: new Date('2099-11-15T23:59').toISOString(),
      items: [{ menu_item_id: 21, promo_price: 31200 }],
    })
  })

  it('F6-FE-22 kiểm tra trước khi gửi: kết thúc trước bắt đầu, chưa có món; lỗi server hiện trong form', async () => {
    const state = initialState()
    state.fail = { 'POST /api/staff/promotions': { status: 422, code: 'PROMOTION_INVALID', message: 'Thời gian kết thúc đã qua, chương trình sẽ không có hiệu lực' } }
    const { fetchMock } = adminBackend('ADMIN', state)
    renderApp('/admin/promotions')
    await userEvent.click(await screen.findByRole('button', { name: '+ Tạo chương trình' }))
    const d = dialog()
    await userEvent.type(d.getByLabelText('Tên chương trình'), 'KM')
    await userEvent.click(d.getByRole('button', { name: 'Lưu chương trình' }))
    expect(d.getByRole('alert')).toHaveTextContent('Vui lòng thêm ít nhất 1 món')
    await userEvent.clear(d.getByLabelText('Kết thúc'))
    await userEvent.type(d.getByLabelText('Kết thúc'), '2020-01-01T00:00')
    await userEvent.click(d.getByRole('button', { name: 'Lưu chương trình' }))
    expect(d.getByRole('alert')).toHaveTextContent('Thời gian kết thúc phải sau thời gian bắt đầu')
    expect(writes(fetchMock)).toEqual([])
    await userEvent.clear(d.getByLabelText('Kết thúc'))
    await userEvent.type(d.getByLabelText('Kết thúc'), '2099-01-01T00:00')
    await waitFor(() => expect(within(d.getByLabelText('Chọn món thêm vào chương trình')).getAllByRole('option').length).toBeGreaterThan(1))
    await userEvent.selectOptions(d.getByLabelText('Chọn món thêm vào chương trình'), '11')
    await userEvent.click(d.getByRole('button', { name: '+ Thêm món' }))
    await userEvent.type(d.getByLabelText('Giá KM Cà phê sữa đá'), '25000')
    await userEvent.click(d.getByRole('button', { name: 'Lưu chương trình' }))
    expect(await d.findByRole('alert')).toHaveTextContent('Thời gian kết thúc đã qua')
  })

  it('F6-FE-23 hàm tiện ích: % giảm, đổi giờ ISO sang ô datetime-local', () => {
    expect(discountPercent(45000, 36000)).toBe(20)
    expect(discountPercent(45000, 45000)).toBe(0)
    expect(discountPercent(0, 0)).toBe(0)
    expect(toLocalInput(new Date(2026, 10, 2, 8, 5).toISOString())).toBe('2026-11-02T08:05')
  })
})

describe('F6-FE-24 W01 – menu khách tự cập nhật khi quản trị thay đổi (MENU_UPDATED)', () => {
  it('F6-FE-24 nhận MENU_UPDATED trên /ws/menu/1 → tải lại menu, món vừa hết hàng hiện "Tạm hết"', async () => {
    let menu = MENU
    const fetchMock = mockFetch((url) => {
      if (url === '/api/public/tables/good') return { status: 200, body: TABLE }
      if (url === '/api/public/branches/1/menu') return { status: 200, body: menu }
      return { status: 404, body: {} }
    })
    renderApp('/t/good/menu')
    await screen.findByText('Trà gừng mật ong')
    const ws = FakeWebSocket.instances.find((w) => w.url.endsWith('/ws/menu/1'))!
    expect(ws).toBeTruthy()
    menu = {
      ...MENU,
      categories: MENU.categories.map((c) => ({ ...c, items: c.items.map((i) => (i.id === 22 ? { ...i, is_available: false } : i)) })),
    }
    const before = fetchMock.mock.calls.filter(([u]) => u === '/api/public/branches/1/menu').length
    act(() => ws.emit('MENU_UPDATED', { branch_id: 1, reason: 'BRANCH_MENU' }))
    await waitFor(() => expect(fetchMock.mock.calls.filter(([u]) => u === '/api/public/branches/1/menu').length).toBe(before + 1))
    await waitFor(() => expect(screen.queryByRole('button', { name: 'Thêm Trà gừng mật ong' })).not.toBeInTheDocument())
    expect(screen.getByRole('button', { name: 'Thêm Trà đào cam sả' })).toBeInTheDocument()
  })
})
