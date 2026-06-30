from __future__ import annotations

from pathlib import Path

from src.transform.clean_results import clean_results as transform_clean_results
from src.transform.clean_results import save_clean_results


def _validate_input_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")


def _validate_output_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Expected output file was not created: {path}")
    if path.stat().st_size == 0:
        raise ValueError(f"Output file is empty: {path}")


def clean_results(
    input_path: str | Path,
    output_dir: str | Path,
) -> None:
    """Clean historical results and split completed/future matches."""
    input_path = Path(input_path)
    output_dir = Path(output_dir)

    _validate_input_file(input_path)

    historical_matches, future_matches = transform_clean_results(input_path)
    save_clean_results(historical_matches, future_matches, output_dir)

    _validate_output_file(output_dir / "results_historical.csv")
    _validate_output_file(output_dir / "results_future.csv")
