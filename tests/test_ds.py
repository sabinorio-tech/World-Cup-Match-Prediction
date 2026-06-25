"""
DS test suite — covers outputs of 01_EDA.ipynb, 02_model.ipynb, 03_poisson_model.ipynb.

Run with:
    .worldcupfootball/bin/pytest tests/test_ds.py -v
"""

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def features():
    return pd.read_csv(ROOT / "data/processed/features.csv", parse_dates=["date"])


@pytest.fixture(scope="session")
def predictions():
    return pd.read_csv(ROOT / "data/processed/predictions_2026.csv")


@pytest.fixture(scope="session")
def xgb_artifact():
    with open(ROOT / "models/xgb_model.pkl", "rb") as f:
        return pickle.load(f)


@pytest.fixture(scope="session")
def poisson_artifact():
    with open(ROOT / "models/poisson_model.pkl", "rb") as f:
        return pickle.load(f)


@pytest.fixture(scope="session")
def predict_fn():
    import sys
    sys.path.insert(0, str(ROOT))
    from src.predict import predict_match
    return predict_match


# ---------------------------------------------------------------------------
# 1. features.csv  (output of 01_EDA.ipynb)
# ---------------------------------------------------------------------------

class TestFeatures:

    def test_shape(self, features):
        assert features.shape == (16_610, 17), (
            f"Expected (16610, 17), got {features.shape}"
        )

    def test_required_columns(self, features):
        expected = {
            "date", "home_team", "away_team", "neutral", "tournament",
            "home_win_rate", "home_draw_rate",
            "home_avg_goals_scored", "home_avg_goals_conceded",
            "away_win_rate", "away_draw_rate",
            "away_avg_goals_scored", "away_avg_goals_conceded",
            "elo_diff", "home_elo", "away_elo", "result",
        }
        assert expected.issubset(set(features.columns))

    def test_no_missing_values(self, features):
        missing = features.isnull().sum()
        assert missing.sum() == 0, f"Missing values found:\n{missing[missing > 0]}"

    def test_result_values(self, features):
        valid = {"home_win", "draw", "away_win"}
        actual = set(features["result"].unique())
        assert actual == valid, f"Unexpected result values: {actual - valid}"

    def test_win_rate_range(self, features):
        for col in ["home_win_rate", "away_win_rate"]:
            assert features[col].between(0, 1).all(), f"{col} out of [0, 1]"

    def test_draw_rate_range(self, features):
        for col in ["home_draw_rate", "away_draw_rate"]:
            assert features[col].between(0, 1).all(), f"{col} out of [0, 1]"

    def test_goals_non_negative(self, features):
        for col in [
            "home_avg_goals_scored", "home_avg_goals_conceded",
            "away_avg_goals_scored", "away_avg_goals_conceded",
        ]:
            assert (features[col] >= 0).all(), f"{col} has negative values"

    def test_elo_diff_range(self, features):
        assert features["elo_diff"].between(-1500, 1500).all(), "elo_diff out of expected range"

    def test_date_range(self, features):
        assert features["date"].min() >= pd.Timestamp("1900-01-01")
        assert features["date"].max() <= pd.Timestamp("2026-12-31")

    def test_neutral_is_bool(self, features):
        assert features["neutral"].dtype == bool

    def test_tournament_values(self, features):
        expected_tournaments = {
            "FIFA World Cup", "FIFA World Cup qualification",
            "UEFA Euro", "UEFA Euro qualification",
            "Copa América", "African Cup of Nations",
            "AFC Asian Cup", "Gold Cup",
            "UEFA Nations League", "CONCACAF Nations League",
        }
        actual = set(features["tournament"].unique())
        assert actual == expected_tournaments, f"Unexpected tournaments: {actual ^ expected_tournaments}"

    def test_result_distribution(self, features):
        dist = features["result"].value_counts(normalize=True)
        assert dist["home_win"] > 0.40, "home_win rate suspiciously low"
        assert dist["draw"] > 0.15, "draw rate suspiciously low"
        assert dist["away_win"] > 0.20, "away_win rate suspiciously low"

    def test_wc_2026_matches_present(self, features):
        wc_2026 = features[features["date"] >= pd.Timestamp("2026-06-11")]
        assert len(wc_2026) >= 28, "Expected at least 28 WC 2026 test matches"

    def test_canonical_team_names(self, features):
        all_teams = set(features["home_team"]) | set(features["away_team"])
        banned = {"Turkey", "United States", "Czech Republic"}
        found = banned & all_teams
        assert not found, f"Non-canonical team names found: {found}"


