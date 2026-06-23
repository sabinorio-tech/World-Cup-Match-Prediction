from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


TEAM_NAME_MAPPING = {
    "Turkey": "Türkiye",
    "United States": "USA",
    "Czech Republic": "Czechia",
}

SCORE_COLUMNS = ["home_score", "away_score"]
VALID_OUTCOMES = {"home_win", "away_win", "draw"}


def load_results(path: str | Path) -> pd.DataFrame:
    """Load raw match results and parse date values."""
    results = pd.read_csv(path)

    results["date"] = pd.to_datetime(
        results["date"],
        format="%Y-%m-%d",
        errors="raise",
    )

    return results


def standardize_team_names(
    results: pd.DataFrame,
    mapping: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Apply canonical team names to home and away team columns."""
    cleaned = results.copy()

    cleaned[["home_team", "away_team"]] = cleaned[["home_team", "away_team"]].replace(
        mapping or TEAM_NAME_MAPPING
    )

    return cleaned


def split_historical_future(
    results: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split completed matches from future fixtures with fully missing scores."""
    complete_scores = results[SCORE_COLUMNS].notna().all(axis=1)
    missing_scores = results[SCORE_COLUMNS].isna().all(axis=1)
    partial_scores = results[SCORE_COLUMNS].isna().any(axis=1) & ~missing_scores

    if partial_scores.any():
        count = int(partial_scores.sum())
        raise ValueError(f"Found {count} rows with exactly one missing score")

    historical_matches = results.loc[complete_scores].copy()
    future_matches = results.loc[missing_scores].copy()

    historical_matches[SCORE_COLUMNS] = historical_matches[SCORE_COLUMNS].astype(
        "int64"
    )

    return historical_matches, future_matches


def add_outcome(historical_matches: pd.DataFrame) -> pd.DataFrame:
    """Add match outcome labels for completed matches."""
    with_outcome = historical_matches.copy()

    with_outcome["outcome"] = np.select(
        [
            with_outcome["home_score"] > with_outcome["away_score"],
            with_outcome["home_score"] < with_outcome["away_score"],
        ],
        ["home_win", "away_win"],
        default="draw",
    )

    return with_outcome


def validate_clean_results(
    results: pd.DataFrame,
    historical_matches: pd.DataFrame,
    future_matches: pd.DataFrame,
    expected_historical_rows: int | None = 49_433,
    expected_future_rows: int | None = 44,
) -> None:
    """Validate cleaned outputs against expected source profile."""
    all_output_teams = (
        set(historical_matches["home_team"])
        | set(historical_matches["away_team"])
        | set(future_matches["home_team"])
        | set(future_matches["away_team"])
    )

    old_names = set(TEAM_NAME_MAPPING)
    canonical_names = set(TEAM_NAME_MAPPING.values())

    if expected_historical_rows is not None:
        assert len(historical_matches) == expected_historical_rows

    if expected_future_rows is not None:
        assert len(future_matches) == expected_future_rows

    assert len(historical_matches) + len(future_matches) == len(results)

    assert historical_matches[SCORE_COLUMNS].notna().all().all()
    assert future_matches[SCORE_COLUMNS].isna().all().all()
    assert historical_matches[SCORE_COLUMNS].dtypes.eq("int64").all()

    assert "outcome" in historical_matches.columns
    assert historical_matches["outcome"].isin(VALID_OUTCOMES).all()

    assert old_names.isdisjoint(
        all_output_teams
    ), f"Old names still present: {old_names & all_output_teams}"

    assert canonical_names.issubset(
        all_output_teams
    ), f"Missing canonical names: {canonical_names - all_output_teams}"


def clean_results(
    path: str | Path,
    expected_historical_rows: int | None = 49_433,
    expected_future_rows: int | None = 44,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load, clean, split, add outcome, and validate results data."""
    results = load_results(path)
    results = standardize_team_names(results)

    historical_matches, future_matches = split_historical_future(results)
    historical_matches = add_outcome(historical_matches)

    validate_clean_results(
        results=results,
        historical_matches=historical_matches,
        future_matches=future_matches,
        expected_historical_rows=expected_historical_rows,
        expected_future_rows=expected_future_rows,
    )

    return historical_matches, future_matches

def save_clean_results(
    historical_matches: pd.DataFrame,
    future_matches: pd.DataFrame,
    output_dir: str | Path,
) -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    historical_matches.to_csv(
        output_dir / "results_historical.csv",
        index=False,
    )

    future_matches.to_csv(
        output_dir / "results_future.csv",
        index=False,
    )

if __name__ == "__main__": 
    historical_matches, future_matches = clean_results(
        "data/raw/IF_1872_2026/results.csv"
    )

    save_clean_results(
        historical_matches,
        future_matches,
        "data/processed"
    )

    print("Cleaned datasets saved.")