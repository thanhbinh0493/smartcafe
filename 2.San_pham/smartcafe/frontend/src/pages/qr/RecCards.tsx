import type { RecItem } from '../../api/recommend'
import { formatVND } from '../../lib/format'

/** Thẻ gợi ý cuộn ngang (W01 "Gợi ý cho bạn", W02 "Thường gọi kèm"): ảnh, tên, giá, lý do gợi ý, nút thêm. */
export default function RecCards({ title, items, onAdd, testId }: {
  title: string
  items: RecItem[]
  onAdd: (r: RecItem) => void
  testId: string
}) {
  if (items.length === 0) return null
  return (
    <section aria-label={title} data-testid={testId} className="mt-4">
      <h2 className="mb-2 text-sm font-bold uppercase tracking-wide text-coffee">{title}</h2>
      <ul className="-mx-4 flex gap-3 overflow-x-auto px-4 pb-2">
        {items.map((r) => (
          <li key={r.menu_item_id} className="w-40 shrink-0 space-y-1 rounded-xl bg-white p-3 shadow-sm">
            <div className="flex h-16 items-center justify-center rounded-lg bg-coffee/10 text-2xl" aria-hidden>
              {r.image_url ? <img src={r.image_url} alt="" className="h-full w-full rounded-lg object-cover" /> : '☕'}
            </div>
            <p className="line-clamp-2 text-sm font-medium">{r.name}</p>
            <p className="text-xs font-semibold text-promo">{r.reason}</p>
            <div className="flex items-center justify-between">
              <span className="text-sm">
                {r.is_promo && <del className="mr-1 text-xs text-stone-400">{formatVND(r.regular_price)}</del>}
                <b>{formatVND(r.sell_price)}</b>
              </span>
              <button onClick={() => onAdd(r)} aria-label={`Thêm ${r.name} (gợi ý)`}
                className="h-8 w-8 rounded-full bg-coffee text-xl leading-none text-white">+</button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  )
}
