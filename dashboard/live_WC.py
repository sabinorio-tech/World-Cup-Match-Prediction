import pandas as pd
import streamlit as st

df = pd.read_csv("data/processed/live_matches.csv")

st.title("World Cup Live Matches")
st.dataframe(df)

finished = df[df["status"] == "FINISHED"]
upcoming = df[df["status"] == "TIMED"]

st.subheader("Finished Matches")
st.dataframe(finished)

st.subheader("Upcoming Matches")
st.dataframe(upcoming)