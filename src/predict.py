from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import poisson

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

# Load XGBoost model
with open(_ROOT / 'models' / 'xgb_model.pkl', 'rb') as f:
    _xgb = pickle.load(f)

_xgb_model        = _xgb['model']
_le_tournament    = _xgb['le_tournament']
_xgb_feature_cols = _xgb['feature_cols']
_result_map_inv   = _xgb['result_map_inv']

# Load Poisson model
with open(_ROOT / 'models' / 'poisson_model.pkl', 'rb') as f:
    _poi = pickle.load(f)

_poi_model_home  = _poi['model_home']
_poi_model_away  = _poi['model_away']
_poi_scaler_home = _poi['scaler_home']
_poi_scaler_away = _poi['scaler_away']
_poi_feats_home  = _poi['feats_home']
_poi_feats_away  = _poi['feats_away']

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
        return {
            'win_rate': 0.5, 'draw_rate': 0.22,
            'avg_goals_scored': 1.5, 'avg_goals_conceded': 1.5,
        }

    wins, draws, goals_for, goals_against = 0, 0, 0, 0
    for _, row in recent.iterrows():
        if row['result'] == 'draw':
            draws += 1
            goals_for     += row['home_score'] if row['home_team'] == team else row['away_score']
            goals_against += row['away_score'] if row['home_team'] == team else row['home_score']
        elif row['home_team'] == team:
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
        'win_rate':           wins  / len(recent),
        'draw_rate':          draws / len(recent),
        'avg_goals_scored':   goals_for  / len(recent),
        'avg_goals_conceded': goals_against / len(recent),
    }


def _get_elo(team: str) -> float:
    row = _elo[_elo['country'] == team]
    if len(row) == 0:
        return 1500.0
    return float(row.iloc[-1]['rating'])


def _poisson_proba(lam_home: float, lam_away: float, max_goals: int = 10) -> np.ndarray:
    p_home = p_draw = p_away = 0.0
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            p = poisson.pmf(i, lam_home) * poisson.pmf(j, lam_away)
            if   i > j:  p_home += p
            elif i == j: p_draw += p
            else:        p_away += p
    return np.array([p_home, p_draw, p_away])


def predict_match(
    home: str,
    away: str,
    neutral: bool = True,
    tournament: str = 'FIFA World Cup',
) -> dict:
    """Predict match outcome probabilities using XGBoost + Poisson ensemble.

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
    elo_diff  = home_elo - away_elo

    # XGBoost prediction
    xgb_row = {
        'home_win_rate':           home_form['win_rate'],
        'home_draw_rate':          home_form['draw_rate'],
        'home_avg_goals_scored':   home_form['avg_goals_scored'],
        'home_avg_goals_conceded': home_form['avg_goals_conceded'],
        'away_win_rate':           away_form['win_rate'],
        'away_draw_rate':          away_form['draw_rate'],
        'away_avg_goals_scored':   away_form['avg_goals_scored'],
        'away_avg_goals_conceded': away_form['avg_goals_conceded'],
        'elo_diff':                elo_diff,
        'neutral':                 int(neutral),
        'tournament':              _le_tournament.transform([tournament])[0],
    }
    X_xgb = pd.DataFrame([xgb_row])[_xgb_feature_cols]
    proba_xgb = _xgb_model.predict_proba(X_xgb)[0]

    # Poisson prediction
    poi_h = pd.DataFrame([{
        'home_avg_goals_scored':   home_form['avg_goals_scored'],
        'away_avg_goals_conceded': away_form['avg_goals_conceded'],
        'home_win_rate':           home_form['win_rate'],
        'elo_diff':                elo_diff,
        'neutral':                 int(neutral),
    }])[_poi_feats_home]
    poi_a = pd.DataFrame([{
        'away_avg_goals_scored':   away_form['avg_goals_scored'],
        'home_avg_goals_conceded': home_form['avg_goals_conceded'],
        'away_win_rate':           away_form['win_rate'],
        'elo_diff':                elo_diff,
        'neutral':                 int(neutral),
    }])[_poi_feats_away]

    lam_home  = float(_poi_model_home.predict(_poi_scaler_home.transform(poi_h))[0])
    lam_away  = float(_poi_model_away.predict(_poi_scaler_away.transform(poi_a))[0])
    proba_poi = _poisson_proba(lam_home, lam_away)

    # Ensemble: simple average
    proba = (proba_xgb + proba_poi) / 2

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
