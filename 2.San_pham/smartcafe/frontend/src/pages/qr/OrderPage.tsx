import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import type { ApiError } from '../../api/client'
import { getOrder, type ItemStatus, type OrderStatus, type OrderView } from '../../api/orders'
import { useOrderSocket, type WsMessage } from '../../hooks/useOrderSocket'
import { formatVND } from '../../lib/format'
import QrHeader from './QrHeader'

const STEPS: { label: string; reached: OrderStatus[] }[] = [
  { label: 'Đang chờ', reached: ['PAID', 'PREPARING', 'READY', 'COMPLETED'] },
  { label: 'Đang pha chế', reached: ['PREPARING', 'READY', 'COMPLETED'] },
  { label: 'Có thể lấy', reached: ['READY', 'COMPLETED'] },
]

const ITEM_LABEL: Record<ItemStatus, string> = {
  WAITING: 'Đang chờ',
  PREPARING: 'Đang pha',
  DONE: '✔ Xong',
  CANCELLED: 'Đã hủy',
}

const isOrderView = (d: Record<string, unknown>): d is OrderView & Record<string, unknown> =>
  typeof d.order_code === 'string' && Array.isArray(d.items)

/** W03 – Theo dõi trạng thái đơn (UC06), cập nhật realtime qua WebSocket. */
export default function OrderPage() {
  const { orderId = '0' } = useParams()
  const [search] = useSearchParams()
  const token = search.get('token') ?? ''
  const id = Number(orderId)
  const [order, setOrder] = useState<OrderView | null>(null)
  const [error, setError] = useState<ApiError | null>(null)
  const prevStatus = useRef<OrderStatus | null>(null)

  const refresh = useCallback(() => {
    getOrder(id, token)
      .then(setOrder)
      .catch((e: ApiError) => setError(e))
  }, [id, token])

  useEffect(refresh, [refresh])

  const connected = useOrderSocket(id, token, (msg: WsMessage) => {
    // Sự kiện mang đủ dữ liệu đơn thì dùng luôn; QUEUE_POSITION chỉ cập nhật vị trí; còn lại tải lại qua REST
    if (isOrderView(msg.data)) setOrder(msg.data)
    else if (msg.type === 'QUEUE_POSITION' && typeof msg.data.queue_position === 'number') {
      const pos = msg.data.queue_position
      setOrder((o) => (o ? { ...o, queue_position: pos } : o))
    } else refresh()
  })

  // Đơn vừa chuyển sang "Có thể lấy": rung điện thoại (UC06 bước 3)
  useEffect(() => {
    if (order?.status === 'READY' && prevStatus.current && prevStatus.current !== 'READY') {
      navigator.vibrate?.([200, 100, 200])
    }
    prevStatus.current = order?.status ?? null
  }, [order?.status])

  if (error) {
    return (
      <div className="mx-auto min-h-screen max-w-md">
        <QrHeader />
        <p role="alert" className="p-6 text-center">
          {error.message}
        </p>
      </div>
    )
  }
  if (!order) return <p className="p-6 text-center text-coffee">Đang tải đơn hàng...</p>

  const s = order.status
  return (
    <div className="mx-auto min-h-screen max-w-md pb-8">
      <QrHeader />
      <main className="space-y-3 p-4">
        {/* Số bàn đã có trên thanh tiêu đề (QrHeader) */}
        <h1 className="text-xl font-bold text-coffee">Đơn #{order.order_code}</h1>

        {!connected && (
          <p className="text-xs text-amber-700" data-testid="reconnecting">
            Đang kết nối lại để cập nhật trạng thái...
          </p>
        )}

        {s === 'PENDING_PAYMENT' && (
          <p className="rounded-xl bg-amber-50 p-3 text-amber-800">Đơn chưa được thanh toán.</p>
        )}
        {s === 'CANCELLED' && (
          <div role="alert" className="rounded-xl bg-red-50 p-3 text-red-700">
            <p className="font-semibold">Đơn đã hủy – đã hoàn tiền</p>
            {order.cancel_reason && <p className="text-sm">Lý do: {order.cancel_reason}</p>}
          </div>
        )}
        {s === 'READY' && (
          <div role="alert" className="rounded-xl bg-green-600 p-4 font-semibold text-white">
            Đồ uống đã sẵn sàng – mời bạn đến quầy nhận
          </div>
        )}
        {s === 'COMPLETED' && (
          <div className="rounded-xl bg-stone-100 p-3 font-medium">
            <p>Bạn đã nhận đồ. Cảm ơn bạn!</p>
            {order.points_earned != null && order.points_earned > 0 && (
              <p className="text-coffee" data-testid="points-earned">
                Bạn được cộng {order.points_earned} điểm tích lũy.
              </p>
            )}
          </div>
        )}

        {order.paid_at && s !== 'CANCELLED' && (
          <p className="font-semibold text-green-700">✔ Thanh toán thành công – {formatVND(order.total)}</p>
        )}

        {s !== 'CANCELLED' && s !== 'PENDING_PAYMENT' && (
          <ol className="flex items-center justify-between rounded-xl bg-white p-3 text-sm shadow-sm" aria-label="Tiến trình">
            {STEPS.map((step) => {
              const done = step.reached.includes(s)
              return (
                <li key={step.label} aria-current={done ? 'step' : undefined} className="flex items-center gap-1">
                  <span className={`inline-block h-3 w-3 rounded-full ${done ? 'bg-coffee' : 'border border-stone-400'}`} />
                  <span className={done ? 'font-semibold text-coffee' : 'text-stone-500'}>{step.label}</span>
                </li>
              )
            })}
          </ol>
        )}

        {order.queue_position && (
          <p className="text-sm italic">Bạn đang ở vị trí thứ {order.queue_position} trong hàng đợi pha chế.</p>
        )}

        <table className="w-full overflow-hidden rounded-xl bg-white text-sm shadow-sm">
          <thead className="bg-coffee/10 text-left">
            <tr>
              <th className="p-2">Món</th>
              <th className="p-2 text-right">Trạng thái</th>
            </tr>
          </thead>
          <tbody>
            {order.items.map((i) => (
              <tr key={i.id} className="border-t border-stone-100">
                <td className="p-2">
                  {i.name} ×{i.quantity}
                  {i.note && <span className="block text-xs text-stone-500">{i.note}</span>}
                </td>
                <td className="p-2 text-right">{ITEM_LABEL[i.status]}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {(s === 'PAID' || s === 'PREPARING') && (
          <p className="text-sm italic text-stone-600">Bạn sẽ nhận thông báo khi đồ uống sẵn sàng.</p>
        )}

        <Link
          to="../../menu"
          relative="path"
          className="block rounded-xl border-2 border-coffee py-3 text-center font-semibold text-coffee"
        >
          Gọi thêm món
        </Link>
      </main>
    </div>
  )
}
