import TopicEmptyState from "@/components/TopicEmptyState";

// Same fixed OG/OO/CG/CO order and colors as StrengthBandChart - one
// position always means one color everywhere on the site.
const POSITIONS = [
  { key: "OG", color: "#2a78d6" },
  { key: "OO", color: "#eb6834" },
  { key: "CG", color: "#1baf7a" },
  { key: "CO", color: "#eda100" },
];

// BP scoring is 0-3 points per team per debate, so that's the fixed scale
// for the bars - not derived from whatever the max observed value happens
// to be, which would make the same average look different across pages.
const POINTS_SCALE = 3;

function aggregateByPosition(rows) {
  const totals = {};
  for (const r of rows) {
    const t = (totals[r.position] ??= { sum: 0, n: 0 });
    t.sum += r.avg_points * r.n;
    t.n += r.n;
  }
  return POSITIONS.map((p) => {
    const t = totals[p.key];
    return { ...p, avg: t && t.n > 0 ? t.sum / t.n : null, n: t?.n || 0 };
  });
}

export default function PositionBalancePanel({ rows }) {
  if (!rows || rows.length === 0) return <TopicEmptyState title="Position balance" />;
  const positions = aggregateByPosition(rows);

  return (
    <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-6">
      <h3 className="text-sm font-semibold text-gray-900 mb-1">Position balance</h3>
      <p className="text-xs text-gray-400 mb-4">
        Average points per position, pooled across every topic-classified motion — not adjusted for team strength.
      </p>
      <div className="space-y-3">
        {positions.map((p) => (
          <div key={p.key} className="flex items-center gap-3">
            <span className="text-xs font-medium text-gray-500 w-7 shrink-0">{p.key}</span>
            <div className="flex-1 h-2.5 bg-gray-50 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full"
                style={{
                  width: `${p.avg != null ? (p.avg / POINTS_SCALE) * 100 : 0}%`,
                  backgroundColor: p.color,
                }}
              />
            </div>
            <span className="text-xs text-gray-400 tabular-nums w-28 text-right shrink-0">
              {p.avg != null ? `${p.avg.toFixed(2)} pts (n=${p.n})` : "no data"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
