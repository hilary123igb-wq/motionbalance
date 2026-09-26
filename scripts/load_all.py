import collections
import csv
import json
import pathlib
import subprocess
import sys
import duckdb

CATALOG_RESULTS = pathlib.Path("data/tournament_probe_results.csv")
RAW_ROOT = pathlib.Path("data/raw")
DB_PATH = "motionbalance.duckdb"

BP_POSITIONS = {"OG", "OO", "CG", "CO"}
VALID_POINTS = {0, 1, 2, 3}


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


def extract_bp_team_results(team_results):
    """Return the 4 team-result dicts if - and only if - they form a
    complete, valid BP result: exactly 4 teams, each with a distinct BP
    position, and points forming a full 0-3 permutation. Returns None
    (reject the whole debate) otherwise. Never partially accepts a
    non-BP or malformed debate - this is what keeps AFF/NEG and other
    non-BP formats out of the analytics entirely."""
    if len(team_results) != 4:
        return None
    positions, points = [], []
    for tr in team_results:
        if not tr.get("team") or not tr.get("side"):
            return None
        side = tr["side"].upper()
        if side not in BP_POSITIONS:
            return None
        if tr.get("points") is None or tr["points"] not in VALID_POINTS:
            return None
        positions.append(side)
        points.append(tr["points"])
    if set(positions) != BP_POSITIONS:
        return None
    if sorted(points) != [0, 1, 2, 3]:
        return None
    return team_results


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
    team_rows = [(nsid(host, slug, t["id"]), tournament_id, t.get("long_name") or t.get("short_name") or t.get("reference", ""))
                 for t in teams]
    if team_rows:
        con.executemany("INSERT INTO teams VALUES (?, ?, ?)", team_rows)

    speakers = dedupe_by_id(load_json(out_dir / "speakers.json"))
    participant_rows = [(nsid(host, slug, s["id"]), s.get("name", ""), bool(s.get("anonymous", False))) for s in speakers]
    if participant_rows:
        con.executemany("INSERT INTO participants VALUES (?, ?, ?)", participant_rows)

    team_member_rows = [(nsid(host, slug, id_from_url(s["team"])), nsid(host, slug, s["id"])) for s in speakers if s.get("team")]
    if team_member_rows:
        con.executemany("INSERT INTO team_members VALUES (?, ?)", team_member_rows)

    rounds = dedupe_by_id(load_json(out_dir / "rounds.json"))
    round_rows = [(nsid(host, slug, r["id"]), tournament_id, r.get("seq"), r.get("name", ""), r.get("stage", ""), r.get("break_category"))
                  for r in rounds]
    if round_rows:
        con.executemany("INSERT INTO rounds VALUES (?, ?, ?, ?, ?, ?)", round_rows)
    round_id_by_seq = {r["seq"]: nsid(host, slug, r["id"]) for r in rounds}

    motions = dedupe_by_id(load_json(out_dir / "motions.json"))
    motion_rows = [(nsid(host, slug, m["id"]), m.get("text", ""), m.get("reference", ""), m.get("info_slide", "")) for m in motions]
    if motion_rows:
        con.executemany("INSERT INTO motions VALUES (?, ?, ?, ?)", motion_rows)

    debate_rows, debate_team_rows = [], []
    seen_debate_ids = set()
    skipped = collections.Counter()

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
                skipped["no_confirmed_ballot"] += 1
                continue

            if ballot.get("forfeit"):
                skipped["forfeit"] += 1
                continue

            sheets = ballot.get("result", {}).get("sheets", [])
            if not sheets:
                skipped["no_result_sheet"] += 1
                continue

            team_results = extract_bp_team_results(sheets[0].get("teams", []))
            if team_results is None:
                skipped["not_valid_bp_result"] += 1
                continue

            seen_debate_ids.add(debate_id)
            venue_id = nsid(host, slug, id_from_url(pairing["venue"])) if pairing.get("venue") else None
            motion_id = nsid(host, slug, id_from_url(ballot["motion"])) if ballot.get("motion") else None

            debate_rows.append((debate_id, round_id, motion_id, venue_id))

            for tr in team_results:
                debate_team_rows.append((
                    debate_id, nsid(host, slug, id_from_url(tr["team"])), tr["side"].upper(),
                    tr["points"], 4 - tr["points"], tr.get("score"),
                ))

    if debate_rows:
        con.executemany("INSERT INTO debates VALUES (?, ?, ?, ?)", debate_rows)
    if debate_team_rows:
        con.executemany("INSERT INTO debate_teams VALUES (?, ?, ?, ?, ?, ?)", debate_team_rows)

    return len(teams), len(debate_rows), skipped


def main():
    # Build into a throwaway file, not the live database. Only swap it in
    # if the finished build passes validate.py.
    tmp_path = DB_PATH + ".tmp"
    if pathlib.Path(tmp_path).exists():
        pathlib.Path(tmp_path).unlink()

    con = duckdb.connect(tmp_path)
    con.execute(open("sql/schema.sql").read())

    with open(CATALOG_RESULTS, newline="", encoding="utf-8") as f:
        viable = [r for r in csv.DictReader(f) if r["status"] == "viable"]

    loaded, not_yet_fetched, failed = 0, 0, 0
    total_skipped = collections.Counter()

    for row in viable:
        host, slug, name = row["host"], row["slug"], row["tournament"]
        if not (RAW_ROOT / host / slug / "_complete").exists():
            not_yet_fetched += 1
            continue

        con.execute("BEGIN TRANSACTION")
        try:
            n_teams, n_debates, skipped = load_tournament(con, host, slug, name)
            con.execute("COMMIT")
            loaded += 1
            total_skipped.update(skipped)
            skip_note = f" ({sum(skipped.values())} debates excluded: {dict(skipped)})" if skipped else ""
            print(f"loaded {name}: {n_teams} teams, {n_debates} debates{skip_note}")
        except Exception as e:
            con.execute("ROLLBACK")
            failed += 1
            print(f"FAILED to load {name} ({host}/{slug}): {type(e).__name__}: {e}")

    con.close()

    print()
    print(f"tournaments loaded: {loaded}")
    print(f"tournaments not yet fetched: {not_yet_fetched}")
    print(f"tournaments failed to load: {failed}")
    if total_skipped:
        print(f"debates excluded across all tournaments: {dict(total_skipped)}")

    print("\nvalidating build before replacing live database...")
    result = subprocess.run([sys.executable, "scripts/validate.py", "--db", tmp_path])
    if result.returncode != 0:
        print(f"\nVALIDATION FAILED. New build left at {tmp_path} for inspection.")
        print(f"{DB_PATH} was NOT touched - it still holds the last known-good build.")
        sys.exit(1)

    pathlib.Path(tmp_path).replace(DB_PATH)
    print(f"\nvalidation passed - {DB_PATH} updated")


if __name__ == "__main__":
    main()