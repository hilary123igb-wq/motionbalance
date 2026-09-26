import csv
import json
import time
import pathlib
import requests

CATALOG_RESULTS = pathlib.Path("data/tournament_probe_results.csv")
RAW_ROOT = pathlib.Path("data/raw")
LOG_PATH = pathlib.Path("data/ingestion_log.csv")


def get_with_retry(url: str, max_retries: int = 5, timeout: int = 15) -> requests.Response:
    """GET with retry/backoff on transient errors (429, 5xx). Raises on
    persistent failure or non-transient errors - callers must never treat
    a failed request as 'no data available'."""
    backoff = 1.0
    resp = None
    for attempt in range(max_retries):
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 200:
            return resp
        if resp.status_code == 429 or resp.status_code >= 500:
            retry_after = resp.headers.get("Retry-After")
            wait = float(retry_after) if retry_after else backoff
            print(f"    transient error {resp.status_code} on {url}, retrying in {wait:.1f}s (attempt {attempt + 1}/{max_retries})")
            time.sleep(wait)
            backoff *= 2
            continue
        resp.raise_for_status()
    raise RuntimeError(f"exhausted {max_retries} retries fetching {url} (last status {resp.status_code if resp else 'unknown'})")


def fetch_all_pages(base: str, path: str) -> list:
    url = f"{base}/{path}"
    records = []
    while url:
        resp = get_with_retry(url)
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
            resp = get_with_retry(ballots_url)
            ballots = resp.json()
            time.sleep(0.2)
        enriched.append({"pairing": pairing, "ballots": ballots})
    return enriched


def save_raw(path: pathlib.Path, data):
    """Write atomically - write to a temp file, then rename. A killed or
    crashed process can never leave a truncated/corrupt file that a rerun
    would mistake for a successfully fetched one."""
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(data, indent=2))
    tmp_path.replace(path)


def fetch_tournament(host: str, slug: str) -> dict:
    """Fetch one tournament end to end. Never raises - a broken tournament
    must never stop a multi-hour batch job. Any transient failure that
    survives retries propagates as an exception here, which is caught and
    reported as a real failure rather than silently saved as empty data."""
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
                existing = json.loads(round_path.read_text())
                has_any_ballots = any(entry["ballots"] for entry in existing)
                if has_any_ballots or len(existing) == 0:
                    continue  # already fetched successfully, or genuinely no pairings drawn yet
                # every pairing had empty ballots - under the old code that
                # always meant a silently-swallowed failed request, so
                # treat it as stale and refetch rather than trusting it
                print(f"  round {seq}: existing file has zero ballots across {len(existing)} pairings, re-fetching")

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