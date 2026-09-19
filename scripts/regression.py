import duckdb
import statsmodels.formula.api as smf

con = duckdb.connect("motionbalance.duckdb")

df = con.execute("""
    SELECT team_points, position, prior_team_rank, final_rank
    FROM team_strength_with_final_rank
    WHERE prior_team_strength IS NOT NULL
""").df()

print(f"rows in both models: {len(df)}")
print()

df["prior_rank_centered"] = df["prior_team_rank"] - df["prior_team_rank"].mean()
df["final_rank_centered"] = df["final_rank"] - df["final_rank"].mean()

print("=" * 70)
print("MODEL A — leakage-safe: strength known BEFORE this round only")
print("=" * 70)
model_a = smf.ols(
    "team_points ~ C(position, Treatment(reference='OG')) + prior_rank_centered",
    data=df,
).fit()
print(model_a.summary())

print()
print("=" * 70)
print("MODEL B — illustrative / leaky: strength from the FINAL tournament tab")
print("(uses information from rounds that hadn't happened yet at debate time)")
print("=" * 70)
model_b = smf.ols(
    "team_points ~ C(position, Treatment(reference='OG')) + final_rank_centered",
    data=df,
).fit()
print(model_b.summary())