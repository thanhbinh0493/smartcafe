import { request } from './client'

export type StaffRole = 'ADMIN' | 'MANAGER' | 'CASHIER' | 'BARISTA'

export interface StaffMe {
  id: number
  username: string
  full_name: string
  role: StaffRole
  branch: { id: number; code: string; name: string } | null
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  staff: StaffMe
}

export const login = (username: string, password: string) =>
  request<LoginResponse>('/api/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) })

export const getMe = (token: string) => request<StaffMe>('/api/auth/me', { token })
