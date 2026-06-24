"""
Reusable, football-flavoured UI building blocks for the Streamlit app.
Keeps app.py focused on page composition rather than markup.
"""

import streamlit as st

CSS = """
<style>
.wc-card {
    background: linear-gradient(135deg, #0e2a1f 0%, #143d2b 100%);
    border-radius: 14px;
    padding: 18px 20px;
    color: #f4f7f5;
    box-shadow: 0 2px 10px rgba(0,0,0,0.18);
    margin-bottom: 10px;
}
.wc-kpi-label { font-size: 0.78rem; opacity: 0.75; text-transform: uppercase; letter-spacing: 0.06em; }
.wc-kpi-value { font-size: 1.6rem; font-weight: 700; margin-top: 2px; }
.wc-kpi-sub { font-size: 0.82rem; opacity: 0.85; margin-top: 4px; }

.wc-match-card {
    background: #ffffff10;
    border: 1px solid #ffffff22;
    border-radius: 16px;
    padding: 16px;
}
.wc-team-row { display: flex; justify-content: space-between; align-items: center; font-size: 1.05rem; font-weight: 600; }
.wc-prob-bar-wrap { display: flex; height: 10px; border-radius: 6px; overflow: hidden; margin: 10px 0; background: #00000022; }
.wc-prob-seg { height: 100%; }
.wc-prob-labels { display: flex; justify-content: space-between; font-size: 0.78rem; opacity: 0.85; }
.wc-pill {
    display: inline-block; padding: 2px 10px; border-radius: 999px;
    font-size: 0.75rem; font-weight: 600;
}
.wc-pill-high { background: #1e7d4733; color: #5fd98f; }
.wc-pill-medium { background: #c98a1f33; color: #f0b94d; }
.wc-pill-low { background: #b8333322; color: #ef7b7b; }
.wc-upset { color: #f0b94d; font-size: 0.8rem; }
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def kpi_card(label: str, value: str, sub: str = ""):
    st.markdown(
        f"""<div class="wc-card">
            <div class="wc-kpi-label">{label}</div>
            <div class="wc-kpi-value">{value}</div>
            <div class="wc-kpi-sub">{sub}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def confidence_pill(label: str) -> str:
    css_class = {"High": "wc-pill-high", "Medium": "wc-pill-medium", "Low": "wc-pill-low"}.get(label, "wc-pill-medium")
    return f'<span class="wc-pill {css_class}">{label} confidence</span>'


def probability_bar(home_pct: float, draw_pct: float, away_pct: float,
                     home_label: str, away_label: str):
    st.markdown(
        f"""
        <div class="wc-prob-bar-wrap">
            <div class="wc-prob-seg" style="width:{home_pct}%; background:#2e9e5b;"></div>
            <div class="wc-prob-seg" style="width:{draw_pct}%; background:#7a7a7a;"></div>
            <div class="wc-prob-seg" style="width:{away_pct}%; background:#c1473d;"></div>
        </div>
        <div class="wc-prob-labels">
            <span>{home_label} {home_pct:.0f}%</span>
            <span>Draw {draw_pct:.0f}%</span>
            <span>{away_label} {away_pct:.0f}%</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def match_card(match_row, team1, team2):
    st.markdown('<div class="wc-match-card">', unsafe_allow_html=True)

    played = bool(match_row.get("played", False))
    if played:
        st.markdown(
            f"""<div class="wc-team-row">
                <span>{team1.flag} {team1.name}</span>
                <span style="opacity:0.9; font-weight:700;">{int(match_row['home_goals'])} - {int(match_row['away_goals'])}</span>
                <span>{team2.name} {team2.flag}</span>
            </div>""",
            unsafe_allow_html=True,
        )
        st.markdown('<span class="wc-pill wc-pill-high">Played \u2014 final score</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        return

    home_pct = match_row["home_win_probability"] * 100
    draw_pct = match_row["draw_probability"] * 100
    away_pct = match_row["away_win_probability"] * 100

    st.markdown(
        f"""<div class="wc-team-row">
            <span>{team1.flag} {team1.name}</span>
            <span style="opacity:0.6; font-weight:400;">vs</span>
            <span>{team2.name} {team2.flag}</span>
        </div>""",
        unsafe_allow_html=True,
    )
    probability_bar(home_pct, draw_pct, away_pct, team1.name, team2.name)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(confidence_pill(match_row["confidence_label"]), unsafe_allow_html=True)
    with c2:
        if match_row["upset_risk_score"] >= 0.7:
            st.markdown(f'<span class="wc-upset">\u26a0 Upset potential ({match_row["upset_risk_score"]:.2f})</span>',
                         unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
