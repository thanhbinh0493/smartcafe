import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeAll, vi } from 'vitest'

// Web Admin và Dashboard được tải lazy (BUG-ST-02). Nạp sẵn module trước mỗi file test để lần render đầu
// không phải chờ biên dịch (khi chạy --coverage có thể > 1 giây, vượt thời gian chờ mặc định của findBy).
beforeAll(async () => {
  await import('../AdminRoutes')
  await import('../pages/admin/DashboardPage')
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
  localStorage.clear()
  sessionStorage.clear()
})
