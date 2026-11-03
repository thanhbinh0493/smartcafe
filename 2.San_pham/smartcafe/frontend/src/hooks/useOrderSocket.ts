import { useEffect, useRef, useState } from 'react'

export interface WsMessage {
  type: string
  data: Record<string, unknown>
  ts: string | null
}

const BACKOFF_MS = [1000, 2000, 5000, 10000]
/** Mã đóng do server từ chối (sai token / không có quyền / sai mã đơn): không thử kết nối lại. */
const STOP_CODES = [4401, 4403, 4404]

/** Kết nối WebSocket tới `path` (VD /ws/bar/1?token=...), tự kết nối lại khi rớt mạng (NFR-R3).
 *  `onOpen` chạy mỗi lần kết nối (lại) thành công – nơi client tải lại dữ liệu để không lỡ sự kiện. */
export function useSocket(path: string, onMessage: (msg: WsMessage) => void, onOpen?: () => void) {
  const [connected, setConnected] = useState(false)
  const handler = useRef(onMessage)
  const openHandler = useRef(onOpen)
  handler.current = onMessage
  openHandler.current = onOpen

  useEffect(() => {
    let ws: WebSocket | null = null
    let attempt = 0
    let timer: ReturnType<typeof setTimeout> | undefined
    let stopped = false

    const connect = () => {
      const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
      ws = new WebSocket(`${proto}://${window.location.host}${path}`)
      ws.onopen = () => {
        attempt = 0
        setConnected(true)
        openHandler.current?.()
      }
      ws.onmessage = (ev) => {
        try {
          handler.current(JSON.parse(ev.data) as WsMessage)
        } catch {
          /* bỏ qua message hỏng */
        }
      }
      ws.onclose = (ev) => {
        setConnected(false)
        if (stopped || STOP_CODES.includes(ev.code)) return
        timer = setTimeout(connect, BACKOFF_MS[Math.min(attempt++, BACKOFF_MS.length - 1)])
      }
    }
    connect()

    return () => {
      stopped = true
      clearTimeout(timer)
      ws?.close()
    }
  }, [path])

  return connected
}

/** Trang theo dõi đơn: /ws/order/{id}?token=... Mỗi lần kết nối (lại), server gửi ORDER_SNAPSHOT. */
export function useOrderSocket(orderId: number, token: string, onMessage: (msg: WsMessage) => void) {
  return useSocket(`/ws/order/${orderId}?token=${encodeURIComponent(token)}`, onMessage)
}
