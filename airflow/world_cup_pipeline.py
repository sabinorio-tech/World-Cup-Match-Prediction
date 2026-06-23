from __future__ import annotations

import sys
from datetime import datetime
import os
from pathlib import Path

from airflow import DAG

try:
    from airflow.providers.standard.operators.python import PythonOperator
except ImportError:
    from airflow.operators.python import PythonOperator

BASE_DIR = Path(
    os.environ.get(
        "WORLD_CUP_PROJECT_DIR",
        "/home/seans/becode/projects/World-Cup-Match-Prediction",
    )
).resolve()
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

sys.path.insert(0, str(BASE_DIR))

from src.cleaning.clean_results import clean_results
from src.cleaning.clean_elo import clean_elo
from src.cleaning.standardize_teams import standardize_teams
from src.enrichment.enrich_fixtures import enrich_fixtures
from src.export.build_model_dataset import build_model_dataset


default_args = {
    "owner": "sean",
    "depends_on_past": False,
}


def run_clean_results() -> None:
    clean_results(
        input_path=RAW_DIR / "IF_1872_2026" / "results.csv",
        output_dir=PROCESSED_DIR,
    )


def run_clean_elo() -> None:
    clean_elo(
        input_path=RAW_DIR / "FIFA_WK_Elo_Ratings" / "elo_ratings_wc2026.csv",
        teams_path=RAW_DIR / "FIFA_WC_1930_2026" / "wc_2026_teams.csv",
        output_dir=PROCESSED_DIR,
    )


def run_standardize_teams() -> None:
    standardize_teams(
        teams_input_path=RAW_DIR / "FIFA_WC_1930_2026" / "wc_2026_teams.csv",
        fixtures_input_path=RAW_DIR / "FIFA_WC_1930_2026" / "wc_2026_fixtures.csv",
        elo_latest_path=PROCESSED_DIR / "elo_latest.csv",
        teams_output_path=PROCESSED_DIR / "wc_2026_teams_cleaned.csv",
        fixtures_output_path=PROCESSED_DIR / "wc_2026_fixtures_validated.csv",
    )


def run_enrich_fixtures() -> None:
    enrich_fixtures(
        fixtures_path=PROCESSED_DIR / "wc_2026_fixtures_validated.csv",
        teams_path=PROCESSED_DIR / "wc_2026_teams_cleaned.csv",
        elo_latest_path=PROCESSED_DIR / "elo_latest.csv",
        output_path=PROCESSED_DIR / "wc_2026_fixtures_enriched.csv",
    )


def run_build_model_dataset() -> None:
    build_model_dataset(
        historical_results_path=PROCESSED_DIR / "results_historical.csv",
        output_path=PROCESSED_DIR / "model_training_base.csv",
    )


with DAG(
    dag_id="world_cup_pipeline",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule="30 14 * * *",
    catchup=False,
    tags=["world-cup", "data-engineering"],
) as dag:
    clean_results_task = PythonOperator(
        task_id="clean_results",
        python_callable=run_clean_results,
    )

    clean_elo_task = PythonOperator(
        task_id="process_elo",
        python_callable=run_clean_elo,
    )

    standardize_task = PythonOperator(
        task_id="standardize_teams",
        python_callable=run_standardize_teams,
    )

    enrich_task = PythonOperator(
        task_id="enrich_fixtures",
        python_callable=run_enrich_fixtures,
    )

    build_dataset_task = PythonOperator(
        task_id="build_model_dataset",
        python_callable=run_build_model_dataset,
    )

    (
        clean_results_task
        >> clean_elo_task
        >> standardize_task
        >> enrich_task
        >> build_dataset_task
    )
