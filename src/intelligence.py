from __future__ import annotations

from datetime import date

import pandas as pd


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["started_on"] = pd.to_datetime(out["started_on"], errors="coerce")
    out["days_live"] = (pd.Timestamp(date.today()) - out["started_on"]).dt.days
    out["days_live"] = out["days_live"].fillna(0).astype(int)
    return out


def trend_table(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["mosaic_brand", "competitor_brand", "media_type"], as_index=False)
        .size()
        .rename(columns={"size": "ad_count"})
        .sort_values(["mosaic_brand", "ad_count"], ascending=[True, False])
    )


def longevity_winners(df: pd.DataFrame, top_n=10) -> pd.DataFrame:
    cols = [
        "mosaic_brand",
        "competitor_brand",
        "media_type",
        "message_theme",
        "days_live",
        "started_on",
        "ad_text",
    ]
    return df.sort_values("days_live", ascending=False)[cols].head(top_n)


def gap_detection(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for brand, brand_df in df.groupby("mosaic_brand"):
        used = set(brand_df["message_theme"].dropna().unique())
        universe = {"offer_promo", "problem_solution", "social_proof", "education", "urgency"}
        gaps = sorted(universe - used)
        rows.append({"mosaic_brand": brand, "missing_themes": ", ".join(gaps) if gaps else "none"})
    return pd.DataFrame(rows)


def monday_actions(df: pd.DataFrame) -> list[str]:
    actions = []
    for brand, sub in df.groupby("mosaic_brand"):
        media_share = sub["media_type"].value_counts(normalize=True)
        dominant_media = media_share.index[0] if len(media_share) else "unknown"

        long_live = sub[sub["days_live"] >= 30]
        top_theme = (
            long_live["message_theme"].value_counts().index[0]
            if len(long_live)
            else sub["message_theme"].value_counts().index[0]
        )

        actions.append(
            f"{brand}: Test {dominant_media} creatives this week using a '{top_theme}' hook; competitors keep these live longest."
        )

        abandoned = sub[sub["days_live"] <= 7]["media_type"].value_counts()
        if len(abandoned):
            actions.append(
                f"{brand}: Avoid over-investing in {abandoned.index[0]} until fresh angle is validated; it has the highest short-lived churn among competitors."
            )
    return actions
