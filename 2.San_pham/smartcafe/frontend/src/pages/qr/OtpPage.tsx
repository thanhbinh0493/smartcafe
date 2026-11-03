import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import type { ApiError } from '../../api/client'
import { requestOtp, verifyOtp } from '../../api/customer'
import { useMember } from '../../auth/MemberContext'
import QrHeader from './QrHeader'

const LEN = 6

interface Sent {
  phone: string
  phoneMasked: string
  demoCode: string | null
  expiresAt: number
  resendAt: number
}

const mmss = (sec: number) => `${String(Math.floor(sec / 60)).padStart(2, '0')}:${String(sec % 60).padStart(2, '0')}`

/** W00a – Nhập SĐT và mã OTP giả lập (UC02, SD01). */
export default function OtpPage() {
  const navigate = useNavigate()
  const { login } = useMember()
  const [phone, setPhone] = useState('')
  const [sent, setSent] = useState<Sent | null>(null)
  const [digits, setDigits] = useState<string[]>(Array(LEN).fill(''))
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [now, setNow] = useState(Date.now())
  const boxes = useRef<(HTMLInputElement | null)[]>([])

  // Đồng hồ đếm ngược hạn mã và thời gian chờ gửi lại
  useEffect(() => {
    if (!sent) return
    const t = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(t)
  }, [sent])

  const secLeft = (at: number) => Math.max(0, Math.ceil((at - now) / 1000))

  async function send(target: string) {
    setBusy(true)
    setError(null)
    try {
      const r = await requestOtp(target)
      const t = Date.now()
      setNow(t)
      setSent({
        phone: target,
        phoneMasked: r.phone_masked,
        demoCode: r.demo_code,
        expiresAt: t + r.expires_in * 1000,
        resendAt: t + r.resend_after * 1000,
      })
      setDigits(Array(LEN).fill(''))
      setTimeout(() => boxes.current[0]?.focus(), 0)
    } catch (e) {
      const err = e as ApiError
      setError(err.message)
      const retry = Number(err.details.retry_after)
      if (err.code === 'OTP_RATE_LIMITED' && sent && retry > 0) {
        const t = Date.now()
        setNow(t) // đếm ngược tính từ thời điểm hiện tại, không đợi nhịp đồng hồ kế tiếp (BUG-F4-02)
        setSent({ ...sent, resendAt: t + retry * 1000 })
      }
    } finally {
      setBusy(false)
    }
  }

  async function confirm(e: FormEvent) {
    e.preventDefault()
    if (!sent) return
    setBusy(true)
    setError(null)
    try {
      login(await verifyOtp(sent.phone, digits.join('')))
      navigate('../menu', { relative: 'path', replace: true })
    } catch (e) {
      const err = e as ApiError
      setError(err.message)
      setDigits(Array(LEN).fill(''))
      boxes.current[0]?.focus()
    } finally {
      setBusy(false)
    }
  }

  /** Gõ từng số hoặc dán cả mã 6 số vào một ô */
  function typeAt(i: number, value: string) {
    const nums = value.replace(/\D/g, '')
    if (!nums) {
      setDigits((d) => d.map((x, k) => (k === i ? '' : x)))
      return
    }
    const next = [...digits]
    let k = i
    for (const ch of nums.slice(0, LEN - i)) next[k++] = ch
    setDigits(next)
    boxes.current[Math.min(k, LEN - 1)]?.focus()
  }

  const back = () => {
    if (sent) {
      setSent(null)
      setError(null)
    } else navigate('..', { relative: 'path' })
  }

  const header = (title: string) => (
    <div className="flex items-center gap-2">
      {/* type="button": nút nằm trong form, không được gửi form (BUG-F4-01) */}
      <button type="button" onClick={back} aria-label="Quay lại" className="h-9 w-9 rounded-full border border-coffee text-coffee">
        ‹
      </button>
      <h1 className="text-xl font-bold text-coffee">{title}</h1>
    </div>
  )

  const alert = error && (
    <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-700">
      {error}
    </p>
  )

  if (!sent) {
    return (
      <div className="mx-auto min-h-screen max-w-md">
        <QrHeader />
        <form
          className="space-y-4 p-4"
          onSubmit={(e) => {
            e.preventDefault()
            send(phone)
          }}
        >
          {header('Thành viên tích điểm')}
          <label className="block space-y-1">
            <span className="font-medium">Số điện thoại</span>
            <input
              type="tel"
              inputMode="tel"
              autoComplete="tel"
              autoFocus
              placeholder="0912 345 678"
              value={phone}
              maxLength={20}
              onChange={(e) => setPhone(e.target.value)}
              className="w-full rounded-xl border border-stone-300 bg-white px-4 py-3 text-lg outline-none focus:border-coffee"
            />
          </label>
          <p className="text-sm italic text-stone-600">
            Chỉ dùng để tích điểm (1 điểm cho mỗi 10.000đ) và gợi ý món theo sở thích của bạn.
          </p>
          {alert}
          <button
            type="submit"
            disabled={busy || phone.replace(/\D/g, '').length < 9}
            className="w-full rounded-xl bg-coffee py-3 font-semibold text-white disabled:opacity-50"
          >
            {busy ? 'Đang gửi...' : 'Gửi mã OTP'}
          </button>
        </form>
      </div>
    )
  }

  const expiresIn = secLeft(sent.expiresAt)
  const resendIn = secLeft(sent.resendAt)
  return (
    <div className="mx-auto min-h-screen max-w-md">
      <QrHeader />
      <form className="space-y-4 p-4" onSubmit={confirm}>
        {header('Nhập mã xác thực')}
        <p>
          Mã 6 số đã gửi tới <b>{sent.phoneMasked}</b>
        </p>
        <div className="flex justify-between gap-2">
          {digits.map((d, i) => (
            <input
              key={i}
              ref={(el) => {
                boxes.current[i] = el
              }}
              aria-label={`Số thứ ${i + 1} của mã OTP`}
              inputMode="numeric"
              autoComplete={i === 0 ? 'one-time-code' : 'off'}
              value={d}
              onChange={(e) => typeAt(i, e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Backspace' && !digits[i] && i > 0) boxes.current[i - 1]?.focus()
              }}
              className="h-14 w-12 rounded-xl border border-stone-300 bg-white text-center text-2xl font-bold outline-none focus:border-coffee"
            />
          ))}
        </div>
        <p className="text-sm italic text-stone-600" data-testid="otp-expiry">
          {expiresIn > 0 ? `Mã hết hạn sau ${mmss(expiresIn)}` : 'Mã đã hết hạn, vui lòng gửi lại mã'}
        </p>
        <button
          type="button"
          onClick={() => send(sent.phone)}
          disabled={busy || resendIn > 0}
          className="w-full rounded-xl border-2 border-coffee py-2 font-medium text-coffee disabled:border-stone-300 disabled:text-stone-400"
        >
          {resendIn > 0 ? `Gửi lại mã (sau ${resendIn}s)` : 'Gửi lại mã'}
        </button>
        {sent.demoCode && (
          <p className="rounded-lg border border-dashed border-amber-500 bg-amber-50 p-3 text-sm italic text-amber-900">
            [DEMO] Mã OTP giả lập: <b data-testid="demo-code">{sent.demoCode}</b>
          </p>
        )}
        {alert}
        <button
          type="submit"
          disabled={busy || digits.some((d) => !d)}
          className="w-full rounded-xl bg-coffee py-3 font-semibold text-white disabled:opacity-50"
        >
          {busy ? 'Đang xác thực...' : 'Xác nhận'}
        </button>
      </form>
    </div>
  )
}
