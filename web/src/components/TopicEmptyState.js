// Shared empty state for every topic-dependent chart, mirroring
// StrengthBandChart's pattern: a missing export is treated as "not
// generated yet" with the exact commands to fix it, never as an error and
// never papered over with fabricated data.
export default function TopicEmptyState({ title }) {
  return (
    <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-8 text-center">
      <p className="text-gray-700 font-medium mb-2">{title} not available yet</p>
      <p className="text-sm text-gray-500 max-w-md mx-auto">
        This needs motions to be topic-tagged first. Run{" "}
        <code className="bg-gray-50 px-1.5 py-0.5 rounded text-gray-600">python scripts/classify_motions.py</code>{" "}
        (requires a local Ollama model - see the README), then{" "}
        <code className="bg-gray-50 px-1.5 py-0.5 rounded text-gray-600">python scripts/export_data.py</code> to
        publish it, and rebuild the site.
      </p>
    </div>
  );
}
