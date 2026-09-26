"use client";

import {
  Bar,
  BarChart as RechartsBarChart,
  CartesianGrid,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

// Fixed order + fixed colors for the four BP positions. Never cycled, never
// reassigned per-chart - same position always means the same color anywhere
// on the site. Validated as a categorical palette (adjacent-pair colorblind
// safety) against this project's light surface with the dataviz skill's
// validator: worst adjacent CVD deltaE 9.1, worst adjacent normal-vision
// deltaE 22.9 - both clear the target.
const POSITIONS = [
  { key: "OG", color: "#2a78d6" },
  { key: "OO", color: "#eb6834" },
  { key: "CG", color: "#1baf7a" },
  { key: "CO", color: "#eda100" },
];

function buildChartRows(bandOrder, rows) {
  const byBand = {};
  for (const r of rows) {
    (byBand[r.strength_band] ??= {})[r.position] = r;
  }
  return bandOrder.map((band) => {
    const entry = { band };
    for (const { key } of POSITIONS) {
      const cell = byBand[band]?.[key];
      entry[key] = cell ? cell.avg_points : null;
      entry[`${key}_n`] = cell ? cell.n : 0;
    }
    return entry;
  });
}

function StrengthTooltip({ active, payload, label }) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="bg-white border border-gray-100 rounded-xl shadow-md p-3 text-xs min-w-[160px]">
      <div className="text-gray-400 mb-2">{label}</div>
      <div className="space-y-1">
        {payload.map((p) => {
          const n = p.payload[`${p.dataKey}_n`];
          return (
            <div key={p.dataKey} className="flex items-center justify-between gap-4">
              <span className="flex items-center gap-1.5 text-gray-600">
                <span className="w-2 h-2 rounded-sm shrink-0" style={{ backgroundColor: p.color }} />
                {p.dataKey}
              </span>
              <span className="font-medium text-gray-900 whitespace-nowrap">
                {p.value == null ? "no data" : `${p.value} pts (n=${n})`}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function renderLegend() {
  // Deliberately ignores the payload Recharts hands back (it re-sorts
  // alphabetically) and renders straight from POSITIONS instead, so the
  // legend always matches the fixed OG/OO/CG/CO order the bars are drawn in.
  return (
    <div className="flex flex-wrap gap-4 justify-center mt-3">
      {POSITIONS.map((p) => (
        <div key={p.key} className="flex items-center gap-1.5 text-xs text-gray-600">
          <span className="w-2.5 h-2.5 rounded-sm shrink-0" style={{ backgroundColor: p.color }} />
          {p.key}
        </div>
      ))}
    </div>
  );
}

function StrengthTable({ bandOrder, rows, referenceLine }) {
  const byBand = {};
  for (const r of rows) {
    (byBand[r.strength_band] ??= {})[r.position] = r;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs uppercase tracking-wide text-gray-400 border-b border-gray-100">
            <th className="py-2 pr-4">Strength band</th>
            {POSITIONS.map((p) => (
              <th key={p.key} className="py-2 pr-4">{p.key}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {bandOrder.map((band) => (
            <tr key={band} className="border-b border-gray-50 last:border-0">
              <td className="py-2 pr-4 text-gray-700">{band}</td>
              {POSITIONS.map((p) => {
                const cell = byBand[band]?.[p.key];
                return (
                  <td key={p.key} className="py-2 pr-4">
                    {cell ? (
                      <span className="text-gray-900 font-medium">
                        {cell.avg_points} <span className="text-gray-400 font-normal">(n={cell.n})</span>
                      </span>
                    ) : (
                      <span className="text-gray-400">no data</span>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="text-xs text-gray-400 mt-3">
        Reference line: {referenceLine} pts, the average across all four teams in a complete BP debate (0+1+2+3, divided by 4) — not a prediction for any single band.
      </p>
    </div>
  );
}

export default function StrengthBandChart({ strengthBands }) {
  if (!strengthBands || !strengthBands.data || strengthBands.data.length === 0) {
    return (
      <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-8 text-center">
        <p className="text-gray-700 font-medium mb-2">Strength-band analysis not available yet</p>
        <p className="text-sm text-gray-500 max-w-md mx-auto">
          This chart reads <code className="bg-gray-50 px-1.5 py-0.5 rounded text-gray-600">web/public/data/strength_bands.json</code>,
          which is generated from the local DuckDB database. Run{" "}
          <code className="bg-gray-50 px-1.5 py-0.5 rounded text-gray-600">python scripts/export_data.py</code> against a built database
          (see the README) to produce it, then rebuild the site.
        </p>
      </div>
    );
  }

  const { definition, data, coverage, takeaway } = strengthBands;
  const bandOrder = definition.band_order;
  const referenceLine = definition.reference_line;
  const chartRows = buildChartRows(bandOrder, data);

  return (
    <div>
      <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-6">
        <div style={{ width: "100%", height: 360 }}>
          <ResponsiveContainer>
            <RechartsBarChart data={chartRows} margin={{ top: 12, right: 44, left: 4, bottom: 12 }} barCategoryGap="20%" barGap={2}>
              <CartesianGrid vertical={false} stroke="#e1e0d9" />
              <XAxis
                dataKey="band"
                tick={{ fill: "#52514e", fontSize: 12 }}
                tickLine={false}
                axisLine={{ stroke: "#c3c2b7" }}
              />
              <YAxis
                domain={[0, 3]}
                ticks={[0, 1, 2, 3]}
                tick={{ fill: "#898781", fontSize: 12 }}
                tickLine={false}
                axisLine={false}
                label={{ value: "Avg. points", angle: -90, position: "insideLeft", fill: "#898781", fontSize: 12 }}
              />
              <Tooltip content={<StrengthTooltip />} cursor={{ fill: "#f9f9f7" }} />
              <Legend
                content={renderLegend}
                payload={POSITIONS.map((p) => ({ value: p.key, color: p.color, type: "square" }))}
              />
              <ReferenceLine
                y={referenceLine}
                stroke="#c3c2b7"
                strokeDasharray="4 4"
                label={{ value: `${referenceLine}`, position: "right", fill: "#898781", fontSize: 11 }}
              />
              {POSITIONS.map((p) => (
                <Bar key={p.key} dataKey={p.key} fill={p.color} radius={[4, 4, 0, 0]} maxBarSize={22} />
              ))}
            </RechartsBarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="mt-6 bg-white border border-gray-100 rounded-2xl shadow-sm p-6">
        <StrengthTable bandOrder={bandOrder} rows={data} referenceLine={referenceLine} />
      </div>

      {takeaway && (
        <p className="text-sm text-gray-700 bg-indigo-50 border border-indigo-100 rounded-xl p-4 mt-6">
          {takeaway}
        </p>
      )}

      <p className="text-sm text-gray-500 mt-4">
        Teams are grouped using their average points from earlier available rounds. The chart shows their average
        points from each position. Only preliminary-round observations with at least two earlier results are
        included.
      </p>
      <p className="text-sm text-gray-500 mt-2">
        These comparisons describe patterns in the available results; they do not prove that position caused the
        differences.
      </p>

      {coverage && (
        <p className="text-xs text-gray-400 mt-4">
          This analysis uses {coverage.n_team_observations_in_sample.toLocaleString()} team observations across{" "}
          {coverage.n_debates_in_sample.toLocaleString()} debates in {coverage.n_tournaments_in_sample.toLocaleString()}{" "}
          tournaments — the subset where a team already had at least two earlier preliminary results. The full
          dataset covers {coverage.n_team_observations_total.toLocaleString()} team observations across{" "}
          {coverage.n_debates_total.toLocaleString()} debates in {coverage.n_tournaments_total.toLocaleString()}{" "}
          tournaments.
        </p>
      )}
    </div>
  );
}
