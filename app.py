from pathlib import Path

import pandas as pd
import streamlit as st

from src.intelligence import enrich, gap_detection, longevity_winners, monday_actions, trend_table

st.set_page_config(page_title="Mosaic Competitive Intelligence", layout="wide")
st.title("Mosaic Meta Ad Intelligence")

DATA_PATH = Path("data/meta_ads_latest.csv")

if not DATA_PATH.exists():
    st.warning("No data found. Run: python scripts/scrape_meta_ads.py")
    st.stop()

raw = pd.read_csv(DATA_PATH)
df = enrich(raw)

brands = ["All"] + sorted(df["mosaic_brand"].dropna().unique().tolist())
media_types = ["All"] + sorted(df["media_type"].dropna().unique().tolist())
themes = ["All"] + sorted(df["message_theme"].dropna().unique().tolist())

c1, c2, c3, c4 = st.columns(4)
selected_brand = c1.selectbox("Mosaic Brand", brands)
selected_media = c2.selectbox("Ad format", media_types)
selected_theme = c3.selectbox("Message theme", themes)
max_days = c4.slider("Max recency (days live)", 1, 180, 90)

filtered = df.copy()
if selected_brand != "All":
    filtered = filtered[filtered["mosaic_brand"] == selected_brand]
if selected_media != "All":
    filtered = filtered[filtered["media_type"] == selected_media]
if selected_theme != "All":
    filtered = filtered[filtered["message_theme"] == selected_theme]
filtered = filtered[filtered["days_live"] <= max_days]

st.subheader("Weekly AI Brief")
for action in monday_actions(filtered if len(filtered) else df):
    st.markdown(f"- {action}")

st.subheader("Format + Theme Trends")
st.dataframe(trend_table(filtered if len(filtered) else df), use_container_width=True)

st.subheader("Longevity Signals (Likely Winners)")
st.dataframe(longevity_winners(filtered if len(filtered) else df), use_container_width=True)

st.subheader("Gap Detection")
st.dataframe(gap_detection(filtered if len(filtered) else df), use_container_width=True)

st.subheader("Raw ads")
st.dataframe(
    filtered[
        [
            "mosaic_brand",
            "competitor_brand",
            "media_type",
            "message_theme",
            "days_live",
            "started_on",
            "ad_text",
        ]
    ],
    use_container_width=True,
)
