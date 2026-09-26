"use client";

import { useState } from "react";

export default function MotionSearch({ motions }) {
  const [query, setQuery] = useState("");
  const [expanded, setExpanded] = useState(new Set());

  const q = query.toLowerCase();
  const filtered = motions.filter(
    (m) => m.text.toLowerCase().includes(q) || m.tournament_name.toLowerCase().includes(q)
  );

  function toggle(key) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  return (
    <div>
      <div className="relative mb-8">
        <input
          type="text"
          placeholder="Search motions..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full bg-white border border-gray-200 rounded-full px-5 py-3 text-sm placeholder-gray-400 outline-none focus:ring-2 focus:ring-indigo-200"
        />
        <svg className="absolute right-5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <circle cx="11" cy="11" r="7" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
      </div>

      <p className="text-sm text-gray-400 mb-4">{filtered.length} of {motions.length} motions</p>

      <div className="space-y-4">
        {filtered.map((m) => {
          const key = `${m.motion_id}-${m.round_seq}`;
          const isOpen = expanded.has(key);
          return (
            <div key={key} className="bg-white border border-gray-100 rounded-2xl shadow-sm p-5 hover:border-indigo-200 transition">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-gray-400">
                  {m.tournament_name} · Round {m.round_seq}
                  {m.stage !== "P" ? " · Break round" : ""}
                </span>
                <span className="text-xs text-gray-400 whitespace-nowrap">{m.n_debates} debates</span>
              </div>
              <p className="text-gray-900 font-medium leading-snug mb-2">{m.text}</p>
              {m.info_slide && (
                <button onClick={() => toggle(key)} className="text-xs text-gray-400 hover:text-indigo-500">
                  {isOpen ? "Hide infoslide ↑" : "Show infoslide ↓"}
                </button>
              )}
              {isOpen && m.info_slide && (
                <div className="text-sm text-gray-600 mt-3 bg-gray-50 rounded-xl p-4" dangerouslySetInnerHTML={{ __html: m.info_slide }} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}