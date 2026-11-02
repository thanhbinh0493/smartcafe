/** Màn hình giữ chỗ cho các luồng chưa làm (W04 ở F3, W08 ở F8). */
export default function ComingSoonPage({ title, flow }: { title: string; flow: string }) {
  return (
    <section className="rounded-2xl bg-white p-6 shadow-sm">
      <h1 className="text-xl font-bold text-coffee">{title}</h1>
      <p className="text-stone-600">Màn hình này sẽ được xây dựng ở luồng {flow}.</p>
    </section>
  )
}
