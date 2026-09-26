import csv
import json
import time
import pathlib
import requests

CATALOG_RESULTS = pathlib.Path("data/tournament_probe_results.csv")
RAW_ROOT = pathlib.Path("data/raw")
LOG_PATH = pathlib.Path("data/ingestion_log.csv")


def fetch_all_pages(base: str, path: str) -> list:
    url = f"{base}/{path}"
    records = []
    while url:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            records.extend(data)
            url = None
        else:
            records.extend(data.get("results", []))
            url = data.get("next")
        time.sleep(0.2)
    return records


def fetch_round_pairings_with_ballots(base: str, slug: str, seq: int) -> list:
    pairings = fetch_all_pages(base, f"tournaments/{slug}/rounds/{seq}/pairings")
    enriched = []
    for pairing in pairings:
        ballots_url = pairing.get("_links", {}).get("ballots")
        ballots = []
        if ballots_url:
            resp = requests.get(ballots_url, timeout=15)
            if resp.status_code == 200:
                ballots = resp.json()
            time.sleep(0.2)
        enriched.append({"pairing": pairing, "ballots": ballots})
    return enriched


def save_raw(path: pathlib.Path, data):
    path.write_text(json.dumps(data, indent=2))


def fetch_tournament(host: str, slug: str) -> dict:
    """Fetch one tournament end to end. Never raises - a broken tournament
    must never stop a multi-hour batch job."""
    base = f"https://{host}/api/v1"
    out_dir = RAW_ROOT / host / slug
    pairings_dir = out_dir / "pairings"
    complete_marker = out_dir / "_complete"

    if complete_marker.exists():
        return {"host": host, "slug": slug, "status": "already_complete"}

    out_dir.mkdir(parents=True, exist_ok=True)
    pairings_dir.mkdir(parents=True, exist_ok=True)

    try:
        for name in ("teams", "speakers", "rounds", "motions"):
            save_raw(out_dir / f"{name}.json", fetch_all_pages(base, f"tournaments/{slug}/{name}"))

        rounds = json.loads((out_dir / "rounds.json").read_text())
        for r in rounds:
            seq = r["seq"]
            round_path = pairings_dir / f"round_{seq}.json"
            if round_path.exists():
                continue
            save_raw(round_path, fetch_round_pairings_with_ballots(base, slug, seq))

        complete_marker.write_text("ok")
        return {"host": host, "slug": slug, "status": "success", "rounds": len(rounds)}

    except Exception as e:
        return {"host": host, "slug": slug, "status": f"failed: {type(e).__name__}: {e}"}


def main():
    with open(CATALOG_RESULTS, newline="", encoding="utf-8") as f:
        viable = [r for r in csv.DictReader(f) if r["status"] == "viable"]

    print(f"fetching {len(viable)} tournaments...")

    log_exists = LOG_PATH.exists()
    log_file = open(LOG_PATH, "a", newline="", encoding="utf-8")
    log_writer = csv.DictWriter(log_file, fieldnames=["host", "slug", "status", "rounds"])
    if not log_exists:
        log_writer.writeheader()

    for i, row in enumerate(viable, 1):
        result = fetch_tournament(row["host"], row["slug"])
        log_writer.writerow({
            "host": result["host"],
            "slug": result["slug"],
            "status": result["status"],
            "rounds": result.get("rounds", ""),
        })
        log_file.flush()

        if result["status"] != "already_complete":
            print(f"[{i}/{len(viable)}] {row['tournament']}: {result['status']}")

    log_file.close()
    print("done - see data/ingestion_log.csv for full results")


if __name__ == "__main__":
    main()