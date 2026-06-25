"""
FIFA World Cup 2026 — Prediction Dashboard
Streamlit entrypoint.

Run with:  streamlit run app.py
"""

import streamlit as st
import pandas as pd

from data import get_teams, get_team, get_matches, get_group_standings, get_round_reach, get_knockout_schedule
from components import (inject_css, kpi_card, match_card, confidence_pill, flag_img,
                         probability_bar, circular_gauge, ranked_bar, bracket_match_box, schedule_row)
import bracket_tree as bt
import expected_goals as xg

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
    st.title("🏆 Tournament Overview")
    st.caption("AI predictions for FIFA World Cup 2026™")

    matches = get_matches()
    today = pd.Timestamp.now().normalize()
    matches["date_ts"] = pd.to_datetime(matches["date"])
    upcoming = matches[(~matches["played"]) & (matches["date_ts"] >= today)]
    pending = matches[(~matches["played"]) & (matches["date_ts"] < today)]
    teams = get_teams()
    round_reach = get_round_reach()

    confeds = ["All"] + sorted({t.confederation for t in teams})
    fc1, fc2 = st.columns([1, 4])
    with fc1:
        confed_filter = st.selectbox("Confederation", confeds)

    upcoming_f = upcoming
    if confed_filter != "All":
        names_in_confed = {t.name for t in teams if t.confederation == confed_filter}
        upcoming_f = upcoming[upcoming.home_team.isin(names_in_confed) | upcoming.away_team.isin(names_in_confed)]

    biggest_fav = upcoming.loc[upcoming[["home_win_probability", "away_win_probability"]].max(axis=1).idxmax()]
    fav_team, fav_prob, fav_opp = (
        (biggest_fav.home_team, biggest_fav.home_win_probability, biggest_fav.away_team)
        if biggest_fav.home_win_probability > biggest_fav.away_win_probability
        else (biggest_fav.away_team, biggest_fav.away_win_probability, biggest_fav.home_team)
    )
    biggest_upset = upcoming.loc[upcoming.upset_risk_score.idxmax()]
    avg_confidence = (1 - upcoming.upset_risk_score).mean() * 100

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Group matches played", f"{int(matches['played'].sum())}/{len(matches)}",
                  f"{len(teams)} teams &middot; 12 groups", variant="blue")
    with c2:
        kpi_card("Avg. model confidence", f"{avg_confidence:.0f}%", "Across remaining group matches",
                  variant="green")
    with c3:
        kpi_card("Highest win probability", f"{fav_prob*100:.0f}%", f"{fav_team} vs {fav_opp}", variant="purple")
    with c4:
        kpi_card("Biggest upset risk", f"{biggest_upset.upset_risk_score*100:.0f}%",
                  f"{biggest_upset.home_team} vs {biggest_upset.away_team}", variant="orange")

    col_a, col_b, col_c = st.columns([1.1, 1, 1.3])

    with col_a:
        st.markdown("##### Top 10 strongest teams (Elo)")
        top10 = sorted(teams, key=lambda t: -t.elo)[:10]
        max_elo = top10[0].elo
        for i, t in enumerate(top10):
            ranked_bar(f"{i+1}. {flag_img(t.flag_url, 16)}{t.name}", t.elo, max_elo, str(t.elo))

    with col_b:
        st.markdown("##### Qualification chance (top 8)")
        rr_with_group = get_round_reach()
        standings = get_group_standings().set_index("team")
        top8 = standings.sort_values("group_qualification_probability", ascending=False).head(8)
        gcols = st.columns(4)
        for i, (name, row) in enumerate(top8.iterrows()):
            with gcols[i % 4]:
                circular_gauge(row.group_qualification_probability * 100, name, row.flag_url, color="#3b82f6")

    with col_c:
        st.markdown("##### Next up")
        for _, m in upcoming_f.head(3).iterrows():
            t1, t2 = get_team(m.home_team), get_team(m.away_team)
            match_card(m, t1, t2)

    st.markdown("---")
    st.markdown("##### Full schedule \u2014 remaining group matches through the Final")
    st.caption("Group-stage matches show real teams and model probabilities. Knockout fixtures "
               "from Round of 32 onward don't have known teams yet — those show date and venue only.")

    ko_schedule = get_knockout_schedule()

    with st.expander(f"Group Stage \u2014 {len(upcoming_f)} matches remaining", expanded=True):
        for _, m in upcoming_f.iterrows():
            t1, t2 = get_team(m.home_team), get_team(m.away_team)
            match_card(m, t1, t2)

    if not pending.empty:
        with st.expander(f"\u23f3 Results pending \u2014 {len(pending)} match(es) already kicked off, "
                          f"no score in this dataset yet", expanded=False):
            st.caption("This dataset's real results stop at 2026-06-18. These matches are dated "
                       "before today but the snapshot hasn't been refreshed with their scores.")
            for _, m in pending.iterrows():
                t1, t2 = get_team(m.home_team), get_team(m.away_team)
                match_card(m, t1, t2)

    for stage in ["Round of 32", "Round of 16", "Quarter-final", "Semi-final", "3rd Place Match", "Final"]:
        stage_rows = ko_schedule[ko_schedule.stage == stage]
        if stage_rows.empty:
            continue
        with st.expander(f"{stage} \u2014 {len(stage_rows)} match(es) \u2014 teams TBD", expanded=False):
            for _, r in stage_rows.iterrows():
                schedule_row(stage, r.date, r.kickoff_et, r.venue, r.city)


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

    st.caption(f"{len(filtered)} match(es) — select one for full detail")
    match_labels = [f"{r.home_team} vs {r.away_team} ({r.date})" for _, r in filtered.iterrows()]
    if not match_labels:
        st.info("No matches match this filter.")
        return
    choice_idx = st.selectbox("Match", range(len(match_labels)), format_func=lambda i: match_labels[i])
    m = filtered.iloc[choice_idx]
    t1, t2 = get_team(m.home_team), get_team(m.away_team)

    st.markdown(f"#### Group {m.group} \u2014 {m.date}" + (f" \u00b7 {m.kickoff_et}" if pd.notna(m.get('kickoff_et')) else ""))
    if isinstance(m.get("venue"), str):
        st.caption(f"📍 {m.venue}, {m.get('city', '')}")

    big1, vs_col, big2 = st.columns([2, 1, 2])
    with big1:
        st.markdown(f"<div style='text-align:center;'>{flag_img(t1.flag_url, 56)}<br><b style='font-size:1.2rem;'>{t1.name}</b></div>",
                    unsafe_allow_html=True)
    with vs_col:
        st.markdown("<div style='text-align:center; padding-top:18px; opacity:0.5; font-weight:700;'>VS</div>",
                    unsafe_allow_html=True)
    with big2:
        st.markdown(f"<div style='text-align:center;'>{flag_img(t2.flag_url, 56)}<br><b style='font-size:1.2rem;'>{t2.name}</b></div>",
                    unsafe_allow_html=True)

    st.markdown("")

    if bool(m.get("played")):
        st.success(f"**Final score: {int(m.home_goals)} - {int(m.away_goals)}**  (already played)")
    else:
        probability_bar(m.home_win_probability * 100, m.draw_probability * 100, m.away_win_probability * 100)
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            st.metric(f"{t1.name} win", f"{m.home_win_probability*100:.0f}%")
        with pc2:
            st.metric("Draw", f"{m.draw_probability*100:.0f}%")
        with pc3:
            st.metric(f"{t2.name} win", f"{m.away_win_probability*100:.0f}%")
        st.markdown(confidence_pill(m.confidence_label), unsafe_allow_html=True)

        st.markdown("##### Key factors")
        kf1, kf2, kf3, kf4 = st.columns(4)
        with kf1:
            kpi_card("Elo difference", f"{m.elo_difference:+.0f}", f"{t1.name} perspective", variant="blue")
        with kf2:
            form1 = " ".join(t1.recent_form) or "n/a"
            kpi_card(f"{t1.name} recent form", form1, "Last 5 before WC", variant="green")
        with kf3:
            form2 = " ".join(t2.recent_form) or "n/a"
            kpi_card(f"{t2.name} recent form", form2, "Last 5 before WC", variant="green")
        with kf4:
            kpi_card("Venue context", "Neutral" if pd.isna(m.get("country")) or True else "Home",
                      "All WC2026 group venues are neutral", variant="purple")

        st.markdown("##### Estimated score (secondary heuristic — not the model's output)")
        st.caption("The production model only predicts win/draw/loss. This expected-goals estimate is derived "
                   "separately from each team's real recent scoring/conceding rates, for illustration only.")
        lam1, lam2 = xg.estimate_match_xg(t1.name, t2.name, m.elo_difference)
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            kpi_card("Estimated score", f"{round(lam1)} - {round(lam2)}", "Rounded from expected goals",
                      variant="neutral")
        with sc2:
            kpi_card(f"{t1.name} xG", f"{lam1:.2f}", "Estimated", variant="neutral")
        with sc3:
            kpi_card(f"{t2.name} xG", f"{lam2:.2f}", "Estimated", variant="neutral")


