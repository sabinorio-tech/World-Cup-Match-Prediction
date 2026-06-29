from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd


FINISHED_STATUSES = {"FINISHED", "COMPLETED", "FT", "AET", "PEN"}


def _value(row: Any, *names: str) -> Any:
    if row is None:
        return None
    for name in names:
        if isinstance(row, Mapping) and name in row:
            return row[name]
        if hasattr(row, "get"):
            value = row.get(name, None)
            if value is not None:
                return value
        if hasattr(row, name):
            return getattr(row, name)
    return None


def _number(value: Any) -> float | None:
    number = pd.to_numeric(value, errors="coerce")
    return None if pd.isna(number) else float(number)


def _team(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _truthy(value: Any) -> bool:
    if value is None or pd.isna(value):
        return False
    return bool(value)


def _declared_winner(value: Any, home_team: str | None, away_team: str | None) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    upper = text.upper()
    if upper == "HOME_TEAM":
        return home_team
    if upper == "AWAY_TEAM":
        return away_team
    if upper in {"DRAW", "NONE"}:
        return None
    if text in {home_team, away_team}:
        return text
    return None


def get_match_source_of_truth(
    match_row: Any,
    prediction_row: Any = None,
    *,
    is_knockout: bool = False,
) -> dict[str, Any]:
    """Resolve a match outcome with completed results taking precedence."""
    home_team = _team(_value(match_row, "home_team", "team1"))
    away_team = _team(_value(match_row, "away_team", "team2"))
    home_score = _number(_value(match_row, "home_goals", "home_score", "team1_goals"))
    away_score = _number(_value(match_row, "away_goals", "away_score", "team2_goals"))
    home_penalties = _number(_value(match_row, "home_score_penalties", "home_penalties"))
    away_penalties = _number(_value(match_row, "away_score_penalties", "away_penalties"))
    status = str(_value(match_row, "status") or "").strip().upper()
    is_finished = status in FINISHED_STATUSES or _truthy(_value(match_row, "is_finished"))
    declared = _declared_winner(_value(match_row, "winner"), home_team, away_team)

    if is_finished and home_score is not None and away_score is not None:
        if home_score > away_score:
            winner = home_team
            outcome = "home_win"
        elif away_score > home_score:
            winner = away_team
            outcome = "away_win"
        elif is_knockout:
            if home_penalties is not None and away_penalties is not None and home_penalties != away_penalties:
                winner = home_team if home_penalties > away_penalties else away_team
                outcome = "home_win" if winner == home_team else "away_win"
            else:
                return {
                    "result_source": "unresolved",
                    "winner": None,
                    "outcome": None,
                    "home_score": home_score,
                    "away_score": away_score,
                    "home_penalties": home_penalties,
                    "away_penalties": away_penalties,
                    "display_label": "Unresolved tied knockout result",
                    "winner_consistent": declared is None,
                }
        else:
            winner = None
            outcome = "draw"

        return {
            "result_source": "actual",
            "winner": winner,
            "outcome": outcome,
            "home_score": home_score,
            "away_score": away_score,
            "home_penalties": home_penalties,
            "away_penalties": away_penalties,
            "display_label": "Actual result",
            "winner_consistent": declared in {None, winner},
        }

    prediction = prediction_row if prediction_row is not None else match_row
    home_probability = _number(_value(prediction, "home_win_probability", "team1_win_prob", "home_win"))
    draw_probability = _number(_value(prediction, "draw_probability", "draw_prob", "draw"))
    away_probability = _number(_value(prediction, "away_win_probability", "team2_win_prob", "away_win"))
    if home_team and away_team and home_probability is not None and away_probability is not None:
        if is_knockout or draw_probability is None:
            winner = home_team if home_probability >= away_probability else away_team
            outcome = "home_win" if winner == home_team else "away_win"
        else:
            probabilities = {
                "home_win": home_probability,
                "draw": draw_probability,
                "away_win": away_probability,
            }
            outcome = max(probabilities, key=probabilities.get)
            winner = home_team if outcome == "home_win" else away_team if outcome == "away_win" else None
        return {
            "result_source": "prediction",
            "winner": winner,
            "outcome": outcome,
            "home_score": home_score,
            "away_score": away_score,
            "home_penalties": home_penalties,
            "away_penalties": away_penalties,
            "display_label": "Projected winner",
            "winner_consistent": None,
        }

    return {
        "result_source": "unresolved",
        "winner": None,
        "outcome": None,
        "home_score": home_score,
        "away_score": away_score,
        "home_penalties": home_penalties,
        "away_penalties": away_penalties,
        "display_label": "Unresolved",
        "winner_consistent": None,
    }
