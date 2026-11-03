import { useState, type FormEvent } from 'react'
import { listBranches, saveBranch, type AdminBranch, type BranchIn } from '../../api/admin'
import type { ApiError } from '../../api/client'
import { ActiveBadge, Alert, btnLight, btnPrimary, Field, inputCls, Modal, PageHeader, tableCls, useLoad, useToken } from './ui'

/** A03 – Quản lý chi nhánh (UC11, chỉ Quản trị viên). Mã chi nhánh là tiền tố mã đơn nên không sửa được. */
export default function BranchesPage() {
  const token = useToken()
  const { data, error, reload } = useLoad(() => listBranches(token), [token])
  const [editing, setEditing] = useState<AdminBranch | 'new' | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  return (
    <section className="rounded-2xl bg-white p-5 shadow-sm">
      <PageHeader title="Chi nhánh">
        <button className={btnPrimary} onClick={() => { setNotice(null); setEditing('new') }}>+ Thêm chi nhánh</button>
      </PageHeader>
      {error && <Alert>{error}</Alert>}
      {notice && <Alert kind="ok">{notice}</Alert>}
      {!data ? (
        <p>Đang tải...</p>
      ) : (
        <table className={tableCls}>
          <thead>
            <tr><th>Mã</th><th>Tên chi nhánh</th><th>Địa chỉ</th><th>Điện thoại</th><th>Số bàn</th><th>Nhân viên</th><th>Trạng thái</th><th></th></tr>
          </thead>
          <tbody>
            {data.map((b) => (
              <tr key={b.id}>
                <td className="font-mono font-bold">{b.code}</td>
                <td className="font-medium">{b.name}</td>
                <td>{b.address}</td>
                <td>{b.phone ?? '–'}</td>
                <td>{b.table_count}</td>
                <td>{b.staff_count}</td>
                <td><ActiveBadge active={b.is_active} on="Hoạt động" off="Ngừng hoạt động" /></td>
                <td><button className={btnLight} onClick={() => { setNotice(null); setEditing(b) }} aria-label={`Sửa ${b.name}`}>Sửa</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {editing && (
        <BranchForm token={token} branch={editing === 'new' ? null : editing} onClose={() => setEditing(null)}
          onSaved={(b) => { setEditing(null); setNotice(`Đã lưu chi nhánh "${b.name}".`); void reload() }} />
      )}
    </section>
  )
}

const num = (s: string) => (s.trim() === '' ? null : Number(s))

function BranchForm({ token, branch, onClose, onSaved }: {
  token: string
  branch: AdminBranch | null
  onClose: () => void
  onSaved: (b: AdminBranch) => void
}) {
  const [code, setCode] = useState(branch?.code ?? '')
  const [name, setName] = useState(branch?.name ?? '')
  const [address, setAddress] = useState(branch?.address ?? '')
  const [phone, setPhone] = useState(branch?.phone ?? '')
  const [lat, setLat] = useState(branch?.latitude?.toString() ?? '')
  const [lng, setLng] = useState(branch?.longitude?.toString() ?? '')
  const [active, setActive] = useState(branch?.is_active ?? true)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (!branch && !/^[A-Za-z0-9]{2,10}$/.test(code.trim())) return setError('Mã chi nhánh gồm 2–10 chữ cái / số, VD: CG')
    if (!name.trim() || !address.trim()) return setError('Vui lòng nhập tên và địa chỉ chi nhánh')
    if (branch?.is_active && !active && !window.confirm(
      `Ngừng hoạt động "${branch.name}"? Khách quét QR các bàn của chi nhánh sẽ báo mã không hợp lệ.`)) return
    setBusy(true)
    setError(null)
    const body: BranchIn & { code?: string } = {
      code: code.trim(), name, address, phone: phone || null, latitude: num(lat), longitude: num(lng), is_active: active,
    }
    try {
      onSaved(await saveBranch(token, body, branch?.id))
    } catch (err) {
      setError((err as ApiError).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal title={branch ? `Sửa chi nhánh ${branch.name}` : 'Thêm chi nhánh'} onClose={onClose}>
      <form onSubmit={submit} className="grid grid-cols-2 gap-3">
        <Field label="Mã chi nhánh" hint={branch ? 'Không đổi được (tiền tố mã đơn)' : 'VD: CG → mã đơn CG-0142'}>
          <input className={inputCls} value={code} onChange={(e) => setCode(e.target.value.toUpperCase())}
            disabled={!!branch} maxLength={10} />
        </Field>
        <Field label="Tên chi nhánh">
          <input className={inputCls} value={name} onChange={(e) => setName(e.target.value)} maxLength={100} />
        </Field>
        <div className="col-span-2">
          <Field label="Địa chỉ">
            <input className={inputCls} value={address} onChange={(e) => setAddress(e.target.value)} maxLength={255} />
          </Field>
        </div>
        <Field label="Điện thoại">
          <input className={inputCls} value={phone} onChange={(e) => setPhone(e.target.value)} maxLength={15} />
        </Field>
        <div />
        <Field label="Vĩ độ" hint="Dùng lấy thời tiết cho gợi ý món">
          <input className={inputCls} value={lat} onChange={(e) => setLat(e.target.value)} placeholder="21.0368" />
        </Field>
        <Field label="Kinh độ">
          <input className={inputCls} value={lng} onChange={(e) => setLng(e.target.value)} placeholder="105.7826" />
        </Field>
        <label className="col-span-2 flex items-center gap-2 text-sm">
          <input type="checkbox" checked={active} onChange={(e) => setActive(e.target.checked)} /> Đang hoạt động
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
