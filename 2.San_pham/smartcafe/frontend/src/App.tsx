import { Navigate, Route, Routes } from 'react-router-dom'
import AdminLayout from './pages/admin/AdminLayout'
import BarPage from './pages/admin/BarPage'
import ComingSoonPage from './pages/admin/ComingSoonPage'
import LoginPage from './pages/admin/LoginPage'
import CartPage from './pages/qr/CartPage'
import MenuPage from './pages/qr/MenuPage'
import OrderPage from './pages/qr/OrderPage'
import OtpPlaceholderPage from './pages/qr/OtpPlaceholderPage'
import QrLayout from './pages/qr/QrLayout'
import WelcomePage from './pages/qr/WelcomePage'

export default function App() {
  return (
    <Routes>
      {/* QR Order Web App (khách) */}
      <Route path="/t/:qrToken" element={<QrLayout />}>
        <Route index element={<WelcomePage />} />
        <Route path="menu" element={<MenuPage />} />
        <Route path="otp" element={<OtpPlaceholderPage />} />
        <Route path="cart" element={<CartPage />} />
        <Route path="orders/:orderId" element={<OrderPage />} />
      </Route>

      {/* Web Admin (nhân viên) */}
      <Route path="/admin/login" element={<LoginPage />} />
      <Route path="/admin" element={<AdminLayout />}>
        <Route index element={<Navigate to="/admin/login" replace />} />
        <Route path="dashboard" element={<ComingSoonPage title="Dashboard bán hàng (W08)" flow="F8" />} />
        <Route path="bar" element={<BarPage />} />
      </Route>

      <Route path="/" element={<Navigate to="/admin/login" replace />} />
      <Route path="*" element={<p className="p-6 text-center">Không tìm thấy trang.</p>} />
    </Routes>
  )
}