# ----------------------------------------------------------------- Groups
def page_groups():
    st.title("Group Stage Analysis")
    standings = get_group_standings()
    groups = sorted(standings.group.unique())
    group_choice = st.selectbox("Select group", groups)

    g = standings[standings.group == group_choice].sort_values(
        ["points", "goal_difference"], ascending=[False, False]).reset_index(drop=True)

    left, right = st.columns([1.4, 1])

    with left:
        st.markdown(f"##### Group {group_choice} \u2014 current standings")
        st.caption("Points reflect matches actually played. Qualification % comes from the "
                   "3,000-run Monte Carlo simulation of remaining fixtures.")
        header = st.columns([3, 1, 1, 1, 1, 1, 1, 1, 2])
        for col, label in zip(header, ["Team", "P", "W", "D", "L", "GF", "GA", "GD", "Qualify"]):
            col.markdown(f"**{label}**")
        for _, row in g.iterrows():
            cols = st.columns([3, 1, 1, 1, 1, 1, 1, 1, 2])
            cols[0].markdown(f"{flag_img(row.flag_url, 18)}{row.team}", unsafe_allow_html=True)
            cols[1].write(int(row.played))
            cols[2].write(int(row.w))
            cols[3].write(int(row.d))
            cols[4].write(int(row.l))
            cols[5].write(int(row.goals_for))
            cols[6].write(int(row.goals_against))
            cols[7].write(f"{int(row.goal_difference):+d}")
            cols[8].progress(min(1.0, row.group_qualification_probability),
                              text=f"{row.group_qualification_probability*100:.0f}%")

    with right:
        st.markdown("##### Projected final points")
        max_pts = g.projected_points.max()
        for _, row in g.sort_values("projected_points", ascending=False).iterrows():
            ranked_bar(flag_img(row.flag_url, 16) + row.team, row.projected_points, max_pts, f"{row.projected_points}")

        st.markdown("##### Stats overview")
        most_gf = g.loc[g.goals_for.idxmax()]
        best_def = g.loc[g.goals_against.idxmin()]
        kpi_card("Most goals scored so far", f"{flag_img(most_gf.flag_url,16)}{most_gf.team}",
                  f"{int(most_gf.goals_for)} goals", variant="green")
        kpi_card("Best defense so far", f"{flag_img(best_def.flag_url,16)}{best_def.team}",
                  f"{int(best_def.goals_against)} conceded", variant="blue")

    st.markdown("##### Remaining fixtures \u2014 Group " + group_choice)
    matches = get_matches()
    today = pd.Timestamp.now().normalize()
    matches["date_ts"] = pd.to_datetime(matches["date"])
    group_matches = matches[(matches.group == group_choice) & (~matches.played) & (matches.date_ts >= today)]
    for _, m in group_matches.iterrows():
        t1, t2 = get_team(m.home_team), get_team(m.away_team)
        match_card(m, t1, t2)


