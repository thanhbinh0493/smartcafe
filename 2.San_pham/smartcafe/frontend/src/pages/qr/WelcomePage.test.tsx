import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { qrBackend, renderApp } from '../../test/utils'

describe('F1-FE-03..06 W00 – Màn hình chào (UC01)', () => {
  it('F1-FE-03 QR hợp lệ: hiện chi nhánh, bàn và 2 lựa chọn', async () => {
    qrBackend()
    renderApp('/t/good')
    expect(await screen.findByText('Chào mừng bạn đến SmartCafe!')).toBeInTheDocument()
    expect(screen.getByText('SmartCafe Cầu Giấy')).toBeInTheDocument()
    expect(screen.getByText('Bàn 05')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Nhập số điện thoại' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Xem menu ngay' })).toBeInTheDocument()
  })

  it('F1-FE-04 chọn "Xem menu ngay" -> chuyển sang menu ẩn danh', async () => {
    qrBackend()
    renderApp('/t/good')
    await userEvent.click(await screen.findByRole('button', { name: 'Xem menu ngay' }))
    expect(screen.getByTestId('location')).toHaveTextContent('/t/good/menu')
    expect(await screen.findByText('Cà phê sữa đá')).toBeInTheDocument()
  })

  it('F1-FE-05 chọn "Nhập số điện thoại" -> chuyển sang màn hình thành viên', async () => {
    qrBackend()
    renderApp('/t/good')
    await userEvent.click(await screen.findByRole('button', { name: 'Nhập số điện thoại' }))
    expect(screen.getByTestId('location')).toHaveTextContent('/t/good/otp')
  })

  it('F1-FE-06 QR sai: báo "Mã QR không hợp lệ, vui lòng gọi nhân viên"', async () => {
    qrBackend()
    renderApp('/t/bad-token')
    expect(await screen.findByRole('alert')).toHaveTextContent('Mã QR không hợp lệ, vui lòng gọi nhân viên')
    expect(screen.queryByRole('button', { name: 'Xem menu ngay' })).not.toBeInTheDocument()
  })

  it('F1-FE-17 mất mạng khi quét QR: báo không kết nối được máy chủ', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
    renderApp('/t/good')
    expect(await screen.findByRole('alert')).toHaveTextContent('Không kết nối được máy chủ, vui lòng thử lại')
    expect(screen.getByText('Có lỗi xảy ra')).toBeInTheDocument()
  })

  it('F1-FE-07 không lưu định danh khách trên thiết bị (NFR-S7)', async () => {
    qrBackend()
    renderApp('/t/good')
    await userEvent.click(await screen.findByRole('button', { name: 'Xem menu ngay' }))
    await screen.findByText('Cà phê sữa đá')
    expect(localStorage.length).toBe(0)
    expect(document.cookie).toBe('')
  })
})
