import pandas as pd
from config import PERSONAS


def _norm_price_inverted(series: pd.Series) -> pd.Series:
    """Min-max normalize price then invert so lower price = higher score."""
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series([0.5] * len(series), index=series.index)
    return 1.0 - (series - mn) / (mx - mn)


def compute_pavs(df: pd.DataFrame, persona_key: str) -> pd.DataFrame:
    """
    Layer 2 — Persona-Adaptive Value Score (PAVS).

    value_score = wp × norm_price_inverted + wr × adjusted_rating_norm + wt × trend_score

    All inputs are in [0, 1]:
      - norm_price_inverted: global min-max, inverted (lower price → higher score)
      - adjusted_rating_norm: adjusted_rating / 5.0 (from RCS layer)
      - trend_score: PTI output, 0.5 neutral, >0.5 dropping (good), <0.5 rising (bad)
    """
    df = df.copy()
    p = PERSONAS[persona_key]
    wp, wr, wt = p["wp"], p["wr"], p.get("wt", 0.0)

    if "norm_price_inverted" not in df.columns:
        df["norm_price_inverted"] = _norm_price_inverted(df["price"])

    # Min-max normalize rating within this result set (amplifies within-group differences)
    r_min, r_max = df["adjusted_rating"].min(), df["adjusted_rating"].max()
    if r_max > r_min:
        adj_rating_norm = (df["adjusted_rating"] - r_min) / (r_max - r_min)
    else:
        adj_rating_norm = df["adjusted_rating_norm"]  # fallback: /5.0

    # trend_score defaults to 0.5 if PTI hasn't run yet
    trend_score = df["trend_score"] if "trend_score" in df.columns else 0.5

    df[f"value_score_{persona_key}"] = (
        wp * df["norm_price_inverted"]
        + wr * adj_rating_norm
        + wt * trend_score
    )
    return df


def compute_all_personas(df: pd.DataFrame) -> pd.DataFrame:
    """Compute value scores and ranks for all three personas."""
    # Compute inverted price norm once
    df = df.copy()
    df["norm_price_inverted"] = _norm_price_inverted(df["price"])

    for key in PERSONAS:
        df = compute_pavs(df, key)
        df[f"rank_{key}"] = (
            df[f"value_score_{key}"]
            .rank(ascending=False, method="min")
            .astype(int)
        )

    print(f"[pavs] Value scores computed for {list(PERSONAS.keys())}")
    return df
