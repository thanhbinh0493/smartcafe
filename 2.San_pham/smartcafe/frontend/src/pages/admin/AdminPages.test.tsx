import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { adminBackend, initialState, writes } from '../../test/adminBackend'
import { installFakeWebSocket, renderApp } from '../../test/utils'

beforeEach(() => {
  installFakeWebSocket()
  vi.spyOn(window, 'confirm').mockReturnValue(true)
})

const nav = () => within(screen.getByRole('navigation', { name: 'Menu quản trị' }))
const dialog = () => within(screen.getByRole('dialog'))

describe('F6-FE-01..03 Khung Web Admin: menu theo vai trò, chặn màn hình không đúng quyền', () => {
  it('F6-FE-01 Quản trị viên thấy đủ menu quản trị (không có Màn hình Bar)', async () => {
    adminBackend('ADMIN')
    renderApp('/admin/dashboard')
    await screen.findByRole('navigation', { name: 'Menu quản trị' })
    expect(nav().getAllByRole('link').map((a) => a.textContent)).toEqual([
      'Tổng quan', 'Chi nhánh', 'Nhân viên', 'Danh mục', 'Món', 'Menu chi nhánh', 'Bàn & mã QR', 'Khuyến mãi',
    ])
  })

  it('F6-FE-02 Quản lý chi nhánh chỉ thấy menu chi nhánh mình; gõ URL màn hình quản trị viên bị chặn', async () => {
    adminBackend('MANAGER')
    renderApp('/admin/promotions')
    await screen.findByRole('navigation', { name: 'Menu quản trị' })
    expect(nav().getAllByRole('link').map((a) => a.textContent)).toEqual([
      'Tổng quan', 'Nhân viên', 'Menu chi nhánh', 'Bàn & mã QR', 'Màn hình Bar',
    ])
    expect(screen.getByRole('alert')).toHaveTextContent('Bạn không có quyền truy cập màn hình này.')
  })

  it('F6-FE-03 Pha chế / thu ngân không có menu quản trị, mở URL quản trị bị chặn', async () => {
    adminBackend('BARISTA')
    renderApp('/admin/tables')
    expect(await screen.findByText('Bạn không có quyền truy cập màn hình này.')).toBeInTheDocument()
    expect(screen.queryByRole('navigation', { name: 'Menu quản trị' })).not.toBeInTheDocument()
  })
})

