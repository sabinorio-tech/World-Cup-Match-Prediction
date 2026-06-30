"""
Reusable, football-flavoured UI building blocks for the Streamlit app.
Keeps app.py focused on page composition rather than markup.
"""

from html import escape
from urllib.parse import quote

import pandas as pd
import streamlit as st

from src.utils.match_results import get_match_source_of_truth
from time_utils import belgian_kickoff

_FLAG_IMAGE_CODES = {
    "England": "gb-eng",
    "Scotland": "gb-sct",
    "Wales": "gb-wls",
    "Northern Ireland": "gb-nir",
}


def _flag_image_url(team, size: str = "w40") -> str | None:
    code = _FLAG_IMAGE_CODES.get(team.name) or getattr(team, "iso2", "")
    code = str(code).strip().lower()
    if not code:
        return None
    return f"https://flagcdn.com/{size}/{code}.png"


def _flag_image_html(team, class_name: str = "wc-team-flag-img") -> str:
    size = "w320" if class_name in {"wc-detail-team-flag", "wc-elo-flag", "wc-ta-hero-flag", "wc-ta-crest", "wc-feature-flag"} else "w40"
    url = _flag_image_url(team, size)
    if not url:
        return f'<span class="wc-team-flag">{team.flag}</span>'
    if class_name == "wc-detail-team-flag":
        return (
            f'<span class="{class_name}" role="img" aria-label="{team.name} flag" '
            f'style="background-image:url({url});"></span>'
        )
    return (
        f'<img class="{class_name}" '
        f'src="{url}" '
        f'alt="{team.name} flag" loading="lazy">'
    )


