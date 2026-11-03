import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import CartPage from './pages/qr/CartPage'
import MenuPage from './pages/qr/MenuPage'
import OrderPage from './pages/qr/OrderPage'
import OtpPage from './pages/qr/OtpPage'
import QrLayout from './pages/qr/QrLayout'
import WelcomePage from './pages/qr/WelcomePage'

// Web Admin tải riêng (lazy): điện thoại khách quét QR chỉ tải phần QR Order (NFR-P1, BUG-ST-02).
const AdminRoutes = lazy(() => import('./AdminRoutes'))

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
      <Route
        path="/admin/*"
        element={
          <Suspense fallback={<p className="p-6 text-center">Đang tải...</p>}>
            <AdminRoutes />
          </Suspense>
        }
      />

      <Route path="/" element={<Navigate to="/admin/login" replace />} />
      <Route path="*" element={<p className="p-6 text-center">Không tìm thấy trang.</p>} />
    </Routes>
  )
}
