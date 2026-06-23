from __future__ import annotations

from pathlib import Path

from src.transform.enrich_fixtures import enrich_fixtures as transform_enrich_fixtures
from src.transform.enrich_fixtures import save_output


def _validate_input_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")


def _validate_output_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Expected output file was not created: {path}")
    if path.stat().st_size == 0:
        raise ValueError(f"Output file is empty: {path}")


def enrich_fixtures(
    fixtures_path: str | Path,
    teams_path: str | Path,
    elo_latest_path: str | Path,
    output_path: str | Path,
) -> None:
    """Create the lean enriched World Cup 2026 fixture dataset."""
    fixtures_path = Path(fixtures_path)
    teams_path = Path(teams_path)
    elo_latest_path = Path(elo_latest_path)
    output_path = Path(output_path)

    for path in [fixtures_path, teams_path, elo_latest_path]:
        _validate_input_file(path)

    enriched = transform_enrich_fixtures(
        fixtures_path=fixtures_path,
        teams_path=teams_path,
        elo_latest_path=elo_latest_path,
    )
    save_output(enriched, output_path)

    _validate_output_file(output_path)
