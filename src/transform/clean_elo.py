from __future__ import annotations

from pathlib import Path

import pandas as pd


TEAM_NAME_MAPPING = {
    "Turkey": "Türkiye",
    "United States": "USA",
}

EXPECTED_COLUMNS = [
    "year",
    "snapshot_date",
    "country",
    "rank",
    "country_code",
    "rating",
    "rank_max",
    "rating_max",
    "rank_avg",
    "rating_avg",
    "rank_min",
    "rating_min",
    "matches_total",
    "matches_home",
    "matches_away",
    "matches_neutral",
    "wins",
    "losses",
    "draws",
    "goals_for",
    "goals_against",
    "confederation",
    "is_host",
]

NUMERIC_COLUMNS = [
    "year",
    "rank",
    "rating",
    "rank_max",
    "rating_max",
    "rank_avg",
    "rating_avg",
    "rank_min",
    "rating_min",
    "matches_total",
    "matches_home",
    "matches_away",
    "matches_neutral",
    "wins",
    "losses",
    "draws",
    "goals_for",
    "goals_against",
]

VALID_CONFEDERATIONS = {"AFC", "CAF", "CONCACAF", "CONMEBOL", "OFC", "UEFA"}
DEFAULT_AS_OF_DATE = "2026-06-10"


def load_elo(path: str | Path) -> pd.DataFrame:
    """Load raw Elo ratings and apply stable datatypes."""
    elo = pd.read_csv(path)

    if list(elo.columns) != EXPECTED_COLUMNS:
        raise ValueError("Unexpected Elo columns or column order")

    elo["snapshot_date"] = pd.to_datetime(
        elo["snapshot_date"],
        format="%Y-%m-%d",
        errors="raise",
    )
    elo["is_host"] = elo["is_host"].astype(bool)

    return elo


def standardize_country_names(
    elo: pd.DataFrame,
    mapping: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Apply canonical project country names."""
    cleaned = elo.copy()
    cleaned["country"] = cleaned["country"].replace(mapping or TEAM_NAME_MAPPING)
    return cleaned


def create_latest_elo_snapshot(
    elo: pd.DataFrame,
    as_of_date: str | pd.Timestamp = DEFAULT_AS_OF_DATE,
) -> pd.DataFrame:
    """Create one latest available Elo row per country at or before a cutoff date."""
    cutoff = pd.to_datetime(as_of_date, format="%Y-%m-%d", errors="raise")
    eligible = elo.loc[elo["snapshot_date"] <= cutoff].copy()

    missing_countries = set(elo["country"]) - set(eligible["country"])
    if missing_countries:
        raise ValueError(f"No Elo snapshot available before cutoff for: {missing_countries}")

    latest_index = eligible.groupby("country")["snapshot_date"].idxmax()
    latest_elo = eligible.loc[latest_index].sort_values("country").reset_index(drop=True)

    return latest_elo


def validate_clean_elo(
    elo_history: pd.DataFrame,
    latest_elo: pd.DataFrame,
    reference_teams: pd.Series | None = None,
    expected_history_rows: int | None = 4_683,
    expected_country_count: int | None = 48,
) -> None:
    """Validate cleaned Elo history and latest snapshot outputs."""
    old_names = set(TEAM_NAME_MAPPING)
    canonical_names = set(TEAM_NAME_MAPPING.values())

    if expected_history_rows is not None:
        assert len(elo_history) == expected_history_rows

    if expected_country_count is not None:
        assert elo_history["country"].nunique() == expected_country_count
        assert len(latest_elo) == expected_country_count
        assert latest_elo["country"].nunique() == expected_country_count

    assert list(elo_history.columns) == EXPECTED_COLUMNS
    assert elo_history.isna().sum().sum() == 0
    assert elo_history.duplicated().sum() == 0
    assert elo_history.duplicated(subset=["country", "year", "snapshot_date"]).sum() == 0
    assert latest_elo.duplicated(subset=["country"]).sum() == 0

    assert (elo_history["year"] == elo_history["snapshot_date"].dt.year).all()
    assert set(elo_history["is_host"].unique()).issubset({False, True})
    assert set(elo_history["confederation"]).issubset(VALID_CONFEDERATIONS)
    assert (elo_history[NUMERIC_COLUMNS] >= 0).all().all()

    assert old_names.isdisjoint(
        set(elo_history["country"])
    ), f"Old country names still present: {old_names & set(elo_history['country'])}"
    assert canonical_names.issubset(
        set(elo_history["country"])
    ), f"Missing canonical country names: {canonical_names - set(elo_history['country'])}"

    if reference_teams is not None:
        assert set(elo_history["country"]) == set(reference_teams)


def clean_elo(
    path: str | Path,
    as_of_date: str | pd.Timestamp = DEFAULT_AS_OF_DATE,
    reference_teams_path: str | Path | None = None,
    expected_history_rows: int | None = 4_683,
    expected_country_count: int | None = 48,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load, clean, validate, and create latest Elo snapshot data."""
    elo_history = load_elo(path)
    elo_history = standardize_country_names(elo_history)
    latest_elo = create_latest_elo_snapshot(elo_history, as_of_date=as_of_date)

    reference_teams = None
    if reference_teams_path is not None:
        reference_teams = pd.read_csv(reference_teams_path)["team"]

    validate_clean_elo(
        elo_history=elo_history,
        latest_elo=latest_elo,
        reference_teams=reference_teams,
        expected_history_rows=expected_history_rows,
        expected_country_count=expected_country_count,
    )

    return elo_history, latest_elo


def save_clean_elo(
    elo_history: pd.DataFrame,
    latest_elo: pd.DataFrame,
    output_dir: str | Path,
) -> None:
    """Save cleaned Elo history and latest snapshot outputs."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    elo_history.to_csv(output_dir / "elo_history.csv", index=False)
    latest_elo.to_csv(output_dir / "elo_latest.csv", index=False)


if __name__ == "__main__":
    elo_history, latest_elo = clean_elo(
        "data/raw/FIFA_WK_Elo_Ratings/elo_ratings_wc2026.csv",
        as_of_date=DEFAULT_AS_OF_DATE,
        reference_teams_path="data/raw/FIFA_WC_1930_2026/wc_2026_teams.csv",
    )

    save_clean_elo(
        elo_history,
        latest_elo,
        "data/processed",
    )

    print("Cleaned Elo datasets saved.")
