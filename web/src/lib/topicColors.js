// Topics are open-ended (discovered from the actual motion corpus by
// scripts/classify_motions.py, not a fixed enum), so colors are assigned by
// hashing the topic name into a fixed palette rather than by list position.
// That keeps a given topic's color stable across components even though
// each component may only see a subset or a differently-sorted list of
// topics.
const PALETTE = [
  "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#8b5cf6", "#e0507a",
  "#0ea5b7", "#65a30d", "#c026d3", "#f59e0b", "#475569", "#0891b2",
];

function hashString(str) {
  let h = 0;
  for (let i = 0; i < str.length; i++) {
    h = (h * 31 + str.charCodeAt(i)) | 0;
  }
  return Math.abs(h);
}

export function colorForTopic(topic) {
  if (!topic) return "#c3c2b7"; // neutral gray for "Unclassified" / missing
  return PALETTE[hashString(topic) % PALETTE.length];
}
