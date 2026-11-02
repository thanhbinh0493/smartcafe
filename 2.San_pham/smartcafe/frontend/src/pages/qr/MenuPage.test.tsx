import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { errorBody, MENU, mockFetch, qrBackend, renderApp, TABLE } from '../../test/utils'

const openMenu = async () => {
  renderApp('/t/good/menu')
  await screen.findByText('Cà phê sữa đá')
}

describe('F1-FE-08..15 W01 – Menu điện tử (UC03)', () => {
  it('F1-FE-08 hiển thị danh mục và món theo thứ tự', async () => {
    qrBackend()
    await openMenu()
    const headings = screen.getAllByRole('heading', { level: 2 }).map((h) => h.textContent)
    expect(headings).toEqual(['Cà phê', 'Trà'])
  })

  it('F1-FE-09 món KM: giá gốc gạch ngang + giá bán', async () => {
    qrBackend()
    await openMenu()
    const row = screen.getByTestId('menu-item-11')
    expect(within(row).getByText('29.000đ').tagName).toBe('DEL')
    expect(within(row).getByText('25.000đ')).toBeInTheDocument()
    // món không KM chỉ có 1 giá
    const normal = screen.getByTestId('menu-item-22')
    expect(normal.querySelector('del')).toBeNull()
    expect(within(normal).getByText('35.000đ')).toBeInTheDocument()
  })

  it('F1-FE-10 nhãn MỚI và "Tạm hết"', async () => {
    qrBackend()
    await openMenu()
    expect(within(screen.getByTestId('menu-item-12')).getByText('MỚI')).toBeInTheDocument()
    const soldOut = screen.getByTestId('menu-item-13')
    expect(within(soldOut).getByText('Tạm hết')).toBeInTheDocument()
    expect(soldOut.className).toContain('opacity-50')
    expect(screen.getAllByText('MỚI')).toHaveLength(1)
    expect(screen.getAllByText('Tạm hết')).toHaveLength(1)
  })

  it('F1-FE-11 tab "Khuyến mãi" chỉ hiện món đang KM', async () => {
    qrBackend()
    await openMenu()
    await userEvent.click(screen.getByRole('button', { name: 'Khuyến mãi' }))
    expect(screen.getByText('Cà phê sữa đá')).toBeInTheDocument()
    expect(screen.getByText('Trà đào cam sả')).toBeInTheDocument()
    expect(screen.queryByText('Bạc xỉu dừa')).not.toBeInTheDocument()
    expect(screen.queryByText('Trà gừng mật ong')).not.toBeInTheDocument()
  })

  it('F1-FE-12 lọc theo danh mục', async () => {
    qrBackend()
    await openMenu()
    await userEvent.click(screen.getByRole('button', { name: 'Trà' }))
    expect(screen.queryByText('Cà phê sữa đá')).not.toBeInTheDocument()
    expect(screen.getByText('Trà gừng mật ong')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Tất cả' }))
    expect(screen.getByText('Cà phê sữa đá')).toBeInTheDocument()
  })

  it('F1-FE-13 tìm món không dấu; không có kết quả thì báo', async () => {
    qrBackend()
    await openMenu()
    const box = screen.getByRole('searchbox', { name: 'Tìm món' })
    await userEvent.type(box, 'bac xiu')
    expect(screen.getByText('Bạc xỉu dừa')).toBeInTheDocument()
    expect(screen.getByText('Bạc xỉu nóng')).toBeInTheDocument()
    expect(screen.queryByText('Cà phê sữa đá')).not.toBeInTheDocument()
    await userEvent.clear(box)
    await userEvent.type(box, 'pizza')
    expect(screen.getByText('Không tìm thấy món phù hợp.')).toBeInTheDocument()
  })

  it('F1-FE-14 không có món KM thì không hiện tab "Khuyến mãi"', async () => {
    const noPromo = {
      ...MENU,
      categories: MENU.categories.map((c) => ({
        ...c,
        items: c.items.map((i) => ({ ...i, is_promo: false, promotion_id: null, sell_price: i.regular_price })),
      })),
    }
    qrBackend(noPromo)
    await openMenu()
    expect(screen.queryByRole('button', { name: 'Khuyến mãi' })).not.toBeInTheDocument()
  })

  it('F1-FE-15 lỗi tải menu: báo lỗi và "Thử lại" tải lại thành công', async () => {
    let calls = 0
    mockFetch((url) => {
      if (url === '/api/public/tables/good') return { status: 200, body: TABLE }
      calls += 1
      return calls === 1
        ? { status: 500, body: errorBody('HTTP_ERROR', 'Máy chủ đang bận') }
        : { status: 200, body: MENU }
    })
    renderApp('/t/good/menu')
    expect(await screen.findByRole('alert')).toHaveTextContent('Máy chủ đang bận')
    await userEvent.click(screen.getByRole('button', { name: 'Thử lại' }))
    expect(await screen.findByText('Cà phê sữa đá')).toBeInTheDocument()
  })

  it('F1-FE-16 nút "Nhập SĐT tích điểm" trên menu', async () => {
    qrBackend()
    await openMenu()
    await userEvent.click(screen.getByRole('link', { name: 'Nhập SĐT tích điểm' }))
    expect(screen.getByTestId('location')).toHaveTextContent('/t/good/otp')
  })
})
