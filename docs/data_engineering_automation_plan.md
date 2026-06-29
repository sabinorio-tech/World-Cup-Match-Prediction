# Data Engineering Automation Plan

> **Historical planning document:** this records the original five-stage automation milestone. The production pipeline now contains 13 Data Engineering and Machine Learning stages, including live data, knockout resolution, player enrichment, model training, predictions, and evaluation. See `README.md` and `main.py` for the current authoritative flow.

## Objective

This document explains the lightweight Python pipeline added for the FIFA World Cup 2026 Match Prediction project.

The goal is to move the Data Engineering workflow from notebook/manual execution toward a reproducible command:

```bash
python main.py
```

This pipeline is intentionally simple. It prepares the project for future orchestration without adding Airflow or external API complexity yet.

## Previous Workflow

The project originally used notebooks and individual scripts for Data Engineering work:

- `notebooks/00_shared_data_discovery.ipynb`
- `notebooks/01_de_cleaning_exploration.ipynb`
- `notebooks/03_fixture_enrichment.ipynb`
- `src/transform/clean_results.py`
- `src/transform/clean_elo.py`
- `src/transform/enrich_fixtures.py`

These files remain useful for exploration, validation, and documentation. The new pipeline does not delete or replace the notebooks.

## New Pipeline

The root-level `main.py` runs the main Data Engineering steps in order:

```text
Raw data
  |
  v
Clean historical results
  |
  v
Clean/process Elo ratings
  |
  v
Standardize team and fixture references
  |
  v
Enrich World Cup 2026 fixtures
  |
  v
Build base model dataset
```

## Pipeline Modules

The pipeline-facing modules are organized as:

```text
src/
├── cleaning/
│   ├── clean_results.py
│   ├── clean_elo.py
│   └── standardize_teams.py
├── enrichment/
│   └── enrich_fixtures.py
└── export/
    └── build_model_dataset.py
```

The existing `src/transform/` scripts are still reused. The new modules act as lightweight orchestration wrappers with basic input/output checks.

## How to Run

From the project root:

```bash
python main.py
```

If your environment does not expose `python`, use the virtual environment interpreter:

```bash
.venv/bin/python main.py
```

Expected log output:

```text
[1/5] Cleaning historical results...
[2/5] Processing Elo ratings...
[3/5] Standardizing team and fixture references...
[4/5] Enriching World Cup 2026 fixtures...
[5/5] Building base model dataset...
Pipeline completed successfully.
```

## Generated Outputs

The pipeline writes processed datasets to `data/processed/`:

- `results_historical.csv`
- `results_future.csv`
- `elo_history.csv`
- `elo_latest.csv`
- `wc_2026_teams_cleaned.csv`
- `wc_2026_fixtures_validated.csv`
- `wc_2026_fixtures_enriched.csv`
- `model_training_base.csv`

`model_training_base.csv` is a simple base modeling export from completed historical matches. It is not a feature-engineered dataset. Feature engineering should happen in the next project phase under `src/features/`.

## Validation

The pipeline includes lightweight validation:

- input files must exist
- required columns must exist
- output files must be created
- output files must not be empty
- known World Cup fixture teams must match team and Elo references
- fixture stage counts must match the expected World Cup 2026 structure
- known group-stage fixtures must have complete metadata
- placeholder knockout fixtures are preserved
- enriched fixtures must keep the lean production schema
- the base modeling dataset must contain non-null target values

These checks are intentionally practical and lightweight. More formal validation can be added later if needed.

## Future Airflow Integration

Airflow should not be added yet. The current goal is to keep the pipeline easy to run locally.

Future Airflow tasks could map directly to the current steps:

1. Clean historical results
2. Clean Elo ratings
3. Standardize teams and fixtures
4. Enrich fixtures
5. Build modeling exports
6. Run validation checks
7. Load outputs to a database or dashboard layer

Because the current steps are now Python functions, they can later be wrapped by Airflow operators without redesigning the whole project.

## Future Live Football API Integration

The current project uses static raw data files. A future live-data layer could add:

- updated match results
- updated Elo or ranking snapshots
- injury/squad data
- live fixture changes
- post-match results during the tournament

Recommended future approach:

- keep API extraction under `src/extract/`
- store raw API responses separately before transformation
- preserve the current processed dataset contracts when possible
- add clear timestamp/as-of-date metadata for live data
- avoid mixing live API logic directly into cleaning or feature scripts

## Current Status

The pipeline is ready for local Data Engineering automation.

Next recommended phase:

```text
Feature Engineering
```

Feature Engineering should build on:

- `results_historical.csv`
- `elo_history.csv`
- `wc_2026_fixtures_enriched.csv`
- `model_training_base.csv`
