import argparse
import json

import requests


def probe_api(url):
    try:
        response = requests.get(
            url,
            headers={"Accept": "application/json"},
            timeout=20,
        )

        print(f"URL: {response.url}")
        print(f"HTTP status: {response.status_code}")
        response.raise_for_status()

        data = response.json()

    except requests.exceptions.RequestException as error:
        print(f"Request failed: {error}")
        return

    except ValueError:
        print("The server responded, but its response was not valid JSON.")
        return

    print(f"JSON structure: {type(data).__name__}")

    if isinstance(data, list):
        print(f"Items returned: {len(data)}")
        example = data[0] if data else None
    else:
        example = data

    if isinstance(example, dict):
        print("Fields:", ", ".join(example.keys()))
        print("\nLinks:")
        print(json.dumps(example.get("_links", {}), indent=2))

    print("\nFirst item, or top-level response:")
    print(json.dumps(example, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect a public API endpoint.")
    parser.add_argument("url", help="The API URL to request")
    args = parser.parse_args()

    probe_api(args.url)