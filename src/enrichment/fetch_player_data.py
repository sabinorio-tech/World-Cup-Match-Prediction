from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.enrichment.statbunker_client import fetch_statbunker_player_pages
from src.enrichment.transform_player_data import (
    PROFILE_COLUMNS,
    PROCESSED_DIR,
    RAW_DIR,
    STATS_COLUMNS,
    transform_player_data,
)


PLAYER_OUTPUTS = [
    PROCESSED_DIR / "player_profiles.csv",
    PROCESSED_DIR / "player_stats.csv",
]


def _has_cached_raw_data(raw_dir: Path = RAW_DIR) -> bool:
    required_files = [
        "statbunker_player_standings.html",
        "statbunker_fantasy_players.html",
        "statbunker_shots_on_goal.html",
    ]
    return all((raw_dir / filename).exists() for filename in required_files)


def _has_processed_outputs() -> bool:
    return all(path.exists() and path.stat().st_size > 0 for path in PLAYER_OUTPUTS)


def _write_empty_outputs() -> list[Path]:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(columns=PROFILE_COLUMNS).to_csv(PLAYER_OUTPUTS[0], index=False)
    pd.DataFrame(columns=STATS_COLUMNS).to_csv(PLAYER_OUTPUTS[1], index=False)
    return PLAYER_OUTPUTS


def _fallback_player_outputs(reason: Exception) -> None:
    print(f"Warning: player data refresh failed: {reason}")
    if _has_cached_raw_data():
        print("Using cached raw player-data files.")
        try:
            processed_paths = transform_player_data()
            print(f"Processed player-data files saved: {len(processed_paths)}")
            return
        except Exception as exc:
            print(f"Warning: cached player-data transform failed: {exc}")

    if _has_processed_outputs():
        print("Keeping existing processed player-data files.")
        return

    print("No cached player data found; writing empty player-data outputs.")
    processed_paths = _write_empty_outputs()
    print(f"Empty player-data files saved: {len(processed_paths)}")


def run_player_data_pipeline() -> None:
    """Fetch and transform free World Cup player data for dashboard enrichment."""
    print("Fetching free World Cup player data...")
    try:
        raw_paths = fetch_statbunker_player_pages()
        print(f"Raw player-data files saved: {len(raw_paths)}")

        print("Transforming player data...")
        processed_paths = transform_player_data()
        print(f"Processed player-data files saved: {len(processed_paths)}")
    except Exception as exc:
        _fallback_player_outputs(exc)
    print("Player data proof of concept completed.")


if __name__ == "__main__":
    run_player_data_pipeline()
