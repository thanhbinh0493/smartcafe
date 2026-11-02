import { useQr } from './QrLayout'

export default function QrHeader() {
  const { info } = useQr()
  return (
    <header className="sticky top-0 z-10 flex items-center justify-between bg-coffee px-4 py-3 text-white shadow">
      <span className="font-semibold">{info.branch.name}</span>
      <span className="rounded-full bg-white/20 px-3 py-1 text-sm">Bàn {info.table.table_number}</span>
    </header>
  )
}
