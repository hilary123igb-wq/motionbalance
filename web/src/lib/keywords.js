// Plain word-frequency counting over real motion text. No classification, no
// external model, no invented categories - this file only counts words that
// are actually present in web/public/data/motions.json.

// Generic English stopwords plus BP debating boilerplate that appears in
// almost every motion ("this house believes/would/supports/regrets/prefers
// that ...") and would otherwise dominate any frequency count without
// telling you anything about what the motions are actually about.
const STOPWORDS = new Set([
  // generic function words
  "a", "an", "the", "this", "that", "these", "those", "of", "in", "on", "at",
  "to", "for", "with", "by", "from", "as", "is", "are", "was", "were", "be",
  "been", "being", "and", "or", "but", "if", "than", "then", "so", "not",
  "no", "it", "its", "their", "they", "them", "his", "her", "he", "she",
  "we", "you", "your", "our", "us", "i", "which", "who", "whom", "whose",
  "what", "when", "where", "why", "how", "all", "any", "each", "more",
  "most", "other", "some", "such", "only", "own", "same", "so", "than",
  "too", "very", "can", "will", "just", "into", "over", "under", "again",
  "further", "once", "here", "there", "both", "few", "against",
  "have", "has", "had", "having", "do", "does", "did", "doing", "up",
  "out", "about", "between", "through", "during", "before", "after",
  "above", "below", "off", "should", "would", "could", "may", "might",
  "must", "shall",
  // BP debating boilerplate, including shorthand abbreviations tournaments
  // commonly use in place of the full "This House believes/would/..."
  // phrasing (thbt = "this house believes that", thw = "this house would").
  "house", "houses", "believes", "believe", "supports", "support",
  "regrets", "regret", "prefers", "prefer", "opposes", "oppose", "opposed",
  "would", "will", "adopt", "adopts", "model", "models", "mandate",
  "mandates", "ban", "bans", "abolish", "abolishes", "introduce",
  "introduces", "rather", "thbt", "thw", "thr", "thp", "tha", "ths", "tho",
  "etc",
]);

function tokenize(text) {
  return (text.toLowerCase().match(/[a-z][a-z'-]*[a-z]|[a-z]/g) || []);
}

/**
 * Count real word frequency across a list of motion objects with a `text`
 * field. Returns the top N words by count, each with the count itself, so
 * the caller can size/rank them without any fabricated weighting.
 */
export function topKeywords(motions, { topN = 24, minLength = 4 } = {}) {
  const counts = new Map();
  for (const m of motions) {
    if (!m.text) continue;
    const seenInMotion = new Set();
    for (const word of tokenize(m.text)) {
      if (word.length < minLength) continue;
      if (STOPWORDS.has(word)) continue;
      // Count each word once per motion, not once per occurrence within a
      // motion - this keeps a single verbose motion from dominating the
      // count the way raw token frequency would.
      seenInMotion.add(word);
    }
    for (const word of seenInMotion) {
      counts.set(word, (counts.get(word) || 0) + 1);
    }
  }

  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, topN)
    .map(([word, count]) => ({ word, count }));
}
