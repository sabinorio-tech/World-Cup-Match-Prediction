import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv


BASE_URL = "https://api.football-data.org/v4"
OUTPUT_DIR = Path("data/raw/live")

load_dotenv()

API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")


def fetch_competition_matches(competition_code: str = "WC", season: int = 2026) -> dict:
    if not API_KEY:
        raise ValueError("Missing FOOTBALL_DATA_API_KEY environment variable.")

    url = f"{BASE_URL}/competitions/{competition_code}/matches"

    response = requests.get(
        url,
        headers={"X-Auth-Token": API_KEY},
        params={"season": season},
        timeout=30,
    )

    print(f"Status code: {response.status_code}")
    print(response.text[:500])

    response.raise_for_status()
    return response.json()


def save_json(data: dict, filename: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_path = OUTPUT_DIR / filename

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    print(f"Saved: {output_path}")


if __name__ == "__main__":
    matches = fetch_competition_matches("WC", 2026)

    print(matches.keys())
    print(f"Number of matches: {len(matches.get('matches', []))}")

    if matches.get("matches"):
        print(matches["matches"][0])

    save_json(matches, "football_data_wc_matches.json")