CSS = """
<style>
:root {
    --wc-midnight: #030812;
    --wc-ink: #06101b;
    --wc-pitch: #0a2f28;
    --wc-pitch-soft: rgba(17, 91, 62, .30);
    --wc-gold: #d7a83f;
    --wc-gold-soft: rgba(215, 168, 63, .24);
    --wc-red: #b92d35;
    --wc-red-soft: rgba(185, 45, 53, .20);
    --wc-blue: #174c78;
    --wc-line: rgba(231, 195, 96, .18);
}
html, body, [data-testid="stAppViewContainer"] {
    background:
        linear-gradient(115deg, rgba(185, 45, 53, .10) 0%, transparent 22%),
        linear-gradient(245deg, rgba(215, 168, 63, .16) 0%, transparent 24%),
        repeating-linear-gradient(90deg, rgba(255,255,255,.018) 0 1px, transparent 1px 72px),
        linear-gradient(135deg, var(--wc-midnight) 0%, var(--wc-ink) 34%, #071f1d 68%, #03070f 100%);
    color: #f5f7fb;
}

[data-testid="stAppViewContainer"] > .main {
    background: transparent;
}

.block-container {
    padding-top: 4.25rem;
    padding-bottom: 2rem;
    max-width: 1600px;
}

[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, rgba(7, 28, 24, 0.98), rgba(3, 9, 18, 0.99)),
        linear-gradient(145deg, rgba(215, 168, 63, .16), transparent 42%),
        linear-gradient(35deg, rgba(185, 45, 53, .13), transparent 44%);
    border-right: 1px solid var(--wc-line);
}

[data-testid="stSidebar"] * {
    color: #f5f7fb;
}

[data-testid="stRadio"] label {
    background: transparent;
    border-radius: 8px;
}

h1, h2, h3 {
    letter-spacing: 0;
}

.wc-page-title {
    font-size: 2rem;
    line-height: 1.05;
    font-weight: 800;
    text-transform: uppercase;
    margin: 0 0 4px 0;
    color: #ffffff;
}

.wc-page-header {
    display: flex;
    align-items: center;
    gap: 14px;
    min-width: 0;
}
.wc-page-emblem {
    width: 138px;
    height: 138px;
    object-fit: contain;
    flex: 0 0 auto;
    position: relative;
    top: -18px;
    filter: drop-shadow(0 8px 18px rgba(215, 168, 63, .24));
}
.wc-page-header-text {
    min-width: 0;
}

.wc-top-spacer {
    height: 44px;
}

.wc-page-subtitle {
    color: #d9bd6a;
    font-size: 0.92rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-top: 6px;
}

.wc-panel {
    background:
        linear-gradient(145deg, rgba(10, 35, 35, 0.94), rgba(5, 15, 27, 0.96)),
        linear-gradient(35deg, rgba(215, 168, 63, .08), transparent 40%);
    border: 1px solid rgba(215, 168, 63, 0.18);
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0 18px 50px rgba(0,0,0,0.22);
    min-height: 100%;
}

.wc-panel-title {
    color: #ffffff;
    font-weight: 800;
    font-size: 0.92rem;
    text-transform: uppercase;
    margin-bottom: 12px;
}

.wc-card {
    background:
        linear-gradient(135deg, rgba(12, 48, 58, 0.96) 0%, rgba(5, 19, 32, 0.98) 100%),
        linear-gradient(90deg, rgba(215, 168, 63, .10), transparent);
    border: 1px solid rgba(215, 168, 63, 0.22);
    border-radius: 8px;
    padding: 18px 20px;
    color: #f4f7f5;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.06), 0 12px 30px rgba(0,0,0,0.20);
    margin-bottom: 10px;
    min-height: 116px;
}
.wc-card-green { background: linear-gradient(135deg, rgba(12, 70, 44, 0.96), rgba(6, 38, 29, 0.96)); border-color: rgba(111, 198, 112, 0.30); }
.wc-card-purple { background: linear-gradient(135deg, rgba(46, 31, 70, 0.96), rgba(17, 13, 44, 0.96)); border-color: rgba(215, 168, 63, 0.30); }
.wc-card-gold { background: linear-gradient(135deg, rgba(91, 64, 13, 0.96), rgba(45, 30, 7, 0.96)); border-color: rgba(226, 184, 70, 0.42); }
.wc-kpi-label { font-size: 0.78rem; opacity: 0.86; text-transform: uppercase; letter-spacing: 0.04em; }
.wc-kpi-value { font-size: 1.75rem; font-weight: 800; margin-top: 8px; color: #ffffff; }
.wc-kpi-sub { font-size: 0.82rem; opacity: 0.85; margin-top: 5px; max-width: 14rem; }
.wc-kpi-icon { float: right; font-size: 2.5rem; opacity: 0.35; margin-top: -4px; }

.wc-match-card {
    background:
        linear-gradient(145deg, rgba(9, 39, 41, 0.76), rgba(7, 20, 33, 0.82));
    border: 1px solid rgba(215, 168, 63, 0.14);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 10px;
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
.wc-match-meta { margin-top: 8px; font-size: 0.78rem; opacity: 0.78; }

.wc-overview-hero {
    display: grid;
    grid-template-columns: minmax(0, 1.25fr) minmax(340px, .82fr);
    gap: 18px;
    margin-bottom: 14px;
}
.wc-overview-hero-left,
.wc-overview-next {
    border: 1px solid rgba(215, 168, 63, .20);
    border-radius: 8px;
    background:
        linear-gradient(112deg, rgba(4, 12, 23, .96), rgba(8, 31, 32, .74) 54%, rgba(4, 10, 18, .94)),
        linear-gradient(32deg, rgba(185,45,53,.14), transparent 40%);
    min-height: 276px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 22px 58px rgba(0,0,0,.30);
}
.wc-overview-hero-left {
    padding: 28px 34px;
}
.wc-overview-hero-left::before {
    content: "";
    position: absolute;
    inset: 0;
    background:
        radial-gradient(circle at 72% 44%, rgba(215,168,63,.30), transparent 18%),
        radial-gradient(circle at 72% 52%, rgba(17,91,62,.30), transparent 34%),
        repeating-linear-gradient(115deg, rgba(255,255,255,.05) 0 1px, transparent 1px 18px);
    opacity: .65;
}
.wc-overview-hero-title {
    position: relative;
    z-index: 1;
    font-size: clamp(2.25rem, 5vw, 4.25rem);
    line-height: .95;
    font-weight: 900;
    color: #ffffff;
    text-transform: uppercase;
    max-width: 520px;
}
.wc-overview-hero-subtitle {
    position: relative;
    z-index: 1;
    color: #78df49;
    font-size: 1rem;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: .08em;
    margin-top: 12px;
}
.wc-overview-copy {
    position: relative;
    z-index: 1;
    color: rgba(240,246,255,.86);
    max-width: 340px;
    line-height: 1.45;
    margin-top: 16px;
}
.wc-overview-trophy {
    position: absolute;
    right: 7%;
    bottom: -32px;
    width: min(32vw, 300px);
    max-height: 330px;
    object-fit: contain;
    filter: drop-shadow(0 20px 34px rgba(215,168,63,.28));
    z-index: 0;
}
.wc-live-chip {
    position: relative;
    z-index: 1;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin-top: 18px;
    padding: 8px 16px;
    border: 1px solid rgba(100,215,80,.38);
    border-radius: 999px;
    color: #f3fff1;
    font-weight: 900;
    text-transform: uppercase;
    font-size: .82rem;
    background: rgba(11, 35, 30, .68);
}
.wc-data-freshness {
    color: rgba(222, 233, 245, .62);
    font-size: .68rem;
    margin-top: 9px;
}
.wc-live-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #e73232;
    box-shadow: 0 0 14px rgba(231,50,50,.8);
}
.wc-progress-box {
    position: relative;
    z-index: 1;
    width: min(440px, 100%);
    margin-top: 16px;
    padding: 13px 16px;
    border-radius: 8px;
    background: rgba(3, 11, 20, .70);
    border: 1px solid rgba(215,168,63,.18);
}
.wc-progress-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: #70df49;
    font-weight: 900;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.wc-progress-value {
    color: #70df49;
    font-size: 1.65rem;
    line-height: 1;
}
.wc-progress-track {
    display: grid;
    grid-template-columns: repeat(18, 1fr);
    gap: 4px;
    margin-bottom: 8px;
}
.wc-progress-seg {
    height: 12px;
    transform: skewX(-18deg);
    background: rgba(114,135,155,.22);
}
.wc-progress-seg-on {
    background: linear-gradient(90deg, #62cb39, #a2e45d);
}
.wc-progress-meta {
    display: flex;
    justify-content: space-between;
    color: rgba(244,249,255,.86);
    font-size: .78rem;
    font-weight: 800;
    text-transform: uppercase;
}
.wc-overview-next {
    padding: 22px;
}
.wc-next-head {
    display: flex;
    justify-content: space-between;
    color: #7ee54f;
    text-transform: uppercase;
    font-weight: 900;
    font-size: .8rem;
    letter-spacing: .05em;
}
.wc-next-feature {
    display: grid;
    grid-template-columns: 1fr minmax(110px, .7fr) 1fr;
    align-items: center;
    gap: 16px;
    margin-top: 26px;
    text-align: center;
}
.wc-feature-flag {
    width: 126px;
    height: 84px;
    object-fit: cover;
    border-radius: 9px;
    box-shadow: 0 10px 24px rgba(0,0,0,.34), 0 0 0 1px rgba(255,255,255,.14);
}
.wc-feature-team {
    color: #ffffff;
    font-size: 1rem;
    font-weight: 900;
    text-transform: uppercase;
    margin-top: 12px;
}
.wc-feature-time {
    color: #ffffff;
}
.wc-feature-date {
    font-size: .76rem;
    font-weight: 900;
    text-transform: uppercase;
    color: rgba(243,247,255,.84);
}
.wc-feature-hour {
    font-size: 2.65rem;
    font-weight: 900;
    line-height: 1;
    margin-top: 8px;
}
.wc-feature-utc {
    font-size: .75rem;
    font-weight: 900;
    text-transform: uppercase;
    color: rgba(243,247,255,.82);
    margin-top: 4px;
}
.wc-feature-probs {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-top: 22px;
    padding-top: 16px;
    border-top: 1px solid rgba(255,255,255,.10);
}
.wc-feature-prob {
    text-align: center;
    color: rgba(235,244,255,.76);
    font-size: .72rem;
    text-transform: uppercase;
}
.wc-feature-prob strong {
    display: block;
    color: #ffffff;
    font-size: 1.55rem;
    line-height: 1;
    margin-bottom: 5px;
}
.wc-feature-prob-home strong { color: #70df49; }
.wc-feature-prob-away strong { color: #70a9ff; }
.wc-overview-kpis {
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 12px;
    margin: 14px 0;
}
.wc-overview-kpi {
    min-height: 96px;
    display: grid;
    grid-template-columns: 46px 1fr;
    gap: 13px;
    align-items: center;
    padding: 14px;
    border: 1px solid rgba(215,168,63,.16);
    border-radius: 8px;
    background: linear-gradient(135deg, rgba(10,34,37,.86), rgba(7,19,31,.92));
}
.wc-overview-kpi-icon {
    width: 46px;
    height: 46px;
    border-radius: 50%;
    display: grid;
    place-items: center;
    color: #ffffff;
    font-weight: 900;
    border: 1px solid currentColor;
    background: rgba(255,255,255,.06);
}
.wc-overview-kpi-value {
    color: #ffffff;
    font-size: 1.55rem;
    font-weight: 900;
    line-height: 1;
}
.wc-overview-kpi-label {
    color: rgba(239,246,255,.86);
    font-size: .72rem;
    text-transform: uppercase;
    font-weight: 800;
    margin-top: 5px;
}
.wc-overview-kpi-sub {
    color: rgba(221,232,245,.64);
    font-size: .70rem;
    margin-top: 2px;
}
.wc-overview-grid {
    display: grid;
    grid-template-columns: .95fr 1.4fr 1.2fr;
    gap: 14px;
    align-items: stretch;
}
.wc-overview-grid-bottom {
    display: grid;
    grid-template-columns: 1.1fr .95fr 1.05fr;
    gap: 14px;
    margin-top: 14px;
}
.wc-overview-panel {
    border: 1px solid rgba(215,168,63,.16);
    border-radius: 8px;
    background: linear-gradient(145deg, rgba(8,31,34,.88), rgba(5,17,30,.94));
    padding: 16px;
    min-height: 100%;
}
.wc-overview-panel-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: #75df48;
    font-size: .82rem;
    font-weight: 900;
    text-transform: uppercase;
    margin-bottom: 12px;
}
.wc-view-all {
    color: #7fe34f;
    font-size: .68rem;
    text-decoration: none;
    cursor: pointer;
}
.wc-view-all:hover {
    color: #ffffff;
    text-decoration: none;
}
.wc-overview-team-row {
    display: grid;
    grid-template-columns: 24px minmax(110px, 1fr) minmax(80px, 120px) 46px;
    gap: 10px;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid rgba(255,255,255,.07);
    color: #ffffff;
    font-size: .84rem;
    font-weight: 800;
}
.wc-overview-bar {
    height: 7px;
    border-radius: 999px;
    background: rgba(255,255,255,.10);
    overflow: hidden;
}
.wc-overview-bar span {
    display: block;
    width: var(--w);
    height: 100%;
    background: linear-gradient(90deg, #65c73b, #a4dc55);
}
.wc-overview-match-row,
.wc-overview-result-row {
    display: grid;
    grid-template-columns: 74px minmax(0, 1fr) minmax(154px, .9fr);
    gap: 10px;
    align-items: center;
    padding: 9px 0;
    border-bottom: 1px solid rgba(255,255,255,.07);
    color: #ffffff;
}
.wc-overview-result-row {
    grid-template-columns: 72px minmax(0, 1fr) 72px minmax(0, 1fr);
}
.wc-overview-match-date {
    color: rgba(233,242,255,.72);
    font-size: .72rem;
    font-weight: 800;
    text-transform: uppercase;
}
.wc-overview-match-teams,
.wc-overview-result-team {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
    font-weight: 900;
}
.wc-overview-match-teams span,
.wc-overview-result-team span {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.wc-overview-prob-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 6px;
}
.wc-overview-prob-chip {
    padding: 7px 5px;
    text-align: center;
    border-radius: 5px;
    color: #ffffff;
    font-size: .70rem;
    font-weight: 900;
    background: rgba(255,255,255,.08);
}
.wc-overview-prob-chip-home { background: rgba(54, 143, 64, .70); }
.wc-overview-prob-chip-draw { background: rgba(92, 104, 116, .72); }
.wc-overview-prob-chip-away { background: rgba(36, 82, 145, .72); }
.wc-overview-score {
    text-align: center;
    color: #ffffff;
    font-size: 1rem;
    font-weight: 900;
    padding: 7px 10px;
    border-radius: 5px;
    background: rgba(255,255,255,.08);
}
.wc-overview-donut-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(70px, 1fr));
    gap: 14px 10px;
}
.wc-overview-risk {
    min-height: 178px;
    background:
        linear-gradient(115deg, rgba(81, 54, 5, .92), rgba(8, 17, 25, .88)),
        radial-gradient(circle at 82% 52%, rgba(215,168,63,.35), transparent 28%);
    border-color: rgba(215,168,63,.40);
}
.wc-risk-layout {
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: center;
    gap: 18px;
    color: #ffffff;
}
.wc-risk-big {
    color: #efc24b;
    font-size: 2rem;
    font-weight: 900;
}
.wc-scorer-card {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 78px;
    gap: 14px;
    align-items: center;
    min-height: 116px;
}
.wc-scorer-name {
    color: #ffffff;
    font-weight: 900;
    font-size: 1.05rem;
}
.wc-scorer-meta {
    color: rgba(231,240,252,.72);
    font-size: .78rem;
    margin-top: 5px;
}
.wc-scorer-goals {
    color: #75df48;
    font-size: 2.7rem;
    font-weight: 900;
    text-align: center;
}
@media (max-width: 1100px) {
    .wc-overview-hero,
    .wc-overview-grid,
    .wc-overview-grid-bottom {
        grid-template-columns: 1fr;
    }
    .wc-overview-kpis {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

.wc-team-rank {
    display: grid;
    grid-template-columns: 24px 28px minmax(92px, 1fr) minmax(90px, 170px) 46px;
    gap: 10px;
    align-items: center;
    padding: 5px 0;
    font-size: 0.84rem;
}
.wc-team-flag {
    font-size: 1.05rem;
    line-height: 1;
}
.wc-team-flag-img {
    width: 24px;
    height: 16px;
    object-fit: cover;
    border-radius: 2px;
    box-shadow: 0 0 0 1px rgba(255,255,255,0.16);
}
.wc-rank-bar {
    height: 6px;
    border-radius: 999px;
    background: rgba(255,255,255,0.08);
    overflow: hidden;
}
.wc-rank-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, #5ca736, #98c94d);
}

.wc-donut-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(76px, 1fr));
    gap: 16px 18px;
}
.wc-donut-item { text-align: center; }
.wc-donut {
    --p: 50;
    width: 70px;
    height: 70px;
    margin: 0 auto 6px;
    border-radius: 50%;
    display: grid;
    place-items: center;
    background:
        radial-gradient(circle closest-side, #071827 69%, transparent 70% 100%),
        conic-gradient(#7fb345 calc(var(--p) * 1%), rgba(130, 169, 216, 0.22) 0);
    color: #ffffff;
    font-weight: 800;
}
.wc-donut-name {
    font-size: 0.82rem;
    color: #e8eef6;
}

.wc-compact-match {
    display: grid;
    grid-template-columns: 78px minmax(145px, 1fr) minmax(150px, 190px);
    gap: 10px;
    align-items: center;
    padding: 8px 10px;
    margin-bottom: 7px;
    border: 1px solid rgba(215, 168, 63, 0.13);
    border-radius: 8px;
    background: linear-gradient(135deg, rgba(10, 36, 36, 0.78), rgba(8, 23, 37, 0.78));
    font-size: 0.84rem;
}
.wc-compact-date {
    color: #a9bdd4;
    line-height: 1.2;
    font-weight: 700;
}
.wc-compact-date small {
    display: block;
    color: rgba(205, 221, 239, 0.62);
    font-weight: 500;
    margin-top: 3px;
}
.wc-compact-teams {
    display: grid;
    grid-template-columns: 1fr 26px 1fr;
    gap: 8px;
    align-items: center;
    color: #ffffff;
}
.wc-compact-team {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.wc-compact-vs {
    opacity: .72;
    text-align: center;
    font-weight: 700;
    font-size: .72rem;
}
.wc-compact-probs {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 5px;
    min-width: 0;
}
.wc-prob-chip {
    position: relative;
    overflow: hidden;
    background: rgba(255,255,255,0.075);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 5px;
    padding: 5px 4px;
    color: #dce8f4;
    font-size: 0.68rem;
    text-align: center;
    font-weight: 700;
}
.wc-prob-chip-fill {
    position: absolute;
    inset: 0 auto 0 0;
    width: var(--w);
    background: linear-gradient(90deg, rgba(91, 166, 50, 0.90), rgba(125, 196, 72, 0.82));
    opacity: .85;
}
.wc-prob-chip-fill-draw {
    background: linear-gradient(90deg, rgba(129, 145, 162, 0.92), rgba(172, 184, 196, 0.78));
}
.wc-prob-chip-fill-away {
    background: linear-gradient(90deg, rgba(58, 117, 185, 0.92), rgba(89, 153, 219, 0.78));
}
.wc-prob-chip span {
    position: relative;
    z-index: 1;
}
.wc-prob-chip-muted {
    background: rgba(136, 152, 170, 0.20);
}
.wc-prob-chip-away {
    background: rgba(45, 96, 150, 0.22);
    border-color: rgba(93, 160, 230, 0.22);
}

.wc-group-shell {
    background:
        linear-gradient(120deg, rgba(185, 45, 53, .10), transparent 34%),
        linear-gradient(245deg, rgba(215, 168, 63, .14), transparent 30%),
        linear-gradient(145deg, rgba(6, 29, 30, 0.98), rgba(2, 11, 20, 0.98));
    border: 1px solid rgba(215, 168, 63, 0.24);
    border-radius: 8px;
    padding: 18px;
    box-shadow: 0 22px 58px rgba(0,0,0,0.32);
}
.wc-group-title {
    color: #ffffff;
    font-size: 1.35rem;
    font-weight: 800;
    text-transform: uppercase;
    margin-bottom: 18px;
}
.wc-group-table {
    display: grid;
    gap: 0;
    overflow-x: auto;
}
.wc-group-row {
    display: grid;
    grid-template-columns: 32px minmax(180px, 1.8fr) repeat(8, minmax(44px, .42fr)) minmax(128px, .9fr);
    align-items: center;
    min-width: 780px;
    min-height: 40px;
    border-bottom: 1px solid rgba(130, 173, 222, 0.12);
    color: #f4f7fb;
    font-size: .84rem;
}
.wc-group-row:last-child {
    border-bottom: 0;
}
.wc-group-head {
    min-height: 34px;
    color: rgba(221, 232, 245, .78);
    font-size: .68rem;
    font-weight: 800;
    text-transform: uppercase;
}
.wc-group-team-cell {
    display: flex;
    align-items: center;
    gap: 9px;
    min-width: 0;
    font-weight: 800;
}
.wc-group-team-cell span:last-child {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.wc-group-flag-img {
    width: 30px;
    height: 20px;
    object-fit: cover;
    border-radius: 2px;
    box-shadow: 0 0 0 1px rgba(255,255,255,.16);
}
.wc-group-stat {
    text-align: center;
    font-weight: 700;
}
.wc-qual-cell {
    padding-left: 8px;
}
.wc-qual-bar {
    position: relative;
    height: 24px;
    overflow: hidden;
    border-radius: 4px;
    background: rgba(255,255,255,.08);
    border: 1px solid rgba(255,255,255,.08);
}
.wc-qual-fill {
    position: absolute;
    inset: 0 auto 0 0;
    width: var(--w);
    background: linear-gradient(90deg, #5ca736, #91c84c);
}
.wc-qual-cell span {
    position: relative;
    z-index: 1;
    display: block;
    text-align: right;
    padding: 3px 8px 0 0;
    font-size: .75rem;
    font-weight: 800;
    color: #ffffff;
}
.wc-group-mid {
    display: grid;
    grid-template-columns: 1.08fr .95fr;
    gap: 14px;
    margin-top: 16px;
}
.wc-points-row {
    display: grid;
    grid-template-columns: minmax(110px, .7fr) minmax(150px, 1.4fr) 42px;
    align-items: center;
    gap: 10px;
    margin: 10px 0;
    color: #ffffff;
    font-size: .82rem;
}
.wc-points-track {
    height: 22px;
    border-radius: 3px;
    background: rgba(255,255,255,.08);
    overflow: hidden;
}
.wc-points-fill {
    display: block;
    height: 100%;
    width: var(--w);
    border-radius: 3px;
}
.wc-axis {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    margin-left: calc(110px + 10px);
    color: rgba(221,232,245,.58);
    font-size: .72rem;
}
.wc-stat-line {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 14px;
    padding: 11px 0;
    border-bottom: 1px solid rgba(255,255,255,.08);
    color: #eaf1f8;
    font-size: .84rem;
}
.wc-stat-line:last-child {
    border-bottom: 0;
}
.wc-stat-value {
    font-weight: 800;
    color: #ffffff;
}
.wc-next-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
}
.wc-next-card {
    min-height: 82px;
    display: grid;
    align-content: center;
    gap: 8px;
    padding: 12px;
    border-radius: 8px;
    border: 1px solid rgba(130, 173, 222, 0.13);
    background: rgba(10, 27, 43, 0.76);
    color: #ffffff;
}
.wc-next-teams {
    display: grid;
    grid-template-columns: 1fr 24px 1fr;
    align-items: center;
    gap: 8px;
    font-size: .82rem;
    font-weight: 800;
}
.wc-next-team {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 7px;
    min-width: 0;
}
.wc-next-team span {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.wc-next-date {
    text-align: center;
    color: #dce8f4;
    font-size: .8rem;
    font-weight: 800;
}
.wc-next-status {
    text-align: center;
    color: rgba(221,232,245,.62);
    font-size: .68rem;
    text-transform: uppercase;
}

.wc-bracket-shell {
    background: transparent;
    border: 0;
    border-radius: 0;
    padding: 0;
    box-shadow: none;
}
.wc-bracket-tabs {
    display: grid;
    grid-template-columns: repeat(4, minmax(120px, 1fr));
    gap: 8px;
    max-width: 700px;
    margin: 0 auto 16px;
}
.wc-bracket-tab {
    text-align: center;
    padding: 8px 12px;
    border-radius: 6px;
    background: rgba(255,255,255,.06);
    border: 1px solid rgba(130, 173, 222, 0.08);
    color: rgba(235,243,252,.70);
    font-size: .78rem;
    font-weight: 800;
}
.wc-bracket-tab-active {
    color: #ffffff;
    background: linear-gradient(135deg, rgba(134, 92, 20, .92), rgba(40, 91, 61, .92));
    border-color: rgba(226, 184, 70, .35);
}
.wc-bracket-grid {
    display: grid;
    grid-template-columns: 1.15fr .92fr .88fr .82fr .72fr;
    gap: 22px;
    align-items: center;
}
.wc-bracket-col-title {
    color: rgba(235,243,252,.76);
    font-size: .7rem;
    font-weight: 800;
    text-transform: uppercase;
    margin: 0 0 8px 4px;
}
.wc-bracket-col {
    display: grid;
    gap: 10px;
}
.wc-bracket-col-r16 { gap: 32px; }
.wc-bracket-col-qf { gap: 74px; }
.wc-bracket-col-sf { gap: 152px; }
.wc-bracket-match {
    position: relative;
    border-radius: 7px;
    overflow: hidden;
    background: linear-gradient(135deg, rgba(13, 42, 39, .92), rgba(10, 24, 39, .96));
    border: 1px solid rgba(215, 168, 63, 0.15);
    box-shadow: inset 0 1px 0 rgba(255,255,255,.05);
}
.wc-bracket-team {
    display: grid;
    grid-template-columns: 34px 28px minmax(70px, 1fr) 42px;
    align-items: center;
    gap: 7px;
    min-height: 30px;
    padding: 4px 8px;
    border-bottom: 1px solid rgba(255,255,255,.07);
    color: #ffffff;
    font-size: .76rem;
}
.wc-bracket-team:last-child {
    border-bottom: 0;
}
.wc-bracket-slot {
    color: rgba(221,232,245,.62);
    font-weight: 800;
}
.wc-bracket-team-name {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-weight: 800;
}
.wc-bracket-prob {
    text-align: right;
    color: #dce8f4;
    font-weight: 800;
}
.wc-bracket-single {
    grid-template-columns: 28px minmax(90px, 1fr) 48px;
    min-height: 36px;
}
.wc-bracket-source {
    padding: 4px 8px;
    color: rgba(222, 233, 245, .68);
    font-size: .58rem;
    font-weight: 800;
    text-transform: uppercase;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.wc-bracket-source-actual {
    color: #9be36c;
    background: rgba(63, 139, 65, .12);
}
.wc-bracket-scroll {
    width: 100%;
    overflow-x: auto;
    padding: 6px 2px 14px;
    scrollbar-width: thin;
    scrollbar-color: rgba(215,168,63,.52) rgba(255,255,255,.05);
}
.wc-bracket-mirror {
    min-width: 2200px;
    min-height: 1280px;
    display: grid;
    grid-template-columns: 245px 225px 216px 208px 260px 208px 216px 225px 245px;
    gap: 22px;
    align-items: stretch;
}
.wc-bracket-mirror .wc-bracket-team {
    grid-template-columns: 32px 30px minmax(76px, 1fr) 46px;
    gap: 7px;
    min-height: 38px;
    padding: 7px 9px;
    font-size: .84rem;
}
.wc-bracket-mirror .wc-bracket-single {
    grid-template-columns: 30px minmax(82px, 1fr) 48px;
}
.wc-bracket-mirror .wc-group-flag-img {
    width: 30px;
    height: 20px;
}
.wc-bracket-mirror .wc-bracket-source {
    font-size: .64rem;
    padding: 6px 9px;
}
.wc-mirror-stage {
    min-height: 1280px;
    display: flex;
    flex-direction: column;
}
.wc-mirror-stage-title {
    min-height: 32px;
    display: grid;
    place-items: center;
    color: rgba(235,243,252,.72);
    font-size: .78rem;
    font-weight: 900;
    text-transform: uppercase;
}
.wc-mirror-stage-cards {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: space-around;
    gap: 8px;
}
.wc-mirror-match {
    position: relative;
}
.wc-mirror-match-number {
    color: rgba(222,233,245,.52);
    font-size: .66rem;
    font-weight: 900;
    text-transform: uppercase;
    margin: 0 0 3px 4px;
}
.wc-mirror-left .wc-mirror-match::after,
.wc-mirror-right .wc-mirror-match::before {
    content: "";
    position: absolute;
    top: 50%;
    width: 22px;
    height: 1px;
    background: rgba(196, 210, 224, .32);
}
.wc-mirror-left .wc-mirror-match::after { right: -22px; }
.wc-mirror-right .wc-mirror-match::before { left: -22px; }
.wc-mirror-center {
    min-height: 1280px;
    display: flex;
    flex-direction: column;
    align-items: stretch;
    justify-content: center;
    gap: 16px;
}
.wc-bracket-trophy-image {
    width: 132px;
    height: 190px;
    object-fit: contain;
    margin: 6px auto;
    filter: drop-shadow(0 18px 26px rgba(215,168,63,.28));
}
.wc-mirror-center .wc-bracket-winner {
    margin-top: 2px;
}
.wc-third-place-title {
    color: rgba(235,243,252,.64);
    font-size: .62rem;
    font-weight: 900;
    text-align: center;
    text-transform: uppercase;
    margin-top: 8px;
}
.wc-bracket-winner {
    background: linear-gradient(145deg, rgba(60, 44, 8, .96), rgba(22, 22, 12, .96));
    border: 1px solid rgba(218, 166, 40, .68);
    border-radius: 8px;
    padding: 14px;
    color: #ffffff;
    text-align: center;
}
.wc-trophy {
    font-size: 2.4rem;
    margin-bottom: 4px;
}
.wc-winner-title {
    color: #e7c359;
    font-weight: 800;
    text-transform: uppercase;
    font-size: .82rem;
    margin-bottom: 12px;
}
.wc-winner-main {
    display: grid;
    place-items: center;
    gap: 7px;
    font-size: 1.05rem;
    font-weight: 800;
    margin-bottom: 10px;
}
.wc-winner-list {
    display: grid;
    gap: 8px;
    margin-top: 10px;
}
.wc-winner-row {
    display: grid;
    grid-template-columns: 28px 1fr 42px;
    gap: 8px;
    align-items: center;
    text-align: left;
    font-size: .76rem;
}
.wc-title-card-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
}
.wc-title-card {
    display: grid;
    grid-template-columns: 42px 1fr;
    gap: 12px;
    align-items: center;
    min-height: 84px;
    padding: 12px;
    background: rgba(12, 30, 48, .76);
    border: 1px solid rgba(130, 173, 222, 0.15);
    border-radius: 8px;
    color: #ffffff;
}
.wc-title-rank {
    height: 58px;
    border-radius: 6px;
    display: grid;
    place-items: center;
    font-size: 1.35rem;
    font-weight: 800;
    background: rgba(255,255,255,.08);
}
.wc-title-card:first-child {
    background: linear-gradient(135deg, rgba(27, 73, 124, .88), rgba(12, 36, 70, .88));
    border-color: rgba(113, 169, 232, .32);
}
.wc-title-team {
    font-weight: 800;
    margin-bottom: 8px;
}
.wc-title-prob {
    font-size: 1.2rem;
    font-weight: 800;
}

.wc-team-stats-grid {
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 12px;
}
.wc-team-stat-card {
    min-height: 150px;
    position: relative;
    overflow: hidden;
    border-radius: 8px;
    padding: 14px;
    background: linear-gradient(135deg, rgba(9, 36, 66, .96), rgba(5, 20, 38, .98));
    border: 1px solid rgba(118, 165, 224, .22);
    color: #ffffff;
}
.wc-team-stat-card-green { background: linear-gradient(135deg, rgba(13, 56, 35, .96), rgba(7, 41, 26, .96)); border-color: rgba(93, 181, 102, .28); }
.wc-team-stat-card-purple { background: linear-gradient(135deg, rgba(33, 22, 66, .96), rgba(17, 13, 44, .96)); border-color: rgba(135, 90, 218, .32); }
.wc-team-stat-card-gold { background: linear-gradient(135deg, rgba(78, 55, 10, .96), rgba(44, 31, 5, .96)); border-color: rgba(214, 166, 54, .32); }
.wc-team-stat-card-blue { background: linear-gradient(135deg, rgba(8, 48, 82, .96), rgba(5, 24, 44, .96)); border-color: rgba(71, 142, 219, .28); }
.wc-team-stat-card::after {
    content: "";
    position: absolute;
    right: -30px;
    bottom: -48px;
    width: 126px;
    height: 126px;
    border-radius: 50%;
    background: rgba(255,255,255,.05);
}
.wc-team-stat-label {
    color: rgba(234, 244, 252, .82);
    font-size: .72rem;
    font-weight: 800;
    text-transform: uppercase;
}
.wc-team-stat-value {
    font-size: 1.85rem;
    font-weight: 800;
    margin: 16px 0 4px;
}
.wc-team-stat-name {
    font-weight: 800;
    margin-top: 12px;
}
.wc-team-stat-sub {
    color: rgba(234, 244, 252, .82);
    font-size: .78rem;
    margin-top: 8px;
}
.wc-team-stat-flag {
    position: absolute;
    right: 14px;
    bottom: 16px;
    width: 54px;
    height: 36px;
    object-fit: cover;
    border-radius: 4px;
    box-shadow: 0 10px 28px rgba(0,0,0,.28), 0 0 0 1px rgba(255,255,255,.18);
}
.wc-team-dashboard-grid {
    display: grid;
    grid-template-columns: 1.45fr .95fr .9fr;
    gap: 14px;
    margin-top: 14px;
}
.wc-team-table {
    display: grid;
    gap: 0;
}
.wc-team-table-row {
    display: grid;
    grid-template-columns: 28px minmax(130px, 1.3fr) 54px 40px 40px 44px 52px 58px;
    gap: 8px;
    align-items: center;
    min-height: 32px;
    border-bottom: 1px solid rgba(255,255,255,.07);
    color: #eef6ff;
    font-size: .78rem;
}
.wc-team-table-row:last-child { border-bottom: 0; }
.wc-team-table-head {
    color: rgba(221,232,245,.62);
    text-transform: uppercase;
    font-size: .64rem;
    font-weight: 800;
}
.wc-team-table-team {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
    font-weight: 800;
}
.wc-team-table-team span:last-child {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.wc-elo-layout {
    display: grid;
    grid-template-columns: minmax(0, 1.45fr) minmax(320px, .85fr);
    gap: 14px;
}
.wc-elo-table {
    display: grid;
    gap: 0;
}
.wc-elo-table-row {
    display: grid;
    grid-template-columns: 38px minmax(170px, 1fr) 86px 64px 74px 82px 110px;
    gap: 10px;
    align-items: center;
    min-height: 38px;
    border-bottom: 1px solid rgba(255,255,255,.07);
    color: #eef6ff;
    font-size: .82rem;
}
.wc-elo-table-row:last-child { border-bottom: 0; }
.wc-elo-table-head {
    color: rgba(221,232,245,.62);
    text-transform: uppercase;
    font-size: .64rem;
    font-weight: 800;
}
.wc-elo-table-selected {
    background: rgba(98, 164, 225, .13);
    border-radius: 6px;
    border-bottom-color: transparent;
    box-shadow: inset 3px 0 0 rgba(119, 181, 239, .85);
}
.wc-elo-team {
    display: flex;
    align-items: center;
    gap: 9px;
    min-width: 0;
    font-weight: 800;
}
.wc-elo-team span:last-child {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.wc-elo-bar {
    height: 8px;
    border-radius: 999px;
    background: rgba(255,255,255,.08);
    overflow: hidden;
}
.wc-elo-fill {
    display: block;
    width: var(--w);
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, #5ca736, #9cca4f);
}
.wc-elo-profile {
    display: grid;
    gap: 12px;
}
.wc-elo-hero {
    min-height: 178px;
    position: relative;
    overflow: hidden;
    border-radius: 8px;
    padding: 16px;
    border: 1px solid rgba(118, 165, 224, .22);
    background: linear-gradient(135deg, rgba(8, 48, 82, .96), rgba(5, 24, 44, .96));
}
.wc-elo-hero::after {
    content: "";
    position: absolute;
    right: -38px;
    bottom: -52px;
    width: 150px;
    height: 150px;
    border-radius: 50%;
    background: rgba(255,255,255,.05);
}
.wc-elo-flag {
    position: absolute;
    right: 16px;
    top: 18px;
    width: 72px;
    height: 48px;
    object-fit: cover;
    border-radius: 5px;
    box-shadow: 0 12px 28px rgba(0,0,0,.30), 0 0 0 1px rgba(255,255,255,.20);
}
.wc-elo-rank-label {
    color: rgba(234, 244, 252, .74);
    font-size: .72rem;
    font-weight: 800;
    text-transform: uppercase;
}
.wc-elo-country {
    color: #ffffff;
    font-size: 1.45rem;
    font-weight: 800;
    margin-top: 8px;
    max-width: calc(100% - 96px);
}
.wc-elo-value {
    color: #ffffff;
    font-size: 2.05rem;
    font-weight: 800;
    margin-top: 14px;
}
.wc-elo-sub {
    color: rgba(234, 244, 252, .80);
    font-size: .82rem;
    margin-top: 6px;
}
.wc-elo-kpi-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
}
.wc-elo-kpi {
    border: 1px solid rgba(130, 173, 222, .15);
    border-radius: 8px;
    padding: 12px;
    background: rgba(13, 31, 49, .72);
}
.wc-elo-kpi-label {
    color: rgba(221,232,245,.68);
    font-size: .66rem;
    font-weight: 800;
    text-transform: uppercase;
}
.wc-elo-kpi-value {
    color: #ffffff;
    font-size: 1.08rem;
    font-weight: 800;
    margin-top: 7px;
}
.wc-ta-shell {
    display: grid;
    grid-template-columns: 250px minmax(0, 1.42fr) minmax(330px, .92fr);
    gap: 16px;
    align-items: start;
}
.wc-ta-shell-no-side {
    grid-template-columns: minmax(0, 1.42fr) minmax(330px, .92fr);
}
.wc-native-team-title {
    color: rgba(234, 244, 252, .82);
    font-size: .76rem;
    font-weight: 900;
    text-transform: uppercase;
    margin: 2px 0 9px;
}
.wc-native-team-flag {
    display: block;
    width: 28px;
    height: 18px;
    object-fit: cover;
    border-radius: 2px;
    box-shadow: 0 0 0 1px rgba(255,255,255,.16);
    margin: 0 auto;
}
.st-key-team_selector div[data-testid="stButton"] button {
    min-height: 36px;
    padding: 5px 8px;
    border-radius: 6px;
}
.st-key-team_selector div[data-testid="stButton"] button p {
    text-align: left;
    font-size: .76rem;
    white-space: normal;
}
.wc-ta-panel {
    background:
        linear-gradient(145deg, rgba(9, 35, 35, .94), rgba(5, 17, 30, .96)),
        linear-gradient(35deg, rgba(215, 168, 63, .07), transparent 42%);
    border: 1px solid rgba(215, 168, 63, .18);
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0 18px 50px rgba(0,0,0,.22);
}
.wc-ta-side {
    position: sticky;
    top: 86px;
}
.wc-ta-side-label,
.wc-ta-section-title,
.wc-ta-performer-label {
    color: rgba(234, 244, 252, .78);
    font-size: .72rem;
    font-weight: 800;
    text-transform: uppercase;
}
.wc-ta-selected-box {
    display: flex;
    align-items: center;
    gap: 10px;
    border: 1px solid rgba(130, 173, 222, .18);
    background: rgba(12, 30, 49, .88);
    border-radius: 7px;
    padding: 10px;
    margin: 10px 0 16px;
    color: #ffffff;
    font-weight: 800;
}
.wc-ta-list {
    display: grid;
    gap: 3px;
    margin-top: 10px;
    max-height: calc(100vh - 230px);
    min-height: 360px;
    overflow-y: auto;
    overscroll-behavior: contain;
    padding-right: 5px;
    scrollbar-width: thin;
    scrollbar-color: rgba(117, 223, 72, .52) rgba(255,255,255,.05);
}
.wc-ta-list::-webkit-scrollbar {
    width: 7px;
}
.wc-ta-list::-webkit-scrollbar-track {
    background: rgba(255,255,255,.04);
    border-radius: 8px;
}
.wc-ta-list::-webkit-scrollbar-thumb {
    background: rgba(117, 223, 72, .48);
    border-radius: 8px;
}
.wc-ta-list-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    min-height: 34px;
    border-radius: 6px;
    padding: 7px 9px;
    color: #eaf2fb;
    font-size: .84rem;
    font-weight: 700;
    text-decoration: none;
    transition: background .16s ease, color .16s ease;
}
.wc-ta-list-row:hover {
    color: #ffffff;
    text-decoration: none;
    background: rgba(255,255,255,.08);
}
.wc-ta-list-row-active {
    background: color-mix(in srgb, var(--team-primary, #54b150) 25%, transparent);
    box-shadow: inset 3px 0 0 var(--team-accent, #6fd34e);
}
.wc-ta-list-team {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
}
.wc-ta-list-team span:last-child {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.wc-ta-active-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--team-accent, #6fd34e);
    flex: 0 0 auto;
}
.wc-ta-main,
.wc-ta-right {
    display: grid;
    gap: 16px;
}
.wc-ta-hero {
    min-height: 236px;
    position: relative;
    overflow: hidden;
    border-radius: 8px;
    padding: 34px 34px;
    border: 1px solid rgba(130, 173, 222, .18);
    background:
        linear-gradient(110deg, var(--team-primary, rgba(105, 17, 24, .88)), rgba(8, 23, 41, .72) 58%, var(--team-secondary, rgba(5, 14, 26, .92))),
        radial-gradient(circle at 68% 18%, rgba(255,255,255,.22), transparent 12%),
        linear-gradient(0deg, rgba(255,255,255,.08) 0 1px, transparent 1px 100%),
        linear-gradient(90deg, rgba(255,255,255,.06) 0 1px, transparent 1px 100%);
    background-size: auto, auto, 44px 44px, 44px 44px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,.06);
}
.wc-ta-hero::before {
    content: "";
    position: absolute;
    inset: auto -8% 0 -8%;
    height: 80px;
    background: radial-gradient(ellipse at center, var(--team-glow, rgba(87, 139, 67, .34)), rgba(16, 49, 31, .18) 45%, transparent 72%);
}
.wc-ta-hero::after {
    content: "";
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at 16% 24%, rgba(255,255,255,.12), transparent 26%);
    pointer-events: none;
}
.wc-ta-hero-content {
    position: relative;
    z-index: 1;
    display: grid;
    grid-template-columns: 120px 1fr;
    gap: 28px;
    align-items: center;
}
.wc-ta-hero-flag {
    width: 112px;
    height: 112px;
    object-fit: contain;
    border-radius: 0;
    background: transparent;
    box-shadow: none;
}
.wc-ta-country {
    color: #ffffff;
    font-size: 2.55rem;
    line-height: 1;
    font-weight: 900;
}
.wc-ta-meta-grid {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 16px;
    margin-top: 28px;
}
.wc-ta-meta-item {
    border-left: 1px solid rgba(255,255,255,.10);
    padding-left: 14px;
}
.wc-ta-meta-item:first-child {
    border-left: 0;
    padding-left: 0;
}
.wc-ta-meta-label {
    color: rgba(238, 246, 255, .78);
    font-size: .78rem;
}
.wc-ta-meta-value {
    color: var(--team-accent, #67e05b);
    font-size: 1.35rem;
    font-weight: 900;
    margin-top: 8px;
}
.wc-ta-meta-value-muted {
    color: #ffffff;
}
.wc-ta-performer-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(175px, 1fr));
    gap: 10px;
}
.wc-ta-performer {
    min-height: 132px;
    border: 1px solid rgba(130, 173, 222, .15);
    border-radius: 8px;
    padding: 12px;
    background: rgba(10, 29, 48, .74);
    position: relative;
    overflow: hidden;
}
.wc-ta-performer-top {
    display: block;
    min-height: 32px;
}
.wc-ta-performer-top .wc-ta-performer-label {
    color: rgba(239, 246, 255, .88);
    line-height: 1.3;
    white-space: normal;
    overflow-wrap: anywhere;
}
.wc-ta-position-pill {
    display: inline-flex;
    align-items: center;
    min-height: 20px;
    padding: 2px 7px;
    border-radius: 999px;
    background: rgba(255,255,255,.10);
    border: 1px solid rgba(255,255,255,.13);
    color: rgba(235,244,255,.82);
    font-size: .68rem;
    font-weight: 800;
    text-transform: uppercase;
}
.wc-ta-performer-name {
    color: #ffffff;
    font-size: 1.02rem;
    font-weight: 900;
    line-height: 1.3;
    min-height: 2.6em;
    margin: 12px 0 8px;
    white-space: normal;
    overflow: visible;
    overflow-wrap: anywhere;
}
.wc-ta-performer-value {
    color: var(--team-accent, #71df55);
    font-size: 1.55rem;
    line-height: 1;
    font-weight: 900;
}
.wc-ta-performer-stat {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 7px;
}
.wc-ta-performer-number {
    display: flex;
    align-items: baseline;
    gap: 5px;
    min-width: 0;
}
.wc-ta-performer-unit {
    color: rgba(235, 244, 255, .78);
    font-size: .75rem;
    white-space: nowrap;
}
.wc-ta-outlook-row {
    margin: 0 0 18px;
}
.wc-ta-outlook-head {
    display: flex;
    justify-content: space-between;
    color: #ffffff;
    font-weight: 800;
    font-size: .88rem;
    margin-bottom: 8px;
}
.wc-ta-track {
    height: 7px;
    border-radius: 999px;
    background: rgba(255,255,255,.08);
    overflow: hidden;
}
.wc-ta-fill {
    display: block;
    width: var(--w);
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, #4faf47, #9bd34c);
}
.wc-ta-fill-gold {
    background: linear-gradient(90deg, #d4a82d, #8cb83f);
}
.wc-ta-overview-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
}
.wc-ta-overview-card {
    min-height: 96px;
    border: 1px solid rgba(130, 173, 222, .15);
    border-radius: 8px;
    padding: 14px;
    background: rgba(10, 29, 48, .70);
}
.wc-ta-overview-label {
    color: rgba(221,232,245,.70);
    font-size: .75rem;
}
.wc-ta-overview-value {
    color: #ffffff;
    font-size: 1.55rem;
    font-weight: 900;
    margin-top: 10px;
}
.wc-ta-overview-sub {
    color: rgba(221,232,245,.66);
    font-size: .74rem;
    margin-top: 6px;
}
.wc-ta-record {
    min-height: 150px;
    position: relative;
    overflow: hidden;
    display: grid;
    grid-template-columns: 1fr 96px;
    align-items: center;
    gap: 14px;
    background: linear-gradient(120deg, rgba(11, 31, 53, .94), var(--team-primary, rgba(82, 15, 32, .82)));
}
.wc-ta-crest {
    width: 86px;
    height: 58px;
    object-fit: contain;
    border-radius: 0;
    background: transparent;
    box-shadow: none;
}
.wc-ta-record-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 18px;
}
.wc-ta-record-value {
    color: var(--team-accent, #baf3a5);
    font-size: 1.35rem;
    font-weight: 900;
    margin-bottom: 6px;
}
.wc-ta-match-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
}
.wc-ta-match-card {
    border: 1px solid rgba(130, 173, 222, .15);
    border-radius: 8px;
    padding: 12px;
    background: rgba(10, 29, 48, .70);
}
.wc-ta-match-meta {
    color: rgba(221,232,245,.62);
    font-size: .7rem;
    display: flex;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 12px;
}
.wc-ta-match-line {
    display: grid;
    grid-template-columns: 1fr 56px 1fr;
    align-items: center;
    gap: 8px;
    color: #ffffff;
    font-weight: 800;
    font-size: .78rem;
}
.wc-ta-match-team {
    display: flex;
    align-items: center;
    gap: 6px;
    min-width: 0;
}
.wc-ta-match-team span:last-child {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.wc-ta-score {
    text-align: center;
    color: #ffffff;
    font-size: 1rem;
    font-weight: 900;
    white-space: nowrap;
}
.wc-team-impact-row {
    display: grid;
    grid-template-columns: 28px minmax(110px, 1fr) minmax(110px, 1.2fr) 48px;
    gap: 8px;
    align-items: center;
    min-height: 34px;
    color: #ffffff;
    font-size: .78rem;
}
.wc-team-impact-bar {
    height: 8px;
    border-radius: 999px;
    background: rgba(255,255,255,.08);
    overflow: hidden;
}
.wc-team-impact-fill {
    display: block;
    height: 100%;
    width: var(--w);
    background: linear-gradient(90deg, #67ad3b, #9cca4f);
    border-radius: 999px;
}
.wc-team-bars {
    display: grid;
    gap: 12px;
}
.wc-team-bar-row {
    display: grid;
    grid-template-columns: minmax(100px, .9fr) 1fr 32px;
    gap: 10px;
    align-items: center;
    color: #ffffff;
    font-size: .78rem;
}
.wc-team-bar-track {
    height: 13px;
    border-radius: 4px;
    background: rgba(255,255,255,.08);
    overflow: hidden;
}
.wc-team-bar-fill {
    display: block;
    height: 100%;
    width: var(--w);
    background: linear-gradient(90deg, #5ca736, #91c84c);
    border-radius: 4px;
}
.wc-mini-panel-grid {
    display: grid;
    grid-template-columns: 1.25fr .7fr 1fr;
    gap: 12px;
    margin-top: 14px;
}
.wc-team-donut-row {
    display: grid;
    grid-template-columns: repeat(5, minmax(64px, 1fr));
    gap: 10px;
}
.wc-team-note {
    color: rgba(221,232,245,.72);
    font-size: .75rem;
    margin-top: 12px;
}
@media (max-width: 1100px) {
    .wc-bracket-grid {
        grid-template-columns: 1fr;
    }
    .wc-bracket-col,
    .wc-bracket-col-r16,
    .wc-bracket-col-qf,
    .wc-bracket-col-sf,
    .wc-title-card-grid,
    .wc-team-stats-grid,
    .wc-team-dashboard-grid,
    .wc-mini-panel-grid,
    .wc-elo-layout,
    .wc-ta-shell,
    .wc-ta-performer-grid,
    .wc-ta-match-grid {
        grid-template-columns: 1fr;
        gap: 10px;
    }
    .wc-ta-side {
        position: static;
    }
    .wc-ta-meta-grid,
    .wc-ta-overview-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .wc-elo-table-row {
        grid-template-columns: 34px minmax(130px, 1fr) 58px 64px 82px;
    }
    .wc-elo-table-row > div:nth-child(4),
    .wc-elo-table-row > div:nth-child(5) {
        display: none;
    }
}
@media (max-width: 900px) {
    .wc-group-mid,
    .wc-next-grid {
        grid-template-columns: 1fr;
    }
}

.wc-schedule-heading {
    color: #ffffff;
    font-size: .82rem;
    font-weight: 900;
    text-transform: uppercase;
    margin: 2px 0 9px;
}
.wc-schedule-date {
    color: #75df48;
    font-size: .75rem;
    font-weight: 900;
    text-transform: uppercase;
    padding: 7px 2px 3px;
}
div[data-testid="stVerticalBlockBorderWrapper"] button {
    min-height: 48px;
    border-radius: 6px;
}
div[data-testid="stVerticalBlockBorderWrapper"] button p {
    width: 100%;
    text-align: left;
    font-size: .72rem;
    line-height: 1.25;
    white-space: normal;
}

.wc-detail-shell {
    background:
        linear-gradient(120deg, rgba(185, 45, 53, .12), transparent 35%),
        linear-gradient(245deg, rgba(18, 92, 62, .22), transparent 32%),
        linear-gradient(145deg, rgba(5, 18, 31, 0.98), rgba(2, 11, 20, 0.98));
    border: 1px solid rgba(215, 168, 63, 0.24);
    border-radius: 8px;
    padding: 18px;
    box-shadow: 0 22px 58px rgba(0,0,0,0.32);
}
.wc-detail-back {
    color: #c5d6e8;
    font-size: .82rem;
    margin-bottom: 8px;
}
.wc-detail-head {
    text-align: center;
    margin-bottom: 12px;
}
.wc-detail-title {
    color: #ffffff;
    font-size: 1rem;
    font-weight: 800;
    text-transform: uppercase;
}
.wc-detail-meta {
    color: #b8c6d6;
    font-size: .82rem;
    margin-top: 6px;
}
.wc-detail-teams {
    display: grid;
    grid-template-columns: minmax(120px, 1fr) minmax(260px, 1.35fr) minmax(120px, 1fr);
    align-items: center;
    gap: 16px;
    margin: 8px 0 16px;
}
.wc-detail-team {
    text-align: center;
    color: #ffffff;
    font-weight: 800;
    text-transform: uppercase;
}
.wc-detail-elo {
    color: rgba(203, 216, 229, .78);
    font-size: .74rem;
    font-weight: 700;
    margin-top: 5px;
    text-transform: none;
}
.wc-detail-team-flag {
    display: block;
    width: 216px;
    height: 144px;
    border-radius: 8px;
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    box-shadow: 0 8px 22px rgba(0,0,0,.28), 0 0 0 1px rgba(255,255,255,.18);
    margin: 0 auto 12px;
}
.wc-detail-vs {
    text-align: center;
}
.wc-detail-vs-text {
    color: #ffffff;
    font-size: 1.75rem;
    font-weight: 800;
    margin-bottom: 10px;
}
.wc-detail-prob-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(80px, 1fr));
    gap: 8px;
}
.wc-detail-prob {
    border-radius: 7px;
    padding: 10px 8px;
    color: #ffffff;
    box-shadow: inset 0 1px 0 rgba(255,255,255,.08);
    border: 1px solid rgba(255,255,255,.12);
}
.wc-detail-prob-home { background: linear-gradient(135deg, rgba(70, 126, 192, .95), rgba(42, 80, 130, .95)); }
.wc-detail-prob-draw { background: linear-gradient(135deg, rgba(72, 79, 87, .95), rgba(42, 48, 55, .95)); }
.wc-detail-prob-away { background: linear-gradient(135deg, rgba(30, 97, 55, .95), rgba(15, 69, 39, .95)); }
.wc-detail-prob-value {
    font-size: 1.55rem;
    font-weight: 800;
    line-height: 1;
}
.wc-detail-prob-label {
    font-size: .67rem;
    font-weight: 800;
    text-transform: uppercase;
    opacity: .88;
    margin-top: 6px;
}
.wc-detail-confidence {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    color: #b8c6d6;
    font-size: .75rem;
    margin-bottom: 18px;
}
.wc-detail-confidence-track {
    width: min(180px, 36vw);
    height: 6px;
    border-radius: 999px;
    background: rgba(255,255,255,.16);
    overflow: hidden;
}
.wc-detail-confidence-fill {
    display: block;
    height: 100%;
    width: var(--w);
    background: linear-gradient(90deg, #6fa8dc, #9fd4ff);
}
.wc-detail-score-feature {
    max-width: 420px;
    margin: 0 auto;
    padding: 15px 22px;
    text-align: center;
    border: 1px solid rgba(117, 223, 72, .28);
    border-radius: 8px;
    background: linear-gradient(135deg, rgba(23, 76, 120, .25), rgba(13, 49, 38, .68));
}
.wc-score-model-note {
    color: rgba(203, 216, 229, .68);
    font-size: .7rem;
    margin-top: 8px;
}
.wc-score-comparison {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
}
.wc-score-comparison > div {
    padding: 2px 18px;
}
.wc-score-comparison > div + div {
    border-left: 1px solid rgba(255,255,255,.13);
}
.wc-score-comparison-label {
    color: rgba(226, 236, 246, .74);
    font-size: .68rem;
    font-weight: 900;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.wc-score-big-predicted {
    color: #75df48;
}
.wc-factor-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    border-top: 1px solid rgba(255,255,255,.08);
}
.wc-factor {
    text-align: center;
    padding: 12px 10px;
    border-left: 1px solid rgba(255,255,255,.08);
}
.wc-factor:first-child { border-left: 0; }
.wc-factor-label {
    color: #c6d1de;
    font-size: .68rem;
    font-weight: 800;
    text-transform: uppercase;
}
.wc-factor-value {
    color: #ffffff;
    font-size: 1.12rem;
    font-weight: 800;
    margin: 8px 0;
}
.wc-form-row {
    display: flex;
    justify-content: center;
    gap: 4px;
    margin: 8px 0;
}
.wc-form-chip {
    min-width: 18px;
    height: 18px;
    border-radius: 3px;
    background: #4c9d39;
    color: #ffffff;
    display: inline-grid;
    place-items: center;
    font-size: .68rem;
    font-weight: 800;
}
.wc-form-chip-D { background: #7f8b92; }
.wc-form-chip-L { background: #a74a45; }
.wc-factor-sub {
    color: #aebdcc;
    font-size: .72rem;
    line-height: 1.35;
}
.wc-detail-bottom {
    display: grid;
    grid-template-columns: .8fr 1.05fr 1.35fr;
    gap: 12px;
    margin-top: 14px;
}
.wc-detail-bottom-two {
    grid-template-columns: .85fr 1.15fr;
}
.wc-detail-bottom-three {
    grid-template-columns: repeat(3, minmax(0, 1fr));
}
.wc-detail-mini {
    background: rgba(13, 31, 49, .72);
    border: 1px solid rgba(130, 173, 222, .16);
    border-radius: 8px;
    padding: 14px;
}
.wc-detail-mini-title {
    color: #ffffff;
    font-size: .8rem;
    font-weight: 800;
    text-transform: uppercase;
    padding-bottom: 10px;
    margin-bottom: 12px;
    border-bottom: 1px solid rgba(255,255,255,.08);
}
.wc-score-big {
    color: #ffffff;
    font-size: 1.75rem;
    font-weight: 800;
    text-align: center;
}
.wc-score-sub {
    color: #cbd8e5;
    text-align: center;
    font-size: .82rem;
    margin-top: 8px;
}
.wc-xg-grid {
    display: grid;
    grid-template-columns: 1fr 42px 1fr;
    align-items: center;
    text-align: center;
    color: #ffffff;
}
.wc-xg-value {
    font-size: 1.35rem;
    font-weight: 800;
}
.wc-xg-ball {
    width: 34px;
    height: 34px;
    margin: 0 auto;
    border-radius: 50%;
    display: grid;
    place-items: center;
    background: rgba(255,255,255,.08);
    color: rgba(255,255,255,.35);
}
.wc-xg-team {
    color: #cbd8e5;
    font-size: .75rem;
    margin-top: 8px;
}
.wc-prob-svg {
    width: 100%;
    height: 118px;
}
.wc-detail-shell-compact {
    padding: 16px;
}
.wc-detail-shell-compact .wc-detail-back {
    display: none;
}
.wc-detail-shell-compact .wc-detail-teams {
    grid-template-columns: minmax(90px, .75fr) minmax(230px, 1.5fr) minmax(90px, .75fr);
    gap: 10px;
}
.wc-detail-shell-compact .wc-detail-team-flag {
    width: 132px;
    height: 88px;
}
.wc-detail-shell-compact .wc-detail-prob-value {
    font-size: 1.32rem;
}
.wc-detail-shell-compact .wc-detail-prob-label {
    font-size: .59rem;
}
.wc-detail-shell-compact .wc-detail-score-feature {
    max-width: 360px;
}
@media (max-width: 900px) {
    .wc-detail-teams,
    .wc-detail-bottom,
    .wc-factor-grid {
        grid-template-columns: 1fr;
    }
    .wc-factor {
        border-left: 0;
        border-top: 1px solid rgba(255,255,255,.08);
    }
}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def _compact_html(html: str) -> str:
    return "".join(line.strip() for line in html.splitlines() if line.strip())


def fifa_overview_dashboard(
    matches,
    teams: list,
    round_reach,
    player_stats=None,
    knockout_matches=None,
    next_match: dict | None = None,
    trophy_src: str = "",
    data_updated: str = "Unavailable",
):
    teams_by_name = {team.name: team for team in teams}
    group_played = matches[matches["played"]].copy()
    group_upcoming = matches[~matches["played"]].copy()
    played = group_played
    upcoming = group_upcoming
    knockout_total = len(knockout_matches) if knockout_matches is not None else 0
    knockout_completed = 0
    knockout_goals = 0
    if knockout_matches is not None and not knockout_matches.empty:
        knockout_status = knockout_matches["status"].astype(str).str.upper()
        finished_knockout = knockout_matches[
            knockout_status.isin({"FINISHED", "FT", "AET", "PEN"})
            & knockout_matches["home_goals"].notna()
            & knockout_matches["away_goals"].notna()
        ]
        knockout_completed = len(finished_knockout)
        knockout_goals = int(
            pd.to_numeric(finished_knockout["home_goals"], errors="coerce").fillna(0).sum()
            + pd.to_numeric(finished_knockout["away_goals"], errors="coerce").fillna(0).sum()
        )

    total_matches = len(matches) + knockout_total
    completed = int(matches["played"].sum()) + knockout_completed if total_matches else 0
    remaining = max(total_matches - completed, 0)
    progress = (completed / total_matches * 100) if total_matches else 0
    progress_on = round((progress / 100) * 18)
    progress_segments = "".join(
        f'<span class="wc-progress-seg{" wc-progress-seg-on" if idx < progress_on else ""}"></span>'
        for idx in range(18)
    )

    total_goals = knockout_goals
    if not group_played.empty:
        total_goals += int(
            pd.to_numeric(group_played["home_goals"], errors="coerce").fillna(0).sum()
            + pd.to_numeric(group_played["away_goals"], errors="coerce").fillna(0).sum()
        )

    dashboard_columns = {
        "played", "is_resolved", "home_team", "away_team", "match_date", "kickoff_time_utc",
        "home_win_probability", "draw_probability", "away_win_probability", "upset_risk_score",
    }
    if knockout_matches is not None and dashboard_columns.issubset(knockout_matches.columns):
        resolved = knockout_matches["is_resolved"].fillna(False).astype(str).str.lower().isin({"true", "1"})
        known_teams = knockout_matches["home_team"].notna() & knockout_matches["away_team"].notna()
        knockout_played = knockout_matches[knockout_matches["played"].astype(bool) & known_teams]
        knockout_upcoming = knockout_matches[
            ~knockout_matches["played"].astype(bool)
            & resolved
            & known_teams
            & knockout_matches["home_win_probability"].notna()
        ]
        played = pd.concat([group_played, knockout_played], ignore_index=True, sort=False)
        upcoming = pd.concat([group_upcoming, knockout_upcoming], ignore_index=True, sort=False)

    avg_goals = total_goals / completed if completed else 0
    avg_confidence = (1 - upcoming["upset_risk_score"].mean()) * 100 if not upcoming.empty else 0
    yellow_cards = red_cards = 0
    if player_stats is not None and not player_stats.empty:
        if "yellow_cards" in player_stats.columns:
            yellow_cards = int(pd.to_numeric(player_stats["yellow_cards"], errors="coerce").fillna(0).sum())
        if "red_cards" in player_stats.columns:
            red_cards = int(pd.to_numeric(player_stats["red_cards"], errors="coerce").fillna(0).sum())

    def flag_html(team_name: str, class_name: str = "wc-group-flag-img") -> str:
        team = teams_by_name.get(team_name)
        return _flag_image_html(team, class_name) if team else ""

    def pct(value: float) -> str:
        return f"{float(value) * 100:.0f}%"

    def date_label(date_value: object, kickoff: object = "") -> str:
        date_text, kickoff_text, timezone_label = belgian_kickoff(date_value, kickoff)
        if not date_text:
            return "TBD"
        try:
            parsed = pd.to_datetime(date_text)
            day = parsed.strftime("%b %d").upper()
        except Exception:
            day = date_text
        if kickoff_text:
            return f"{day}<br><span>{escape(kickoff_text)} {escape(timezone_label)}</span>"
        return day

    next_data = next_match or {}
    if not next_data and not upcoming.empty:
        row = upcoming.sort_values(["match_date", "kickoff_time_utc"]).iloc[0]
        next_data = {
            "home_team": row.home_team,
            "away_team": row.away_team,
            "date": row.match_date,
            "kickoff_time": row.kickoff_time_utc,
            "stage": f"Group {row.group}",
            "home_win_probability": row.home_win_probability,
            "draw_probability": row.draw_probability,
            "away_win_probability": row.away_win_probability,
        }

    home_team = str(next_data.get("home_team", "TBD"))
    away_team = str(next_data.get("away_team", "TBD"))
    next_home_prob = float(next_data.get("home_win_probability", 0) or 0)
    next_draw_prob = float(next_data.get("draw_probability", 0) or 0)
    next_away_prob = float(next_data.get("away_win_probability", 0) or 0)
    next_stage = escape(str(next_data.get("stage", "Next Match")).replace("_", " ").title())
    next_date, next_kickoff, next_timezone = belgian_kickoff(
        next_data.get("date", ""), next_data.get("kickoff_time", "")
    )
    try:
        next_date_display = pd.to_datetime(next_date).strftime("%B %d, %Y").upper()
    except Exception:
        next_date_display = next_date or "TBD"
    next_hour = next_kickoff or "TBD"

    trophy_img = f'<img class="wc-overview-trophy" src="{trophy_src}" alt="World Cup trophy">' if trophy_src else ""
    live_count = len(played[played["status"].astype(str).str.upper().isin(["IN_PLAY", "PAUSED"])]) if "status" in played else 0
    live_label = f"{live_count} live matches" if live_count else f"{completed} matches completed"

    kpis = [
        ("⌗", "Total Matches", str(total_matches), f"{completed} completed", "#68d445"),
        ("●", "Total Goals", str(total_goals), f"{avg_goals:.2f} avg per match", "#d443e5"),
        ("♟", "Teams", str(len(teams)), "from 6 confederations", "#4aa7ff"),
        ("▣", "Yellow Cards", str(yellow_cards), "player stats total", "#e2b43e"),
        ("▮", "Red Cards", str(red_cards), "player stats total", "#ff4141"),
        ("↗", "Avg Prediction Spread", f"{avg_confidence:.0f}%", "across upcoming matches", "#58e0d2"),
    ]
    kpi_html = "".join(
        f"""<div class="wc-overview-kpi">
            <div class="wc-overview-kpi-icon" style="color:{color};">{icon}</div>
            <div>
                <div class="wc-overview-kpi-value">{escape(value)}</div>
                <div class="wc-overview-kpi-label">{escape(label)}</div>
                <div class="wc-overview-kpi-sub">{escape(sub)}</div>
            </div>
        </div>"""
        for icon, label, value, sub, color in kpis
    )

    strongest = sorted(teams, key=lambda team: (-team.elo, team.name))[:5]
    max_elo = max((team.elo for team in strongest), default=1)
    strongest_rows = "".join(
        f"""<div class="wc-overview-team-row">
            <div>{idx}</div>
            <div class="wc-overview-result-team">{_flag_image_html(team, "wc-group-flag-img")}<span>{escape(team.name)}</span></div>
            <div class="wc-overview-bar"><span style="--w:{team.elo / max_elo * 100:.0f}%;"></span></div>
            <div>{int(team.elo)}</div>
        </div>"""
        for idx, team in enumerate(strongest, start=1)
    )

    upcoming_rows = []
    for row in upcoming.sort_values(["match_date", "kickoff_time_utc"]).head(4).itertuples(index=False):
        upcoming_rows.append(
            f"""<div class="wc-overview-match-row">
                <div class="wc-overview-match-date">{date_label(row.match_date, row.kickoff_time_utc)}</div>
                <div class="wc-overview-match-teams">
                    {flag_html(row.home_team)}<span>{escape(str(row.home_team)[:3].upper())}</span>
                    <span style="opacity:.62;">vs</span>
                    <span>{escape(str(row.away_team)[:3].upper())}</span>{flag_html(row.away_team)}
                </div>
                <div class="wc-overview-prob-grid">
                    <div class="wc-overview-prob-chip wc-overview-prob-chip-home" title="Home win probability">H {row.home_win_probability * 100:.0f}%</div>
                    <div class="wc-overview-prob-chip wc-overview-prob-chip-draw" title="Draw probability">D {row.draw_probability * 100:.0f}%</div>
                    <div class="wc-overview-prob-chip wc-overview-prob-chip-away" title="Away win probability">A {row.away_win_probability * 100:.0f}%</div>
                </div>
            </div>"""
        )
    if not upcoming_rows:
        upcoming_rows.append('<div class="wc-overview-match-row"><div>No upcoming matches</div></div>')

    rr_top = round_reach.sort_values("group_qualification_probability", ascending=False).head(8)
    qualification_html = "".join(
        f"""<div class="wc-donut-item">
            <div class="wc-donut" style="--p:{row.group_qualification_probability * 100:.0f};">{row.group_qualification_probability * 100:.0f}%</div>
            <div class="wc-donut-name">{escape(str(row.team))}</div>
        </div>"""
        for row in rr_top.itertuples(index=False)
    )

    latest_rows = []
    for row in played.sort_values(["match_date", "kickoff_time_utc"], ascending=[False, False]).head(3).itertuples(index=False):
        latest_rows.append(
            f"""<div class="wc-overview-result-row">
                <div class="wc-overview-match-date">{date_label(row.match_date)}<br><span>FT</span></div>
                <div class="wc-overview-result-team">{flag_html(row.home_team)}<span>{escape(str(row.home_team))}</span></div>
                <div class="wc-overview-score">{escape(str(row.score_display))}</div>
                <div class="wc-overview-result-team">{flag_html(row.away_team)}<span>{escape(str(row.away_team))}</span></div>
            </div>"""
        )
    if not latest_rows:
        latest_rows.append('<div class="wc-overview-result-row"><div>No latest results</div></div>')

    if not upcoming.empty:
        risk_row = upcoming.loc[upcoming["upset_risk_score"].idxmax()]
        fav = risk_row.home_team if risk_row.home_win_probability >= risk_row.away_win_probability else risk_row.away_team
        challenger = risk_row.away_team if fav == risk_row.home_team else risk_row.home_team
        risk_html = f"""<div class="wc-risk-layout">
            <div>
                <div class="wc-overview-panel-head" style="margin-bottom:8px;">Highest Prediction Uncertainty</div>
                <div class="wc-overview-result-team" style="font-size:1.05rem;">{flag_html(challenger)}<span>{escape(str(challenger))}</span></div>
                <div class="wc-overview-match-date" style="margin:10px 0;">could surprise</div>
                <div class="wc-overview-result-team" style="font-size:1.05rem;">{flag_html(fav)}<span>{escape(str(fav))}</span></div>
            </div>
            <div class="wc-risk-big">{risk_row.upset_risk_score * 100:.0f}%</div>
        </div>"""
    else:
        risk_html = '<div class="wc-risk-layout"><div>No upcoming prediction uncertainty</div></div>'

    scorer_html = '<div class="wc-scorer-card"><div><div class="wc-scorer-name">No player stats</div></div><div class="wc-scorer-goals">0</div></div>'
    if player_stats is not None and not player_stats.empty and {"player_name", "team", "goals"}.issubset(player_stats.columns):
        scorers = player_stats.copy()
        scorers["goals"] = pd.to_numeric(scorers["goals"], errors="coerce").fillna(0)
        top = scorers.sort_values(["goals", "player_name"], ascending=[False, True]).iloc[0]
        scorer_team = str(top["team"])
        scorer_name = str(top["player_name"])
        scorer_goals = int(top["goals"])
        scorer_html = f"""<div class="wc-scorer-card">
            <div>
                <div class="wc-scorer-name">{escape(scorer_name)}</div>
                <div class="wc-scorer-meta">{flag_html(scorer_team)} {escape(scorer_team)}</div>
            </div>
            <div>
                <div class="wc-scorer-goals">{scorer_goals}</div>
                <div class="wc-overview-match-date" style="text-align:center;">Goals</div>
            </div>
        </div>"""

    html = f"""<div class="wc-overview-hero">
        <section class="wc-overview-hero-left">
            {trophy_img}
            <div class="wc-overview-hero-title">FIFA World Cup<br>2026</div>
            <div class="wc-overview-hero-subtitle">Live Tournament Overview</div>
            <div class="wc-overview-copy">Real-time predictions, live results, resolved fixtures, and advanced analytics.</div>
            <div class="wc-live-chip"><span class="wc-live-dot"></span>{escape(live_label)}</div>
            <div class="wc-data-freshness">Data updated: {escape(data_updated)}</div>
            <div class="wc-progress-box">
                <div class="wc-progress-head"><span>Tournament Progress</span><span class="wc-progress-value">{progress:.0f}%</span></div>
                <div class="wc-progress-track">{progress_segments}</div>
                <div class="wc-progress-meta"><span>{completed} of {total_matches} matches completed</span><span>{remaining} remaining</span></div>
            </div>
        </section>
        <section class="wc-overview-next">
            <div class="wc-next-head"><span>Next Match</span><span>{next_stage}</span></div>
            <div class="wc-next-feature">
                <div>{flag_html(home_team, "wc-feature-flag")}<div class="wc-feature-team">{escape(home_team)}</div></div>
                <div class="wc-feature-time">
                    <div class="wc-feature-date">{escape(next_date_display)}</div>
                    <div class="wc-feature-hour">{escape(next_hour)}</div>
                    <div class="wc-feature-utc">{escape(next_timezone or "Belgian time")}</div>
                </div>
                <div>{flag_html(away_team, "wc-feature-flag")}<div class="wc-feature-team">{escape(away_team)}</div></div>
            </div>
            <div class="wc-feature-probs">
                <div class="wc-feature-prob wc-feature-prob-home"><strong>{pct(next_home_prob)}</strong>Win Probability</div>
                <div class="wc-feature-prob"><strong>{pct(next_draw_prob)}</strong>Draw</div>
                <div class="wc-feature-prob wc-feature-prob-away"><strong>{pct(next_away_prob)}</strong>Win Probability</div>
            </div>
        </section>
    </div>
    <div class="wc-overview-kpis">{kpi_html}</div>
    <div class="wc-overview-grid">
        <section class="wc-overview-panel">
            <div class="wc-overview-panel-head"><span>Strongest Teams <span style="color:#fff;">(by Elo)</span></span></div>
            {strongest_rows}
        </section>
        <section class="wc-overview-panel">
            <div class="wc-overview-panel-head"><span>Upcoming Matches</span><a class="wc-view-all" href="?page=Match%20Details" target="_self">View all</a></div>
            {''.join(upcoming_rows)}
        </section>
        <section class="wc-overview-panel">
            <div class="wc-overview-panel-head"><span>Qualification Chance <span style="color:#fff;">(top 8)</span></span></div>
            <div class="wc-overview-donut-grid">{qualification_html}</div>
        </section>
    </div>
    <div class="wc-overview-grid-bottom">
        <section class="wc-overview-panel">
            <div class="wc-overview-panel-head"><span>Latest Results</span><a class="wc-view-all" href="?page=Match%20Details" target="_self">View all</a></div>
            {''.join(latest_rows)}
        </section>
        <section class="wc-overview-panel wc-overview-risk">{risk_html}</section>
        <section class="wc-overview-panel">
            <div class="wc-overview-panel-head"><span>Top Goalscorer</span><span class="wc-view-all">View all</span></div>
            {scorer_html}
        </section>
    </div>"""
    st.markdown(_compact_html(html), unsafe_allow_html=True)


def kpi_card(label: str, value: str, sub: str = "", accent: str = "", icon: str = ""):
    accent_class = f" wc-card-{accent}" if accent else ""
    icon_html = f'<div class="wc-kpi-icon">{icon}</div>' if icon else ""
    st.markdown(
        f"""<div class="wc-card{accent_class}">
            {icon_html}
            <div class="wc-kpi-label">{label}</div>
            <div class="wc-kpi-value">{value}</div>
            <div class="wc-kpi-sub">{sub}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def confidence_pill(label: str) -> str:
    css_class = {"High": "wc-pill-high", "Medium": "wc-pill-medium", "Low": "wc-pill-low"}.get(label, "wc-pill-medium")
    return f'<span class="wc-pill {css_class}">{label} confidence</span>'


