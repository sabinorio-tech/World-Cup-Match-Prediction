import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

# --- PAGE AND THEME CONFIGURATION ---
st.set_page_config(page_title="FIFA World Cup 2026 Predictions", page_icon="⚽", layout="wide")

# --- FOOTBALL PLATFORM CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0c111e; color: #f5f5f5; }
    /* Football-style card designs */
    div.stMetric { 
        background-color: #1a2235; 
        padding: 20px; 
        border-radius: 12px; 
        border: 1px solid #2a3a5a; 
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    div.stMetric label { color: #8e99b2 !important; font-size: 0.95em !important; font-weight: 600 !important; text-transform: uppercase;}
    div.stMetric div[data-testid="stMetricValue"] { color: #38bdf8 !important; font-size: 2.4em !important; font-weight: bold !important;}
    div[data-testid="stDataFrame"] { border-radius: 10px; border: 1px solid #2a3a5a; background-color: #1a2235;}
    h1, h2, h3 { color: #ffffff !important; font-weight: 700 !important; }
    .stProgress .st-bo { background-color: #10b981; }
    </style>
    """, unsafe_allow_html=True)

# --- GLOBAL FILTERS AND CONSTANTS ---
TEAMS = ["Argentina", "France", "Spain", "England", "Brazil", "Portugal", "Belgium", "Netherlands", "Germany", "Croatia", "Mexico", "USA", "Poland", "Algeria", "Denmark", "Saudi Arabia"]
GROUPS = ["Group A", "Group B", "Group C", "Group D", "Group E", "Group F", "Group G", "Group H"]
CONFEDERATIONS = ["All", "UEFA", "CONMEBOL", "CONCACAF", "CAF", "AFC"]

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/a/a4/2026_FIFA_World_Cup_official_logo.svg", width=130)
    st.title("🏆 AI Prediction Companion")
    st.write("---")
    
    # 5-page structure from the guidelines
    secilen_sayfa = option_menu(
        menu_title="Navigation",
        options=["Tournament Overview", "Match Prediction Center", "Team Explorer", "Group Stage Analysis", "Knockout Bracket"],
        icons=["globe", "sliders", "search", "table", "diagram-3"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"background-color": "#121829", "padding": "5px"},
            "nav-link": {"font-size": "14px", "color": "#8e99b2", "text-align": "left", "--hover-color": "#2a3a5a"},
            "nav-link-selected": {"background-color": "#38bdf8", "color": "white", "font-weight": "600"},
        }
    )
    st.write("---")
    st.caption("Data Status: Active Tournament Mode\nDate: June 2026")

# ====================================================================
# PAGE 1: TOURNAMENT OVERVIEW
# ====================================================================
if secilen_sayfa == "Tournament Overview":
    st.title("🏆 Tournament Overview")
    st.subheader("AI Predictions for FIFA World Cup 2026™")
    st.write("---")
    
    # Football-style KPI Cards from the examples
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1: st.metric(label="Total Matches", value="104")
    with kpi2: st.metric(label="Avg Confidence", value="68%")
    with kpi3: st.metric(label="Highest Win Prob", value="82%", delta="Spain vs KSA")
    with kpi4: st.metric(label="Biggest Upset Risk", value="34%", delta="Japan vs GER", delta_color="inverse")
    with kpi5: st.metric(label="Tournament Favorite", value="31%", delta="Argentina")
    
    st.write("---")
    
    col1, col2 = st.columns([1.2, 1])
    with col1:
        st.subheader("📊 Top 10 Strongest Teams (By Elo)")
        elo_mock = pd.DataFrame({'Team': TEAMS[:10], 'Elo Rating': [2113, 2097, 2084, 2071, 2058, 2043, 2028, 2023, 2015, 1994]}).sort_values(by='Elo Rating', ascending=True)
        fig_elo = px.bar(elo_mock, x='Elo Rating', y='Team', orientation='h', color='Elo Rating', color_continuous_scale='Blues', text_auto=True)
        fig_elo.update_layout(paper_bgcolor="#1a2235", plot_bgcolor="#1a2235", font_color="#f5f5f5", coloraxis_showscale=False, height=400)
        st.plotly_chart(fig_elo, use_container_width=True)
        
    with col2:
        st.subheader("📅 Upcoming Matches & Live Odds")
        upcoming_mock = pd.DataFrame({
            'Date': ['24 Jun', '24 Jun', '25 Jun', '25 Jun'],
            'Match': ['Mexico vs South Africa', 'Canada vs Switzerland', 'Argentina vs Algeria', 'France vs Australia'],
            '1 (Home)': ['56%', '32%', '78%', '74%'],
            'X (Draw)': ['24%', '28%', '15%', '17%'],
            '2 (Away)': ['20%', '40%', '7%', '9%']
        })
        st.dataframe(upcoming_mock, use_container_width=True, hide_index=True)

# ====================================================================
# PAGE 2: MATCH PREDICTION CENTER
# ====================================================================
elif secilen_sayfa == "Match Prediction Center":
    st.title("🤖 Match Prediction Center")
    st.caption("Explore individual match predictions like a football preview.")
    st.write("---")
    
    # Match Selection Slicers
    m_col1, m_col2 = st.columns(2)
    with m_col1: t1 = st.selectbox("Select Team 1 (Home)", TEAMS, index=0)
    with m_col2: t2 = st.selectbox("Select Team 2 (Away)", TEAMS, index=3)
    
    if t1 == t2:
        st.warning("Please select two different countries to preview the match.")
    else:
        st.write("---")
        # Match Preview Card Design
        card_col1, card_col2, card_col3 = st.columns([1, 0.8, 1])
        with card_col1:
            st.markdown(f"<h2 style='text-align: center;'>{t1}</h2>", unsafe_allow_html=True)
            st.metric(label="Win Probability", value="55%")
        with card_col2:
            st.markdown("<h1 style='text-align: center; color: #facc15 !important;'>VS</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; font-size: 1.2em;'><b>Predicted Score: 2 - 1</b></p>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #8e99b2;'>Confidence: <b>MEDIUM</b></p>", unsafe_allow_html=True)
        with card_col3:
            st.markdown(f"<h2 style='text-align: center;'>{t2}</h2>", unsafe_allow_html=True)
            st.metric(label="Win Probability", value="22%")
            
        st.write("---")
        st.subheader("💡 Key Prediction Factors")
        f1, f2, f3, f4 = st.columns(4)
        f1.metric("Elo Difference", "+142 pts", "Favoring Team 1")
        f2.metric("Recent Form", "W - W - D - W", "Strong", delta_color="normal")
        f3.metric("Upset Risk Level", "12%", "Low Risk", delta_color="inverse")
        f4.metric("Context", "Neutral Site", "No Host Advantage")

# ====================================================================
# PAGE 3: TEAM EXPLORER
# ====================================================================
elif secilen_sayfa == "Team Explorer":
    st.title("📊 Team Explorer")
    st.caption("Understand a country's historical strength and tournament outlook.")
    st.write("---")
    
    # Team Filters
    flt1, flt2 = st.columns(2)
    with flt1: selected_conf = st.selectbox("Filter by Confederation", CONFEDERATIONS)
    with flt2: selected_team = st.selectbox("Select Country Profile", TEAMS)
    
    st.write("---")
    st.subheader(f"⚽ {selected_team} Tournament Outlook")
    
    t_col1, t_col2 = st.columns(2)
    with t_col1:
        st.markdown("### 📈 Core Metrics")
        st.write(f"**Current Elo Rating:** 2113")
        st.write(f"**FIFA World Ranking:** #3")
        st.write(f"**Confederation:** {selected_conf if selected_conf != 'All' else 'CONMEBOL'}")
        st.write(f"**Recent Form:** 🟢 🟢 🟡 🟢 🔴")
    with t_col2:
        st.markdown("### 🔮 AI Tournament Simulation Targets")
        st.write("**Group Qualification Probability:** 98%")
        st.progress(0.98)
        st.write("**Tournament Win Probability:** 31%")
        st.progress(0.31)

# ====================================================================
# PAGE 4: GROUP STAGE ANALYSIS
# ====================================================================
elif secilen_sayfa == "Group Stage Analysis":
    st.title("📋 Group Stage Analysis")
    st.caption("AI-predicted standings and qualification data per group.")
    st.write("---")
    
    selected_group = st.selectbox("Select Tournament Group", GROUPS)
    st.write(f"### Predicted Standings: {selected_group}")
    
    # Standard Table Fields from Guidelines
    group_table_mock = pd.DataFrame({
        'Team': ['Argentina', 'Poland', 'Mexico', 'Saudi Arabia'],
        'Predicted Points': [7.1, 4.2, 3.6, 1.1],
        'Qualification Probability': ['98%', '54%', '42%', '6%'],
        'Goals For (Expected)': [6.2, 3.8, 3.1, 1.5],
        'Goals Against (Expected)': [1.1, 3.2, 4.0, 5.8],
        'Goal Difference': [+5.1, +0.6, -0.9, -4.3]
    })
    st.dataframe(group_table_mock, use_container_width=True, hide_index=True)
    
    st.write("---")
    st.subheader("Remaining Fixtures for this Group")
    st.write("📝 *Matchday 3: Argentina vs Poland | Mexico vs Saudi Arabia*")

# ====================================================================
# PAGE 5: KNOCKOUT BRACKET
# ====================================================================
elif secilen_sayfa == "Knockout Bracket":
    st.title("🌿 Knockout Bracket Paths")
    st.caption("Visually polished overview of the most likely paths to the World Cup trophy.")
    st.write("---")
    
    st.success("🏆 PROJECTED CHAMPION: ARGENTINA (31% Global Probability)")
    
    # Simulated Knockout Progression
    st.write("### Probability of Reaching Each Stage")
    stages_mock = pd.DataFrame({
        'Team': ['Argentina', 'France', 'Spain', 'Germany', 'Brazil'],
        'Reach Quarter-Finals': ['88%', '82%', '79%', '66%', '71%'],
        'Reach Semi-Finals': ['65%', '58%', '52%', '41%', '48%'],
        'Reach Final': ['46%', '39%', '34%', '22%', '27%'],
        'Win Tournament': ['31%', '20%', '15%', '8%', '12%']
    })
    st.dataframe(stages_mock, use_container_width=True, hide_index=True)



