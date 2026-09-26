export function BarChart({ data, labelKey = "label", valueKey = "value", formatValue }) {
  const max = Math.max(...data.map((d) => d[valueKey]), 0.001);
  return (
    <div className="space-y-3">
      {data.map((d, i) => {
        const value = d[valueKey];
        const pct = Math.max(4, (value / max) * 100);
        const color = i % 2 === 0 ? "bg-indigo-500" : "bg-rose-400";
        return (
          <div key={d[labelKey]} className="flex items-center gap-3">
            <div className="w-28 shrink-0 text-sm text-gray-500">{d[labelKey]}</div>
            <div className="flex-1 h-3 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`h-full ${color} rounded-full`}
                style={{ width: `${pct}%` }}
                title={`${d[labelKey]}: ${formatValue ? formatValue(value) : value}`}
              />
            </div>
            <div className="w-16 text-right text-sm font-medium text-gray-900">
              {formatValue ? formatValue(value) : value}
            </div>
          </div>
        );
      })}
    </div>
  );
}

const RANK_COLORS = ["bg-indigo-600", "bg-indigo-400", "bg-indigo-300", "bg-indigo-200"];
const RANK_LABELS = ["1st", "2nd", "3rd", "4th"];

export function FinishDistribution({ distribution }) {
  if (!distribution || distribution.length === 0) return null;
  return (
    <div className="space-y-3">
      {distribution.map((row) => (
        <div key={row.position} className="flex items-center gap-3">
          <div className="w-10 shrink-0 text-sm font-medium text-gray-700">{row.position}</div>
          <div className="flex-1 h-4 rounded-full overflow-hidden flex bg-gray-100">
            {[row.pct_1st, row.pct_2nd, row.pct_3rd, row.pct_4th].map(
              (pct, i) =>
                pct > 0 && (
                  <div
                    key={i}
                    className={`${RANK_COLORS[i]} h-full`}
                    style={{ width: `${pct}%` }}
                    title={`${RANK_LABELS[i]}: ${pct}%`}
                  />
                )
            )}
          </div>
        </div>
      ))}
      <div className="flex items-center gap-4 pt-1 text-xs text-gray-400">
        {RANK_LABELS.map((label, i) => (
          <div key={label} className="flex items-center gap-1.5">
            <span className={`w-2.5 h-2.5 rounded-full ${RANK_COLORS[i]}`} />
            {label}
          </div>
        ))}
      </div>
    </div>
  );
}