# Processed Data Report

## Overview

This report summarizes every CSV currently available in `data/processed`.

Reviewed files:

- `elo_history.csv`
- `elo_latest.csv`
- `model_training_base.csv`
- `results_future.csv`
- `results_historical.csv`
- `wc_2026_fixtures_enriched.csv`
- `wc_2026_fixtures_validated.csv`
- `wc_2026_teams_cleaned.csv`

## Report Metadata

Generated date:

- `2026-06-23`

Last reviewed date:

- `2026-06-23`

Transform scripts:

- `src/transform/clean_results.py`
- `src/transform/clean_elo.py`
- `src/transform/enrich_fixtures.py`
- `src/export/build_model_dataset.py`

Modeling handoff:

- Initial target variable: `outcome`
- Training dataset: `model_training_base.csv`
- Inference dataset: `wc_2026_fixtures_enriched.csv`

## Join Keys

Important project joins:

- `wc_2026_fixtures_validated.team1` / `team2` -> `wc_2026_teams_cleaned.team`
- `wc_2026_fixtures_validated.team1` / `team2` -> `elo_latest.country`
- `results_historical.home_team` / `away_team` -> canonical standardized team names
- `elo_history.country` -> canonical standardized team names

Join caveats:

- Knockout-stage placeholders should not be joined to team or Elo metadata until the placeholder teams are resolved.
- Historical Elo joins must be time-aware and use only snapshots available before the match date.

## Summary Table

| Dataset | Rows | Columns | Duplicate rows | Missing values |
| --- | ---: | ---: | ---: | --- |
| `elo_history.csv` | 4,683 | 23 | 0 | None |
| `elo_latest.csv` | 48 | 23 | 0 | None |
| `model_training_base.csv` | 49,433 | 10 | 0 | None |
| `results_future.csv` | 44 | 9 | 0 | Expected missing scores |
| `results_historical.csv` | 49,433 | 10 | 0 | None |
| `wc_2026_fixtures_enriched.csv` | 104 | 26 | 0 | Expected placeholder metadata/Elo nulls |
| `wc_2026_fixtures_validated.csv` | 104 | 18 | 0 | Expected knockout placeholder metadata nulls |
| `wc_2026_teams_cleaned.csv` | 48 | 7 | 0 | None |

## `elo_history.csv`

Purpose:

- Historical Elo rating table for all 48 FIFA World Cup 2026 teams.
- Useful for time-aware feature engineering and historical model training.

Shape:

- Rows: 4,683
- Columns: 23

Columns:

```text
year, snapshot_date, country, rank, country_code, rating, rank_max,
rating_max, rank_avg, rating_avg, rank_min, rating_min, matches_total,
matches_home, matches_away, matches_neutral, wins, losses, draws,
goals_for, goals_against, confederation, is_host
```

Validation notes:

- Duplicate rows: 0
- Missing values: none
- Countries: 48
- `snapshot_date` parses successfully.
- Date range: `1901-12-31` to `2026-12-31`

Readiness:

- Ready for use.
- Important caveat: use time-aware joins only. The table contains future snapshots, so downstream feature engineering must enforce an as-of-date cutoff.

## `elo_latest.csv`

Purpose:

- Latest Elo snapshot for the 48 qualified teams.
- Used for fixture enrichment.

Shape:

- Rows: 48
- Columns: 23

Columns:

```text
year, snapshot_date, country, rank, country_code, rating, rank_max,
rating_max, rank_avg, rating_avg, rank_min, rating_min, matches_total,
matches_home, matches_away, matches_neutral, wins, losses, draws,
goals_for, goals_against, confederation, is_host
```

Validation notes:

- Duplicate rows: 0
- Missing values: none
- Countries: 48
- One row per country.
- `snapshot_date` parses successfully.
- Snapshot date: `2026-05-27`

Readiness:

- Ready for fixture enrichment.
- Full coverage for `wc_2026_teams_cleaned.csv`.

## `results_future.csv`

Purpose:

- Future result-style fixtures separated from the raw historical results source.
- These rows are not completed matches and should not be used as historical training results.

Shape:

- Rows: 44
- Columns: 9

Columns:

```text
date, home_team, away_team, home_score, away_score, tournament,
city, country, neutral
```

Validation notes:

- Duplicate rows: 0
- Missing values:
  - `home_score`: 44
  - `away_score`: 44
- Missing scores are expected because these are future matches.
- `date` parses successfully.
- Date range: `2026-06-19` to `2026-06-27`
- Host countries represented: United States, Canada, Mexico

Readiness:

- Ready as a separated future-results dataset.
- Not suitable for model training labels because scores are intentionally missing.

## `results_historical.csv`

Purpose:

- Cleaned historical international football match results.
- Main completed-match dataset for training and historical analysis.

Shape:

- Rows: 49,433
- Columns: 10

Columns:

```text
date, home_team, away_team, home_score, away_score, tournament,
city, country, neutral, outcome
```

Validation notes:

