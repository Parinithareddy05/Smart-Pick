"""
Live pipeline — takes scraped product rows, runs RCS + PTI + PAVS, returns ranked DataFrame.
Uses real price history from pricehistory.app for Amazon and Flipkart products (falls back to simulated).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import pandas as pd
from config import PERSONAS
import rcs
import pti
import pavs


def _simulate_history(product_id: str, current_price: float) -> list:
    """Generate a deterministic 30-day simulated price history as fallback."""
    seed = abs(hash(product_id)) % 100000
    rng = np.random.default_rng(seed)
    regime = seed % 3  # 0=dropping, 1=stable, 2=rising
    trends = [(-0.005, 0.01), (0.0, 0.01), (0.005, 0.01)]
    drift, noise_std = trends[regime]
    prices = []
    p = current_price
    for _ in range(30):
        p = p * (1 + drift + rng.normal(0, noise_std))
        prices.append(max(p, 1.0))
    # Anchor last day to current price
    prices[-1] = current_price
    return [{"product_id": product_id, "day": i, "price": prices[i]} for i in range(30)]


def _get_real_price_history(buy_url: str, product_id: str) -> list:
    """
    Try to fetch real price history from pricehistory.app for an Amazon or Flipkart product.
    Returns list of {product_id, day, price} dicts, or [] if unavailable.
    """
    site = "flipkart" if "flipkart.com" in buy_url else "amazon"
    try:
        from scraper.pricehistory_scraper import get_price_history_for_url, history_to_pti_format
        history, summary = get_price_history_for_url(buy_url, site)
        if history:
            return history_to_pti_format(history, product_id)
    except Exception as e:
        print(f"[live_pipeline] pricehistory fetch failed: {e}")
    return []


def run_live_pipeline(
    scraped_rows: list,
    persona: str = "balanced",
    source_url: str = "",
    return_history: bool = False,
    history_override: dict = None,
) -> pd.DataFrame:
    """
    scraped_rows: list of dicts — product_id, product_name, price, raw_rating,
                  review_count, buy_url, site
    Returns fully-ranked DataFrame sorted by the requested persona's value score.
    """
    if not scraped_rows:
        return pd.DataFrame()

    df = pd.DataFrame(scraped_rows)

    # Clean
    df = df.dropna(subset=["price", "raw_rating", "review_count"])
    df = df[df["price"] > 0]
    df["raw_rating"]   = pd.to_numeric(df["raw_rating"], errors="coerce").clip(1.0, 5.0).fillna(3.5)
    df["review_count"] = pd.to_numeric(df["review_count"], errors="coerce").fillna(1).astype(int)

    # Deduplicate — same product_id from multiple sources → keep highest review_count
    df = (df.sort_values("review_count", ascending=False)
            .drop_duplicates(subset="product_id", keep="first")
            .reset_index(drop=True))

    if df.empty:
        return df

    # ── Build price history ───────────────────────────────────────────────────
    # Priority: 1) Real history from pricehistory.app (Amazon + Flipkart)  2) Simulated fallback
    history_records = []
    real_count = 0

    history_source = {}   # product_id → "real" | "simulated"
    collected_history = {}   # buy_url -> list of records (for caching)

    for row in df.itertuples():
        if history_override is not None and row.buy_url in history_override:
            real_records = history_override[row.buy_url]
            # Re-stamp product_id in case it changed after dedup
            for rec in real_records:
                rec["product_id"] = row.product_id
        else:
            real_records = _get_real_price_history(row.buy_url, row.product_id)

        if real_records:
            history_records.extend(real_records)
            real_count += 1
            history_source[row.product_id] = "real"
            collected_history[row.buy_url] = real_records
        else:
            sim = _simulate_history(row.product_id, row.price)
            history_records.extend(sim)
            history_source[row.product_id] = "simulated"
            collected_history[row.buy_url] = sim

    df["history_source"] = df["product_id"].map(history_source)
    df_history = pd.DataFrame(history_records)

    print(f"[live_pipeline] Real price history: {real_count}/{len(df)} products "
          f"({len(df) - real_count} using simulated fallback)")

    # Layer 1 — RCS
    df = rcs.compute_rcs(df)

    # Layer 2 — PTI
    df_trends = pti.fit_price_trends(df_history)
    df = pti.merge_trends(df, df_trends)

    # Layer 3 — PAVS (all 3 personas)
    df = pavs.compute_all_personas(df)

    # Sort by requested persona
    score_col = f"value_score_{persona}"
    if score_col not in df.columns:
        score_col = "value_score_balanced"
    df = df.sort_values(score_col, ascending=False).reset_index(drop=True)
    df["live_rank"] = range(1, len(df) + 1)

    if return_history:
        return df, df_history, collected_history
    return df
