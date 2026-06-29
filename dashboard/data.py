"""
Data access layer for the World Cup 2026 dashboard — REAL DATA VERSION.

Backed by:
  - realdata.py   -> actual results, model predictions, team metadata, Elo
  - simulate.py   -> Monte Carlo group-qualification + knockout simulation

Same function names as the original demo version (get_teams, get_matches,
get_group_standings, get_round_reach, get_team) so the Streamlit pages in
app.py barely had to change.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

import realdata as rd
import simulate as sim
from cache_utils import ttl_cache
from src.utils.match_results import get_match_source_of_truth

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
PLAYER_RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "player_data"


def _freshness_label(timestamp) -> str:
    if timestamp is None or pd.isna(timestamp):
        return "Unavailable"
    value = pd.Timestamp(timestamp)
    if value.tzinfo is None:
        value = value.tz_localize("UTC")
    else:
        value = value.tz_convert("UTC")
    return value.strftime("%d %B %Y, %H:%M UTC")


def get_data_freshness() -> dict[str, str]:
    live_path = PROCESSED_DIR / "live_matches.csv"
    live_timestamp = None
    if live_path.exists():
        try:
            updates = pd.read_csv(live_path, usecols=["last_updated"])["last_updated"]
            live_timestamp = pd.to_datetime(updates, errors="coerce", utc=True).max()
        except (ValueError, KeyError):
            live_timestamp = pd.Timestamp(live_path.stat().st_mtime, unit="s", tz="UTC")

    player_files = list(PLAYER_RAW_DIR.glob("*.html"))
    player_timestamp = (
        pd.Timestamp(max(path.stat().st_mtime for path in player_files), unit="s", tz="UTC")
        if player_files else None
    )
    return {
        "live": _freshness_label(live_timestamp),
        "players": _freshness_label(player_timestamp),
    }


@dataclass(frozen=True)
class Team:
    name: str
    iso2: str
    confederation: str
    elo: int
    group: str
    flag: str
    fifa_rank: int
    coach: str
    recent_form: list        # last 5 ACTUAL pre-tournament results, e.g. ['W','W','D','L','W']
    goals_for_l5: int
    goals_against_l5: int
    campaign_played: int     # matches played so far IN this World Cup
    campaign_w: int
    campaign_d: int
    campaign_l: int
    campaign_gf: int
    campaign_ga: int
    campaign_results: list


@ttl_cache()
def get_teams() -> list:
    df = rd.load_teams()
    form = rd.load_recent_form()
    campaign = rd.load_campaign_stats()
    teams = []
    for _, row in df.iterrows():
        f = form.get(row["team"], {"results": [], "goals_for": 0, "goals_against": 0})
        c = campaign.get(row["team"], {"played": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "results": []})
        teams.append(Team(
            name=row["team"], iso2=str(row.get("iso2") or ""), confederation=row["confederation"],
            elo=int(row["elo"]), group=row["group"], flag=row["flag"],
            fifa_rank=int(row["fifa_rank"]) if pd.notna(row["fifa_rank"]) else 99,
            coach=row.get("coach", ""),
            recent_form=f["results"], goals_for_l5=f["goals_for"], goals_against_l5=f["goals_against"],
            campaign_played=c["played"], campaign_w=c["w"], campaign_d=c["d"], campaign_l=c["l"],
            campaign_gf=c["gf"], campaign_ga=c["ga"], campaign_results=c["results"],
        ))
    return teams


def get_team(name: str):
    return next((t for t in get_teams() if t.name == name), None)


@ttl_cache()
def get_matches() -> pd.DataFrame:
    """Group-stage fixtures, renamed to the home/away schema the UI expects.
    `played=True` rows carry real scores; `played=False` rows carry the
    XGBoost model's win/draw/loss probabilities."""
    df = rd.load_group_matches().rename(columns={
        "team1": "home_team_predicted", "team2": "away_team_predicted",
        "team1_win_prob": "home_win_probability", "draw_prob": "draw_probability",
        "team2_win_prob": "away_win_probability",
        "team1_goals": "home_goals", "team2_goals": "away_goals",
    })
    df["home_team"] = df["home_team_predicted"]
    df["away_team"] = df["away_team_predicted"]
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    return df


@ttl_cache()
def get_group_standings() -> pd.DataFrame:
    """Actual current standings (from real results) + simulated qualification odds."""
    campaign = rd.load_campaign_stats()
    teams_df = rd.load_teams()
    qual = sim.run_simulation().set_index("team")["group_qualification_probability"]

    rows = []
    for _, t in teams_df.iterrows():
        c = campaign.get(t["team"], {"played": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "points": 0})
        rows.append({
            "group": t["group"], "team": t["team"], "flag": t["flag"],
            "played": c["played"], "points": c["points"],
            "goals_for": c["gf"], "goals_against": c["ga"], "goal_difference": c["gf"] - c["ga"],
            "group_qualification_probability": qual.get(t["team"], 0.0),
        })
    df = pd.DataFrame(rows)
    df = df.sort_values(["group", "points", "goal_difference"], ascending=[True, False, False])
    return df.reset_index(drop=True)


@ttl_cache()
def get_round_reach() -> pd.DataFrame:
    """Monte Carlo round-reach + tournament-win probabilities, with flags attached."""
    df = sim.run_simulation().copy()
    flags = rd.load_teams().set_index("team")["flag"].to_dict()
    groups = rd.load_teams().set_index("team")["group"].to_dict()
    df["flag"] = df["team"].map(flags)
    df["group"] = df["team"].map(groups)
    knockout = rd.load_knockout_matches()
    if not knockout.empty:
        r32 = knockout[knockout["stage"].eq("Round of 32")]
        confirmed_r32 = set(r32["home_team"].dropna()) | set(r32["away_team"].dropna())
        if len(confirmed_r32) == 32:
            df["round_of_32"] = df["team"].isin(confirmed_r32).astype(float)

        next_round_columns = {
            "Round of 32": "round_of_16",
            "Round of 16": "quarterfinal",
            "Quarter-final": "semifinal",
            "Semi-final": "final",
            "Final": "tournament_win_probability",
        }
        ordered_columns = [
            "round_of_16", "quarterfinal", "semifinal", "final", "tournament_win_probability"
        ]
        for _, match in knockout.iterrows():
            truth = get_match_source_of_truth(match, is_knockout=True)
            if truth["result_source"] != "actual" or not truth["winner"]:
                continue
            next_column = next_round_columns.get(str(match.get("stage")))
            if not next_column:
                continue
            participants = {match.get("home_team"), match.get("away_team")}
            loser = next((team for team in participants if pd.notna(team) and team != truth["winner"]), None)
            start = ordered_columns.index(next_column)
            df.loc[df["team"].eq(truth["winner"]), next_column] = 1.0
            if loser:
                df.loc[df["team"].eq(loser), ordered_columns[start:]] = 0.0
    return df.sort_values("tournament_win_probability", ascending=False).reset_index(drop=True)


@ttl_cache()
def get_knockout_matches() -> pd.DataFrame:
    return rd.load_knockout_matches()


def get_tournament_winner_probs(top_n: int = 10) -> pd.DataFrame:
    return get_round_reach().head(top_n)


@ttl_cache()
def get_player_profiles() -> pd.DataFrame:
    path = PROCESSED_DIR / "player_profiles.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@ttl_cache()
def get_player_stats() -> pd.DataFrame:
    path = PROCESSED_DIR / "player_stats.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def db_available() -> bool:
    return True
