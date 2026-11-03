import { useEffect, useMemo, useState, type FormEvent } from 'react'
import {
  getBranchMenu, listBranches, listMenuItems, listPromotions, savePromotion,
  type PromoStatus, type Promotion,
} from '../../api/admin'
import type { ApiError } from '../../api/client'
import { formatVND } from '../../lib/format'
import { Alert, btnLight, btnPrimary, Field, inputCls, Modal, PageHeader, parseMoney, tableCls, useLoad, useToken } from './ui'

const TABS: { key: PromoStatus; label: string }[] = [
  { key: 'running', label: 'Đang chạy' },
  { key: 'upcoming', label: 'Sắp chạy' },
  { key: 'ended', label: 'Đã kết thúc' },
]

const pad = (n: number) => String(n).padStart(2, '0')
/** ISO → giá trị ô datetime-local theo giờ máy (máy quầy đặt giờ Việt Nam). */
export function toLocalInput(iso: string): string {
  const d = new Date(iso)
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}
const fmt = (iso: string) => {
  const d = new Date(iso)
  return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}
export const discountPercent = (current: number, promo: number) =>
  current > 0 && promo < current ? Math.round(((current - promo) * 100) / current) : 0

/** W07 – Khuyến mãi (UC15, chỉ Quản trị viên): 3 tab Đang chạy / Sắp chạy / Đã kết thúc + form tạo / sửa. */
export default function PromotionsPage() {
  const token = useToken()
  const [tab, setTab] = useState<PromoStatus>('running')
  const { data, error, reload } = useLoad(() => listPromotions(token, tab), [token, tab])
  const [editing, setEditing] = useState<Promotion | 'new' | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  return (
    <section className="rounded-2xl bg-white p-5 shadow-sm">
      <PageHeader title="Khuyến mãi">
        <button className={btnPrimary} onClick={() => { setNotice(null); setEditing('new') }}>+ Tạo chương trình</button>
      </PageHeader>
      <div role="tablist" className="mb-3 flex gap-2">
        {TABS.map((t) => (
          <button key={t.key} role="tab" aria-selected={tab === t.key} onClick={() => setTab(t.key)}
            className={`rounded-full px-4 py-1 text-sm ${tab === t.key ? 'bg-coffee font-semibold text-white' : 'bg-stone-100'}`}>
            {t.label}
          </button>
        ))}
      </div>
      {error && <Alert>{error}</Alert>}
      {notice && <Alert kind="ok">{notice}</Alert>}
      {!data ? (
        <p>Đang tải...</p>
      ) : data.length === 0 ? (
        <p className="text-sm text-stone-500">Không có chương trình nào.</p>
      ) : (
        <ul className="space-y-2">
          {data.map((p) => (
            <li key={p.id} className="rounded-xl border border-stone-200 p-3 text-sm" data-testid={`promo-${p.id}`}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="font-bold">
                  {p.name}
                  <span className="ml-2 rounded bg-stone-100 px-2 py-0.5 text-xs font-semibold">{p.branch_name ?? 'Toàn chuỗi'}</span>
                  {!p.is_active && <span className="ml-2 rounded bg-stone-300 px-2 py-0.5 text-xs">Đã tắt</span>}
                </p>
                <button className={btnLight} onClick={() => { setNotice(null); setEditing(p) }} aria-label={`${p.status === 'ended' ? 'Xem' : 'Sửa'} ${p.name}`}>
                  {p.status === 'ended' ? 'Xem' : 'Sửa'}
                </button>
              </div>
              <p className="text-stone-600">{fmt(p.start_at)} → {fmt(p.end_at)} · tạo bởi {p.created_by}</p>
              <p>{p.items.map((i) => `${i.name} ${formatVND(i.promo_price)} (-${i.discount_percent}%)`).join(' · ')}</p>
            </li>
          ))}
        </ul>
      )}
      {editing && (
        <PromotionForm token={token} promo={editing === 'new' ? null : editing} onClose={() => setEditing(null)}
          onSaved={(p) => { setEditing(null); setNotice(`Đã lưu chương trình "${p.name}".`); setTab(p.status); void reload() }} />
      )}
    </section>
  )
}

interface Line {
  menu_item_id: number
  name: string
  price: string
}

