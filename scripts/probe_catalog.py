import csv
import time
import pathlib
from urllib.parse import urlparse

import requests

CATALOG_PATH = pathlib.Path("data/tournament_catalog.csv")
RESULTS_PATH = pathlib.Path("data/tournament_probe_results.csv")


def derive_api_url(home_url: str):
    """Guess a Tabbycat tournament's API root from its public home_url.
    Tabbycat's convention: https://{host}/{slug}/... on the public site
    maps to https://{host}/api/v1/tournaments/{slug} on the API. We take
    the first non-empty path segment as the slug."""
    parsed = urlparse(home_url)
    if not parsed.scheme or not parsed.netloc:
        return None
    segments = [s for s in parsed.path.split("/") if s]
    if not segments:
        return None
    slug = segments[0]
    api_url = f"{parsed.scheme}://{parsed.netloc}/api/v1/tournaments/{slug}"
    return api_url, parsed.netloc, slug


def probe_one(name: str, home_url: str):
    derived = derive_api_url(home_url)
    if derived is None:
        return {"tournament": name, "home_url": home_url, "host": "", "slug": "", "status": "unparseable_url", "api_url": ""}

    api_url, host, slug = derived
    try:
        resp = requests.get(api_url, headers={"Accept": "application/json"}, timeout=10)
    except requests.exceptions.RequestException as e:
        return {"tournament": name, "home_url": home_url, "host": host, "slug": slug, "status": f"error:{type(e).__name__}", "api_url": api_url}

    if resp.status_code != 200:
        return {"tournament": name, "home_url": home_url, "host": host, "slug": slug, "status": f"http_{resp.status_code}", "api_url": api_url}

    try:
        data = resp.json()
    except ValueError:
        return {"tournament": name, "home_url": home_url, "host": host, "slug": slug, "status": "not_json", "api_url": api_url}

    if not isinstance(data, dict) or "slug" not in data:
        return {"tournament": name, "home_url": home_url, "host": host, "slug": slug, "status": "unexpected_shape", "api_url": api_url}

    return {"tournament": name, "home_url": home_url, "host": host, "slug": slug, "status": "viable", "api_url": api_url}


def main():
    with open(CATALOG_PATH, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["format"] == "BP"]

    print(f"probing {len(rows)} BP tournaments...")

    fieldnames = ["tournament", "home_url", "host", "slug", "status", "api_url"]
    results = []

    for i, row in enumerate(rows, 1):
        result = probe_one(row["tournament"], row["home_url"])
        results.append(result)
        if i % 50 == 0:
            viable_so_far = sum(1 for r in results if r["status"] == "viable")
            print(f"  {i}/{len(rows)} probed, {viable_so_far} viable so far")
        time.sleep(0.3)

    with open(RESULTS_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    viable = sum(1 for r in results if r["status"] == "viable")
    print()
    print(f"done: {viable} / {len(rows)} tournaments have a live, accessible Tabbycat API")
    print(f"full results written to {RESULTS_PATH}")


if __name__ == "__main__":
    main()