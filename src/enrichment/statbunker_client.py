from __future__ import annotations

from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "player_data"
BASE_URL = "https://www.statbunker.com/competitions"
COMPETITION_ID = 790

PAGES = {
    "player_standings": "PlayerStandings",
    "fantasy_players": "FantasyFootballPlayersStats",
    "shots_on_goal": "PlayersShotsOnGoal",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


def build_url(page: str, competition_id: int = COMPETITION_ID) -> str:
    return f"{BASE_URL}/{page}?comp_id={competition_id}"


def fetch_html(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def save_html(html: str, filename: str, output_dir: Path = RAW_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    output_path.write_text(html, encoding="utf-8")
    print(f"Saved: {output_path}")
    return output_path


def fetch_statbunker_player_pages() -> list[Path]:
    saved_paths = []
    for name, page in PAGES.items():
        url = build_url(page)
        print(f"Fetching StatBunker {name}: {url}")
        html = fetch_html(url)
        saved_paths.append(save_html(html, f"statbunker_{name}.html"))
    return saved_paths


if __name__ == "__main__":
    fetch_statbunker_player_pages()
