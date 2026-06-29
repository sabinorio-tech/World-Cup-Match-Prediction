"""
DS v2 test suite — covers the automated production H2H model pipeline.

Run with:
    .worldcupfootball/bin/pytest tests/test_ds_v2.py -v
"""

import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def features_v5():
    return pd.read_csv(ROOT / "data/processed/features.csv", parse_dates=["date"])


@pytest.fixture(scope="session")
def xgb_v2_artifact():
    with open(ROOT / "models/xgb_model.pkl", "rb") as f:
        return pickle.load(f)


@pytest.fixture(scope="session")
def poisson_v2_artifact():
    with open(ROOT / "models/poisson_model.pkl", "rb") as f:
        return pickle.load(f)


@pytest.fixture(scope="session")
def predict_v2_fn():
    sys.path.insert(0, str(ROOT))
    from src.predict import predict_match
    return predict_match


# ---------------------------------------------------------------------------
# 1. features.csv  (automated v2/H2H feature output)
# ---------------------------------------------------------------------------

class TestFeaturesV5:

    def test_shape(self, features_v5):
        assert features_v5.shape == (16_610, 19), (
            f"Expected (16610, 19), got {features_v5.shape}"
        )

    def test_h2h_columns_present(self, features_v5):
        assert "h2h_home_win_rate" in features_v5.columns
        assert "h2h_avg_goal_diff" in features_v5.columns

    def test_v1_columns_preserved(self, features_v5):
        v1_cols = {
            "date", "home_team", "away_team", "neutral", "tournament",
            "home_win_rate", "home_draw_rate",
            "home_avg_goals_scored", "home_avg_goals_conceded",
            "away_win_rate", "away_draw_rate",
            "away_avg_goals_scored", "away_avg_goals_conceded",
            "elo_diff", "home_elo", "away_elo", "result",
        }
        assert v1_cols.issubset(set(features_v5.columns))

    def test_no_missing_values(self, features_v5):
        missing = features_v5.isnull().sum()
        assert missing.sum() == 0, f"Missing values:\n{missing[missing > 0]}"

    def test_h2h_win_rate_range(self, features_v5):
        assert features_v5["h2h_home_win_rate"].between(0, 1).all()

    def test_h2h_win_rate_fallback_present(self, features_v5):
        # Majority of rows have no H2H history → fallback = 0.5
        fallback_pct = (features_v5["h2h_home_win_rate"] == 0.5).mean()
        assert fallback_pct > 0.4, (
            f"Expected >40% fallback rows, got {fallback_pct:.1%}"
        )

    def test_h2h_goal_diff_fallback_present(self, features_v5):
        fallback_pct = (features_v5["h2h_avg_goal_diff"] == 0.0).mean()
        assert fallback_pct > 0.4

    def test_h2h_goal_diff_symmetric(self, features_v5):
        # Non-fallback values: mean should be close to 0 (home advantage is
        # already captured by other features, not by H2H direction bias)
        real = features_v5[features_v5["h2h_avg_goal_diff"] != 0.0]["h2h_avg_goal_diff"]
        assert abs(real.mean()) < 1.0, (
            f"h2h_avg_goal_diff mean={real.mean():.3f} — suspiciously large bias"
        )

    def test_wc_2026_rows_present(self, features_v5):
        wc26 = features_v5[features_v5["date"] >= pd.Timestamp("2026-06-11")]
        assert len(wc26) >= 28


# ---------------------------------------------------------------------------
# 2. XGBoost v2 artifact  (output of 05_ensemble_v2.ipynb)
# ---------------------------------------------------------------------------

