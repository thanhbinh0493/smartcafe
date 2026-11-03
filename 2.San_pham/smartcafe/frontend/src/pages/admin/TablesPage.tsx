import { useEffect, useState, type FormEvent } from 'react'
import { fetchQrPng, listTables, saveTable, type DiningTable } from '../../api/admin'
import type { ApiError } from '../../api/client'
import { ActiveBadge, Alert, btnLight, btnPrimary, Field, inputCls, Modal, PageHeader, tableCls, useBranchChoice, useLoad, useStaff, useToken } from './ui'

const TABLE_RE = /^[A-Za-z0-9-]{1,10}$/

/** A06 – Bàn & mã QR (UC14): thêm / đổi số bàn / khóa bàn, xem và tải ảnh QR để in. */
export default function TablesPage() {
  const staff = useStaff()
  const token = useToken()
  const { branchId, picker } = useBranchChoice(staff, token)
  return (
    <section className="rounded-2xl bg-white p-5 shadow-sm">
      <PageHeader title="Bàn & mã QR">{picker}</PageHeader>
      {branchId ? <Tables key={branchId} token={token} branchId={branchId} /> : <p>Chưa có chi nhánh.</p>}
    </section>
  )
}

function Tables({ token, branchId }: { token: string; branchId: number }) {
  const { data, error, reload } = useLoad(() => listTables(token, branchId), [token, branchId])
  const [number, setNumber] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [editing, setEditing] = useState<DiningTable | null>(null)
  const [preview, setPreview] = useState<DiningTable | null>(null)
  const [printing, setPrinting] = useState(false)

  const add = async (e: FormEvent) => {
    e.preventDefault()
    setNotice(null)
    if (!TABLE_RE.test(number.trim())) return setFormError('Số bàn 1–10 ký tự: chữ, số hoặc dấu -')
    setFormError(null)
    try {
      const t = await saveTable(token, branchId, { table_number: number, is_active: true })
      setNumber('')
      setNotice(`Đã thêm bàn ${t.table_number}. Bấm "Xem QR" để tải ảnh in.`)
      void reload()
    } catch (err) {
      setFormError((err as ApiError).message)
    }
  }

  if (error) return <Alert>{error}</Alert>
  if (!data) return <p>Đang tải...</p>
  const active = data.filter((t) => t.is_active)
  return (
    <>
      <form onSubmit={add} className="mb-3 flex flex-wrap items-end gap-2">
        <Field label="Số bàn mới">
          <input className={`${inputCls} w-28`} value={number} onChange={(e) => setNumber(e.target.value)} maxLength={10} placeholder="VD: 13" />
        </Field>
        <button type="submit" className={btnPrimary}>+ Thêm bàn</button>
        <button type="button" className={btnLight} disabled={active.length === 0} onClick={() => setPrinting(true)}>
          In tất cả mã QR ({active.length})
        </button>
      </form>
      {formError && <Alert>{formError}</Alert>}
      {notice && <Alert kind="ok">{notice}</Alert>}
      <table className={tableCls}>
        <thead>
          <tr><th>Bàn</th><th>Đường dẫn QR</th><th>Trạng thái</th><th>Thao tác</th></tr>
        </thead>
        <tbody>
          {data.map((t) => (
            <tr key={t.id}>
              <td className="font-bold">{t.table_number}</td>
              <td className="max-w-xs truncate font-mono text-xs">{t.qr_url}</td>
              <td><ActiveBadge active={t.is_active} on="Đang dùng" off="Đã khóa" /></td>
              <td className="space-x-1 whitespace-nowrap">
                <button className={btnLight} onClick={() => setPreview(t)} aria-label={`Xem QR bàn ${t.table_number}`}>Xem QR</button>
                <button className={btnLight} onClick={() => { setNotice(null); setEditing(t) }} aria-label={`Sửa bàn ${t.table_number}`}>Sửa</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {data.length === 0 && <p className="p-3 text-sm text-stone-500">Chi nhánh chưa có bàn.</p>}
      {editing && (
        <TableForm token={token} branchId={branchId} table={editing} onClose={() => setEditing(null)}
          onSaved={(t) => { setEditing(null); setNotice(`Đã lưu bàn ${t.table_number}.`); void reload() }} />
      )}
      {preview && <QrPreview token={token} table={preview} onClose={() => setPreview(null)} />}
      {printing && <PrintSheet token={token} tables={active} onClose={() => setPrinting(false)} />}
    </>
  )
}

function TableForm({ token, branchId, table, onClose, onSaved }: {
  token: string
  branchId: number
  table: DiningTable
  onClose: () => void
  onSaved: (t: DiningTable) => void
}) {
  const [number, setNumber] = useState(table.table_number)
  const [active, setActive] = useState(table.is_active)
  const [error, setError] = useState<string | null>(null)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (!TABLE_RE.test(number.trim())) return setError('Số bàn 1–10 ký tự: chữ, số hoặc dấu -')
    try {
      onSaved(await saveTable(token, branchId, { table_number: number, is_active: active }, table.id))
    } catch (err) {
      setError((err as ApiError).message)
    }
  }

  return (
    <Modal title={`Sửa bàn ${table.table_number}`} onClose={onClose}>
      <form onSubmit={submit} className="space-y-3">
        <Field label="Số bàn" hint="Đổi số bàn vẫn giữ nguyên mã QR đã in">
          <input className={inputCls} value={number} onChange={(e) => setNumber(e.target.value)} maxLength={10} />
        </Field>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={active} onChange={(e) => setActive(e.target.checked)} />
          Đang dùng (bỏ tích = khóa bàn, khách quét QR sẽ báo mã không hợp lệ)
        </label>
        {error && <Alert>{error}</Alert>}
        <div className="flex justify-end gap-2">
          <button type="button" className={btnLight} onClick={onClose}>Hủy</button>
          <button type="submit" className={btnPrimary}>Lưu</button>
        </div>
      </form>
    </Modal>
  )
}

/** Tải ảnh QR (cần JWT) thành object URL để hiện trong <img>. */
function useQrImage(token: string, tableId: number) {
  const [url, setUrl] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    let objectUrl: string | null = null
    let cancelled = false
    fetchQrPng(token, tableId)
      .then((blob) => {
        if (cancelled) return
        objectUrl = URL.createObjectURL(blob)
        setUrl(objectUrl)
      })
      .catch((e: ApiError) => !cancelled && setError(e.message))
    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [token, tableId])
  return { url, error }
}

function QrPreview({ token, table, onClose }: { token: string; table: DiningTable; onClose: () => void }) {
  const { url, error } = useQrImage(token, table.id)
  return (
    <Modal title={`Mã QR bàn ${table.table_number}`} onClose={onClose}>
      {error && <Alert>{error}</Alert>}
      {url ? (
        <div className="space-y-3 text-center">
          <img src={url} alt={`QR bàn ${table.table_number}`} className="mx-auto w-64" />
          <p className="break-all font-mono text-xs">{table.qr_url}</p>
          <a href={url} download={`QR_Ban_${table.table_number}.png`} className={`${btnPrimary} inline-block`}>Tải ảnh PNG</a>
        </div>
      ) : (
        !error && <p>Đang tạo mã QR...</p>
      )}
    </Modal>
  )
}

function PrintCard({ token, table }: { token: string; table: DiningTable }) {
  const { url } = useQrImage(token, table.id)
  return (
    <div className="break-inside-avoid rounded border border-stone-300 p-2 text-center">
      {url ? <img src={url} alt={`QR bàn ${table.table_number}`} className="mx-auto w-full" /> : <p className="py-10">...</p>}
    </div>
  )
}

function PrintSheet({ token, tables, onClose }: { token: string; tables: DiningTable[]; onClose: () => void }) {
  return (
    <div className="print-area fixed inset-0 z-40 overflow-auto bg-white p-6" role="dialog" aria-label="In mã QR">
      <div className="mb-4 flex gap-2 print:hidden">
        <button className={btnPrimary} onClick={() => window.print()}>In</button>
        <button className={btnLight} onClick={onClose}>Đóng</button>
      </div>
      <div className="grid grid-cols-3 gap-4">
        {tables.map((t) => <PrintCard key={t.id} token={token} table={t} />)}
      </div>
    </div>
  )
}