def status_pill(status: str, played: bool) -> str:
    label = "Final" if played else str(status or "Scheduled").replace("_", " ").title()
    css_class = "wc-pill-high" if played else "wc-pill-medium"
    return f'<span class="wc-pill {css_class}">{label}</span>'


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


def _form_chips(results: list) -> str:
    if not results:
        return '<span class="wc-factor-sub">No recent form</span>'
    return "".join(f'<span class="wc-form-chip wc-form-chip-{escape(str(r))}">{escape(str(r))}</span>' for r in results[-5:])


def _venue_advantage(match_row, team1, team2) -> tuple[str, str]:
    country = str(match_row.get("country", "") or "").strip()
    aliases = {"USA": "United States"}
    home_country = aliases.get(team1.name, team1.name)
    away_country = aliases.get(team2.name, team2.name)
    if country == home_country:
        return team1.name, f"{team1.name} host venue"
    if country == away_country:
        return team2.name, f"{team2.name} host venue"
    return "Neutral", "No significant home advantage"


def _projected_score(home_pct: float, draw_pct: float, away_pct: float) -> tuple[int, int]:
    if draw_pct >= home_pct and draw_pct >= away_pct:
        return 1, 1
    if home_pct >= away_pct:
        gap = home_pct - away_pct
        return (2, 0) if gap >= 45 else (2, 1)
    gap = away_pct - home_pct
    return (0, 2) if gap >= 45 else (1, 2)


