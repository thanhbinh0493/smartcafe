/** Thành phần giao diện dùng chung cho các màn hình quản trị (F6). */
import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { useOutletContext } from 'react-router-dom'
import { listBranches, type AdminBranch } from '../../api/admin'
import type { StaffMe } from '../../api/auth'
import type { ApiError } from '../../api/client'
import { loadSession } from '../../auth/staffSession'

export const useStaff = () => useOutletContext<StaffMe>()
export const useToken = () => loadSession()?.token ?? ''

/** Tải dữ liệu 1 lần + hàm `reload`; lỗi hiện bằng thông báo của API. */
export function useLoad<T>(fn: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const reload = useCallback(() => {
    setError(null)
    return fn()
      .then(setData)
      .catch((e: ApiError) => setError(e.message))
  }, deps)
  useEffect(() => {
    void reload()
  }, [reload])
  return { data, error, reload, setData }
}

export function PageHeader({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
      <h1 className="text-xl font-bold text-coffee">{title}</h1>
      <div className="flex flex-wrap items-center gap-2">{children}</div>
    </div>
  )
}

export function Alert({ kind = 'error', children }: { kind?: 'error' | 'ok'; children: ReactNode }) {
  return kind === 'error' ? (
    <p role="alert" className="mb-3 rounded-lg bg-red-50 p-2 text-sm text-red-700">{children}</p>
  ) : (
    <p role="status" className="mb-3 rounded-lg bg-green-50 p-2 text-sm text-green-800">{children}</p>
  )
}

export function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: ReactNode }) {
  return (
    <div className="fixed inset-0 z-30 flex items-start justify-center overflow-y-auto bg-black/40 p-4">
      <div role="dialog" aria-modal="true" aria-label={title} className="mt-8 w-full max-w-xl rounded-2xl bg-white p-5">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-bold">{title}</h2>
          <button type="button" onClick={onClose} aria-label="Đóng" className="px-2 text-xl">×</button>
        </div>
        {children}
      </div>
    </div>
  )
}

/** Nhãn bọc ô nhập; dòng gợi ý nằm ngoài nhãn để tên ô (cho trình đọc màn hình / test) chỉ là nhãn. */
export function Field({ label, children, hint }: { label: string; children: ReactNode; hint?: string }) {
  return (
    <div className="text-sm">
      <label className="block">
        <span className="mb-1 block font-medium">{label}</span>
        {children}
      </label>
      {hint && <p className="mt-0.5 text-xs text-stone-500">{hint}</p>}
    </div>
  )
}

export const inputCls = 'w-full rounded-lg border border-stone-300 px-3 py-1.5 outline-none focus:border-coffee'
export const btnPrimary = 'rounded-lg bg-coffee px-4 py-2 font-semibold text-white disabled:opacity-50'
export const btnLight = 'rounded-lg border border-stone-300 px-3 py-1.5'
export const tableCls = 'w-full border-collapse text-sm [&_td]:border-t [&_td]:border-stone-200 [&_td]:p-2 [&_th]:p-2 [&_th]:text-left'

export function ActiveBadge({ active, on = 'Đang dùng', off = 'Đã khóa' }: { active: boolean; on?: string; off?: string }) {
  return (
    <span className={`rounded px-2 py-0.5 text-xs font-semibold ${active ? 'bg-green-100 text-green-800' : 'bg-stone-200 text-stone-600'}`}>
      {active ? on : off}
    </span>
  )
}

/** Chọn chi nhánh để thao tác: Quản trị viên chọn trong danh sách; Quản lý chi nhánh cố định chi nhánh mình. */
export function useBranchChoice(staff: StaffMe, token: string) {
  const [branches, setBranches] = useState<AdminBranch[]>([])
  const [branchId, setBranchId] = useState<number | null>(staff.branch?.id ?? null)
  useEffect(() => {
    if (staff.role !== 'ADMIN') return
    listBranches(token)
      .then((list) => {
        setBranches(list)
        setBranchId((cur) => cur ?? list[0]?.id ?? null)
      })
      .catch(() => setBranches([]))
  }, [staff.role, token])

  const picker =
    staff.role === 'ADMIN' ? (
      <label className="text-sm">
        Chi nhánh{' '}
        <select value={branchId ?? ''} onChange={(e) => setBranchId(Number(e.target.value))}
          aria-label="Chọn chi nhánh" className="rounded-lg border border-stone-300 px-2 py-1">
          {branches.map((b) => (
            <option key={b.id} value={b.id}>{b.name}</option>
          ))}
        </select>
      </label>
    ) : (
      <span className="text-sm font-semibold">{staff.branch?.name}</span>
    )
  return { branchId, picker }
}

/** Chuỗi số "39.000" / "39000" → 39000; rỗng → null; không hợp lệ → NaN. */
export function parseMoney(s: string): number | null {
  const t = s.replace(/[.\s,đ]/g, '')
  if (!t) return null
  return /^\d+$/.test(t) ? Number(t) : NaN
}
