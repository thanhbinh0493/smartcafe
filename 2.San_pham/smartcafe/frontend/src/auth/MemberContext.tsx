import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import type { OtpVerified } from '../api/customer'

/** Phiên khách thành viên (UC02, D18): customer token 1 giờ, CHỈ giữ trong sessionStorage của tab –
 *  đóng tab là mất, không lưu định danh thiết bị (D9, NFR-S7). Hết hạn thì tự về chế độ ẩn danh. */
const KEY = 'smartcafe.member'
export const POINT_VALUE_VND = 100 // D15: 1 điểm = 100đ
export const POINT_UNIT_VND = 10_000 // D15: 1 điểm / 10.000đ

export interface Member {
  token: string
  phoneMasked: string
  points: number
  expiresAt: number // ms
}

interface MemberValue {
  member: Member | null
  /** true khi phiên vừa tự hết hạn (để báo cho khách) */
  expired: boolean
  login: (v: OtpVerified) => void
  logout: () => void
  /** Phiên bị server từ chối (401): xóa phiên và báo hết hạn */
  expire: () => void
  setPoints: (points: number) => void
}

const MemberContext = createContext<MemberValue | null>(null)

function load(): Member | null {
  try {
    const m = JSON.parse(sessionStorage.getItem(KEY) ?? 'null') as Member | null
    if (!m?.token || m.expiresAt <= Date.now()) {
      sessionStorage.removeItem(KEY)
      return null
    }
    return m
  } catch {
    return null
  }
}

export function MemberProvider({ children }: { children: ReactNode }) {
  const [member, setMember] = useState<Member | null>(load)
  const [expired, setExpired] = useState(false)

  useEffect(() => {
    try {
      if (member) sessionStorage.setItem(KEY, JSON.stringify(member))
      else sessionStorage.removeItem(KEY)
    } catch {
      /* trình duyệt chặn storage: phiên chỉ sống trong bộ nhớ */
    }
  }, [member])

  // Tự hết phiên đúng lúc token hết hạn (1 giờ)
  useEffect(() => {
    if (!member) return
    const t = setTimeout(() => {
      setMember(null)
      setExpired(true)
    }, Math.max(0, member.expiresAt - Date.now()))
    return () => clearTimeout(t)
  }, [member])

  const login = useCallback((v: OtpVerified) => {
    setExpired(false)
    setMember({
      token: v.customer_token,
      phoneMasked: v.phone_masked,
      points: v.loyalty_points,
      expiresAt: new Date(v.expires_at).getTime(),
    })
  }, [])
  const logout = useCallback(() => {
    setExpired(false)
    setMember(null)
  }, [])
  const expire = useCallback(() => {
    setMember(null)
    setExpired(true)
  }, [])
  const setPoints = useCallback((points: number) => setMember((m) => (m ? { ...m, points } : m)), [])

  const value = useMemo(
    () => ({ member, expired, login, logout, expire, setPoints }),
    [member, expired, login, logout, expire, setPoints],
  )
  return <MemberContext.Provider value={value}>{children}</MemberContext.Provider>
}

export function useMember(): MemberValue {
  const ctx = useContext(MemberContext)
  if (!ctx) throw new Error('useMember phải dùng bên trong MemberProvider')
  return ctx
}

/** Lỗi 401 do customer token hết hạn / không hợp lệ */
export const isSessionError = (code: string, status: number) =>
  status === 401 && (code === 'TOKEN_EXPIRED' || code === 'UNAUTHORIZED')
