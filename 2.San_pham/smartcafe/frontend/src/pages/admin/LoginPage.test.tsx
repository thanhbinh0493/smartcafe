import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import type { StaffMe } from '../../api/auth'
import { loadSession, saveSession } from '../../auth/staffSession'
import { errorBody, mockFetch, renderApp } from '../../test/utils'

const staffOf = (role: StaffMe['role']): StaffMe => ({
  id: 1,
  username: 'u',
  full_name: 'Nguyễn Văn B',
  role,
  branch: role === 'ADMIN' ? null : { id: 1, code: 'CG', name: 'SmartCafe Cầu Giấy' },
})

function authBackend(role: StaffMe['role'] = 'BARISTA', meStatus = 200) {
  return mockFetch((url, init) => {
    if (url === '/api/auth/login') {
      const { password } = JSON.parse(String(init?.body))
      return password === 'dung'
        ? { status: 200, body: { access_token: 'tok', token_type: 'bearer', expires_in: 28800, staff: staffOf(role) } }
        : { status: 401, body: errorBody('INVALID_CREDENTIALS', 'Tên đăng nhập hoặc mật khẩu không đúng') }
    }
    if (url === '/api/auth/me')
      return meStatus === 200
        ? { status: 200, body: staffOf(role) }
        : { status: meStatus, body: errorBody('TOKEN_EXPIRED', 'Phiên đăng nhập đã hết hạn') }
    return { status: 404, body: errorBody('NOT_FOUND', 'Not Found') }
  })
}

async function fillAndSubmit(password: string) {
  await userEvent.type(await screen.findByLabelText('Tên đăng nhập'), 'pc1_cg') // Web Admin tải lazy (BUG-ST-02)
  await userEvent.type(screen.getByLabelText('Mật khẩu'), password)
  await userEvent.click(screen.getByRole('button', { name: 'Đăng nhập' }))
}

describe('F0-FE-01..06 A01 – Đăng nhập nhân viên (UC08)', () => {
  it.each([
    ['BARISTA', '/admin/bar'],
    ['CASHIER', '/admin/bar'],
    ['MANAGER', '/admin/dashboard'],
    ['ADMIN', '/admin/dashboard'],
  ] as const)('F0-FE-01 %s đăng nhập -> màn hình mặc định %s', async (role, path) => {
    authBackend(role)
    renderApp('/admin/login')
    await fillAndSubmit('dung')
    // Chuyển trang sau đăng nhập là bất đồng bộ: chờ tới khi URL đổi (trước đây kiểm tra ngay → chập chờn khi máy bận)
    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent(path))
    expect(await screen.findByText(/Nguyễn Văn B/)).toBeInTheDocument()
    expect(loadSession()?.token).toBe('tok')
  })

  it('F0-FE-02 sai mật khẩu: hiện thông báo, không lưu phiên', async () => {
    authBackend()
    renderApp('/admin/login')
    await fillAndSubmit('sai')
    expect(await screen.findByRole('alert')).toHaveTextContent('Tên đăng nhập hoặc mật khẩu không đúng')
    expect(loadSession()).toBeNull()
  })

  it('F0-FE-03 chưa đăng nhập mà vào trang admin -> chuyển về đăng nhập', async () => {
    authBackend()
    renderApp('/admin/bar')
    expect(await screen.findByRole('button', { name: 'Đăng nhập' })).toBeInTheDocument()
    expect(screen.getByTestId('location')).toHaveTextContent('/admin/login')
  })

  it('F0-FE-04 token hết hạn phía server -> xóa phiên, về đăng nhập', async () => {
    authBackend('BARISTA', 401)
    saveSession('old', staffOf('BARISTA'), 3600)
    renderApp('/admin/bar')
    expect(await screen.findByRole('button', { name: 'Đăng nhập' })).toBeInTheDocument()
    expect(loadSession()).toBeNull()
  })

  it('F0-FE-05 phiên hết hạn phía client (quá 8 giờ) bị bỏ qua', () => {
    saveSession('old', staffOf('ADMIN'), -1)
    expect(loadSession()).toBeNull()
  })

  it('F0-FE-06 đăng xuất xóa phiên', async () => {
    authBackend('ADMIN')
    saveSession('tok', staffOf('ADMIN'), 3600)
    renderApp('/admin/dashboard')
    await userEvent.click(await screen.findByRole('button', { name: 'Đăng xuất' }))
    expect(screen.getByTestId('location')).toHaveTextContent('/admin/login')
    expect(loadSession()).toBeNull()
  })
})
