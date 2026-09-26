import { colorForTopic } from "@/lib/topicColors";
import TopicEmptyState from "@/components/TopicEmptyState";

// Real word-frequency-adjacent chart, but for actual per-motion topic tags
// rather than words: a plain CSS conic-gradient donut, weighted by debate
// count (not motion count) so a topic used in more debates reads as bigger.
export default function TopicDonut({ topics }) {
  if (!topics || topics.length === 0) return <TopicEmptyState title="Topic distribution" />;

  const total = topics.reduce((sum, t) => sum + t.n_debates, 0);
  const { stops: stopList } = topics.reduce(
    (state, t) => {
      const pct = total > 0 ? (t.n_debates / total) * 100 : 0;
      const start = state.acc;
      const end = start + pct;
      return { acc: end, stops: [...state.stops, `${colorForTopic(t.topic)} ${start.toFixed(2)}% ${end.toFixed(2)}%`] };
    },
    { acc: 0, stops: [] }
  );
  const stops = stopList.join(", ");

  return (
    <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-6">
      <h3 className="text-sm font-semibold text-gray-900 mb-4">Topic distribution</h3>
      <div className="flex items-center gap-8 flex-wrap">
        <div className="relative w-40 h-40 shrink-0">
          <div className="absolute inset-0 rounded-full" style={{ background: `conic-gradient(${stops})` }} />
          <div className="absolute inset-[19%] rounded-full bg-white flex flex-col items-center justify-center">
            <div className="text-lg font-semibold text-gray-900">{total.toLocaleString()}</div>
            <div className="text-[10px] text-gray-400 uppercase tracking-wide">debates</div>
          </div>
        </div>

        <div className="flex-1 min-w-[200px] grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2">
          {topics.map((t) => {
            const pct = total > 0 ? (t.n_debates / total) * 100 : 0;
            return (
              <div key={t.topic} className="flex items-center justify-between gap-2 text-sm">
                <span className="flex items-center gap-2 text-gray-600 truncate">
                  <span className="w-2.5 h-2.5 rounded-sm shrink-0" style={{ backgroundColor: colorForTopic(t.topic) }} />
                  <span className="truncate">{t.topic}</span>
                </span>
                <span className="text-gray-400 whitespace-nowrap">{pct.toFixed(1)}%</span>
              </div>
            );
          })}
        </div>
      </div>
      <p className="text-xs text-gray-400 mt-5">
        Share of debates by topic (each motion tagged once by a local model - see the README for how).
      </p>
    </div>
  );
}
