import { useCallback, useEffect, useRef, useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import type { StaffMe } from '../../api/auth'
import {
  completeOrder,
  getQueue,
  getReadyOrders,
  itemAction,
  type BarOrder,
  type ItemAction,
  type QueueItem,
} from '../../api/bar'
import type { ApiError } from '../../api/client'
import { loadSession } from '../../auth/staffSession'
import { useSocket, type WsMessage } from '../../hooks/useOrderSocket'
import { playBeep, unlockAudio } from '../../lib/beep'
import { formatTime } from '../../lib/format'

export const UNDO_MS = 10_000 // nút "Hoàn tác" hiện 10 giây (UC18 – 3a)
const LATE_MS = 10 * 60_000 // món chờ quá 10 phút hiển thị màu đỏ
const TICK_MS = 15_000

interface UndoEntry {
  itemId: number
  label: string
}

/** W04 – Màn hình quầy Bar (UC17–UC19): hàng đợi pha chế + cột "Có thể lấy", cập nhật realtime.
 *  Pha chế / quản lý: Bắt đầu, Xong, Hoàn tác, Đã giao. Thu ngân: chỉ xem (tra cứu & hủy đơn ở F5). */
export default function BarPage() {
  const staff = useOutletContext<StaffMe>()
  if (!staff.branch) {
    return (
      <p className="rounded-2xl bg-white p-6 shadow-sm">
        Màn hình quầy Bar dành cho nhân viên chi nhánh. Tài khoản quản trị viên không gắn với chi nhánh nào.
      </p>
    )
  }
  return <BarScreen staff={staff} branchId={staff.branch.id} branchName={staff.branch.name} />
}

function BarScreen({ staff, branchId, branchName }: { staff: StaffMe; branchId: number; branchName: string }) {
  const token = loadSession()?.token ?? ''
  const canAct = staff.role === 'BARISTA' || staff.role === 'MANAGER'
  const [items, setItems] = useState<QueueItem[] | null>(null)
  const [ready, setReady] = useState<BarOrder[]>([])
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [busy, setBusy] = useState<Set<string>>(new Set())
  const [undos, setUndos] = useState<UndoEntry[]>([])
  const [now, setNow] = useState(Date.now())
  const clockOffset = useRef(0) // giờ server - giờ máy, để tính số phút đã chờ cho đúng

  const reload = useCallback(async () => {
    try {
      const [q, r] = await Promise.all([getQueue(branchId, token), getReadyOrders(branchId, token)])
      clockOffset.current = new Date(q.server_time).getTime() - Date.now()
      setItems(q.items)
      setReady(r)
      setNow(Date.now())
    } catch (e) {
      setError((e as ApiError).message)
    }
  }, [branchId, token])

  useEffect(() => {
    void reload()
    const t = setInterval(() => setNow(Date.now()), TICK_MS)
    return () => clearInterval(t)
  }, [reload])

  const connected = useSocket(
    `/ws/bar/${branchId}?token=${encodeURIComponent(token)}`,
    (msg: WsMessage) => {
      if (msg.type === 'QUEUE_ITEM_ADDED') {
        playBeep()
        setNotice(`Có món mới – đơn ${String(msg.data.order_code ?? '')}`)
      }
      void reload()
    },
    () => void reload(), // kết nối (lại) xong: tải lại để không lỡ sự kiện lúc mất mạng
  )

  const run = async (key: string, fn: () => Promise<void>) => {
    setBusy((b) => new Set(b).add(key))
    setError(null)
    try {
      await fn()
    } catch (e) {
      setError((e as ApiError).message)
    } finally {
      setBusy((b) => {
        const n = new Set(b)
        n.delete(key)
        return n
      })
      await reload()
    }
  }

  const act = (item: QueueItem, action: ItemAction) =>
    run(`i${item.id}`, async () => {
      await itemAction(item.id, action, token)
      if (action === 'done') {
        const entry = { itemId: item.id, label: `${item.name} ×${item.quantity} – bàn ${item.table_number}` }
        setUndos((u) => [...u, entry])
        setTimeout(() => setUndos((u) => u.filter((x) => x !== entry)), UNDO_MS)
      }
    })

  const undo = (entry: UndoEntry) =>
    run(`u${entry.itemId}`, async () => {
      setUndos((u) => u.filter((x) => x !== entry))
      await itemAction(entry.itemId, 'undo', token)
    })

  const deliver = (order: BarOrder) =>
    run(`o${order.id}`, async () => {
      const res = await completeOrder(order.id, token)
      setNotice(
        `Đã giao đơn ${order.order_code}` +
          (res.points_earned != null ? ` – khách thành viên được cộng ${res.points_earned} điểm` : ''),
      )
    })

  const waited = (paidAt: string) => Math.max(0, now + clockOffset.current - new Date(paidAt).getTime())
  const serverToday = new Date(now + clockOffset.current).toISOString()

  return (
    <div className="space-y-4" onClickCapture={unlockAudio}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-xl font-bold text-coffee">Hàng đợi pha chế – {branchName}</h1>
        <span className={`text-sm ${connected ? 'text-green-700' : 'text-amber-700'}`} data-testid="bar-connection">
          {connected ? '● Trực tuyến' : '● Đang kết nối lại...'}
        </span>
      </div>
      {!canAct && (
        <p className="rounded-xl bg-stone-100 p-3 text-sm">
          Chế độ xem: thu ngân chỉ xem hàng đợi, không thao tác Bắt đầu / Xong / Đã giao.
        </p>
      )}
      {error && (
        <p role="alert" className="rounded-xl bg-red-50 p-3 text-red-700">
          {error}
        </p>
      )}
      {notice && (
        <p role="status" className="rounded-xl bg-green-50 p-3 text-green-800">
          {notice}
        </p>
      )}
      {undos.length > 0 && (
        <ul className="space-y-1" aria-label="Hoàn tác">
          {undos.map((u) => (
            <li key={u.itemId} className="flex items-center gap-3 rounded-xl bg-stone-800 px-4 py-2 text-white">
              <span className="flex-1">Đã xong: {u.label}</span>
              <button
                onClick={() => undo(u)}
                disabled={busy.has(`u${u.itemId}`)}
                className="rounded border border-white px-3 py-1 font-semibold"
              >
                Hoàn tác
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="grid gap-4 lg:grid-cols-[1fr_20rem]">
        <section className="overflow-x-auto rounded-2xl bg-white shadow-sm">
          <h2 className="p-3 font-semibold">Chờ pha chế ({items?.length ?? 0} món)</h2>
          {items === null ? (
            <p className="p-3">Đang tải hàng đợi...</p>
          ) : items.length === 0 ? (
            <p className="p-3 text-stone-500">Không có món nào đang chờ.</p>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-coffee/10 text-left">
                <tr>
                  <th className="p-2">#</th>
                  <th className="p-2">Giờ gọi</th>
                  <th className="p-2">Chờ</th>
                  <th className="p-2">Bàn</th>
                  <th className="p-2">Mã đơn</th>
                  <th className="p-2">Món</th>
                  <th className="p-2">SL</th>
                  <th className="p-2">Ghi chú</th>
                  {canAct && <th className="p-2">Thao tác</th>}
                </tr>
              </thead>
              <tbody>
                {items.map((it, idx) => {
                  const w = waited(it.paid_at)
                  const late = w > LATE_MS
                  const newOrder = idx === 0 || items[idx - 1].order_id !== it.order_id
                  return (
                    <tr
                      key={it.id}
                      data-testid={`queue-row-${it.id}`}
                      data-late={late || undefined}
                      className={`${newOrder ? 'border-t-2 border-stone-300' : 'border-t border-stone-100'} ${late ? 'bg-red-50 text-red-700' : ''}`}
                    >
                      <td className="p-2">{idx + 1}</td>
                      <td className="p-2">{formatTime(it.paid_at, serverToday)}</td>
                      <td className="p-2">{Math.floor(w / 60_000)} phút</td>
                      <td className="p-2 font-semibold">{it.table_number}</td>
                      <td className="p-2">{it.order_code}</td>
                      <td className="p-2 font-medium">{it.name}</td>
                      <td className="p-2">{it.quantity}</td>
                      <td className="p-2">
                        {it.note}
                        {it.order_note && newOrder && <span className="block text-xs italic">Đơn: {it.order_note}</span>}
                      </td>
                      {canAct && (
                        <td className="p-2 whitespace-nowrap">
                          {it.status === 'WAITING' ? (
                            <button
                              onClick={() => act(it, 'start')}
                              disabled={busy.has(`i${it.id}`)}
                              aria-label={`Bắt đầu ${it.name} bàn ${it.table_number}`}
                              className="rounded bg-coffee px-3 py-1 font-semibold text-white disabled:opacity-50"
                            >
                              Bắt đầu
                            </button>
                          ) : (
                            <span className="flex items-center gap-2">
                              <span className="text-xs font-semibold text-amber-700">ĐANG PHA</span>
                              <button
                                onClick={() => act(it, 'done')}
                                disabled={busy.has(`i${it.id}`)}
                                aria-label={`Xong ${it.name} bàn ${it.table_number}`}
                                className="rounded bg-green-700 px-3 py-1 font-semibold text-white disabled:opacity-50"
                              >
                                Xong
                              </button>
                            </span>
                          )}
                        </td>
                      )}
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </section>

        <section className="space-y-2 rounded-2xl bg-white p-3 shadow-sm" aria-label="Có thể lấy">
          <h2 className="font-semibold">Có thể lấy ({ready.length})</h2>
          {ready.length === 0 && <p className="text-sm text-stone-500">Chưa có đơn nào.</p>}
          {ready.map((o) => (
            <article key={o.id} className="rounded-xl border border-green-600 p-3" data-testid={`ready-${o.id}`}>
              <p className="font-bold">
                {o.order_code} · Bàn {o.table_number}
                {o.is_member && <span className="ml-2 text-xs font-normal text-coffee">(thành viên)</span>}
              </p>
              <ul className="text-sm">
                {o.items.map((i) => (
                  <li key={i.id}>
                    {i.name} ×{i.quantity}
                  </li>
                ))}
              </ul>
              {canAct && (
                <button
                  onClick={() => deliver(o)}
                  disabled={busy.has(`o${o.id}`)}
                  aria-label={`Đã giao ${o.order_code}`}
                  className="mt-2 w-full rounded bg-green-700 py-2 font-semibold text-white disabled:opacity-50"
                >
                  Đã giao
                </button>
              )}
            </article>
          ))}
        </section>
      </div>
    </div>
  )
}
