# DS Deliverables — FIFA World Cup 2026 Match Prediction

## Notebooks

### `01_EDA.ipynb` — Feature Engineering

Builds the training dataset from DE's processed files. Filters 16,610 competitive matches across 10 tournament types (FIFA World Cup, UEFA Euro, Copa América, etc.). For each match computes rolling form features over the last 10 games: win rate, draw rate, average goals scored/conceded — separately for home and away team. Adds Elo rating difference as a measure of overall team quality.

Output: `data/processed/features.csv` (16,610 × 17).

### `02_model.ipynb` — XGBoost Classifier

Time-based train/val/test split: train on all matches before WC 2022, validate on WC 2022 (64 matches), test on WC 2026 played matches (28 matches). Trains an XGBoost multi-class classifier (`home_win` / `draw` / `away_win`). Early stopping at iteration 87. Saves model artifact to `models/xgb_model.pkl`. Final cell generates `data/processed/predictions_2026.csv` for all 72 group stage matches using the ensemble (see below).

### `03_poisson_model.ipynb` — Poisson Regression + Ensemble

Trains two separate Poisson regressors: one predicting home goals, one predicting away goals. Match probabilities are derived mathematically: P(draw) = Σ P(score k:k) for k = 0, 1, 2, …. Ensemble averages XGBoost and Poisson probabilities. Saves artifact to `models/poisson_model.pkl`.

---

## Results

| Metric | XGBoost | Poisson | Ensemble |
|---|---|---|---|
| Val log loss (WC 2022, 64 matches) | 1.0189 | 1.0307 | **1.0188** |
| Test log loss (WC 2026, 28 matches) | 0.9843 | 0.9798 | **0.9796** |
| Val accuracy | 46.9% | 51.6% | 50.0% |
| Test accuracy | 53.6% | 50.0% | 50.0% |
| Baseline (always majority class) | 43.8% | 43.8% | 43.8% |

The ensemble wins on log loss across both sets — meaning the **probabilities are better calibrated** than either model alone. Draws are never the argmax prediction (known limitation of all three-class football models), but P(draw) is informative: among the top-8 matches by P(draw) in the validation set, 5 out of 8 actually ended in a draw.

---

## For the DA — How to Use in the Dashboard

### Option A — Dynamic prediction (any match, any teams)

```python
# Install dependencies first:
# pip install scikit-learn>=1.9.0 xgboost>=3.3.0 scipy>=1.15.0

import sys
sys.path.insert(0, '/path/to/project/root')  # adjust to your path

from src.predict import predict_match

result = predict_match('France', 'Argentina')
# → {'home_win': 0.364, 'draw': 0.253, 'away_win': 0.383, 'favorite': 'away_win'}

# Use in Streamlit:
st.metric("France",    f"{result['home_win']:.0%}")
st.metric("Draw",      f"{result['draw']:.0%}")
st.metric("Argentina", f"{result['away_win']:.0%}")
```

Team names must follow DE's canonical convention: `'Türkiye'`, `'USA'`, `'Czechia'` (not Turkey / United States / Czech Republic).

### Option B — Static table (group stage only, no dependencies)

```python
import pandas as pd

df = pd.read_csv('data/processed/predictions_2026.csv')
# Columns: group, date, team1, team2, team1_win_prob, draw_prob, team2_win_prob, favorite

group_a = df[df['group'] == 'A']
st.dataframe(group_a)
```

### Recommended UX note

Always show all three probabilities (home / draw / away) rather than just `favorite`. When `draw_prob > 0.27`, consider adding a visual indicator — those matches historically end in a draw ~60% of the time in our validation data.
