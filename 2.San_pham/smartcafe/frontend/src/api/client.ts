/** Gọi API backend. Lỗi trả về theo định dạng thống nhất {error: {code, message, details}} (IV.3 Mục 2.4). */
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details: Record<string, unknown> = {},
  ) {
    super(message)
  }
}

const NETWORK_ERROR = 'Không kết nối được máy chủ, vui lòng thử lại'

export async function request<T>(path: string, init: RequestInit & { token?: string | null } = {}): Promise<T> {
  const { token, headers, ...rest } = init
  let res: Response
  try {
    res = await fetch(path, {
      ...rest,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...headers,
      },
    })
  } catch {
    throw new ApiError(0, 'NETWORK_ERROR', NETWORK_ERROR)
  }
  const body = await res.json().catch(() => null)
  if (!res.ok) {
    const err = body?.error
    throw new ApiError(res.status, err?.code ?? 'HTTP_ERROR', err?.message ?? NETWORK_ERROR, err?.details ?? {})
  }
  return body as T
}
