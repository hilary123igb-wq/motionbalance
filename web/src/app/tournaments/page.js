import fs from "fs";
import path from "path";
import { playfair } from "@/lib/fonts";
import Nav from "@/components/Nav";
import SectionLabel from "@/components/SectionLabel";
import TournamentList from "./TournamentList";

function loadJson(filename) {
  const filePath = path.join(process.cwd(), "public", "data", filename);
  return JSON.parse(fs.readFileSync(filePath, "utf-8"));
}

export default function TournamentsPage() {
  const tournaments = loadJson("tournaments.json");

  return (
    <>
      <Nav current="tournaments" />
      <main className="max-w-7xl mx-auto px-6 py-16">
        <SectionLabel>BP Tournaments</SectionLabel>
        <h1 className={`${playfair.className} text-5xl mb-8`}>Tournaments</h1>
        <TournamentList tournaments={tournaments} />
      </main>
    </>
  );
}