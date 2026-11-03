import { useEffect, useMemo, useState } from 'react'
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { listBranches, type AdminBranch } from '../../api/admin'
import type { ApiError } from '../../api/client'
import { getDashboard, rebuildReport, type Dashboard } from '../../api/report'
import { formatVND } from '../../lib/format'
import { Alert, btnLight, PageHeader, tableCls, useStaff, useToken } from './ui'

const COLORS = ['#6f4e37', '#ea580c', '#2563eb', '#16a34a', '#7c3aed']
const DAY_MS = 86_400_000

/** Ngày theo giờ Việt Nam dạng YYYY-MM-DD, lùi `back` ngày so với hôm nay. */
export function vnDate(back = 0, now = Date.now()): string {
  return new Date(now + 7 * 3600_000 - back * DAY_MS).toISOString().slice(0, 10)
}
export const dm = (iso: string) => `${iso.slice(8, 10)}/${iso.slice(5, 7)}`

export function formatWait(sec: number | null): string {
  if (sec === null) return '–'
  const m = Math.floor(sec / 60)
  return `${m} phút ${String(sec % 60).padStart(2, '0')}s`
}

const pct = (r: number) => `${(r * 100).toFixed(1).replace('.', ',')}%`

/** Thay đổi so với ngày trước: % với tiền / số đơn; điểm % với tỉ lệ; mm:ss với thời gian chờ. */
export function delta(kind: 'amount' | 'ratio' | 'wait', cur: number | null, prev: number | null | undefined): string | null {
  if (cur === null || prev === null || prev === undefined) return null
  if (kind === 'ratio') {
    const d = (cur - prev) * 100
    return `${d >= 0 ? '+' : ''}${d.toFixed(1).replace('.', ',')} điểm %`
  }
  if (kind === 'wait') {
    const d = cur - prev
    const a = Math.abs(d)
    return `${d >= 0 ? '+' : '-'}${Math.floor(a / 60)}:${String(a % 60).padStart(2, '0')}`
  }
  if (prev === 0) return cur === 0 ? '0%' : null
  const d = ((cur - prev) / prev) * 100
  return `${d >= 0 ? '+' : ''}${d.toFixed(1).replace('.', ',')}%`
}

/** Màu xu hướng: xanh = tốt hơn, đỏ = xấu hơn. Thời gian chờ giảm là tốt (BUG-F8-01: trước đây tô ngược). */
export function trendClass(d: string, lowerIsBetter = false): string {
  if (/^[+-]?0(,0)?(%| điểm %|:00)$/.test(d)) return 'text-stone-500'
  const up = !d.startsWith('-')
  return up !== lowerIsBetter ? 'text-green-700' : 'text-red-600'
}

/** Dữ liệu biểu đồ: mỗi ngày 1 điểm, mỗi chi nhánh 1 cột giá trị (tên cột = mã chi nhánh). */
export function chartData(d: Dashboard, codeOf: Map<number, string>) {
  const days = new Map<string, Record<string, number | string>>()
  for (const p of d.series) {
    const row = days.get(p.report_date) ?? { day: dm(p.report_date) }
    row[codeOf.get(p.branch_id) ?? String(p.branch_id)] = p.revenue
    days.set(p.report_date, row)
  }
  return [...days.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([, v]) => v)
}

