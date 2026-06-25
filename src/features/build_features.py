from __future__ import annotations

from bisect import bisect_left
from collections import defaultdict
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"

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

FEATURE_COLUMNS = [
    "date",
    "home_team",
    "away_team",
    "neutral",
    "tournament",
    "home_win_rate",
    "home_draw_rate",
    "home_avg_goals_scored",
    "home_avg_goals_conceded",
    "away_win_rate",
    "away_draw_rate",
    "away_avg_goals_scored",
    "away_avg_goals_conceded",
    "elo_diff",
    "home_elo",
    "away_elo",
    "result",
]


def _atomic_to_csv(df: pd.DataFrame, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    df.to_csv(temp_path, index=False)
    temp_path.replace(output_path)
    return output_path


def load_inputs(
    model_base_path: Path = PROCESSED_DIR / "model_training_base.csv",
    elo_history_path: Path = PROCESSED_DIR / "elo_history.csv",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    results = pd.read_csv(model_base_path, parse_dates=["date"])
    elo = pd.read_csv(elo_history_path, parse_dates=["snapshot_date"])
    return results, elo


def prepare_competitive_results(results: pd.DataFrame) -> pd.DataFrame:
    df = results[results["tournament"].isin(COMPETITIVE_TOURNAMENTS)].copy()
    df["result"] = df["outcome"]
    return df.sort_values("date").reset_index(drop=True)


def prepare_yearly_elo(elo: pd.DataFrame) -> pd.DataFrame:
    return (
        elo.sort_values("snapshot_date")
        .groupby(["country", "year"])
        .last()
        .reset_index()
    )


def get_recent_form(matches: pd.DataFrame, team: str, date: pd.Timestamp, n: int = 10) -> dict:
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


def _summarize_team_history(history: list[dict], n: int = 10) -> dict:
    recent = history[-n:]
    if not recent:
        return {
            "win_rate": 0.5,
            "draw_rate": 0.22,
            "avg_goals_scored": 1.5,
            "avg_goals_conceded": 1.5,
        }

    return {
        "win_rate": sum(item["win"] for item in recent) / len(recent),
        "draw_rate": sum(item["draw"] for item in recent) / len(recent),
        "avg_goals_scored": sum(item["goals_for"] for item in recent) / len(recent),
        "avg_goals_conceded": sum(item["goals_against"] for item in recent) / len(recent),
    }


def _append_match_to_history(histories: dict[str, list[dict]], row: pd.Series) -> None:
    home = row["home_team"]
    away = row["away_team"]
    home_score = row["home_score"]
    away_score = row["away_score"]
    result = row["result"]

    histories[home].append(
        {
            "win": result == "home_win",
            "draw": result == "draw",
            "goals_for": home_score,
            "goals_against": away_score,
        }
    )
    histories[away].append(
        {
            "win": result == "away_win",
            "draw": result == "draw",
            "goals_for": away_score,
            "goals_against": home_score,
        }
    )


def _build_elo_lookup(elo_yearly: pd.DataFrame) -> dict[str, tuple[list[int], list[float]]]:
    lookup = {}
    for country, group in elo_yearly.sort_values("year").groupby("country"):
        lookup[country] = (group["year"].astype(int).tolist(), group["rating"].astype(float).tolist())
    return lookup


def _get_elo_from_lookup(team: str, date: pd.Timestamp, lookup: dict[str, tuple[list[int], list[float]]]) -> float:
    if team not in lookup:
        return 1500.0
    years, ratings = lookup[team]
    idx = bisect_left(years, date.year) - 1
    if idx < 0:
        return 1500.0
    return ratings[idx]


def get_elo(team: str, date: pd.Timestamp, elo_yearly: pd.DataFrame) -> float:
    recent = elo_yearly[(elo_yearly["country"] == team) & (elo_yearly["year"] < date.year)]
    if recent.empty:
        return 1500.0
    return float(recent.sort_values("year").iloc[-1]["rating"])


def build_feature_frame(results: pd.DataFrame, elo: pd.DataFrame) -> pd.DataFrame:
    matches = prepare_competitive_results(results)
    elo_yearly = prepare_yearly_elo(elo)
    elo_lookup = _build_elo_lookup(elo_yearly)
    histories: dict[str, list[dict]] = defaultdict(list)

    rows = []
    for date, same_day_matches in matches.groupby("date", sort=True):
        for _, row in same_day_matches.iterrows():
            home = row["home_team"]
            away = row["away_team"]

            home_form = _summarize_team_history(histories[home], n=10)
            away_form = _summarize_team_history(histories[away], n=10)
            home_elo = _get_elo_from_lookup(home, date, elo_lookup)
            away_elo = _get_elo_from_lookup(away, date, elo_lookup)

            rows.append(
                {
                    "date": date,
                    "home_team": home,
                    "away_team": away,
                    "neutral": row["neutral"],
                    "tournament": row["tournament"],
                    "home_win_rate": home_form["win_rate"],
                    "home_draw_rate": home_form["draw_rate"],
                    "home_avg_goals_scored": home_form["avg_goals_scored"],
                    "home_avg_goals_conceded": home_form["avg_goals_conceded"],
                    "away_win_rate": away_form["win_rate"],
                    "away_draw_rate": away_form["draw_rate"],
                    "away_avg_goals_scored": away_form["avg_goals_scored"],
                    "away_avg_goals_conceded": away_form["avg_goals_conceded"],
                    "elo_diff": home_elo - away_elo,
                    "home_elo": home_elo,
                    "away_elo": away_elo,
                    "result": row["result"],
                }
            )

        for _, row in same_day_matches.iterrows():
            _append_match_to_history(histories, row)

    features = pd.DataFrame(rows, columns=FEATURE_COLUMNS)
    if features.empty:
        raise ValueError("Feature dataset is empty.")
    if features.isna().any().any():
        missing = features.isna().sum()
        raise ValueError(f"Feature dataset contains missing values: {missing[missing > 0].to_dict()}")
    return features


def build_features(
    model_base_path: Path = PROCESSED_DIR / "model_training_base.csv",
    elo_history_path: Path = PROCESSED_DIR / "elo_history.csv",
    output_path: Path = PROCESSED_DIR / "features.csv",
) -> Path:
    results, elo = load_inputs(model_base_path, elo_history_path)
    features = build_feature_frame(results, elo)
    path = _atomic_to_csv(features, output_path)
    print(f"✓ features.csv generated ({len(features):,} rows)")
    return path


if __name__ == "__main__":
    build_features()