function PromotionForm({ token, promo, onClose, onSaved }: {
  token: string
  promo: Promotion | null
  onClose: () => void
  onSaved: (p: Promotion) => void
}) {
  const readOnly = promo?.status === 'ended'
  const branches = useLoad(() => listBranches(token), [token])
  const items = useLoad(() => listMenuItems(token), [token])
  const now = new Date()
  const [name, setName] = useState(promo?.name ?? '')
  const [description, setDescription] = useState(promo?.description ?? '')
  const [scope, setScope] = useState(promo?.branch_id ? String(promo.branch_id) : 'all')
  const [start, setStart] = useState(promo ? toLocalInput(promo.start_at) : toLocalInput(now.toISOString()))
  const [end, setEnd] = useState(promo ? toLocalInput(promo.end_at) : toLocalInput(new Date(now.getTime() + 7 * 86400_000).toISOString()))
  const [active, setActive] = useState(promo?.is_active ?? true)
  const [lines, setLines] = useState<Line[]>(
    promo?.items.map((i) => ({ menu_item_id: i.menu_item_id, name: i.name, price: String(i.promo_price) })) ?? [],
  )
  const [adding, setAdding] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [branchPrices, setBranchPrices] = useState<Record<number, number> | null>(null)

  // Giá bán hiện tại: KM 1 chi nhánh so với giá chi nhánh, KM toàn chuỗi so với giá chung (UC15)
  useEffect(() => {
    if (scope === 'all') return setBranchPrices(null)
    getBranchMenu(token, Number(scope))
      .then((rows) => setBranchPrices(Object.fromEntries(rows.map((r) => [r.menu_item_id, r.price_override ?? r.base_price]))))
      .catch(() => setBranchPrices(null))
  }, [scope, token])
  const currentPrice = useMemo(() => {
    const base = Object.fromEntries((items.data ?? []).map((m) => [m.id, m.base_price]))
    return (id: number): number | undefined => branchPrices?.[id] ?? base[id]
  }, [items.data, branchPrices])

  const addable = (items.data ?? []).filter((m) => m.is_active && !lines.some((l) => l.menu_item_id === m.id))
  const addLine = () => {
    const m = items.data?.find((x) => String(x.id) === adding)
    if (!m) return
    setLines([...lines, { menu_item_id: m.id, name: m.name, price: '' }])
    setAdding('')
  }

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return setError('Vui lòng nhập tên chương trình')
    if (!start || !end || new Date(end) <= new Date(start)) return setError('Thời gian kết thúc phải sau thời gian bắt đầu')
    if (lines.length === 0) return setError('Vui lòng thêm ít nhất 1 món')
    const parsed = lines.map((l) => ({ ...l, value: parseMoney(l.price) }))
    const bad = parsed.find((l) => l.value === null || Number.isNaN(l.value))
    if (bad) return setError(`Vui lòng nhập giá KM hợp lệ cho "${bad.name}"`)
    const tooHigh = parsed.find((l) => {
      const cur = currentPrice(l.menu_item_id)
      return cur !== undefined && (l.value as number) >= cur
    })
    if (tooHigh)
      return setError(`Giá KM của "${tooHigh.name}" phải nhỏ hơn giá bán hiện tại ${formatVND(currentPrice(tooHigh.menu_item_id) ?? 0)}`)
    setBusy(true)
    setError(null)
    try {
      onSaved(await savePromotion(token, {
        name, description: description || null, branch_id: scope === 'all' ? null : Number(scope),
        start_at: new Date(start).toISOString(), end_at: new Date(end).toISOString(), is_active: active,
        items: parsed.map((l) => ({ menu_item_id: l.menu_item_id, promo_price: l.value as number })),
      }, promo?.id))
    } catch (err) {
      setError((err as ApiError).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal title={promo ? (readOnly ? `Chương trình ${promo.name} (đã kết thúc)` : `Sửa ${promo.name}`) : 'Tạo chương trình khuyến mãi'} onClose={onClose}>
      <form onSubmit={submit} className="space-y-3">
        <fieldset disabled={readOnly} className="space-y-3">
          <Field label="Tên chương trình">
            <input className={inputCls} value={name} onChange={(e) => setName(e.target.value)} maxLength={100} />
          </Field>
          <Field label="Mô tả">
            <input className={inputCls} value={description} onChange={(e) => setDescription(e.target.value)} maxLength={255} />
          </Field>
          <Field label="Áp dụng tại">
            <select className={inputCls} value={scope} onChange={(e) => setScope(e.target.value)}>
              <option value="all">Toàn chuỗi</option>
              {branches.data?.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
            </select>
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Bắt đầu">
              <input className={inputCls} type="datetime-local" value={start} onChange={(e) => setStart(e.target.value)} />
            </Field>
            <Field label="Kết thúc">
              <input className={inputCls} type="datetime-local" value={end} onChange={(e) => setEnd(e.target.value)} />
            </Field>
          </div>
          <div>
            <p className="mb-1 text-sm font-medium">Món áp dụng</p>
            <table className={tableCls}>
              <thead><tr><th>Món</th><th>Giá bán hiện tại</th><th>Giá khuyến mãi</th><th>Giảm</th><th></th></tr></thead>
              <tbody>
                {lines.map((l, idx) => {
                  const cur = currentPrice(l.menu_item_id)
                  const v = parseMoney(l.price)
                  return (
                    <tr key={l.menu_item_id}>
                      <td>{l.name}</td>
                      <td>{cur !== undefined ? formatVND(cur) : '–'}</td>
                      <td>
                        <input aria-label={`Giá KM ${l.name}`} inputMode="numeric" className={`${inputCls} w-28`} value={l.price}
                          onChange={(e) => setLines(lines.map((x, i) => (i === idx ? { ...x, price: e.target.value } : x)))} />
                      </td>
                      <td>{cur !== undefined && v !== null && !Number.isNaN(v) ? `${discountPercent(cur, v)}%` : ''}</td>
                      <td>
                        <button type="button" className={btnLight} aria-label={`Bỏ ${l.name}`}
                          onClick={() => setLines(lines.filter((_, i) => i !== idx))}>Xóa</button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
            <div className="mt-2 flex gap-2">
              <select aria-label="Chọn món thêm vào chương trình" className={inputCls} value={adding} onChange={(e) => setAdding(e.target.value)}>
                <option value="">– Chọn món –</option>
                {addable.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
              </select>
              <button type="button" className={btnLight} onClick={addLine} disabled={!adding}>+ Thêm món</button>
            </div>
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={active} onChange={(e) => setActive(e.target.checked)} /> Kích hoạt
          </label>
        </fieldset>
        {readOnly && <p className="text-sm text-stone-500">Chương trình đã kết thúc, không sửa được để giữ đúng lịch sử.</p>}
        {error && <Alert>{error}</Alert>}
        <div className="flex justify-end gap-2">
          <button type="button" className={btnLight} onClick={onClose}>{readOnly ? 'Đóng' : 'Hủy'}</button>
          {!readOnly && <button type="submit" className={btnPrimary} disabled={busy}>{busy ? 'Đang lưu...' : 'Lưu chương trình'}</button>}
        </div>
      </form>
    </Modal>
  )
}
