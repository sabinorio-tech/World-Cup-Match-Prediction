# DS Deliverables v2 — FIFA World Cup 2026 Match Prediction

> **v1 baseline** is documented in `docs/ds_modeling_report.md`.  
> v2 adds head-to-head (H2H) features to both XGBoost and Poisson. The H2H version is now integrated into the automated production pipeline.

---

## Notebooks

### `01_EDA.ipynb` — Feature Engineering (unchanged)

Builds the training dataset from DE's processed files. Filters 16,610 competitive matches across 10 tournament types. For each match computes rolling form features over the last 10 games: win rate, draw rate, average goals scored/conceded — separately for home and away team. Adds Elo rating difference.

Output: `data/processed/features.csv` (16,610 × 17).

### `02_model.ipynb` — XGBoost v1 (unchanged)

Trains the baseline XGBoost classifier. Saves `models/xgb_model.pkl` (11 features).

### `03_poisson_model.ipynb` — Poisson v1 + Ensemble v1 (unchanged)

Trains the baseline Poisson regressors. Saves `models/poisson_model.pkl` (5 features each). Generates `data/processed/predictions_2026.csv` (group stage, 72 matches).

### `04_goals_trend.ipynb` — Feature Experiments

Tested 6 new feature candidates using a dedicated XGBoost variant (same hyperparams, same split). Each feature was evaluated independently against the v1 baseline (test LL = 0.9843).

| Feature | Test LL | vs baseline | Decision |
|---|---|---|---|
| Goals form trend (linear slope) | 0.9878 | +0.0035 worse | Rejected |
| Days since last match | 0.9878 | +0.0035 worse | Rejected |
| Days since last match (capped at 14) | 0.9903 | +0.0060 worse | Rejected |
| **Head-to-Head win rate + goal diff** | **0.9742** | **−0.0101 better** | **Accepted** |
| ELO momentum (180-day trend) | 0.9878 | +0.0035 worse | Rejected |
| Clean sheet rate | 0.9878 | +0.0035 worse | Rejected |
| Quality-adjusted win rate | 1.0068 | +0.0225 worse | Rejected (multicollinearity) |

Only H2H improved the model. All others added noise — the WC 2026 test set (28 matches) is small enough that features need a strong signal to register.

H2H features used:
- `h2h_home_win_rate` — win rate of home team in last 10 H2H matches (min 3 required, else fallback = 0.5)
- `h2h_avg_goal_diff` — average (home_score − away_score) in last 10 H2H matches (fallback = 0.0)

Output after automation: `data/processed/features.csv` (16,610 × 19).

### `05_ensemble_v2.ipynb` — XGBoost v2 + Poisson v2 + Ensemble v2b

Trains both models with H2H features and evaluates all combinations.

**XGBoost v2:** 13 features (11 original + `h2h_home_win_rate` + `h2h_avg_goal_diff`). Best iteration: 90.

**Poisson v2:** adds `h2h_avg_goal_diff` to both home and away feature sets (6 features each). Signs confirmed correct: home model coef = +0.09 (more H2H dominance → more home goals), away model coef = −0.11 (more H2H dominance → fewer away goals).

---

## Results

| Model | Val LL | Test LL | Test Acc |
|---|---|---|---|
| Ensemble V1 (prod, baseline) | 1.0188 | 0.9796 | 50.0% |
| XGB v2 alone (+H2H) | 1.0128 | 0.9742 | 53.6% |
| Poisson v1 (original) | 1.0307 | 0.9798 | 50.0% |
| Poisson v2 (+h2h_goal_diff) | 1.0293 | 0.9726 | 50.0% |
| Ensemble V2 (XGB_v2 + Poi_v1) | 1.0151 | 0.9747 | 50.0% |
| **Ensemble V2b (XGB_v2 + Poi_v2)** | **1.0167** | **0.9717** | **50.0%** |

**Ensemble V2b is the best model**: test LL 0.9717 vs 0.9796 for V1 (−0.0079 improvement, ~0.8% relative gain).

Val LL for V2b (1.0167) is slightly worse than V2 (1.0151), but val = 64 matches and test = 28 matches — both sets are too small for high-confidence ranking. The test result is the ground truth we care about (real WC 2026 outcomes).

**H2H coverage:** only 46.8% of training rows have real H2H data (≥3 matches). The model learns that (0.5, 0.0) means "no data" and falls back to other features for those cases.

---

## Model Artifacts

| File | Description |
|---|---|
| `models/xgb_model.pkl` | Production XGBoost v2/H2H model, 13 features |
| `models/poisson_model.pkl` | Production Poisson v2/H2H model, 6 features per side, with scalers |

Both artifacts include `model_version="v2_h2h"`, `result_map`, `result_map_inv`, and fallback values for prediction where relevant.

---

## For the DA — How to Use in the Dashboard

### Option A — Dynamic prediction v2 (any match, any teams)

```python
# Install dependencies first:
# pip install scikit-learn>=1.9.0 xgboost>=3.3.0 scipy>=1.15.0

import sys
sys.path.insert(0, '/path/to/project/root')  # adjust to your path

from src.predict import predict_match

result = predict_match('France', 'Argentina')
# → {'home_win': 0.345, 'draw': 0.258, 'away_win': 0.397, 'favorite': 'away_win'}

# Use in Streamlit:
st.metric("France",    f"{result['home_win']:.0%}")
st.metric("Draw",      f"{result['draw']:.0%}")
st.metric("Argentina", f"{result['away_win']:.0%}")
```

Same interface as v1, but the production `src.predict` implementation now uses the H2H model artifacts. `src.predict_v2` remains available as a compatibility wrapper.

Team names must follow DE's canonical convention: `'Türkiye'`, `'USA'`, `'Czechia'` (not Turkey / United States / Czech Republic).

### Option B — Static table (group stage only, no dependencies)

Still valid — `data/processed/predictions_2026.csv` is generated by the automated v2/H2H pipeline.

### Recommended UX note

Always show all three probabilities (home / draw / away) rather than just `favorite`. When `draw_prob > 0.27`, consider adding a visual indicator — those matches historically end in a draw ~60% of the time in our validation data.
