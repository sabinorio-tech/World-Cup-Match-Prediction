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
from functools import lru_cache

import pandas as pd

import realdata as rd
import simulate as sim


@dataclass(frozen=True)
class Team:
    name: str
    iso2: str
    confederation: str
    elo: int
    group: str
    flag: str
    flag_url: str
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


@lru_cache(maxsize=1)
def get_teams() -> list:
    df = rd.load_teams()
    form = rd.load_recent_form()
    campaign = rd.load_campaign_stats()
    teams = []
    for _, row in df.iterrows():
        f = form.get(row["team"], {"results": [], "goals_for": 0, "goals_against": 0})
        c = campaign.get(row["team"], {"played": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0})
        teams.append(Team(
            name=row["team"], iso2=str(row.get("iso2") or ""), confederation=row["confederation"],
            elo=int(row["elo"]), group=row["group"], flag=row["flag"], flag_url=row["flag_url"],
            fifa_rank=int(row["fifa_rank"]) if pd.notna(row["fifa_rank"]) else 99,
            coach=row.get("coach", ""),
            recent_form=f["results"], goals_for_l5=f["goals_for"], goals_against_l5=f["goals_against"],
            campaign_played=c["played"], campaign_w=c["w"], campaign_d=c["d"], campaign_l=c["l"],
            campaign_gf=c["gf"], campaign_ga=c["ga"],
        ))
    return teams


def get_team(name: str):
    return next((t for t in get_teams() if t.name == name), None)


@lru_cache(maxsize=1)
def get_matches() -> pd.DataFrame:
    """Group-stage fixtures, renamed to the home/away schema the UI expects.
    `played=True` rows carry real scores; `played=False` rows carry the
    XGBoost model's win/draw/loss probabilities."""
    df = rd.load_group_matches().rename(columns={
        "team1": "home_team", "team2": "away_team",
        "team1_win_prob": "home_win_probability", "draw_prob": "draw_probability",
        "team2_win_prob": "away_win_probability",
        "team1_goals": "home_goals", "team2_goals": "away_goals",
    })
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    return df


@lru_cache(maxsize=1)
def get_group_standings() -> pd.DataFrame:
    """Actual current standings (from real results) + simulated qualification odds."""
    campaign = rd.load_campaign_stats()
    teams_df = rd.load_teams()
    qual = sim.run_simulation().set_index("team")["group_qualification_probability"]

    rows = []
    for _, t in teams_df.iterrows():
        c = campaign.get(t["team"], {"played": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "points": 0})
        rows.append({
            "group": t["group"], "team": t["team"], "flag": t["flag"], "flag_url": t["flag_url"],
            "played": c["played"], "points": c["points"],
            "goals_for": c["gf"], "goals_against": c["ga"], "goal_difference": c["gf"] - c["ga"],
            "group_qualification_probability": qual.get(t["team"], 0.0),
        })
    df = pd.DataFrame(rows)
    df = df.sort_values(["group", "points", "goal_difference"], ascending=[True, False, False])
    return df.reset_index(drop=True)


@lru_cache(maxsize=1)
def get_round_reach() -> pd.DataFrame:
    """Monte Carlo round-reach + tournament-win probabilities, with flags attached."""
    df = sim.run_simulation().copy()
    flags = rd.load_teams().set_index("team")["flag"].to_dict()
    flag_urls = rd.load_teams().set_index("team")["flag_url"].to_dict()
    groups = rd.load_teams().set_index("team")["group"].to_dict()
    df["flag"] = df["team"].map(flags)
    df["flag_url"] = df["team"].map(flag_urls)
    df["group"] = df["team"].map(groups)
    return df.sort_values("tournament_win_probability", ascending=False).reset_index(drop=True)


def get_tournament_winner_probs(top_n: int = 10) -> pd.DataFrame:
    return get_round_reach().head(top_n)


def db_available() -> bool:
    return True
