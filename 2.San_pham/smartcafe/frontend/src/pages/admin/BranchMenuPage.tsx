import { useMemo, useState } from 'react'
import { getBranchMenu, patchBranchMenu, type BranchMenuRow } from '../../api/admin'
import type { ApiError } from '../../api/client'
import { formatVND, normalizeText } from '../../lib/format'
import { Alert, btnLight, btnPrimary, inputCls, PageHeader, parseMoney, tableCls, useBranchChoice, useLoad, useStaff, useToken } from './ui'

interface Draft {
  price: string
  available: boolean
}

const draftOf = (r: BranchMenuRow): Draft => ({ price: r.price_override?.toString() ?? '', available: r.is_available })

/** W06 – Menu chi nhánh (UC13): giá riêng của chi nhánh và bật/tắt "Còn hàng", chỉnh trực tiếp trên bảng.
 *  Lưu xong menu khách của chi nhánh tự cập nhật (MENU_UPDATED). */
export default function BranchMenuPage() {
  const staff = useStaff()
  const token = useToken()
  const { branchId, picker } = useBranchChoice(staff, token)
  return (
    <section className="rounded-2xl bg-white p-5 shadow-sm">
      <PageHeader title="Menu chi nhánh">{picker}</PageHeader>
      {branchId ? <BranchMenuTable key={branchId} token={token} branchId={branchId} /> : <p>Chưa có chi nhánh.</p>}
    </section>
  )
}

function BranchMenuTable({ token, branchId }: { token: string; branchId: number }) {
  const { data, error, setData } = useLoad(() => getBranchMenu(token, branchId), [token, branchId])
  const [drafts, setDrafts] = useState<Record<number, Draft>>({})
  const [query, setQuery] = useState('')
  const [cat, setCat] = useState('all')
  const [onlyOut, setOnlyOut] = useState(false)
  const [rowError, setRowError] = useState<Record<number, string>>({})
  const [notice, setNotice] = useState<string | null>(null)
  const [busy, setBusy] = useState<number | null>(null)

  const categories = useMemo(
    () => [...new Map((data ?? []).map((r) => [r.category_id, r.category_name])).entries()],
    [data],
  )
  const rows = useMemo(() => {
    const q = normalizeText(query)
    return (data ?? []).filter(
      (r) => (!q || normalizeText(r.name).includes(q)) && (cat === 'all' || String(r.category_id) === cat) && (!onlyOut || !r.is_available),
    )
  }, [data, query, cat, onlyOut])

  const draft = (r: BranchMenuRow) => drafts[r.menu_item_id] ?? draftOf(r)
  const setDraft = (r: BranchMenuRow, d: Partial<Draft>) => setDrafts((all) => ({ ...all, [r.menu_item_id]: { ...draft(r), ...d } }))
  const dirty = (r: BranchMenuRow) => {
    const d = draft(r)
    const o = draftOf(r)
    return d.price.trim() !== o.price || d.available !== o.available
  }

  const save = async (r: BranchMenuRow) => {
    const d = draft(r)
    const price = parseMoney(d.price)
    if (Number.isNaN(price)) return setRowError((e) => ({ ...e, [r.menu_item_id]: 'Giá không hợp lệ' }))
    setBusy(r.menu_item_id)
    setNotice(null)
    setRowError((e) => ({ ...e, [r.menu_item_id]: '' }))
    try {
      const saved = await patchBranchMenu(token, branchId, r.menu_item_id, { price_override: price, is_available: d.available })
      setData((list) => list?.map((x) => (x.menu_item_id === saved.menu_item_id ? saved : x)) ?? list)
      setDrafts((all) => {
        const { [r.menu_item_id]: _, ...rest } = all
        return rest
      })
      setNotice(`Đã lưu "${r.name}" – menu khách đã được cập nhật.`)
    } catch (e) {
      setRowError((x) => ({ ...x, [r.menu_item_id]: (e as ApiError).message }))
    } finally {
      setBusy(null)
    }
  }

  if (error) return <Alert>{error}</Alert>
  if (!data) return <p>Đang tải...</p>
  return (
    <>
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <input type="search" aria-label="Tìm món" placeholder="Tìm món..." value={query} onChange={(e) => setQuery(e.target.value)}
          className={`${inputCls} max-w-xs`} />
        <select aria-label="Lọc danh mục" value={cat} onChange={(e) => setCat(e.target.value)} className={btnLight}>
          <option value="all">Danh mục: Tất cả</option>
          {categories.map(([id, name]) => <option key={id} value={id}>{name}</option>)}
        </select>
        <label className="flex items-center gap-1 text-sm">
          <input type="checkbox" checked={onlyOut} onChange={(e) => setOnlyOut(e.target.checked)} /> Chỉ hiện món hết hàng
        </label>
      </div>
      {notice && <Alert kind="ok">{notice}</Alert>}
      <table className={tableCls}>
        <thead>
          <tr><th>Tên món</th><th>Danh mục</th><th>Giá chung</th><th>Giá chi nhánh</th><th>Còn hàng</th><th></th></tr>
        </thead>
        <tbody>
          {rows.map((r) => {
            const d = draft(r)
            return (
              <tr key={r.menu_item_id} data-testid={`bm-${r.menu_item_id}`} className={d.available ? '' : 'bg-stone-50 text-stone-500'}>
                <td className="font-medium">{r.name}</td>
                <td>{r.category_name}</td>
                <td>{formatVND(r.base_price)}</td>
                <td>
                  <input aria-label={`Giá chi nhánh ${r.name}`} inputMode="numeric" value={d.price} placeholder="Giá chung"
                    onChange={(e) => setDraft(r, { price: e.target.value })} className={`${inputCls} w-32`} />
                  {rowError[r.menu_item_id] && <p role="alert" className="text-xs text-red-700">{rowError[r.menu_item_id]}</p>}
                </td>
                <td>
                  <input type="checkbox" aria-label={`Còn hàng ${r.name}`} checked={d.available}
                    onChange={(e) => setDraft(r, { available: e.target.checked })} />
                </td>
                <td>
                  <button className={btnPrimary} disabled={!dirty(r) || busy === r.menu_item_id} onClick={() => save(r)}
                    aria-label={`Lưu ${r.name}`}>Lưu</button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
      <p className="mt-2 text-xs italic text-stone-500">
        Để trống "Giá chi nhánh" = dùng giá chung. Bỏ tích "Còn hàng" = khách thấy "Tạm hết".
      </p>
    </>
  )
}