# ---------------------------------------------------------------------------
# 2. XGBoost artifact  (output of 02_model.ipynb)
# ---------------------------------------------------------------------------

class TestXGBModel:

    def test_artifact_keys(self, xgb_artifact):
        required = {"model", "le_tournament", "feature_cols", "result_map", "result_map_inv"}
        assert required.issubset(set(xgb_artifact.keys()))

    def test_feature_cols_count(self, xgb_artifact):
        assert len(xgb_artifact["feature_cols"]) == 11, (
            f"Expected 11 feature cols, got {len(xgb_artifact['feature_cols'])}"
        )

    def test_result_map_values(self, xgb_artifact):
        assert xgb_artifact["result_map"] == {"home_win": 0, "draw": 1, "away_win": 2}

    def test_result_map_inv(self, xgb_artifact):
        assert xgb_artifact["result_map_inv"] == {0: "home_win", 1: "draw", 2: "away_win"}

    def test_tournament_encoder_classes(self, xgb_artifact):
        assert len(xgb_artifact["le_tournament"].classes_) == 10

    def test_model_can_predict(self, xgb_artifact, features):
        model = xgb_artifact["model"]
        le    = xgb_artifact["le_tournament"]
        cols  = xgb_artifact["feature_cols"]

        sample = features.head(5)[cols].copy()
        sample["neutral"]    = sample["neutral"].astype(int)
        sample["tournament"] = le.transform(sample["tournament"])

        proba = model.predict_proba(sample)
        assert proba.shape == (5, 3)
        np.testing.assert_allclose(proba.sum(axis=1), 1.0, atol=1e-5)

    def test_probabilities_valid_range(self, xgb_artifact, features):
        model = xgb_artifact["model"]
        le    = xgb_artifact["le_tournament"]
        cols  = xgb_artifact["feature_cols"]

        sample = features.head(20)[cols].copy()
        sample["neutral"]    = sample["neutral"].astype(int)
        sample["tournament"] = le.transform(sample["tournament"])

        proba = model.predict_proba(sample)
        assert (proba >= 0).all() and (proba <= 1).all()


# ---------------------------------------------------------------------------
# 3. Poisson artifact  (output of 03_poisson_model.ipynb)
# ---------------------------------------------------------------------------

class TestPoissonModel:

    def test_artifact_keys(self, poisson_artifact):
        required = {
            "model_home", "model_away",
            "scaler_home", "scaler_away",
            "feats_home", "feats_away",
            "result_map", "result_map_inv",
        }
        assert required.issubset(set(poisson_artifact.keys()))

    def test_feats_home(self, poisson_artifact):
        expected = [
            "home_avg_goals_scored", "away_avg_goals_conceded",
            "home_win_rate", "elo_diff", "neutral",
        ]
        assert poisson_artifact["feats_home"] == expected

    def test_feats_away(self, poisson_artifact):
        expected = [
            "away_avg_goals_scored", "home_avg_goals_conceded",
            "away_win_rate", "elo_diff", "neutral",
        ]
        assert poisson_artifact["feats_away"] == expected

    def test_models_predict_positive_lambda(self, poisson_artifact, features):
        art = poisson_artifact
        sample = features.head(10).copy()
        sample["neutral"] = sample["neutral"].astype(int)

        X_h = art["scaler_home"].transform(sample[art["feats_home"]])
        X_a = art["scaler_away"].transform(sample[art["feats_away"]])

        lam_h = art["model_home"].predict(X_h)
        lam_a = art["model_away"].predict(X_a)

        assert (lam_h > 0).all(), "λ_home must be positive"
        assert (lam_a > 0).all(), "λ_away must be positive"

    def test_lambda_has_variance(self, poisson_artifact, features):
        art = poisson_artifact
        sample = features.sample(50, random_state=42).copy()
        sample["neutral"] = sample["neutral"].astype(int)

        X_h = art["scaler_home"].transform(sample[art["feats_home"]])
        lam_h = art["model_home"].predict(X_h)

        assert lam_h.std() > 0.05, "λ_home has no variance — model collapsed to mean"


# ---------------------------------------------------------------------------
# 4. predict_match()  (src/predict.py — ensemble interface)
# ---------------------------------------------------------------------------

