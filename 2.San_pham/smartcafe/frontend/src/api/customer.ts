import { request } from './client'

export interface OtpRequested {
  expires_in: number
  resend_after: number
  phone_masked: string
  demo_code: string | null
}

export interface OtpVerified {
  customer_token: string
  expires_at: string
  phone_masked: string
  loyalty_points: number
}

export interface LoyaltyTx {
  order_code: string | null
  points: number
  type: 'EARN' | 'ADJUST'
  created_at: string
}

export interface CustomerMe {
  phone_masked: string
  loyalty_points: number
  point_value_vnd: number
  points_value: number
  recent_transactions: LoyaltyTx[]
}

export const requestOtp = (phone: string) =>
  request<OtpRequested>('/api/public/otp/request', { method: 'POST', body: JSON.stringify({ phone }) })

export const verifyOtp = (phone: string, code: string) =>
  request<OtpVerified>('/api/public/otp/verify', { method: 'POST', body: JSON.stringify({ phone, code }) })

export const getMe = (token: string) => request<CustomerMe>('/api/public/me', { token })
