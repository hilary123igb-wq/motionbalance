// Renders real word-frequency counts (see lib/keywords.js) as a tag cloud.
// Every word here comes from actual motion text - nothing is classified,
// tagged, or grouped into topics. Font size and color weight are purely a
// function of how many distinct motions contain the word.

const WEIGHT_STEPS = [
  { min: 0.85, text: "text-2xl", color: "text-indigo-600", weight: "font-semibold" },
  { min: 0.6, text: "text-xl", color: "text-indigo-500", weight: "font-semibold" },
  { min: 0.4, text: "text-lg", color: "text-rose-400", weight: "font-medium" },
  { min: 0.2, text: "text-base", color: "text-gray-500", weight: "font-medium" },
  { min: 0, text: "text-sm", color: "text-gray-400", weight: "font-normal" },
];

function styleFor(count, max) {
  const ratio = max > 0 ? count / max : 0;
  return WEIGHT_STEPS.find((s) => ratio >= s.min) ?? WEIGHT_STEPS[WEIGHT_STEPS.length - 1];
}

export default function CommonKeywords({ keywords, title = "Common keywords", description }) {
  if (!keywords || keywords.length === 0) return null;
  const max = Math.max(...keywords.map((k) => k.count));

  return (
    <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-6">
      <h3 className="text-sm font-semibold text-gray-900 mb-1">{title}</h3>
      {description && <p className="text-xs text-gray-400 mb-4">{description}</p>}
      <div className={`flex flex-wrap items-baseline gap-x-4 gap-y-2 ${description ? "" : "mt-4"}`}>
        {keywords.map(({ word, count }) => {
          const s = styleFor(count, max);
          return (
            <span
              key={word}
              className={`${s.text} ${s.color} ${s.weight} leading-none`}
              title={`${word}: appears in ${count} motion${count === 1 ? "" : "s"}`}
            >
              {word}
            </span>
          );
        })}
      </div>
      <p className="text-xs text-gray-400 mt-5">
        Word size reflects how many motions contain that word — plain frequency counting over the actual motion
        text, not a topic model.
      </p>
    </div>
  );
}