class TestPredictMatch:

    def test_return_keys(self, predict_fn):
        result = predict_fn("France", "Argentina")
        assert set(result.keys()) == {"home_win", "draw", "away_win", "favorite"}

    def test_probabilities_sum_to_one(self, predict_fn):
        result = predict_fn("Brazil", "Germany")
        total = result["home_win"] + result["draw"] + result["away_win"]
        assert abs(total - 1.0) < 0.01, f"Probabilities sum to {total}"

    def test_probabilities_in_range(self, predict_fn):
        result = predict_fn("Spain", "England")
        for key in ("home_win", "draw", "away_win"):
            assert 0 <= result[key] <= 1, f"{key}={result[key]} out of [0,1]"

    def test_favorite_is_valid(self, predict_fn):
        result = predict_fn("Argentina", "France")
        assert result["favorite"] in ("home_win", "draw", "away_win")

    def test_favorite_is_argmax(self, predict_fn):
        result = predict_fn("Germany", "Brazil")
        best = max(("home_win", "draw", "away_win"), key=lambda k: result[k])
        assert result["favorite"] == best

    def test_canonical_team_names(self, predict_fn):
        for home, away in [("Türkiye", "USA"), ("USA", "Czechia"), ("Czechia", "Türkiye")]:
            result = predict_fn(home, away)
            assert result["home_win"] + result["draw"] + result["away_win"] == pytest.approx(1.0, abs=0.01)

    def test_strong_team_higher_probability(self, predict_fn):
        result = predict_fn("Germany", "Curaçao")
        assert result["home_win"] > result["away_win"], (
            "Germany should have higher P(home_win) than Curaçao P(away_win)"
        )

    def test_neutral_flag(self, predict_fn):
        r_neutral  = predict_fn("Brazil", "Argentina", neutral=True)
        r_non_neutral = predict_fn("Brazil", "Argentina", neutral=False)
        assert r_neutral != r_non_neutral, "neutral flag should affect predictions"

    @pytest.mark.parametrize("home,away", [
        ("France", "Senegal"),
        ("Norway", "Iraq"),
        ("Japan", "Sweden"),
        ("Colombia", "Portugal"),
        ("England", "Croatia"),
    ])
    def test_multiple_matches(self, predict_fn, home, away):
        result = predict_fn(home, away)
        total = result["home_win"] + result["draw"] + result["away_win"]
        assert abs(total - 1.0) < 0.01


# ---------------------------------------------------------------------------
# 5. predictions_2026.csv  (output of last cell in 02_model.ipynb)
# ---------------------------------------------------------------------------

class TestPredictions2026:

    def test_total_matches(self, predictions):
        assert len(predictions) == 72, f"Expected 72 matches, got {len(predictions)}"

    def test_required_columns(self, predictions):
        required = {"group", "date", "team1", "team2",
                    "team1_win_prob", "draw_prob", "team2_win_prob", "favorite"}
        assert required.issubset(set(predictions.columns))

    def test_all_groups_present(self, predictions):
        expected_groups = set("ABCDEFGHIJKL")
        actual_groups   = set(predictions["group"].unique())
        assert actual_groups == expected_groups, (
            f"Missing groups: {expected_groups - actual_groups}"
        )

    def test_each_group_has_6_matches(self, predictions):
        counts = predictions.groupby("group").size()
        wrong  = counts[counts != 6]
        assert wrong.empty, f"Groups with wrong match count:\n{wrong}"

    def test_no_duplicate_pairs(self, predictions):
        pairs = predictions.apply(
            lambda r: tuple(sorted([r["team1"], r["team2"]])), axis=1
        )
        assert pairs.duplicated().sum() == 0, "Duplicate match pairs found"

    def test_probabilities_sum_to_one(self, predictions):
        totals = (
            predictions["team1_win_prob"] +
            predictions["draw_prob"] +
            predictions["team2_win_prob"]
        )
        assert (totals - 1.0).abs().max() < 0.01, "Probabilities don't sum to 1"

    def test_probabilities_in_range(self, predictions):
        for col in ("team1_win_prob", "draw_prob", "team2_win_prob"):
            assert predictions[col].between(0, 1).all(), f"{col} out of [0,1]"

    def test_favorite_is_valid(self, predictions):
        valid = set(predictions["team1"]) | set(predictions["team2"]) | {"draw"}
        assert predictions["favorite"].isin(valid).all()

    def test_draw_prob_mean_realistic(self, predictions):
        mean_draw = predictions["draw_prob"].mean()
        assert 0.15 < mean_draw < 0.35, (
            f"Mean draw probability {mean_draw:.3f} outside expected range [0.15, 0.35]"
        )

    def test_no_null_values(self, predictions):
        assert predictions.isnull().sum().sum() == 0
