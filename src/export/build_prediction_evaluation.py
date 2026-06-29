from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.match_results import get_match_source_of_truth

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PREDICTIONS_PATH = PROCESSED_DIR / "predictions_2026.csv"
LIVE_MATCHES_PATH = PROCESSED_DIR / "live_matches.csv"
OUTPUT_PATH = PROCESSED_DIR / "prediction_evaluation.csv"

TEAM_ALIASES = {
    "United States": "USA",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Cape Verde Islands": "Cape Verde",
    "Congo DR": "DR Congo",
    "Turkey": "Türkiye",
}

OUTPUT_COLUMNS = [
    "match_id",
    "home_team",
    "away_team",
    "predicted_winner",
    "actual_winner",
    "prediction_correct",
    "model_confidence",
]


def _pair_key(home: Any, away: Any) -> frozenset[str] | None:
    if pd.isna(home) or pd.isna(away):
        return None
    return frozenset({str(home), str(away)})


def build_prediction_evaluation(
    predictions_path: Path = PREDICTIONS_PATH,
    live_matches_path: Path = LIVE_MATCHES_PATH,
    output_path: Path = OUTPUT_PATH,
) -> Path:
    predictions = pd.read_csv(predictions_path)
    live = pd.read_csv(live_matches_path)
    live["home_team"] = live["home_team"].replace(TEAM_ALIASES)
    live["away_team"] = live["away_team"].replace(TEAM_ALIASES)
    live = live[live["stage"].eq("GROUP_STAGE")].copy()
    live["pair"] = live.apply(lambda row: _pair_key(row.home_team, row.away_team), axis=1)
    live_by_pair = {row.pair: row for row in live.itertuples(index=False) if row.pair is not None}

    rows = []
    for prediction in predictions.itertuples(index=False):
        pair = _pair_key(prediction.team1, prediction.team2)
        match = live_by_pair.get(pair)
        if match is None or str(match.status).upper() not in {"FINISHED", "COMPLETED", "FT"}:
            continue

        team1_is_home = match.home_team == prediction.team1
        home_score = match.home_score if team1_is_home else match.away_score
        away_score = match.away_score if team1_is_home else match.home_score
        match_row = {
            "status": match.status,
            "home_team": prediction.team1,
            "away_team": prediction.team2,
            "home_goals": home_score,
            "away_goals": away_score,
            "is_finished": True,
        }
        prediction_row = {
            "home_win_probability": prediction.team1_win_prob,
            "draw_probability": prediction.draw_prob,
            "away_win_probability": prediction.team2_win_prob,
        }
        truth = get_match_source_of_truth(match_row, prediction_row)
        predicted = get_match_source_of_truth(
            {"home_team": prediction.team1, "away_team": prediction.team2, "status": "SCHEDULED"},
            prediction_row,
        )
        actual_winner = truth["winner"] or "Draw"
        predicted_winner = predicted["winner"] or "Draw"
        rows.append({
            "match_id": match.match_id,
            "home_team": prediction.team1,
            "away_team": prediction.team2,
            "predicted_winner": predicted_winner,
            "actual_winner": actual_winner,
            "prediction_correct": predicted_winner == actual_winner,
            "model_confidence": max(prediction_row.values()),
        })

    evaluation = pd.DataFrame(rows, columns=OUTPUT_COLUMNS)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_suffix(".tmp")
    evaluation.to_csv(temp_path, index=False)
    temp_path.replace(output_path)
    print(f"Saved: {output_path}")
    print(f"Rows: {len(evaluation)}")
    return output_path


if __name__ == "__main__":
    build_prediction_evaluation()