- Duplicate rows: 0
- Missing values: none
- `date` parses successfully.
- Date range: `1872-11-30` to `2026-06-18`
- Home teams: 327 unique values
- Away teams: 321 unique values
- Countries: 269 unique values
- Outcomes:
  - `home_win`: 24,227
  - `away_win`: 13,963
  - `draw`: 11,243

Readiness:

- Ready for historical analysis and model training.
- Recommended future step: decide whether very old matches should be filtered or downweighted during feature engineering/modeling.

## `model_training_base.csv`

Purpose:

- Lightweight base modeling export created from completed historical matches.
- Provides a clean training handoff with the initial target variable.
- This is not a feature-engineered dataset yet.

Shape:

- Rows: 49,433
- Columns: 10

Columns:

```text
date, home_team, away_team, home_score, away_score, tournament,
city, country, neutral, outcome
```

Validation notes:

- Duplicate rows: 0
- Missing values: none
- `date` parses successfully.
- Initial target variable: `outcome`
- Target values are non-null.

Readiness:

- Ready as the base training export for Feature Engineering.
- Feature Engineering should add model features in a separate dataset rather than modifying this base export directly.

## `wc_2026_fixtures_validated.csv`

Purpose:

- Validated FIFA World Cup 2026 fixture table.
- Preserves original fixture information plus validation helper columns.

Shape:

- Rows: 104
- Columns: 18

Columns:

```text
group, stage, team1, team2, venue, city, country, date, kickoff_et,
team1_confederation, team1_fifa_rank, team1_coach,
team2_confederation, team2_fifa_rank, team2_coach,
team1_is_known, team2_is_known, is_placeholder_match
```

Validation notes:

- Duplicate rows: 0
- `date` parses successfully.
- Date range: `2026-06-11` to `2026-07-19`
- Stage counts:
  - Group Stage: 72
  - Round of 32: 16
  - Round of 16: 8
  - Quarter-final: 4
  - Semi-final: 2
  - 3rd Place Match: 1
  - Final: 1
- Placeholder rows:
  - Known fixtures: 72
  - Placeholder fixtures: 32
- Missing values are expected for knockout placeholder rows:
  - `group`: 32
  - team metadata columns: 32 each

Readiness:

- Ready as the validated fixture source.
- Use `is_placeholder_match` to prevent invalid joins on knockout placeholder labels.

## `wc_2026_teams_cleaned.csv`

Purpose:

- Cleaned reference table for the 48 FIFA World Cup 2026 teams.
- Used as the authoritative tournament team metadata source.

Shape:

- Rows: 48
- Columns: 7

Columns:

```text
team, group, confederation, fifa_rank, coach, best_wc_result, debut_2026
```

Validation notes:

- Duplicate rows: 0
- Missing values: none
- Teams: 48 unique values
- Groups: 12 unique values
- Each group contains 4 teams.

Readiness:

- Ready for joins and enrichment.
- Full team coverage aligns with `elo_latest.csv`.

## `wc_2026_fixtures_enriched.csv`

Purpose:

- Lean production-ready fixture enrichment output.
- Contains all 104 fixtures.
- Known group-stage fixtures include team metadata and selected Elo fields.
- Placeholder knockout fixtures remain present with null team/Elo metadata.

Shape:

- Rows: 104
- Columns: 26

Columns:

```text
stage, group, team1, team2, venue, city, country, date, kickoff_et,
is_placeholder_match,
team1_confederation, team1_fifa_rank, team1_coach,
team1_elo_rating, team1_elo_rank, team1_elo_country_code, team1_elo_is_host,
team2_confederation, team2_fifa_rank, team2_coach,
team2_elo_rating, team2_elo_rank, team2_elo_country_code, team2_elo_is_host,
team1_elo_snapshot_date, team2_elo_snapshot_date
```

Validation notes:

- Duplicate rows: 0
- `date` parses successfully.
- Date range: `2026-06-11` to `2026-07-19`
- Known fixtures: 72
- Placeholder fixtures: 32
- Known fixtures missing Elo ratings:
  - `team1_elo_rating`: 0
  - `team2_elo_rating`: 0
- Placeholder fixtures missing Elo ratings:
  - `team1_elo_rating`: 32
  - `team2_elo_rating`: 32
- No `_x` / `_y` merge columns.
- No engineered `elo_diff` column.

Readiness:

- Ready as the final fixture enrichment output.
- This is the recommended input for the next feature engineering phase.

## Overall Status

All processed datasets are valid for their current intended purpose.

Recommended usage:

- Use `results_historical.csv` for training labels and historical modeling.
- Use `model_training_base.csv` as the lightweight base training export for Feature Engineering.
- Use `results_future.csv` only as future result-style reference data.
- Use `elo_history.csv` for time-aware historical feature engineering.
- Use `elo_latest.csv` for current team-strength enrichment.
- Use `wc_2026_teams_cleaned.csv` as the team reference table.
- Use `wc_2026_fixtures_validated.csv` as the validated fixture source.
- Use `wc_2026_fixtures_enriched.csv` as the lean production enrichment output.

Final verdict:

```text
Processed datasets are ready for the next phase.
```
