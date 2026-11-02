import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import type { ApiError } from '../../api/client'
import { getMenu, type Menu, type MenuItem } from '../../api/public'
import { formatVND, normalizeText } from '../../lib/format'
import QrHeader from './QrHeader'
import { useQr } from './QrLayout'

const ALL = 'all'
const PROMO = 'promo'

/** W01 – Menu điện tử (UC03). Khối gợi ý món (F7) và giỏ hàng (F2) sẽ được thêm ở các luồng sau. */
export default function MenuPage() {
  const { info } = useQr()
  const [menu, setMenu] = useState<Menu | null>(null)
  const [error, setError] = useState<ApiError | null>(null)
  const [tab, setTab] = useState<string>(ALL)
  const [query, setQuery] = useState('')

  const load = useCallback(() => {
    setError(null)
    getMenu(info.branch.id)
      .then(setMenu)
      .catch((e: ApiError) => setError(e))
  }, [info.branch.id])

  useEffect(load, [load])

  const sections = useMemo(() => {
    if (!menu) return []
    const q = normalizeText(query)
    const match = (it: MenuItem) => !q || normalizeText(it.name).includes(q)
    if (tab === PROMO) {
      const items = menu.categories.flatMap((c) => c.items).filter((it) => it.is_promo && match(it))
      return [{ id: -1, name: 'Đang khuyến mãi', items }]
    }
    return menu.categories
      .filter((c) => tab === ALL || String(c.id) === tab)
      .map((c) => ({ ...c, items: c.items.filter(match) }))
      .filter((c) => c.items.length > 0)
  }, [menu, tab, query])

  const hasPromo = menu?.categories.some((c) => c.items.some((i) => i.is_promo)) ?? false
  const empty = sections.every((s) => s.items.length === 0)

  return (
    <div className="mx-auto min-h-screen max-w-md pb-8">
      <QrHeader />
      <div className="flex items-center justify-between gap-2 bg-white px-4 py-2 text-sm">
        <span className="text-stone-600">Khách vãng lai</span>
        <Link to="../otp" relative="path" className="rounded-full border border-coffee px-3 py-1 font-medium text-coffee">
          Nhập SĐT tích điểm
        </Link>
      </div>

      <div className="sticky top-12 z-10 space-y-2 bg-cream px-4 pb-2 pt-3">
        <input
          type="search"
          placeholder="Tìm món..."
          aria-label="Tìm món"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full rounded-xl border border-stone-300 bg-white px-4 py-2 outline-none focus:border-coffee"
        />
        {menu && (
          <nav className="flex gap-2 overflow-x-auto pb-1" aria-label="Danh mục">
            <TabButton active={tab === ALL} onClick={() => setTab(ALL)}>
              Tất cả
            </TabButton>
            {hasPromo && (
              <TabButton active={tab === PROMO} onClick={() => setTab(PROMO)}>
                Khuyến mãi
              </TabButton>
            )}
            {menu.categories.map((c) => (
              <TabButton key={c.id} active={tab === String(c.id)} onClick={() => setTab(String(c.id))}>
                {c.name}
              </TabButton>
            ))}
          </nav>
        )}
      </div>

      <main className="px-4">
        {error && (
          <div role="alert" className="my-6 text-center">
            <p className="mb-2">{error.message}</p>
            <button className="rounded-lg bg-coffee px-4 py-2 text-white" onClick={load}>
              Thử lại
            </button>
          </div>
        )}
        {!menu && !error && <p className="py-6 text-center text-coffee">Đang tải menu...</p>}
        {menu && empty && <p className="py-6 text-center text-stone-500">Không tìm thấy món phù hợp.</p>}
        {sections.map((s) =>
          s.items.length === 0 ? null : (
            <section key={s.id} className="mt-4">
              <h2 className="mb-2 text-sm font-bold uppercase tracking-wide text-coffee">{s.name}</h2>
              <ul className="space-y-2">
                {s.items.map((it) => (
                  <MenuRow key={it.id} item={it} />
                ))}
              </ul>
            </section>
          ),
        )}
      </main>
    </div>
  )
}

function TabButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      aria-pressed={active}
      className={`shrink-0 rounded-full px-4 py-1.5 text-sm font-medium ${
        active ? 'bg-coffee text-white' : 'border border-coffee/30 bg-white text-coffee'
      }`}
    >
      {children}
    </button>
  )
}

function MenuRow({ item }: { item: MenuItem }) {
  return (
    <li
      data-testid={`menu-item-${item.id}`}
      className={`flex items-center gap-3 rounded-xl bg-white p-3 shadow-sm ${item.is_available ? '' : 'opacity-50'}`}
    >
      <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-lg bg-coffee/10 text-2xl" aria-hidden>
        {item.image_url ? <img src={item.image_url} alt="" className="h-full w-full rounded-lg object-cover" /> : '☕'}
      </div>
      <div className="min-w-0 flex-1">
        <p className="font-medium">
          {item.name}
          {item.is_new && (
            <span className="ml-2 rounded bg-new px-1.5 py-0.5 align-middle text-[10px] font-bold text-white">MỚI</span>
          )}
        </p>
        <p className="text-sm">
          {item.is_promo && (
            <del className="mr-2 text-stone-400" aria-label={`Giá gốc ${formatVND(item.regular_price)}`}>
              {formatVND(item.regular_price)}
            </del>
          )}
          <span className={item.is_promo ? 'font-semibold text-promo' : 'font-semibold'}>{formatVND(item.sell_price)}</span>
        </p>
      </div>
      {!item.is_available && <span className="text-sm font-medium text-red-600">Tạm hết</span>}
    </li>
  )
}
