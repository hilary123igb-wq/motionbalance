import fs from "fs";
import path from "path";
import { playfair } from "@/lib/fonts";
import Nav from "@/components/Nav";
import SectionLabel from "@/components/SectionLabel";
import MotionSearch from "./MotionSearch";

function loadJson(filename) {
  const filePath = path.join(process.cwd(), "public", "data", filename);
  return JSON.parse(fs.readFileSync(filePath, "utf-8"));
}

export default function MotionsPage() {
  const motions = loadJson("motions.json");
  const tournamentCount = new Set(motions.map((m) => m.tournament_id)).size;

  return (
    <>
      <Nav current="motions" />
      <main className="max-w-5xl mx-auto px-6 py-16">
        <SectionLabel>{tournamentCount} tournaments</SectionLabel>
        <h1 className={`${playfair.className} text-5xl mb-2`}>Motions</h1>
        <p className="text-gray-500 mb-8">{motions.length} motions from {tournamentCount} tournaments</p>
        <MotionSearch motions={motions} />
      </main>
    </>
  );
}