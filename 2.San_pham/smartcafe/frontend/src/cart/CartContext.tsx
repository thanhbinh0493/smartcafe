import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import type { PriceChange } from '../api/orders'
import type { MenuItem } from '../api/public'

/** Giỏ hàng giữ trong sessionStorage của tab cho tới khi đặt (SD03) – không lưu lâu dài trên thiết bị (NFR-S7). */
export const MAX_QTY = 20

export interface CartLine {
  menu_item_id: number
  name: string
  regular_price: number
  sell_price: number
  is_promo: boolean
  quantity: number
  note: string
  is_recommended: boolean
}

interface CartValue {
  lines: CartLine[]
  count: number
  subtotal: number
  total: number
  add: (item: MenuItem, recommended?: boolean) => void
  setQuantity: (menuItemId: number, quantity: number) => void
  setNote: (menuItemId: number, note: string) => void
  remove: (menuItemId: number) => void
  applyPrices: (changes: PriceChange[]) => void
  clear: () => void
}

const CartContext = createContext<CartValue | null>(null)

const keyOf = (qrToken: string) => `smartcafe.cart.${qrToken}`

function load(key: string): CartLine[] {
  try {
    return JSON.parse(sessionStorage.getItem(key) ?? '[]') as CartLine[]
  } catch {
    return []
  }
}

export function CartProvider({ qrToken, children }: { qrToken: string; children: ReactNode }) {
  const key = keyOf(qrToken)
  const [lines, setLines] = useState<CartLine[]>(() => load(key))

  useEffect(() => {
    try {
      if (lines.length) sessionStorage.setItem(key, JSON.stringify(lines))
      else sessionStorage.removeItem(key)
    } catch {
      /* trình duyệt chặn storage: giỏ vẫn chạy trong bộ nhớ */
    }
  }, [key, lines])

  const add = useCallback((item: MenuItem, recommended = false) => {
    setLines((prev) => {
      const found = prev.find((l) => l.menu_item_id === item.id)
      if (found) {
        return prev.map((l) =>
          l.menu_item_id === item.id ? { ...l, quantity: Math.min(MAX_QTY, l.quantity + 1) } : l,
        )
      }
      return [
        ...prev,
        {
          menu_item_id: item.id,
          name: item.name,
          regular_price: item.regular_price,
          sell_price: item.sell_price,
          is_promo: item.is_promo,
          quantity: 1,
          note: '',
          is_recommended: recommended,
        },
      ]
    })
  }, [])

  const setQuantity = useCallback((id: number, quantity: number) => {
    setLines((prev) =>
      quantity <= 0
        ? prev.filter((l) => l.menu_item_id !== id)
        : prev.map((l) => (l.menu_item_id === id ? { ...l, quantity: Math.min(MAX_QTY, quantity) } : l)),
    )
  }, [])

  const setNote = useCallback((id: number, note: string) => {
    setLines((prev) => prev.map((l) => (l.menu_item_id === id ? { ...l, note: note.slice(0, 255) } : l)))
  }, [])

  const remove = useCallback((id: number) => setLines((prev) => prev.filter((l) => l.menu_item_id !== id)), [])

  const applyPrices = useCallback((changes: PriceChange[]) => {
    const byId = new Map(changes.map((c) => [c.menu_item_id, c]))
    setLines((prev) =>
      prev.map((l) => {
        const c = byId.get(l.menu_item_id)
        return c ? { ...l, regular_price: c.regular_price, sell_price: c.sell_price, is_promo: c.is_promo } : l
      }),
    )
  }, [])

  const clear = useCallback(() => setLines([]), [])

  const value = useMemo<CartValue>(
    () => ({
      lines,
      count: lines.reduce((s, l) => s + l.quantity, 0),
      subtotal: lines.reduce((s, l) => s + l.regular_price * l.quantity, 0),
      total: lines.reduce((s, l) => s + l.sell_price * l.quantity, 0),
      add,
      setQuantity,
      setNote,
      remove,
      applyPrices,
      clear,
    }),
    [lines, add, setQuantity, setNote, remove, applyPrices, clear],
  )

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>
}

export function useCart(): CartValue {
  const ctx = useContext(CartContext)
  if (!ctx) throw new Error('useCart phải dùng bên trong CartProvider')
  return ctx
}
