import json
import time
import pathlib
import requests

BASE = "https://wudc2025.calicotab.com/api/v1"
TOURNAMENT_SLUG = "open"
RAW_DIR = pathlib.Path("data/raw") / TOURNAMENT_SLUG
PAIRINGS_DIR = RAW_DIR / "pairings"
RAW_DIR.mkdir(parents=True, exist_ok=True)
PAIRINGS_DIR.mkdir(parents=True, exist_ok=True)

ENDPOINTS = {
    "teams": f"tournaments/{TOURNAMENT_SLUG}/teams",
    "speakers": f"tournaments/{TOURNAMENT_SLUG}/speakers",
    "rounds": f"tournaments/{TOURNAMENT_SLUG}/rounds",
    "motions": f"tournaments/{TOURNAMENT_SLUG}/motions",
}


def fetch_all_pages(path: str) -> list:
    url = f"{BASE}/{path}"
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


def fetch_round_pairings_with_ballots(seq: int) -> list:
    pairings = fetch_all_pages(f"tournaments/{TOURNAMENT_SLUG}/rounds/{seq}/pairings")
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
    n = len(data) if isinstance(data, list) else "n/a"
    print(f"saved {n} records -> {path}")


if __name__ == "__main__":
    for name, path in ENDPOINTS.items():
        try:
            save_raw(RAW_DIR / f"{name}.json", fetch_all_pages(path))
        except requests.exceptions.RequestException as e:
            print(f"FAILED to fetch {name}: {e}")
            continue

rounds = json.loads((RAW_DIR / "rounds.json").read_text())
    for r in rounds:
        seq = r["seq"]
        out_path = PAIRINGS_DIR / f"round_{seq}.json"
        if out_path.exists():
            print(f"round {seq} already fetched, skipping")
            continue
        try:
            enriched = fetch_round_pairings_with_ballots(seq)
            save_raw(out_path, enriched)
        except requests.exceptions.RequestException as e:
            print(f"FAILED to fetch pairings for round {seq}: {e}")
            continue