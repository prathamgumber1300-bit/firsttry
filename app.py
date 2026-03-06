from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.intelligence import enrich, gap_detection, longevity_winners, monday_actions, trend_table

st.set_page_config(page_title="Mosaic Competitive Intelligence", layout="wide", page_icon="📊")

st.markdown(
    """
    <style>
      .main {background: linear-gradient(180deg, #f8fbff 0%, #eef4ff 100%);} 
      .block-container {padding-top: 1.4rem;}
      .kpi-card {
          background: linear-gradient(135deg, #0f62fe 0%, #6f42c1 100%);
          border-radius: 14px;
          padding: 0.9rem 1rem;
          color: white;
          margin-bottom: 0.6rem;
      }
      .kpi-title {font-size: 0.85rem; opacity: 0.9;}
      .kpi-value {font-size: 1.5rem; font-weight: 700;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🚀 Mosaic Meta Ad Intelligence")
st.caption("Track competitor ad strategy shifts with visual insights, trend charts, and weekly actions.")

DATA_PATH = Path("data/meta_ads_latest.csv")

if not DATA_PATH.exists():
    st.warning("No data found. Add `data/meta_ads_latest.csv` or run: `python scripts/scrape_meta_ads.py`")
    st.stop()

raw = pd.read_csv(DATA_PATH)
if raw.empty:
    st.warning("Data file exists but is empty. Please refresh data and reload the dashboard.")
    st.stop()

df = enrich(raw)

# ---------- Filters ----------
st.subheader("🎛️ Filter Controls")
brands = ["All"] + sorted(df["mosaic_brand"].dropna().unique().tolist())
media_types = ["All"] + sorted(df["media_type"].dropna().unique().tolist())
themes = ["All"] + sorted(df["message_theme"].dropna().unique().tolist())

c1, c2, c3, c4 = st.columns(4)
selected_brand = c1.selectbox("Mosaic Brand", brands)
selected_media = c2.selectbox("Ad Format", media_types)
selected_theme = c3.selectbox("Message Theme", themes)

min_days_live = int(df["days_live"].min()) if len(df) else 0
max_days_live = int(df["days_live"].max()) if len(df) else 1
default_max = min(90, max_days_live)
max_days = c4.slider("Max Recency (days live)", min_days_live, max_days_live, default_max)

filtered = df.copy()
if selected_brand != "All":
    filtered = filtered[filtered["mosaic_brand"] == selected_brand]
if selected_media != "All":
    filtered = filtered[filtered["media_type"] == selected_media]
if selected_theme != "All":
    filtered = filtered[filtered["message_theme"] == selected_theme]
filtered = filtered[filtered["days_live"] <= max_days]

if filtered.empty:
    st.warning("No ads match current filters. Try widening recency or setting more filters to 'All'.")

analysis_df = filtered

# ---------- KPI Cards ----------
st.subheader("📌 Snapshot KPIs")
if not analysis_df.empty:
    total_ads = len(analysis_df)
    unique_competitors = analysis_df["competitor_brand"].nunique()
    avg_days_live = round(analysis_df["days_live"].mean(), 1)
    dominant_format = analysis_df["media_type"].mode().iat[0]
else:
    total_ads = unique_competitors = 0
    avg_days_live = 0
    dominant_format = "N/A"

k1, k2, k3, k4 = st.columns(4)
for col, title, value in [
    (k1, "📣 Ads in View", total_ads),
    (k2, "🏷️ Competitors", unique_competitors),
    (k3, "⏳ Avg Days Live", avg_days_live),
    (k4, "🎬 Dominant Format", dominant_format),
]:
    col.markdown(
        f"<div class='kpi-card'><div class='kpi-title'>{title}</div><div class='kpi-value'>{value}</div></div>",
        unsafe_allow_html=True,
    )

# ---------- Charts ----------
st.subheader("📈 Visual Intelligence")
left, right = st.columns(2)

if not analysis_df.empty:
    by_format = analysis_df["media_type"].value_counts().reset_index()
    by_format.columns = ["media_type", "ad_count"]
    fig_format = px.bar(
        by_format,
        x="media_type",
        y="ad_count",
        color="media_type",
        title="Ad Count by Format",
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    fig_format.update_layout(showlegend=False, xaxis_title="Format", yaxis_title="Ads")
    left.plotly_chart(fig_format, use_container_width=True)

    by_theme = analysis_df["message_theme"].value_counts().reset_index()
    by_theme.columns = ["message_theme", "ad_count"]
    fig_theme = px.pie(
        by_theme,
        names="message_theme",
        values="ad_count",
        title="Theme Share",
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    right.plotly_chart(fig_theme, use_container_width=True)

    line_df = analysis_df.copy()
    line_df["started_on"] = pd.to_datetime(line_df["started_on"], errors="coerce")
    line_df = (
        line_df.dropna(subset=["started_on"])
        .groupby([pd.Grouper(key="started_on", freq="W"), "mosaic_brand"], as_index=False)
        .size()
        .rename(columns={"size": "ad_count"})
    )
    if not line_df.empty:
        fig_line = px.line(
            line_df,
            x="started_on",
            y="ad_count",
            color="mosaic_brand",
            markers=True,
            title="Weekly New Ads by Mosaic Brand",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("Charts will appear once filters return at least one row.")

# ---------- Insight Tables ----------
st.subheader("🧠 Weekly AI Brief")
for action in monday_actions(analysis_df):
    st.markdown(f"- {action}")

st.subheader("📊 Format + Theme Trends")
st.dataframe(trend_table(analysis_df), use_container_width=True)

st.subheader("🏆 Longevity Signals (Likely Winners)")
st.dataframe(longevity_winners(analysis_df), use_container_width=True)

st.subheader("🕳️ Gap Detection")
st.dataframe(gap_detection(analysis_df), use_container_width=True)

st.subheader("🗂️ Raw Ads Explorer")
st.dataframe(
    analysis_df[
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
