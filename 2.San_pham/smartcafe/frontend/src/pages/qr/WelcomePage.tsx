import { useNavigate } from 'react-router-dom'
import QrHeader from './QrHeader'

/** W00 – Màn hình chào (UC01). Không ghi nhớ lựa chọn lần trước: lần quét nào cũng hiện màn hình này. */
export default function WelcomePage() {
  const navigate = useNavigate()
  return (
    <div className="mx-auto min-h-screen max-w-md">
      <QrHeader />
      <main className="space-y-4 p-4">
        <section>
          <h1 className="text-2xl font-bold text-coffee">Chào mừng bạn đến SmartCafe!</h1>
          <p className="text-stone-600">Bạn muốn gọi món theo cách nào?</p>
        </section>

        <section className="rounded-2xl border border-coffee/20 bg-white p-4 shadow-sm">
          <h2 className="text-lg font-semibold">Thành viên – Tích điểm</h2>
          <p className="mb-3 text-sm text-stone-600">
            Nhập số điện thoại để tích điểm (1 điểm cho mỗi 10.000đ) và nhận gợi ý theo sở thích của bạn.
          </p>
          <button
            className="w-full rounded-xl bg-coffee py-3 font-semibold text-white active:bg-coffee-dark"
            onClick={() => navigate('otp')}
          >
            Nhập số điện thoại
          </button>
        </section>

        <section className="rounded-2xl border border-coffee/20 bg-white p-4 shadow-sm">
          <h2 className="text-lg font-semibold">Xem menu ngay</h2>
          <p className="mb-3 text-sm text-stone-600">
            Không cần số điện thoại. Gợi ý món bán chạy, đang khuyến mãi và món mới.
          </p>
          <button
            className="w-full rounded-xl border-2 border-coffee py-3 font-semibold text-coffee active:bg-coffee/10"
            onClick={() => navigate('menu')}
          >
            Xem menu ngay
          </button>
        </section>

        <p className="text-center text-sm italic text-stone-500">Bạn có thể nhập số điện thoại sau tại menu.</p>
      </main>
    </div>
  )
}