def _expected_goal_proxy(home_pct: float, away_pct: float) -> tuple[float, float]:
    home_xg = 0.8 + (home_pct / 100) * 1.8
    away_xg = 0.8 + (away_pct / 100) * 1.8
    return home_xg, away_xg


def match_detail_panel(match_row, team1, team2, focus_team: str | None = None, compact: bool = False):
    played = bool(match_row.get("played", False))
    has_score = bool(match_row.get("has_score", False))
    home_pct = float(match_row.get("home_win_probability", 0) or 0) * 100
    draw_pct = float(match_row.get("draw_probability", 0) or 0) * 100
    away_pct = float(match_row.get("away_win_probability", 0) or 0) * 100
    spread_confidence = pd.to_numeric(match_row.get("confidence_score"), errors="coerce")
    confidence = float(spread_confidence) * 100 if pd.notna(spread_confidence) else max(home_pct, draw_pct, away_pct)
    local_date, local_kickoff, timezone_label = belgian_kickoff(
        match_row.get("match_date", match_row.get("date", "")),
        match_row.get("kickoff_time_utc", ""),
    )
    match_date = escape(local_date)
    kickoff = escape(local_kickoff)
    venue = escape(str(match_row.get("venue", "") or "TBD"))
    city = escape(str(match_row.get("city", "") or ""))
    country = escape(str(match_row.get("country", "") or ""))
    group = escape(str(match_row.get("group", "") or ""))
    status_raw = str(match_row.get("status", "SCHEDULED") or "SCHEDULED").replace("_", " ")
    status = escape(status_raw.title())
    score = escape(str(match_row.get("score_display", "TBD") or "TBD"))
    stage = str(match_row.get("competition_stage", "") or "").strip()
    title = escape(stage) if stage else f"Group {group}"
    meta_bits = [match_date]
    if kickoff:
        meta_bits.append(f"{kickoff} {escape(timezone_label)}")
    meta_bits.append(", ".join(bit for bit in [venue, city, country] if bit))
    meta = " - ".join(bit for bit in meta_bits if bit)

    home_flag = _flag_image_html(team1, "wc-detail-team-flag")
    away_flag = _flag_image_html(team2, "wc-detail-team-flag")
    home_name = escape(team1.name)
    away_name = escape(team2.name)
    row_elo_diff = pd.to_numeric(match_row.get("elo_difference"), errors="coerce")
    elo_diff = float(row_elo_diff) if pd.notna(row_elo_diff) else float(team1.elo - team2.elo)
    stronger = team1.name if elo_diff >= 0 else team2.name
    predicted_home, predicted_away = _projected_score(home_pct, draw_pct, away_pct)

    if has_score and score != "TBD" and "-" in score:
        projected_home, projected_away = score.replace(" ", "").split("-", 1)
        score_label = "Final Score" if played else "Live Score"
        score_sub = status
        prediction_note = f"Model prediction: {predicted_home} - {predicted_away}"
    elif played and score != "TBD" and "-" in score:
        projected_home, projected_away = score.replace(" ", "").split("-", 1)
        score_label = "Final Score"
        score_sub = status
        prediction_note = f"Model prediction: {predicted_home} - {predicted_away}"
    else:
        projected_home, projected_away = predicted_home, predicted_away
        score_label = "Predicted Score"
        score_sub = team1.name if projected_home > projected_away else team2.name if projected_away > projected_home else "Draw"
        prediction_note = "Model-derived score proxy"

    if has_score or played:
        score_feature = f"""
            <div class="wc-score-comparison">
                <div>
                    <div class="wc-score-comparison-label">{score_label}</div>
                    <div class="wc-score-big">{projected_home} - {projected_away}</div>
                    <div class="wc-score-sub">{escape(str(score_sub))}</div>
                </div>
                <div>
                    <div class="wc-score-comparison-label">Predicted Score</div>
                    <div class="wc-score-big wc-score-big-predicted">{predicted_home} - {predicted_away}</div>
                    <div class="wc-score-sub">Model prediction</div>
                </div>
            </div>"""
    else:
        score_feature = f"""
            <div class="wc-detail-mini-title">{score_label}</div>
            <div class="wc-score-big">{projected_home} - {projected_away}</div>
            <div class="wc-score-sub">{escape(str(score_sub))}</div>
            <div class="wc-score-model-note">{escape(prediction_note)}</div>"""

    is_knockout = bool(stage and not stage.lower().startswith("group"))
    if is_knockout:
        predicted_outcome = team1.name if home_pct >= away_pct else team2.name
        favorite_probability = max(home_pct, away_pct)
    else:
        predicted_value, predicted_outcome = max(
            [(home_pct, team1.name), (draw_pct, "Draw"), (away_pct, team2.name)],
            key=lambda item: item[0],
        )
        favorite_probability = predicted_value

    uncertainty_value = pd.to_numeric(match_row.get("upset_risk_score"), errors="coerce")
    uncertainty = float(uncertainty_value) * 100 if pd.notna(uncertainty_value) else max(100 - confidence, 0)
    confidence_label = escape(str(match_row.get("confidence_label", "Medium")))

    evaluation_card = ""
    bottom_class = "wc-detail-bottom-two"
    if played:
        actual = get_match_source_of_truth(match_row, is_knockout=is_knockout)
        actual_outcome = (
            actual.get("winner")
            or ("Draw" if actual.get("outcome") == "draw" else "Unavailable")
        )
        evaluation_available = actual.get("result_source") == "actual"
        prediction_correct = evaluation_available and predicted_outcome == actual_outcome
        evaluation_label = "Correct" if prediction_correct else "Incorrect" if evaluation_available else "Unavailable"
        evaluation_color = "#76dc55" if prediction_correct else "#f1b84b" if not evaluation_available else "#f06b6b"
        evaluation_card = f"""
            <div class="wc-detail-mini">
                <div class="wc-detail-mini-title">Prediction Evaluation</div>
                <div class="wc-stat-line"><span>Predicted outcome</span><span class="wc-stat-value">{escape(predicted_outcome)}</span></div>
                <div class="wc-stat-line"><span>Actual outcome</span><span class="wc-stat-value">{escape(str(actual_outcome))}</span></div>
                <div class="wc-stat-line"><span>Result</span><span class="wc-stat-value" style="color:{evaluation_color};">{evaluation_label}</span></div>
            </div>"""
        bottom_class = "wc-detail-bottom-three"

    shell_class = "wc-detail-shell wc-detail-shell-compact" if compact else "wc-detail-shell"
    html = f"""<div class="{shell_class}">
            <div class="wc-detail-back">&larr; Match Details</div>
            <div class="wc-detail-head">
                <div class="wc-detail-title">{title}</div>
                <div class="wc-detail-meta">{meta}</div>
            </div>

            <div class="wc-detail-teams">
                <div class="wc-detail-team">
                    {home_flag}
                    <div>{home_name}</div>
                    <div class="wc-detail-elo">Elo {int(team1.elo)}</div>
                </div>
                <div class="wc-detail-vs">
                    <div class="wc-detail-vs-text">VS</div>
                    <div class="wc-detail-prob-grid">
                        <div class="wc-detail-prob wc-detail-prob-home">
                            <div class="wc-detail-prob-value">{home_pct:.0f}%</div>
                            <div class="wc-detail-prob-label">{home_name} win</div>
                        </div>
                        <div class="wc-detail-prob wc-detail-prob-draw">
                            <div class="wc-detail-prob-value">{draw_pct:.0f}%</div>
                            <div class="wc-detail-prob-label">Draw</div>
                        </div>
                        <div class="wc-detail-prob wc-detail-prob-away">
                            <div class="wc-detail-prob-value">{away_pct:.0f}%</div>
                            <div class="wc-detail-prob-label">{away_name} win</div>
                        </div>
                    </div>
                </div>
                <div class="wc-detail-team">
                    {away_flag}
                    <div>{away_name}</div>
                    <div class="wc-detail-elo">Elo {int(team2.elo)}</div>
                </div>
            </div>

            <div class="wc-detail-confidence">
                <span>Prediction Spread Confidence</span>
                <span class="wc-detail-confidence-track"><span class="wc-detail-confidence-fill" style="--w:{confidence:.0f}%"></span></span>
                <span>{match_row.get("confidence_label", "Medium")}</span>
            </div>

            <div class="wc-detail-score-feature">
                {score_feature}
            </div>

            <div class="wc-detail-bottom {bottom_class}">
                <div class="wc-detail-mini">
                    <div class="wc-detail-mini-title">Elo Comparison</div>
                    <div class="wc-stat-line"><span>{home_name}</span><span class="wc-stat-value">{int(team1.elo)}</span></div>
                    <div class="wc-stat-line"><span>{away_name}</span><span class="wc-stat-value">{int(team2.elo)}</span></div>
                    <div class="wc-stat-line"><span>Rating advantage</span><span class="wc-stat-value">{escape(str(stronger))} ({abs(elo_diff):.0f})</span></div>
                </div>
                <div class="wc-detail-mini">
                    <div class="wc-detail-mini-title">Prediction Summary</div>
                    <div class="wc-stat-line"><span>Model favorite</span><span class="wc-stat-value">{escape(predicted_outcome)}</span></div>
                    <div class="wc-stat-line"><span>Favorite probability</span><span class="wc-stat-value">{favorite_probability:.0f}%</span></div>
                    <div class="wc-stat-line"><span>Confidence</span><span class="wc-stat-value">{confidence_label}</span></div>
                    <div class="wc-stat-line"><span>Prediction uncertainty</span><span class="wc-stat-value">{uncertainty:.0f}%</span></div>
                </div>
                {evaluation_card}
            </div>
        </div>"""
    st.markdown(_compact_html(html), unsafe_allow_html=True)


