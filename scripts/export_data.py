import collections
import csv
import json
import pathlib
from collections import Counter
import duckdb
import pandas as pd
import statsmodels.formula.api as smf

con = duckdb.connect("motionbalance.duckdb")
con.execute(open("sql/analytics.sql").read())
OUT_DIR = pathlib.Path("web/public/data")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def write_json(name, data):
    path = OUT_DIR / f"{name}.json"
    path.write_text(json.dumps(data, indent=2, default=str))
    print(f"wrote {path}")


# --- pull tournament metadata (year, region, level, country) from the catalog ---
catalog = pd.read_csv("data/tournament_catalog.csv")
probe = pd.read_csv("data/tournament_probe_results.csv")
meta = probe.merge(catalog, on="tournament", how="left", suffixes=("", "_catalog"))
meta = meta.drop_duplicates(subset=["host", "slug"])

meta_by_host_slug = {}
for row in meta.itertuples(index=False):
    meta_by_host_slug[(row.host, row.slug)] = {
        "year": None if pd.isna(row.year) else int(row.year),
        "region": None if pd.isna(row.region) else row.region,
        "level": None if pd.isna(row.level) else row.level,
        "country": None if pd.isna(row.country) else row.country,
    }

# --- tournaments.json: one row per tournament, with its own counts + catalog metadata ---
tournaments_df = con.execute("""
    SELECT
        t.tournament_id, t.host, t.slug, t.name, t.short_name, t.source_url,
        (SELECT COUNT(*) FROM teams te WHERE te.tournament_id = t.tournament_id) AS teams,
        (SELECT COUNT(*) FROM team_members tm
            JOIN teams te ON tm.team_id = te.team_id
            WHERE te.tournament_id = t.tournament_id) AS speakers,
        (SELECT COUNT(*) FROM rounds r WHERE r.tournament_id = t.tournament_id) AS rounds_total,
        (SELECT COUNT(*) FROM rounds r WHERE r.tournament_id = t.tournament_id AND r.stage = 'P') AS rounds_prelim,
        (SELECT COUNT(*) FROM debates d
            JOIN rounds r ON d.round_id = r.round_id
            WHERE r.tournament_id = t.tournament_id) AS debates_loaded,
        (SELECT COUNT(DISTINCT m.motion_id) FROM motions m
            JOIN debates d ON d.motion_id = m.motion_id
            JOIN rounds r ON d.round_id = r.round_id
            WHERE r.tournament_id = t.tournament_id) AS motions_total
    FROM tournaments t
    ORDER BY t.name
""").fetchdf()

tournaments = []
for rec in tournaments_df.to_dict(orient="records"):
    extra = meta_by_host_slug.get((rec["host"], rec["slug"]), {})
    tournaments.append({**rec, **extra})
write_json("tournaments", tournaments)

