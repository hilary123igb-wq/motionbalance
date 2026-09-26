import csv
import json
import pathlib
import duckdb

CATALOG_RESULTS = pathlib.Path("data/tournament_probe_results.csv")
RAW_ROOT = pathlib.Path("data/raw")
DB_PATH = "motionbalance.duckdb"


def nsid(host: str, slug: str, raw_id) -> str:
    return f"{host}:{slug}:{raw_id}"

def dedupe_by_id(records):
    seen = {}
    for r in records:
        seen.setdefault(r["id"], r)
    return list(seen.values())

def id_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


def load_json(path: pathlib.Path):
    return json.loads(path.read_text())


def load_tournament(con, host: str, slug: str, name: str):
    out_dir = RAW_ROOT / host / slug
    pairings_dir = out_dir / "pairings"

    tournament_id = f"{host}:{slug}"
    source_url = f"https://{host}/api/v1/tournaments/{slug}"

    con.execute(
        "INSERT INTO tournaments VALUES (?, ?, ?, ?, ?, ?)",
        [tournament_id, host, slug, name, name, source_url],
    )

    teams = dedupe_by_id(load_json(out_dir / "teams.json"))
    con.executemany(
        "INSERT INTO teams VALUES (?, ?, ?)",
        [(nsid(host, slug, t["id"]), tournament_id, t.get("long_name") or t.get("short_name") or t.get("reference", ""))
         for t in teams],
    )

    speakers = dedupe_by_id(load_json(out_dir / "speakers.json"))
    con.executemany(
        "INSERT INTO participants VALUES (?, ?, ?)",
        [(nsid(host, slug, s["id"]), s.get("name", ""), bool(s.get("anonymous", False))) for s in speakers],
    )
    con.executemany(
        "INSERT INTO team_members VALUES (?, ?)",
        [(nsid(host, slug, id_from_url(s["team"])), nsid(host, slug, s["id"])) for s in speakers if s.get("team")],
    )

    rounds = dedupe_by_id(load_json(out_dir / "rounds.json"))
    con.executemany(
        "INSERT INTO rounds VALUES (?, ?, ?, ?, ?, ?)",
        [(nsid(host, slug, r["id"]), tournament_id, r.get("seq"), r.get("name", ""), r.get("stage", ""), r.get("break_category"))
         for r in rounds],
    )
    round_id_by_seq = {r["seq"]: nsid(host, slug, r["id"]) for r in rounds}

    motions = dedupe_by_id(load_json(out_dir / "motions.json"))
    con.executemany(
        "INSERT INTO motions VALUES (?, ?, ?, ?)",
        [(nsid(host, slug, m["id"]), m.get("text", ""), m.get("reference", ""), m.get("info_slide", "")) for m in motions],
    )

    debate_rows, debate_team_rows = [], []
    seen_debate_ids = set()

    for round_file in sorted(pairings_dir.glob("round_*.json")):
        seq = int(round_file.stem.split("_")[1])
        round_id = round_id_by_seq.get(seq)
        if round_id is None:
            continue

        for entry in load_json(round_file):
            pairing, ballots = entry["pairing"], entry["ballots"]

            debate_id = nsid(host, slug, pairing["id"])
            if debate_id in seen_debate_ids:
                continue

            ballot = next((b for b in ballots if b.get("confirmed") and not b.get("discarded")), None)
            if ballot is None:
                continue

            sheets = ballot.get("result", {}).get("sheets", [])
            if not sheets:
                continue
            team_results = sheets[0].get("teams", [])

            if ballot.get("forfeit") or any(t.get("points") is None for t in team_results):
                continue

            seen_debate_ids.add(debate_id)
            venue_id = nsid(host, slug, id_from_url(pairing["venue"])) if pairing.get("venue") else None
            motion_id = nsid(host, slug, id_from_url(ballot["motion"])) if ballot.get("motion") else None

            debate_rows.append((debate_id, round_id, motion_id, venue_id))

            for tr in team_results:
                if not tr.get("team") or not tr.get("side"):
                    continue
                debate_team_rows.append((
                    debate_id, nsid(host, slug, id_from_url(tr["team"])), tr["side"].upper(),
                    tr["points"], 4 - tr["points"], tr.get("score"),
                ))

    if debate_rows:
        con.executemany("INSERT INTO debates VALUES (?, ?, ?, ?)", debate_rows)
    if debate_team_rows:
        con.executemany("INSERT INTO debate_teams VALUES (?, ?, ?, ?, ?, ?)", debate_team_rows)

    return len(teams), len(debate_rows)

def main():
    con = duckdb.connect(DB_PATH)
    con.execute(open("sql/schema.sql").read())

    with open(CATALOG_RESULTS, newline="", encoding="utf-8") as f:
        viable = [r for r in csv.DictReader(f) if r["status"] == "viable"]

    loaded, not_yet_fetched, failed = 0, 0, 0

    for row in viable:
        host, slug, name = row["host"], row["slug"], row["tournament"]
        if not (RAW_ROOT / host / slug / "_complete").exists():
            not_yet_fetched += 1
            continue
        try:
            n_teams, n_debates = load_tournament(con, host, slug, name)
            loaded += 1
            print(f"loaded {name}: {n_teams} teams, {n_debates} debates")
        except Exception as e:
            failed += 1
            print(f"FAILED to load {name} ({host}/{slug}): {type(e).__name__}: {e}")

    print()
    print(f"tournaments loaded: {loaded}")
    print(f"tournaments not yet fetched: {not_yet_fetched}")
    print(f"tournaments failed to load: {failed}")
    con.close()


if __name__ == "__main__":
    main()