def top_teams_panel(teams):
    if not teams:
        st.markdown('<div class="wc-panel"><div class="wc-panel-title">Top 10 strongest teams</div>No teams available.</div>',
                    unsafe_allow_html=True)
        return

    top = sorted(teams, key=lambda t: -t.elo)[:10]
    max_elo = max(t.elo for t in top)
    min_elo = min(t.elo for t in top)
    spread = max(max_elo - min_elo, 1)
    rows = []
    for i, team in enumerate(top, start=1):
        width = 58 + ((team.elo - min_elo) / spread) * 40
        flag_html = _flag_image_html(team)
        rows.append(
            f"""<div class="wc-team-rank">
                <span>{i}</span>
                {flag_html}
                <span>{team.name}</span>
                <span class="wc-rank-bar"><span class="wc-rank-fill" style="display:block;width:{width:.0f}%"></span></span>
                <span>{team.elo}</span>
            </div>"""
        )
    st.markdown(
        f"""<div class="wc-panel">
            <div class="wc-panel-title">Top 10 strongest teams <span style="font-weight:400;">(by Elo)</span></div>
            {''.join(rows)}
        </div>""",
        unsafe_allow_html=True,
    )


def qualification_panel(round_reach, top_n: int = 8):
    rows = []
    for _, row in round_reach.head(top_n).iterrows():
        pct = row["group_qualification_probability"] * 100
        rows.append(
            f"""<div class="wc-donut-item">
                <div class="wc-donut" style="--p:{pct:.0f};">{pct:.0f}%</div>
                <div class="wc-donut-name">{row.flag} {row.team}</div>
            </div>"""
        )
    st.markdown(
        f"""<div class="wc-panel">
            <div class="wc-panel-title">Qualification chance (top 8 teams)</div>
            <div class="wc-donut-grid">{''.join(rows)}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def compact_matches_panel(matches, title: str, empty_message: str = "No matches available.", teams_by_name: dict | None = None):
    teams_by_name = teams_by_name or {}
    rows = []
    for _, match in matches.iterrows():
        date, kickoff, timezone_label = belgian_kickoff(
            match.get("match_date", match.get("date", "")),
            match.get("kickoff_time_utc", ""),
        )
        group = str(match.get("group", "")).replace("GROUP_", "Group ")
        home = match.get("home_team", "")
        away = match.get("away_team", "")
        home_flag = getattr(teams_by_name.get(home), "flag", "")
        away_flag = getattr(teams_by_name.get(away), "flag", "")
        score = match.get("score_display", "TBD")
        home_tla = str(home)[:3].upper()
        away_tla = str(away)[:3].upper()
        if bool(match.get("played", False)):
            probs = f'<div class="wc-prob-chip"><span>{score}</span></div>'
        else:
            home_prob = match.get("home_win_probability", 0) * 100
            draw_prob = match.get("draw_probability", 0) * 100
            away_prob = match.get("away_win_probability", 0) * 100
            max_prob = max(home_prob, draw_prob, away_prob)
            home_fill = f'<div class="wc-prob-chip-fill" style="--w:{home_prob:.0f}%;"></div>' if home_prob == max_prob else ""
            draw_fill = f'<div class="wc-prob-chip-fill wc-prob-chip-fill-draw" style="--w:{draw_prob:.0f}%;"></div>' if draw_prob == max_prob else ""
            away_fill = f'<div class="wc-prob-chip-fill wc-prob-chip-fill-away" style="--w:{away_prob:.0f}%;"></div>' if away_prob == max_prob else ""
            probs = (
                f'<div class="wc-prob-chip">{home_fill}<span>{home_tla} {home_prob:.0f}%</span></div>'
                f'<div class="wc-prob-chip wc-prob-chip-muted">{draw_fill}<span>DRAW {draw_prob:.0f}%</span></div>'
                f'<div class="wc-prob-chip wc-prob-chip-away">{away_fill}<span>{away_tla} {away_prob:.0f}%</span></div>'
            )
        rows.append(
            f"""<div class="wc-compact-match">
                <div class="wc-compact-date">{date}<small>{kickoff} {timezone_label}<br>{group}</small></div>
                <div class="wc-compact-teams">
                    <div class="wc-compact-team">{home_flag} {home}</div>
                    <div class="wc-compact-vs">vs</div>
                    <div class="wc-compact-team">{away_flag} {away}</div>
                </div>
                <div class="wc-compact-probs">{probs}</div>
            </div>"""
        )

    body = "".join(rows) if rows else f'<div style="opacity:.72;font-size:.86rem;">{empty_message}</div>'
    st.markdown(
        f"""<div class="wc-panel">
            <div class="wc-panel-title">{title}</div>
            {body}
        </div>""",
        unsafe_allow_html=True,
    )


def group_stage_panel(group_name: str, standings, matches, teams_by_name: dict):
    group_rows = standings[standings.group == group_name].sort_values(
        ["points", "goal_difference", "goals_for"], ascending=[False, False, False]
    ).reset_index(drop=True)
    group_matches = matches[matches.group == group_name].sort_values(["match_date", "kickoff_time_utc"])

    expected_points = {row.team: float(row.points) for _, row in group_rows.iterrows()}
    xg_for = {row.team: 0.0 for _, row in group_rows.iterrows()}
    xg_against = {row.team: 0.0 for _, row in group_rows.iterrows()}
    for _, match in group_matches.iterrows():
        home = match.home_team
        away = match.away_team
        home_prob = float(match.home_win_probability)
        draw_prob = float(match.draw_probability)
        away_prob = float(match.away_win_probability)
        if not bool(match.played):
            expected_points[home] += home_prob * 3 + draw_prob
            expected_points[away] += away_prob * 3 + draw_prob
        home_xg, away_xg = _expected_goal_proxy(home_prob * 100, away_prob * 100)
        xg_for[home] += home_xg
        xg_against[home] += away_xg
        xg_for[away] += away_xg
        xg_against[away] += home_xg

    # Build the table separately so W/D/L can come from the Team objects.
    table_rows = []
    for rank, row in enumerate(group_rows.itertuples(index=False), start=1):
        team_obj = teams_by_name.get(row.team)
        flag = _flag_image_html(team_obj, "wc-group-flag-img") if team_obj else ""
        w = getattr(team_obj, "campaign_w", 0)
        d = getattr(team_obj, "campaign_d", 0)
        l = getattr(team_obj, "campaign_l", 0)
        gd = f"{int(row.goal_difference):+d}"
        pct = float(row.group_qualification_probability) * 100
        table_rows.append(
            f"""<div class="wc-group-row">
                <div class="wc-group-stat">{rank}</div>
                <div class="wc-group-team-cell">{flag}<span>{escape(row.team)}</span></div>
                <div class="wc-group-stat">{int(row.played)}</div>
                <div class="wc-group-stat">{int(w)}</div>
                <div class="wc-group-stat">{int(d)}</div>
                <div class="wc-group-stat">{int(l)}</div>
                <div class="wc-group-stat">{int(row.goals_for)}</div>
                <div class="wc-group-stat">{int(row.goals_against)}</div>
                <div class="wc-group-stat">{gd}</div>
                <div class="wc-group-stat">{int(row.points)}</div>
                <div class="wc-qual-cell">
                    <div class="wc-qual-bar">
                        <div class="wc-qual-fill" style="--w:{pct:.1f}%;"></div>
                        <span>{pct:.0f}%</span>
                    </div>
                </div>
            </div>"""
        )

    max_points = max(max(expected_points.values()), 8.0)
    colors = ["#6f93c7", "#a6815f", "#7fb34d", "#8b715c"]
    points_rows = []
    for i, row in enumerate(group_rows.itertuples(index=False)):
        pts = expected_points[row.team]
        width = (pts / max_points) * 100
        points_rows.append(
            f"""<div class="wc-points-row">
                <div>{escape(row.team)}</div>
                <div class="wc-points-track"><span class="wc-points-fill" style="--w:{width:.1f}%;background:{colors[i % len(colors)]};"></span></div>
                <div>{pts:.1f}</div>
            </div>"""
        )

    most_goals = group_rows.sort_values(["goals_for", "points"], ascending=[False, False]).iloc[0]
    best_defense = group_rows.sort_values(["goals_against", "points"], ascending=[True, False]).iloc[0]
    highest_xg_team = max(xg_for, key=xg_for.get)
    lowest_xga_team = min(xg_against, key=xg_against.get)

    upcoming = group_matches[~group_matches.played].head(3)
    next_cards = []
    for _, match in upcoming.iterrows():
        home_obj = teams_by_name.get(match.home_team)
        away_obj = teams_by_name.get(match.away_team)
        home_flag = _flag_image_html(home_obj, "wc-group-flag-img") if home_obj else ""
        away_flag = _flag_image_html(away_obj, "wc-group-flag-img") if away_obj else ""
        local_date, local_kickoff, timezone_label = belgian_kickoff(
            match.match_date, match.kickoff_time_utc
        )
        date_label = local_date[5:].replace("-", " ") if local_date else "TBD"
        next_cards.append(
            f"""<div class="wc-next-card">
                <div class="wc-next-teams">
                    <div class="wc-next-team">{home_flag}<span>{escape(match.home_team)}</span></div>
                    <div style="text-align:center;opacity:.72;">vs</div>
                    <div class="wc-next-team">{away_flag}<span>{escape(match.away_team)}</span></div>
                </div>
                <div class="wc-next-date">{escape(date_label)}</div>
                <div class="wc-next-status">{escape(local_kickoff)} {escape(timezone_label)}</div>
            </div>"""
        )
    if not next_cards:
        next_cards.append('<div class="wc-next-card"><div class="wc-next-date">No upcoming group matches</div></div>')

    html = f"""<div class="wc-group-shell">
        <div class="wc-group-title">Group {escape(str(group_name))}</div>
        <div class="wc-group-table">
            <div class="wc-group-row wc-group-head">
                <div></div><div>Team</div><div class="wc-group-stat">P</div><div class="wc-group-stat">W</div>
                <div class="wc-group-stat">D</div><div class="wc-group-stat">L</div><div class="wc-group-stat">GF</div>
                <div class="wc-group-stat">GA</div><div class="wc-group-stat">GD</div><div class="wc-group-stat">PTS</div>
                <div class="wc-group-stat">Qualification<br>Probability</div>
            </div>
            {''.join(table_rows)}
        </div>
        <div class="wc-group-mid">
            <div class="wc-detail-mini">
                <div class="wc-detail-mini-title">Predicted Points (Final)</div>
                {''.join(points_rows)}
                <div class="wc-axis"><span>0</span><span>2</span><span>4</span><span>6</span><span>8</span></div>
            </div>
            <div class="wc-detail-mini">
                <div class="wc-detail-mini-title">Stats Overview</div>
                <div class="wc-stat-line"><span>Most Goals For</span><span class="wc-stat-value">{escape(most_goals.team)} ({int(most_goals.goals_for)})</span></div>
                <div class="wc-stat-line"><span>Best Defense</span><span class="wc-stat-value">{escape(best_defense.team)} ({int(best_defense.goals_against)} GA)</span></div>
                <div class="wc-stat-line"><span>Highest XG</span><span class="wc-stat-value">{escape(highest_xg_team)} ({xg_for[highest_xg_team]:.2f})</span></div>
                <div class="wc-stat-line"><span>Lowest XG Against</span><span class="wc-stat-value">{escape(lowest_xga_team)} ({xg_against[lowest_xga_team]:.2f})</span></div>
            </div>
        </div>
        <div class="wc-detail-mini" style="margin-top:16px;">
            <div class="wc-detail-mini-title">Next Matches - Group {escape(str(group_name))}</div>
            <div class="wc-next-grid">{''.join(next_cards)}</div>
        </div>
    </div>"""
    st.markdown(_compact_html(html), unsafe_allow_html=True)


def _prob_for_round(round_reach, team: str, column: str) -> float:
    row = round_reach[round_reach.team == team]
    if row.empty:
        return 0.0
    return float(row.iloc[0][column])


def _bracket_team_row(slot: str, team: str, prob: float, teams_by_name: dict, single: bool = False) -> str:
    team_obj = teams_by_name.get(team)
    flag = _flag_image_html(team_obj, "wc-group-flag-img") if team_obj else ""
    pct = f"{prob * 100:.0f}%"
    extra = " wc-bracket-single" if single else ""
    slot_html = "" if single else f'<span class="wc-bracket-slot">{escape(slot)}</span>'
    return (
        f'<div class="wc-bracket-team{extra}">'
        f'{slot_html}{flag}<span class="wc-bracket-team-name">{escape(team)}</span>'
        f'<span class="wc-bracket-prob">{pct}</span></div>'
    )


def _match_resolution(pair: tuple[str, str], round_reach, column: str, match_row=None) -> tuple[str, str, str]:
    home, away = pair
    home_probability = _prob_for_round(round_reach, home, column)
    away_probability = _prob_for_round(round_reach, away, column)
    prediction = {
        "home_team": home,
        "away_team": away,
        "home_win_probability": home_probability,
        "away_win_probability": away_probability,
    }
    match_context = dict(match_row) if match_row else {}
    context_home = match_context.get("home_team")
    context_away = match_context.get("away_team")
    if context_home is None or pd.isna(context_home):
        match_context["home_team"] = home
    if context_away is None or pd.isna(context_away):
        match_context["away_team"] = away
    truth = get_match_source_of_truth(match_context or prediction, prediction, is_knockout=True)
    winner = truth["winner"] or "TBD"
    if truth["result_source"] == "actual":
        home_score = int(truth["home_score"])
        away_score = int(truth["away_score"])
        penalty_text = ""
        if truth.get("home_penalties") is not None and truth.get("away_penalties") is not None:
            penalty_text = f" ({int(truth['home_penalties'])}-{int(truth['away_penalties'])} pens)"
        label = f"Actual result: {winner} won {home_score}-{away_score}{penalty_text}"
    elif truth["result_source"] == "prediction":
        label = f"Projected winner: {winner}"
    else:
        label = "Winner unresolved"
    return winner, label, truth["result_source"]


def _winner_sources(rows) -> dict[int, list[int]]:
    sources = {}
    for row in rows.itertuples(index=False):
        if not hasattr(row, "match_number") or pd.isna(row.match_number):
            continue
        source_numbers = []
        for slot in [str(row.home_slot), str(row.away_slot)]:
            if slot.startswith("W") and slot[1:].isdigit():
                source_numbers.append(int(slot[1:]))
        sources[int(row.match_number)] = source_numbers
    return sources


def _bracket_path_order(knockout_matches) -> tuple[list[int], list[int]]:
    """Return R32 and R16 display order following official winner paths."""
    if knockout_matches is None or getattr(knockout_matches, "empty", True):
        return [], []
    required = {"stage", "match_number", "home_slot", "away_slot"}
    if not required.issubset(knockout_matches.columns):
        return [], []

    stage_sources = {
        stage: _winner_sources(knockout_matches[knockout_matches["stage"].eq(stage)])
        for stage in ["Round of 16", "Quarter-final", "Semi-final"]
    }
    r16_order = []
    r32_order = []
    for semifinal_number in sorted(stage_sources["Semi-final"]):
        for quarterfinal_number in stage_sources["Semi-final"][semifinal_number]:
            for r16_number in stage_sources["Quarter-final"].get(quarterfinal_number, []):
                r16_order.append(r16_number)
                r32_order.extend(stage_sources["Round of 16"].get(r16_number, []))
    return r32_order, r16_order


def _resolved_r32_pairs(knockout_matches) -> list[tuple[str, str, str, str, object]]:
    if knockout_matches is None or getattr(knockout_matches, "empty", True):
        return []
    required = {"stage", "home_slot", "away_slot", "home_team", "away_team"}
    if not required.issubset(set(knockout_matches.columns)):
        return []

    r32 = knockout_matches[knockout_matches["stage"].eq("Round of 32")].copy()
    if r32.empty:
        return []
    bracket_order, _ = _bracket_path_order(knockout_matches)

    if bracket_order and "match_number" in r32.columns:
        order_lookup = {match_number: index for index, match_number in enumerate(bracket_order)}
        r32["_bracket_order"] = r32["match_number"].map(order_lookup).fillna(len(order_lookup))
        r32 = r32.sort_values(["_bracket_order", "match_number"])
    else:
        sort_cols = [col for col in ["date", "kickoff_time", "match_id"] if col in r32.columns]
        if sort_cols:
            r32 = r32.sort_values(sort_cols)

    pairs = []
    for row in r32.itertuples(index=False):
        home_slot = str(row.home_slot)
        away_slot = str(row.away_slot)
        home_team = row.home_team if pd.notna(row.home_team) else home_slot
        away_team = row.away_team if pd.notna(row.away_team) else away_slot
        pairs.append((home_slot, away_slot, str(home_team), str(away_team), row._asdict()))
    return pairs


def _stage_match_rows(knockout_matches, stage: str) -> list[dict]:
    if knockout_matches is None or getattr(knockout_matches, "empty", True):
        return []
    rows = knockout_matches[knockout_matches["stage"].eq(stage)].copy()
    if "match_number" in rows.columns:
        rows = rows.sort_values("match_number")
    return rows.to_dict("records")


def _mirror_card(match_number: object, inner_html: str) -> str:
    number = int(match_number) if pd.notna(match_number) else "-"
    return (
        '<div class="wc-mirror-match">'
        f'<div class="wc-mirror-match-number">Match {number}</div>'
        f'{inner_html}</div>'
    )


def knockout_bracket_panel(
    standings,
    round_reach,
    teams_by_name: dict,
    knockout_matches=None,
    trophy_src: str = "",
    zoom: float = 1.0,
):
    zoom = max(0.7, min(1.5, float(zoom)))
    ranked_groups = {
        group: g.sort_values(["points", "goal_difference", "goals_for"], ascending=[False, False, False]).reset_index(drop=True)
        for group, g in standings.groupby("group")
    }

    slots = {}
    third_rows = []
    for group, rows in ranked_groups.items():
        if len(rows) >= 1:
            slots[f"1{group}"] = rows.iloc[0].team
        if len(rows) >= 2:
            slots[f"2{group}"] = rows.iloc[1].team
        if len(rows) >= 3:
            third = rows.iloc[2].copy()
            third["slot_group"] = group
            third_rows.append(third)

    third_ranked = sorted(
        third_rows,
        key=lambda r: (r.points, r.goal_difference, r.goals_for, r.group_qualification_probability),
        reverse=True,
    )[:8]
    for i, row in enumerate(third_ranked, start=1):
        slots[f"Best 3rd #{i}"] = row.team

    slot_pairs = [
        ("1A", "2B"), ("1B", "2A"), ("1C", "2D"), ("1D", "2C"),
        ("1E", "2F"), ("1F", "2E"), ("1G", "2H"), ("1H", "2G"),
        ("1I", "2J"), ("1J", "2I"), ("1K", "2L"), ("1L", "2K"),
        ("Best 3rd #1", "Best 3rd #2"), ("Best 3rd #3", "Best 3rd #4"),
        ("Best 3rd #5", "Best 3rd #6"), ("Best 3rd #7", "Best 3rd #8"),
    ]
    r32_pairs = _resolved_r32_pairs(knockout_matches)
    if not r32_pairs:
        r32_pairs = [(a, b, slots.get(a, "TBD"), slots.get(b, "TBD"), None) for a, b in slot_pairs]

    r32_cards = []
    r16_teams = []
    advancers: dict[int, str] = {}
    eliminated: dict[int, str] = {}
    for pair_index, (slot_a, slot_b, team_a, team_b, match_row) in enumerate(r32_pairs):
        prob_a = _prob_for_round(round_reach, team_a, "round_of_16")
        prob_b = _prob_for_round(round_reach, team_b, "round_of_16")
        winner, source_label, source = _match_resolution(
            (team_a, team_b), round_reach, "round_of_16", match_row
        )
        r16_teams.append(winner)
        match_number = int(match_row.get("match_number", 73 + pair_index)) if match_row else 73 + pair_index
        advancers[match_number] = winner
        if winner != "TBD":
            eliminated[match_number] = team_b if winner == team_a else team_a
        card = (
            f'<div class="wc-bracket-match">'
            f'{_bracket_team_row(slot_a, team_a, prob_a, teams_by_name)}'
            f'{_bracket_team_row(slot_b, team_b, prob_b, teams_by_name)}'
            f'<div class="wc-bracket-source wc-bracket-source-{source}">{escape(source_label)}</div>'
            f'</div>'
        )
        r32_cards.append(_mirror_card(match_number, card))

    def round_cards(
        source_teams: list[str],
        reach_col: str,
        next_col: str,
        stage: str,
    ) -> tuple[list[str], list[str]]:
        cards = []
        winners = []
        official_rows = _stage_match_rows(knockout_matches, stage)
        row_count = len(official_rows) if official_rows else len(source_teams) // 2
        for row_index in range(row_count):
            match_row = official_rows[row_index] if official_rows else None
            if match_row:
                home_slot = str(match_row.get("home_slot", ""))
                away_slot = str(match_row.get("away_slot", ""))
                team_a = advancers.get(int(home_slot[1:]), "TBD") if home_slot.startswith("W") else "TBD"
                team_b = advancers.get(int(away_slot[1:]), "TBD") if away_slot.startswith("W") else "TBD"
                if pd.notna(match_row.get("home_team")) and pd.notna(match_row.get("away_team")):
                    team_a = str(match_row["home_team"])
                    team_b = str(match_row["away_team"])
            else:
                team_a, team_b = source_teams[row_index * 2:row_index * 2 + 2]
            prob_a = _prob_for_round(round_reach, team_a, reach_col)
            prob_b = _prob_for_round(round_reach, team_b, reach_col)
            winner, source_label, source = _match_resolution((team_a, team_b), round_reach, next_col, match_row)
            winners.append(winner)
            match_number = None
            if match_row and pd.notna(match_row.get("match_number")):
                match_number = int(match_row["match_number"])
                advancers[match_number] = winner
                if winner != "TBD":
                    eliminated[match_number] = team_b if winner == team_a else team_a
            card = (
                f'<div class="wc-bracket-match">'
                f'{_bracket_team_row("", team_a, prob_a, teams_by_name, single=True)}'
                f'{_bracket_team_row("", team_b, prob_b, teams_by_name, single=True)}'
                f'<div class="wc-bracket-source wc-bracket-source-{source}">{escape(source_label)}</div>'
                f'</div>'
            )
            cards.append(_mirror_card(match_number, card))
        return cards, winners

    r16_cards, qf_teams = round_cards(r16_teams, "quarterfinal", "quarterfinal", "Round of 16")
    qf_cards, sf_teams = round_cards(qf_teams, "semifinal", "semifinal", "Quarter-final")
    sf_cards, final_teams = round_cards(sf_teams, "final", "final", "Semi-final")

    _, r16_order = _bracket_path_order(knockout_matches)
    if r16_order:
        official_r16 = _stage_match_rows(knockout_matches, "Round of 16")
        cards_by_number = {
            int(row["match_number"]): card
            for row, card in zip(official_r16, r16_cards)
            if pd.notna(row.get("match_number"))
        }
        r16_cards = [cards_by_number[number] for number in r16_order if number in cards_by_number]

    final_cards = []
    final_winner = None
    if len(final_teams) >= 2:
        final_rows = _stage_match_rows(knockout_matches, "Final")
        final_row = final_rows[0] if final_rows else None
        if final_row and pd.notna(final_row.get("home_team")) and pd.notna(final_row.get("away_team")):
            final_teams = [str(final_row["home_team"]), str(final_row["away_team"])]
        final_winner, final_label, final_source = _match_resolution(
            (final_teams[0], final_teams[1]), round_reach, "tournament_win_probability", final_row
        )
        final_number = final_row.get("match_number", 104) if final_row else 104
        final_card = (
            f'<div class="wc-bracket-match">'
            f'{_bracket_team_row("", final_teams[0], _prob_for_round(round_reach, final_teams[0], "tournament_win_probability"), teams_by_name, single=True)}'
            f'{_bracket_team_row("", final_teams[1], _prob_for_round(round_reach, final_teams[1], "tournament_win_probability"), teams_by_name, single=True)}'
            f'<div class="wc-bracket-source wc-bracket-source-{final_source}">{escape(final_label)}</div>'
            f'</div>'
        )
        final_cards.append(_mirror_card(final_number, final_card))

    third_place_cards = []
    third_rows = _stage_match_rows(knockout_matches, "3rd Place Match")
    third_row = third_rows[0] if third_rows else None
    third_teams = [eliminated.get(101, "TBD"), eliminated.get(102, "TBD")]
    if third_row and pd.notna(third_row.get("home_team")) and pd.notna(third_row.get("away_team")):
        third_teams = [str(third_row["home_team"]), str(third_row["away_team"])]
    _third_winner, third_label, third_source = _match_resolution(
        (third_teams[0], third_teams[1]), round_reach, "tournament_win_probability", third_row
    )
    third_number = third_row.get("match_number", 103) if third_row else 103
    third_card = (
        f'<div class="wc-bracket-match">'
        f'{_bracket_team_row("", third_teams[0], _prob_for_round(round_reach, third_teams[0], "tournament_win_probability"), teams_by_name, single=True)}'
        f'{_bracket_team_row("", third_teams[1], _prob_for_round(round_reach, third_teams[1], "tournament_win_probability"), teams_by_name, single=True)}'
        f'<div class="wc-bracket-source wc-bracket-source-{third_source}">{escape(third_label)}</div>'
        f'</div>'
    )
    third_place_cards.append(_mirror_card(third_number, third_card))

    top_winners = round_reach.head(4)
    champion = top_winners.iloc[0]
    champion_name = final_winner if final_winner and final_winner != "TBD" else champion.team
    champion_probability = _prob_for_round(round_reach, champion_name, "tournament_win_probability")
    champion_obj = teams_by_name.get(champion_name)
    champion_flag = _flag_image_html(champion_obj, "wc-group-flag-img") if champion_obj else ""
    winner_rows = []
    for row in top_winners.itertuples(index=False):
        team_obj = teams_by_name.get(row.team)
        flag = _flag_image_html(team_obj, "wc-group-flag-img") if team_obj else ""
        winner_rows.append(
            f'<div class="wc-winner-row">{flag}<span>{escape(row.team)}</span><span>{row.tournament_win_probability * 100:.0f}%</span></div>'
        )

    trophy_html = (
        f'<img class="wc-bracket-trophy-image" src="{trophy_src}" alt="World Cup trophy">'
        if trophy_src else '<div class="wc-trophy">🏆</div>'
    )
    html = f"""<div class="wc-bracket-shell">
        <div class="wc-bracket-scroll">
            <div class="wc-bracket-mirror" style="zoom:{zoom:.1f};">
                <section class="wc-mirror-stage wc-mirror-left">
                    <div class="wc-mirror-stage-title">Round of 32</div>
                    <div class="wc-mirror-stage-cards">{''.join(r32_cards[:8])}</div>
                </section>
                <section class="wc-mirror-stage wc-mirror-left">
                    <div class="wc-mirror-stage-title">Round of 16</div>
                    <div class="wc-mirror-stage-cards">{''.join(r16_cards[:4])}</div>
                </section>
                <section class="wc-mirror-stage wc-mirror-left">
                    <div class="wc-mirror-stage-title">Quarter-finals</div>
                    <div class="wc-mirror-stage-cards">{''.join(qf_cards[:2])}</div>
                </section>
                <section class="wc-mirror-stage wc-mirror-left">
                    <div class="wc-mirror-stage-title">Semi-final 1</div>
                    <div class="wc-mirror-stage-cards">{''.join(sf_cards[:1])}</div>
                </section>

                <section class="wc-mirror-center">
                    <div class="wc-mirror-stage-title">Final</div>
                    {''.join(final_cards)}
                    {trophy_html}
                    <div class="wc-bracket-winner">
                        <div class="wc-winner-title">Winner</div>
                        <div class="wc-winner-main">{champion_flag}<span>{escape(champion_name)}</span><span>{champion_probability * 100:.0f}%</span></div>
                        <div class="wc-winner-list">{''.join(winner_rows[1:])}</div>
                    </div>
                    <div class="wc-third-place-title">Third Place</div>
                    {''.join(third_place_cards)}
                </section>

                <section class="wc-mirror-stage wc-mirror-right">
                    <div class="wc-mirror-stage-title">Semi-final 2</div>
                    <div class="wc-mirror-stage-cards">{''.join(sf_cards[1:])}</div>
                </section>
                <section class="wc-mirror-stage wc-mirror-right">
                    <div class="wc-mirror-stage-title">Quarter-finals</div>
                    <div class="wc-mirror-stage-cards">{''.join(qf_cards[2:])}</div>
                </section>
                <section class="wc-mirror-stage wc-mirror-right">
                    <div class="wc-mirror-stage-title">Round of 16</div>
                    <div class="wc-mirror-stage-cards">{''.join(r16_cards[4:])}</div>
                </section>
                <section class="wc-mirror-stage wc-mirror-right">
                    <div class="wc-mirror-stage-title">Round of 32</div>
                    <div class="wc-mirror-stage-cards">{''.join(r32_cards[8:])}</div>
                </section>
            </div>
        </div>
    </div>"""
    st.markdown(_compact_html(html), unsafe_allow_html=True)


TEAM_THEME_COLORS = {
    "Algeria": ("rgba(24, 112, 62, .88)", "rgba(246, 246, 246, .18)", "#e84c5c"),
    "Argentina": ("rgba(77, 145, 205, .88)", "rgba(246, 246, 246, .20)", "#9fd4ff"),
    "Australia": ("rgba(18, 96, 68, .88)", "rgba(216, 174, 44, .34)", "#f2c744"),
    "Austria": ("rgba(178, 24, 36, .88)", "rgba(246, 246, 246, .16)", "#ffffff"),
    "Belgium": ("rgba(112, 14, 27, .88)", "rgba(39, 35, 19, .88)", "#f1c232"),
    "Bosnia and Herzegovina": ("rgba(20, 76, 156, .88)", "rgba(214, 177, 36, .34)", "#f1d24f"),
    "Brazil": ("rgba(21, 115, 57, .88)", "rgba(24, 55, 120, .82)", "#f5d441"),
    "Canada": ("rgba(147, 18, 28, .88)", "rgba(246, 246, 246, .18)", "#ff6d72"),
    "Cape Verde": ("rgba(20, 61, 145, .88)", "rgba(181, 30, 40, .68)", "#f1d24f"),
    "Colombia": ("rgba(185, 145, 25, .88)", "rgba(22, 62, 136, .82)", "#f1d24f"),
    "Croatia": ("rgba(170, 26, 44, .88)", "rgba(21, 54, 126, .82)", "#ffffff"),
    "Curaçao": ("rgba(29, 79, 174, .88)", "rgba(235, 196, 37, .34)", "#f1d24f"),
    "Czechia": ("rgba(22, 67, 151, .88)", "rgba(177, 28, 43, .76)", "#ffffff"),
    "DR Congo": ("rgba(39, 127, 207, .88)", "rgba(194, 42, 45, .72)", "#f1d24f"),
    "Ecuador": ("rgba(196, 151, 29, .88)", "rgba(29, 64, 138, .82)", "#ef4d4d"),
    "Egypt": ("rgba(174, 27, 36, .88)", "rgba(27, 27, 27, .82)", "#ffffff"),
    "England": ("rgba(180, 28, 44, .82)", "rgba(246, 246, 246, .16)", "#ffffff"),
    "France": ("rgba(20, 53, 138, .88)", "rgba(160, 18, 35, .76)", "#ffffff"),
    "Germany": ("rgba(22, 22, 22, .88)", "rgba(156, 21, 31, .76)", "#f1c232"),
    "Ghana": ("rgba(186, 32, 42, .88)", "rgba(21, 105, 55, .76)", "#f1d24f"),
    "Haiti": ("rgba(28, 72, 155, .88)", "rgba(168, 28, 45, .76)", "#ffffff"),
    "Iran": ("rgba(25, 126, 67, .88)", "rgba(174, 30, 44, .76)", "#ffffff"),
    "Iraq": ("rgba(28, 124, 67, .88)", "rgba(178, 26, 39, .76)", "#ffffff"),
    "Ivory Coast": ("rgba(210, 112, 37, .88)", "rgba(24, 126, 69, .76)", "#ffffff"),
    "Japan": ("rgba(137, 19, 45, .88)", "rgba(246, 246, 246, .18)", "#ffffff"),
    "Jordan": ("rgba(28, 117, 65, .88)", "rgba(174, 28, 43, .76)", "#ffffff"),
    "Mexico": ("rgba(23, 105, 56, .88)", "rgba(137, 24, 37, .78)", "#ffffff"),
    "Morocco": ("rgba(151, 25, 35, .88)", "rgba(19, 93, 55, .76)", "#4fce78"),
    "Netherlands": ("rgba(210, 90, 30, .86)", "rgba(17, 48, 128, .82)", "#ffffff"),
    "New Zealand": ("rgba(22, 26, 31, .88)", "rgba(178, 32, 46, .70)", "#ffffff"),
    "Norway": ("rgba(174, 27, 42, .88)", "rgba(24, 50, 132, .82)", "#ffffff"),
    "Panama": ("rgba(181, 32, 47, .88)", "rgba(26, 78, 159, .78)", "#ffffff"),
    "Paraguay": ("rgba(184, 31, 46, .88)", "rgba(28, 70, 147, .78)", "#ffffff"),
    "Portugal": ("rgba(21, 104, 51, .88)", "rgba(147, 22, 34, .78)", "#f1d24f"),
    "Qatar": ("rgba(111, 24, 58, .88)", "rgba(246, 246, 246, .14)", "#ffffff"),
    "Saudi Arabia": ("rgba(20, 118, 64, .88)", "rgba(246, 246, 246, .14)", "#ffffff"),
    "Scotland": ("rgba(29, 83, 164, .88)", "rgba(246, 246, 246, .16)", "#ffffff"),
    "Senegal": ("rgba(24, 121, 68, .88)", "rgba(197, 44, 46, .70)", "#f1d24f"),
    "South Africa": ("rgba(22, 112, 65, .88)", "rgba(200, 161, 34, .36)", "#f1d24f"),
    "South Korea": ("rgba(175, 25, 45, .84)", "rgba(18, 50, 130, .78)", "#ffffff"),
    "Spain": ("rgba(155, 26, 32, .88)", "rgba(172, 123, 18, .36)", "#f2d14b"),
    "Sweden": ("rgba(31, 88, 168, .88)", "rgba(209, 170, 34, .38)", "#f1d24f"),
    "Switzerland": ("rgba(185, 18, 30, .88)", "rgba(246, 246, 246, .16)", "#ffffff"),
    "Tunisia": ("rgba(176, 28, 42, .88)", "rgba(246, 246, 246, .16)", "#ffffff"),
    "Türkiye": ("rgba(181, 27, 42, .88)", "rgba(246, 246, 246, .14)", "#ffffff"),
    "USA": ("rgba(30, 62, 138, .88)", "rgba(157, 24, 44, .78)", "#ffffff"),
    "Uruguay": ("rgba(67, 138, 201, .88)", "rgba(218, 174, 43, .32)", "#f1c232"),
    "Uzbekistan": ("rgba(31, 131, 183, .88)", "rgba(31, 142, 80, .70)", "#ffffff"),
}


def _team_theme_style(team_name: str) -> str:
    primary, secondary, accent = TEAM_THEME_COLORS.get(
        team_name,
        ("rgba(37, 87, 128, .88)", "rgba(8, 23, 41, .82)", "#71df55"),
    )
    return (
        f"--team-primary:{primary};"
        f"--team-secondary:{secondary};"
        f"--team-accent:{accent};"
        f"--team-glow:color-mix(in srgb, {accent} 34%, transparent);"
    )


def _available_player_performers(player_stats, team_name: str) -> tuple[list[tuple[str, str, object, str, str, str]], int]:
    if player_stats is None or player_stats.empty or "team" not in player_stats.columns:
        return [], 0

    team_players = player_stats[player_stats["team"] == team_name].copy()
    if team_players.empty:
        return [], 0

    specs = [
        ("Most Goals", "goals", "Goals", "MG"),
        ("Most Assists", "assists", "Assists", "AS"),
        ("Most Appearances", "appearances", "Apps", "AP"),
        ("Most Starts", "starts", "Starts", "ST"),
        ("Most Yellow Cards", "yellow_cards", "Yellow Cards", "YC"),
        ("Most Red Cards", "red_cards", "Red Cards", "RC"),
        ("Most Shots", "shots", "Shots", "SH"),
        ("Most Shots on Target", "shots_on_target", "On Target", "SOT"),
        ("Most Passes", "passes", "Passes", "PS"),
        ("Best Pass Accuracy", "pass_accuracy", "Accuracy", "PA"),
        ("Most Key Passes", "key_passes", "Key Passes", "KP"),
        ("Most Tackles", "tackles", "Tackles", "TK"),
    ]
    performers = []
    for label, column, unit, token in specs:
        if column not in team_players.columns:
            continue
        values = pd.to_numeric(team_players[column], errors="coerce")
        valid = team_players[values.notna()].copy()
        if valid.empty:
            continue
        valid[column] = values[values.notna()]
        best = valid.sort_values([column, "player_name"], ascending=[False, True]).iloc[0]
        value = best[column]
        if pd.isna(value):
            continue
        if float(value) == 0 and column not in {"appearances", "starts"}:
            continue
        display_value = f"{float(value):.0f}" if float(value).is_integer() else f"{float(value):.1f}"
        if column == "pass_accuracy":
            display_value = f"{display_value}%"
        position = str(best.get("position", "") or "").strip()
        performers.append((label, str(best["player_name"]), display_value, unit, token, position))
    return performers, len(team_players)


def team_stats_dashboard(
    teams: list,
    standings,
    round_reach,
    matches=None,
    player_stats=None,
    selected_team: str | None = None,
    show_team_list: bool = True,
    player_data_updated: str = "Unavailable",
):
    teams_by_name = {t.name: t for t in teams}
    rr = round_reach.set_index("team")
    st_by_team = standings.set_index("team")
    ranked_teams = sorted(teams, key=lambda t: (-t.elo, t.name))
    selected = teams_by_name.get(selected_team) or ranked_teams[0]
    selected_rank = next((idx for idx, team in enumerate(ranked_teams, start=1) if team.name == selected.name), 1)
    theme_style = _team_theme_style(selected.name)

    selected_rr = rr.loc[selected.name]
    selected_st = st_by_team.loc[selected.name]
    selected_flag = _flag_image_html(selected, "wc-ta-hero-flag")
    selected_crest = _flag_image_html(selected, "wc-ta-crest")
    selected_form_values = selected.campaign_results or selected.recent_form
    selected_form = _form_chips(selected_form_values)
    selected_record = (
        f"{selected.campaign_w}W {selected.campaign_d}D {selected.campaign_l}L"
        if selected.campaign_played
        else "No WC matches played"
    )
    form_goals = (
        f"GF {selected.campaign_gf} / GA {selected.campaign_ga}"
        if selected.campaign_played
        else f"GF {selected.goals_for_l5} / GA {selected.goals_against_l5}"
    )

    side_rows = []
    for team in ranked_teams:
        active = " wc-ta-list-row-active" if team.name == selected.name else ""
        active_dot = '<span class="wc-ta-active-dot"></span>' if team.name == selected.name else ""
        flag = _flag_image_html(team, "wc-group-flag-img")
        team_url = f"?page=Teams&team={quote(team.name)}"
        side_rows.append(
            f"""<a class="wc-ta-list-row{active}" href="{team_url}" target="_self">
                <div class="wc-ta-list-team">{flag}<span>{escape(team.name)}</span></div>
                {active_dot}
            </a>"""
        )

    performers, player_count = _available_player_performers(player_stats, selected.name)
    performer_rows = []
    for label, player, value, unit, _token, position in performers[:12]:
        position_badge = (
            f'<span class="wc-ta-position-pill">{escape(position)}</span>'
            if position and position.lower() != "nan"
            else ""
        )
        performer_rows.append(
            f"""<div class="wc-ta-performer">
                <div class="wc-ta-performer-top">
                    <div class="wc-ta-performer-label">{escape(label)}</div>
                </div>
                <div class="wc-ta-performer-name">{escape(player)}</div>
                <div class="wc-ta-performer-stat">
                    <div class="wc-ta-performer-number">
                        <div class="wc-ta-performer-value">{value}</div>
                        <div class="wc-ta-performer-unit">{escape(unit)}</div>
                    </div>
                    {position_badge}
                </div>
            </div>"""
        )
    if not performer_rows:
        performer_rows.append(
            """<div class="wc-ta-performer">
                <div class="wc-ta-performer-top">
                    <div class="wc-ta-performer-label">Player Data</div>
                </div>
                <div class="wc-ta-performer-name">No player rows available</div>
                <div class="wc-ta-performer-stat">
                    <div class="wc-ta-performer-number">
                        <div class="wc-ta-performer-value">-</div>
                        <div class="wc-ta-performer-unit">No statistics</div>
                    </div>
                </div>
            </div>"""
        )
    player_note = (
        f"Real StatBunker player data loaded for {player_count} {escape(selected.name)} players. "
        f"Unavailable advanced fields are hidden. Refreshed: {escape(player_data_updated)}."
        if player_count
        else f"No player data available for this team yet. Last refresh: {escape(player_data_updated)}."
    )

    match_rows = []
    if matches is not None:
        team_matches = matches[(matches.home_team == selected.name) | (matches.away_team == selected.name)].copy()
        team_matches = team_matches.sort_values(["match_date", "kickoff_time_utc"]).head(3)
        for row in team_matches.itertuples(index=False):
            home = teams_by_name.get(row.home_team)
            away = teams_by_name.get(row.away_team)
            home_flag = _flag_image_html(home, "wc-group-flag-img") if home else ""
            away_flag = _flag_image_html(away, "wc-group-flag-img") if away else ""
            score = row.score_display if str(row.score_display) != "TBD" else "- -"
            match_rows.append(
                f"""<div class="wc-ta-match-card">
                    <div class="wc-ta-match-meta"><span>{escape(str(row.match_date))}</span><span>Group {escape(str(row.group))}</span></div>
                    <div class="wc-ta-match-line">
                        <div class="wc-ta-match-team">{home_flag}<span>{escape(str(row.home_team))}</span></div>
                        <div class="wc-ta-score">{escape(str(score))}</div>
                        <div class="wc-ta-match-team">{away_flag}<span>{escape(str(row.away_team))}</span></div>
                    </div>
                </div>"""
            )
    if not match_rows:
        match_rows.append('<div class="wc-ta-match-card"><div class="wc-ta-match-meta">No matches available</div></div>')

    gf_per_game = selected.campaign_gf / selected.campaign_played if selected.campaign_played else 0
    ga_per_game = selected.campaign_ga / selected.campaign_played if selected.campaign_played else 0
    overview_cards = [
        ("Matches Played", selected.campaign_played, ""),
        ("Goals For", selected.campaign_gf, f"{gf_per_game:.1f} per game"),
        ("Goals Against", selected.campaign_ga, f"{ga_per_game:.1f} per game"),
        ("Group Points", int(selected_st.points), f"Group {selected.group}"),
        ("FIFA Rank", f"#{selected.fifa_rank}", selected.confederation),
        ("Elo Rank", f"#{selected_rank}", f"Elo {selected.elo}"),
    ]
    overview_html = "".join(
        f"""<div class="wc-ta-overview-card">
            <div class="wc-ta-overview-label">{escape(label)}</div>
            <div class="wc-ta-overview-value">{value}</div>
            <div class="wc-ta-overview-sub">{escape(sub)}</div>
        </div>"""
        for label, value, sub in overview_cards
    )

    outlook_rows = [
        ("Qualification Chance", selected_rr.group_qualification_probability, ""),
        ("Round of 16", selected_rr.round_of_16, ""),
        ("Quarterfinal", selected_rr.quarterfinal, ""),
        ("Semifinal", selected_rr.semifinal, ""),
        ("Win Tournament", selected_rr.tournament_win_probability, " wc-ta-fill-gold"),
    ]
    outlook_html = "".join(
        f"""<div class="wc-ta-outlook-row">
            <div class="wc-ta-outlook-head"><span>{escape(label)}</span><span>{prob * 100:.1f}%</span></div>
            <div class="wc-ta-track"><span class="wc-ta-fill{accent}" style="--w:{prob * 100:.1f}%;"></span></div>
        </div>"""
        for label, prob, accent in outlook_rows
    )

    side_html = f"""<aside class="wc-ta-panel wc-ta-side">
            <div class="wc-ta-side-label">All Teams</div>
            <div class="wc-ta-list">{''.join(side_rows)}</div>
            <div class="wc-ta-selected-box" style="justify-content:center;margin-top:18px;color:#9be36c;">Compare Teams</div>
        </aside>""" if show_team_list else ""
    shell_class = "wc-ta-shell" if show_team_list else "wc-ta-shell wc-ta-shell-no-side"

    html = f"""<div class="{shell_class}" style="{theme_style}">
        {side_html}

        <main class="wc-ta-main">
            <section class="wc-ta-hero">
                <div class="wc-ta-hero-content">
                    {selected_flag}
                    <div>
                        <div class="wc-ta-country">{escape(selected.name)}</div>
                        <div class="wc-ta-meta-grid">
                            <div class="wc-ta-meta-item"><div class="wc-ta-meta-label">FIFA Rank</div><div class="wc-ta-meta-value">{selected.fifa_rank}</div></div>
                            <div class="wc-ta-meta-item"><div class="wc-ta-meta-label">Elo Rating</div><div class="wc-ta-meta-value">{selected.elo}</div></div>
                            <div class="wc-ta-meta-item"><div class="wc-ta-meta-label">Elo Rank</div><div class="wc-ta-meta-value">{selected_rank}</div></div>
                            <div class="wc-ta-meta-item"><div class="wc-ta-meta-label">Confederation</div><div class="wc-ta-meta-value wc-ta-meta-value-muted">{escape(selected.confederation)}</div></div>
                            <div class="wc-ta-meta-item"><div class="wc-ta-meta-label">Group</div><div class="wc-ta-meta-value wc-ta-meta-value-muted">{escape(selected.group)}</div></div>
                        </div>
                    </div>
                </div>
            </section>

            <section class="wc-ta-panel">
                <div class="wc-panel-title">Top Performers ({escape(selected.name)})</div>
                <div class="wc-ta-performer-grid">{''.join(performer_rows)}</div>
                <div class="wc-ta-overview-sub" style="text-align:center;margin-top:12px;">{player_note}</div>
            </section>

            <section class="wc-ta-panel">
                <div class="wc-panel-title">Recent Matches</div>
                <div class="wc-ta-match-grid">{''.join(match_rows)}</div>
            </section>
        </main>

        <aside class="wc-ta-right">
            <section class="wc-ta-panel wc-ta-record">
                <div>
                    <div class="wc-ta-section-title">This World Cup</div>
                    <div class="wc-ta-record-grid" style="margin-top:18px;">
                        <div><div class="wc-ta-record-value">{escape(selected_record)}</div><div class="wc-ta-overview-sub">Record</div></div>
                        <div><div class="wc-ta-record-value">{int(selected_st.points)}</div><div class="wc-ta-overview-sub">Group Points</div></div>
                        <div><div class="wc-ta-section-title">Recent Form</div><div class="wc-form-row" style="justify-content:flex-start;">{selected_form}</div><div class="wc-ta-overview-sub">{form_goals}</div></div>
                        <div><div class="wc-ta-section-title">Goal Difference</div><div class="wc-ta-record-value">{int(selected_st.goal_difference):+d}</div></div>
                    </div>
                </div>
                {selected_crest}
            </section>
            <section class="wc-ta-panel">
                <div class="wc-panel-title">Tournament Outlook</div>
                {outlook_html}
            </section>
            <section class="wc-ta-panel">
                <div class="wc-panel-title">Team Overview</div>
                <div class="wc-ta-overview-grid">{overview_html}</div>
            </section>
        </aside>
    </div>"""
    st.markdown(_compact_html(html), unsafe_allow_html=True)


def match_card(match_row, team1, team2):
    st.markdown('<div class="wc-match-card">', unsafe_allow_html=True)

    played = bool(match_row.get("played", False))
    score_display = match_row.get("score_display", "TBD")
    status = match_row.get("status", "SCHEDULED")
    match_date, kickoff_time, timezone_label = belgian_kickoff(
        match_row.get("match_date", match_row.get("date", "")),
        match_row.get("kickoff_time_utc", ""),
    )
    if played:
        st.markdown(
            f"""<div class="wc-team-row">
                <span>{team1.flag} {team1.name}</span>
                <span style="opacity:0.9; font-weight:700;">{score_display}</span>
                <span>{team2.name} {team2.flag}</span>
            </div>""",
            unsafe_allow_html=True,
        )
        st.markdown(status_pill(status, played), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        return

    home_pct = match_row["home_win_probability"] * 100
    draw_pct = match_row["draw_probability"] * 100
    away_pct = match_row["away_win_probability"] * 100

    st.markdown(
        f"""<div class="wc-team-row">
            <span>{team1.flag} {team1.name}</span>
            <span style="opacity:0.6; font-weight:400;">{score_display if score_display != "TBD" else "vs"}</span>
            <span>{team2.name} {team2.flag}</span>
        </div>""",
        unsafe_allow_html=True,
    )
    probability_bar(home_pct, draw_pct, away_pct, team1.name, team2.name)
    if match_date or kickoff_time:
        st.markdown(
            f'<div class="wc-match-meta">Kickoff: {match_date} {kickoff_time} {timezone_label}</div>',
            unsafe_allow_html=True,
        )
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            status_pill(status, played) + " " + confidence_pill(match_row["confidence_label"]),
            unsafe_allow_html=True,
        )
    with c2:
        if match_row["upset_risk_score"] >= 0.7:
            st.markdown(f'<span class="wc-upset">\u26a0 Prediction uncertainty ({match_row["upset_risk_score"]:.2f})</span>',
                         unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
