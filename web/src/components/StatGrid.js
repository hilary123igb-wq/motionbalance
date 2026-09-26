import { playfair } from "@/lib/fonts";

export default function StatGrid({ stats, gridClassName = "grid-cols-2 sm:grid-cols-4" }) {
  return (
    <div
      className={`grid ${gridClassName} bg-indigo-50/40 border border-indigo-100/60 rounded-2xl divide-x divide-y sm:divide-y-0 divide-indigo-100/60 overflow-hidden`}
    >
      {stats.map((s) => (
        <div key={s.label} className="px-6 py-6">
          <div className={`${playfair.className} text-3xl font-semibold text-gray-900 tabular-nums`}>{s.value}</div>
          <div className="text-xs tracking-wide text-gray-400 uppercase mt-1.5">{s.label}</div>
        </div>
      ))}
    </div>
  );
}