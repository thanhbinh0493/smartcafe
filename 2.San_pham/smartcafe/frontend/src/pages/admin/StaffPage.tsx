import { useMemo, useState, type FormEvent } from 'react'
import { listBranches, listStaff, saveStaff, type StaffAccount, type StaffIn } from '../../api/admin'
import type { StaffMe, StaffRole } from '../../api/auth'
import type { ApiError } from '../../api/client'
import { ActiveBadge, Alert, btnLight, btnPrimary, Field, inputCls, Modal, PageHeader, tableCls, useLoad, useStaff, useToken } from './ui'

export const ROLE_LABEL: Record<StaffRole, string> = {
  ADMIN: 'Quản trị viên',
  MANAGER: 'Quản lý chi nhánh',
  CASHIER: 'Thu ngân',
  BARISTA: 'Pha chế',
}

/** Vai trò mà người đang đăng nhập được gán cho tài khoản khác (ma trận RBAC – III.1). */
export const assignableRoles = (me: StaffMe): StaffRole[] =>
  me.role === 'ADMIN' ? ['ADMIN', 'MANAGER', 'CASHIER', 'BARISTA'] : ['CASHIER', 'BARISTA']

/** Được sửa tài khoản này không: Quản lý chỉ sửa Thu ngân / Pha chế chi nhánh mình (và chính mình). */
export const canEdit = (me: StaffMe, s: StaffAccount) =>
  me.role === 'ADMIN' || s.id === me.id || (s.branch_id === me.branch?.id && (s.role === 'CASHIER' || s.role === 'BARISTA'))

