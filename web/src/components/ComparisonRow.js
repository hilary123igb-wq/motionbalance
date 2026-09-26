import { playfair } from "@/lib/fonts";

function ArrowIcon({ direction }) {
  return (
    <svg
      className={`w-3 h-3 ${direction === "right" ? "rotate-180" : ""}`}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2.5}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 12H5m0 0l6-6m-6 6l6 6" />
    </svg>
  );
}

function formatDelta(magnitude) {
  return magnitude.toFixed(3).replace(/0+$/, "").replace(/\.$/, "");
}

// A restyled "A vs B" comparison card: two real average-point figures side
// by side with a center badge naming which side is ahead and by how much.
// `advantage` follows the sign convention already used in analytics.json -
// positive means leftStat is ahead, negative means rightStat is ahead.
export default function ComparisonRow({ title, leftStat, rightStat, advantage, unit = "pts" }) {
  const leftWins = advantage >= 0;
  const magnitude = formatDelta(Math.abs(advantage));
  const winnerLabel = leftWins ? leftStat.label : rightStat.label;
  const total = leftStat.value + rightStat.value;
  const leftPct = total > 0 ? (leftStat.value / total) * 100 : 50;

  return (
    <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-6">
      {title && <h3 className="text-sm font-semibold text-gray-900 mb-5">{title}</h3>}

      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-wide text-gray-400 mb-1">{leftStat.label}</div>
          <div className={`${playfair.className} text-3xl ${leftWins ? "text-indigo-600" : "text-gray-900"}`}>
            {leftStat.value}
          </div>
        </div>

        <span className="inline-flex items-center gap-1.5 bg-rose-50 text-rose-600 text-xs font-medium px-3 py-1.5 rounded-full whitespace-nowrap shrink-0">
          <ArrowIcon direction={leftWins ? "left" : "right"} />
          {winnerLabel} +{magnitude} {unit}
        </span>

        <div className="text-right">
          <div className="text-xs uppercase tracking-wide text-gray-400 mb-1">{rightStat.label}</div>
          <div className={`${playfair.className} text-3xl ${!leftWins ? "text-indigo-600" : "text-gray-900"}`}>
            {rightStat.value}
          </div>
        </div>
      </div>

      <div className="mt-5 h-2 rounded-full bg-gray-100 overflow-hidden flex">
        <div className="h-full bg-indigo-500" style={{ width: `${leftPct}%` }} />
        <div className="h-full bg-rose-400" style={{ width: `${100 - leftPct}%` }} />
      </div>
      <div className="flex justify-between text-[11px] text-gray-400 mt-1.5">
        <span>{leftStat.label}</span>
        <span>{rightStat.label}</span>
      </div>
    </div>
  );
}
