import { useMemo, useState, type FormEvent } from 'react'
import {
  deleteMenuItem, listCategories, listMenuItems, saveMenuItem, uploadMenuImage,
  type AdminMenuItem, type MenuItemIn, type TempType,
} from '../../api/admin'
import type { ApiError } from '../../api/client'
import { formatVND, normalizeText } from '../../lib/format'
import {
  ActiveBadge, Alert, btnLight, btnPrimary, Field, inputCls, Modal, PageHeader, parseMoney, tableCls, useLoad, useToken,
} from './ui'

export const TEMP_LABEL: Record<TempType, string> = { HOT: 'Nóng', COLD: 'Lạnh', BOTH: 'Cả hai', NONE: '–' }
const PAGE_SIZE = 10
const MAX_IMAGE = 2 * 1024 * 1024

/** W05 – Quản lý món, menu chung toàn chuỗi (UC10, chỉ Quản trị viên). */
export default function MenuItemsPage() {
  const token = useToken()
  const items = useLoad(() => listMenuItems(token), [token])
  const cats = useLoad(() => listCategories(token), [token])
  const [query, setQuery] = useState('')
  const [cat, setCat] = useState('all')
  const [status, setStatus] = useState('active')
  const [page, setPage] = useState(0)
  const [editing, setEditing] = useState<AdminMenuItem | 'new' | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  const filtered = useMemo(() => {
    const q = normalizeText(query)
    return (items.data ?? []).filter(
      (m) =>
        (!q || normalizeText(m.name).includes(q)) &&
        (cat === 'all' || String(m.category_id) === cat) &&
        (status === 'all' || m.is_active === (status === 'active')),
    )
  }, [items.data, query, cat, status])
  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const shown = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  const run = async (fn: () => Promise<unknown>, ok: string) => {
    setActionError(null)
    setNotice(null)
    try {
      await fn()
      setNotice(ok)
      void items.reload()
    } catch (e) {
      setActionError((e as ApiError).message)
    }
  }
  const toggle = (m: AdminMenuItem) =>
    run(() => saveMenuItem(token, { ...toInput(m), is_active: !m.is_active }, m.id),
      m.is_active ? `Đã ẩn "${m.name}" khỏi menu toàn chuỗi.` : `Đã mở bán lại "${m.name}".`)
  const remove = (m: AdminMenuItem) => {
    if (window.confirm(`Xóa món "${m.name}"? Đơn cũ vẫn giữ lịch sử.`))
      void run(() => deleteMenuItem(token, m.id), `Đã xóa món "${m.name}".`)
  }

  return (
    <section className="rounded-2xl bg-white p-5 shadow-sm">
      <PageHeader title="Quản lý món (menu chung)">
        <button className={btnPrimary} onClick={() => { setNotice(null); setEditing('new') }}>+ Thêm món</button>
      </PageHeader>
      <div className="mb-3 flex flex-wrap gap-2">
        <input type="search" aria-label="Tìm theo tên" placeholder="Tìm theo tên..." value={query}
          onChange={(e) => { setQuery(e.target.value); setPage(0) }} className={`${inputCls} max-w-xs`} />
        <select aria-label="Lọc danh mục" value={cat} onChange={(e) => { setCat(e.target.value); setPage(0) }} className={btnLight}>
          <option value="all">Danh mục: Tất cả</option>
          {cats.data?.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select aria-label="Lọc trạng thái" value={status} onChange={(e) => { setStatus(e.target.value); setPage(0) }} className={btnLight}>
          <option value="active">Trạng thái: Đang bán</option>
          <option value="hidden">Ngừng bán</option>
          <option value="all">Tất cả</option>
        </select>
      </div>
      {(items.error || cats.error) && <Alert>{items.error ?? cats.error}</Alert>}
      {actionError && <Alert>{actionError}</Alert>}
      {notice && <Alert kind="ok">{notice}</Alert>}
      {!items.data ? (
        <p>Đang tải...</p>
      ) : (
        <>
          <table className={tableCls}>
            <thead>
              <tr><th>Ảnh</th><th>Tên món</th><th>Danh mục</th><th>Giá gốc</th><th>Nóng/Lạnh</th><th>Trạng thái</th><th>Thao tác</th></tr>
            </thead>
            <tbody>
              {shown.map((m) => (
                <tr key={m.id}>
                  <td>
                    {m.image_url ? <img src={m.image_url} alt={m.name} className="h-10 w-10 rounded object-cover" />
                      : <span className="inline-block h-10 w-10 rounded bg-stone-100" />}
                  </td>
                  <td className="font-medium">{m.name}</td>
                  <td>{m.category_name}</td>
                  <td>{formatVND(m.base_price)}</td>
                  <td>{TEMP_LABEL[m.temperature_type]}</td>
                  <td><ActiveBadge active={m.is_active} on="Đang bán" off="Ngừng bán" /></td>
                  <td className="space-x-1 whitespace-nowrap">
                    <button className={btnLight} onClick={() => { setNotice(null); setEditing(m) }} aria-label={`Sửa ${m.name}`}>Sửa</button>
                    <button className={btnLight} onClick={() => toggle(m)} aria-label={`${m.is_active ? 'Ẩn' : 'Hiện'} ${m.name}`}>
                      {m.is_active ? 'Ẩn' : 'Hiện'}
                    </button>
                    <button className={btnLight} onClick={() => remove(m)} aria-label={`Xóa ${m.name}`}>Xóa</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filtered.length === 0 && <p className="p-3 text-sm text-stone-500">Không có món phù hợp.</p>}
          {pages > 1 && (
            <div className="mt-3 flex items-center gap-2 text-sm" aria-label="Phân trang">
              <button className={btnLight} disabled={page === 0} onClick={() => setPage(page - 1)}>‹</button>
              Trang {page + 1}/{pages}
              <button className={btnLight} disabled={page >= pages - 1} onClick={() => setPage(page + 1)}>›</button>
            </div>
          )}
        </>
      )}
      {editing && cats.data && (
        <MenuItemForm token={token} item={editing === 'new' ? null : editing} categories={cats.data}
          onClose={() => setEditing(null)}
          onSaved={(m) => { setEditing(null); setNotice(`Đã lưu món "${m.name}".`); void items.reload() }} />
      )}
    </section>
  )
}

function toInput(m: AdminMenuItem): MenuItemIn {
  const { category_id, name, description, base_price, temperature_type, tags, is_active } = m
  return { category_id, name, description, base_price, temperature_type, tags, is_active }
}

function MenuItemForm({ token, item, categories, onClose, onSaved }: {
  token: string
  item: AdminMenuItem | null
  categories: { id: number; name: string }[]
  onClose: () => void
  onSaved: (m: AdminMenuItem) => void
}) {
  const [name, setName] = useState(item?.name ?? '')
  const [categoryId, setCategoryId] = useState(String(item?.category_id ?? categories[0]?.id ?? ''))
  const [price, setPrice] = useState(item ? String(item.base_price) : '')
  const [description, setDescription] = useState(item?.description ?? '')
  const [temp, setTemp] = useState<TempType>(item?.temperature_type ?? 'BOTH')
  const [tags, setTags] = useState((item?.tags ?? []).join(', '))
  const [active, setActive] = useState(item?.is_active ?? true)
  const [file, setFile] = useState<File | null>(null)
  // Món mới đã lưu nhưng upload ảnh lỗi: lần bấm Lưu sau phải sửa món đó, không tạo trùng
  const [savedId, setSavedId] = useState(item?.id)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    const base = parseMoney(price)
    if (!name.trim()) return setError('Vui lòng nhập tên món')
    if (base === null || Number.isNaN(base)) return setError('Giá gốc phải là số tiền hợp lệ (VD 45000)')
    if (file && file.size > MAX_IMAGE) return setError('Ảnh tối đa 2 MB')
    setBusy(true)
    setError(null)
    try {
      const body: MenuItemIn = {
        category_id: Number(categoryId), name, description: description || null, base_price: base,
        temperature_type: temp, tags: tags.split(',').map((t) => t.trim()).filter(Boolean), is_active: active,
      }
      let saved = await saveMenuItem(token, body, savedId)
      setSavedId(saved.id)
      if (file) {
        try {
          saved = await uploadMenuImage(token, saved.id, file)
        } catch (err) {
          // Món đã lưu; chỉ ảnh lỗi → báo để chọn ảnh khác, giữ form mở ở chế độ sửa
          setError(`Đã lưu món nhưng chưa lưu được ảnh: ${(err as ApiError).message}`)
          return
        }
      }
      onSaved(saved)
    } catch (err) {
      setError((err as ApiError).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal title={item ? `Sửa món ${item.name}` : 'Thêm món'} onClose={onClose}>
      <form onSubmit={submit} className="grid grid-cols-2 gap-3">
        <div className="col-span-2">
          <Field label="Tên món">
            <input className={inputCls} value={name} onChange={(e) => setName(e.target.value)} maxLength={100} />
          </Field>
        </div>
        <Field label="Danh mục">
          <select className={inputCls} value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
            {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </Field>
        <Field label="Giá gốc (đ)">
          <input className={inputCls} inputMode="numeric" value={price} onChange={(e) => setPrice(e.target.value)} placeholder="45000" />
        </Field>
        <div className="col-span-2">
          <Field label="Mô tả">
            <textarea className={inputCls} rows={2} value={description} onChange={(e) => setDescription(e.target.value)} maxLength={1000} />
          </Field>
        </div>
        <Field label="Loại nóng / lạnh" hint="Dùng cho gợi ý theo thời tiết">
          <select className={inputCls} value={temp} onChange={(e) => setTemp(e.target.value as TempType)}>
            {(Object.keys(TEMP_LABEL) as TempType[]).map((t) => (
              <option key={t} value={t}>{t === 'NONE' ? 'Không áp dụng' : TEMP_LABEL[t]}</option>
            ))}
          </select>
        </Field>
        <Field label="Thẻ (tags)" hint="Cách nhau bởi dấu phẩy, VD: coffee, milk – dùng cho gợi ý món tương tự">
          <input className={inputCls} value={tags} onChange={(e) => setTags(e.target.value)} />
        </Field>
        <div className="col-span-2">
          <Field label="Ảnh món" hint="JPG, PNG hoặc WEBP, tối đa 2 MB">
            <input type="file" accept="image/jpeg,image/png,image/webp" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          </Field>
        </div>
        <label className="col-span-2 flex items-center gap-2 text-sm">
          <input type="checkbox" checked={active} onChange={(e) => setActive(e.target.checked)} /> Đang bán
        </label>
        {error && <div className="col-span-2"><Alert>{error}</Alert></div>}
        <div className="col-span-2 flex justify-end gap-2">
          <button type="button" className={btnLight} onClick={onClose}>Hủy</button>
          <button type="submit" className={btnPrimary} disabled={busy}>{busy ? 'Đang lưu...' : 'Lưu'}</button>
        </div>
      </form>
    </Modal>
  )
}