describe('F6-FE-04..05 A05 – Danh mục (UC09)', () => {
  it('F6-FE-04 thêm, sửa danh mục; gửi đúng dữ liệu kèm JWT', async () => {
    const { fetchMock } = adminBackend('ADMIN')
    renderApp('/admin/categories')
    await screen.findByText('Cà phê')
    await userEvent.click(screen.getByRole('button', { name: '+ Thêm danh mục' }))
    await userEvent.type(dialog().getByLabelText('Tên danh mục'), 'Đá xay')
    await userEvent.clear(dialog().getByLabelText('Thứ tự hiển thị'))
    await userEvent.type(dialog().getByLabelText('Thứ tự hiển thị'), '3')
    await userEvent.click(dialog().getByRole('button', { name: 'Lưu' }))
    expect(await screen.findByRole('status')).toHaveTextContent('Đã lưu danh mục "Đá xay".')
    expect(screen.getByText('Đá xay')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Sửa Trà' }))
    await userEvent.click(dialog().getByLabelText('Hiển thị trên menu khách'))
    await userEvent.click(dialog().getByRole('button', { name: 'Lưu' }))
    await screen.findByText('Đã ẩn')
    expect(writes(fetchMock)).toEqual([
      ['POST /api/staff/categories', { name: 'Đá xay', sort_order: 3, is_active: true }],
      ['PUT /api/staff/categories/2', { name: 'Trà', sort_order: 2, is_active: false }],
    ])
    const auth = fetchMock.mock.calls.find(([u]) => u === '/api/staff/categories')?.[1]?.headers as Record<string, string>
    expect(auth.Authorization).toBe('Bearer tok')
  })

  it('F6-FE-05 xóa danh mục còn món: hiện lỗi của server; tên trống thì không gửi', async () => {
    const state = initialState()
    state.fail = { 'DELETE /api/staff/categories/1': { status: 409, code: 'CATEGORY_IN_USE', message: 'Danh mục còn 2 món, hãy chuyển món sang danh mục khác hoặc ẩn danh mục' } }
    const { fetchMock } = adminBackend('ADMIN', state)
    renderApp('/admin/categories')
    await userEvent.click(await screen.findByRole('button', { name: 'Xóa Cà phê' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Danh mục còn 2 món')
    await userEvent.click(screen.getByRole('button', { name: '+ Thêm danh mục' }))
    await userEvent.click(dialog().getByRole('button', { name: 'Lưu' }))
    expect(dialog().getByRole('alert')).toHaveTextContent('Vui lòng nhập tên danh mục')
    expect(writes(fetchMock).map(([k]) => k)).toEqual(['DELETE /api/staff/categories/1'])
  })
})

describe('F6-FE-06..09 W05 – Quản lý món (UC10)', () => {
  it('F6-FE-06 danh sách theo bộ lọc: mặc định món đang bán, tìm không dấu, lọc danh mục', async () => {
    adminBackend('ADMIN')
    renderApp('/admin/menu-items')
    await screen.findByText('Cà phê sữa đá')
    expect(screen.queryByText('Croissant')).not.toBeInTheDocument()            // ngừng bán bị ẩn mặc định
    await userEvent.type(screen.getByLabelText('Tìm theo tên'), 'bac xiu')
    expect(screen.getAllByRole('row')).toHaveLength(2)
    expect(screen.getByText('Bạc xỉu')).toBeInTheDocument()
    await userEvent.clear(screen.getByLabelText('Tìm theo tên'))
    await userEvent.selectOptions(screen.getByLabelText('Lọc trạng thái'), 'hidden')
    expect(screen.getByText('Croissant')).toBeInTheDocument()
    expect(screen.queryByText('Cà phê sữa đá')).not.toBeInTheDocument()
  })

  it('F6-FE-07 thêm món kèm ảnh: lưu món rồi upload ảnh (multipart, không đặt Content-Type JSON)', async () => {
    const { fetchMock } = adminBackend('ADMIN')
    renderApp('/admin/menu-items')
    await userEvent.click(await screen.findByRole('button', { name: '+ Thêm món' }))
    const d = dialog()
    await userEvent.type(d.getByLabelText('Tên món'), 'Matcha đá xay')
    await userEvent.selectOptions(d.getByLabelText('Danh mục'), '2')
    await userEvent.type(d.getByLabelText('Giá gốc (đ)'), '55.000')
    await userEvent.selectOptions(d.getByLabelText('Loại nóng / lạnh'), 'COLD')
    await userEvent.type(d.getByLabelText('Thẻ (tags)'), 'matcha, sweet')
    const file = new File(['img'], 'matcha.png', { type: 'image/png' })
    await userEvent.upload(d.getByLabelText('Ảnh món'), file)
    await userEvent.click(d.getByRole('button', { name: 'Lưu' }))
    expect(await screen.findByRole('status')).toHaveTextContent('Đã lưu món "Matcha đá xay".')
    const [create, upload] = writes(fetchMock)
    expect(create).toEqual(['POST /api/staff/menu-items', {
      category_id: 2, name: 'Matcha đá xay', description: null, base_price: 55000, temperature_type: 'COLD',
      tags: ['matcha', 'sweet'], is_active: true,
    }])
    expect(upload[0]).toMatch(/^POST \/api\/staff\/menu-items\/\d+\/image$/)
    const init = fetchMock.mock.calls.find(([u]) => String(u).endsWith('/image'))![1]!
    expect(init.body).toBeInstanceOf(FormData)
    expect((init.body as FormData).get('file')).toBe(file)
    expect(init.headers).toEqual({ Authorization: 'Bearer tok' })
  })

  it('F6-FE-08 kiểm tra dữ liệu trước khi gửi: giá không hợp lệ, ảnh quá 2 MB', async () => {
    const { fetchMock } = adminBackend('ADMIN')
    renderApp('/admin/menu-items')
    await userEvent.click(await screen.findByRole('button', { name: '+ Thêm món' }))
    const d = dialog()
    await userEvent.type(d.getByLabelText('Tên món'), 'Món A')
    await userEvent.type(d.getByLabelText('Giá gốc (đ)'), '45k')
    await userEvent.click(d.getByRole('button', { name: 'Lưu' }))
    expect(d.getByRole('alert')).toHaveTextContent('Giá gốc phải là số tiền hợp lệ')
    await userEvent.clear(d.getByLabelText('Giá gốc (đ)'))
    await userEvent.type(d.getByLabelText('Giá gốc (đ)'), '45000')
    const big = new File([new Uint8Array(2 * 1024 * 1024 + 1)], 'big.jpg', { type: 'image/jpeg' })
    await userEvent.upload(d.getByLabelText('Ảnh món'), big)
    await userEvent.click(d.getByRole('button', { name: 'Lưu' }))
    expect(d.getByRole('alert')).toHaveTextContent('Ảnh tối đa 2 MB')
    expect(writes(fetchMock)).toEqual([])
  })

  it('F6-FE-09 ẩn món, xóa món (xác nhận), sửa món trùng tên hiện lỗi server', async () => {
    const state = initialState()
    state.fail = { 'PUT /api/staff/menu-items/12': { status: 409, code: 'DUPLICATE_VALUE', message: 'Đã có món cùng tên trong menu chung' } }
    const { fetchMock } = adminBackend('ADMIN', state)
    renderApp('/admin/menu-items')
    await userEvent.click(await screen.findByRole('button', { name: 'Ẩn Cà phê sữa đá' }))
    expect(await screen.findByRole('status')).toHaveTextContent('Đã ẩn "Cà phê sữa đá" khỏi menu toàn chuỗi.')
    await userEvent.click(screen.getByRole('button', { name: 'Xóa Trà đào cam sả' }))
    await waitFor(() => expect(screen.queryByText('Trà đào cam sả')).not.toBeInTheDocument())
    expect(window.confirm).toHaveBeenCalledWith('Xóa món "Trà đào cam sả"? Đơn cũ vẫn giữ lịch sử.')

    await userEvent.click(screen.getByRole('button', { name: 'Sửa Bạc xỉu' }))
    await userEvent.clear(dialog().getByLabelText('Tên món'))
    await userEvent.type(dialog().getByLabelText('Tên món'), 'Cà phê sữa đá')
    await userEvent.click(dialog().getByRole('button', { name: 'Lưu' }))
    expect(await dialog().findByRole('alert')).toHaveTextContent('Đã có món cùng tên trong menu chung')
    expect(writes(fetchMock).map(([k, b]) => [k, (b as { is_active?: boolean } | null)?.is_active])).toEqual([
      ['PUT /api/staff/menu-items/11', false], ['DELETE /api/staff/menu-items/21', undefined], ['PUT /api/staff/menu-items/12', true],
    ])
  })
})

describe('F6-FE-10..11 A03 – Chi nhánh (UC11)', () => {
  it('F6-FE-10 thêm chi nhánh: mã tự viết hoa; sửa thì không đổi được mã', async () => {
    const { fetchMock } = adminBackend('ADMIN')
    renderApp('/admin/branches')
    await screen.findByText('SmartCafe Hà Đông')
    await userEvent.click(screen.getByRole('button', { name: '+ Thêm chi nhánh' }))
    const d = dialog()
    await userEvent.type(d.getByLabelText('Mã chi nhánh'), 'td')
    await userEvent.type(d.getByLabelText('Tên chi nhánh'), 'SmartCafe Thủ Đức')
    await userEvent.type(d.getByLabelText('Địa chỉ'), '1 Võ Văn Ngân')
    await userEvent.type(d.getByLabelText('Vĩ độ'), '10.85')
    await userEvent.click(d.getByRole('button', { name: 'Lưu' }))
    expect(await screen.findByRole('status')).toHaveTextContent('Đã lưu chi nhánh "SmartCafe Thủ Đức".')
    expect(writes(fetchMock)[0]).toEqual(['POST /api/staff/branches', {
      code: 'TD', name: 'SmartCafe Thủ Đức', address: '1 Võ Văn Ngân', phone: null, latitude: 10.85, longitude: null, is_active: true,
    }])
    await userEvent.click(screen.getByRole('button', { name: 'Sửa SmartCafe Cầu Giấy' }))
    expect(dialog().getByLabelText('Mã chi nhánh')).toBeDisabled()
  })

  it('F6-FE-11 ngừng hoạt động chi nhánh phải xác nhận (khách quét QR sẽ báo không hợp lệ)', async () => {
    const { fetchMock } = adminBackend('ADMIN')
    vi.mocked(window.confirm).mockReturnValue(false)
    renderApp('/admin/branches')
    await userEvent.click(await screen.findByRole('button', { name: 'Sửa SmartCafe Hà Đông' }))
    await userEvent.click(dialog().getByLabelText('Đang hoạt động'))
    await userEvent.click(dialog().getByRole('button', { name: 'Lưu' }))
    expect(window.confirm).toHaveBeenCalledWith(expect.stringContaining('Khách quét QR các bàn của chi nhánh sẽ báo mã không hợp lệ'))
    expect(writes(fetchMock)).toEqual([])
    vi.mocked(window.confirm).mockReturnValue(true)
    await userEvent.click(dialog().getByRole('button', { name: 'Lưu' }))
    expect(await screen.findByText('Ngừng hoạt động')).toBeInTheDocument()
  })
})
