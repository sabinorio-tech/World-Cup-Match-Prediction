from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "dashboard"))

from components import _bracket_path_order, _match_resolution
from time_utils import belgian_kickoff
from src.utils.match_results import get_match_source_of_truth


def test_live_dataset_has_all_104_fixtures():
    live = pd.read_csv(ROOT / "data" / "processed" / "live_matches.csv")
    assert len(live) == 104


def test_all_round_of_32_fixtures_are_resolved():
    knockout = pd.read_csv(ROOT / "data" / "processed" / "knockout_matches.csv")
    r32 = knockout[knockout["stage"].eq("Round of 32")]
    assert len(r32) == 16
    assert r32["is_resolved"].astype(bool).all()
    assert r32[["home_team", "away_team"]].notna().all().all()


def test_actual_result_overrides_higher_prediction():
    match = {
        "status": "FINISHED",
        "home_team": "Home",
        "away_team": "Away",
        "home_goals": 0,
        "away_goals": 1,
        "winner": "AWAY_TEAM",
    }
    prediction = {
        "home_win_probability": 0.80,
        "draw_probability": 0.10,
        "away_win_probability": 0.10,
    }
    truth = get_match_source_of_truth(match, prediction, is_knockout=True)
    assert truth["result_source"] == "actual"
    assert truth["winner"] == "Away"


def test_actual_knockout_winner_advances_in_bracket_logic():
    reach = pd.DataFrame([
        {"team": "Home", "round_of_16": 0.90},
        {"team": "Away", "round_of_16": 0.10},
    ])
    match = {
        "status": "FINISHED",
        "home_team": "Home",
        "away_team": "Away",
        "home_goals": 0,
        "away_goals": 1,
    }
    winner, _, source = _match_resolution(("Home", "Away"), reach, "round_of_16", match)
    assert source == "actual"
    assert winner == "Away"


def test_tied_knockout_without_penalties_is_unresolved():
    truth = get_match_source_of_truth(
        {
            "status": "FINISHED",
            "home_team": "Home",
            "away_team": "Away",
            "home_goals": 1,
            "away_goals": 1,
        },
        is_knockout=True,
    )
    assert truth["result_source"] == "unresolved"
    assert truth["winner"] is None


def test_null_future_match_is_safe():
    truth = get_match_source_of_truth(
        {"status": "TIMED", "home_team": None, "away_team": None},
        is_knockout=True,
    )
    assert truth["result_source"] == "unresolved"


def test_dashboard_output_schemas():
    knockout = pd.read_csv(ROOT / "data" / "processed" / "knockout_matches.csv")
    evaluation = pd.read_csv(ROOT / "data" / "processed" / "prediction_evaluation.csv")
    assert {
        "match_number", "match_id", "stage", "home_team", "away_team", "status",
        "home_goals", "away_goals", "winner", "result_source", "is_resolved",
    }.issubset(knockout.columns)
    assert {
        "match_id", "home_team", "away_team", "predicted_winner", "actual_winner",
        "prediction_correct", "model_confidence",
    }.issubset(evaluation.columns)


def test_knockout_display_order_follows_winner_paths():
    knockout = pd.read_csv(ROOT / "data" / "processed" / "knockout_matches.csv")
    r32_order, r16_order = _bracket_path_order(knockout)
    expected_r32 = [73, 75, 74, 77, 83, 84, 81, 82, 76, 78, 79, 80, 86, 88, 85, 87]
    expected_r16 = [89, 90, 93, 94, 91, 92, 95, 96]
    assert r32_order == expected_r32
    assert r16_order == expected_r16

    # A live provider may replace W73/W75 with confirmed group slots once
    # those teams advance. Visual ordering must still follow the official tree.
    progressed = knockout.copy()
    progressed.loc[progressed["match_number"].eq(89), ["home_slot", "away_slot"]] = ["2B", "1F"]
    assert _bracket_path_order(progressed) == (expected_r32, expected_r16)


def test_kickoff_is_displayed_in_belgian_summer_time():
    assert belgian_kickoff("2026-06-29", "20:30") == ("2026-06-29", "22:30", "CEST")
    assert belgian_kickoff("2026-06-29", "23:00") == ("2026-06-30", "01:00", "CEST")
