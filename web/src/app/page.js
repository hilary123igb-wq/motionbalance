import fs from "fs";
import path from "path";
import { playfair } from "@/lib/fonts";
import Nav from "@/components/Nav";
import SectionLabel from "@/components/SectionLabel";
import StatGrid from "@/components/StatGrid";
import { ButtonPrimary, ButtonSecondary } from "@/components/Button";

function loadJson(filename) {
  const filePath = path.join(process.cwd(), "public", "data", filename);
  return JSON.parse(fs.readFileSync(filePath, "utf-8"));
}

export default function Home() {
  const tournaments = loadJson("tournaments.json");

  const totals = tournaments.reduce(
    (acc, t) => ({
      debates: acc.debates + t.debates_loaded,
      teams: acc.teams + t.teams,
      speakers: acc.speakers + t.speakers,
      motions: acc.motions + t.motions_total,
    }),
    { debates: 0, teams: 0, speakers: 0, motions: 0 }
  );

  const stats = [
    { label: "Tournaments", value: tournaments.length },
    { label: "Debates analysed", value: totals.debates },
    { label: "Teams", value: totals.teams },
    { label: "Motions", value: totals.motions },
  ];

  return (
    <>
      <Nav current="home" />
      <main className="max-w-5xl mx-auto px-6 py-16">
        <SectionLabel>Debate data & analytics</SectionLabel>
        <h1 className={`${playfair.className} text-6xl sm:text-7xl leading-[1.05] mb-6`}>
          <span className="text-gray-900">Motion</span>
          <br />
          <span className="text-indigo-500">Balance</span>
        </h1>
        <p className="text-gray-600 text-lg max-w-lg mb-4">
          Explore debate motions, tournaments and patterns in positional
          strength across British Parliamentary debating.
        </p>
        <p className="text-gray-600 text-lg max-w-lg mb-8">
          The central question:{" "}
          <span className="text-gray-900 font-medium">
            how do average points earned from Opening Government, Opening Opposition, Closing Government and
            Closing Opposition vary between teams with different levels of prior performance?
          </span>
        </p>

        <div className="flex gap-3 mb-10">
          <ButtonPrimary href="/analytics">See the main analysis →</ButtonPrimary>
          <ButtonSecondary href="/motions">Explore motions</ButtonSecondary>
        </div>

        <StatGrid stats={stats} />

        <div className="grid sm:grid-cols-3 gap-4 mt-6">
          <NavCard
            icon={<BookIcon />}
            title="Browse motions"
            description={`Search and filter ${totals.motions} motions from ${tournaments.length} tournaments`}
            href="/motions"
          />
          <NavCard
            icon={<TrophyIcon />}
            title="Tournaments"
            description="Explore tournament data, motions and results"
            href="/tournaments"
          />
          <NavCard
            icon={<ChartIcon />}
            title="Analytics"
            description="How positional outcomes vary with team strength, plus pooled stats and modeling"
            href="/analytics"
          />
        </div>

        <p className="text-xs text-gray-400 mt-12">
          Data sourced from Tabbycat public APIs · {tournaments.length} tournaments
        </p>
      </main>
    </>
  );
}

function NavCard({ icon, title, description, href }) {
  return (
    <a href={href} className="group block bg-white border border-gray-100 rounded-2xl shadow-sm p-5 hover:shadow-md hover:border-indigo-200 transition">
      <div className="flex items-start justify-between mb-4">
        <div className="w-9 h-9 rounded-lg bg-indigo-50 text-indigo-500 flex items-center justify-center">{icon}</div>
        <span className="text-indigo-300 group-hover:text-indigo-500 group-hover:translate-x-0.5 transition transform">→</span>
      </div>
      <div className="font-semibold text-gray-900 mb-1">{title}</div>
      <p className="text-sm text-gray-500">{description}</p>
    </a>
  );
}

function BookIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.25C10.5 5 8 4.5 6 5v13c2 -0.5 4.5 0 6 1.25M12 6.25C13.5 5 16 4.5 18 5v13c-2 -0.5 -4.5 0 -6 1.25M12 6.25v13" />
    </svg>
  );
}
function TrophyIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M8 4h8v4a4 4 0 0 1-8 0V4Z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M8 5H5a3 3 0 0 0 3 4M16 5h3a3 3 0 0 1-3 4M12 12v4m-3 4h6M10 16h4" />
    </svg>
  );
}
function ChartIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 19V5m5 14v-8m5 8V9m5 10V4" />
    </svg>
  );
}