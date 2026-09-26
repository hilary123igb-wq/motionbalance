"use client";

import { Line, LineChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { colorForTopic } from "@/lib/topicColors";
import TopicEmptyState from "@/components/TopicEmptyState";

const MAX_TOPICS = 6;

function pivot(rows) {
  const totalByTopic = {};
  for (const r of rows) totalByTopic[r.topic] = (totalByTopic[r.topic] || 0) + r.n_debates;
  const topTopics = Object.entries(totalByTopic)
    .sort((a, b) => b[1] - a[1])
    .slice(0, MAX_TOPICS)
    .map(([topic]) => topic);

  const byYear = {};
  for (const r of rows) {
    if (!topTopics.includes(r.topic)) continue;
    (byYear[r.year] ??= { year: r.year })[r.topic] = r.n_debates;
  }
  const chartRows = Object.values(byYear).sort((a, b) => a.year - b.year);
  return { topTopics, chartRows };
}

export default function TopicTrendsChart({ topicTrends }) {
  if (!topicTrends || topicTrends.length === 0) return <TopicEmptyState title="Topic trends" />;

  const { topTopics, chartRows } = pivot(topicTrends);

  return (
    <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-6">
      <h3 className="text-sm font-semibold text-gray-900 mb-1">Topic trends over time</h3>
      <p className="text-xs text-gray-400 mb-4">
        Debates per year for the {topTopics.length} highest-volume topics. Years come from each tournament&rsquo;s
        listed year; tournaments with no known year are excluded here.
      </p>
      <div style={{ width: "100%", height: 320 }}>
        <ResponsiveContainer>
          <LineChart data={chartRows} margin={{ top: 8, right: 24, left: 0, bottom: 8 }}>
            <CartesianGrid vertical={false} stroke="#e1e0d9" />
            <XAxis dataKey="year" tick={{ fill: "#52514e", fontSize: 12 }} tickLine={false} axisLine={{ stroke: "#c3c2b7" }} />
            <YAxis tick={{ fill: "#898781", fontSize: 12 }} tickLine={false} axisLine={false} allowDecimals={false} />
            <Tooltip
              contentStyle={{ borderRadius: 12, border: "1px solid #f0efe9", fontSize: 12 }}
              labelStyle={{ color: "#898781" }}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            {topTopics.map((topic) => (
              <Line
                key={topic}
                type="monotone"
                dataKey={topic}
                stroke={colorForTopic(topic)}
                strokeWidth={2}
                dot={{ r: 2.5 }}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
