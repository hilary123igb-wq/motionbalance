"use client";
import { useState } from "react";
import { FinishDistribution } from "@/components/Charts";

function colorFor(label) {
  return ["Government", "Opening", "OG", "OO"].includes(label) ? "text-rose-500" : "text-indigo-500";
}

function StatRow({ label, items, nameKey }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wide text-gray-400 mb-2">{label}</div>
      <div className="flex flex-wrap gap-4">
        {items.map((item) => (
          <div key={item[nameKey]} className="flex items-baseline gap-1.5">
            <span className={`text-sm font-semibold ${colorFor(item[nameKey])}`}>{item[nameKey]}</span>
            <span className="text-sm text-gray-500">{item.avg_points} pts</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function MotionBreakdown({ motions }) {
  const [query, setQuery] = useState("");
  const [openInfoslide, setOpenInfoslide] = useState({});

  const filtered = motions.filter((m) => m.text.toLowerCase().includes(query.toLowerCase()));

  return (
    <div className="mt-16">
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">Motion breakdown</h2>

      <input
        type="text"
        placeholder="Search motions..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="w-full mb-6 px-4 py-3 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200"
      />

      <div className="space-y-4">
        {filtered.map((m) => {
          const key = `${m.motion_id}-${m.round_seq}`;
          const isOpen = !!openInfoslide[key];
          return (
            <div key={key} className="bg-white border border-gray-100 rounded-2xl shadow-sm p-6">
              <div className="flex items-center gap-2 mb-3">
                <span className="inline-flex items-center px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-600 text-xs font-medium">
                  Round {m.round_seq}
                </span>
                <span className="text-xs text-gray-400">
                  {m.n_debates} debate{m.n_debates === 1 ? "" : "s"}
                </span>
              </div>

              <p className="text-gray-900 font-medium leading-snug mb-3">{m.text}</p>

              {m.info_slide && (
                <button
                  onClick={() => setOpenInfoslide((prev) => ({ ...prev, [key]: !prev[key] }))}
                  className="text-xs text-indigo-500 hover:underline mb-4"
                >
                  {isOpen ? "Hide infoslide" : "Show infoslide"}
                </button>
              )}
              {isOpen && m.info_slide && (
                <p className="text-sm text-gray-500 bg-gray-50 rounded-xl p-4 mb-4 whitespace-pre-line">
                  {m.info_slide}
                </p>
              )}

              {m.n_debates === 0 ? (
                <p className="text-sm text-gray-400">No confirmed results available for this motion.</p>
              ) : (
                <div className="space-y-5 mt-4 pt-4 border-t border-gray-100">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <StatRow label="Bench" items={m.bench_stats} nameKey="bench" />
                    <StatRow label="Half" items={m.half_stats} nameKey="half" />
                    <StatRow label="Position" items={m.position_stats} nameKey="position" />
                  </div>

                  {m.finish_distribution?.length > 0 && (
                    <div>
                      <div className="text-xs uppercase tracking-wide text-gray-400 mb-2">Finish distribution</div>
                      <FinishDistribution distribution={m.finish_distribution} />
                    </div>
                  )}

                  {m.most_successful_position && (
                    <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-gray-500 pt-2">
                      <span>
                        Most successful: <strong className="text-gray-700">{m.most_successful_position}</strong> ({m.most_successful_avg} pts)
                      </span>
                      <span>
                        Least successful: <strong className="text-gray-700">{m.least_successful_position}</strong> ({m.least_successful_avg} pts)
                      </span>
                      <span>
                        Spread: <strong className="text-gray-700">{m.position_spread} pts</strong>
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}