class TestXGBV2Artifact:

    def test_artifact_keys(self, xgb_v2_artifact):
        required = {
            "model", "le_tournament", "feature_cols",
            "result_map", "result_map_inv", "h2h_fallback", "model_version",
        }
        assert required.issubset(set(xgb_v2_artifact.keys()))

    def test_model_version(self, xgb_v2_artifact):
        assert xgb_v2_artifact["model_version"] == "v2_h2h"

    def test_feature_cols_count(self, xgb_v2_artifact):
        assert len(xgb_v2_artifact["feature_cols"]) == 13, (
            f"Expected 13 feature cols, got {len(xgb_v2_artifact['feature_cols'])}"
        )

    def test_h2h_features_in_cols(self, xgb_v2_artifact):
        cols = xgb_v2_artifact["feature_cols"]
        assert "h2h_home_win_rate" in cols
        assert "h2h_avg_goal_diff" in cols

    def test_h2h_fallback_values(self, xgb_v2_artifact):
        fb = xgb_v2_artifact["h2h_fallback"]
        assert fb["h2h_home_win_rate"] == 0.5
        assert fb["h2h_avg_goal_diff"] == 0.0

    def test_result_map(self, xgb_v2_artifact):
        assert xgb_v2_artifact["result_map"] == {"home_win": 0, "draw": 1, "away_win": 2}

    def test_result_map_inv(self, xgb_v2_artifact):
        assert xgb_v2_artifact["result_map_inv"] == {0: "home_win", 1: "draw", 2: "away_win"}

    def test_tournament_encoder_classes(self, xgb_v2_artifact):
        assert len(xgb_v2_artifact["le_tournament"].classes_) == 10

    def test_model_can_predict(self, xgb_v2_artifact, features_v5):
        art   = xgb_v2_artifact
        model = art["model"]
        le    = art["le_tournament"]
        cols  = art["feature_cols"]

        sample = features_v5.head(5)[cols].copy()
        sample["neutral"]    = sample["neutral"].astype(int)
        sample["tournament"] = le.transform(sample["tournament"])

        proba = model.predict_proba(sample)
        assert proba.shape == (5, 3)
        np.testing.assert_allclose(proba.sum(axis=1), 1.0, atol=1e-5)

    def test_probabilities_valid_range(self, xgb_v2_artifact, features_v5):
        art    = xgb_v2_artifact
        sample = features_v5.head(20)[art["feature_cols"]].copy()
        sample["neutral"]    = sample["neutral"].astype(int)
        sample["tournament"] = art["le_tournament"].transform(sample["tournament"])

        proba = art["model"].predict_proba(sample)
        assert (proba >= 0).all() and (proba <= 1).all()


# ---------------------------------------------------------------------------
# 3. Poisson v2 artifact  (output of 05_ensemble_v2.ipynb)
# ---------------------------------------------------------------------------

class TestPoissonV2Artifact:

    def test_artifact_keys(self, poisson_v2_artifact):
        required = {
            "model_home", "model_away",
            "scaler_home", "scaler_away",
            "feats_home", "feats_away",
            "result_map", "result_map_inv", "model_version",
        }
        assert required.issubset(set(poisson_v2_artifact.keys()))

    def test_model_version(self, poisson_v2_artifact):
        assert poisson_v2_artifact["model_version"] == "v2_h2h"

    def test_feats_home(self, poisson_v2_artifact):
        expected = [
            "home_avg_goals_scored", "away_avg_goals_conceded",
            "home_win_rate", "elo_diff", "neutral",
            "h2h_avg_goal_diff",
        ]
        assert poisson_v2_artifact["feats_home"] == expected

    def test_feats_away(self, poisson_v2_artifact):
        expected = [
            "away_avg_goals_scored", "home_avg_goals_conceded",
            "away_win_rate", "elo_diff", "neutral",
            "h2h_avg_goal_diff",
        ]
        assert poisson_v2_artifact["feats_away"] == expected

    def test_h2h_coef_sign_home(self, poisson_v2_artifact):
        # Positive h2h_avg_goal_diff → more home goals → positive coefficient
        art = poisson_v2_artifact
        idx = art["feats_home"].index("h2h_avg_goal_diff")
        coef = art["model_home"].coef_[idx]
        assert coef > 0, f"Expected positive h2h coef in home model, got {coef:.4f}"

    def test_h2h_coef_sign_away(self, poisson_v2_artifact):
        # Positive h2h_avg_goal_diff → fewer away goals → negative coefficient
        art = poisson_v2_artifact
        idx = art["feats_away"].index("h2h_avg_goal_diff")
        coef = art["model_away"].coef_[idx]
        assert coef < 0, f"Expected negative h2h coef in away model, got {coef:.4f}"

    def test_models_predict_positive_lambda(self, poisson_v2_artifact, features_v5):
        art    = poisson_v2_artifact
        sample = features_v5.head(10).copy()
        sample["neutral"] = sample["neutral"].astype(int)

        X_h = art["scaler_home"].transform(sample[art["feats_home"]])
        X_a = art["scaler_away"].transform(sample[art["feats_away"]])

        lam_h = art["model_home"].predict(X_h)
        lam_a = art["model_away"].predict(X_a)

        assert (lam_h > 0).all(), "λ_home must be positive"
        assert (lam_a > 0).all(), "λ_away must be positive"

    def test_lambda_has_variance(self, poisson_v2_artifact, features_v5):
        art    = poisson_v2_artifact
        sample = features_v5.sample(50, random_state=42).copy()
        sample["neutral"] = sample["neutral"].astype(int)

        X_h = art["scaler_home"].transform(sample[art["feats_home"]])
        lam_h = art["model_home"].predict(X_h)

        assert lam_h.std() > 0.05, "λ_home has no variance — model collapsed to mean"


