import fs from "fs";
import path from "path";
import { playfair } from "@/lib/fonts";
import Nav from "@/components/Nav";
import SectionLabel from "@/components/SectionLabel";
import StatGrid from "@/components/StatGrid";
import { BarChart } from "@/components/Charts";

function loadJson(filename) {
  const filePath = path.join(process.cwd(), "public", "data", filename);
  return JSON.parse(fs.readFileSync(filePath, "utf-8"));
}

function formatTerm(term) {
  if (term === "Intercept") return "Intercept";
  if (term === "prior_rank_centered") return "Prior team rank (centered)";
  if (term === "final_rank_centered") return "Final team rank (centered)";
  const match = term.match(/C\(position, Treatment\(reference='OG'\)\)\[T\.(\w+)\]/);
  if (match) return `${match[1]} vs. OG`;
  return term;
}

function RegressionTable({ model }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs uppercase tracking-wide text-gray-400 border-b border-gray-100">
            <th className="py-2 pr-4">Term</th>
            <th className="py-2 pr-4">Coefficient</th>
            <th className="py-2">p-value</th>
          </tr>
        </thead>
        <tbody>
          {model.coefficients.map((c) => (
            <tr key={c.term} className="border-b border-gray-50 last:border-0">
              <td className="py-2 pr-4 text-gray-700">{formatTerm(c.term)}</td>
              <td className="py-2 pr-4 font-medium text-gray-900">{c.coef}</td>
              <td className={`py-2 ${c.p_value < 0.05 ? "text-indigo-600 font-medium" : "text-gray-400"}`}>
                {c.p_value}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ModelCard({ title, description, model }) {
  return (
    <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-1">{title}</h3>
      <p className="text-sm text-gray-500 mb-4">{description}</p>
      <div className="flex gap-6 text-sm mb-4">
        <div>
          <div className="text-xs text-gray-400 uppercase tracking-wide">R²</div>
          <div className="font-semibold text-gray-900">{model.r_squared}</div>
        </div>
        <div>
          <div className="text-xs text-gray-400 uppercase tracking-wide">Observations</div>
          <div className="font-semibold text-gray-900">{model.n_obs}</div>
        </div>
      </div>
      <details>
        <summary className="text-xs text-indigo-500 cursor-pointer hover:underline mb-2">
          Full coefficient table
        </summary>
        <div className="mt-3">
          <RegressionTable model={model} />
        </div>
      </details>
    </div>
  );
}

export default function AnalyticsPage() {
  const data = loadJson("analytics.json");

  const summaryStats = [
    { label: "Tournaments", value: data.n_tournaments },
    { label: "Debates in model", value: data.n_debates_in_model },
    { label: "Government advantage", value: `${data.government_advantage > 0 ? "+" : ""}${data.government_advantage}` },
    { label: "Opening advantage", value: `${data.opening_advantage > 0 ? "+" : ""}${data.opening_advantage}` },
  ];

  const positionData = data.position_stats.map((p) => ({ label: p.position, value: p.avg_points }));
  const benchData = data.bench_stats.map((b) => ({ label: b.bench, value: b.avg_points }));
  const halfData = data.half_stats.map((h) => ({ label: h.half, value: h.avg_points }));

  return (
    <>
      <Nav current="analytics" />
      <main className="max-w-7xl mx-auto px-6 py-16">
        <SectionLabel>Pooled analysis</SectionLabel>
        <h1 className={`${playfair.className} text-5xl mb-4`}>Analytics</h1>
        <p className="text-gray-500 max-w-2xl mb-8">
          Average points earned by position, bench and half across every tournament with confirmed ballots, plus two regression models estimating position effects while controlling for team strength.
        </p>

        <StatGrid stats={summaryStats} />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
          <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-6">
            <h3 className="text-sm font-semibold text-gray-900 mb-4">By position</h3>
            <BarChart data={positionData} formatValue={(v) => `${v} pts`} />
          </div>
          <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-6">
            <h3 className="text-sm font-semibold text-gray-900 mb-4">By bench</h3>
            <BarChart data={benchData} formatValue={(v) => `${v} pts`} />
          </div>
          <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-6">
            <h3 className="text-sm font-semibold text-gray-900 mb-4">By half</h3>
            <BarChart data={halfData} formatValue={(v) => `${v} pts`} />
          </div>
        </div>

        <div className="mt-12">
          <SectionLabel>Regression models</SectionLabel>
          <h2 className={`${playfair.className} text-3xl mb-6 mt-2`}>
            Does position still matter, controlling for team strength?
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <ModelCard
              title="Leakage-safe model"
              description="Controls for each team's rank going into the round (prior rounds only) — the honest estimate."
              model={data.regression.leakage_safe}
            />
            <ModelCard
              title="Leaky comparison model"
              description="Controls for final tournament rank instead, which uses information not available at debate time — shown for comparison only."
              model={data.regression.leaky_comparison}
            />
          </div>
        </div>
      </main>
    </>
  );
}