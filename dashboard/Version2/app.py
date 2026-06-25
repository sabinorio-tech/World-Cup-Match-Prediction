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

import streamlit as st
import pandas as pd

from data import get_teams, get_team, get_matches, get_group_standings, get_round_reach, db_available
from components import inject_css, kpi_card, match_card, confidence_pill, flag_img
from bracket import build_funnel_svg

st.set_page_config(page_title="World Cup 2026 Predictions", layout="wide", page_icon="⚽")
inject_css()

PAGES = ["Overview", "Match Details", "Groups", "Knockout Bracket", "Teams", "About"]

with st.sidebar:
    st.markdown("## ⚽ WC 2026 Predictions")
    page = st.radio("Navigate", PAGES, label_visibility="collapsed")
    st.markdown("---")
    matches_now = get_matches()
    st.caption(f"🟢 Live model: XGBoost classifier\n\n"
               f"{int(matches_now['played'].sum())}/{len(matches_now)} group matches played")


# ---------------------------------------------------------------- Overview
def page_overview():
    st.title("Tournament Overview")
    matches = get_matches()
    upcoming = matches[~matches["played"]]
    teams = get_teams()
    round_reach = get_round_reach()

    biggest_fav = upcoming.loc[upcoming[["home_win_probability", "away_win_probability"]].max(axis=1).idxmax()]
    fav_team, fav_prob, fav_opp = (
        (biggest_fav.home_team, biggest_fav.home_win_probability, biggest_fav.away_team)
        if biggest_fav.home_win_probability > biggest_fav.away_win_probability
        else (biggest_fav.away_team, biggest_fav.away_win_probability, biggest_fav.home_team)
    )
    biggest_upset = upcoming.loc[upcoming.upset_risk_score.idxmax()]
    avg_confidence = (1 - upcoming.upset_risk_score).mean() * 100
    tournament_fav = round_reach.iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Group matches played", f"{int(matches['played'].sum())}/{len(matches)}",
                  f"{len(teams)} teams, 12 groups")
    with c2:
        kpi_card("Highest win probability", f"{fav_team} {fav_prob*100:.0f}%", f"vs {fav_opp}")
    with c3:
        kpi_card("Biggest upset risk", f"{biggest_upset.home_team} vs {biggest_upset.away_team}",
                  f"risk score {biggest_upset.upset_risk_score:.2f}")
    with c4:
        kpi_card("Average model confidence", f"{avg_confidence:.0f}%", "across remaining group matches")

    st.markdown("### Tournament favorites (Monte Carlo simulation)")
    cols = st.columns(5)
    for i, (_, row) in enumerate(round_reach.head(5).iterrows()):
        with cols[i]:
            kpi_card(f"{flag_img(row.flag_url)}{row.team}", f"{row.tournament_win_probability*100:.1f}%", "win probability")

    st.markdown("### Top 10 strongest teams (Elo)")
    top10 = sorted(teams, key=lambda t: -t.elo)[:10]
    df = pd.DataFrame([{"Rank": i + 1, "Flag": t.flag_url, "Team": t.name, "Elo": t.elo} for i, t in enumerate(top10)])
    st.dataframe(df, hide_index=True, width='stretch',
                 column_config={
                     "Flag": st.column_config.ImageColumn("Flag", width="small"),
                     "Elo": st.column_config.ProgressColumn(
                         "Elo", min_value=int(df.Elo.min()) - 20, max_value=int(df.Elo.max()) + 20)})

    st.markdown("### Upcoming matches")
    for _, m in upcoming.head(5).iterrows():
        t1, t2 = get_team(m.home_team), get_team(m.away_team)
        match_card(m, t1, t2)


