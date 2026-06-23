from __future__ import annotations

from pathlib import Path

import pandas as pd


MODEL_BASE_COLUMNS = [
    "date",
    "home_team",
    "away_team",
    "home_score",
    "away_score",
    "tournament",
    "city",
    "country",
    "neutral",
    "outcome",
]


def _validate_input_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")


def _validate_output_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Expected output file was not created: {path}")
    if path.stat().st_size == 0:
        raise ValueError(f"Output file is empty: {path}")


def build_model_dataset(
    historical_results_path: str | Path,
    output_path: str | Path,
) -> None:
    """Create a lightweight base modeling dataset from completed matches.

    This is intentionally not a feature-engineered dataset yet. Feature creation
    belongs in the next project phase under src/features/.
    """
    historical_results_path = Path(historical_results_path)
    output_path = Path(output_path)

    _validate_input_file(historical_results_path)

    historical_results = pd.read_csv(historical_results_path)
    missing_columns = set(MODEL_BASE_COLUMNS) - set(historical_results.columns)
    if missing_columns:
        raise ValueError(
            f"Historical results missing columns: {sorted(missing_columns)}"
        )

    model_dataset = historical_results[MODEL_BASE_COLUMNS].copy()
    model_dataset["date"] = pd.to_datetime(
        model_dataset["date"],
        format="%Y-%m-%d",
        errors="raise",
    )

    if model_dataset.empty:
        raise ValueError("Model base dataset is empty")
    if model_dataset["outcome"].isna().any():
        raise ValueError("Model base dataset contains missing target values")
    if model_dataset.duplicated().sum() != 0:
        raise ValueError("Model base dataset contains duplicate rows")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    model_dataset.to_csv(output_path, index=False)

    _validate_output_file(output_path)
