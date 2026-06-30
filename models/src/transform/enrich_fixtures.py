from __future__ import annotations

from pathlib import Path

import pandas as pd


FIXTURE_COLUMNS = [
    "stage",
    "group",
    "team1",
    "team2",
    "venue",
    "city",
    "country",
    "date",
    "kickoff_et",
    "is_placeholder_match",
    "team1_confederation",
    "team1_fifa_rank",
    "team1_coach",
    "team2_confederation",
    "team2_fifa_rank",
    "team2_coach",
]

ELO_COLUMNS = [
    "country",
    "snapshot_date",
    "rank",
    "country_code",
    "rating",
    "is_host",
]

FINAL_COLUMNS = [
    "stage",
    "group",
    "team1",
    "team2",
    "venue",
    "city",
    "country",
    "date",
    "kickoff_et",
    "is_placeholder_match",
    "team1_confederation",
    "team1_fifa_rank",
    "team1_coach",
    "team1_elo_rating",
    "team1_elo_rank",
    "team1_elo_country_code",
    "team1_elo_is_host",
    "team2_confederation",
    "team2_fifa_rank",
    "team2_coach",
    "team2_elo_rating",
    "team2_elo_rank",
    "team2_elo_country_code",
    "team2_elo_is_host",
    "team1_elo_snapshot_date",
    "team2_elo_snapshot_date",
]


def load_inputs(
    fixtures_path: str | Path,
    teams_path: str | Path,
    elo_latest_path: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load validated fixtures, cleaned teams, and latest Elo ratings."""
    fixtures = pd.read_csv(fixtures_path)
    teams = pd.read_csv(teams_path)
    elo_latest = pd.read_csv(elo_latest_path)

    fixtures["date"] = pd.to_datetime(
        fixtures["date"],
        format="%Y-%m-%d",
        errors="raise",
    )
    elo_latest["snapshot_date"] = pd.to_datetime(
        elo_latest["snapshot_date"],
        format="%Y-%m-%d",
        errors="raise",
    )

    return fixtures, teams, elo_latest


def merge_team_elo(fixtures: pd.DataFrame, elo_latest: pd.DataFrame) -> pd.DataFrame:
    """Attach lean latest Elo attributes for team1 and team2."""
    missing_fixture_columns = set(FIXTURE_COLUMNS) - set(fixtures.columns)
    missing_elo_columns = set(ELO_COLUMNS) - set(elo_latest.columns)

    if missing_fixture_columns:
        raise ValueError(f"Missing fixture columns: {sorted(missing_fixture_columns)}")

    if missing_elo_columns:
        raise ValueError(f"Missing Elo columns: {sorted(missing_elo_columns)}")

    enriched = fixtures[FIXTURE_COLUMNS].copy()
    elo_subset = elo_latest[ELO_COLUMNS].copy()

    team1_elo = elo_subset.add_prefix("team1_elo_")
    team2_elo = elo_subset.add_prefix("team2_elo_")

    enriched = enriched.merge(
        team1_elo,
        left_on="team1",
        right_on="team1_elo_country",
        how="left",
    )
    enriched = enriched.merge(
        team2_elo,
        left_on="team2",
        right_on="team2_elo_country",
        how="left",
    )

    return enriched


def select_final_columns(enriched: pd.DataFrame) -> pd.DataFrame:
    """Return the production fixture enrichment schema."""
    missing_columns = set(FINAL_COLUMNS) - set(enriched.columns)

    if missing_columns:
        raise ValueError(f"Missing final columns: {sorted(missing_columns)}")

    return enriched[FINAL_COLUMNS].copy()


def validate_output(
    enriched: pd.DataFrame,
    expected_shape: tuple[int, int] = (104, 26),
) -> None:
    """Validate the lean enriched fixture output."""
    if enriched.shape != expected_shape:
        raise ValueError(
            f"Expected output shape {expected_shape}, found {enriched.shape}"
        )

    duplicate_count = int(enriched.duplicated().sum())
    if duplicate_count:
        raise ValueError(f"Found {duplicate_count} duplicate output rows")

    duplicate_suffix_columns = [
        column for column in enriched.columns if column.endswith(("_x", "_y"))
    ]
    if duplicate_suffix_columns:
        raise ValueError(
            f"Unexpected duplicate merge columns: {duplicate_suffix_columns}"
        )

    if "elo_diff" in enriched.columns:
        raise ValueError("Unexpected engineered column found: elo_diff")

    placeholder_matches = enriched["is_placeholder_match"].astype(bool)
    known_matches = ~placeholder_matches

    if int(known_matches.sum()) != 72:
        raise ValueError(f"Expected 72 known fixtures, found {int(known_matches.sum())}")

    if int(placeholder_matches.sum()) != 32:
        raise ValueError(
            f"Expected 32 placeholder fixtures, found {int(placeholder_matches.sum())}"
        )

    known_missing_ratings = enriched.loc[
        known_matches,
        ["team1_elo_rating", "team2_elo_rating"],
    ].isna()

    if known_missing_ratings.any().any():
        missing_rows = enriched.loc[
            known_matches & known_missing_ratings.any(axis=1),
            ["team1", "team2", "team1_elo_rating", "team2_elo_rating"],
        ]
        raise ValueError(
            "Known group-stage fixtures have missing Elo ratings: "
            f"{missing_rows.to_dict(orient='records')}"
        )


def enrich_fixtures(
    fixtures_path: str | Path,
    teams_path: str | Path,
    elo_latest_path: str | Path,
) -> pd.DataFrame:
    """Load, enrich, select, and validate World Cup 2026 fixtures."""
    fixtures, teams, elo_latest = load_inputs(
        fixtures_path=fixtures_path,
        teams_path=teams_path,
        elo_latest_path=elo_latest_path,
    )

    missing_teams = set(teams["team"]) - set(elo_latest["country"])
    if missing_teams:
        raise ValueError(f"Teams missing from latest Elo data: {sorted(missing_teams)}")

    enriched = merge_team_elo(fixtures=fixtures, elo_latest=elo_latest)
    enriched = select_final_columns(enriched)
    validate_output(enriched)

    return enriched


def save_output(enriched: pd.DataFrame, output_path: str | Path) -> None:
    """Save the enriched fixture output."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    enriched.to_csv(output_path, index=False)


def main() -> None:
    fixtures_path = Path("data/processed/wc_2026_fixtures_validated.csv")
    teams_path = Path("data/processed/wc_2026_teams_cleaned.csv")
    elo_latest_path = Path("data/processed/elo_latest.csv")
    output_path = Path("data/processed/wc_2026_fixtures_enriched.csv")

    enriched = enrich_fixtures(
        fixtures_path=fixtures_path,
        teams_path=teams_path,
        elo_latest_path=elo_latest_path,
    )
    save_output(enriched, output_path)

    print(f"Enriched fixtures saved to {output_path}")


if __name__ == "__main__":
    main()
