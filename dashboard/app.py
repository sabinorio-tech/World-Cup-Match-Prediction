"""
FIFA World Cup 2026 — Prediction Dashboard
Streamlit entrypoint.

Page set and ordering follow the Data Analytics handoff doc:
  1. Tournament Overview
  2. Match Prediction Center
  3. Group Stage Analysis
  4. Team Explorer
  5. Knockout Bracket

Run with:  streamlit run dashboard/app.py
"""

import base64
from pathlib import Path
import sys

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data import (
    get_teams,
    get_team,
    get_matches,
    get_group_standings,
    get_knockout_matches,
    get_round_reach,
    get_player_stats,
    get_data_freshness,
)
from components import (
    inject_css,
    kpi_card,
    match_card,
    top_teams_panel,
    qualification_panel,
    compact_matches_panel,
    match_detail_panel,
    group_stage_panel,
    knockout_bracket_panel,
    team_stats_dashboard,
    fifa_overview_dashboard,
    _flag_image_url,
)
from time_utils import belgian_kickoff

st.set_page_config(page_title="World Cup 2026 Predictions", layout="wide", page_icon="⚽")
inject_css()

ASSET_DIR = Path(__file__).resolve().parent.parent / "assets"
TITLE_IMAGE_PATH = ASSET_DIR / "WC_trophy_transparent.png"


