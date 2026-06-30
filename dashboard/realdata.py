"""
Loads the real Phase 1-3 deliverables (DS model predictions + DE team/fixture
data) and assembles them into the shapes the dashboard pages consume.

Inputs (data/raw/, produced by the DE/DS notebooks):
    wc_2026_teams_cleaned.csv       team metadata: group, confederation, fifa_rank, coach
    elo_latest.csv                  current Elo rating + career W/D/L/goals per team
    predictions_2026.csv            XGBoost model output: team1/draw/team2 win probabilities
                                     for all 72 group-stage fixtures
    live_matches.csv                football-data.org match status, kickoff time, and scores
    results_historical.csv          full historical results, incl. WC2026 matches already played
    wc_2026_fixtures_enriched.csv   fixtures + venue/city/Elo context, PLUS the 32 official
                                     knockout placeholder rows (R32 -> Final bracket skeleton)
    knockout_matches.csv            resolved knockout slots where group standings are final

This module does the joining/cleaning once (cached) and exposes plain
DataFrames/dicts that simulate.py and data.py build on.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from cache_utils import ttl_cache

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"

_ISO2_OVERRIDES = {
    "South Korea": "KR", "USA": "US", "Ivory Coast": "CI", "Türkiye": "TR",
    "Bosnia and Herzegovina": "BA", "Cape Verde": "CV", "DR Congo": "CD",
    "New Zealand": "NZ", "Saudi Arabia": "SA", "South Africa": "ZA",
    "Curaçao": "CW", "Czechia": "CZ",
}

_LIVE_TEAM_NAME_MAP = {
    "United States": "USA",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Cape Verde Islands": "Cape Verde",
    "Congo DR": "DR Congo",
    "Turkey": "Türkiye",
}


def _flag_emoji(name: str, code_hint: str | None = None) -> str:
    iso2 = code_hint or _ISO2_OVERRIDES.get(name)
    if not iso2:
        return "🏳️"
    iso2 = str(iso2)[:2].upper()
    base = 0x1F1E6
    try:
        return chr(base + (ord(iso2[0]) - 65)) + chr(base + (ord(iso2[1]) - 65))
    except Exception:
        return "🏳️"


def _pair_key(a, b):
    if pd.isna(a) or pd.isna(b):
        return None
    return frozenset([a, b])


@ttl_cache()
def load_teams() -> pd.DataFrame:
    teams = pd.read_csv(RAW_DIR / "wc_2026_teams_cleaned.csv")
    elo = pd.read_csv(RAW_DIR / "elo_latest.csv")
    elo = elo.rename(columns={"country": "team", "rating": "elo", "rank": "elo_rank",
                               "country_code": "iso2"})
    elo = elo[["team", "elo", "elo_rank", "iso2", "wins", "losses", "draws",
               "goals_for", "goals_against", "matches_total"]]
    df = teams.merge(elo, on="team", how="left")
    df["flag"] = df.apply(lambda r: _flag_emoji(r["team"], r.get("iso2")), axis=1)
    # A handful of teams in the qualified-teams file aren't in the Elo
    # snapshot (e.g. very recent qualifiers) — fall back to a neutral Elo
    # rather than dropping them from the dashboard.
    df["elo"] = df["elo"].fillna(df["elo"].median())
    df["elo_rank"] = df["elo_rank"].fillna(df["elo_rank"].max() + 1)
    return df


@ttl_cache()
def load_live_matches() -> pd.DataFrame:
    """football-data.org match status and scores, normalized to project team names."""
    path = RAW_DIR / "live_matches.csv"
    if not path.exists():
        return pd.DataFrame()

    live = pd.read_csv(path, parse_dates=["utc_date", "last_updated"])
    live = live.copy()
    live["home_team"] = live["home_team"].replace(_LIVE_TEAM_NAME_MAP)
    live["away_team"] = live["away_team"].replace(_LIVE_TEAM_NAME_MAP)
    live = live[live["home_team"].notna() & live["away_team"].notna()].copy()
    live["pair"] = live.apply(lambda r: _pair_key(r.home_team, r.away_team), axis=1)
    return live


@ttl_cache()
def load_group_matches() -> pd.DataFrame:
    """All 72 group-stage fixtures: model probabilities + live status/scores."""
    pred = pd.read_csv(RAW_DIR / "predictions_2026.csv", parse_dates=["date"])
    fixtures = pd.read_csv(RAW_DIR / "wc_2026_fixtures_enriched.csv")
    fixtures = fixtures[fixtures["is_placeholder_match"] == False]  # noqa: E712

    pred = pred.copy()
    pred["pair"] = pred.apply(lambda r: _pair_key(r.team1, r.team2), axis=1)

    live = load_live_matches()
    live_cols = [
        "pair", "match_id", "match_date", "kickoff_time_utc", "status",
        "is_finished", "is_scheduled", "has_score", "score_display",
        "home_team", "away_team", "home_score", "away_score",
    ]
    if not live.empty:
        live_group = live[live["stage"].eq("GROUP_STAGE")].copy()
        merged = pred.merge(live_group[live_cols].drop_duplicates("pair"), on="pair", how="left")
    else:
        merged = pred.copy()
        for col in live_cols:
            if col != "pair":
                merged[col] = pd.NA

    # Attach venue/city/Elo context from the enriched fixtures file.
    fixtures = fixtures.copy()
    fixtures["pair"] = fixtures.apply(lambda r: _pair_key(r.team1, r.team2), axis=1)
    context_cols = ["pair", "venue", "city", "country", "kickoff_et",
                     "team1_elo_rating", "team2_elo_rating"]
    merged = merged.merge(fixtures[context_cols].drop_duplicates("pair"), on="pair", how="left")

    merged["is_finished"] = merged["is_finished"].fillna(False).astype(bool)
    merged["is_scheduled"] = merged["is_scheduled"].fillna(True).astype(bool)
    merged["has_score"] = merged["has_score"].fillna(False).astype(bool)
    merged["played"] = merged["is_finished"] & merged["has_score"]
    merged["status"] = merged["status"].fillna("SCHEDULED")
    merged["match_date"] = merged["match_date"].fillna(merged["date"].dt.strftime("%Y-%m-%d"))
    merged["score_display"] = merged["score_display"].fillna("TBD")

    def resolve_live_goals(row, col_for_team1):
        if not row["has_score"]:
            return None
        if row["home_team"] == row["team1"]:
            return row["home_score"] if col_for_team1 else row["away_score"]
        return row["away_score"] if col_for_team1 else row["home_score"]

    merged["team1_goals"] = merged.apply(lambda r: resolve_live_goals(r, True), axis=1)
    merged["team2_goals"] = merged.apply(lambda r: resolve_live_goals(r, False), axis=1)

    def score_display(row):
        if not row["has_score"]:
            return "TBD"
        return f"{int(row['team1_goals'])}-{int(row['team2_goals'])}"

    merged["score_display"] = merged.apply(score_display, axis=1)

    def actual_outcome(row):
        if not row["played"]:
            return None
        if row["team1_goals"] > row["team2_goals"]:
            return "team1_win"
        if row["team1_goals"] < row["team2_goals"]:
            return "team2_win"
        return "draw"

    merged["actual_outcome"] = merged.apply(actual_outcome, axis=1)
    merged["elo_difference"] = merged["team1_elo_rating"] - merged["team2_elo_rating"]

    # Confidence + upset-risk derived from how skewed the model's own
    # probabilities are (no fabricated fields beyond what the model gave us).
    probs = merged[["team1_win_prob", "draw_prob", "team2_win_prob"]].values
    top2 = -pd.DataFrame(probs).apply(lambda r: sorted(r, reverse=True)[:2], axis=1, result_type="expand")
    spread = (-top2[0] + top2[1]).abs()  # gap between best and 2nd-best outcome prob
    merged["confidence_score"] = spread.round(2)
    merged["confidence_label"] = pd.cut(
        merged["confidence_score"], bins=[-1, 0.12, 0.30, 2],
        labels=["Low", "Medium", "High"]
    ).astype(str)
    merged["upset_risk_score"] = (1 - merged["confidence_score"]).round(2)

    merged = merged.drop(columns=["pair"])
    return merged.sort_values(["group", "date"]).reset_index(drop=True)


@ttl_cache()
def load_knockout_skeleton() -> pd.DataFrame:
    """The 32 official placeholder rows: R32 -> R16 -> QF -> SF -> 3rd place -> Final."""
    fixtures = pd.read_csv(RAW_DIR / "wc_2026_fixtures_enriched.csv")
    return fixtures[fixtures["is_placeholder_match"] == True].reset_index(drop=True)  # noqa: E712


@ttl_cache()
def load_knockout_matches() -> pd.DataFrame:
    """Resolved knockout fixtures produced by the pipeline, when available."""
    path = RAW_DIR / "knockout_matches.csv"
    if not path.exists():
        return pd.DataFrame()
    knockout = pd.read_csv(path)
    for column in ["home_team", "away_team"]:
        if column in knockout.columns:
            knockout[column] = knockout[column].replace(_LIVE_TEAM_NAME_MAP)
    return knockout


@ttl_cache()
def load_recent_form() -> dict:
    """Last 5 *actual* matches played by each team before the tournament started,
    from real historical results (not synthetic)."""
    hist = pd.read_csv(RAW_DIR / "results_historical.csv", parse_dates=["date"])
    pre_wc = hist[hist["date"] < "2026-06-11"]
    teams = load_teams()["team"].tolist()
    form = {}
    for team in teams:
        rows = pre_wc[(pre_wc.home_team == team) | (pre_wc.away_team == team)].sort_values("date").tail(5)
        results, gf, ga = [], 0, 0
        for _, r in rows.iterrows():
            is_home = r.home_team == team
            my_goals = r.home_score if is_home else r.away_score
            opp_goals = r.away_score if is_home else r.home_score
            gf += my_goals
            ga += opp_goals
            if my_goals > opp_goals:
                results.append("W")
            elif my_goals < opp_goals:
                results.append("L")
            else:
                results.append("D")
        form[team] = {"results": results, "goals_for": int(gf), "goals_against": int(ga)}
    return form


@ttl_cache()
def load_campaign_stats() -> dict:
    """Actual results *within* this World Cup so far, per team."""
    matches = load_group_matches()
    played = matches[matches["played"]]
    teams = load_teams()["team"].tolist()
    stats = {}
    for team in teams:
        rows = played[(played.team1 == team) | (played.team2 == team)].sort_values(
            ["match_date", "kickoff_time_utc"]
        )
        w = d = l = gf = ga = 0
        results = []
        for _, r in rows.iterrows():
            is_t1 = r.team1 == team
            my_goals = r.team1_goals if is_t1 else r.team2_goals
            opp_goals = r.team2_goals if is_t1 else r.team1_goals
            if pd.isna(my_goals) or pd.isna(opp_goals):
                continue
            gf += my_goals
            ga += opp_goals
            if my_goals > opp_goals:
                w += 1
                results.append("W")
            elif my_goals < opp_goals:
                l += 1
                results.append("L")
            else:
                d += 1
                results.append("D")
        stats[team] = {"played": w + d + l, "w": w, "d": d, "l": l,
                        "gf": int(gf), "ga": int(ga), "points": w * 3 + d,
                        "results": results}
    return stats
