import duckdb

con = duckdb.connect("motionbalance.duckdb")

print("By position:")
con.sql("SELECT * FROM position_stats ORDER BY position").show()

print("By bench (Government vs Opposition):")
con.sql("SELECT * FROM bench_stats ORDER BY bench").show()

print("By half (Opening vs Closing):")
con.sql("SELECT * FROM half_stats ORDER BY half").show()

gov, opp = con.execute("SELECT avg_points FROM bench_stats ORDER BY bench").fetchall()
opening, closing = con.execute("SELECT avg_points FROM half_stats ORDER BY half").fetchall()

print(f"government_advantage = {gov[0] - opp[0]:.3f}")
print(f"opening_advantage = {opening[0] - closing[0]:.3f}")