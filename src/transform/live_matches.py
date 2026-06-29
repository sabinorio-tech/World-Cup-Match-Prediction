import json
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "live" / "football_data_wc_matches.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "live_matches.csv"

OUTPUT_COLUMNS = [
    "match_id",
    "utc_date",
    "match_date",
    "kickoff_time_utc",
    "status",
    "is_finished",
    "is_scheduled",
    "has_score",
    "matchday",
    "stage",
    "group",
    "last_updated",
    "home_team_id",
    "home_team",
    "home_team_short",
    "home_team_tla",
    "home_team_crest",
    "away_team_id",
    "away_team",
    "away_team_short",
    "away_team_tla",
    "away_team_crest",
    "winner",
    "duration",
    "home_score",
    "away_score",
    "home_score_full_time",
    "away_score_full_time",
    "home_score_half_time",
    "away_score_half_time",
    "home_score_penalties",
    "away_score_penalties",
    "score_display",
]


def load_raw_matches(input_path: Path = INPUT_PATH) -> dict[str, Any]:
    with open(input_path, "r", encoding="utf-8") as file:
        return json.load(file)


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _score_display(home_score: Any, away_score: Any) -> str:
    if pd.isna(home_score) or pd.isna(away_score):
        return "TBD"
    return f"{int(home_score)}-{int(away_score)}"


def flatten_match(match: dict[str, Any]) -> dict[str, Any]:
    home_team = _as_dict(match.get("homeTeam"))
    away_team = _as_dict(match.get("awayTeam"))
    score = _as_dict(match.get("score"))
    full_time = _as_dict(score.get("fullTime"))
    half_time = _as_dict(score.get("halfTime"))
    penalties = _as_dict(score.get("penalties"))

    home_full_time = full_time.get("home")
    away_full_time = full_time.get("away")
    has_score = home_full_time is not None and away_full_time is not None
    status = match.get("status")

    return {
        "match_id": match.get("id"),
        "utc_date": match.get("utcDate"),
        "match_date": None,
        "kickoff_time_utc": None,
        "status": match.get("status"),
        "is_finished": status == "FINISHED",
        "is_scheduled": status in {"SCHEDULED", "TIMED"},
        "has_score": has_score,
        "matchday": match.get("matchday"),
        "stage": match.get("stage"),
        "group": match.get("group"),
        "last_updated": match.get("lastUpdated"),

        "home_team_id": home_team.get("id"),
        "home_team": home_team.get("name"),
        "home_team_short": home_team.get("shortName"),
        "home_team_tla": home_team.get("tla"),
        "home_team_crest": home_team.get("crest"),

        "away_team_id": away_team.get("id"),
        "away_team": away_team.get("name"),
        "away_team_short": away_team.get("shortName"),
        "away_team_tla": away_team.get("tla"),
        "away_team_crest": away_team.get("crest"),

        "winner": score.get("winner"),
        "duration": score.get("duration"),
        "home_score": home_full_time,
        "away_score": away_full_time,
        "home_score_full_time": home_full_time,
        "away_score_full_time": away_full_time,
        "home_score_half_time": half_time.get("home"),
        "away_score_half_time": half_time.get("away"),
        "home_score_penalties": penalties.get("home"),
        "away_score_penalties": penalties.get("away"),
        "score_display": _score_display(home_full_time, away_full_time),
    }


def transform_matches(raw_data: dict[str, Any]) -> pd.DataFrame:
    matches = raw_data.get("matches", [])
    rows = [flatten_match(match) for match in matches]

    df = pd.DataFrame(rows, columns=OUTPUT_COLUMNS)

    df["utc_date"] = pd.to_datetime(df["utc_date"], errors="coerce")
    df["last_updated"] = pd.to_datetime(df["last_updated"], errors="coerce")
    df["match_date"] = df["utc_date"].dt.date.astype("string")
    df["kickoff_time_utc"] = df["utc_date"].dt.strftime("%H:%M")

    return df


def save_matches(df: pd.DataFrame, output_path: Path = OUTPUT_PATH) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved: {output_path}")
    print(f"Rows: {len(df)}")
    return output_path


if __name__ == "__main__":
    raw_data = load_raw_matches()
    live_matches = transform_matches(raw_data)
    save_matches(live_matches)
