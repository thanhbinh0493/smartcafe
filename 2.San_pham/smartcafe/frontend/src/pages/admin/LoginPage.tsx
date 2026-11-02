import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { login } from '../../api/auth'
import type { ApiError } from '../../api/client'
import { defaultPathForRole, loadSession, saveSession } from '../../auth/staffSession'

/** A01 – Đăng nhập nhân viên (UC08). */
export default function LoginPage() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const existing = loadSession()
  if (existing) return <Navigate to={defaultPathForRole(existing.staff.role)} replace />

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const res = await login(username.trim(), password)
      saveSession(res.access_token, res.staff, res.expires_in)
      navigate(defaultPathForRole(res.staff.role), { replace: true })
    } catch (err) {
      setError((err as ApiError).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-4">
      <form onSubmit={onSubmit} className="w-full max-w-sm space-y-4 rounded-2xl bg-white p-6 shadow">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-coffee">SmartCafe Admin</h1>
          <p className="text-sm text-stone-500">Đăng nhập dành cho nhân viên</p>
        </div>
        <label className="block">
          <span className="text-sm font-medium">Tên đăng nhập</span>
          <input
            className="mt-1 w-full rounded-lg border border-stone-300 px-3 py-2 outline-none focus:border-coffee"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
          />
        </label>
        <label className="block">
          <span className="text-sm font-medium">Mật khẩu</span>
          <input
            type="password"
            className="mt-1 w-full rounded-lg border border-stone-300 px-3 py-2 outline-none focus:border-coffee"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </label>
        {error && (
          <p role="alert" className="text-sm text-red-600">
            {error}
          </p>
        )}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-coffee py-2.5 font-semibold text-white disabled:opacity-60"
        >
          {loading ? 'Đang đăng nhập...' : 'Đăng nhập'}
        </button>
      </form>
    </main>
  )
}
