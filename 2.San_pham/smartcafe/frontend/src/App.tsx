import { Navigate, Route, Routes } from 'react-router-dom'
import type { StaffRole } from './api/auth'
import AdminLayout from './pages/admin/AdminLayout'
import BarPage from './pages/admin/BarPage'
import BranchesPage from './pages/admin/BranchesPage'
import BranchMenuPage from './pages/admin/BranchMenuPage'
import CategoriesPage from './pages/admin/CategoriesPage'
import DashboardPage from './pages/admin/DashboardPage'
import LoginPage from './pages/admin/LoginPage'
import MenuItemsPage from './pages/admin/MenuItemsPage'
import { RequireRole } from './pages/admin/nav'
import PromotionsPage from './pages/admin/PromotionsPage'
import StaffPage from './pages/admin/StaffPage'
import TablesPage from './pages/admin/TablesPage'
import CartPage from './pages/qr/CartPage'
import MenuPage from './pages/qr/MenuPage'
import OrderPage from './pages/qr/OrderPage'
import OtpPage from './pages/qr/OtpPage'
import QrLayout from './pages/qr/QrLayout'
import WelcomePage from './pages/qr/WelcomePage'

const ADMIN: StaffRole[] = ['ADMIN']
const ADMIN_MANAGER: StaffRole[] = ['ADMIN', 'MANAGER']

export default function App() {
  return (
    <Routes>
      {/* QR Order Web App (khách) */}
      <Route path="/t/:qrToken" element={<QrLayout />}>
        <Route index element={<WelcomePage />} />
        <Route path="menu" element={<MenuPage />} />
        <Route path="otp" element={<OtpPage />} />
        <Route path="cart" element={<CartPage />} />
        <Route path="orders/:orderId" element={<OrderPage />} />
      </Route>

      {/* Web Admin (nhân viên) */}
      <Route path="/admin/login" element={<LoginPage />} />
      <Route path="/admin" element={<AdminLayout />}>
        <Route index element={<Navigate to="/admin/login" replace />} />
        <Route path="dashboard" element={<RequireRole roles={ADMIN_MANAGER}><DashboardPage /></RequireRole>} />
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

      <Route path="/" element={<Navigate to="/admin/login" replace />} />
      <Route path="*" element={<p className="p-6 text-center">Không tìm thấy trang.</p>} />
    </Routes>
  )
}
