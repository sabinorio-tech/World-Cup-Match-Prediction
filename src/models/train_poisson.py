from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import poisson
from sklearn.linear_model import PoissonRegressor
from sklearn.metrics import accuracy_score, log_loss
from sklearn.preprocessing import StandardScaler

BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"

RESULT_MAP = {"home_win": 0, "draw": 1, "away_win": 2}
RESULT_MAP_INV = {0: "home_win", 1: "draw", 2: "away_win"}
WC_2022_START = pd.Timestamp("2022-11-20")
WC_2026_START = pd.Timestamp("2026-06-11")

FEATS_HOME = [
    "home_avg_goals_scored",
    "away_avg_goals_conceded",
    "home_win_rate",
    "elo_diff",
    "neutral",
]
FEATS_AWAY = [
    "away_avg_goals_scored",
    "home_avg_goals_conceded",
    "away_win_rate",
    "elo_diff",
    "neutral",
]


def _atomic_pickle(artifact: dict, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    with open(temp_path, "wb") as file:
        pickle.dump(artifact, file)
    temp_path.replace(output_path)
    return output_path


def _poisson_proba(lam_home: np.ndarray, lam_away: np.ndarray, max_goals: int = 10) -> np.ndarray:
    rows = []
    for home_lambda, away_lambda in zip(lam_home, lam_away):
        p_home = p_draw = p_away = 0.0
        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                p = poisson.pmf(i, home_lambda) * poisson.pmf(j, away_lambda)
                if i > j:
                    p_home += p
                elif i == j:
                    p_draw += p
                else:
                    p_away += p
        rows.append([p_home, p_draw, p_away])
    probabilities = np.array(rows)
    totals = probabilities.sum(axis=1, keepdims=True)
    return np.divide(probabilities, totals, out=np.zeros_like(probabilities), where=totals != 0)


def load_training_data(
    features_path: Path = PROCESSED_DIR / "features.csv",
    results_path: Path = PROCESSED_DIR / "results_historical.csv",
) -> pd.DataFrame:
    features = pd.read_csv(features_path, parse_dates=["date"])
    results = pd.read_csv(results_path, parse_dates=["date"])
    data = features.merge(
        results[["date", "home_team", "away_team", "home_score", "away_score"]],
        on=["date", "home_team", "away_team"],
        how="left",
    )
    if data[["home_score", "away_score"]].isna().any().any():
        raise ValueError("Poisson training data contains missing scores after merge.")
    return data


def split_data(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train = data[data["date"] < WC_2022_START].copy()
    val = data[
        (data["date"] >= WC_2022_START)
        & (data["date"] < WC_2026_START)
        & (data["tournament"] == "FIFA World Cup")
    ].copy()
    test = data[data["date"] >= WC_2026_START].copy()
    if train.empty or val.empty:
        raise ValueError(f"Invalid split sizes: train={len(train)}, val={len(val)}, test={len(test)}")
    return train, val, test


def train_poisson_model(data: pd.DataFrame) -> dict:
    train, val, test = split_data(data)

    scaler_home = StandardScaler()
    scaler_away = StandardScaler()
    x_train_h = scaler_home.fit_transform(train[FEATS_HOME])
    x_train_a = scaler_away.fit_transform(train[FEATS_AWAY])
    x_val_h = scaler_home.transform(val[FEATS_HOME])
    x_val_a = scaler_away.transform(val[FEATS_AWAY])

    model_home = PoissonRegressor(alpha=0.01, max_iter=1000)
    model_away = PoissonRegressor(alpha=0.01, max_iter=1000)
    model_home.fit(x_train_h, train["home_score"])
    model_away.fit(x_train_a, train["away_score"])

    lam_home_val = model_home.predict(x_val_h)
    lam_away_val = model_away.predict(x_val_a)
    val_proba = _poisson_proba(lam_home_val, lam_away_val)
    y_val = val["result"].map(RESULT_MAP)

    metrics = {
        "train_rows": len(train),
        "validation_rows": len(val),
        "test_rows": len(test),
        "validation_log_loss": float(log_loss(y_val, val_proba, labels=[0, 1, 2])),
        "validation_accuracy": float(accuracy_score(y_val, val_proba.argmax(axis=1))),
        "validation_mean_lambda_home": float(lam_home_val.mean()),
        "validation_mean_lambda_away": float(lam_away_val.mean()),
    }

    return {
        "model_home": model_home,
        "model_away": model_away,
        "scaler_home": scaler_home,
        "scaler_away": scaler_away,
        "feats_home": FEATS_HOME,
        "feats_away": FEATS_AWAY,
        "result_map": RESULT_MAP,
        "result_map_inv": RESULT_MAP_INV,
        "metrics": metrics,
    }


def train_poisson(
    features_path: Path = PROCESSED_DIR / "features.csv",
    results_path: Path = PROCESSED_DIR / "results_historical.csv",
    output_path: Path = MODELS_DIR / "poisson_model.pkl",
) -> Path:
    data = load_training_data(features_path, results_path)
    artifact = train_poisson_model(data)
    path = _atomic_pickle(artifact, output_path)
    metrics = artifact["metrics"]
    print(
        "✓ poisson_model.pkl saved "
        f"(val_accuracy={metrics['validation_accuracy']:.3f}, "
        f"val_log_loss={metrics['validation_log_loss']:.3f})"
    )
    return path


if __name__ == "__main__":
    train_poisson()
