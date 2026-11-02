import { useEffect, useState } from 'react'
import { Navigate, Outlet, useNavigate } from 'react-router-dom'
import { getMe, type StaffRole } from '../../api/auth'
import type { ApiError } from '../../api/client'
import { clearSession, loadSession } from '../../auth/staffSession'

const ROLE_LABEL: Record<StaffRole, string> = {
  ADMIN: 'Quản trị viên',
  MANAGER: 'Quản lý chi nhánh',
  CASHIER: 'Thu ngân',
  BARISTA: 'Pha chế',
}

/** Khung Web Admin: bắt buộc đăng nhập; kiểm tra lại token với /api/auth/me khi mở. */
export default function AdminLayout() {
  const navigate = useNavigate()
  const session = loadSession()
  const [checked, setChecked] = useState(false)

  useEffect(() => {
    if (!session) return
    getMe(session.token)
      .then(() => setChecked(true))
      .catch((e: ApiError) => {
        if (e.status === 401 || e.status === 403) {
          clearSession()
          navigate('/admin/login', { replace: true })
        } else {
          setChecked(true)
        }
      })
  }, []) // chỉ kiểm tra 1 lần khi mở Web Admin

  if (!session) return <Navigate to="/admin/login" replace />

  const { staff } = session
  const logout = () => {
    clearSession()
    navigate('/admin/login', { replace: true })
  }

  return (
    <div className="min-h-screen">
      <header className="flex items-center justify-between bg-coffee px-6 py-3 text-white">
        <span className="font-bold">SmartCafe Admin</span>
        <span className="text-sm">
          {staff.full_name} ({ROLE_LABEL[staff.role]}
          {staff.branch ? ` – ${staff.branch.name}` : ''})
          <button onClick={logout} className="ml-4 rounded border border-white/60 px-3 py-1">
            Đăng xuất
          </button>
        </span>
      </header>
      <main className="p-6">{checked ? <Outlet context={staff} /> : <p>Đang kiểm tra phiên đăng nhập...</p>}</main>
    </div>
  )
}
