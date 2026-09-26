import fs from "fs";
import path from "path";
import Link from "next/link";
import { notFound } from "next/navigation";
import { playfair } from "@/lib/fonts";
import Nav from "@/components/Nav";
import SectionLabel from "@/components/SectionLabel";
import StatGrid from "@/components/StatGrid";
import MotionBreakdown from "@/components/MotionBreakdown";

function loadJson(filename) {
  const filePath = path.join(process.cwd(), "public", "data", filename);
  return JSON.parse(fs.readFileSync(filePath, "utf-8"));
}

export function generateStaticParams() {
  const tournaments = loadJson("tournaments.json");
  return tournaments.map((t) => ({ id: encodeURIComponent(t.tournament_id) }));
}

export default async function TournamentDetailPage({ params }) {
  const { id: rawId } = await params;
  const id = decodeURIComponent(rawId);

  const tournaments = loadJson("tournaments.json");
  const allMotions = loadJson("motions.json");
  const t = tournaments.find((tour) => tour.tournament_id === id);

  if (!t) return notFound();

  const motions = allMotions.filter((m) => m.tournament_id === t.tournament_id);

  const stats = [
    { label: "Teams", value: t.teams },
    { label: "Speakers", value: t.speakers },
    { label: "Preliminary rounds", value: t.rounds_prelim },
    { label: "Total rounds (incl. breaks)", value: t.rounds_total },
    { label: "Debates analysed", value: t.debates_loaded },
    { label: "Motions", value: t.motions_total },
  ];

  return (
    <>
      <Nav current="tournaments" />
      <main className="max-w-7xl mx-auto px-6 py-16">
        <Link href="/tournaments" className="text-sm text-gray-400 hover:text-indigo-500">
          ← All tournaments
        </Link>

        <div className="mt-4">
          <SectionLabel>Tournament overview</SectionLabel>
        </div>
        <h1 className={`${playfair.className} text-4xl sm:text-5xl leading-tight mb-8`}>
          {t.name}
        </h1>

        <StatGrid stats={stats} gridClassName="grid-cols-2 sm:grid-cols-3" />

        {motions.length > 0 && <MotionBreakdown motions={motions} />}
      </main>
    </>
  );
}