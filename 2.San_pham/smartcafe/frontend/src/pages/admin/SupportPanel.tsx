import { useCallback, useEffect, useState, type FormEvent } from 'react'
import type { ApiError } from '../../api/client'
import type { OrderStatus } from '../../api/orders'
import { cancelOrder, searchOrders, type SupportOrder } from '../../api/support'
import { formatTime, formatVND } from '../../lib/format'

export const REASON_MIN = 5
const QUICK_REASONS = ['Khách gọi nhầm món', 'Khách đổi ý', 'Hết nguyên liệu', 'Khách phải đi gấp']

const STATUS_LABEL: Record<OrderStatus, string> = {
  PENDING_PAYMENT: 'Chờ thanh toán',
  PAID: 'Đang chờ',
  PREPARING: 'Đang pha',
  READY: 'Có thể lấy',
  COMPLETED: 'Đã giao',
  CANCELLED: 'Đã hủy',
}

/** UC20 – Thu ngân (và quản lý chi nhánh) hỗ trợ khách: tra cứu đơn theo mã / bàn, hủy đơn & hoàn tiền giả lập.
 *  `refreshKey` tăng mỗi khi màn hình Bar nhận sự kiện realtime để danh sách luôn mới. */
export default function SupportPanel({ token, refreshKey, onCancelled }: {
  token: string
  refreshKey: number
  onCancelled: () => void
}) {
  const [code, setCode] = useState('')
  const [table, setTable] = useState('')
  const [filter, setFilter] = useState({ code: '', table: '' })
  const [orders, setOrders] = useState<SupportOrder[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [target, setTarget] = useState<SupportOrder | null>(null)

  const load = useCallback(async () => {
    try {
      setOrders(await searchOrders(token, filter.code, filter.table))
    } catch (e) {
      setError((e as ApiError).message)
    }
  }, [token, filter])

  useEffect(() => {
    void load()
  }, [load, refreshKey])

  const submit = (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setFilter({ code, table })
  }

  const done = (o: SupportOrder) => {
    setTarget(null)
    // Cập nhật ngay dòng vừa hủy từ kết quả trả về, không đợi tải lại (BUG-F5-01: tránh còn nút "Hủy đơn")
    setOrders((list) => list?.map((x) => (x.id === o.id ? o : x)) ?? list)
    setNotice(`Đã hủy đơn ${o.order_code} và hoàn ${formatVND(o.total)} cho khách (giả lập).`)
    onCancelled()
    void load()
  }

  return (
    <section className="space-y-3 rounded-2xl bg-white p-4 shadow-sm" aria-label="Hỗ trợ khách">
      <h2 className="font-semibold">Hỗ trợ khách – tra cứu & hủy đơn</h2>
      <form onSubmit={submit} className="flex flex-wrap items-end gap-2">
        <label className="text-sm">
          <span className="block">Mã đơn</span>
          <input value={code} onChange={(e) => setCode(e.target.value)} maxLength={20} placeholder="VD: 0142"
            className="w-36 rounded-lg border border-stone-300 px-2 py-1" />
        </label>
        <label className="text-sm">
          <span className="block">Bàn</span>
          <input value={table} onChange={(e) => setTable(e.target.value)} maxLength={10} placeholder="VD: 05"
            className="w-20 rounded-lg border border-stone-300 px-2 py-1" />
        </label>
        <button type="submit" className="rounded-lg bg-coffee px-4 py-1.5 font-semibold text-white">Tìm</button>
        <span className="text-xs text-stone-500">Để trống để xem đơn trong ngày và đơn còn tồn.</span>
      </form>
      {error && <p role="alert" className="rounded-lg bg-red-50 p-2 text-sm text-red-700">{error}</p>}
      {notice && <p role="status" className="rounded-lg bg-green-50 p-2 text-sm text-green-800">{notice}</p>}

      {orders === null ? (
        <p className="text-sm">Đang tải...</p>
      ) : orders.length === 0 ? (
        <p className="text-sm text-stone-500">Không tìm thấy đơn phù hợp.</p>
      ) : (
        <ul className="space-y-2">
          {orders.map((o) => (
            <li key={o.id} data-testid={`support-${o.id}`} className="rounded-xl border border-stone-200 p-3 text-sm">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="font-bold">
                  {o.order_code} · Bàn {o.table_number}
                  <span className="ml-2 rounded bg-stone-100 px-2 py-0.5 text-xs font-semibold">{STATUS_LABEL[o.status]}</span>
                  {o.is_member && <span className="ml-2 text-xs font-normal text-coffee">(thành viên)</span>}
                </p>
                <p>
                  {o.paid_at && <span className="mr-2 text-stone-500">{formatTime(o.paid_at, new Date().toISOString())}</span>}
                  <b>{formatVND(o.total)}</b>
                </p>
              </div>
              <p className="text-stone-700">{o.items.map((i) => `${i.name} ×${i.quantity}`).join(', ')}</p>
              {o.status === 'CANCELLED' && (
                <p className="text-red-700">
                  Đã hủy{o.cancelled_by ? ` bởi ${o.cancelled_by}` : ''} – Lý do: {o.cancel_reason}
                  {o.payment?.status === 'REFUNDED' && ' – đã hoàn tiền'}
                </p>
              )}
              {o.can_cancel && (
                <button onClick={() => { setNotice(null); setTarget(o) }} aria-label={`Hủy đơn ${o.order_code}`}
                  className="mt-2 rounded border border-red-600 px-3 py-1 font-semibold text-red-700">
                  Hủy đơn
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
      {target && <CancelDialog order={target} token={token} onClose={() => setTarget(null)} onDone={done} />}
    </section>
  )
}

function CancelDialog({ order, token, onClose, onDone }: {
  order: SupportOrder
  token: string
  onClose: () => void
  onDone: (o: SupportOrder) => void
}) {
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const ok = reason.trim().length >= REASON_MIN

  const confirm = async () => {
    setBusy(true)
    setError(null)
    try {
      onDone(await cancelOrder(order.id, reason.trim(), token))
    } catch (e) {
      setError((e as ApiError).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 z-30 flex items-center justify-center bg-black/40 p-4">
      <div role="dialog" aria-modal="true" aria-label={`Hủy đơn ${order.order_code}`}
        className="w-full max-w-md space-y-3 rounded-2xl bg-white p-5">
        <h3 className="text-lg font-bold">Hủy đơn {order.order_code} – Bàn {order.table_number}</h3>
        <p className="text-sm">
          Hệ thống sẽ hoàn <b>{formatVND(order.total)}</b> cho khách (giả lập) và xóa các món khỏi hàng đợi Bar.
        </p>
        <div className="flex flex-wrap gap-1">
          {QUICK_REASONS.map((r) => (
            <button key={r} type="button" onClick={() => setReason(r)}
              className="rounded-full border border-stone-300 px-2 py-0.5 text-xs">{r}</button>
          ))}
        </div>
        <label className="block text-sm">
          <span className="block font-medium">Lý do hủy (bắt buộc)</span>
          <textarea value={reason} onChange={(e) => setReason(e.target.value)} maxLength={255} rows={2}
            className="w-full rounded-lg border border-stone-300 p-2" />
        </label>
        {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className="rounded-lg border px-4 py-2">Đóng</button>
          <button type="button" onClick={confirm} disabled={!ok || busy}
            className="rounded-lg bg-red-700 px-4 py-2 font-semibold text-white disabled:opacity-50">
            {busy ? 'Đang hủy...' : 'Xác nhận hủy & hoàn tiền'}
          </button>
        </div>
      </div>
    </div>
  )
}
