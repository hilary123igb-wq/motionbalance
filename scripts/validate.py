import argparse
import sys
import duckdb

parser = argparse.ArgumentParser()
parser.add_argument("--db", default="motionbalance.duckdb")
args = parser.parse_args()

con = duckdb.connect(args.db)

checks = {
    "null values in debate_teams": """
        SELECT * FROM debate_teams
        WHERE position IS NULL OR team_points IS NULL OR rank IS NULL
           OR team_id IS NULL OR debate_id IS NULL
    """,
    "bad positions (row-level)": """
        SELECT * FROM debate_teams
        WHERE position IS NULL OR position NOT IN ('OG','OO','CG','CO')
    """,
    "bad points (row-level)": """
        SELECT * FROM debate_teams
        WHERE team_points IS NULL OR team_points NOT IN (0,1,2,3)
    """,
    "bad ranks (row-level)": """
        SELECT * FROM debate_teams
        WHERE rank IS NULL OR rank NOT IN (1,2,3,4)
    """,
    "debates without exactly 4 teams (includes debates with zero rows)": """
        SELECT d.debate_id, COUNT(dt.team_id) AS n_teams
        FROM debates d
        LEFT JOIN debate_teams dt ON d.debate_id = dt.debate_id
        GROUP BY d.debate_id
        HAVING COUNT(dt.team_id) != 4
    """,
    "debate positions aren't exactly {OG,OO,CG,CO}": """
        SELECT debate_id, list_sort(array_agg(position)) AS positions
        FROM debate_teams
        GROUP BY debate_id
        HAVING list_sort(array_agg(position)) != ['CG','CO','OG','OO']
    """,
    "debate points aren't a valid 0-3 permutation": """
        SELECT debate_id, list_sort(array_agg(team_points)) AS points
        FROM debate_teams
        GROUP BY debate_id
        HAVING list_sort(array_agg(team_points)) != [0,1,2,3]
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
if all_passed:
    print("ALL CHECKS PASSED")
    sys.exit(0)
else:
    print("SOME CHECKS FAILED — investigate before trusting the data")
    sys.exit(1)