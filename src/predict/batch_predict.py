from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.predict import predict_match

BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"


def _atomic_to_csv(df: pd.DataFrame, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    df.to_csv(temp_path, index=False)
    temp_path.replace(output_path)
    return output_path


def _known_team_mask(fixtures: pd.DataFrame) -> pd.Series:
    mask = fixtures["team1"].notna() & fixtures["team2"].notna()
    if "is_placeholder_match" in fixtures.columns:
        placeholder = fixtures["is_placeholder_match"]
        if placeholder.dtype == object:
            placeholder = placeholder.astype(str).str.lower().isin(["true", "1", "yes"])
        mask &= ~placeholder.astype(bool)
    return mask


def _favorite_label(prediction: dict, home: str, away: str) -> str:
    favorite = prediction["favorite"]
    if favorite == "home_win":
        return home
    if favorite == "away_win":
        return away
    return "draw"


def build_prediction_frame(fixtures: pd.DataFrame) -> pd.DataFrame:
    known_fixtures = fixtures[_known_team_mask(fixtures)].copy()
    if known_fixtures.empty:
        raise ValueError("No known World Cup fixtures available for batch prediction.")

    rows = []
    for _, match in known_fixtures.iterrows():
        team1 = match["team1"]
        team2 = match["team2"]
        prediction = predict_match(team1, team2, neutral=True)

        rows.append(
            {
                "group": match.get("group"),
                "date": match.get("date"),
                "team1": team1,
                "team2": team2,
                "team1_win_prob": prediction["home_win"],
                "draw_prob": prediction["draw"],
                "team2_win_prob": prediction["away_win"],
                "favorite": _favorite_label(prediction, team1, team2),
            }
        )

    predictions = pd.DataFrame(rows)
    return predictions.sort_values(["group", "date", "team1", "team2"]).reset_index(drop=True)


def batch_predict(
    fixtures_path: Path = PROCESSED_DIR / "wc_2026_fixtures_enriched.csv",
    output_path: Path = PROCESSED_DIR / "predictions_2026.csv",
) -> Path:
    fixtures = pd.read_csv(fixtures_path)
    predictions = build_prediction_frame(fixtures)
    path = _atomic_to_csv(predictions, output_path)
    print(f"✓ predictions_2026.csv exported ({len(predictions):,} matches)")
    return path


if __name__ == "__main__":
    batch_predict()
