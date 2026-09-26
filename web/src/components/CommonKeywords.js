// Renders real word-frequency counts (see lib/keywords.js) as a ranked bar
// list. Every word here comes from actual motion text - nothing is
// classified, tagged, or grouped into topics. Bar length and rank are purely
// a function of how many distinct motions contain the word.

export default function CommonKeywords({ keywords, title = "Common keywords", description }) {
  if (!keywords || keywords.length === 0) return null;
  const max = Math.max(...keywords.map((k) => k.count));

  return (
    <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-6">
      <h3 className="text-sm font-semibold text-gray-900 mb-1">{title}</h3>
      {description && <p className="text-xs text-gray-400 mb-4">{description}</p>}
      <div className={`space-y-2.5 ${description ? "" : "mt-4"}`}>
        {keywords.map(({ word, count }, i) => {
          const pct = max > 0 ? Math.max((count / max) * 100, 4) : 0;
          return (
            <div key={word} className="flex items-center gap-3">
              <span className="text-xs text-gray-300 tabular-nums w-5 text-right shrink-0">{i + 1}</span>
              <span className="text-sm text-gray-700 w-28 sm:w-36 truncate shrink-0">{word}</span>
              <div className="flex-1 h-2 bg-indigo-50 rounded-full overflow-hidden">
                <div className="h-full bg-indigo-400 rounded-full" style={{ width: `${pct}%` }} />
              </div>
              <span className="text-xs text-gray-400 tabular-nums w-10 text-right shrink-0">{count}</span>
            </div>
          );
        })}
      </div>
      <p className="text-xs text-gray-400 mt-5">
        Ranked by how many motions contain each word — plain frequency counting over the actual motion text, not a
        topic model.
      </p>
    </div>
  );
}
