"""
Dark-theme UI components for the World Cup 2026 dashboard.
"""

import streamlit as st

CSS = """
<style>
/* ---------- Global text contrast fix ----------
   Streamlit's own text (headings, sidebar, captions, metrics, widget
   labels) defaults to a dark gray meant for a LIGHT background. We only
   changed .stApp's background to dark, so without this override that
   text is nearly invisible. Force everything bright explicitly. */
.stApp, .stApp p, .stApp span, .stApp li, .stApp label,
.stApp div, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
    color: #f1f5f9 !important;
}
.stApp [data-testid="stCaptionContainer"], .stApp small,
.stApp [data-testid="stCaptionContainer"] * {
    color: #aab4c5 !important;
}
.stApp h1, .stApp h2, .stApp h3 { color: #ffffff !important; font-weight: 800 !important; }
.stApp h4, .stApp h5, .stApp h6 { color: #f8fafc !important; }

section[data-testid="stSidebar"] { background: #0d1320; }
section[data-testid="stSidebar"] * { color: #f1f5f9 !important; }
section[data-testid="stSidebar"] [role="radiogroup"] label p { font-size: 0.95rem !important; font-weight: 600 !important; }

[data-testid="stMetricValue"] { color: #ffffff !important; font-weight: 800 !important; }
[data-testid="stMetricLabel"] { color: #aab4c5 !important; }

[data-testid="stProgress"] p, [data-testid="stProgress"] div { color: #f1f5f9 !important; }
[data-baseweb="select"] * { color: #f1f5f9 !important; }
[data-baseweb="select"] { background: #1a2236 !important; }

[data-testid="stDataFrame"] { color: #f1f5f9 !important; }

/* ---------- Component styles ---------- */
.stApp { background: #0a0e1a; }
section[data-testid="stSidebar"] { background: #0d1320; }

.wc-card {
    border-radius: 14px;
    padding: 16px 20px;
    color: #e8ecf3;
    box-shadow: 0 2px 10px rgba(0,0,0,0.35);
    margin-bottom: 10px;
    border: 1px solid rgba(255,255,255,0.06);
}
.wc-card-blue   { background: linear-gradient(135deg, #0f2247 0%, #15305f 100%); }
.wc-card-green  { background: linear-gradient(135deg, #0d2818 0%, #134024 100%); }
.wc-card-purple { background: linear-gradient(135deg, #1f1530 0%, #2c1f4a 100%); }
.wc-card-orange { background: linear-gradient(135deg, #2e1d08 0%, #4a2e0c 100%); }
.wc-card-neutral{ background: #111827; }

.wc-kpi-label { font-size: 0.72rem; color: #c2cad6; text-transform: uppercase; letter-spacing: 0.07em; font-weight: 700; }
.wc-kpi-value { font-size: 1.65rem; font-weight: 800; margin-top: 4px; line-height: 1.1; color: #ffffff; }
.wc-kpi-sub { font-size: 0.8rem; color: #c2cad6; margin-top: 4px; }

.wc-match-card {
    background: #111827;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 10px;
}
.wc-match-meta { font-size: 0.74rem; color: #9aa5b8; margin-bottom: 8px; display:flex; gap:14px; }
.wc-team-row { display: flex; justify-content: space-between; align-items: center; font-size: 1.0rem; font-weight: 700; margin-bottom: 8px; color: #ffffff;}

.wc-prob-bar-wrap { position: relative; height: 26px; border-radius: 7px; overflow: hidden; margin: 8px 0; background:#1e293b; }
.wc-prob-seg { position: absolute; top: 0; height: 100%; }
.wc-prob-label {
    position: absolute; top: 50%; transform: translate(-50%, -50%);
    font-size: 11.5px; font-weight: 700; color: #fff; text-shadow: 0 1px 2px rgba(0,0,0,0.5);
    white-space: nowrap; pointer-events:none;
}

.wc-pill { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 0.72rem; font-weight: 700; }
.wc-pill-high   { background: #0f3d2433; color: #4ade80; }
.wc-pill-medium { background: #4a330a55; color: #fbbf24; }
.wc-pill-low    { background: #4a151555; color: #f87171; }
.wc-upset { color: #fbbf24; font-size: 0.78rem; font-weight: 600; }

.wc-gauge-wrap { display:flex; flex-direction:column; align-items:center; gap:6px; }
.wc-gauge {
    width: 84px; height: 84px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    position: relative;
}
.wc-gauge::before {
    content: ""; position: absolute; width: 64px; height: 64px; border-radius: 50%;
    background: #0a0e1a;
}
.wc-gauge-text { position: relative; z-index: 1; font-weight: 800; font-size: 1.05rem; color: #fff; }
.wc-gauge-label { font-size: 0.8rem; font-weight: 700; color: #e8ecf3; text-align:center; }

.wc-bar-row { display: flex; align-items: center; gap: 8px; margin-bottom: 7px; font-size: 0.85rem; color: #e8ecf3; }
.wc-bar-track { flex: 1; height: 9px; background: #1e293b; border-radius: 5px; overflow: hidden; }
.wc-bar-fill { height: 100%; border-radius: 5px; background: linear-gradient(90deg, #22c55e, #16a34a); }

.wc-bracket-box {
    background: #111827; border: 1px solid rgba(255,255,255,0.08); border-radius: 10px;
    padding: 8px 12px; margin-bottom: 6px;
}
.wc-bracket-team { display:flex; justify-content:space-between; align-items:center; padding: 3px 0; font-size: 0.85rem; }
.wc-bracket-winner { font-weight: 800; color: #4ade80; }
.wc-bracket-loser { opacity: 0.55; }
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def flag_img(url: str, size: int = 20) -> str:
    """Inline <img> tag for a flag — use inside any unsafe_allow_html markdown."""
    return (f'<img src="{url}" style="height:{size}px;width:auto;vertical-align:middle;'
            f'border-radius:2px;margin-right:6px;box-shadow:0 0 1px rgba(0,0,0,0.4);">')


def flag_img_html(team, size: int = 20) -> str:
    return f'{flag_img(team.flag_url, size)}{team.name}'


def kpi_card(label: str, value: str, sub: str = "", variant: str = "neutral"):
    st.markdown(
        f"""<div class="wc-card wc-card-{variant}">
            <div class="wc-kpi-label">{label}</div>
            <div class="wc-kpi-value">{value}</div>
            <div class="wc-kpi-sub">{sub}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def confidence_pill(label: str) -> str:
    css_class = {"High": "wc-pill-high", "Medium": "wc-pill-medium", "Low": "wc-pill-low"}.get(label, "wc-pill-medium")
    return f'<span class="wc-pill {css_class}">{label} confidence</span>'


