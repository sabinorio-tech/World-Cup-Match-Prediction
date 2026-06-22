# FIFA World Cup 2026 Match Prediction

[![Project Status](https://img.shields.io/badge/status-data%20engineering%20complete-green)](#)
[![Python](https://img.shields.io/badge/python-3.x-blue)](#)
[![BeCode](https://img.shields.io/badge/BeCode-team%20project-black)](#)

## Project Overview

This project aims to predict FIFA World Cup 2026 match outcomes using historical international football results, Elo ratings, qualified-team information, and FIFA World Cup 2026 fixture data.

The project is structured as an end-to-end data product. The Data Engineering phase is complete: raw data has been discovered, cleaned, validated, standardized, and transformed into reusable processed datasets. The project is now ready to move into Feature Engineering and Modeling.

## Project Objectives

- Build a clean and maintainable football match prediction dataset.
- Separate completed historical matches from future fixtures.
- Standardize team names across all input sources.
- Validate FIFA World Cup 2026 team and fixture coverage.
- Enrich World Cup 2026 fixtures with selected team metadata and Elo attributes.
- Produce lean processed datasets that can be reused by feature engineering, modeling, and dashboard workflows.
- Keep data engineering outputs separate from later machine learning features.

## Data Sources

The project uses four primary data source groups:

| Source | Purpose |
| --- | --- |
| Historical international results | Completed international match results used for training and historical analysis. |
| FIFA World Cup 2026 teams | Qualified team reference data, including group, confederation, FIFA rank, coach, best World Cup result, and debut status. |
| Elo ratings | Historical and latest Elo ratings for qualified teams. |
| FIFA World Cup 2026 fixtures | Group-stage fixtures and knockout-stage placeholder fixtures for the 2026 tournament. |

Raw data is stored under `data/raw/`. Cleaned and reusable outputs are stored under `data/processed/`.

## Project Structure

```text
.
├── data/
│   ├── external/
│   ├── processed/
│   │   ├── elo_history.csv
│   │   ├── elo_latest.csv
│   │   ├── results_future.csv
│   │   ├── results_historical.csv
│   │   ├── wc_2026_fixtures_enriched.csv
│   │   ├── wc_2026_fixtures_validated.csv
│   │   └── wc_2026_teams_cleaned.csv
│   └── raw/
├── database/
│   └── schema.sql
├── docs/
│   ├── data_findings.md
│   ├── fixture_enrichment_readiness_report.md
│   └── processed_data_report.md
├── notebooks/
│   ├── 00_shared_data_discovery.ipynb
│   ├── 01_de_cleaning_exploration.ipynb
│   └── 03_fixture_enrichment.ipynb
├── requirements/
│   ├── base.txt
│   ├── dashboard.txt
│   ├── de.txt
│   ├── dev.txt
│   └── ds.txt
├── src/
│   ├── extract/
│   ├── features/
│   ├── load/
│   ├── transform/
│   │   ├── clean_elo.py
│   │   ├── clean_results.py
│   │   └── enrich_fixtures.py
│   └── utils/
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## Data Engineering Pipeline

The current pipeline converts raw football data into validated processed datasets.

```text
Raw data
  |
  v
Data discovery and validation
  |
  v
Team-name standardization
  |
  v
Historical/future result split
  |
  v
Elo history cleaning and latest snapshot creation
  |
  v
World Cup 2026 fixture validation
  |
  v
Fixture enrichment with team metadata and latest Elo ratings
  |
  v
Processed datasets for feature engineering and modeling
```

### Transform Scripts

| Script | Purpose | Main outputs |
| --- | --- | --- |
| `src/transform/clean_results.py` | Cleans historical results, standardizes team names, separates completed and future matches, and adds match outcome labels. | `results_historical.csv`, `results_future.csv` |
| `src/transform/clean_elo.py` | Cleans Elo ratings, standardizes country names, validates coverage, and creates the latest Elo snapshot. | `elo_history.csv`, `elo_latest.csv` |
| `src/transform/enrich_fixtures.py` | Enriches all 104 World Cup 2026 fixtures with lean team and Elo metadata while preserving knockout placeholders. | `wc_2026_fixtures_enriched.csv` |

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

The main enriched fixture output keeps all 104 fixtures:

- 72 known group-stage fixtures include team and Elo metadata.
- 32 knockout-stage placeholder fixtures remain present with null team/Elo metadata.
- No engineered ML features are included in this file.

More detailed dataset profiling is available in:

- `docs/data_findings.md`
- `docs/fixture_enrichment_readiness_report.md`
- `docs/processed_data_report.md`

## Current Project Status

Data Engineering is complete.

Completed work:

- Raw data discovery and documentation.
- Historical results cleaning.
- Future fixture separation from historical results.
- Team-name standardization across datasets.
- Elo history cleaning and latest snapshot creation.
- World Cup 2026 team reference validation.
- World Cup 2026 fixture validation.
- Lean fixture enrichment.
- Processed dataset documentation.

The project is ready to transition into Feature Engineering.

## Next Steps

The next phase should focus on creating modeling-ready features from the processed datasets.

Recommended next steps:

- Build feature engineering scripts under `src/features/`.
- Create team-level and match-level features from historical results and Elo history.
- Use time-aware joins to avoid data leakage.
- Keep model features separate from raw enrichment outputs.
- Define train/test validation strategy.
- Prepare modeling datasets for Data Science workflows.
- Add automated validation checks for feature outputs.
- Document feature definitions and assumptions.

Model selection and detailed model evaluation should happen after the feature engineering layer is defined.

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

### 4. Run the Data Engineering transforms

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

### 5. Explore notebooks

Notebook-based discovery and validation work is available in:

```text
notebooks/
```

Run notebooks with:

```bash
jupyter notebook
```

## Technologies Used

- Python
- Pandas
- NumPy
- Jupyter Notebook
- SQL / database schema planning
- Git and GitHub
- Streamlit planned for dashboarding
- Airflow or scheduling tooling planned for later pipeline automation

## Notes

- `wc_2026_fixtures_enriched.csv` is an enrichment output, not a feature-engineered modeling dataset.
- Knockout-stage placeholders are expected and intentionally retained.
- Historical Elo data must be joined with date cutoffs during future feature engineering to avoid leakage.
- Processed datasets are versioned so team members can work from the same Data Engineering outputs.
