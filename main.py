from __future__ import annotations

from pathlib import Path

from src.cleaning.clean_elo import clean_elo
from src.cleaning.clean_results import clean_results
from src.cleaning.standardize_teams import standardize_teams
from src.enrichment.enrich_fixtures import enrich_fixtures
from src.export.build_model_dataset import build_model_dataset
from src.extract.football_data_api import fetch_competition_matches, get_api_key, save_json
from src.features.build_features import build_features
from src.models.train_poisson import train_poisson
from src.models.train_xgb import train_xgb
from src.predict.batch_predict import batch_predict
from src.transform.live_matches import load_raw_matches, transform_matches, save_matches

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"


def run_stage(label: str, action) -> None:
    print(label)
    try:
        action()
    except Exception as exc:
        print(f"Pipeline failed during {label}: {exc}")
        raise


def run_live_data_pipeline() -> None:
    """Fetch and transform live World Cup data when an API key is configured."""
    if not get_api_key():
        print("Skipping live World Cup matches: FOOTBALL_DATA_API_KEY is not set.")
        return

    matches = fetch_competition_matches("WC", 2026)
    raw_output_path = save_json(matches, "football_data_wc_matches.json")

    raw_live_matches = load_raw_matches(raw_output_path)
    live_matches = transform_matches(raw_live_matches)
    save_matches(live_matches)


def main() -> None:
    """Run the complete Data Engineering and Machine Learning pipeline."""
    run_stage(
        "[1/10] Cleaning historical results...",
        lambda: clean_results(
            input_path=RAW_DIR / "IF_1872_2026" / "results.csv",
            output_dir=PROCESSED_DIR,
        ),
    )

    run_stage(
        "[2/10] Processing Elo ratings...",
        lambda: clean_elo(
            input_path=RAW_DIR / "FIFA_WK_Elo_Ratings" / "elo_ratings_wc2026.csv",
            teams_path=RAW_DIR / "FIFA_WC_1930_2026" / "wc_2026_teams.csv",
            output_dir=PROCESSED_DIR,
        ),
    )

    run_stage(
        "[3/10] Standardizing team and fixture references...",
        lambda: standardize_teams(
            teams_input_path=RAW_DIR / "FIFA_WC_1930_2026" / "wc_2026_teams.csv",
            fixtures_input_path=RAW_DIR / "FIFA_WC_1930_2026" / "wc_2026_fixtures.csv",
            elo_latest_path=PROCESSED_DIR / "elo_latest.csv",
            teams_output_path=PROCESSED_DIR / "wc_2026_teams_cleaned.csv",
            fixtures_output_path=PROCESSED_DIR / "wc_2026_fixtures_validated.csv",
        ),
    )

    run_stage(
        "[4/10] Enriching World Cup 2026 fixtures...",
        lambda: enrich_fixtures(
            fixtures_path=PROCESSED_DIR / "wc_2026_fixtures_validated.csv",
            teams_path=PROCESSED_DIR / "wc_2026_teams_cleaned.csv",
            elo_latest_path=PROCESSED_DIR / "elo_latest.csv",
            output_path=PROCESSED_DIR / "wc_2026_fixtures_enriched.csv",
        ),
    )

    run_stage(
        "[5/10] Building base model dataset...",
        lambda: build_model_dataset(
            historical_results_path=PROCESSED_DIR / "results_historical.csv",
            output_path=PROCESSED_DIR / "model_training_base.csv",
        ),
    )

    run_stage("[6/10] Fetching and transforming live World Cup matches...", run_live_data_pipeline)
    run_stage("[7/10] Building ML features...", build_features)
    run_stage("[8/10] Training XGBoost...", train_xgb)
    run_stage("[9/10] Training Poisson model...", train_poisson)
    run_stage("[10/10] Generating World Cup predictions...", batch_predict)

    print("Pipeline completed successfully.")


if __name__ == "__main__":
    main()