/** A04 – Quản lý nhân viên & phân quyền (UC12). */
export default function StaffPage() {
  const me = useStaff()
  const token = useToken()
  const staff = useLoad(() => listStaff(token), [token])
  const branches = useLoad(() => (me.role === 'ADMIN' ? listBranches(token) : Promise.resolve([])), [token, me.role])
  const [branchFilter, setBranchFilter] = useState('all')
  const [editing, setEditing] = useState<StaffAccount | 'new' | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  const rows = useMemo(
    () =>
      (staff.data ?? []).filter((s) =>
        branchFilter === 'all' ? true : branchFilter === 'hq' ? s.branch_id === null : String(s.branch_id) === branchFilter),
    [staff.data, branchFilter],
  )

  return (
    <section className="rounded-2xl bg-white p-5 shadow-sm">
      <PageHeader title={me.role === 'ADMIN' ? 'Nhân viên toàn chuỗi' : `Nhân viên ${me.branch?.name ?? ''}`}>
        {me.role === 'ADMIN' && (
          <select aria-label="Lọc chi nhánh" value={branchFilter} onChange={(e) => setBranchFilter(e.target.value)} className={btnLight}>
            <option value="all">Tất cả chi nhánh</option>
            <option value="hq">Trụ sở</option>
            {branches.data?.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
          </select>
        )}
        <button className={btnPrimary} onClick={() => { setNotice(null); setEditing('new') }}>+ Thêm nhân viên</button>
      </PageHeader>
      {staff.error && <Alert>{staff.error}</Alert>}
      {notice && <Alert kind="ok">{notice}</Alert>}
      {!staff.data ? (
        <p>Đang tải...</p>
      ) : (
        <table className={tableCls}>
          <thead>
            <tr><th>Tên đăng nhập</th><th>Họ tên</th><th>Vai trò</th><th>Chi nhánh</th><th>Điện thoại</th><th>Trạng thái</th><th></th></tr>
          </thead>
          <tbody>
            {rows.map((s) => (
              <tr key={s.id}>
                <td className="font-mono">{s.username}</td>
                <td className="font-medium">{s.full_name}{s.id === me.id && <span className="ml-1 text-xs text-stone-500">(bạn)</span>}</td>
                <td>{ROLE_LABEL[s.role]}</td>
                <td>{s.branch_name ?? 'Trụ sở'}</td>
                <td>{s.phone ?? '–'}</td>
                <td><ActiveBadge active={s.is_active} /></td>
                <td>
                  {canEdit(me, s) && (
                    <button className={btnLight} onClick={() => { setNotice(null); setEditing(s) }} aria-label={`Sửa ${s.username}`}>Sửa</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {editing && (
        <StaffForm token={token} me={me} account={editing === 'new' ? null : editing} branches={branches.data ?? []}
          onClose={() => setEditing(null)}
          onSaved={(s) => { setEditing(null); setNotice(`Đã lưu tài khoản "${s.username}".`); void staff.reload() }} />
      )}
    </section>
  )
}

function StaffForm({ token, me, account, branches, onClose, onSaved }: {
  token: string
  me: StaffMe
  account: StaffAccount | null
  branches: { id: number; name: string }[]
  onClose: () => void
  onSaved: (s: StaffAccount) => void
}) {
  const self = account?.id === me.id
  const roles = self ? [account.role] : assignableRoles(me)
  const [username, setUsername] = useState(account?.username ?? '')
  const [fullName, setFullName] = useState(account?.full_name ?? '')
  const [phone, setPhone] = useState(account?.phone ?? '')
  const [role, setRole] = useState<StaffRole>(account?.role ?? roles[roles.length - 1])
  const [branchId, setBranchId] = useState<string>(String(account?.branch_id ?? me.branch?.id ?? branches[0]?.id ?? ''))
  const [active, setActive] = useState(account?.is_active ?? true)
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const needsBranch = role !== 'ADMIN'

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (!account && !/^[a-z0-9_.]{3,50}$/.test(username.trim().toLowerCase()))
      return setError('Tên đăng nhập 3–50 ký tự: chữ không dấu, số, dấu _ hoặc .')
    if (!fullName.trim()) return setError('Vui lòng nhập họ tên')
    if ((!account || password) && password.length < 8) return setError('Mật khẩu tối thiểu 8 ký tự')
    if (needsBranch && !branchId) return setError('Vui lòng chọn chi nhánh')
    setBusy(true)
    setError(null)
    const body: StaffIn = {
      full_name: fullName, phone: phone || null, role, is_active: active,
      branch_id: needsBranch ? Number(branchId) : null,
      ...(account ? { password: password || null } : { username, password }),
    }
    try {
      onSaved(await saveStaff(token, body, account?.id))
    } catch (err) {
      setError((err as ApiError).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal title={account ? `Sửa tài khoản ${account.username}` : 'Thêm nhân viên'} onClose={onClose}>
      <form onSubmit={submit} className="grid grid-cols-2 gap-3">
        <Field label="Tên đăng nhập">
          <input className={inputCls} value={username} onChange={(e) => setUsername(e.target.value)} disabled={!!account} maxLength={50} />
        </Field>
        <Field label="Họ tên">
          <input className={inputCls} value={fullName} onChange={(e) => setFullName(e.target.value)} maxLength={100} />
        </Field>
        <Field label="Vai trò">
          <select className={inputCls} value={role} onChange={(e) => setRole(e.target.value as StaffRole)} disabled={self}>
            {roles.map((r) => <option key={r} value={r}>{ROLE_LABEL[r]}</option>)}
          </select>
        </Field>
        <Field label="Chi nhánh">
          {me.role === 'ADMIN' && needsBranch && !self ? (
            <select className={inputCls} value={branchId} onChange={(e) => setBranchId(e.target.value)} aria-label="Chi nhánh làm việc">
              {branches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
            </select>
          ) : (
            <input className={inputCls} disabled value={needsBranch ? (account?.branch_name ?? me.branch?.name ?? '') : 'Trụ sở'} />
          )}
        </Field>
        <Field label="Điện thoại">
          <input className={inputCls} value={phone} onChange={(e) => setPhone(e.target.value)} maxLength={15} />
        </Field>
        <Field label={account ? 'Đặt lại mật khẩu' : 'Mật khẩu'} hint={account ? 'Để trống = giữ mật khẩu cũ' : 'Tối thiểu 8 ký tự'}>
          <input className={inputCls} type="password" value={password} onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password" maxLength={128} />
        </Field>
        <label className="col-span-2 flex items-center gap-2 text-sm">
          <input type="checkbox" checked={active} onChange={(e) => setActive(e.target.checked)} disabled={self} />
          Cho phép đăng nhập (bỏ tích = khóa tài khoản, có hiệu lực ngay)
        </label>
        {self && <p className="col-span-2 text-xs text-stone-500">Bạn không thể tự khóa hoặc tự đổi vai trò, chi nhánh của mình.</p>}
        {error && <div className="col-span-2"><Alert>{error}</Alert></div>}
        <div className="col-span-2 flex justify-end gap-2">
          <button type="button" className={btnLight} onClick={onClose}>Hủy</button>
          <button type="submit" className={btnPrimary} disabled={busy}>{busy ? 'Đang lưu...' : 'Lưu'}</button>
        </div>
      </form>
    </Modal>
  )
}
