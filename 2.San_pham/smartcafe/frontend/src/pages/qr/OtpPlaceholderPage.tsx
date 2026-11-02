import { Link } from 'react-router-dom'
import QrHeader from './QrHeader'

/** W00a – sẽ làm ở luồng F4 (OTP & tích điểm). */
export default function OtpPlaceholderPage() {
  return (
    <div className="mx-auto min-h-screen max-w-md">
      <QrHeader />
      <main className="space-y-4 p-6 text-center">
        <h1 className="text-xl font-bold text-coffee">Đăng nhập thành viên</h1>
        <p className="text-stone-600">Chức năng nhập số điện thoại và mã OTP đang được phát triển.</p>
        <Link to="../menu" relative="path" className="inline-block rounded-xl bg-coffee px-6 py-3 font-semibold text-white">
          Xem menu ngay
        </Link>
      </main>
    </div>
  )
}
