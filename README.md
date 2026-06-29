# FIFA World Cup 2026 Match Prediction

[![Project Status](https://img.shields.io/badge/status-portfolio%20v1.0-green)](#)
[![Python](https://img.shields.io/badge/python-3.12-blue)](#)
[![BeCode](https://img.shields.io/badge/BeCode-team%20project-black)](#)

## Project Overview

This project predicts FIFA World Cup 2026 match outcomes using historical international results, Elo ratings, qualified-team and fixture data, live tournament results, and an automated XGBoost/Poisson ensemble.

The project is structured as an end-to-end data product. The Data Engineering layer cleans, validates, standardizes, enriches, and exports reusable datasets for modeling, dashboarding, and AI assistant workflows.

The end-to-end pipeline also resolves knockout fixtures, enriches team pages with StatBunker player data, evaluates completed predictions, and supplies a multi-page Streamlit analytics dashboard.

## Project Objectives

- Build a clean and maintainable football match prediction dataset.
- Separate completed historical matches from future fixtures.
- Standardize team names across all input sources.
- Validate FIFA World Cup 2026 team and fixture coverage.
- Enrich World Cup 2026 fixtures with selected team metadata and Elo attributes.
- Produce lean processed datasets that can be reused by feature engineering, modeling, and dashboard workflows.
- Keep data engineering outputs separate from later machine learning features.
- Ingest live World Cup 2026 match data from football-data.org.
- Store raw live API responses separately from processed datasets.
- Transform live match data into a dashboard-ready match status dataset.
- Support scheduled refreshes for overnight match results and upcoming fixture status.
- Generate deterministic ML features, train versioned models, and export batch predictions without notebooks.
- Resolve confirmed knockout participants and prefer actual results over projected winners.
- Enrich team analytics with tournament-specific player statistics.
- Present predictions, results, standings, team analytics, and bracket progression in Streamlit.

## Data Sources

The project uses six primary data source groups:

| Source | Purpose |
| --- | --- |
| Historical international results | Completed international match results used for training and historical analysis. |
| FIFA World Cup 2026 teams | Qualified team reference data, including group, confederation, FIFA rank, coach, best World Cup result, and debut status. |
| Elo ratings | Historical and latest Elo ratings for qualified teams. |
| FIFA World Cup 2026 fixtures | Group-stage fixtures and knockout-stage placeholder fixtures for the 2026 tournament. |
| football-data.org | Live World Cup match data, including match status, kickoff time, teams, scores, and result updates. |
| StatBunker | Tournament player appearances, starts, goals, assists, cards, and available shooting statistics. |

Raw data is stored under `data/raw/`. Cleaned and reusable outputs are stored under `data/processed/`.

## Project Structure

```text
.
├── data/
│   ├── processed/
│   │   ├── features.csv
│   │   ├── knockout_matches.csv
│   │   ├── live_matches.csv
│   │   ├── player_profiles.csv
│   │   ├── player_stats.csv
│   │   ├── prediction_evaluation.csv
│   │   ├── predictions_2026.csv
│   │   └── ...
│   └── raw/
│       ├── live/football_data_wc_matches.json
│       └── player_data/*.html
├── dashboard/
│   ├── app.py
│   ├── cache_utils.py
│   ├── components.py
│   ├── data.py
│   ├── realdata.py
│   ├── simulate.py
│   └── time_utils.py
├── docs/
│   ├── ds_modeling_report_v2.md
│   ├── knockout_resolution.md
│   ├── player_data_pipeline.md
│   └── ...
├── models/
│   ├── poisson_model.pkl
│   └── xgb_model.pkl
├── notebooks/
│   └── exploratory and historical modeling notebooks
├── requirements/
│   └── grouped runtime and development dependencies
├── src/
│   ├── assistant/
│   ├── cleaning/
│   ├── enrichment/
│   ├── export/
│   ├── extract/
│   ├── features/
│   ├── models/
│   ├── predict/
│   ├── transform/
│   └── utils/
├── tests/
├── .github/
│   └── workflows/
│       └── de_pipeline.yml
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## Data Engineering Pipeline

The 13-stage pipeline converts raw football data into validated datasets, trained model artifacts, current tournament state, and dashboard-ready predictions.

```text
Raw sources
  -> results and Elo cleaning
  -> team and fixture standardization
  -> fixture enrichment and base model dataset
  -> live match ingestion
  -> knockout resolution
  -> player enrichment
  -> feature engineering
  -> XGBoost and Poisson training
  -> batch predictions
  -> completed-prediction evaluation
  -> Streamlit-ready outputs
```

### Extract and Transform Scripts

| Script | Purpose | Main outputs |
| --- | --- | --- |
| `src/cleaning/clean_results.py` | Cleans historical results and separates completed and future matches. | `results_historical.csv`, `results_future.csv` |
| `src/cleaning/clean_elo.py` | Cleans Elo ratings and creates the latest qualified-team snapshot. | `elo_history.csv`, `elo_latest.csv` |
| `src/enrichment/enrich_fixtures.py` | Enriches all 104 fixtures with team and Elo context. | `wc_2026_fixtures_enriched.csv` |
| `src/extract/football_data_api.py` | Fetches World Cup 2026 match data from football-data.org and stores the raw API response. | `data/raw/live/football_data_wc_matches.json` |
| `src/transform/live_matches.py` | Flattens the live API response into a dashboard-ready match status dataset. | `live_matches.csv` |
| `src/transform/knockout_matches.py` | Resolves official knockout slots and applies actual-result precedence. | `knockout_matches.csv` |
| `src/enrichment/fetch_player_data.py` | Fetches, caches, transforms, and validates free player data. | `player_profiles.csv`, `player_stats.csv` |
| `src/features/build_features.py` | Builds rolling form, Elo, and H2H model features. | `features.csv` |
| `src/models/train_xgb.py`, `train_poisson.py` | Trains deterministic v2/H2H model artifacts. | `models/*.pkl` |
| `src/predict/batch_predict.py` | Generates all known group-stage fixture probabilities. | `predictions_2026.csv` |
| `src/export/build_prediction_evaluation.py` | Compares predictions with completed match outcomes. | `prediction_evaluation.csv` |

### Pipeline Entry Point

The root-level `main.py` runs Data Engineering and Machine Learning end to end. Notebook execution is not required.

The pipeline currently runs:

1. Clean historical results.
2. Process Elo ratings.
3. Standardize team and fixture references.
4. Enrich World Cup 2026 fixtures.
5. Build the base model dataset.
6. Fetch and transform live World Cup match data from football-data.org.
7. Resolve knockout fixtures.
8. Fetch and transform player data, with cached fallback if StatBunker is unavailable.
9. Build ML features.
10. Train the XGBoost model.
11. Train the Poisson model.
12. Generate World Cup predictions.
13. Evaluate predictions for completed matches.

The live-data step requires `FOOTBALL_DATA_API_KEY`. When the key is available, the pipeline writes the raw API response to `data/raw/live/football_data_wc_matches.json` and the processed output to `data/processed/live_matches.csv`.

## Processed Datasets

| Dataset | Description |
| --- | --- |
| `results_historical.csv` | Completed historical international matches with scores and outcome labels. |
| `results_future.csv` | Future result-style rows separated from the raw results source. Scores are intentionally missing. |
| `elo_history.csv` | Historical Elo ratings for the 48 World Cup 2026 teams. Must be used with time-aware joins. |
| `elo_latest.csv` | Latest Elo snapshot for the 48 qualified teams. Used for fixture enrichment. |
| `wc_2026_teams_cleaned.csv` | Cleaned reference table for all 48 qualified World Cup 2026 teams. |
| `wc_2026_fixtures_validated.csv` | Validated fixture table with group-stage teams and knockout placeholders. |
| `wc_2026_fixtures_enriched.csv` | Lean enriched fixture dataset containing all 104 fixtures, selected team metadata, and selected Elo attributes. |
| `model_training_base.csv` | Lightweight base modeling export from completed historical matches. |
| `live_matches.csv` | Dashboard-ready live World Cup match data from football-data.org, including match status, kickoff date/time, teams, scores, and score display fields. |
| `knockout_matches.csv` | Official knockout structure with confirmed teams, original slots, status, scores, and actual/projected result source. |
| `player_profiles.csv` | Normalized player identity, team, position, and reserved profile fields. |
| `player_stats.csv` | Available World Cup player appearances, goals, assists, cards, and shooting statistics. |
| `features.csv` | Reproducible v2 model features, including rolling form, Elo difference, and H2H context. |
| `predictions_2026.csv` | Home/draw/away probabilities and favorite for all 72 known group fixtures. |
| `prediction_evaluation.csv` | Predicted versus actual outcomes for completed matches. |

The main enriched fixture output keeps all 104 fixtures:

- 72 known group-stage fixtures include team and Elo metadata.
- 32 knockout-stage rows remain in the enriched fixture skeleton; confirmed participants are resolved separately in `knockout_matches.csv`.
- No engineered ML features are included in this file.

More detailed dataset profiling is available in:

- `docs/data_findings.md`
- `docs/fixture_enrichment_readiness_report.md`
- `docs/processed_data_report.md`

## Live Match Data

Live World Cup match data is fetched from football-data.org.

Raw API output:

```text
data/raw/live/football_data_wc_matches.json
```

Processed output:

```text
data/processed/live_matches.csv
```

The processed live match dataset includes Streamlit-ready columns such as:

- `match_date`
- `kickoff_time_utc`
- `status`
- `is_finished`
- `is_scheduled`
- `has_score`
- `home_team`
- `away_team`
- `home_score`
- `away_score`
- `score_display`

Future matches can have null score fields. Knockout placeholder matches can have null team fields. These null values are expected and should be handled by dashboard logic.

## Current Project Status

The project is a portfolio-ready v1.0 MVP with an automated Data Engineering and Machine Learning pipeline.

Completed work:

- Raw data discovery and documentation.
- Historical results cleaning.
- Future fixture separation from historical results.
- Team-name standardization across datasets.
- Elo history cleaning and latest snapshot creation.
- World Cup 2026 team reference validation.
- World Cup 2026 fixture validation.
- Lean fixture enrichment.
- Base model dataset export.
- Live World Cup match extraction from football-data.org.
- Live match transformation into `live_matches.csv`.
- Confirmed knockout resolution with actual-result precedence.
- StatBunker player enrichment with cached fallback behavior.
- Automated v2/H2H feature engineering and model training.
- XGBoost and Poisson ensemble prediction export.
- Completed-match prediction evaluation.
- Streamlit Overview, Match Details, Groups, Knockout Bracket, Teams, and About pages.
- TTL-based dashboard data caching and source freshness timestamps.
- GitHub Actions pipeline support for scheduled refreshes.
- Processed dataset documentation.

The project supports modeling, dashboarding, and AI assistant workflows without requiring notebooks to regenerate production outputs.

## Current Limitations

- StatBunker is an HTML source and can temporarily reject automated requests; cached raw files keep the pipeline usable.
- Advanced player metrics and player portraits are not reliably available from the selected free source.
- Composite third-place knockout slots are not guessed before the provider confirms participants.
- Tournament simulations and model probabilities are analytical projections, not guarantees.
- Freshness timestamps are displayed, but the dashboard does not yet raise a separate stale-data warning.

## How to Run the Project

### 1. Clone the repository

```bash
git clone <repository-url>
cd World-Cup-Match-Prediction
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Add your football-data.org API token:

```text
FOOTBALL_DATA_API_KEY=your_api_token_here
```

The `.env` file is ignored by Git and must not be committed.

### 5. Run the complete pipeline

Run all 13 Data Engineering and Machine Learning stages from the project root:

```bash
python main.py
```

This refreshes source data, processed datasets, model artifacts, predictions, and evaluation outputs.

If your environment does not expose `python`, use:

```bash
.venv/bin/python main.py
```

### 6. Run the Streamlit dashboard

```bash
streamlit run dashboard/app.py
```

The dashboard reads the generated files under `data/processed/` and the model artifacts under `models/`.

### 7. Run individual pipeline stages

Clean historical results:

```bash
python src/transform/clean_results.py
```

Clean Elo ratings:

```bash
python src/transform/clean_elo.py
```

Create the lean enriched fixture dataset:

```bash
python src/transform/enrich_fixtures.py
```

Expected enriched output:

```text
data/processed/wc_2026_fixtures_enriched.csv
```

Fetch live World Cup match data:

```bash
python src/extract/football_data_api.py
```

Transform live World Cup match data:

```bash
python src/transform/live_matches.py
```

Expected live output:

```text
data/processed/live_matches.csv
```

Build features and models independently:

```bash
python -m src.features.build_features
python -m src.models.train_xgb
python -m src.models.train_poisson
python -m src.predict.batch_predict
```

### 8. Run tests

```bash
pytest -q
```

The root-level `test_ollama.py` is an optional manual connectivity check and only runs when executed directly.

### 9. Explore notebooks

Notebook-based discovery and validation work is available in:

```text
notebooks/
```

Run notebooks with:

```bash
jupyter notebook
```

## GitHub Actions Automation

The complete Data Engineering and Machine Learning pipeline is automated with GitHub Actions.

Workflow:

```text
.github/workflows/de_pipeline.yml
```

The workflow runs:

- on manual dispatch
- on relevant source-code/input pushes to `main` and `feature/ai-assistant`
- on a daily schedule

Current schedule:

```text
06:00 UTC daily
08:00 Belgium time during summer
```

The scheduled run is intended to refresh World Cup results and match status after overnight matches.

The workflow requires the following GitHub repository secret:

```text
FOOTBALL_DATA_API_KEY
```

This secret is passed to `main.py` during the live-data extraction step. The API token should never be committed to the repository.

The workflow validates all key CSV and model outputs, runs actual-result regression tests, uploads generated datasets/models as a GitHub artifact, and commits refreshed dashboard data and model artifacts back to the branch. It has `contents: write` permission for this purpose. Scheduled workflows run from the repository's default branch.

## Dashboard Data Availability

The dashboard can consume both static prediction datasets and refreshed live match data.

Relevant dashboard-ready datasets:

| Dataset | Dashboard use |
| --- | --- |
| `wc_2026_teams_cleaned.csv` | Team profiles, groups, confederations, FIFA ranks. |
| `elo_latest.csv` | Team strength, Elo-based comparisons, dashboard KPIs. |
| `wc_2026_fixtures_enriched.csv` | Fixture context, venues, cities, team metadata, Elo context. |
| `predictions_2026.csv` | Group-stage model probabilities for match prediction cards. |
| `live_matches.csv` | Latest match status, scores, kickoff times, and live/upcoming match display. |
| `knockout_matches.csv` | Resolved knockout participants, actual results, and projected advancement fallback. |
| `player_profiles.csv`, `player_stats.csv` | Teams-page player identity and available tournament statistics. |
| `prediction_evaluation.csv` | Actual-versus-predicted outcome checks for completed matches. |

`live_matches.csv` should be used by the frontend as the preferred source for current match status and score display.

## Technologies Used

- Python
- Pandas
- NumPy
- Requests
- python-dotenv
- Jupyter Notebook
- SQL / database schema planning
- Git and GitHub
- GitHub Actions
- Streamlit
- football-data.org API
- StatBunker player data
- scikit-learn
- XGBoost
- SciPy
- Plotly / Altair
- Airflow / scheduling tooling for local orchestration experiments

## Notes

- `wc_2026_fixtures_enriched.csv` is an enrichment output; production model features live in `features.csv`.
- Original knockout slots are retained for traceability while `knockout_matches.csv` stores resolved participants.
- Historical Elo and rolling match features must remain time-aware to avoid leakage.
- Processed datasets are versioned so team members can work from the same Data Engineering outputs.
- `.env` files are ignored and should be used for local secrets only.
- `FOOTBALL_DATA_API_KEY` must be configured locally or as a GitHub Actions repository secret for live-data extraction.
- `live_matches.csv` is a live-data output for dashboard status and score display.
- Future live matches can have null score fields.
- Future knockout rounds can retain null team fields until participants are known.
- The two production model artifacts under `models/` are intentionally versioned; other pickle files remain ignored.