# ---------------------------------------------------------- Match Details
def page_match_details():
    st.title("Match Prediction Center")
    matches = get_matches()
    teams_list = sorted(set(matches.home_team) | set(matches.away_team))

    c1, c2 = st.columns(2)
    with c1:
        group_filter = st.selectbox("Group", ["All"] + sorted(matches.group.unique()))
    with c2:
        team_filter = st.selectbox("Team", ["All"] + teams_list)

    filtered = matches.copy()
    if group_filter != "All":
        filtered = filtered[filtered.group == group_filter]
    if team_filter != "All":
        filtered = filtered[(filtered.home_team == team_filter) | (filtered.away_team == team_filter)]

    st.caption(f"{len(filtered)} match(es)")
    for _, m in filtered.iterrows():
        t1, t2 = get_team(m.home_team), get_team(m.away_team)
        with st.container():
            match_card(m, t1, t2)
            if not m["played"]:
                with st.expander("Key factors"):
                    st.write(f"- **Elo difference:** {m.elo_difference:+.0f} ({t1.name} perspective)")
                    st.write(f"- **Model:** XGBoost classifier (win/draw/loss probabilities)")
                    st.write(f"- **Group:** {m.group}  |  **Venue:** {m.venue}, {m.city}  |  **Date:** {m.date}")
            st.markdown("")


# ----------------------------------------------------------------- Groups
def page_groups():
    st.title("Group Stage Analysis")
    standings = get_group_standings()
    groups = sorted(standings.group.unique())
    group_choice = st.selectbox("Select group", groups)

    g = standings[standings.group == group_choice].sort_values(
        ["points", "goal_difference"], ascending=[False, False])
    st.markdown(f"### Group {group_choice} — current standings")
    st.caption("Points reflect matches actually played so far. Qualification % comes from "
               "the Monte Carlo simulation of remaining fixtures.")

    for _, row in g.iterrows():
        c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
        with c1:
            st.markdown(f"**{flag_img(row.flag_url)}{row.team}**", unsafe_allow_html=True)
        with c2:
            st.markdown(f"Pts: **{int(row.points)}** ({int(row.played)} played)")
        with c3:
            st.markdown(f"GD: **{int(row.goal_difference):+d}**")
        with c4:
            st.progress(min(1.0, row.group_qualification_probability),
                        text=f"Qualify: {row.group_qualification_probability*100:.0f}%")

    with st.expander("Full table (goals for / against)"):
        st.dataframe(
            g[["team", "played", "points", "goals_for", "goals_against", "goal_difference",
               "group_qualification_probability"]].rename(columns={
                "team": "Team", "played": "Played", "points": "Pts", "goals_for": "GF",
                "goals_against": "GA", "goal_difference": "GD",
                "group_qualification_probability": "Qual. Prob.",
            }),
            hide_index=True, width='stretch',
        )


# --------------------------------------------------------- Knockout Bracket
def page_bracket():
    st.title("Knockout Bracket — Road to the Final")
    st.caption("Funnel view of round-reach probabilities for the top contenders. "
               "Replace with the real single-elimination bracket once group results are final.")
    round_reach = get_round_reach()
    top_n = st.slider("Show top N teams", 4, 16, 8)
    svg = build_funnel_svg(round_reach, top_n=top_n)
    st.markdown(f'<div style="color:#1a1a1a; background:#fafafa; border-radius:12px; padding:8px;">{svg}</div>',
                unsafe_allow_html=True)

    st.markdown("### Tournament winner probability")
    winner_df = round_reach.head(10)[["flag_url", "team", "tournament_win_probability"]]
    winner_df = winner_df.rename(columns={"flag_url": "", "team": "Team", "tournament_win_probability": "Win %"})
    winner_df["Win %"] = (winner_df["Win %"] * 100).round(1)
    st.dataframe(winner_df, hide_index=True, width='stretch',
                 column_config={
                     "": st.column_config.ImageColumn("", width="small"),
                     "Win %": st.column_config.ProgressColumn("Win %", min_value=0, max_value=float(winner_df["Win %"].max()))})


