import json
import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


BASE_URL = "https://api.football-data.org/v4"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "live"


def get_api_key() -> str | None:
    """Load the football-data.org token from the environment or local .env."""
    load_dotenv()
    return os.getenv("FOOTBALL_DATA_API_KEY")


def fetch_competition_matches(competition_code: str = "WC", season: int = 2026) -> dict[str, Any]:
    api_key = get_api_key()
    if not api_key:
        raise ValueError("Missing FOOTBALL_DATA_API_KEY environment variable.")

    url = f"{BASE_URL}/competitions/{competition_code}/matches"

    response = requests.get(
        url,
        headers={"X-Auth-Token": api_key},
        params={"season": season},
        timeout=30,
    )

    response.raise_for_status()
    return response.json()


def save_json(data: dict[str, Any], filename: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_path = OUTPUT_DIR / filename

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    print(f"Saved: {output_path}")
    return output_path


if __name__ == "__main__":
    matches = fetch_competition_matches("WC", 2026)
    save_json(matches, "football_data_wc_matches.json")
    print(f"Fetched {len(matches.get('matches', []))} matches from football-data.org.")
