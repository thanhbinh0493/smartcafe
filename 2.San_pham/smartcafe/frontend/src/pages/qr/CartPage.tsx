import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import type { ApiError } from '../../api/client'
import { createOrder, payOrder, type CreatedOrder, type PaymentMethod, type PriceChange } from '../../api/orders'
import { getRecommendations, lastLog, recToMenuItem, rememberLog, type RecItem } from '../../api/recommend'
import { isSessionError, POINT_UNIT_VND, useMember } from '../../auth/MemberContext'
import { MAX_QTY, useCart } from '../../cart/CartContext'
import { formatVND } from '../../lib/format'
import QrHeader from './QrHeader'
import RecCards from './RecCards'
import { useQr } from './QrLayout'

/** W02 thể hiện popup "Đang xử lý…" khoảng 1,5 giây (thanh toán giả lập). */
export const PROCESSING_MS = import.meta.env.MODE === 'test' ? 0 : 1500
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))

type Notice = { kind: 'error' | 'warn'; text: string; relogin?: boolean } | null

/** W02 – Giỏ hàng & thanh toán giả lập (UC04, UC05, SD03). */
export default function CartPage() {
  const { qrToken, info } = useQr()
  const cart = useCart()
  const { member, expire } = useMember()
  const navigate = useNavigate()
  const [method, setMethod] = useState<PaymentMethod>('MOCK_EWALLET')
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState<Notice>(null)
  const [unavailable, setUnavailable] = useState<number[]>([])
  // Đơn đã tạo nhưng thanh toán thất bại: thử lại trên chính đơn này (UC05 – 5a)
  const [pending, setPending] = useState<CreatedOrder | null>(null)
  const [alsoBought, setAlsoBought] = useState<RecItem[]>([])

  // "Thường gọi kèm" theo món trong giỏ (luật kết hợp FP-Growth – F7); lỗi thì ẩn khối
  const cartKey = cart.lines.map((l) => l.menu_item_id).join(',')
  const memberToken = member?.token
  useEffect(() => {
    if (!cartKey) return setAlsoBought([])
    getRecommendations(info.branch.id, cartKey.split(',').map(Number), memberToken)
      .then((r) => {
        setAlsoBought(Array.isArray(r.also_bought) ? r.also_bought : [])
        rememberLog(qrToken, r.log_id)
      })
      .catch(() => setAlsoBought([]))
  }, [cartKey, info.branch.id, memberToken, qrToken])

  // Giỏ đã đổi thì lần thanh toán sau tạo đơn mới
  const changed = () => {
    setPending(null)
    setNotice(null)
  }
  const setQty = (id: number, q: number) => {
    cart.setQuantity(id, q)
    changed()
  }
  const remove = (id: number) => {
    cart.remove(id)
    changed()
  }

  if (cart.lines.length === 0) {
    return (
      <div className="mx-auto min-h-screen max-w-md">
        <QrHeader />
        <main className="space-y-4 p-6 text-center">
          <p className="text-stone-600">Giỏ hàng trống.</p>
          <Link to="../menu" relative="path" className="inline-block rounded-xl bg-coffee px-6 py-3 font-semibold text-white">
            Xem menu
          </Link>
        </main>
      </div>
    )
  }

  async function submit() {
    setBusy(true)
    setNotice(null)
    try {
      let order = pending
      if (!order) {
        order = await createOrder(
          {
          qr_token: qrToken,
          expected_total: cart.total,
          recommendation_log_id: lastLog(qrToken),
          items: cart.lines.map((l) => ({
            menu_item_id: l.menu_item_id,
            quantity: l.quantity,
            note: l.note.trim() || undefined,
            is_recommended: l.is_recommended,
          })),
          },
          member?.token,
        )
        setPending(order)
      }
      await sleep(PROCESSING_MS)
      await payOrder(order.order_id, order.access_token, method)
      cart.clear()
      navigate(`../orders/${order.order_id}?token=${encodeURIComponent(order.access_token)}`, { relative: 'path' })
    } catch (e) {
      const err = e as ApiError
      if (isSessionError(err.code, err.status)) {
        // Phiên thành viên hết hạn: không âm thầm đặt đơn ẩn danh, để khách chọn (UC06 – phiên thành viên)
        expire()
        setNotice({
          kind: 'warn',
          relogin: true,
          text: 'Phiên thành viên đã hết hạn (1 giờ). Bấm thanh toán lại để đặt món không tích điểm, hoặc nhập lại số điện thoại.',
        })
      } else if (err.code === 'ITEM_UNAVAILABLE') {
        setUnavailable((err.details.item_ids as number[]) ?? [])
        setNotice({ kind: 'error', text: err.message })
      } else if (err.code === 'PRICE_CHANGED') {
        cart.applyPrices((err.details.prices as PriceChange[]) ?? [])
        setNotice({ kind: 'warn', text: `${err.message}. Tổng mới: ${formatVND(err.details.total as number)}` })
      } else {
        setNotice({ kind: 'error', text: err.message })
      }
    } finally {
      setBusy(false)
    }
  }

  const discount = cart.subtotal - cart.total
  const blocked = cart.lines.some((l) => unavailable.includes(l.menu_item_id))

  return (
    <div className="mx-auto min-h-screen max-w-md pb-28">
      <QrHeader />
      <main className="space-y-3 p-4">
        <div className="flex items-center justify-between">
          {/* Số bàn đã có trên thanh tiêu đề (QrHeader) */}
          <h1 className="text-xl font-bold text-coffee">Giỏ hàng</h1>
          <Link to="../menu" relative="path" className="text-sm font-medium text-coffee underline">
            Thêm món
          </Link>
        </div>

        <ul className="space-y-2">
          {cart.lines.map((l) => {
            const soldOut = unavailable.includes(l.menu_item_id)
            return (
              <li
                key={l.menu_item_id}
                data-testid={`cart-line-${l.menu_item_id}`}
                className={`space-y-2 rounded-xl bg-white p-3 shadow-sm ${soldOut ? 'ring-2 ring-red-500' : ''}`}
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="font-medium">
                    {l.name}
                    {soldOut && <span className="ml-2 text-sm text-red-600">Tạm hết</span>}
                  </p>
                  <p className="text-right text-sm">
                    {l.is_promo && <del className="mr-1 text-stone-400">{formatVND(l.regular_price * l.quantity)}</del>}
                    <span className="font-semibold">{formatVND(l.sell_price * l.quantity)}</span>
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    aria-label={`Bớt ${l.name}`}
                    onClick={() => setQty(l.menu_item_id, l.quantity - 1)}
                    className="h-8 w-8 rounded-full border border-coffee text-coffee"
                  >
                    −
                  </button>
                  <span aria-label={`Số lượng ${l.name}`} className="w-6 text-center font-semibold">
                    {l.quantity}
                  </span>
                  <button
                    aria-label={`Thêm ${l.name}`}
                    onClick={() => setQty(l.menu_item_id, l.quantity + 1)}
                    disabled={l.quantity >= MAX_QTY}
                    className="h-8 w-8 rounded-full border border-coffee text-coffee disabled:opacity-40"
                  >
                    +
                  </button>
                  <input
                    aria-label={`Ghi chú ${l.name}`}
                    placeholder="Ghi chú: ít đá, ít đường..."
                    value={l.note}
                    maxLength={255}
                    onChange={(e) => {
                      cart.setNote(l.menu_item_id, e.target.value)
                      changed()
                    }}
                    className="min-w-0 flex-1 rounded-lg border border-stone-300 px-2 py-1 text-sm outline-none focus:border-coffee"
                  />
                  <button onClick={() => remove(l.menu_item_id)} className="text-sm text-red-600">
                    Xóa
                  </button>
                </div>
              </li>
            )
          })}
        </ul>

        <RecCards title="Thường gọi kèm" testId="also-bought" items={alsoBought}
          onAdd={(r) => { cart.add(recToMenuItem(r), true); changed() }} />

        <fieldset className="rounded-xl bg-white p-3 shadow-sm">
          <legend className="px-1 text-sm font-semibold">Phương thức thanh toán (giả lập)</legend>
          {(
            [
              ['MOCK_EWALLET', 'Ví điện tử'],
              ['MOCK_CARD', 'Thẻ ngân hàng'],
            ] as const
          ).map(([value, label]) => (
            <label key={value} className="flex items-center gap-2 py-1">
              <input type="radio" name="method" checked={method === value} onChange={() => setMethod(value)} />
              {label}
            </label>
          ))}
        </fieldset>

        <dl className="space-y-1 rounded-xl bg-white p-3 text-sm shadow-sm">
          <div className="flex justify-between">
            <dt>Tạm tính</dt>
            <dd>{formatVND(cart.subtotal)}</dd>
          </div>
          {discount > 0 && (
            <div className="flex justify-between text-promo">
              <dt>Khuyến mãi</dt>
              <dd>-{formatVND(discount)}</dd>
            </div>
          )}
          <div className="flex justify-between text-base font-bold">
            <dt>Tổng cộng</dt>
            <dd data-testid="cart-total">{formatVND(cart.total)}</dd>
          </div>
          {member && (
            <p className="pt-1 text-coffee" data-testid="cart-points">
              Bạn sẽ nhận +{Math.floor(cart.total / POINT_UNIT_VND)} điểm khi nhận đồ
            </p>
          )}
        </dl>

        {notice && (
          <p
            role="alert"
            className={`rounded-lg p-3 text-sm ${notice.kind === 'error' ? 'bg-red-50 text-red-700' : 'bg-amber-50 text-amber-800'}`}
          >
            {notice.text}
            {notice.relogin && (
              <Link to="../otp" relative="path" className="ml-1 font-semibold underline">
                Nhập lại SĐT
              </Link>
            )}
          </p>
        )}
      </main>

      <div className="fixed inset-x-0 bottom-0 z-20 mx-auto max-w-md p-3">
        <button
          onClick={submit}
          disabled={busy || blocked}
          className="w-full rounded-2xl bg-coffee py-4 font-semibold text-white shadow-lg disabled:opacity-50"
        >
          {pending ? 'Thử thanh toán lại' : 'Thanh toán & gửi đơn'} – {formatVND(cart.total)}
        </button>
      </div>

      {busy && (
        <div role="status" className="fixed inset-0 z-30 flex items-center justify-center bg-black/40">
          <div className="rounded-2xl bg-white px-8 py-6 text-center font-medium">Đang xử lý thanh toán...</div>
        </div>
      )}
    </div>
  )
}
