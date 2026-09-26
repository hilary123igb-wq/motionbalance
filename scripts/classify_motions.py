"""Tag every motion with a topic - no LLM, no network, no local server.

Inspired by the classifier architecture in vikwritescode/derivative (a TF-IDF
vectorizer + a scikit-learn classifier, persisted as reusable artifacts), but
adapted to this project's constraint: we don't have a hand-labeled training
set of motions-to-topics, and (like that project's own README says about its
training data) inventing one isn't something to do quietly. So this uses
weak supervision instead of hand-labeled data:

  1. A curated keyword dictionary (TOPIC_KEYWORDS below) gives each motion a
     "seed" topic wherever its text clearly, unambiguously matches one
     topic's keywords. This part is fully transparent and deterministic -
     every seed label is inspectable and explainable by the keywords that
     produced it.
  2. A TF-IDF + logistic regression classifier is then trained ONLY on those
     seed-labeled motions, and used to predict topics for the motions the
     keyword pass couldn't confidently label - the same "self-training"
     pattern classic weak-supervision pipelines use. A motion only gets a
     model-predicted topic if the model's confidence clears
     MIN_MODEL_CONFIDENCE; below that it's left "Unclassified" rather than
     forcing a guess dressed up as a real classification.

Reads web/public/data/motions.json (already-exported, real motion text -
not the local DuckDB), so this step has no dependency on
motionbalance.duckdb and can run anywhere this repo is checked out. Writes:
  - data/motion_topics.csv   (motion_id, topic, source, confidence, classified_at)
  - models/topic_vectorizer.joblib, models/topic_classifier.joblib
    (gitignored - regenerate any time by re-running this script; kept only
    so a topic assignment can be explained/reproduced without redoing the
    keyword pass from scratch)

Safe to re-run: re-derives everything from motions.json + TOPIC_KEYWORDS
each time, so it naturally picks up newly-added motions. Re-run
scripts/export_data.py afterward to publish the results.
"""

import csv
import json
import pathlib
import re
from collections import Counter
from datetime import datetime, timezone

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import joblib

MOTIONS_PATH = pathlib.Path("web/public/data/motions.json")
OUT_PATH = pathlib.Path("data/motion_topics.csv")
MODELS_DIR = pathlib.Path("models")
FIELDNAMES = ["motion_id", "topic", "source", "confidence", "classified_at"]

# Keyword dictionary used only for SEED labeling (step 1). Order matters as a
# tie-break: if a motion matches keywords from more than one topic with an
# equal hit count, the earlier topic in this dict wins. Keywords are matched
# as whole-word/stem prefixes against the lowercased motion text + info
# slide, so "economic" and "economics" both hit "econom".
TOPIC_KEYWORDS = {
    "Economics": [
        "econom", "bank", "tax", "trade", "market", "subsid", "wage", "capitalis",
        "currency", "inflation", "gdp", "corporat", "privatiz", "nationaliz",
        "financ", "monopol", "industry", "stock exchange", "investor", "debt",
        "loan", "austerity", "consumer",
    ],
    "Politics & Governance": [
        "government", "democra", "election", "parliament", "president",
        "voting", " vote ", "policy", "political part", "politician",
        "constitution", "monarch", "legislat", "bureaucra", "lobbying",
        "campaign finance", "referendum", "cabinet", "prime minister",
        "political system",
    ],
    "International Relations": [
        "foreign policy", "treaty", "united nations", "security council",
        "sanction", "invasion", "sovereignty", "diplomat", "alliance",
        "nato", "refugee", "immigra", "asylum", "border ", "international law",
        "geopolit", "superpower", "colonial", "decoloniz", "global south",
        "developing countr", "developing nation", "foreign aid",
    ],
    "Law & Criminal Justice": [
        "crime", "criminal", "prison", "punish", "sentenc", "police",
        " court", "judge", "jury", "legal system", "justice system",
        "death penalty", "prosecut", " trial", "law enforcement",
        "incarcerat",
    ],
    "Education": [
        "school", "student", "universit", "teacher", "curriculum",
        "education", " exam", "tuition", "classroom", "academ", "degree program",
    ],
    "Gender & Feminism": [
        "feminis", "gender", "women", "woman", "lgbt", "transgender", "queer",
        "sexual orientation", "patriarchy", "misogyn", "abortion",
        "reproductive right", "sex work", "non-binary",
    ],
    "Technology & Science": [
        "technolog", "internet", "artificial intelligence", " ai ", "robot",
        "social media", "algorithm", "data privacy", "surveillance",
        "tech compan", "scientist", "space explor", "genetic", "biotech",
        "automation", "cryptocurrency", "software",
    ],
    "Environment": [
        "environment", "climate", "pollution", "carbon", "fossil fuel",
        "renewable", "sustainab", "wildlife", "conservation",
        "deforestation", "emission", "biodiversity",
    ],
    "Health": [
        "health", "medic", "hospital", "doctor", "vaccin", "disease",
        "pandemic", "mental health", "healthcare", "pharmaceutic", "obesity",
        "public health", "therap",
    ],
    "Media & Culture": [
        "media", "journalis", "press freedom", "celebrity", " film", "movie",
        "music industry", " art ", "television", "entertainment industry",
        "pop culture",
        # NOT "narrative" - too generic ("the narrative that...") to be a
        # reliable media/culture signal on its own; it was pulling in
        # unrelated motions when tried during development.
    ],
    "Religion": [
        "religio", "church", "islam", "muslim", "christian", "hindu",
        "jewish", "secular", "atheis", " faith ",
    ],
    "Military & Security": [
        "military", " army", "weapon", "nuclear", "terroris", "defence",
        "defense spending", "intelligence agency", "espionage", "warfare",
        "armed forces",
    ],
    "Social Policy & Welfare": [
        "welfare", "homeless", "housing crisis", "social security",
        "inequality", "minimum wage", "labor right", "labour right",
        "unemployment", "disabilit", "aging population", "poverty",
    ],
}

