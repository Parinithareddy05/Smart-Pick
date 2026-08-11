import numpy as np
import pandas as pd
from scipy.stats import linregress as _linregress
from config import PTI_THRESHOLD, PRICE_HISTORY_DAYS


def fit_price_trends(df_history: pd.DataFrame) -> pd.DataFrame:
    """
    Layer 3 — Price Trend Indicator (PTI).

    Fits a LinearRegression on each product's 30-day price history.
    Classifies trend using normalized slope = slope / mean_price
    to be scale-invariant across cheap and expensive products.
    """
    records = []

    for product_id, group in df_history.groupby("product_id"):
        # Deduplicate by day (keep last price if same day appears twice)
        group_sorted = (group.sort_values("day")
                            .drop_duplicates(subset="day", keep="last"))
        # Cap to last PRICE_HISTORY_DAYS entries
        group_sorted = group_sorted.tail(PRICE_HISTORY_DAYS)
        y = group_sorted["price"].values.astype(float)

        if len(y) < 2:
            records.append({
                "product_id": product_id,
                "slope": 0.0,
                "norm_slope": 0.0,
                "r_squared": 0.0,
                "trend_score": 0.5,
                "trend_label": "Price Stable",
                "trend_signal": "No urgency",
                "low_confidence": True,
            })
            continue

        # Build X from actual number of data points (not fixed PRICE_HISTORY_DAYS)
        x_fit = np.arange(len(y), dtype=float)
        lr = _linregress(x_fit, y)
        slope  = float(lr.slope)
        r_sq   = float(lr.rvalue ** 2)
        p_val  = float(lr.pvalue)
        mean_price = float(y.mean())
        norm_slope = slope / mean_price if mean_price > 0 else 0.0

        # Only classify as Dropping/Rising if trend is statistically significant
        if p_val < 0.05:
            trend_label, trend_signal = _classify_trend(norm_slope)
        else:
            trend_label, trend_signal = "Price Stable", "Trend not significant"

        low_conf = r_sq < 0.3

        # trend_score ∈ [0,1]: 1=strongly dropping (good buy), 0.5=stable, 0=strongly rising
        # Dampened by r_sq so low-confidence trends barely move the score
        trend_score = float(np.clip(0.5 - norm_slope * r_sq * 5, 0.0, 1.0))

        records.append({
            "product_id": product_id,
            "slope": round(slope, 4),
            "norm_slope": round(norm_slope, 6),
            "r_squared": round(r_sq, 4),
            "trend_score": round(trend_score, 4),
            "trend_label": trend_label,
            "trend_signal": trend_signal + ("*" if low_conf else ""),
            "low_confidence": low_conf,
        })

    df_trends = pd.DataFrame(records)
    counts = df_trends["trend_label"].value_counts().to_dict()
    print(f"[pti] Trend distribution: {counts}")
    return df_trends


def _classify_trend(norm_slope: float):
    if norm_slope < -PTI_THRESHOLD:
        return "Price Dropping", "Good time to buy"
    elif norm_slope > PTI_THRESHOLD:
        return "Price Rising", "Buy now or wait for drop"
    else:
        return "Price Stable", "No urgency"


def merge_trends(df: pd.DataFrame, df_trends: pd.DataFrame) -> pd.DataFrame:
    """Left-merge trend columns into main products DataFrame."""
    trend_cols = ["product_id", "slope", "norm_slope", "r_squared", "trend_score",
                  "trend_label", "trend_signal", "low_confidence"]
    df = df.merge(df_trends[trend_cols], on="product_id", how="left")
    df["trend_label"] = df["trend_label"].fillna("Unknown")
    df["trend_signal"] = df["trend_signal"].fillna("No data")
    df["trend_score"] = df["trend_score"].fillna(0.5)
    return df
