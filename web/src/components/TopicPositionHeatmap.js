import TopicEmptyState from "@/components/TopicEmptyState";

const POSITION_ORDER = ["OG", "OO", "CG", "CO"];

function cellShade(value, min, max) {
  if (value == null || max === min) return "rgba(99, 102, 241, 0.12)";
  const ratio = (value - min) / (max - min);
  // Light indigo -> solid indigo, scaled by where this cell falls in the
  // observed range - a plain sequential heatmap, not a judgment of
  // "good"/"bad" position outcomes.
  const alpha = 0.08 + ratio * 0.55;
  return `rgba(99, 102, 241, ${alpha.toFixed(3)})`;
}

export default function TopicPositionHeatmap({ rows }) {
  if (!rows || rows.length === 0) return <TopicEmptyState title="Position advantage by topic" />;

  const byTopic = {};
  for (const r of rows) {
    (byTopic[r.topic] ??= {})[r.position] = r;
  }
  const topics = Object.keys(byTopic).sort(
    (a, b) => POSITION_ORDER.reduce((s, p) => s + (byTopic[b][p]?.n || 0), 0) - POSITION_ORDER.reduce((s, p) => s + (byTopic[a][p]?.n || 0), 0)
  );

  const values = rows.map((r) => r.avg_points);
  const min = Math.min(...values);
  const max = Math.max(...values);

  return (
    <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-6">
      <h3 className="text-sm font-semibold text-gray-900 mb-1">Position advantage by topic</h3>
      <p className="text-xs text-gray-400 mb-4">
        Average points earned from each BP position, split by topic. Darker = higher average within this table;
        pooled across all tournaments, not adjusted for team strength.
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-separate border-spacing-1">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wide text-gray-400">
              <th className="py-1 pr-3 font-medium">Topic</th>
              {POSITION_ORDER.map((p) => (
                <th key={p} className="py-1 px-2 font-medium text-center">{p}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {topics.map((topic) => (
              <tr key={topic}>
                <td className="py-1 pr-3 text-gray-700 whitespace-nowrap">{topic}</td>
                {POSITION_ORDER.map((p) => {
                  const cell = byTopic[topic][p];
                  return (
                    <td
                      key={p}
                      className="py-2 px-2 text-center rounded-lg text-gray-900 font-medium"
                      style={{ backgroundColor: cellShade(cell?.avg_points, min, max) }}
                      title={cell ? `${topic} × ${p}: ${cell.avg_points} pts (n=${cell.n})` : `${topic} × ${p}: no data`}
                    >
                      {cell ? cell.avg_points : <span className="text-gray-300 font-normal">—</span>}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
