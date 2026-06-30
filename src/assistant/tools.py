from pathlib import Path
import pandas as pd

from src.predict import predict_match

BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"

def load_csv(filename: str) -> pd.DataFrame:
    path = PROCESSED_DIR /filename

    if not path.exists():
        raise FileNotFoundError(f"Could not find file: {path}")
    
    return pd.read_csv(path)

def get_team_elo(team_name: str) -> dict:
    elo_df = load_csv("elo_latest.csv")

    match = elo_df[
        elo_df["country"].str.lower() == team_name.lower()
    ]

    if match.empty:
        return {
            "found": False,
            "message": f"No Elo data found for {team_name}."
        }
    
    row = match.iloc[0]

    return {
        "found": True,
        "team": row["country"],
        "elo_rating": int(row["rating"]),
        "elo_rank": int(row["rank"]),
        "snapshot_date": row["snapshot_date"]
    }

def get_team_group(team_name: str) -> dict: 
    teams_df = load_csv("wc_2026_teams_cleaned.csv")

    match = teams_df[
        teams_df["team"].str.lower() == team_name.lower()
    ]

    if match.empty:
        return {
            "found": False,
            "message": f"No team data found for {team_name}"
        }
    
    row = match.iloc[0]

    return {
        "found": True,
        "team": row["team"],
        "group": row["group"],
        "confederation": row["confederation"],
        "fifa_rank": int(row["fifa_rank"])
    }

def get_team_fixtures(team_name: str) -> dict:
    fixtures_df = load_csv("wc_2026_fixtures_enriched.csv")

    matches = fixtures_df[
        (fixtures_df["team1"].str.lower() == team_name.lower())
        |
        (fixtures_df["team2"].str.lower() == team_name.lower())
    ]

    if matches.empty:
        return {
            "found": False,
            "message": f"No team data found for {team_name}"
        }

    fixtures = []

    for _, row in matches.iterrows():

        opponent = (
            row["team2"]
            if  row["team1"].lower() == team_name.lower()
            else row["team1"]
        )

        fixtures.append({
            "opponent": opponent,
            "stage": row["stage"],
            "date": row["date"]
        })
    
    return {
        "found": True,
        "team": team_name,
        "fixtures": fixtures
    }

def compare_teams(team1: str, team2: str) -> dict :
    team1_elo = get_team_elo(team1)
    team2_elo = get_team_elo(team2)

    if not team1_elo["found"]:
        return team1_elo
    
    if not team2_elo["found"]:
        return team2_elo
    
    elo_difference = team1_elo["elo_rating"] - team2_elo["elo_rating"]

    return {
        "found": True,
        "team1": {
            "name": team1_elo["team"],
            "elo_rating": team1_elo["elo_rating"],
            "elo_rank": team1_elo["elo_rank"],
        },
        "team2": {
            "name": team2_elo["team"],
            "elo_rating": team2_elo["elo_rating"],
            "elo_rank": team2_elo["elo_rank"],
        },
        "elo_difference": elo_difference,
        "stronger_team": team1_elo["team"] if elo_difference > 0 else team2_elo["team"]
    }

def get_match_prediction(home: str, away: str) -> dict:
    prediction = predict_match(home, away)

    return {
        "found": True,
        "home_team": home,
        "away_team": away,
        "home_win": prediction["home_win"],
        "draw": prediction["draw"],
        "away_win": prediction["away_win"],
        "favorite": prediction["favorite"],
    }


if __name__ == "__main__":
    print(get_team_elo("Belgium"))
    print(get_team_group("Belgium"))
    print(get_team_fixtures("Belgium"))
    print(compare_teams("Belgium", "Egypt"))