import json
import pathlib
import duckdb

RAW_DIR = pathlib.Path("data/raw/open")
PAIRINGS_DIR = RAW_DIR / "pairings"
DB_PATH = "motionbalance.duckdb"

TOURNAMENT_ID = 3496
TOURNAMENT_SLUG = "open"
TOURNAMENT_NAME = "Panama World Universities Debating Championships 2025 (Open)"
SOURCE_URL = "https://wudc2025.calicotab.com/api/v1/tournaments/open"


def id_from_url(url: str) -> int:
    return int(url.rstrip("/").split("/")[-1])


def load_json(path: pathlib.Path):
    return json.loads(path.read_text())


def main():
    con = duckdb.connect(DB_PATH)
    con.execute(open("sql/schema.sql").read())

    con.execute(
        "INSERT INTO tournaments VALUES (?, ?, ?, ?, ?)",
        [TOURNAMENT_ID, TOURNAMENT_SLUG, TOURNAMENT_NAME, "WUDC 2025 Open", SOURCE_URL],
    )

    teams = load_json(RAW_DIR / "teams.json")
    con.executemany(
        "INSERT INTO teams VALUES (?, ?, ?)",
        [(t["id"], TOURNAMENT_ID, t["long_name"]) for t in teams],
    )

    speakers = load_json(RAW_DIR / "speakers.json")
    con.executemany(
        "INSERT INTO participants VALUES (?, ?, ?)",
        [(s["id"], s["name"], s["anonymous"]) for s in speakers],
    )
    con.executemany(
        "INSERT INTO team_members VALUES (?, ?)",
        [(id_from_url(s["team"]), s["id"]) for s in speakers if s.get("team")],
    )

    rounds = load_json(RAW_DIR / "rounds.json")
    con.executemany(
        "INSERT INTO rounds VALUES (?, ?, ?, ?, ?, ?)",
        [
            (r["id"], TOURNAMENT_ID, r["seq"], r["name"], r["stage"], r.get("break_category"))
            for r in rounds
        ],
    )
    round_id_by_seq = {r["seq"]: r["id"] for r in rounds}

    motions = load_json(RAW_DIR / "motions.json")
    con.executemany(
        "INSERT INTO motions VALUES (?, ?, ?, ?)",
        [(m["id"], m["text"], m["reference"], m.get("info_slide", "")) for m in motions],
    )

    debate_rows = []
    debate_team_rows = []
    skipped_no_ballot = 0
    skipped_incomplete = 0

    for round_file in sorted(PAIRINGS_DIR.glob("round_*.json")):
        seq = int(round_file.stem.split("_")[1])
        round_id = round_id_by_seq[seq]

        for entry in load_json(round_file):
            pairing = entry["pairing"]
            ballots = entry["ballots"]

            ballot = next(
                (b for b in ballots if b["confirmed"] and not b["discarded"]), None
            )
            if ballot is None:
                skipped_no_ballot += 1
                continue

            sheet = ballot["result"]["sheets"][0]
            team_results = sheet["teams"]

            # A forfeit or a partially-entered ballot can leave a team with
            # no points recorded. We can't compute a fair position effect
            # from an incomplete room, so we skip the whole debate rather
            # than guess a value (e.g. treating it as 0, which would falsely
            # penalise whichever position happens to forfeit more often).
            if ballot.get("forfeit") or any(t.get("points") is None for t in team_results):
                skipped_incomplete += 1
                continue

            debate_id = pairing["id"]
            venue_id = id_from_url(pairing["venue"]) if pairing.get("venue") else None
            motion_id = id_from_url(ballot["motion"]) if ballot.get("motion") else None

            debate_rows.append((debate_id, round_id, motion_id, venue_id))

            for team_result in team_results:
                team_id = id_from_url(team_result["team"])
                position = team_result["side"].upper()
                points = team_result["points"]
                rank = 4 - points
                score = team_result.get("score")
                debate_team_rows.append((debate_id, team_id, position, points, rank, score))

    con.executemany("INSERT INTO debates VALUES (?, ?, ?, ?)", debate_rows)
    con.executemany("INSERT INTO debate_teams VALUES (?, ?, ?, ?, ?, ?)", debate_team_rows)

    print(f"loaded {len(debate_rows)} debates")
    print(f"skipped {skipped_no_ballot} debates with no confirmed ballot")
    print(f"skipped {skipped_incomplete} debates with a forfeit or incomplete points")

    con.close()


if __name__ == "__main__":
    main()