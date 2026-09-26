import { playfair } from "@/lib/fonts";

function formatDelta(magnitude) {
  return magnitude.toFixed(3).replace(/0+$/, "").replace(/\.$/, "");
}

// A compact "A vs B" comparison row: a small delta badge up top, a thin
// split bar showing the real share of the two average-point figures, and
// the figures themselves underneath. `advantage` follows the sign
// convention already used in analytics.json - positive means leftStat is
// ahead, negative means rightStat is ahead.
export default function ComparisonRow({ title, leftStat, rightStat, advantage, unit = "pts" }) {
  const leftWins = advantage >= 0;
  const magnitude = formatDelta(Math.abs(advantage));
  const winnerLabel = leftWins ? leftStat.label : rightStat.label;
  const total = leftStat.value + rightStat.value;
  const leftPct = total > 0 ? (leftStat.value / total) * 100 : 50;

  return (
    <div className="bg-white border border-gray-100 rounded-2xl shadow-sm px-5 py-4">
      <div className="flex items-center justify-between gap-3 mb-3">
        {title && <h3 className="text-sm font-semibold text-gray-900">{title}</h3>}
        <span className="inline-flex items-center gap-1 bg-rose-50 text-rose-600 text-[11px] font-medium px-2.5 py-1 rounded-full whitespace-nowrap shrink-0">
          {winnerLabel} +{magnitude} {unit}
        </span>
      </div>

      <div className="flex items-center gap-3">
        <span className="text-xs text-gray-500 w-16 shrink-0">{leftStat.label}</span>
        <div className="flex-1 h-2 rounded-full bg-gray-100 overflow-hidden flex">
          <div className="h-full bg-indigo-500" style={{ width: `${leftPct}%` }} />
          <div className="h-full bg-rose-400" style={{ width: `${100 - leftPct}%` }} />
        </div>
        <span className="text-xs text-gray-500 w-16 shrink-0 text-right">{rightStat.label}</span>
      </div>

      <div className="flex justify-between mt-1.5">
        <span className={`${playfair.className} text-lg font-semibold ${leftWins ? "text-indigo-600" : "text-gray-900"}`}>
          {leftStat.value}
        </span>
        <span className={`${playfair.className} text-lg font-semibold ${!leftWins ? "text-indigo-600" : "text-gray-900"}`}>
          {rightStat.value}
        </span>
      </div>
    </div>
  );
}
