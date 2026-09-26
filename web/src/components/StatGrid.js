import { playfair } from "@/lib/fonts";

const ACCENTS = ["bg-indigo-400", "bg-rose-400"];

export default function StatGrid({ stats, gridClassName = "grid-cols-2 sm:grid-cols-4" }) {
  return (
    <div className={`grid ${gridClassName} bg-white border border-gray-100 rounded-2xl shadow-sm divide-x divide-y sm:divide-y-0 divide-gray-100 overflow-hidden`}>
      {stats.map((s, i) => (
        <div key={s.label} className="relative px-6 py-6 overflow-hidden">
          <span className={`absolute top-0 left-0 right-0 h-[3px] ${ACCENTS[i % ACCENTS.length]}`} />
          <div className={`${playfair.className} text-3xl font-semibold text-gray-900 tabular-nums`}>{s.value}</div>
          <div className="text-xs tracking-wide text-gray-400 uppercase mt-1.5">{s.label}</div>
        </div>
      ))}
    </div>
  );
}