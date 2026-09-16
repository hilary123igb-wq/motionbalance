import duckdb

con = duckdb.connect("motionbalance.duckdb")

checks = {
    "bad positions": """
        SELECT * FROM debate_teams
        WHERE position NOT IN ('OG','OO','CG','CO')
    """,
    "bad points": """
        SELECT * FROM debate_teams
        WHERE team_points NOT IN (0,1,2,3)
    """,
    "bad ranks": """
        SELECT * FROM debate_teams
        WHERE rank NOT IN (1,2,3,4)
    """,
    "rank doesn't match points (4 - team_points)": """
        SELECT * FROM debate_teams
        WHERE rank != 4 - team_points
    """,
    "duplicate position in one debate": """
        SELECT debate_id, position, COUNT(*)
        FROM debate_teams
        GROUP BY debate_id, position
        HAVING COUNT(*) > 1
    """,
    "debates without exactly 4 teams": """
        SELECT debate_id, COUNT(*)
        FROM debate_teams
        GROUP BY debate_id
        HAVING COUNT(*) != 4
    """,
    "debate_teams referencing a nonexistent team": """
        SELECT dt.* FROM debate_teams dt
        LEFT JOIN teams t ON dt.team_id = t.team_id
        WHERE t.team_id IS NULL
    """,
    "debates referencing a nonexistent round": """
        SELECT d.* FROM debates d
        LEFT JOIN rounds r ON d.round_id = r.round_id
        WHERE r.round_id IS NULL
    """,
}

all_passed = True
for name, query in checks.items():
    bad_rows = con.execute(query).fetchall()
    if bad_rows:
        all_passed = False
        print(f"FAIL — {name}: {len(bad_rows)} bad rows")
    else:
        print(f"PASS — {name}")

print()
print("ALL CHECKS PASSED" if all_passed else "SOME CHECKS FAILED — investigate before trusting the data")