"""
SmartPick Evaluation — runs the full live pipeline on a fixed set of real products
and measures:
  1. PTI quality  — % real price history, R² distribution, min-days flag
  2. PAVS vs baselines — satisfaction score lift (top-K), per category
  3. Spearman / Kendall rank correlation
  4. Wilcoxon signed-rank test for statistical significance

Usage:
    conda activate mlproject
    cd <project_root>
    python src/evaluate.py
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, kendalltau, wilcoxon

from config import PERSONAS, RESULTS_DIR
from scraper import url_parser, aggregator
import live_pipeline
from eval_cache import load_cache, save_cache, get_cached, set_cached

_eval_cache = None  # loaded lazily

def _get_eval_cache():
    global _eval_cache
    if _eval_cache is None:
        _eval_cache = load_cache()
    return _eval_cache


# ── Test product set ──────────────────────────────────────────────────────────
# Format: (label, amazon_url, category)
TEST_PRODUCTS = [
    # ── Phones ────────────────────────────────────────────────────────────────
    ("Samsung Galaxy A55 5G",   "https://www.amazon.in/dp/B0CWPD9PTK", "phone"),
    ("iQOO Z9s Pro",            "https://www.amazon.in/dp/B0DW47JCHW", "phone"),
    ("Samsung Galaxy S25",      "https://www.amazon.in/dp/B0GL86QFC4", "phone"),
    ("Realme P3 Pro",           "https://www.amazon.in/dp/B0G4B8957C", "phone"),
    ("Apple iPhone Air 256GB",  "https://www.amazon.in/dp/B0FQFBDQJ1", "phone"),
    ("iQOO Z10 5G",             "https://www.amazon.in/dp/B0GL8NJDG5", "phone"),   # lower-rated
    ("Motorola G57 5G",         "https://www.amazon.in/dp/B0G3SWTTQ7", "phone"),   # lower-rated

    # ── Laptops ───────────────────────────────────────────────────────────────
    ("Lenovo IdeaPad Slim 3 i5-12450H", "https://www.amazon.in/dp/B0FH71SN5N", "laptop"),
    ("Lenovo IdeaPad i5-13420H",        "https://www.amazon.in/dp/B0F637DPFW", "laptop"),
    ("ASUS TUF Gaming F15",             "https://www.amazon.in/dp/B0F8P4Y7VF", "laptop"),
    ("HP Office fd1354TU",              "https://www.amazon.in/dp/B0F5B1N9SJ", "laptop"),
    ("Dell 15 i5-1334U",                "https://www.amazon.in/dp/B0DSFQZTVW", "laptop"),
    ("Dell 15 Platinum i7",             "https://www.amazon.in/dp/B0FDQ2R315", "laptop"),  # lower-rated
    ("HP Victus i7-14650HX",            "https://www.amazon.in/dp/B0FM3WC2QY", "laptop"),  # lower-rated

    # ── Earphones / Headphones ────────────────────────────────────────────────
    ("OnePlus Nord Buds Pro",   "https://www.amazon.in/dp/B0FMDL81GS", "earphone"),
    ("Realme Buds Air 6",       "https://www.amazon.in/dp/B0DBGP48NW", "earphone"),
    ("Redmi Buds 5 Pro",        "https://www.amazon.in/dp/B0CQJZD55X", "earphone"),
    ("Noise Cancellation Pro",  "https://www.amazon.in/dp/B09Y5MK1KB", "earphone"),
    ("boAt Airdopes Alpha",     "https://www.amazon.in/dp/B0C3ZYFZ77", "earphone"),
    ("Realme Buds Wireless 3",  "https://www.amazon.in/dp/B0FVLFTL4B", "earphone"), # lower-rated
    ("Realme Earphones R1",     "https://www.amazon.in/dp/B0G1B93FV2", "earphone"), # lower-rated
]

MIN_HISTORY_DAYS = 14   # flag PTI as unreliable below this
TOP_K_FRACTION   = 0.4  # use top 40% of results for satisfaction score (min 2)


# ── Core evaluation ───────────────────────────────────────────────────────────

def satisfaction_score(df: pd.DataFrame, wp: float, wr: float, wt: float, top_k: int) -> float:
    """Mean persona utility for top-K products using absolute quality scale."""
    k = min(top_k, len(df))
    return float((
        wp * df["norm_price_inverted"].iloc[:k]
        + wr * df["adjusted_rating_norm"].iloc[:k]
    ).mean())


def compute_top_k(n_products: int) -> int:
    return max(2, int(np.ceil(n_products * TOP_K_FRACTION)))


def evaluate_product(label: str, url: str, category: str) -> dict | None:
    print(f"\n{'='*60}")
    print(f"  [{category.upper()}] {label}")
    print(f"  URL: {url[:70]}")
    print(f"{'='*60}")

    # ── Cache check (before any network calls) ───────────────────────────────
    cache = _get_eval_cache()
    cached = get_cached(cache, url)
    if cached:
        scraped_rows, history_override = cached
        print(f"  [cache] HIT — using cached data ({len(scraped_rows)} products)")
        source_site = "amazon" if "amazon" in url else "flipkart"
    else:
        history_override = None
        # Step 1 — parse URL (network call to fetch title if needed)
        try:
            query, source_site = url_parser.extract_query(url)
            original_name = url_parser.extract_full_name(url)
        except Exception as e:
            print(f"  [SKIP] URL parse failed: {e}")
            return None

    # Step 2 — scrape (only on cache miss)
    if history_override is None:
        scraped_rows = aggregator.scrape_all_sites(query, original_name=original_name)
        print(f"  [cache] MISS — scraped {len(scraped_rows)} products")
    if not scraped_rows:
        print(f"  [SKIP] No products scraped")
        return None
    print(f"  Scraped {len(scraped_rows)} products")

    # Step 3 — full pipeline
    try:
        df, df_history, collected_history = live_pipeline.run_live_pipeline(
            scraped_rows, persona="balanced", source_url=url,
            return_history=True, history_override=history_override
        )
        # Save to cache if this was a fresh fetch
        if history_override is None:
            set_cached(cache, url, scraped_rows, collected_history)
            save_cache(cache)
    except Exception as e:
        print(f"  [SKIP] Pipeline failed: {e}")
        return None

    if df.empty or len(df) < 2:
        print(f"  [SKIP] Too few products ({len(df)}) to evaluate")
        return None

    print(f"  Products after pipeline: {len(df)}")

    top_k = compute_top_k(len(df))

    # ── PTI metrics ───────────────────────────────────────────────────────────
    real_mask  = df["history_source"] == "real"
    real_count = real_mask.sum()
    mean_r2    = df.loc[real_mask, "r_squared"].mean() if real_count > 0 else 0.0

    # Count products with insufficient history days (< MIN_HISTORY_DAYS)
    days_per_product = df_history.groupby("product_id")["day"].count()
    low_data_count   = (days_per_product < MIN_HISTORY_DAYS).sum()

    trend_dist = df["trend_label"].value_counts().to_dict()

    # ── Baseline ranks ────────────────────────────────────────────────────────
    df = df.copy()
    df["rank_price_only"]  = df["price"].rank(ascending=True,  method="min").astype(int)
    df["rank_rating_only"] = df["raw_rating"].rank(ascending=False, method="min").astype(int)

    # ── Satisfaction + correlation per persona ────────────────────────────────
    persona_results = {}
    for key, meta in PERSONAS.items():
        wp, wr, wt = meta["wp"], meta["wr"], meta.get("wt", 0.0)

        df_pavs   = df.sort_values(f"value_score_{key}", ascending=False)
        df_price  = df.sort_values("price",      ascending=True)
        df_rating = df.sort_values("raw_rating", ascending=False)

        sat_pavs   = satisfaction_score(df_pavs,   wp, wr, wt, top_k)
        sat_price  = satisfaction_score(df_price,  wp, wr, wt, top_k)
        sat_rating = satisfaction_score(df_rating, wp, wr, wt, top_k)

        lift_vs_price  = (sat_pavs - sat_price)  / sat_price  * 100 if sat_price  > 0 else 0.0
        lift_vs_rating = (sat_pavs - sat_rating) / sat_rating * 100 if sat_rating > 0 else 0.0

        with np.errstate(invalid="ignore"):
            rho_price,  _ = spearmanr(df[f"rank_{key}"], df["rank_price_only"])
            rho_rating, _ = spearmanr(df[f"rank_{key}"], df["rank_rating_only"])
            tau_price,  _ = kendalltau(df[f"rank_{key}"], df["rank_price_only"])
            tau_rating, _ = kendalltau(df[f"rank_{key}"], df["rank_rating_only"])

        persona_results[key] = {
            "sat_pavs":           round(float(sat_pavs),   4),
            "sat_price_only":     round(float(sat_price),  4),
            "sat_rating_only":    round(float(sat_rating), 4),
            "lift_vs_price":      round(float(lift_vs_price),  2),
            "lift_vs_rating":     round(float(lift_vs_rating), 2),
            "spearman_vs_price":  round(float(rho_price)  if not np.isnan(rho_price)  else 0.0, 4),
            "spearman_vs_rating": round(float(rho_rating) if not np.isnan(rho_rating) else 0.0, 4),
            "kendall_vs_price":   round(float(tau_price)  if not np.isnan(tau_price)  else 0.0, 4),
            "kendall_vs_rating":  round(float(tau_rating) if not np.isnan(tau_rating) else 0.0, 4),
        }

    return {
        "label":    label,
        "url":      url,
        "category": category,
        "n_products": len(df),
        "top_k":      top_k,
        "sites":      df["site"].value_counts().to_dict(),
        "pti": {
            "real_history_count":  int(real_count),
            "total":               len(df),
            "real_history_pct":    round(real_count / len(df) * 100, 1),
            "mean_r2":             round(float(mean_r2), 4),
            "low_data_products":   int(low_data_count),
            "trend_distribution":  trend_dist,
        },
        "personas": persona_results,
    }


def aggregate_results(results: list[dict]) -> dict:
    """Overall + per-category aggregation with Wilcoxon significance test."""
    valid = [r for r in results if r is not None]
    if not valid:
        return {}

    categories = sorted(set(r["category"] for r in valid))

    def agg_group(group: list[dict]) -> dict:
        if not group:
            return {}
        out = {
            "n": len(group),
            "avg_products_per_search": round(np.mean([r["n_products"] for r in group]), 1),
            "pti": {
                "avg_real_history_pct": round(np.mean([r["pti"]["real_history_pct"] for r in group]), 1),
                "avg_r2": round(float(np.mean([r["pti"]["mean_r2"] for r in group if r["pti"]["mean_r2"] > 0]) if any(r["pti"]["mean_r2"] > 0 for r in group) else 0), 4),
                "avg_low_data_products": round(np.mean([r["pti"]["low_data_products"] for r in group]), 1),
            },
            "personas": {},
        }

        for key in PERSONAS:
            metrics = [r["personas"][key] for r in group if key in r.get("personas", {})]
            if not metrics:
                continue

            pavs_scores  = [m["sat_pavs"]        for m in metrics]
            price_scores = [m["sat_price_only"]  for m in metrics]
            rating_scores= [m["sat_rating_only"] for m in metrics]
            lifts_price  = [m["lift_vs_price"]   for m in metrics]
            lifts_rating = [m["lift_vs_rating"]  for m in metrics]

            # Wilcoxon signed-rank test (needs ≥ 5 samples ideally, skip if too few)
            def wilcoxon_p(a, b):
                diff = [x - y for x, y in zip(a, b)]
                if len(diff) < 3 or all(d == 0 for d in diff):
                    return None
                try:
                    _, p = wilcoxon(diff, alternative="greater")
                    return round(float(p), 4)
                except Exception:
                    return None

            out["personas"][key] = {
                "avg_sat_pavs":           round(np.mean(pavs_scores),   4),
                "avg_sat_price_only":     round(np.mean(price_scores),  4),
                "avg_sat_rating_only":    round(np.mean(rating_scores), 4),
                "avg_lift_vs_price":      round(np.mean(lifts_price),   2),
                "avg_lift_vs_rating":     round(np.mean(lifts_rating),  2),
                "avg_spearman_vs_price":  round(np.mean([m["spearman_vs_price"]  for m in metrics]), 4),
                "avg_spearman_vs_rating": round(np.mean([m["spearman_vs_rating"] for m in metrics]), 4),
                "avg_kendall_vs_price":   round(np.mean([m["kendall_vs_price"]   for m in metrics]), 4),
                "avg_kendall_vs_rating":  round(np.mean([m["kendall_vs_rating"]  for m in metrics]), 4),
                "wilcoxon_p_vs_price":    wilcoxon_p(pavs_scores, price_scores),
                "wilcoxon_p_vs_rating":   wilcoxon_p(pavs_scores, rating_scores),
            }
        return out

    result = {
        "overall":    agg_group(valid),
        "by_category": {cat: agg_group([r for r in valid if r["category"] == cat])
                        for cat in categories},
    }
    return result


def print_report(results: list[dict], agg: dict):
    overall = agg.get("overall", {})
    print("\n\n" + "="*70)
    print("  SMARTPICK EVALUATION REPORT")
    print("="*70)

    print(f"\nProducts evaluated : {overall.get('n', 0)} / {len(TEST_PRODUCTS)}")
    print(f"Avg results/search : {overall.get('avg_products_per_search', 0)} products")

    pti = overall.get("pti", {})
    print(f"\n── PTI (Price Trend Indicator) ──────────────────────────────────────")
    print(f"  Real price history (pricehistory.app) : {pti.get('avg_real_history_pct', 0)}%")
    print(f"  Mean R²                               : {pti.get('avg_r2', 0)}")
    print(f"  Avg products with <{MIN_HISTORY_DAYS} days history  : {pti.get('avg_low_data_products', 0)}")

    def print_persona_table(data: dict, title: str):
        personas = data.get("personas", {})
        if not personas:
            return
        print(f"\n── {title} ─────────────────────────────────────")
        header = f"  {'Persona':<14} {'PAVS':>7} {'Price':>8} {'Rating':>8} {'↑Price':>9} {'↑Rating':>9} {'p(price)':>10} {'p(rating)':>10}"
        print(header)
        print("  " + "-" * 80)
        for key, meta in PERSONAS.items():
            p = personas.get(key, {})
            if not p:
                continue
            pp  = f"{p['wilcoxon_p_vs_price']:.4f}"  if p.get("wilcoxon_p_vs_price")  is not None else "  n/a  "
            pr  = f"{p['wilcoxon_p_vs_rating']:.4f}" if p.get("wilcoxon_p_vs_rating") is not None else "  n/a  "
            print(f"  {meta['label']:<14} "
                  f"{p['avg_sat_pavs']:>7.4f} "
                  f"{p['avg_sat_price_only']:>8.4f} "
                  f"{p['avg_sat_rating_only']:>8.4f} "
                  f"{p['avg_lift_vs_price']:>+8.1f}% "
                  f"{p['avg_lift_vs_rating']:>+8.1f}% "
                  f"{pp:>10} "
                  f"{pr:>10}")

        print(f"\n  Spearman ρ (lower = more different from baseline):")
        print(f"  {'Persona':<14} {'ρ vs Price':>12} {'ρ vs Rating':>13}")
        print("  " + "-" * 42)
        for key, meta in PERSONAS.items():
            p = personas.get(key, {})
            if not p:
                continue
            print(f"  {meta['label']:<14} "
                  f"{p['avg_spearman_vs_price']:>12.4f} "
                  f"{p['avg_spearman_vs_rating']:>13.4f}")

    print_persona_table(overall, "OVERALL — PAVS vs Baselines")

    for cat, cat_data in agg.get("by_category", {}).items():
        n = cat_data.get("n", 0)
        print_persona_table(cat_data, f"{cat.upper()} (n={n})")

    print(f"\n  p-value < 0.05 = statistically significant improvement\n")


def main():
    all_results = []
    for label, url, category in TEST_PRODUCTS:
        result = evaluate_product(label, url, category)
        all_results.append(result)

    valid = [r for r in all_results if r is not None]
    agg   = aggregate_results(valid)

    print_report(valid, agg)

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / "evaluation_report.json"
    with open(out_path, "w") as f:
        json.dump({"summary": agg, "per_product": valid}, f, indent=2)
    print(f"Full results saved to {out_path}\n")


if __name__ == "__main__":
    main()
