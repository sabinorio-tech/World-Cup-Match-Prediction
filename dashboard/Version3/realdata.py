"""
Loads the real Phase 1-3 deliverables (DS model predictions + DE team/fixture
data) and assembles them into the shapes the dashboard pages consume.

Inputs (data/raw/, produced by the DE/DS notebooks):
    wc_2026_teams_cleaned.csv       team metadata: group, confederation, fifa_rank, coach
    elo_latest.csv                  current Elo rating + career W/D/L/goals per team
    predictions_2026.csv            XGBoost model output: team1/draw/team2 win probabilities
                                     for all 72 group-stage fixtures
    results_historical.csv          full historical results, incl. WC2026 matches already played
    wc_2026_fixtures_enriched.csv   fixtures + venue/city/Elo context, PLUS the 32 official
                                     knockout placeholder rows (R32 -> Final bracket skeleton)

This module does the joining/cleaning once (cached) and exposes plain
DataFrames/dicts that simulate.py and data.py build on.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"

# "Today" for this snapshot of the dataset — matches played up to and
# including this date are treated as final; everything else is "upcoming"
# and gets the model's predicted probabilities instead of a real score.
SNAPSHOT_DATE = pd.Timestamp("2026-06-18")

_ISO2_OVERRIDES = {
    "South Korea": "KR", "USA": "US", "Ivory Coast": "CI", "Türkiye": "TR",
    "Bosnia and Herzegovina": "BA", "Cape Verde": "CV", "DR Congo": "CD",
    "New Zealand": "NZ", "Saudi Arabia": "SA", "South Africa": "ZA",
    "Curaçao": "CW", "Czechia": "CZ",
}

# flagcdn.com codes for teams that don't have a standard ISO 3166-1
# country (the UK home nations compete separately in football).
_FLAG_CODE_OVERRIDES = {
    "England": "gb-eng",
    "Scotland": "gb-sct",
    "Wales": "gb-wls",
    "Northern Ireland": "gb-nir",
}


def _flag_code(name: str, iso2: str | None) -> str:
    if name in _FLAG_CODE_OVERRIDES:
        return _FLAG_CODE_OVERRIDES[name]
    code = (iso2 or _ISO2_OVERRIDES.get(name) or "xx")
    return str(code)[:2].lower()


def flag_image_url(name: str, iso2: str | None = None, height: int = 40) -> str:
    """Real flag image via flagcdn.com (height in px: 20/40/80/160/etc.)."""
    return f"https://flagcdn.com/h{height}/{_flag_code(name, iso2)}.png"


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


@lru_cache(maxsize=1)
def load_teams() -> pd.DataFrame:
    teams = pd.read_csv(RAW_DIR / "wc_2026_teams_cleaned.csv")
    elo = pd.read_csv(RAW_DIR / "elo_latest.csv")
    elo = elo.rename(columns={"country": "team", "rating": "elo", "rank": "elo_rank",
                               "country_code": "iso2"})
    elo = elo[["team", "elo", "elo_rank", "iso2", "wins", "losses", "draws",
               "goals_for", "goals_against", "matches_total"]]
    df = teams.merge(elo, on="team", how="left")
    df["flag"] = df.apply(lambda r: _flag_emoji(r["team"], r.get("iso2")), axis=1)
    df["flag_url"] = df.apply(lambda r: flag_image_url(r["team"], r.get("iso2")), axis=1)
    # A handful of teams in the qualified-teams file aren't in the Elo
    # snapshot (e.g. very recent qualifiers) — fall back to a neutral Elo
    # rather than dropping them from the dashboard.
    df["elo"] = df["elo"].fillna(df["elo"].median())
    df["elo_rank"] = df["elo_rank"].fillna(df["elo_rank"].max() + 1)
    return df


@lru_cache(maxsize=1)
def load_group_matches() -> pd.DataFrame:
    """All 72 group-stage fixtures: model probabilities + actual result if played."""
    pred = pd.read_csv(RAW_DIR / "predictions_2026.csv", parse_dates=["date"])
    hist = pd.read_csv(RAW_DIR / "results_historical.csv", parse_dates=["date"])
    fixtures = pd.read_csv(RAW_DIR / "wc_2026_fixtures_enriched.csv")
    fixtures = fixtures[fixtures["is_placeholder_match"] == False]  # noqa: E712

    wc = hist[(hist["tournament"] == "FIFA World Cup") &
              (hist["date"] >= "2026-06-01")].copy()

    def pair_key(a, b):
        return frozenset([a, b])

    pred = pred.copy()
    pred["pair"] = pred.apply(lambda r: pair_key(r.team1, r.team2), axis=1)
    wc["pair"] = wc.apply(lambda r: pair_key(r.home_team, r.away_team), axis=1)

    merged = pred.merge(
        wc[["pair", "home_team", "home_score", "away_score"]],
        on="pair", how="left",
    )

    # Attach venue/city/Elo context from the enriched fixtures file.
    fixtures = fixtures.copy()
    fixtures["pair"] = fixtures.apply(lambda r: pair_key(r.team1, r.team2), axis=1)
    context_cols = ["pair", "venue", "city", "country", "kickoff_et",
                     "team1_elo_rating", "team2_elo_rating"]
    merged = merged.merge(fixtures[context_cols].drop_duplicates("pair"), on="pair", how="left")

    merged["played"] = merged["home_score"].notna()

    def resolve_goals(row, col_for_team1):
        """home_score/away_score are relative to results_historical's home_team,
        which doesn't always equal team1 — resolve to team1/team2 perspective."""
        if pd.isna(row["home_score"]):
            return None
        if row["home_team"] == row["team1"]:
            return row["home_score"] if col_for_team1 else row["away_score"]
        return row["away_score"] if col_for_team1 else row["home_score"]

    merged["team1_goals"] = merged.apply(lambda r: resolve_goals(r, True), axis=1)
    merged["team2_goals"] = merged.apply(lambda r: resolve_goals(r, False), axis=1)

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

    merged = merged.drop(columns=["pair", "home_team", "home_score", "away_score"])
    return merged.sort_values(["group", "date"]).reset_index(drop=True)


@lru_cache(maxsize=1)
def load_knockout_skeleton() -> pd.DataFrame:
    """The 32 official placeholder rows: R32 -> R16 -> QF -> SF -> 3rd place -> Final."""
    fixtures = pd.read_csv(RAW_DIR / "wc_2026_fixtures_enriched.csv")
    return fixtures[fixtures["is_placeholder_match"] == True].reset_index(drop=True)  # noqa: E712


@lru_cache(maxsize=1)
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


@lru_cache(maxsize=1)
def load_campaign_stats() -> dict:
    """Actual results *within* this World Cup so far, per team."""
    matches = load_group_matches()
    played = matches[matches["played"]]
    teams = load_teams()["team"].tolist()
    stats = {}
    for team in teams:
        rows = played[(played.team1 == team) | (played.team2 == team)]
        w = d = l = gf = ga = 0
        for _, r in rows.iterrows():
            is_t1 = r.team1 == team
            my_goals = r.team1_goals if is_t1 else r.team2_goals
            opp_goals = r.team2_goals if is_t1 else r.team1_goals
            gf += my_goals
            ga += opp_goals
            if my_goals > opp_goals:
                w += 1
            elif my_goals < opp_goals:
                l += 1
            else:
                d += 1
        stats[team] = {"played": len(rows), "w": w, "d": d, "l": l,
                        "gf": int(gf), "ga": int(ga), "points": w * 3 + d}
    return stats
