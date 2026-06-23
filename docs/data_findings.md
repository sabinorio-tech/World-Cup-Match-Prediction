# Data Discovery Report

## Project Goal

The objective of this project is to predict FIFA World Cup 2026 match outcomes using historical football results, Elo rating history, qualified-team reference data, and FIFA World Cup 2026 fixture information.

This document summarizes the initial data discovery findings before any cleaning, feature engineering, modeling, or pipeline development begins.

---

# Dataset Inventory

| Dataset Name | Purpose | Relevance | Status |
| --- | --- | --- | --- |
| `results.csv` | Historical international football match results, including scores, tournaments, dates, teams, and locations. | High | Authoritative historical match source |
| `wc_2026_teams.csv` | Reference list of the 48 qualified FIFA World Cup 2026 teams and team metadata. | High | Authoritative team reference source |
| `elo_ratings_wc2026.csv` | Historical and current Elo ratings for the 48 qualified World Cup 2026 teams. | High | Authoritative team-strength source |
| `wc_2026_fixtures.csv` | FIFA World Cup 2026 fixture list, including group-stage matches and knockout-stage placeholders. | High | Authoritative fixture source |

---

# Dataset Findings

## `results.csv`

### Findings

- Contains **49,477 rows** and **9 columns**.
- Date range starts at **1872-11-30** and extends into **2026**.
- Contains **44 missing values** in `home_score`.
- Contains **44 missing values** in `away_score`.
- Missing score values correspond to future FIFA World Cup 2026 matches.
- Contains **336 unique football entities**.
- Includes both FIFA teams and non-FIFA entities.
- FIFA World Cup matches represent a small fraction of the total match history.
- `neutral` is already stored as a boolean-style field.
- Scores are stored as float-compatible values because future-match score fields contain missing values.

### Conclusions

- `results.csv` should be treated as the authoritative historical match source.
- Future matches must be separated from completed historical matches.
- Team standardization is required before reliable joins can be made.

---

## `wc_2026_teams.csv`

### Findings

- Contains **48 rows** and **7 columns**.
- Contains no missing values.
- Contains one row per qualified FIFA World Cup 2026 team.
- Includes:
  - group
  - confederation
  - FIFA ranking
  - coach
  - best World Cup result
  - debut status
- The `team` column appears unique.

### Conclusions

- `wc_2026_teams.csv` should be treated as the authoritative team reference dataset for FIFA World Cup 2026.

---

## `elo_ratings_wc2026.csv`

### Findings

- Contains **4,683 rows** and **23 columns**.
- Contains no missing values.
- Covers **48 countries**.
- Coverage spans from **1901 to 2026**.
- Primarily contains yearly rating snapshots.
- Includes an additional FIFA World Cup 2026 snapshot.
- The dataset is not guaranteed to be chronologically sorted.
- Contains:
  - Elo ratings
  - Elo rankings
  - goals for
  - goals against
  - wins
  - losses
  - draws
  - confederation
  - host status

### Conclusions

- `elo_ratings_wc2026.csv` should be treated as the authoritative team-strength dataset.
- Temporal joins must be handled carefully to avoid data leakage.

---

## `wc_2026_fixtures.csv`

### Findings

- Contains **104 matches**.
- Contains **72 group-stage matches**.
- Contains **32 knockout-stage matches**.
- Group-stage rows contain team metadata.
- Knockout-stage rows contain placeholder entities.
- Placeholder examples include:
  - `1A`
  - `2B`
  - `Best 3rd #1`
  - `R32 W1`
  - `QF1`
  - `SF1`
  - `Finalist 1`
- Missing values in knockout-stage rows are expected and structural.

### Conclusions

- `wc_2026_fixtures.csv` should be treated as the authoritative fixture dataset.
- Placeholder entities are not data-quality issues.
- Group-stage fixtures and knockout-stage placeholders should be interpreted differently during later project phases.

---

# Dataset Relationships

The four primary datasets have complementary roles:

```text
results.csv
  |
  v
Historical matches

wc_2026_teams.csv
  |
  v
Team reference

elo_ratings_wc2026.csv
  |
  v
Team strength history

wc_2026_fixtures.csv
  |
  v
Future matches to predict
```

Conceptual joins:

- Historical match teams in `results.csv` can be aligned with standardized team names.
- FIFA World Cup 2026 teams in `wc_2026_teams.csv` can be used as the reference list for valid tournament teams.
- Elo ratings in `elo_ratings_wc2026.csv` can be linked to standardized team names and rating snapshot dates.
- Fixtures in `wc_2026_fixtures.csv` can be linked to the team reference and team-strength history for prediction context.

Reliable joins require team-name standardization before combining datasets.

---

# Team Standardization Findings

The following naming mismatches were identified during discovery:

| Canonical Name | Alternative Name |
| --- | --- |
| Türkiye | Turkey |
| USA | United States |
| Czechia | Czech Republic |

## Conclusion

A small team-name mapping layer will be required before joins can be trusted across datasets.

---

# Data Quality Findings

## Expected Missing Values

- Future match scores in `results.csv`.
- Knockout-stage team metadata in `wc_2026_fixtures.csv`.

These missing values are expected and should not automatically be interpreted as data-quality failures.

## Potential Risks

- Team-name mismatches across datasets.
- Temporal leakage when joining Elo ratings to historical matches.
- Historical football entities that are not relevant to FIFA World Cup 2026.
- Future 2026 fixtures mixed into historical result-style datasets.
- Knockout-stage placeholders requiring separate interpretation from known team names.

---

# Recommended MVP Dataset Strategy

The recommended primary datasets for the first MVP are:

- `results.csv`
- `wc_2026_teams.csv`
- `elo_ratings_wc2026.csv`
- `wc_2026_fixtures.csv`

These datasets are sufficient for the first MVP because they provide:

- an authoritative historical match source,
- an authoritative list of qualified FIFA World Cup 2026 teams,
- an authoritative team-strength history through Elo ratings,
- and an authoritative fixture list for matches to predict.

Together, they provide enough coverage to support an initial match-level prediction workflow after team standardization and historical/future match separation.

---

# Final Conclusions

- `results.csv` is the authoritative historical match source.
- `wc_2026_teams.csv` is the authoritative FIFA World Cup 2026 team reference source.
- `elo_ratings_wc2026.csv` is the authoritative team-strength source.
- `wc_2026_fixtures.csv` is the authoritative fixture source.
- The most important cleaning requirement is team-name standardization.
- Future matches must be separated from completed historical matches.
- Elo rating joins must be time-aware to prevent data leakage.
- Knockout-stage placeholders in the fixture dataset are expected and should not be treated as errors.
- The biggest risk is joining datasets before resolving team-name differences.

## Recommended Next Step

**Team Standardization Phase**

The next project phase should focus on defining a shared canonical team-name convention and documenting the approved mapping between alternative names across datasets.
