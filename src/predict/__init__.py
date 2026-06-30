from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import poisson

ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT / "models"
PROCESSED_DIR = ROOT / "data" / "processed"

COMPETITIVE_TOURNAMENTS = [
    "FIFA World Cup",
    "FIFA World Cup qualification",
    "UEFA Euro",
    "UEFA Euro qualification",
    "Copa América",
    "African Cup of Nations",
    "AFC Asian Cup",
    "Gold Cup",
    "UEFA Nations League",
    "CONCACAF Nations League",
]

_MODEL_CACHE: dict[str, object] = {}
_MODEL_MTIMES: dict[Path, float] = {}
_DATA_CACHE: dict[str, pd.DataFrame] = {}
_DATA_MTIMES: dict[Path, float] = {}
H2H_FALLBACK = {
    "h2h_home_win_rate": 0.5,
    "h2h_avg_goal_diff": 0.0,
}


def _load_pickle(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing model artifact: {path}")
    with open(path, "rb") as file:
        return pickle.load(file)


def _load_models() -> tuple[dict, dict]:
    xgb_path = MODELS_DIR / "xgb_model.pkl"
    poisson_path = MODELS_DIR / "poisson_model.pkl"
    mtimes = {path: path.stat().st_mtime for path in [xgb_path, poisson_path]}
    if (
        "xgb" not in _MODEL_CACHE
        or "poisson" not in _MODEL_CACHE
        or any(_MODEL_MTIMES.get(path) != mtime for path, mtime in mtimes.items())
    ):
        _MODEL_CACHE["xgb"] = _load_pickle(xgb_path)
        _MODEL_CACHE["poisson"] = _load_pickle(poisson_path)
        _MODEL_MTIMES.clear()
        _MODEL_MTIMES.update(mtimes)
    return _MODEL_CACHE["xgb"], _MODEL_CACHE["poisson"]  # type: ignore[return-value]


def _load_csv_cached(name: str, path: Path, parse_dates: list[str] | None = None) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing prediction input: {path}")
    mtime = path.stat().st_mtime
    if name not in _DATA_CACHE or _DATA_MTIMES.get(path) != mtime:
        _DATA_CACHE[name] = pd.read_csv(path, parse_dates=parse_dates)
        _DATA_MTIMES[path] = mtime
    return _DATA_CACHE[name]


def _prediction_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    results = _load_csv_cached("results", PROCESSED_DIR / "results_historical.csv", parse_dates=["date"]).copy()
    results["result"] = results["outcome"]
    matches = results[results["tournament"].isin(COMPETITIVE_TOURNAMENTS)].copy()
    matches = matches.sort_values("date").reset_index(drop=True)
    elo = _load_csv_cached("elo", PROCESSED_DIR / "elo_latest.csv")
    return matches, elo


def _get_recent_form(team: str, date: pd.Timestamp, n: int = 10) -> dict:
    matches, _ = _prediction_inputs()
    mask = (
        ((matches["home_team"] == team) | (matches["away_team"] == team))
        & (matches["date"] < date)
    )
    recent = matches[mask].tail(n)
    if recent.empty:
        return {
            "win_rate": 0.5,
            "draw_rate": 0.22,
            "avg_goals_scored": 1.5,
            "avg_goals_conceded": 1.5,
        }

    wins = draws = goals_for = goals_against = 0
    for _, row in recent.iterrows():
        is_home = row["home_team"] == team
        team_goals = row["home_score"] if is_home else row["away_score"]
        opp_goals = row["away_score"] if is_home else row["home_score"]
        goals_for += team_goals
        goals_against += opp_goals

        if row["result"] == "draw":
            draws += 1
        elif (is_home and row["result"] == "home_win") or (not is_home and row["result"] == "away_win"):
            wins += 1

    return {
        "win_rate": wins / len(recent),
        "draw_rate": draws / len(recent),
        "avg_goals_scored": goals_for / len(recent),
        "avg_goals_conceded": goals_against / len(recent),
    }


def _get_elo(team: str) -> float:
    _, elo = _prediction_inputs()
    row = elo[elo["country"] == team]
    if row.empty:
        return 1500.0
    return float(row.iloc[-1]["rating"])


def _get_h2h(
    home_team: str,
    away_team: str,
    date: pd.Timestamp,
    n: int = 10,
    min_matches: int = 3,
    fallback: dict | None = None,
) -> dict:
    matches, _ = _prediction_inputs()
    mask = (
        (
            ((matches["home_team"] == home_team) & (matches["away_team"] == away_team))
            | ((matches["home_team"] == away_team) & (matches["away_team"] == home_team))
        )
        & (matches["date"] < date)
    )
    recent = matches[mask].tail(n)
    if len(recent) < min_matches:
        return (fallback or H2H_FALLBACK).copy()

    home_wins = 0
    goal_diffs = []
    for _, row in recent.iterrows():
        if row["home_team"] == home_team:
            home_wins += int(row["result"] == "home_win")
            goal_diffs.append(row["home_score"] - row["away_score"])
        else:
            home_wins += int(row["result"] == "away_win")
            goal_diffs.append(row["away_score"] - row["home_score"])

    return {
        "h2h_home_win_rate": home_wins / len(recent),
        "h2h_avg_goal_diff": float(np.mean(goal_diffs)),
    }


def _poisson_proba(lam_home: float, lam_away: float, max_goals: int = 10) -> np.ndarray:
    p_home = p_draw = p_away = 0.0
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            p = poisson.pmf(i, lam_home) * poisson.pmf(j, lam_away)
            if i > j:
                p_home += p
            elif i == j:
                p_draw += p
            else:
                p_away += p
    probabilities = np.array([p_home, p_draw, p_away])
    total = probabilities.sum()
    if total == 0:
        return np.array([0.0, 1.0, 0.0])
    return probabilities / total


def predict_match(
    home: str,
    away: str,
    neutral: bool = True,
    tournament: str = "FIFA World Cup",
) -> dict:
    """Predict match outcome probabilities using the XGBoost + Poisson ensemble."""
    xgb, poi = _load_models()
    date = pd.Timestamp.now()

    home_form = _get_recent_form(home, date)
    away_form = _get_recent_form(away, date)
    home_elo = _get_elo(home)
    away_elo = _get_elo(away)
    elo_diff = home_elo - away_elo
    h2h = _get_h2h(home, away, date, fallback=xgb.get("h2h_fallback", H2H_FALLBACK))

    xgb_row = {
        "home_win_rate": home_form["win_rate"],
        "home_draw_rate": home_form["draw_rate"],
        "home_avg_goals_scored": home_form["avg_goals_scored"],
        "home_avg_goals_conceded": home_form["avg_goals_conceded"],
        "away_win_rate": away_form["win_rate"],
        "away_draw_rate": away_form["draw_rate"],
        "away_avg_goals_scored": away_form["avg_goals_scored"],
        "away_avg_goals_conceded": away_form["avg_goals_conceded"],
        "elo_diff": elo_diff,
        "neutral": int(neutral),
        "tournament": xgb["le_tournament"].transform([tournament])[0],
        "h2h_home_win_rate": h2h["h2h_home_win_rate"],
        "h2h_avg_goal_diff": h2h["h2h_avg_goal_diff"],
    }
    x_xgb = pd.DataFrame([xgb_row])[xgb["feature_cols"]]
    proba_xgb = xgb["model"].predict_proba(x_xgb)[0]

    poi_h = pd.DataFrame(
        [
            {
                "home_avg_goals_scored": home_form["avg_goals_scored"],
                "away_avg_goals_conceded": away_form["avg_goals_conceded"],
                "home_win_rate": home_form["win_rate"],
                "elo_diff": elo_diff,
                "neutral": int(neutral),
                "h2h_avg_goal_diff": h2h["h2h_avg_goal_diff"],
            }
        ]
    )[poi["feats_home"]]
    poi_a = pd.DataFrame(
        [
            {
                "away_avg_goals_scored": away_form["avg_goals_scored"],
                "home_avg_goals_conceded": home_form["avg_goals_conceded"],
                "away_win_rate": away_form["win_rate"],
                "elo_diff": elo_diff,
                "neutral": int(neutral),
                "h2h_avg_goal_diff": h2h["h2h_avg_goal_diff"],
            }
        ]
    )[poi["feats_away"]]

    lam_home = float(poi["model_home"].predict(poi["scaler_home"].transform(poi_h))[0])
    lam_away = float(poi["model_away"].predict(poi["scaler_away"].transform(poi_a))[0])
    proba_poi = _poisson_proba(lam_home, lam_away)

    proba = (proba_xgb + proba_poi) / 2
    result = {
        "home_win": round(float(proba[0]), 3),
        "draw": round(float(proba[1]), 3),
        "away_win": round(float(proba[2]), 3),
    }
    result["favorite"] = max(("home_win", "draw", "away_win"), key=lambda key: result[key])
    return result
