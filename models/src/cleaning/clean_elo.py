from __future__ import annotations

from pathlib import Path

from src.transform.clean_elo import DEFAULT_AS_OF_DATE
from src.transform.clean_elo import clean_elo as transform_clean_elo
from src.transform.clean_elo import save_clean_elo


def _validate_input_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")


def _validate_output_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Expected output file was not created: {path}")
    if path.stat().st_size == 0:
        raise ValueError(f"Output file is empty: {path}")


def clean_elo(
    input_path: str | Path,
    teams_path: str | Path,
    output_dir: str | Path,
    as_of_date: str = DEFAULT_AS_OF_DATE,
) -> None:
    """Clean Elo history and create the latest Elo snapshot."""
    input_path = Path(input_path)
    teams_path = Path(teams_path)
    output_dir = Path(output_dir)

    _validate_input_file(input_path)
    _validate_input_file(teams_path)

    elo_history, elo_latest = transform_clean_elo(
        input_path,
        as_of_date=as_of_date,
        reference_teams_path=teams_path,
    )
    save_clean_elo(elo_history, elo_latest, output_dir)

    _validate_output_file(output_dir / "elo_history.csv")
    _validate_output_file(output_dir / "elo_latest.csv")
