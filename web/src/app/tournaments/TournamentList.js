"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

function uniqueSorted(values) {
  return [...new Set(values.filter((v) => v != null && v !== ""))].sort();
}

export default function TournamentList({ tournaments }) {
  const [query, setQuery] = useState("");
  const [year, setYear] = useState("");
  const [region, setRegion] = useState("");
  const [level, setLevel] = useState("");

  const years = useMemo(() => uniqueSorted(tournaments.map((t) => t.year)).reverse(), [tournaments]);
  const regions = useMemo(() => uniqueSorted(tournaments.map((t) => t.region)), [tournaments]);
  const levels = useMemo(() => uniqueSorted(tournaments.map((t) => t.level)), [tournaments]);

  const q = query.toLowerCase();
  const filtered = tournaments
    .filter((t) => t.name.toLowerCase().includes(q))
    .filter((t) => !year || String(t.year) === String(year))
    .filter((t) => !region || t.region === region)
    .filter((t) => !level || t.level === level)
    .sort((a, b) => b.debates_loaded - a.debates_loaded);

  return (
    <div>
      <div className="relative mb-4">
        <input
          type="text"
          placeholder="Search tournaments..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full bg-white border border-gray-200 rounded-full px-5 py-3 text-sm placeholder-gray-400 outline-none focus:ring-2 focus:ring-indigo-200"
        />
        <svg className="absolute right-5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <circle cx="11" cy="11" r="7" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
      </div>

      <div className="flex flex-wrap gap-2 mb-6">
        <FilterSelect label="All years" value={year} onChange={setYear} options={years} />
        <FilterSelect label="All regions" value={region} onChange={setRegion} options={regions} />
        <FilterSelect label="All levels" value={level} onChange={setLevel} options={levels} />
      </div>

      <p className="text-sm text-gray-400 mb-4">{filtered.length} of {tournaments.length} tournaments</p>

      <div className="space-y-3">
        {filtered.map((t) => (
          <Link
            key={t.tournament_id}
            href={`/tournaments/${encodeURIComponent(t.tournament_id)}`}
            className="flex items-center justify-between bg-white border border-gray-100 rounded-2xl shadow-sm p-5 hover:border-indigo-200 hover:shadow-md transition"
          >
            <div>
              <div className="font-medium text-gray-900">{t.name}</div>
              <div className="text-sm text-gray-500 mt-1">
                {[t.country, t.level].filter(Boolean).join(" · ") || "BP"} · {t.teams} teams · {t.debates_loaded} debates
              </div>
            </div>
            <div className="flex items-center gap-3 shrink-0">
              {t.year && <span className="text-sm text-gray-400">{t.year}</span>}
              <span className="text-indigo-300">→</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

function FilterSelect({ label, value, onChange, options }) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)} className="text-sm bg-white border border-gray-200 rounded-full px-4 py-2 text-gray-600 outline-none focus:ring-2 focus:ring-indigo-200">
      <option value="">{label}</option>
      {options.map((o) => (
        <option key={o} value={o}>{o}</option>
      ))}
    </select>
  );
}