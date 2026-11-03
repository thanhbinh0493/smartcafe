import type { ReactNode } from 'react'
import type { StaffRole } from '../../api/auth'
import { useStaff } from './ui'

/** Menu bên trái theo vai trò (IV.2 Mục 2, wireframe W05 – W07). Pha chế / thu ngân chỉ dùng màn hình Bar. */
const ITEMS: { to: string; label: string; roles: StaffRole[] }[] = [
  { to: '/admin/dashboard', label: 'Tổng quan', roles: ['ADMIN', 'MANAGER'] },
  { to: '/admin/branches', label: 'Chi nhánh', roles: ['ADMIN'] },
  { to: '/admin/staff', label: 'Nhân viên', roles: ['ADMIN', 'MANAGER'] },
  { to: '/admin/categories', label: 'Danh mục', roles: ['ADMIN'] },
  { to: '/admin/menu-items', label: 'Món', roles: ['ADMIN'] },
  { to: '/admin/branch-menu', label: 'Menu chi nhánh', roles: ['ADMIN', 'MANAGER'] },
  { to: '/admin/tables', label: 'Bàn & mã QR', roles: ['ADMIN', 'MANAGER'] },
  { to: '/admin/promotions', label: 'Khuyến mãi', roles: ['ADMIN'] },
  { to: '/admin/bar', label: 'Màn hình Bar', roles: ['MANAGER'] },
]

export function navFor(role: StaffRole) {
  return role === 'ADMIN' || role === 'MANAGER' ? ITEMS.filter((i) => i.roles.includes(role)) : []
}

/** Chặn mở màn hình không đúng vai trò bằng cách gõ URL (API vẫn kiểm tra quyền – NFR-S2). */
export function RequireRole({ roles, children }: { roles: StaffRole[]; children: ReactNode }) {
  const staff = useStaff()
  if (!roles.includes(staff.role)) {
    return (
      <p role="alert" className="rounded-2xl bg-white p-6 shadow-sm">
        Bạn không có quyền truy cập màn hình này.
      </p>
    )
  }
  return <>{children}</>
}
