"""
Expected-goals (xG) estimator — NOT the XGBoost classifier.

The production model (predictions_2026.csv) only outputs win/draw/loss
probabilities; it has no goals output. Rather than invent a scoreline,
this module derives a transparent expected-goals estimate from each
team's own real recent scoring/conceding rates — conceptually the same
inputs the DS team's Poisson notebook (03_poisson_model.ipynb) used
(avg goals scored/conceded, Elo difference), just without a fitted
PoissonRegressor artifact to load. Always label this in the UI as an
estimate, separate from the model's actual probabilities.
"""

from __future__ import annotations

import realdata as rd

LEAGUE_AVG_GOALS = 1.4  # rough long-run international-football mean


def _team_scoring_rate(team_name: str) -> tuple[float, float]:
    """Blend pre-tournament form (last 5) with in-tournament results so far.
    Returns (avg_goals_scored, avg_goals_conceded) per match."""
    form = rd.load_recent_form().get(team_name, {"results": [], "goals_for": 0, "goals_against": 0})
    campaign = rd.load_campaign_stats().get(team_name, {"played": 0, "gf": 0, "ga": 0})

    n_form = len(form["results"])
    n_camp = campaign["played"]

    total_played = n_form + n_camp
    if total_played == 0:
        return LEAGUE_AVG_GOALS, LEAGUE_AVG_GOALS

    gf = form["goals_for"] + campaign["gf"]
    ga = form["goals_against"] + campaign["ga"]
    return gf / total_played, ga / total_played


def estimate_match_xg(team1: str, team2: str, elo_diff: float) -> tuple[float, float]:
    """Returns (xg_team1, xg_team2). Simple, transparent, clearly an estimate."""
    t1_attack, t1_defense = _team_scoring_rate(team1)
    t2_attack, t2_defense = _team_scoring_rate(team2)

    lam1 = (t1_attack + t2_defense) / 2
    lam2 = (t2_attack + t1_defense) / 2

    # Small Elo-based tilt, capped so it can't swing wildly on big mismatches.
    tilt = max(-0.35, min(0.35, elo_diff / 1800))
    lam1 = max(0.3, lam1 + tilt)
    lam2 = max(0.3, lam2 - tilt)

    return round(lam1, 2), round(lam2, 2)
