import json
from pathlib import Path

import pandas as pd


INPUT_PATH = Path("data/raw/live/football_data_wc_matches.json")
OUTPUT_PATH = Path("data/processed/live_matches.csv")


def load_raw_matches(input_path: Path = INPUT_PATH) -> dict:
    with open(input_path, "r", encoding="utf-8") as file:
        return json.load(file)


def flatten_match(match: dict) -> dict:
    home_team = match.get("homeTeam", {})
    away_team = match.get("awayTeam", {})
    score = match.get("score", {})
    full_time = score.get("fullTime", {})
    half_time = score.get("halfTime", {})

    return {
        "match_id": match.get("id"),
        "utc_date": match.get("utcDate"),
        "status": match.get("status"),
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
        "home_score_full_time": full_time.get("home"),
        "away_score_full_time": full_time.get("away"),
        "home_score_half_time": half_time.get("home"),
        "away_score_half_time": half_time.get("away"),
    }


def transform_matches(raw_data: dict) -> pd.DataFrame:
    matches = raw_data.get("matches", [])
    rows = [flatten_match(match) for match in matches]

    df = pd.DataFrame(rows)

    df["utc_date"] = pd.to_datetime(df["utc_date"], errors="coerce")
    df["last_updated"] = pd.to_datetime(df["last_updated"], errors="coerce")

    return df


def save_matches(df: pd.DataFrame, output_path: Path = OUTPUT_PATH) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved: {output_path}")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")


if __name__ == "__main__":
    raw_data = load_raw_matches()
    live_matches = transform_matches(raw_data)
    save_matches(live_matches)

    print(live_matches.head())