/** W08 – Dashboard bán hàng (UC16): số liệu tổng hợp hằng ngày lúc 00:05, không có số liệu realtime trong ngày. */
export default function DashboardPage() {
  const staff = useStaff()
  const token = useToken()
  const isAdmin = staff.role === 'ADMIN'
  const [branches, setBranches] = useState<AdminBranch[]>([])
  const [branchId, setBranchId] = useState<number | null>(isAdmin ? null : (staff.branch?.id ?? null))
  const [days, setDays] = useState(7)
  const [data, setData] = useState<Dashboard | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [reload, setReload] = useState(0)

  useEffect(() => {
    listBranches(token).then(setBranches).catch(() => setBranches([]))
  }, [token])

  useEffect(() => {
    setError(null)
    getDashboard(token, { branchId, from: vnDate(days), to: vnDate(1) })
      .then(setData)
      .catch((e: ApiError) => setError(e.message))
  }, [token, branchId, days, reload])

  const codeOf = useMemo(() => new Map(branches.map((b) => [b.id, b.code])), [branches])
  const lines = useMemo(
    () => [...new Set((data?.series ?? []).map((p) => p.branch_id))].map((id) => codeOf.get(id) ?? String(id)),
    [data, codeOf],
  )

  const colorOf = (code: string, i: number) => {
    const idx = branches.findIndex((b) => b.code === code)
    return COLORS[(idx >= 0 ? idx : i) % COLORS.length]
  }

  const rebuild = async () => {
    setNotice(null)
    try {
      const r = await rebuildReport(token, vnDate(1))
      setNotice(`Đã tính lại báo cáo ngày ${dm(r.report_date)} cho ${r.branches} chi nhánh.`)
      setReload((x) => x + 1)
    } catch (e) {
      setError((e as ApiError).message)
    }
  }

  const k = data?.latest
  const p = data?.previous
  const cards: { label: string; value: string; d: string | null; lowerIsBetter?: boolean }[] = k
    ? [
        { label: 'Doanh thu', value: formatVND(k.revenue), d: delta('amount', k.revenue, p?.revenue) },
        { label: 'Số đơn', value: String(k.order_count), d: delta('amount', k.order_count, p?.order_count) },
        { label: 'Giá trị TB/đơn', value: formatVND(k.avg_order_value), d: delta('amount', k.avg_order_value, p?.avg_order_value) },
        { label: 'Thời gian chờ TB', value: formatWait(k.avg_wait_seconds), d: delta('wait', k.avg_wait_seconds, p?.avg_wait_seconds), lowerIsBetter: true },
        { label: 'Đơn thành viên', value: pct(k.member_order_ratio), d: delta('ratio', k.member_order_ratio, p?.member_order_ratio) },
        { label: 'Món từ gợi ý AI', value: pct(k.recommended_item_ratio), d: delta('ratio', k.recommended_item_ratio, p?.recommended_item_ratio) },
        { label: 'Doanh thu KM', value: formatVND(k.promo_revenue), d: delta('amount', k.promo_revenue, p?.promo_revenue) },
        { label: 'Đơn hủy', value: String(k.cancelled_count), d: null },
      ]
    : []

  return (
    <section className="space-y-4">
      <div className="rounded-2xl bg-white p-5 shadow-sm">
        <PageHeader title="Báo cáo bán hàng">
          {isAdmin ? (
            <select aria-label="Chi nhánh" value={branchId ?? ''} className={btnLight}
              onChange={(e) => setBranchId(e.target.value ? Number(e.target.value) : null)}>
              <option value="">Tất cả chi nhánh</option>
              {branches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
            </select>
          ) : (
            <span className="text-sm font-semibold">{staff.branch?.name}</span>
          )}
          <select aria-label="Khoảng thời gian" value={days} onChange={(e) => setDays(Number(e.target.value))} className={btnLight}>
            <option value={7}>7 ngày qua</option>
            <option value={30}>30 ngày qua</option>
          </select>
          {isAdmin && <button className={btnLight} onClick={rebuild}>Tính lại hôm qua</button>}
        </PageHeader>
        <p className="text-xs italic text-stone-500">
          Tự động tổng hợp lúc 00:05 hằng ngày, chỉ gồm các ngày đã kết thúc (không có số liệu trong ngày hôm nay).
          {data?.generated_at && ` Cập nhật lần cuối: ${new Date(data.generated_at).toLocaleString('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh' })}.`}
        </p>
      </div>
      {error && <Alert>{error}</Alert>}
      {notice && <Alert kind="ok">{notice}</Alert>}
      {!data && !error && <p>Đang tải...</p>}
      {data && !k && <p className="rounded-2xl bg-white p-5 text-stone-500 shadow-sm">Chưa có báo cáo trong khoảng này.</p>}

      {data && k && (
        <>
          <div className="rounded-2xl bg-white p-5 shadow-sm">
            <h2 className="mb-3 font-semibold">Ngày {dm(data.latest_date!)} (so với ngày trước)</h2>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4" aria-label="Chỉ số ngày gần nhất">
              {cards.map((c) => (
                <div key={c.label} className="rounded-xl border border-stone-200 p-3" data-testid={`kpi-${c.label}`}>
                  <p className="text-xs text-stone-500">{c.label}</p>
                  <p className="text-lg font-bold text-coffee">{c.value}</p>
                  {c.d && <p className={`text-xs ${trendClass(c.d, c.lowerIsBetter)}`}>{c.d}</p>}
                </div>
              ))}
            </div>
            <p className="mt-3 text-sm text-stone-600" data-testid="period">
              {days} ngày ({dm(data.from_date)} – {dm(data.to_date)}): doanh thu <b>{formatVND(data.period.revenue)}</b>,{' '}
              {data.period.order_count} đơn, {data.period.cancelled_count} đơn hủy, doanh thu KM {formatVND(data.period.promo_revenue)}.
            </p>
          </div>

          <div className="rounded-2xl bg-white p-5 shadow-sm">
            <h2 className="mb-3 font-semibold">Doanh thu theo ngày</h2>
            <div className="h-72" data-testid="revenue-chart">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData(data, codeOf)} margin={{ left: 20, right: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" />
                  <YAxis tickFormatter={(v: number) => `${Math.round(v / 1000)}k`} />
                  <Tooltip formatter={(v: number) => formatVND(v)} />
                  <Legend />
                  {lines.map((code, i) => (
                    <Line key={code} type="monotone" dataKey={code} stroke={colorOf(code, i)} strokeWidth={2} dot={false}
                      isAnimationActive={false} />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-2xl bg-white p-5 shadow-sm">
              <h2 className="mb-3 font-semibold">So sánh chi nhánh ({dm(data.latest_date!)})</h2>
              <table className={tableCls} aria-label="So sánh chi nhánh">
                <thead><tr><th>Chi nhánh</th><th>Doanh thu</th><th>Số đơn</th><th>Hủy</th><th>Chờ TB</th></tr></thead>
                <tbody>
                  {data.branches.map((b) => (
                    <tr key={b.branch_id}>
                      <td>{b.name}</td><td>{formatVND(b.kpi.revenue)}</td><td>{b.kpi.order_count}</td>
                      <td>{b.kpi.cancelled_count}</td><td>{formatWait(b.kpi.avg_wait_seconds)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="rounded-2xl bg-white p-5 shadow-sm">
              <h2 className="mb-3 font-semibold">Top 5 món ({dm(data.latest_date!)})</h2>
              <table className={tableCls} aria-label="Top 5 món">
                <thead><tr><th>#</th><th>Món</th><th>SL</th></tr></thead>
                <tbody>
                  {data.top_items.map((t, i) => (
                    <tr key={t.menu_item_id}><td>{i + 1}</td><td>{t.name}</td><td>{t.qty}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </section>
  )
}