@st.cache_data(show_spinner=False)
def _title_image_src() -> str:
    if not TITLE_IMAGE_PATH.exists():
        return ""
    encoded = base64.b64encode(TITLE_IMAGE_PATH.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def page_header(title: str, subtitle: str) -> None:
    image_src = _title_image_src()
    image_html = f'<img class="wc-page-emblem" src="{image_src}" alt="World Cup trophy">' if image_src else ""
    st.markdown(
        f"""<div class="wc-page-header">
            {image_html}
            <div class="wc-page-header-text">
                <div class="wc-page-title">{title}</div>
                <div class="wc-page-subtitle">{subtitle}</div>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def _predict_teams(home: str, away: str) -> dict:
    try:
        from src.predict import predict_match

        return predict_match(home, away)
    except Exception:
        return {"home_win": 1 / 3, "draw": 1 / 3, "away_win": 1 / 3}


def _dashboard_knockout_matches(knockout_matches):
    if knockout_matches is None or knockout_matches.empty:
        return knockout_matches

    enriched = knockout_matches.copy()
    enriched["match_date"] = enriched["date"]
    enriched["kickoff_time_utc"] = enriched["kickoff_time"]
    enriched["group"] = enriched["stage"]
    finished_statuses = {"FINISHED", "FT", "AET", "PEN"}
    enriched["has_score"] = enriched["home_goals"].notna() & enriched["away_goals"].notna()
    enriched["played"] = enriched["status"].astype(str).str.upper().isin(finished_statuses) & enriched["has_score"]
    enriched["home_win_probability"] = float("nan")
    enriched["draw_probability"] = float("nan")
    enriched["away_win_probability"] = float("nan")
    enriched["upset_risk_score"] = float("nan")
    enriched["confidence_score"] = float("nan")
    enriched["confidence_label"] = "Low"
    enriched["elo_difference"] = 0.0

    resolved = (
        enriched["is_resolved"].fillna(False).astype(str).str.lower().isin({"true", "1"})
        & enriched["home_team"].notna()
        & enriched["away_team"].notna()
    )
    for idx, row in enriched[resolved].iterrows():
        prediction = _predict_teams(str(row.home_team), str(row.away_team))
        probabilities = [prediction["home_win"], prediction["draw"], prediction["away_win"]]
        top_two = sorted(probabilities, reverse=True)[:2]
        confidence_score = abs(top_two[0] - top_two[1])
        home_team = get_team(str(row.home_team))
        away_team = get_team(str(row.away_team))
        enriched.loc[idx, "home_win_probability"] = probabilities[0]
        enriched.loc[idx, "draw_probability"] = probabilities[1]
        enriched.loc[idx, "away_win_probability"] = probabilities[2]
        enriched.loc[idx, "upset_risk_score"] = 1 - confidence_score
        enriched.loc[idx, "confidence_score"] = confidence_score
        enriched.loc[idx, "confidence_label"] = (
            "Low" if confidence_score <= 0.12 else "Medium" if confidence_score <= 0.30 else "High"
        )
        if home_team and away_team:
            enriched.loc[idx, "elo_difference"] = home_team.elo - away_team.elo

    return enriched


def _next_resolved_knockout_match(knockout_matches):
    if knockout_matches is None or knockout_matches.empty:
        return None
    required = {"home_team", "away_team", "is_resolved", "date", "kickoff_time"}
    if not required.issubset(set(knockout_matches.columns)):
        return None

    upcoming = knockout_matches[
        knockout_matches["is_resolved"].astype(bool)
        & knockout_matches["home_team"].notna()
        & knockout_matches["away_team"].notna()
        & ~knockout_matches["status"].astype(str).str.upper().eq("FINISHED")
    ].copy()
    if upcoming.empty:
        return None

    upcoming = upcoming.sort_values(["date", "kickoff_time", "match_id"], na_position="last")
    row = upcoming.iloc[0]
    home = str(row["home_team"])
    away = str(row["away_team"])
    prediction = _predict_teams(home, away)

    return {
        "home_team": home,
        "away_team": away,
        "date": row.get("date"),
        "kickoff_time": row.get("kickoff_time"),
        "stage": row.get("stage", "Knockout"),
        "home_win_probability": prediction["home_win"],
        "draw_probability": prediction["draw"],
        "away_win_probability": prediction["away_win"],
    }


def _next_dashboard_match(matches, knockout_matches):
    if matches is not None and not matches.empty:
        required = {"home_team", "away_team", "played", "match_date", "kickoff_time_utc"}
        if required.issubset(set(matches.columns)):
            upcoming = matches[
                ~matches["played"].astype(bool)
                & matches["home_team"].notna()
                & matches["away_team"].notna()
            ].copy()
            if not upcoming.empty:
                sort_columns = ["match_date", "kickoff_time_utc"]
                if "match_id" in upcoming.columns:
                    sort_columns.append("match_id")
                upcoming = upcoming.sort_values(sort_columns, na_position="last")
                row = upcoming.iloc[0]
                return {
                    "home_team": row.get("home_team"),
                    "away_team": row.get("away_team"),
                    "date": row.get("match_date"),
                    "kickoff_time": row.get("kickoff_time_utc"),
                    "stage": f"Group {row.get('group')}" if row.get("group") else row.get("stage", "Next Match"),
                    "home_win_probability": row.get("home_win_probability", 0),
                    "draw_probability": row.get("draw_probability", 0),
                    "away_win_probability": row.get("away_win_probability", 0),
                }

    return _next_resolved_knockout_match(knockout_matches)


PAGES = ["Overview", "Match Details", "Groups", "Knockout Bracket", "Teams", "About"]


def _clear_page_query() -> None:
    st.query_params.clear()


def _select_team_from_search() -> None:
    st.session_state["selected_team"] = st.session_state["teams_search_country"]


requested_page = st.query_params.get("page")
if requested_page in PAGES and st.session_state.get("dashboard_page") != requested_page:
    st.session_state["dashboard_page"] = requested_page

with st.sidebar:
    st.markdown("## ⚽ WC 2026 Predictions")
    page = st.radio(
        "Navigate",
        PAGES,
        label_visibility="collapsed",
        key="dashboard_page",
        on_change=_clear_page_query,
    )
    st.markdown("---")
    matches_now = get_matches()
    freshness = get_data_freshness()
    st.caption(f"🟢 Live model: XGBoost + Poisson v2 ensemble\n\n"
               f"{int(matches_now['played'].sum())}/{len(matches_now)} group matches played\n\n"
               f"Live data: {freshness['live']}")


# ---------------------------------------------------------------- Overview
def page_overview():
    st.markdown('<div class="wc-top-spacer"></div>', unsafe_allow_html=True)
    matches = get_matches()
    teams = get_teams()
    round_reach = get_round_reach()
    player_stats = get_player_stats()
    knockout_matches = get_knockout_matches()
    dashboard_knockout_matches = _dashboard_knockout_matches(knockout_matches)
    fifa_overview_dashboard(
        matches=matches,
        teams=teams,
        round_reach=round_reach,
        player_stats=player_stats,
        knockout_matches=dashboard_knockout_matches,
        next_match=_next_dashboard_match(matches, dashboard_knockout_matches),
        trophy_src=_title_image_src(),
        data_updated=freshness["live"],
    )


# ---------------------------------------------------------- Match Details
def page_match_details():
    st.markdown('<div class="wc-top-spacer"></div>', unsafe_allow_html=True)
    group_matches = get_matches().copy()
    group_matches["competition_stage"] = "Group " + group_matches["group"].astype(str)
    knockout_matches = _dashboard_knockout_matches(get_knockout_matches())
    if knockout_matches is not None and not knockout_matches.empty:
        resolved = knockout_matches["is_resolved"].fillna(False).astype(str).str.lower().isin({"true", "1"})
        known_teams = knockout_matches["home_team"].notna() & knockout_matches["away_team"].notna()
        knockout_schedule = knockout_matches[resolved & known_teams].copy()
        knockout_schedule["competition_stage"] = knockout_schedule["stage"]
        matches = pd.concat([group_matches, knockout_schedule], ignore_index=True, sort=False)
    else:
        matches = group_matches
    teams_list = sorted(set(matches.home_team) | set(matches.away_team))

    page_header("Match Details", "Browse fixtures, results, and prediction breakdowns")

    status_filter = st.radio(
        "Match status",
        ["All Matches", "Upcoming", "Finished"],
        horizontal=True,
        label_visibility="collapsed",
    )

    c1, c2, c3 = st.columns([0.8, 1.05, 1.45])
    with c1:
        stage_filter = st.selectbox(
            "Stage",
            ["All Stages"] + sorted(matches.competition_stage.dropna().unique()),
        )
    with c2:
        date_options = sorted(matches.match_date.dropna().astype(str).unique())
        date_filter = st.selectbox("Date", ["All Dates"] + date_options)
    with c3:
        team_filter = st.selectbox("Search team", ["All Teams"] + teams_list)

    filtered = matches.copy()
    if status_filter == "Upcoming":
        filtered = filtered[~filtered.played.astype(bool)]
    elif status_filter == "Finished":
        filtered = filtered[filtered.played.astype(bool)]
    if stage_filter != "All Stages":
        filtered = filtered[filtered.competition_stage == stage_filter]
    if date_filter != "All Dates":
        filtered = filtered[filtered.match_date.astype(str) == date_filter]
    if team_filter != "All Teams":
        filtered = filtered[(filtered.home_team == team_filter) | (filtered.away_team == team_filter)]

    filtered = filtered.sort_values(["match_date", "kickoff_time_utc"]).reset_index(drop=True)
    if filtered.empty:
        st.info("No matches found for the selected filters.")
        return

    def match_key(row):
        match_id = row.get("match_id")
        if match_id is not None and str(match_id) not in {"", "nan", "<NA>"}:
            return f"match-{match_id}"
        return f"{row.get('match_date')}-{row.get('home_team')}-{row.get('away_team')}"

    available_keys = [match_key(row) for _, row in filtered.iterrows()]
    selected_key = st.session_state.get("match_detail_selection")
    if selected_key not in available_keys:
        upcoming = filtered[~filtered.played.astype(bool)]
        default_row = upcoming.iloc[0] if not upcoming.empty else filtered.iloc[0]
        selected_key = match_key(default_row)
        st.session_state["match_detail_selection"] = selected_key

    schedule_col, detail_col = st.columns([0.88, 1.42], gap="medium", vertical_alignment="top")
    with schedule_col:
        st.markdown('<div class="wc-schedule-heading">Match Schedule</div>', unsafe_allow_html=True)
        with st.container(height=790, border=True):
            current_date = None
            for _, row in filtered.iterrows():
                row_date, local_kickoff, timezone_label = belgian_kickoff(
                    row.match_date, row.get("kickoff_time_utc", "")
                )
                if row_date != current_date:
                    current_date = row_date
                    st.markdown(
                        f'<div class="wc-schedule-date">{row_date}</div>',
                        unsafe_allow_html=True,
                    )

                row_key = match_key(row)
                home = get_team(row.home_team)
                away = get_team(row.away_team)
                home_flag = home.flag if home else ""
                away_flag = away.flag if away else ""
                status = str(row.get("status", "SCHEDULED")).replace("_", " ").upper()
                if bool(row.played):
                    match_state = f"FT  {row.score_display}"
                elif bool(row.get("has_score", False)):
                    match_state = f"{status}  {row.score_display}"
                else:
                    match_state = (
                        f"{local_kickoff} {timezone_label}"
                        if local_kickoff else "TBD"
                    )
                label = (
                    f"{match_state}  |  {home_flag} {row.home_team}  vs  "
                    f"{away_flag} {row.away_team}  |  {row.competition_stage}"
                )
                if st.button(
                    label,
                    key=f"schedule-{row_key}",
                    use_container_width=True,
                    type="primary" if row_key == selected_key else "secondary",
                ):
                    st.session_state["match_detail_selection"] = row_key
                    st.rerun()

    selected_idx = available_keys.index(st.session_state["match_detail_selection"])
    m = filtered.iloc[selected_idx]
    t1, t2 = get_team(m.home_team), get_team(m.away_team)
    focus_team = team_filter if team_filter != "All Teams" else None
    with detail_col:
        st.markdown('<div class="wc-schedule-heading">Match Preview</div>', unsafe_allow_html=True)
        match_detail_panel(m, t1, t2, focus_team=focus_team, compact=True)


# ----------------------------------------------------------------- Groups
def page_groups():
    st.markdown('<div class="wc-top-spacer"></div>', unsafe_allow_html=True)
    standings = get_group_standings()
    matches = get_matches()
    teams = get_teams()
    teams_by_name = {t.name: t for t in teams}
    groups = sorted(standings.group.unique())
    header_col, select_col = st.columns([2.4, 1])
    with header_col:
        page_header("Group Stage Page", "Current standings, qualification probability, and next fixtures")
    with select_col:
        group_choice = st.selectbox("Select group", groups)

    group_stage_panel(group_choice, standings, matches, teams_by_name)


# --------------------------------------------------------- Knockout Bracket
def page_bracket():
    st.markdown('<div class="wc-top-spacer"></div>', unsafe_allow_html=True)
    standings = get_group_standings()
    round_reach = get_round_reach()
    knockout_matches = get_knockout_matches()
    teams = get_teams()
    teams_by_name = {t.name: t for t in teams}

    page_header("Knockout Bracket Page", "Resolved fixtures when available, with projected progression from simulations")
    zoom = float(st.session_state.get("bracket_zoom", 1.0))
    spacer, zoom_value, zoom_out, zoom_reset, zoom_in = st.columns(
        [8, 0.8, 0.55, 0.55, 0.55], vertical_alignment="center"
    )
    with zoom_out:
        if st.button("−", key="bracket_zoom_out", help="Zoom out", use_container_width=True, disabled=zoom <= 0.7):
            zoom = max(0.7, round(zoom - 0.1, 1))
    with zoom_reset:
        if st.button("↺", key="bracket_zoom_reset", help="Reset zoom", use_container_width=True):
            zoom = 1.0
    with zoom_in:
        if st.button("+", key="bracket_zoom_in", help="Zoom in", use_container_width=True, disabled=zoom >= 1.5):
            zoom = min(1.5, round(zoom + 0.1, 1))
    st.session_state["bracket_zoom"] = zoom
    with zoom_value:
        st.caption(f"{zoom * 100:.0f}%")

    knockout_bracket_panel(
        standings,
        round_reach,
        teams_by_name,
        knockout_matches=knockout_matches,
        trophy_src=_title_image_src(),
        zoom=zoom,
    )


# ------------------------------------------------------------------- Teams
def page_teams():
    st.markdown('<div class="wc-top-spacer"></div>', unsafe_allow_html=True)
    teams = get_teams()
    ranked_teams = sorted(teams, key=lambda t: (-t.elo, t.name))
    names = [t.name for t in ranked_teams]
    requested_team = st.query_params.get("team")
    pending_team = st.session_state.pop("pending_team_selection", None)
    selected_team = pending_team or requested_team or st.session_state.get("selected_team") or names[0]
    if selected_team not in names:
        selected_team = names[0]
    st.session_state["selected_team"] = selected_team
    st.session_state["teams_search_country"] = selected_team

    header_col, select_col = st.columns([2.35, 1])
    with header_col:
        page_header("Team Elo Rankings", "Search countries, compare Elo strength, and inspect tournament context")
    with select_col:
        st.selectbox(
            "Search country",
            names,
            key="teams_search_country",
            on_change=_select_team_from_search,
        )

    team = get_team(st.session_state["selected_team"])
    round_reach = get_round_reach()
    standings = get_group_standings()
    matches = get_matches()
    player_stats = get_player_stats()

    list_col, dashboard_col = st.columns([0.22, 0.78], gap="medium")
    with list_col:
        st.markdown('<div class="wc-native-team-title">All Teams</div>', unsafe_allow_html=True)
        with st.container(height=820, border=True, key="team_selector"):
            for rank, candidate in enumerate(ranked_teams, start=1):
                flag_col, button_col = st.columns([0.18, 0.82], vertical_alignment="center", gap="small")
                with flag_col:
                    flag_url = _flag_image_url(candidate)
                    if flag_url:
                        st.markdown(
                            f'<img class="wc-native-team-flag" src="{flag_url}" alt="{candidate.name} flag">',
                            unsafe_allow_html=True,
                        )
                with button_col:
                    if st.button(
                        f"{rank}. {candidate.name}",
                        key=f"team-select-{candidate.name}",
                        use_container_width=True,
                        type="primary" if candidate.name == team.name else "secondary",
                    ):
                        st.session_state["pending_team_selection"] = candidate.name
                        st.query_params.clear()
                        st.rerun()

    with dashboard_col:
        team_stats_dashboard(
            teams,
            standings,
            round_reach,
            matches=matches,
            player_stats=player_stats,
            selected_team=team.name,
            show_team_list=False,
            player_data_updated=freshness["players"],
        )


# ------------------------------------------------------------------- About
def page_about():
    st.markdown('<div class="wc-top-spacer"></div>', unsafe_allow_html=True)
    page_header("About This Dashboard", "Project context, data sources, and model scope")
    matches = get_matches()
    st.markdown(f"""
This dashboard is built around **football questions, not datasets** —
match-centric cards, qualification odds, and a road-to-the-final view
instead of raw tables, per the Data Analytics handoff brief.

**Model:** a versioned **XGBoost + Poisson ensemble** (`v2_h2h`) trained on
historical international results. XGBoost produces three-way outcome
probabilities from recent form, scoring rates, Elo difference, neutral
venue context, tournament type, and head-to-head features. The Poisson
regressors independently model expected scoring behavior using form, Elo,
venue, and head-to-head goal difference. The final home/draw/away output is
the average of both models' probabilities.

Model quality is measured with time-based validation and documented in
`docs/ds_modeling_report_v2.md`. This page intentionally does not present
one universal "accuracy" number: component validation, the small World Cup
holdout, and refreshed in-tournament outcome tracking answer different
questions and should not be compared as if they were the same metric.

**What's real vs. simulated:**
- Match outcomes for the {int(matches['played'].sum())} matches already played are the
  **actual final scores** — not predictions.
- Win/draw/loss probabilities for the remaining {int((~matches['played']).sum())} group
  matches are the **model's own output**, unmodified.
- Group standings combine real points earned so far with the model's
  probabilities for the matches still to come.
- Qualification and future round-reach odds come from a **3,000-run Monte
  Carlo simulation** using the official 48-team qualification format.
  Hypothetical knockout paths use an Elo-based probability curve, while
  confirmed participants and completed results come from the live source.
  Actual winners always replace projected winners in the bracket.

**Pages:**
- **Overview** — the big tournament story at a glance
- **Match Details** — match-preview style cards: real scores if played, model odds if not
- **Groups** — actual standings plus simulated qualification odds, one group at a time
- **Knockout Bracket** — confirmed fixtures, actual winners, and projected future paths
- **Teams** — country profile, Elo, tournament record, outlook, fixtures, and available player leaders
""")


PAGE_FUNCS = {
    "Overview": page_overview,
    "Match Details": page_match_details,
    "Groups": page_groups,
    "Knockout Bracket": page_bracket,
    "Teams": page_teams,
    "About": page_about,
}

PAGE_FUNCS[page]()