def probability_bar(home_pct: float, draw_pct: float, away_pct: float):
    """Single continuous tri-color bar. Each percentage is centered INSIDE
    its own segment — including the draw % sitting in the middle of the
    gray segment, regardless of how narrow that segment is."""
    home_color, draw_color, away_color = "#16a34a", "#475569", "#dc2626"
    home_mid = home_pct / 2
    draw_mid = home_pct + draw_pct / 2
    away_mid = home_pct + draw_pct + away_pct / 2

    st.markdown(
        f"""
        <div class="wc-prob-bar-wrap">
            <div class="wc-prob-seg" style="left:0%; width:{home_pct}%; background:{home_color};"></div>
            <div class="wc-prob-seg" style="left:{home_pct}%; width:{draw_pct}%; background:{draw_color};"></div>
            <div class="wc-prob-seg" style="left:{home_pct+draw_pct}%; width:{away_pct}%; background:{away_color};"></div>
            <span class="wc-prob-label" style="left:{home_mid}%;">{home_pct:.0f}%</span>
            <span class="wc-prob-label" style="left:{draw_mid}%;">{draw_pct:.0f}%</span>
            <span class="wc-prob-label" style="left:{away_mid}%;">{away_pct:.0f}%</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def match_datetime_str(match_row) -> str:
    date_str = match_row.get("date", "")
    time_str = match_row.get("kickoff_et")
    if isinstance(time_str, str) and time_str.strip():
        return f"{date_str} \u00b7 {time_str}"
    return str(date_str)


def match_card(match_row, team1, team2, compact: bool = False):
    st.markdown('<div class="wc-match-card">', unsafe_allow_html=True)

    when = match_datetime_str(match_row)
    venue = match_row.get("venue")
    meta_bits = [f"\U0001F4C5 {when}"]
    if isinstance(venue, str) and venue:
        meta_bits.append(f"\U0001F4CD {venue}")
    if match_row.get("group"):
        meta_bits.append(f"Group {match_row['group']}")
    st.markdown(f'<div class="wc-match-meta">{"&nbsp;&nbsp;|&nbsp;&nbsp;".join(meta_bits)}</div>',
                unsafe_allow_html=True)

    played = bool(match_row.get("played", False))
    if played:
        st.markdown(
            f"""<div class="wc-team-row">
                <span>{flag_img(team1.flag_url)}{team1.name}</span>
                <span style="opacity:0.95; font-weight:800; font-size:1.1rem;">
                    {int(match_row['home_goals'])} - {int(match_row['away_goals'])}</span>
                <span>{team2.name}{flag_img(team2.flag_url)}</span>
            </div>""",
            unsafe_allow_html=True,
        )
        st.markdown('<span class="wc-pill wc-pill-high">Played \u2014 final score</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        return

    st.markdown(
        f"""<div class="wc-team-row">
            <span>{flag_img(team1.flag_url)}{team1.name}</span>
            <span style="opacity:0.5; font-weight:400; font-size:0.85rem;">vs</span>
            <span>{team2.name}{flag_img(team2.flag_url)}</span>
        </div>""",
        unsafe_allow_html=True,
    )
    probability_bar(match_row["home_win_probability"] * 100, match_row["draw_probability"] * 100,
                     match_row["away_win_probability"] * 100)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(confidence_pill(match_row["confidence_label"]), unsafe_allow_html=True)
    with c2:
        if match_row["upset_risk_score"] >= 0.7:
            st.markdown(f'<span class="wc-upset">\u26a0 Upset potential ({match_row["upset_risk_score"]:.2f})</span>',
                         unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def circular_gauge(pct: float, label: str, flag_url: str = None, color: str = "#3b82f6"):
    pct_clamped = max(0, min(100, pct))
    gauge = f"""
    <div class="wc-gauge-wrap">
        <div class="wc-gauge" style="background: conic-gradient({color} {pct_clamped*3.6:.1f}deg, #1e293b 0deg);">
            <div class="wc-gauge-text">{pct_clamped:.0f}%</div>
        </div>
        <div class="wc-gauge-label">{flag_img(flag_url, 16) if flag_url else ""}{label}</div>
    </div>
    """
    st.markdown(gauge, unsafe_allow_html=True)


def ranked_bar(label_html: str, value: float, max_value: float, value_label: str, color: str = None):
    pct = 0 if max_value <= 0 else (value / max_value) * 100
    fill_style = f"background:{color};" if color else ""
    st.markdown(
        f"""<div class="wc-bar-row">
            <div style="width:150px; flex-shrink:0;">{label_html}</div>
            <div class="wc-bar-track"><div class="wc-bar-fill" style="width:{pct:.1f}%; {fill_style}"></div></div>
            <div style="width:48px; text-align:right; font-weight:700;">{value_label}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def schedule_row(stage: str, date: str, time: str, venue: str, city: str):
    """A fixture where the teams aren't known yet (Round of 32 onward, before
    group results are final) — show date/place only, no team names."""
    time_bit = f" \u00b7 {time}" if isinstance(time, str) and time and time != "TBD" else ""
    place_bit = f"{venue}, {city}" if venue else (city or "Venue TBD")
    st.markdown(
        f"""<div class="wc-match-card" style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-weight:700;">{stage}</span>
            <span style="color:#aab4c5; font-size:0.85rem;">\U0001F4C5 {date}{time_bit} &nbsp;|&nbsp; \U0001F4CD {place_bit}</span>
        </div>""",
        unsafe_allow_html=True,
    )


def bracket_match_box(match: dict, teams_by_name: dict):
    t1 = teams_by_name.get(match["team1"])
    t2 = teams_by_name.get(match["team2"])
    rows = []
    for team, prob in [(t1, match["prob1"]), (t2, match["prob2"])]:
        cls = "wc-bracket-winner" if team and team.name == match["winner"] else "wc-bracket-loser"
        flag = flag_img(team.flag_url, 16) if team else ""
        name = team.name if team else "?"
        rows.append(f'<div class="wc-bracket-team {cls}"><span>{flag}{name}</span><span>{prob*100:.0f}%</span></div>')
    st.markdown(f'<div class="wc-bracket-box">{"".join(rows)}</div>', unsafe_allow_html=True)
