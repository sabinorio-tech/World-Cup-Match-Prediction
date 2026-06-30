from __future__ import annotations

from pathlib import Path

import pandas as pd


EXPECTED_STAGE_COUNTS = {
    "Group Stage": 72,
    "Round of 32": 16,
    "Round of 16": 8,
    "Quarter-final": 4,
    "Semi-final": 2,
    "3rd Place Match": 1,
    "Final": 1,
}

METADATA_COLUMNS = [
    "team1_confederation",
    "team1_fifa_rank",
    "team1_coach",
    "team2_confederation",
    "team2_fifa_rank",
    "team2_coach",
]


def _validate_input_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")


def _validate_output_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Expected output file was not created: {path}")
    if path.stat().st_size == 0:
        raise ValueError(f"Output file is empty: {path}")


def _validate_required_columns(
    frame: pd.DataFrame,
    required_columns: list[str],
    dataset_name: str,
) -> None:
    missing_columns = set(required_columns) - set(frame.columns)
    if missing_columns:
        raise ValueError(
            f"{dataset_name} is missing columns: {sorted(missing_columns)}"
        )


def standardize_teams(
    teams_input_path: str | Path,
    fixtures_input_path: str | Path,
    elo_latest_path: str | Path,
    teams_output_path: str | Path,
    fixtures_output_path: str | Path,
) -> None:
    """Validate and export cleaned World Cup 2026 team and fixture references."""
    teams_input_path = Path(teams_input_path)
    fixtures_input_path = Path(fixtures_input_path)
    elo_latest_path = Path(elo_latest_path)
    teams_output_path = Path(teams_output_path)
    fixtures_output_path = Path(fixtures_output_path)

    for path in [teams_input_path, fixtures_input_path, elo_latest_path]:
        _validate_input_file(path)

    teams = pd.read_csv(teams_input_path)
    fixtures = pd.read_csv(fixtures_input_path)
    elo_latest = pd.read_csv(elo_latest_path)

    _validate_required_columns(
        teams,
        ["team", "group", "confederation", "fifa_rank", "coach"],
        "World Cup teams",
    )
    _validate_required_columns(
        fixtures,
        ["group", "stage", "team1", "team2", "date", *METADATA_COLUMNS],
        "World Cup fixtures",
    )
    _validate_required_columns(elo_latest, ["country"], "latest Elo")

    fixtures["date"] = pd.to_datetime(
        fixtures["date"],
        format="%Y-%m-%d",
        errors="raise",
    )

    qualified_teams = set(teams["team"])
    elo_teams = set(elo_latest["country"])
    fixture_teams = set(fixtures["team1"]) | set(fixtures["team2"])
    old_team_names = {"Turkey", "United States", "Czech Republic"}
    canonical_team_names = {"Türkiye", "USA", "Czechia"}

    fixtures["team1_is_known"] = fixtures["team1"].isin(qualified_teams)
    fixtures["team2_is_known"] = fixtures["team2"].isin(qualified_teams)
    fixtures["is_placeholder_match"] = ~(
        fixtures["team1_is_known"] & fixtures["team2_is_known"]
    )

    known_fixture_teams = (
        set(fixtures.loc[fixtures["team1_is_known"], "team1"])
        | set(fixtures.loc[fixtures["team2_is_known"], "team2"])
    )
    match_pair_key = fixtures.apply(
        lambda row: tuple(sorted([row["team1"], row["team2"]])),
        axis=1,
    )
    placeholder_matches = fixtures["is_placeholder_match"]
    known_matches = ~placeholder_matches

    if len(teams) != 48 or teams["team"].nunique() != 48:
        raise ValueError("Expected 48 unique World Cup 2026 teams")
    if teams.isna().sum().sum() != 0:
        raise ValueError("World Cup teams reference contains missing values")
    if set(teams["team"]) != elo_teams:
        raise ValueError("World Cup teams do not match latest Elo countries")
    if len(fixtures) != 104:
        raise ValueError(f"Expected 104 World Cup fixtures, found {len(fixtures)}")
    if fixtures["stage"].value_counts().to_dict() != EXPECTED_STAGE_COUNTS:
        raise ValueError("Fixture stage counts do not match expected World Cup format")
    if known_fixture_teams != qualified_teams:
        raise ValueError("Known fixture teams do not match qualified teams")
    if old_team_names & (fixture_teams | qualified_teams | elo_teams):
        raise ValueError("Old team names still present after standardization")
    if not canonical_team_names.issubset(fixture_teams):
        raise ValueError("Expected canonical team names are missing from fixtures")
    if int(known_matches.sum()) != 72 or int(placeholder_matches.sum()) != 32:
        raise ValueError("Unexpected known/placeholder fixture counts")
    if fixtures.duplicated().sum() != 0:
        raise ValueError("Duplicate fixture rows found")
    if fixtures.duplicated(["stage", "date", "team1", "team2"]).sum() != 0:
        raise ValueError("Duplicate ordered fixture keys found")
    if (
        fixtures.assign(match_pair_key=match_pair_key)
        .duplicated(["stage", "date", "match_pair_key"])
        .sum()
        != 0
    ):
        raise ValueError("Duplicate unordered fixture pair keys found")
    if not fixtures.loc[known_matches, METADATA_COLUMNS].notna().all().all():
        raise ValueError("Known fixtures have missing team metadata")
    if not fixtures.loc[placeholder_matches, METADATA_COLUMNS].isna().all().all():
        raise ValueError("Placeholder fixtures have unexpected team metadata")

    teams_output_path.parent.mkdir(parents=True, exist_ok=True)
    fixtures_output_path.parent.mkdir(parents=True, exist_ok=True)
    teams.to_csv(teams_output_path, index=False)
    fixtures.to_csv(fixtures_output_path, index=False)

    _validate_output_file(teams_output_path)
    _validate_output_file(fixtures_output_path)