MIN_MODEL_CONFIDENCE = 0.35
MIN_SEED_EXAMPLES_PER_TOPIC = 8


def load_motions():
    motions = json.loads(MOTIONS_PATH.read_text())
    # motions.json has one row per (motion, round) it appeared in - dedupe to
    # one row per motion_id so we don't classify the same text twice.
    by_id = {}
    for m in motions:
        by_id.setdefault(m["motion_id"], m)
    return list(by_id.values())


def full_text(m):
    return f"{m.get('text', '')} {m.get('info_slide', '') or ''}".lower()


def keyword_seed_topic(text):
    scores = Counter()
    for topic, keywords in TOPIC_KEYWORDS.items():
        for kw in keywords:
            if kw.strip() and kw.lower() in text:
                scores[topic] += 1
    if not scores:
        return None
    ranked = scores.most_common()
    top_topic, top_score = ranked[0]
    # require a clear leader - a flat tie between two topics isn't a
    # confident seed label, leave it for the model (or Unclassified) instead
    if len(ranked) > 1 and ranked[1][1] == top_score:
        return None
    return top_topic


def main():
    if not MOTIONS_PATH.exists():
        raise SystemExit(f"{MOTIONS_PATH} not found - run scripts/export_data.py at least once first.")

    motions = load_motions()
    print(f"{len(motions)} distinct motions loaded from {MOTIONS_PATH}")

    texts = {m["motion_id"]: full_text(m) for m in motions}

    # --- step 1: keyword seed pass ---
    seed_topic = {}
    for motion_id, text in texts.items():
        topic = keyword_seed_topic(text)
        if topic:
            seed_topic[motion_id] = topic

    seed_counts = Counter(seed_topic.values())
    print(f"keyword pass seeded {len(seed_topic)} of {len(motions)} motions:")
    for topic, n in seed_counts.most_common():
        print(f"  {topic}: {n}")

    trainable_topics = {t for t, n in seed_counts.items() if n >= MIN_SEED_EXAMPLES_PER_TOPIC}
    dropped = set(seed_counts) - trainable_topics
    if dropped:
        print(f"  (topics with < {MIN_SEED_EXAMPLES_PER_TOPIC} seed examples, excluded from model training: {sorted(dropped)})")

    train_ids = [mid for mid, t in seed_topic.items() if t in trainable_topics]
    train_texts = [texts[mid] for mid in train_ids]
    train_labels = [seed_topic[mid] for mid in train_ids]

    results = {}
    now = datetime.now(timezone.utc).isoformat()

    for mid, topic in seed_topic.items():
        if topic in trainable_topics:
            results[mid] = {"topic": topic, "source": "keyword", "confidence": 1.0}

    remaining_ids = [mid for mid in texts if mid not in results]

    if len(train_texts) >= 2 * MIN_SEED_EXAMPLES_PER_TOPIC and len(trainable_topics) >= 2:
        print(f"training TF-IDF + logistic regression on {len(train_texts)} seed-labeled motions across {len(trainable_topics)} topics...")
        vectorizer = TfidfVectorizer(max_features=8000, ngram_range=(1, 2), stop_words="english", min_df=2)
        X_train = vectorizer.fit_transform(train_texts)
        clf = LogisticRegression(max_iter=2000, class_weight="balanced")
        clf.fit(X_train, train_labels)

        MODELS_DIR.mkdir(exist_ok=True)
        joblib.dump(vectorizer, MODELS_DIR / "topic_vectorizer.joblib")
        joblib.dump(clf, MODELS_DIR / "topic_classifier.joblib")

        if remaining_ids:
            X_rest = vectorizer.transform([texts[mid] for mid in remaining_ids])
            probs = clf.predict_proba(X_rest)
            classes = clf.classes_
            n_model_labeled = 0
            for mid, prob_row in zip(remaining_ids, probs):
                best_idx = prob_row.argmax()
                confidence = float(prob_row[best_idx])
                if confidence >= MIN_MODEL_CONFIDENCE:
                    results[mid] = {"topic": classes[best_idx], "source": "model", "confidence": round(confidence, 3)}
                    n_model_labeled += 1
            print(f"model labeled {n_model_labeled} additional motions (confidence >= {MIN_MODEL_CONFIDENCE})")
    else:
        print("not enough seed-labeled motions across enough topics to train a model - using keyword labels only")

    n_unclassified = len(motions) - len(results)
    print(f"{n_unclassified} motions remain Unclassified")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for m in motions:
            mid = m["motion_id"]
            r = results.get(mid)
            writer.writerow({
                "motion_id": mid,
                "topic": r["topic"] if r else "",
                "source": r["source"] if r else "",
                "confidence": r["confidence"] if r else "",
                "classified_at": now,
            })

    final_counts = Counter(r["topic"] for r in results.values())
    print(f"\nwrote {OUT_PATH} - {len(results)} of {len(motions)} motions classified across {len(final_counts)} topics:")
    for topic, n in final_counts.most_common():
        print(f"  {topic}: {n}")
    print("\nre-run scripts/export_data.py to publish topic data to the website")


if __name__ == "__main__":
    main()