# --------------------------------------------------------- Knockout Bracket
def page_bracket():
    st.title("Knockout Bracket")
    st.caption("Most-likely single path through the real Round-of-32 \u2192 Final structure "
               "(12 groups, top 2 + best 8 third-place teams). See About for methodology.")

    bracket = bt.build_bracket()
    teams_by_name = {t.name: t for t in get_teams()}

    round_tabs = st.tabs(["Round of 32", "Round of 16", "Quarterfinal", "Semifinal", "Final"])
    round_keys = ["round_of_32", "round_of_16", "quarterfinal", "semifinal", "final"]
    for tab, key in zip(round_tabs, round_keys):
        with tab:
            matches = bracket[key]
            n_cols = 2 if len(matches) > 1 else 1
            cols = st.columns(n_cols)
            for i, m in enumerate(matches):
                with cols[i % n_cols]:
                    bracket_match_box(m, teams_by_name)

    champ = teams_by_name.get(bracket["champion"])
    st.markdown("---")
    st.markdown(f"### 🏆 Predicted champion: {flag_img(champ.flag_url, 28)}{champ.name}", unsafe_allow_html=True)

    st.markdown("##### Chance to win the tournament (Monte Carlo simulation)")
    round_reach = get_round_reach()
    top4 = round_reach.head(4)
    cols = st.columns(4)
    for i, (_, row) in enumerate(top4.iterrows()):
        with cols[i]:
            kpi_card(f"#{i+1} {flag_img(row.flag_url,18)}{row.team}", f"{row.tournament_win_probability*100:.0f}%",
                      "win probability", variant=["blue", "green", "purple", "orange"][i])


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
        kpi_card(f"{flag_img(team.flag_url)}{team.name}", f"Elo {team.elo}", f"FIFA rank #{team.fifa_rank}",
                  variant="blue")
    with c2:
        kpi_card("Group", team.group, f"Confederation: {team.confederation}", variant="green")
    with c3:
        kpi_card("This World Cup so far", f"{team.campaign_w}W {team.campaign_d}D {team.campaign_l}L",
                  f"{team.campaign_played} played, GF {team.campaign_gf} / GA {team.campaign_ga}", variant="purple")
    with c4:
        win_p = round_reach.loc[team.name, "tournament_win_probability"] * 100
        kpi_card("Tournament win probability", f"{win_p:.1f}%", "from Monte Carlo simulation", variant="orange")

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
**Model:** XGBoost multi-class classifier (`multi:softprob`) trained on historical international
results (1916-2026) using Elo difference, recent win/draw rates, and average goals scored/conceded
as features. Validated on the 2022 World Cup, tested on the {int(matches['played'].sum())} WC 2026
group matches played so far: **53.6% accuracy** and **0.984 log-loss** (vs. a 1.099 random baseline).

**What's real vs. estimated/simulated:**
- Match outcomes for matches already played are the **actual final scores**, not predictions.
- Win/draw/loss probabilities for upcoming matches are the **model's own output**, unmodified.
- The "Estimated score" / xG shown on the Match Details page is a **separate, clearly-labeled
  heuristic** built from each team's real recent scoring/conceding rates — the production
  classifier doesn't output goals, so this is not the same model.
- Group qualification odds come from a **3,000-run Monte Carlo simulation** that resamples only
  unplayed matches from the model's probabilities and applies the official format (top 2 per
  group + best 8 third-placed teams).
- The **Knockout Bracket page shows ONE deterministic "most likely" path** (highest-probability
  team advances at every step) through the real official Round-of-32 \u2192 Final structure — this
  is different from the Monte Carlo distribution used for the "chance to win" cards, which
  reflects the full spread of outcomes across all 3,000 simulated tournaments.
- This dashboard uses the **real 2026 format**: 48 teams, 12 groups, Round of 32 with 8
  best-third-place wildcard slots — not the older 32-team/8-group format.
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
