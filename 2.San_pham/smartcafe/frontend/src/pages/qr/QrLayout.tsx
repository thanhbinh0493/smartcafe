import { createContext, useContext, useEffect, useState } from 'react'
import { Outlet, useParams } from 'react-router-dom'
import { ApiError } from '../../api/client'
import { getTable, type TableInfo } from '../../api/public'
import { CartProvider } from '../../cart/CartContext'

interface QrContextValue {
  qrToken: string
  info: TableInfo
}

const QrContext = createContext<QrContextValue | null>(null)

export function useQr(): QrContextValue {
  const ctx = useContext(QrContext)
  if (!ctx) throw new Error('useQr phải dùng bên trong QrLayout')
  return ctx
}

/** Khung chung cho /t/:qrToken/*: tra cứu bàn 1 lần (UC01) rồi chia sẻ cho các màn hình con. */
export default function QrLayout() {
  const { qrToken = '' } = useParams()
  const [info, setInfo] = useState<TableInfo | null>(null)
  const [error, setError] = useState<ApiError | null>(null)

  useEffect(() => {
    let alive = true
    setInfo(null)
    setError(null)
    getTable(qrToken)
      .then((data) => alive && setInfo(data))
      .catch((e: ApiError) => alive && setError(e))
    return () => {
      alive = false
    }
  }, [qrToken])

  if (error) {
    return (
      <main className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center p-6 text-center">
        <div className="mb-4 text-5xl" aria-hidden>
          ☕
        </div>
        <h1 className="mb-2 text-xl font-bold text-coffee">
          {error.code === 'TABLE_NOT_FOUND' ? 'Mã QR không hợp lệ' : 'Có lỗi xảy ra'}
        </h1>
        <p role="alert">{error.message}</p>
      </main>
    )
  }
  if (!info) {
    return <p className="p-6 text-center text-coffee">Đang tải...</p>
  }
  return (
    <QrContext.Provider value={{ qrToken, info }}>
      <CartProvider qrToken={qrToken}>
        <Outlet />
      </CartProvider>
    </QrContext.Provider>
  )
}
