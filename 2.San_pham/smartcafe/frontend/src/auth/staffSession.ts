import type { StaffMe, StaffRole } from '../api/auth'

/** Phiên nhân viên (JWT 8 giờ = 1 ca) lưu ở localStorage của máy quầy/tablet.
 *  Khách hàng KHÔNG lưu gì lâu dài trên thiết bị (NFR-S7). */
const KEY = 'smartcafe.staff'

export interface StaffSession {
  token: string
  staff: StaffMe
  expiresAt: number
}

export function saveSession(token: string, staff: StaffMe, expiresInSec: number): void {
  const s: StaffSession = { token, staff, expiresAt: Date.now() + expiresInSec * 1000 }
  localStorage.setItem(KEY, JSON.stringify(s))
}

export function loadSession(): StaffSession | null {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return null
    const s = JSON.parse(raw) as StaffSession
    if (!s.token || s.expiresAt <= Date.now()) {
      clearSession()
      return null
    }
    return s
  } catch {
    return null
  }
}

export function clearSession(): void {
  localStorage.removeItem(KEY)
}

/** Màn hình mặc định sau đăng nhập (IV.2 Mục 2). */
export function defaultPathForRole(role: StaffRole): string {
  return role === 'ADMIN' || role === 'MANAGER' ? '/admin/dashboard' : '/admin/bar'
}