# --- optional: motion topics (data/motion_topics.csv, produced by
# scripts/classify_motions.py against a local Ollama model - see its
# docstring for why this lives in a CSV rather than the database). Treated
# as "not generated yet" rather than an error if it's missing, same as
# strength_bands.json below - the site renders an explicit empty state.
TOPICS_PATH = pathlib.Path("data/motion_topics.csv")
topic_by_motion_id = {}
if TOPICS_PATH.exists():
    with open(TOPICS_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            topic = (row.get("topic") or "").strip()
            if topic:
                topic_by_motion_id[row["motion_id"]] = topic
    print(f"loaded {len(topic_by_motion_id)} motion topics from {TOPICS_PATH}")
else:
    print(f"{TOPICS_PATH} not found - topic exports skipped (run scripts/classify_motions.py to generate it)")

# --- motions.json: every motion used in a debate, with per-motion breakdown stats ---
motions_df = con.execute("""
    SELECT DISTINCT
        m.motion_id, m.text, m.reference, m.info_slide,
        r.seq AS round_seq, r.name AS round_name, r.stage,
        t.tournament_id, t.name AS tournament_name
    FROM motions m
    JOIN debates d ON d.motion_id = m.motion_id
    JOIN rounds r ON d.round_id = r.round_id
    JOIN tournaments t ON r.tournament_id = t.tournament_id
    ORDER BY t.name, r.seq
""").fetchdf()

motion_position = con.execute("""
    SELECT d.motion_id, dt.position, COUNT(*) AS n, ROUND(AVG(dt.team_points), 3) AS avg_points
    FROM debate_teams dt
    JOIN debates d ON dt.debate_id = d.debate_id
    GROUP BY d.motion_id, dt.position
""").fetchdf()

motion_position_rank = con.execute("""
    SELECT d.motion_id, dt.position, dt.rank, COUNT(*) AS n
    FROM debate_teams dt
    JOIN debates d ON dt.debate_id = d.debate_id
    GROUP BY d.motion_id, dt.position, dt.rank
""").fetchdf()

motion_debate_counts = con.execute("""
    SELECT motion_id, COUNT(*) AS n_debates
    FROM debates
    WHERE motion_id IS NOT NULL
    GROUP BY motion_id
""").fetchdf()
debates_by_motion = dict(zip(motion_debate_counts["motion_id"], motion_debate_counts["n_debates"].astype(int)))

position_by_motion = {}
for row in motion_position.itertuples(index=False):
    position_by_motion.setdefault(row.motion_id, {})[row.position] = {
        "position": row.position,
        "avg_points": row.avg_points,
        "n": int(row.n),
    }

rank_by_motion = {}
for row in motion_position_rank.itertuples(index=False):
    rank_by_motion.setdefault(row.motion_id, {}).setdefault(row.position, {})[int(row.rank)] = int(row.n)


def bench_of(pos):
    return "Government" if pos in ("OG", "CG") else "Opposition"


def half_of(pos):
    return "Opening" if pos in ("OG", "OO") else "Closing"


motions = []
for rec in motions_df.to_dict(orient="records"):
    motion_id = rec["motion_id"]
    pos_map = position_by_motion.get(motion_id, {})
    motion_position_stats = [pos_map[p] for p in ["OG", "OO", "CG", "CO"] if p in pos_map]
    n_debates = debates_by_motion.get(motion_id, 0)

    bench_totals, half_totals = {}, {}
    for p in ["OG", "OO", "CG", "CO"]:
        if p not in pos_map:
            continue
        avg = pos_map[p]["avg_points"]
        bench_totals.setdefault(bench_of(p), []).append(avg)
        half_totals.setdefault(half_of(p), []).append(avg)

    motion_bench_stats = [{"bench": b, "avg_points": round(sum(v) / len(v), 3)} for b, v in bench_totals.items()]
    motion_half_stats = [{"half": h, "avg_points": round(sum(v) / len(v), 3)} for h, v in half_totals.items()]

    finish_distribution = []
    pos_ranks = rank_by_motion.get(motion_id, {})
    for p in ["OG", "OO", "CG", "CO"]:
        if p not in pos_map:
            continue
        counts = pos_ranks.get(p, {})
        denom = pos_map[p]["n"] or 1
        finish_distribution.append({
            "position": p,
            "pct_1st": round(100 * counts.get(1, 0) / denom, 1),
            "pct_2nd": round(100 * counts.get(2, 0) / denom, 1),
            "pct_3rd": round(100 * counts.get(3, 0) / denom, 1),
            "pct_4th": round(100 * counts.get(4, 0) / denom, 1),
        })

    if motion_position_stats:
        best = max(motion_position_stats, key=lambda p: p["avg_points"])
        worst = min(motion_position_stats, key=lambda p: p["avg_points"])
        position_spread = round(best["avg_points"] - worst["avg_points"], 3)
    else:
        best = worst = None
        position_spread = None

    motions.append({
        **rec,
        "n_debates": n_debates,
        "position_stats": motion_position_stats,
        "bench_stats": motion_bench_stats,
        "half_stats": motion_half_stats,
        "finish_distribution": finish_distribution,
        "position_spread": position_spread,
        "most_successful_position": best["position"] if best else None,
        "most_successful_avg": best["avg_points"] if best else None,
        "least_successful_position": worst["position"] if worst else None,
        "least_successful_avg": worst["avg_points"] if worst else None,
        "topic": topic_by_motion_id.get(motion_id),
    })

write_json("motions", motions)

# --- analytics.json: pooled stats + regression across every loaded tournament ---
position_stats = con.execute("SELECT * FROM position_stats ORDER BY position").fetchdf()
bench_stats = con.execute("SELECT * FROM bench_stats ORDER BY bench").fetchdf()
half_stats = con.execute("SELECT * FROM half_stats ORDER BY half").fetchdf()

# Look up by label, never by row position after a sort.
bench_avg = dict(zip(bench_stats["bench"], bench_stats["avg_points"]))
half_avg = dict(zip(half_stats["half"], half_stats["avg_points"]))
gov, opp = bench_avg["Government"], bench_avg["Opposition"]
opening, closing = half_avg["Opening"], half_avg["Closing"]

n_tournaments = con.execute("SELECT COUNT(*) FROM tournaments").fetchone()[0]
n_debates_total = con.execute("SELECT COUNT(*) FROM debates").fetchone()[0]

df = con.execute("""
    SELECT debate_id, tournament_id, team_points, position, prior_team_rank, final_rank
    FROM team_strength_with_final_rank
    WHERE prior_team_strength IS NOT NULL
""").df()
df["prior_rank_centered"] = df["prior_team_rank"] - df["prior_team_rank"].mean()
df["final_rank_centered"] = df["final_rank"] - df["final_rank"].mean()

model_a = smf.ols(
    "team_points ~ C(position, Treatment(reference='OG')) + prior_rank_centered", data=df
).fit(cov_type="cluster", cov_kwds={"groups": df["tournament_id"]})
model_b = smf.ols(
    "team_points ~ C(position, Treatment(reference='OG')) + final_rank_centered", data=df
).fit(cov_type="cluster", cov_kwds={"groups": df["tournament_id"]})


def model_to_dict(model):
    return {
        "r_squared": round(model.rsquared, 4),
        "n_obs": int(model.nobs),
        "coefficients": [
            {"term": t, "coef": round(model.params[t], 4), "p_value": round(model.pvalues[t], 4)}
            for t in model.params.index
        ],
    }


write_json("analytics", {
    "n_tournaments": n_tournaments,
    "n_debates_total": int(n_debates_total),
    "n_debates_in_model": int(df["debate_id"].nunique()),
    "n_model_observations": int(model_a.nobs),
    "position_stats": position_stats.to_dict(orient="records"),
    "bench_stats": bench_stats.to_dict(orient="records"),
    "half_stats": half_stats.to_dict(orient="records"),
    "government_advantage": round(gov - opp, 3),
    "opening_advantage": round(opening - closing, 3),
    "regression": {
        "leakage_safe": model_to_dict(model_a),
        "leaky_comparison": model_to_dict(model_b),
    },
})

# --- strength_bands.json: the central analysis for this release - average
# points earned by BP position, split by each team's prior-performance band
# (see sql/analytics.sql:strength_band_stats for the exact window/filter). ---
BAND_ORDER = ["Lower prior performance", "Middle prior performance", "Higher prior performance"]
POSITION_ORDER = ["OG", "OO", "CG", "CO"]

# Name deliberately does NOT match the SQL view "strength_band_stats" -
# DuckDB's Python replacement scan will happily query a same-named Python
# list/DataFrame instead of the real view if the names collide (we hit this
# exact bug earlier in the project with position_stats/bench_stats/half_stats).
strength_band_df = con.execute("""
    SELECT strength_band, position, n, avg_points
    FROM strength_band_stats
    ORDER BY
        CASE strength_band
            WHEN 'Lower prior performance' THEN 1
            WHEN 'Middle prior performance' THEN 2
            ELSE 3
        END,
        position
""").fetchdf()
strength_band_rows = strength_band_df.to_dict(orient="records")

# Coverage: the full dataset vs. the smaller sample this analysis can use.
# A team only qualifies once it has at least two earlier prelim results, so
# early rounds and short tournaments contribute fewer observations here than
# to the headline dataset totals above - report both, never just one.
n_team_obs_total = con.execute("SELECT COUNT(*) FROM prelim_debate_teams").fetchone()[0]
n_team_obs_in_sample = int(strength_band_df["n"].sum()) if not strength_band_df.empty else 0
sample_scope = con.execute("""
    SELECT COUNT(DISTINCT debate_id) AS n_debates, COUNT(DISTINCT tournament_id) AS n_tournaments
    FROM team_strength
    WHERE prior_team_strength IS NOT NULL AND prior_rounds_played >= 2
""").fetchone()


def strength_band_takeaway(rows):
    """Plain-English summary of the largest observed gap in the actual
    exported data. Always derived from `rows`, never hand-written, so the
    text can't drift from what the chart/table show. Returns None if there
    isn't enough data (fewer than 2 positions in every band) to say anything."""
    by_band = {}
    for r in rows:
        by_band.setdefault(r["strength_band"], {})[r["position"]] = r

    widest = None
    for band in BAND_ORDER:
        positions = by_band.get(band, {})
        if len(positions) < 2:
            continue
        best = max(positions.values(), key=lambda r: r["avg_points"])
        worst = min(positions.values(), key=lambda r: r["avg_points"])
        gap = round(best["avg_points"] - worst["avg_points"], 3)
        if widest is None or gap > widest[0]:
            widest = (gap, band, best, worst)

    if widest is None:
        return None
    gap, band, best, worst = widest
    return (
        f"The largest gap observed is within the \"{band}\" group: {best['position']} teams "
        f"averaged {best['avg_points']} points per debate versus {worst['avg_points']} for "
        f"{worst['position']} (n={best['n']} and n={worst['n']} team observations respectively) "
        f"— a difference of {gap} points."
    )


write_json("strength_bands", {
    "definition": {
        "measure": "Average points earned per team observation, by prior-performance strength band and BP position.",
        "prior_strength_definition": "Each team's average points from its own earlier preliminary-round debates only. The strength feature is computed with a window frame ending one row before the current round, so the current and any future round can never leak into it.",
        "min_prior_rounds": 2,
        "bands": [
            {"band": "Lower prior performance", "range": "Below 1.0"},
            {"band": "Middle prior performance", "range": "1.0 to below 2.0"},
            {"band": "Higher prior performance", "range": "2.0 to 3.0"},
        ],
        "band_order": BAND_ORDER,
        "position_order": POSITION_ORDER,
        "reference_line": 1.5,
        "reference_line_label": "Average points across all four teams in a complete BP debate",
    },
    "data": strength_band_rows,
    "takeaway": strength_band_takeaway(strength_band_rows),
    "coverage": {
        "n_tournaments_total": n_tournaments,
        "n_debates_total": int(n_debates_total),
        "n_team_observations_total": int(n_team_obs_total),
        "n_team_observations_in_sample": n_team_obs_in_sample,
        "n_debates_in_sample": int(sample_scope[0]) if sample_scope[0] is not None else 0,
        "n_tournaments_in_sample": int(sample_scope[1]) if sample_scope[1] is not None else 0,
    },
})

# --- topic-derived exports: topics.json, topic_trends.json,
# position_topic_heatmap.json. Only produced once classify_motions.py has
# been run at least once (topic_by_motion_id non-empty).
#
# Computed entirely from the `motions` and `tournaments` lists already built
# above in this same script - no database query needed. Each motion already
# carries its own position_stats (avg_points + n per position) and
# n_debates, so a topic's position averages are a weighted mean of those
# per-motion means (weighted by each motion's n) rather than a fresh
# groupby over raw debate_teams rows. That's mathematically identical to
# grouping the raw rows directly (a weighted mean of group means, weighted
# by group size, equals the mean of the pooled group) and means this whole
# block - and therefore classify_motions.py's output - can be sanity-checked
# without motionbalance.duckdb at all, since motions.json and tournaments.json
# are both committed, unlike the database.
if topic_by_motion_id:
    year_by_tournament_id = {t["tournament_id"]: t.get("year") for t in tournaments}

    topic_motion_counts = Counter()
    topic_debate_counts = Counter()
    topic_year_debate_counts = Counter()
    # position -> topic -> [sum(avg_points * n), sum(n)]
    position_topic_totals = collections.defaultdict(lambda: collections.defaultdict(lambda: [0.0, 0]))

    for m in motions:
        topic = m.get("topic")
        if not topic:
            continue
        motion_id = m["motion_id"]
        n_debates = m.get("n_debates", 0)

        topic_motion_counts[topic] += 1
        topic_debate_counts[topic] += n_debates

        year = year_by_tournament_id.get(m.get("tournament_id"))
        if year is not None:
            topic_year_debate_counts[(year, topic)] += n_debates

        for p in m.get("position_stats", []):
            totals = position_topic_totals[p["position"]][topic]
            totals[0] += p["avg_points"] * p["n"]
            totals[1] += p["n"]

    # topics.json: how many motions/debates fall under each topic
    topic_dist = [
        {"topic": topic, "n_motions": topic_motion_counts[topic], "n_debates": topic_debate_counts[topic]}
        for topic in topic_motion_counts
    ]
    topic_dist.sort(key=lambda r: r["n_debates"], reverse=True)
    write_json("topics", topic_dist)

    # topic_trends.json: topic mix by tournament year
    trend_rows = [
        {"year": year, "topic": topic, "n_debates": n}
        for (year, topic), n in topic_year_debate_counts.items()
    ]
    trend_rows.sort(key=lambda r: (r["year"], r["topic"]))
    write_json("topic_trends", trend_rows)

    # position_topic_heatmap.json: avg points by position, within each topic
    # (motions.json rows are deduplicated per motion_id above the loop that
    # builds `motions`, so each motion's position_stats is counted once here)
    heatmap_rows = []
    for position in ["OG", "OO", "CG", "CO"]:
        for topic, (weighted_sum, n) in position_topic_totals[position].items():
            if n == 0:
                continue
            heatmap_rows.append({
                "topic": topic,
                "position": position,
                "n": n,
                "avg_points": round(weighted_sum / n, 3),
            })
    heatmap_rows.sort(key=lambda r: (r["topic"], r["position"]))
    write_json("position_topic_heatmap", heatmap_rows)

    print(f"exported topic data for {len(topic_by_motion_id)} classified motions across {len(topic_motion_counts)} topics")
else:
    print("skipping topics.json / topic_trends.json / position_topic_heatmap.json (no topic data yet)")

con.close()