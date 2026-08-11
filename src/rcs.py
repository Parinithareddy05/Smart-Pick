import numpy as np
import pandas as pd
from config import CONFIDENCE_THRESHOLDS


def compute_rcs(df: pd.DataFrame) -> pd.DataFrame:
    """
    Layer 1 — Review Confidence Score (RCS).

    confidence_i = log(max(review_count_i, 2)) / log(max(review_count))
    adjusted_rating_i = raw_rating_i × confidence_i
    adjusted_rating_norm_i = adjusted_rating_i / 5.0   (scale to [0, 1])

    Clamping review_count to min=2 prevents log(1)=0 from zeroing
    out a single-review product's adjusted rating entirely.
    """
    df = df.copy()

    safe_counts = df["review_count"].clip(lower=2)
    max_count = safe_counts.max()

    df["confidence"] = np.log(safe_counts) / np.log(max_count)
    df["adjusted_rating"] = df["raw_rating"] * df["confidence"]
    df["adjusted_rating_norm"] = df["adjusted_rating"] / 5.0

    df = _assign_confidence_label(df)
    print(f"[rcs] Confidence range: {df['confidence'].min():.3f} – {df['confidence'].max():.3f}")
    return df


def _assign_confidence_label(df: pd.DataFrame) -> pd.DataFrame:
    high = CONFIDENCE_THRESHOLDS["high"]
    med  = CONFIDENCE_THRESHOLDS["medium"]

    conditions = [
        df["confidence"] >= high,
        df["confidence"] >= med,
    ]
    labels = ["High Confidence", "Medium Confidence"]
    df["confidence_label"] = np.select(conditions, labels, default="Low Confidence")
    return df
