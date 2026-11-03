import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import type { StaffRole } from './api/auth'
import AdminLayout from './pages/admin/AdminLayout'
import BarPage from './pages/admin/BarPage'
import BranchesPage from './pages/admin/BranchesPage'
import BranchMenuPage from './pages/admin/BranchMenuPage'
import CategoriesPage from './pages/admin/CategoriesPage'
import LoginPage from './pages/admin/LoginPage'
import MenuItemsPage from './pages/admin/MenuItemsPage'
import { RequireRole } from './pages/admin/nav'
import PromotionsPage from './pages/admin/PromotionsPage'
import StaffPage from './pages/admin/StaffPage'
import TablesPage from './pages/admin/TablesPage'

// Dashboard kéo theo thư viện biểu đồ Recharts (~350 KB): tách riêng để màn hình Bar không phải tải.
const DashboardPage = lazy(() => import('./pages/admin/DashboardPage'))

const ADMIN: StaffRole[] = ['ADMIN']
const ADMIN_MANAGER: StaffRole[] = ['ADMIN', 'MANAGER']

/** Web Admin (nhân viên), tải riêng khỏi trang QR của khách (NFR-P1, BUG-ST-02). Đường dẫn tương đối với /admin. */
export default function AdminRoutes() {
  return (
    <Routes>
      <Route path="login" element={<LoginPage />} />
      <Route element={<AdminLayout />}>
        <Route index element={<Navigate to="/admin/login" replace />} />
        <Route
          path="dashboard"
          element={
            <RequireRole roles={ADMIN_MANAGER}>
              <Suspense fallback={<p>Đang tải...</p>}>
                <DashboardPage />
              </Suspense>
            </RequireRole>
          }
        />
        <Route path="bar" element={<BarPage />} />
        {/* F6 – Quản trị (UC09–UC15); quyền theo ma trận RBAC (III.1) */}
        <Route path="branches" element={<RequireRole roles={ADMIN}><BranchesPage /></RequireRole>} />
        <Route path="categories" element={<RequireRole roles={ADMIN}><CategoriesPage /></RequireRole>} />
        <Route path="menu-items" element={<RequireRole roles={ADMIN}><MenuItemsPage /></RequireRole>} />
        <Route path="promotions" element={<RequireRole roles={ADMIN}><PromotionsPage /></RequireRole>} />
        <Route path="staff" element={<RequireRole roles={ADMIN_MANAGER}><StaffPage /></RequireRole>} />
        <Route path="branch-menu" element={<RequireRole roles={ADMIN_MANAGER}><BranchMenuPage /></RequireRole>} />
        <Route path="tables" element={<RequireRole roles={ADMIN_MANAGER}><TablesPage /></RequireRole>} />
      </Route>
      <Route path="*" element={<p className="p-6 text-center">Không tìm thấy trang.</p>} />
    </Routes>
  )
}