# ------------------------------------------------------------------- Teams
def page_teams():
    st.title("Team Explorer")
    teams = get_teams()
    names = sorted(t.name for t in teams)
    choice = st.selectbox("Select a country", names)
    team = get_team(choice)
    round_reach = get_round_reach().set_index("team")
    standings = get_group_standings().set_index("team")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card(f"{flag_img(team.flag_url)}{team.name}", f"Elo {team.elo}", f"FIFA rank #{team.fifa_rank}")
    with c2:
        kpi_card("Group", team.group, f"Confederation: {team.confederation}")
    with c3:
        kpi_card("This World Cup so far", f"{team.campaign_w}W {team.campaign_d}D {team.campaign_l}L",
                  f"{team.campaign_played} played, GF {team.campaign_gf} / GA {team.campaign_ga}")
    with c4:
        win_p = round_reach.loc[team.name, "tournament_win_probability"] * 100
        kpi_card("Tournament win probability", f"{win_p:.1f}%", "from Monte Carlo simulation")

    st.markdown(f"**Recent form before the tournament (last 5):** {' '.join(team.recent_form) or 'n/a'} "
                f"(GF {team.goals_for_l5} / GA {team.goals_against_l5})")
    if team.coach:
        st.caption(f"Coach: {team.coach}")

    st.markdown("### Group-stage fixtures")
    matches = get_matches()
    team_matches = matches[(matches.home_team == team.name) | (matches.away_team == team.name)]
    for _, m in team_matches.iterrows():
        t1, t2 = get_team(m.home_team), get_team(m.away_team)
        match_card(m, t1, t2)

    st.markdown("### Qualification & progression")
    qual = standings.loc[team.name, "group_qualification_probability"] * 100
    rr = round_reach.loc[team.name]
    st.progress(min(1.0, qual / 100), text=f"Group qualification: {qual:.0f}%")
    cols = st.columns(5)
    rounds = [("Round of 16", "round_of_16"), ("Quarterfinal", "quarterfinal"),
              ("Semifinal", "semifinal"), ("Final", "final"), ("Winner", "tournament_win_probability")]
    for col, (label, key) in zip(cols, rounds):
        with col:
            st.metric(label, f"{rr[key]*100:.1f}%")


# ------------------------------------------------------------------- About
def page_about():
    st.title("About this dashboard")
    matches = get_matches()
    st.markdown(f"""
This dashboard is built around **football questions, not datasets** —
match-centric cards, qualification odds, and a road-to-the-final view
instead of raw tables, per the Data Analytics handoff brief.

**Model:** XGBoost multi-class classifier (`multi:softprob`) trained on
historical international results (1916-2026) using Elo difference, recent
win/draw rates, and average goals scored/conceded as features. Validated
on the 2022 World Cup, tested on the {int(matches['played'].sum())} WC 2026
group matches played so far: **53.6% accuracy** and **0.984 log-loss**
(vs. a 1.099 random baseline). `elo_diff` was by far the strongest feature,
followed by each side's average goals conceded and win rate.

**What's real vs. simulated:**
- Match outcomes for the {int(matches['played'].sum())} matches already played are the
  **actual final scores** — not predictions.
- Win/draw/loss probabilities for the remaining {int((~matches['played']).sum())} group
  matches are the **model's own output**, unmodified.
- Group standings combine real points earned so far with the model's
  probabilities for the matches still to come.
- Qualification and round-reach odds come from a **3,000-run Monte Carlo
  simulation** that resamples only the unplayed group matches, applies the
  official 48-team format (top 2 per group + best 8 third-place teams),
  and follows the real knockout bracket skeleton (1A vs 2B, etc.) through
  to the Final. Knockout matches themselves use a standard Elo win-probability
  curve, since the trained classifier needs recent-form features that don't
  exist yet for hypothetical knockout pairings — this is a clearly-flagged
  approximation layered on top of the model's group-stage predictions, not
  a replacement for them.

**Pages:**
- **Overview** — the big tournament story at a glance
- **Match Details** — match-preview style cards: real scores if played, model odds if not
- **Groups** — actual standings plus simulated qualification odds, one group at a time
- **Knockout Bracket** — round-reach funnel and tournament winner odds from the simulation
- **Teams** — per-country profile: Elo, this campaign's results, pre-tournament form, fixtures
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
