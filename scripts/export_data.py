import json
import pathlib
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

con.close()