from __future__ import annotations

import pickle
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, log_loss
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"

FEATURE_COLS = [
    "home_win_rate",
    "home_draw_rate",
    "home_avg_goals_scored",
    "home_avg_goals_conceded",
    "away_win_rate",
    "away_draw_rate",
    "away_avg_goals_scored",
    "away_avg_goals_conceded",
    "elo_diff",
    "neutral",
    "tournament",
]
TARGET_COL = "result"
RESULT_MAP = {"home_win": 0, "draw": 1, "away_win": 2}
RESULT_MAP_INV = {0: "home_win", 1: "draw", 2: "away_win"}
WC_2022_START = pd.Timestamp("2022-11-20")
WC_2026_START = pd.Timestamp("2026-06-11")


def _atomic_pickle(artifact: dict, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    with open(temp_path, "wb") as file:
        pickle.dump(artifact, file)
    temp_path.replace(output_path)
    return output_path


def load_features(features_path: Path = PROCESSED_DIR / "features.csv") -> pd.DataFrame:
    features = pd.read_csv(features_path, parse_dates=["date"])
    missing = set(FEATURE_COLS + [TARGET_COL, "date"]) - set(features.columns)
    if missing:
        raise ValueError(f"features.csv missing columns: {sorted(missing)}")
    return features


def split_features(features: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train = features[features["date"] < WC_2022_START].copy()
    val = features[
        (features["date"] >= WC_2022_START)
        & (features["date"] < WC_2026_START)
        & (features["tournament"] == "FIFA World Cup")
    ].copy()
    test = features[features["date"] >= WC_2026_START].copy()
    if train.empty or val.empty:
        raise ValueError(f"Invalid split sizes: train={len(train)}, val={len(val)}, test={len(test)}")
    return train, val, test


def train_xgb_model(features: pd.DataFrame) -> dict:
    train, val, test = split_features(features)

    le_tournament = LabelEncoder()
    le_tournament.fit(features["tournament"])

    def encode_x(df: pd.DataFrame) -> pd.DataFrame:
        x = df[FEATURE_COLS].copy()
        x["neutral"] = x["neutral"].astype(int)
        x["tournament"] = le_tournament.transform(x["tournament"])
        return x

    def encode_y(df: pd.DataFrame) -> pd.Series:
        return df[TARGET_COL].map(RESULT_MAP)

    x_train = encode_x(train)
    y_train = encode_y(train)
    x_val = encode_x(val)
    y_val = encode_y(val)

    model = XGBClassifier(
        objective="multi:softprob",
        num_class=3,
        n_estimators=500,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="mlogloss",
        early_stopping_rounds=30,
        random_state=42,
        verbosity=0,
    )
    model.fit(x_train, y_train, eval_set=[(x_val, y_val)], verbose=False)

    val_proba = model.predict_proba(x_val)
    metrics = {
        "train_rows": len(train),
        "validation_rows": len(val),
        "test_rows": len(test),
        "validation_log_loss": float(log_loss(y_val, val_proba, labels=[0, 1, 2])),
        "validation_accuracy": float(accuracy_score(y_val, val_proba.argmax(axis=1))),
        "best_iteration": int(getattr(model, "best_iteration", model.n_estimators)),
    }

    return {
        "model": model,
        "le_tournament": le_tournament,
        "feature_cols": FEATURE_COLS,
        "result_map": RESULT_MAP,
        "result_map_inv": RESULT_MAP_INV,
        "metrics": metrics,
    }


def train_xgb(
    features_path: Path = PROCESSED_DIR / "features.csv",
    output_path: Path = MODELS_DIR / "xgb_model.pkl",
) -> Path:
    features = load_features(features_path)
    artifact = train_xgb_model(features)
    path = _atomic_pickle(artifact, output_path)
    metrics = artifact["metrics"]
    print(
        "✓ xgb_model.pkl saved "
        f"(val_accuracy={metrics['validation_accuracy']:.3f}, "
        f"val_log_loss={metrics['validation_log_loss']:.3f})"
    )
    return path


if __name__ == "__main__":
    train_xgb()
