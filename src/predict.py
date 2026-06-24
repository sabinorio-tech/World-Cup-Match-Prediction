from __future__ import annotations

import pickle
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent

_COMPETITIVE = [
    'FIFA World Cup',
    'FIFA World Cup qualification',
    'UEFA Euro',
    'UEFA Euro qualification',
    'Copa América',
    'African Cup of Nations',
    'AFC Asian Cup',
    'Gold Cup',
    'UEFA Nations League',
    'CONCACAF Nations League',
]

with open(_ROOT / 'models' / 'xgb_model.pkl', 'rb') as f:
    _artifact = pickle.load(f)

_model          = _artifact['model']
_le_tournament  = _artifact['le_tournament']
_feature_cols   = _artifact['feature_cols']
_result_map_inv = _artifact['result_map_inv']

_results = pd.read_csv(
    _ROOT / 'data' / 'processed' / 'results_historical.csv',
    parse_dates=['date'],
)
_results['result'] = _results['outcome']
_df = _results[_results['tournament'].isin(_COMPETITIVE)].copy()
_df = _df.sort_values('date').reset_index(drop=True)

_elo = pd.read_csv(_ROOT / 'data' / 'processed' / 'elo_latest.csv')


def _get_recent_form(team: str, date: pd.Timestamp, n: int = 10) -> dict:
    mask = (
        ((_df['home_team'] == team) | (_df['away_team'] == team)) &
        (_df['date'] < date)
    )
    recent = _df[mask].tail(n)
    if len(recent) == 0:
        return {'win_rate': 0.5, 'avg_goals_scored': 1.5, 'avg_goals_conceded': 1.5}

    wins, goals_for, goals_against = 0, 0, 0
    for _, row in recent.iterrows():
        if row['home_team'] == team:
            goals_for     += row['home_score']
            goals_against += row['away_score']
            if row['result'] == 'home_win':
                wins += 1
        else:
            goals_for     += row['away_score']
            goals_against += row['home_score']
            if row['result'] == 'away_win':
                wins += 1

    return {
        'win_rate':           wins / len(recent),
        'avg_goals_scored':   goals_for / len(recent),
        'avg_goals_conceded': goals_against / len(recent),
    }


def _get_elo(team: str) -> float:
    row = _elo[_elo['country'] == team]
    if len(row) == 0:
        return 1500.0
    return float(row.iloc[-1]['rating'])


def predict_match(
    home: str,
    away: str,
    neutral: bool = True,
    tournament: str = 'FIFA World Cup',
) -> dict:
    """Predict match outcome probabilities.

    Args:
        home:       Home team name (DE canonical: 'Türkiye', 'USA', 'Czechia')
        away:       Away team name
        neutral:    True for all WC 2026 matches
        tournament: One of the 10 competitive tournament names

    Returns:
        dict with home_win, draw, away_win (float probabilities) and favorite (str)
    """
    date = pd.Timestamp.now()

    home_form = _get_recent_form(home, date)
    away_form = _get_recent_form(away, date)
    home_elo  = _get_elo(home)
    away_elo  = _get_elo(away)

    row = {
        'home_win_rate':           home_form['win_rate'],
        'home_avg_goals_scored':   home_form['avg_goals_scored'],
        'home_avg_goals_conceded': home_form['avg_goals_conceded'],
        'away_win_rate':           away_form['win_rate'],
        'away_avg_goals_scored':   away_form['avg_goals_scored'],
        'away_avg_goals_conceded': away_form['avg_goals_conceded'],
        'elo_diff':                home_elo - away_elo,
        'neutral':                 int(neutral),
        'tournament':              _le_tournament.transform([tournament])[0],
    }

    X = pd.DataFrame([row])[_feature_cols]
    proba = _model.predict_proba(X)[0]

    result = {
        'home_win': round(float(proba[0]), 3),
        'draw':     round(float(proba[1]), 3),
        'away_win': round(float(proba[2]), 3),
    }
    result['favorite'] = max(
        ('home_win', 'draw', 'away_win'),
        key=lambda k: result[k],
    )

    return result