# ---------------------------------------------------------------------------
# 4. predict_v2.predict_match()
# ---------------------------------------------------------------------------

class TestPredictV2:

    def test_return_keys(self, predict_v2_fn):
        result = predict_v2_fn("France", "Argentina")
        assert set(result.keys()) == {"home_win", "draw", "away_win", "favorite"}

    def test_probabilities_sum_to_one(self, predict_v2_fn):
        result = predict_v2_fn("Brazil", "Germany")
        total = result["home_win"] + result["draw"] + result["away_win"]
        assert abs(total - 1.0) < 0.01

    def test_probabilities_in_range(self, predict_v2_fn):
        result = predict_v2_fn("Spain", "England")
        for key in ("home_win", "draw", "away_win"):
            assert 0 <= result[key] <= 1, f"{key}={result[key]} out of [0, 1]"

    def test_favorite_is_argmax(self, predict_v2_fn):
        result = predict_v2_fn("Germany", "Brazil")
        best = max(("home_win", "draw", "away_win"), key=lambda k: result[k])
        assert result["favorite"] == best

    def test_favorite_is_valid(self, predict_v2_fn):
        result = predict_v2_fn("Argentina", "France")
        assert result["favorite"] in ("home_win", "draw", "away_win")

    def test_canonical_team_names(self, predict_v2_fn):
        for home, away in [("Türkiye", "USA"), ("USA", "Czechia"), ("Czechia", "Türkiye")]:
            result = predict_v2_fn(home, away)
            assert abs(result["home_win"] + result["draw"] + result["away_win"] - 1.0) < 0.01

    def test_strong_team_higher_probability(self, predict_v2_fn):
        result = predict_v2_fn("Germany", "Curaçao")
        assert result["home_win"] > result["away_win"]

    def test_neutral_flag_affects_prediction(self, predict_v2_fn):
        r_neutral     = predict_v2_fn("Brazil", "Argentina", neutral=True)
        r_non_neutral = predict_v2_fn("Brazil", "Argentina", neutral=False)
        assert r_neutral != r_non_neutral

    def test_h2h_fallback_for_unknown_pair(self, predict_v2_fn):
        # Teams with no shared history should still return valid probabilities
        result = predict_v2_fn("Iceland", "Curaçao")
        total = result["home_win"] + result["draw"] + result["away_win"]
        assert abs(total - 1.0) < 0.01

    def test_predictor_uses_v2_artifacts(self, xgb_v2_artifact, poisson_v2_artifact):
        assert xgb_v2_artifact["model_version"] == "v2_h2h"
        assert poisson_v2_artifact["model_version"] == "v2_h2h"

    @pytest.mark.parametrize("home,away", [
        ("France", "Senegal"),
        ("Norway", "Iraq"),
        ("Japan", "Sweden"),
        ("Colombia", "Portugal"),
        ("England", "Croatia"),
    ])
    def test_multiple_matches(self, predict_v2_fn, home, away):
        result = predict_v2_fn(home, away)
        total = result["home_win"] + result["draw"] + result["away_win"]
        assert abs(total - 1.0) < 0.01
