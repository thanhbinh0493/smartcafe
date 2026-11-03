import { useState, type FormEvent } from 'react'
import { deleteCategory, listCategories, saveCategory, type Category } from '../../api/admin'
import type { ApiError } from '../../api/client'
import { ActiveBadge, Alert, btnLight, btnPrimary, Field, inputCls, Modal, PageHeader, tableCls, useLoad, useToken } from './ui'

/** A05 – Quản lý danh mục (UC09, chỉ Quản trị viên). */
export default function CategoriesPage() {
  const token = useToken()
  const { data, error, reload } = useLoad(() => listCategories(token), [token])
  const [editing, setEditing] = useState<Category | 'new' | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  const remove = async (c: Category) => {
    if (!window.confirm(`Xóa danh mục "${c.name}"?`)) return
    setActionError(null)
    try {
      await deleteCategory(token, c.id)
      setNotice(`Đã xóa danh mục "${c.name}".`)
      void reload()
    } catch (e) {
      setActionError((e as ApiError).message)
    }
  }

  return (
    <section className="rounded-2xl bg-white p-5 shadow-sm">
      <PageHeader title="Danh mục món">
        <button className={btnPrimary} onClick={() => { setNotice(null); setEditing('new') }}>+ Thêm danh mục</button>
      </PageHeader>
      {error && <Alert>{error}</Alert>}
      {actionError && <Alert>{actionError}</Alert>}
      {notice && <Alert kind="ok">{notice}</Alert>}
      {!data ? (
        <p>Đang tải...</p>
      ) : (
        <table className={tableCls}>
          <thead>
            <tr><th>Thứ tự</th><th>Tên danh mục</th><th>Số món</th><th>Trạng thái</th><th>Thao tác</th></tr>
          </thead>
          <tbody>
            {data.map((c) => (
              <tr key={c.id}>
                <td>{c.sort_order}</td>
                <td className="font-medium">{c.name}</td>
                <td>{c.item_count}</td>
                <td><ActiveBadge active={c.is_active} on="Hiển thị" off="Đã ẩn" /></td>
                <td className="space-x-2">
                  <button className={btnLight} onClick={() => { setNotice(null); setEditing(c) }} aria-label={`Sửa ${c.name}`}>Sửa</button>
                  <button className={btnLight} onClick={() => remove(c)} aria-label={`Xóa ${c.name}`}>Xóa</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {editing && (
        <CategoryForm token={token} category={editing === 'new' ? null : editing} onClose={() => setEditing(null)}
          onSaved={(c) => { setEditing(null); setNotice(`Đã lưu danh mục "${c.name}".`); void reload() }} />
      )}
    </section>
  )
}

function CategoryForm({ token, category, onClose, onSaved }: {
  token: string
  category: Category | null
  onClose: () => void
  onSaved: (c: Category) => void
}) {
  const [name, setName] = useState(category?.name ?? '')
  const [sort, setSort] = useState(String(category?.sort_order ?? 0))
  const [active, setActive] = useState(category?.is_active ?? true)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return setError('Vui lòng nhập tên danh mục')
    setBusy(true)
    setError(null)
    try {
      onSaved(await saveCategory(token, { name, sort_order: Number(sort) || 0, is_active: active }, category?.id))
    } catch (err) {
      setError((err as ApiError).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal title={category ? `Sửa danh mục ${category.name}` : 'Thêm danh mục'} onClose={onClose}>
      <form onSubmit={submit} className="space-y-3">
        <Field label="Tên danh mục">
          <input className={inputCls} value={name} onChange={(e) => setName(e.target.value)} maxLength={50} />
        </Field>
        <Field label="Thứ tự hiển thị" hint="Số nhỏ hiện trước trên menu khách">
          <input className={inputCls} type="number" min={0} max={999} value={sort} onChange={(e) => setSort(e.target.value)} />
        </Field>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={active} onChange={(e) => setActive(e.target.checked)} /> Hiển thị trên menu khách
        </label>
        {error && <Alert>{error}</Alert>}
        <div className="flex justify-end gap-2">
          <button type="button" className={btnLight} onClick={onClose}>Hủy</button>
          <button type="submit" className={btnPrimary} disabled={busy}>{busy ? 'Đang lưu...' : 'Lưu'}</button>
        </div>
      </form>
    </Modal>
  )
}
