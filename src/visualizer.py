"""
SmartPick Visualizer — reads results/evaluation_report.json and generates
5 IEEE paper-quality charts saved to results/charts/

Usage:
    python src/visualizer.py
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from config import RESULTS_DIR, PERSONAS

CHARTS_DIR = RESULTS_DIR / "charts"

# ── IEEE-style rcParams ────────────────────────────────────────────────────────
IEEE_RC = {
    "figure.facecolor":      "white",
    "axes.facecolor":        "white",
    "axes.edgecolor":        "#333333",
    "axes.linewidth":        0.8,
    "axes.grid":             True,
    "grid.color":            "#CCCCCC",
    "grid.linestyle":        "--",
    "grid.linewidth":        0.5,
    "grid.alpha":            0.7,
    "axes.axisbelow":        True,
    "font.family":           "serif",
    "font.size":             9,
    "axes.titlesize":        13,
    "axes.titleweight":      "bold",
    "axes.labelsize":        10,
    "xtick.labelsize":       9,
    "ytick.labelsize":       9,
    "legend.fontsize":       8,
    "legend.framealpha":     0.9,
    "legend.edgecolor":      "#AAAAAA",
    "savefig.dpi":           200,
    "savefig.bbox":          "tight",
    "savefig.facecolor":     "white",
}

PERSONA_LABELS = {k: v["label"] for k, v in PERSONAS.items()}
PERSONA_KEYS   = list(PERSONAS.keys())   # ["budget", "quality", "balanced"]

COLORS = {
    "pavs":         "#2171B5",   # blue
    "price_only":   "#E87B4C",   # orange
    "rating_only":  "#D62728",   # red
    "real":         "#2171B5",   # blue  (PTI)
    "simulated":    "#AAAAAA",   # grey  (PTI)
    "lift_pos":     "#2CA02C",   # green (positive lift)
    "lift_neg":     "#D62728",   # red   (negative lift)
}


# ── Data loading ───────────────────────────────────────────────────────────────

def load_report() -> dict:
    """
    Load evaluation_report.json.
    Handles two formats:
      - Old format:  {"summary": {"personas": {...}, "pti": {...}}, "per_product": [...]}
      - New format:  {"summary": {"overall": {...}, "by_category": {...}}, "per_product": [...]}
    Returns a normalised dict with keys: summary, per_product.
    summary always contains sub-keys: personas, pti.
    """
    path = RESULTS_DIR / "evaluation_report.json"
    if not path.exists():
        raise FileNotFoundError(f"Run evaluate.py first — {path} not found")

    with open(path) as f:
        data = json.load(f)

    # Detect format and normalise
    raw_summary = data.get("summary", data.get("overall", {}))

    # New format: summary has "overall" and "by_category" nested inside
    if "overall" in raw_summary:
        overall = raw_summary["overall"]
    else:
        overall = raw_summary

    # Ensure personas key exists
    if "personas" not in overall:
        overall["personas"] = {}

    # Ensure pti key exists
    if "pti" not in overall:
        overall["pti"] = {}

    per_product = data.get("per_product", [])

    # Also expose by_category if present (new format)
    by_category = raw_summary.get("by_category", {})

    return {
        "summary":     overall,
        "per_product": per_product,
        "by_category": by_category,
    }


def _safe_persona_val(summary: dict, persona: str, key: str, default=0.0):
    """Return summary['personas'][persona][key] safely."""
    return summary.get("personas", {}).get(persona, {}).get(key, default)


# ── Chart 1: Satisfaction Score Comparison ────────────────────────────────────

def chart_satisfaction(summary: dict):
    """
    Grouped bar chart: 3 persona groups (Budget/Quality/Balanced),
    3 bars each (PAVS=blue, Price-only=orange, Rating-only=red).
    """
    personas = PERSONA_KEYS
    p_labels = [PERSONA_LABELS[k] for k in personas]

    pavs_scores   = [_safe_persona_val(summary, k, "avg_sat_pavs")         for k in personas]
    price_scores  = [_safe_persona_val(summary, k, "avg_sat_price_only")   for k in personas]
    rating_scores = [_safe_persona_val(summary, k, "avg_sat_rating_only")  for k in personas]

    if not any(pavs_scores):
        print("[visualizer] chart_satisfaction: no persona data, skipping.")
        return

    x     = np.arange(len(personas))
    width = 0.25

    with plt.rc_context(IEEE_RC):
        fig, ax = plt.subplots(figsize=(8, 4.5))

        b1 = ax.bar(x - width, pavs_scores,   width,
                    label="SmartPick (PAVS)",   color=COLORS["pavs"],        zorder=3)
        b2 = ax.bar(x,         price_scores,  width,
                    label="Price-only baseline", color=COLORS["price_only"],  zorder=3)
        b3 = ax.bar(x + width, rating_scores, width,
                    label="Rating-only baseline", color=COLORS["rating_only"], zorder=3)

        ax.set_title("Satisfaction Score: SmartPick vs Baselines (Top-K Products)",
                     pad=14)
        ax.set_ylabel("Satisfaction Score (0–1)")
        ax.set_xlabel("User Persona")
        ax.set_xticks(x)
        ax.set_xticklabels(p_labels)
        ax.set_ylim(0, 1.15)
        ax.legend(loc="upper left", ncol=1)

        # Value labels on bars
        for bars in [b1, b2, b3]:
            for bar in bars:
                h = bar.get_height()
                if h > 0:
                    ax.text(bar.get_x() + bar.get_width() / 2.0, h + 0.012,
                            f"{h:.3f}", ha="center", va="bottom",
                            fontsize=7.5, color="#222222")

        plt.tight_layout()
        out = CHARTS_DIR / "satisfaction_comparison.png"
        plt.savefig(out)
        plt.close()
    print(f"[visualizer] Saved {out}")


# ── Chart 2: Satisfaction Lift % ──────────────────────────────────────────────

def chart_lift(summary: dict):
    """
    Grouped bar chart: lift % vs price-only and rating-only, per persona.
    Positive lifts = green, negative = red.
    Horizontal dashed line at 0.
    """
    personas = PERSONA_KEYS
    p_labels = [PERSONA_LABELS[k] for k in personas]

    lift_price  = [_safe_persona_val(summary, k, "avg_lift_vs_price")  for k in personas]
    lift_rating = [_safe_persona_val(summary, k, "avg_lift_vs_rating") for k in personas]

    if not any(lift_price) and not any(lift_rating):
        print("[visualizer] chart_lift: no lift data, skipping.")
        return

    x     = np.arange(len(personas))
    width = 0.35

    with plt.rc_context(IEEE_RC):
        fig, ax = plt.subplots(figsize=(8, 4.5))

        # Colour each bar individually by sign
        def _bar_colors(values, pos_color, neg_color):
            return [pos_color if v >= 0 else neg_color for v in values]

        bars1 = ax.bar(x - width / 2, lift_price,  width,
                       color=_bar_colors(lift_price,  COLORS["lift_pos"], COLORS["lift_neg"]),
                       label="_nolegend_", zorder=3)
        bars2 = ax.bar(x + width / 2, lift_rating, width,
                       color=_bar_colors(lift_rating, COLORS["lift_pos"], COLORS["lift_neg"]),
                       label="_nolegend_", zorder=3)

        # Manually build legend patches
        pos_patch  = mpatches.Patch(color=COLORS["lift_pos"],   label="Positive lift")
        neg_patch  = mpatches.Patch(color=COLORS["lift_neg"],   label="Negative lift")
        # Hatch to distinguish vs-price / vs-rating within same colour
        bars1[0].set_label("vs Price-only")
        bars2[0].set_label("vs Rating-only")

        ax.axhline(0, color="#444444", linewidth=1.0, linestyle="--", zorder=4)

        ax.set_title("SmartPick Satisfaction Lift over Baselines (%)", pad=14)
        ax.set_ylabel("Lift (%)")
        ax.set_xlabel("User Persona")
        ax.set_xticks(x)
        ax.set_xticklabels(p_labels)

        # Custom legend: hatching to distinguish bars + colour for sign
        h_patch  = mpatches.Patch(facecolor="#888888", edgecolor="white",
                                  hatch="",  label="vs Price-only")
        r_patch  = mpatches.Patch(facecolor="#888888", edgecolor="white",
                                  hatch="//", label="vs Rating-only")
        for bar in bars2:
            bar.set_hatch("//")
            bar.set_edgecolor("white")

        ax.legend(handles=[pos_patch, neg_patch, h_patch, r_patch],
                  loc="upper right", ncol=2)

        # Value labels
        for bars in [bars1, bars2]:
            for bar in bars:
                h = bar.get_height()
                va = "bottom" if h >= 0 else "top"
                offset = 0.4 if h >= 0 else -0.4
                ax.text(bar.get_x() + bar.get_width() / 2.0, h + offset,
                        f"{h:+.1f}%", ha="center", va=va,
                        fontsize=7.5, color="#222222")

        plt.tight_layout()
        out = CHARTS_DIR / "satisfaction_lift.png"
        plt.savefig(out)
        plt.close()
    print(f"[visualizer] Saved {out}")


# ── Chart 3: Spearman Correlation Heatmap ────────────────────────────────────

def chart_spearman(summary: dict):
    """
    3×2 heatmap (personas × baselines).
    Colormap RdYlGn_r: red = high ρ (bad, PAVS ≈ baseline), green = low ρ (good).
    """
    personas  = PERSONA_KEYS
    p_labels  = [PERSONA_LABELS[k] for k in personas]
    baselines = ["vs Price-only", "vs Rating-only"]

    data = np.array([
        [_safe_persona_val(summary, k, "avg_spearman_vs_price"),
         _safe_persona_val(summary, k, "avg_spearman_vs_rating")]
        for k in personas
    ])

    if not data.any():
        print("[visualizer] chart_spearman: no spearman data, skipping.")
        return

    with plt.rc_context(IEEE_RC):
        fig, ax = plt.subplots(figsize=(5.5, 3.8))

        sns.heatmap(
            data,
            annot=True,
            fmt=".3f",
            cmap="RdYlGn_r",
            vmin=-1, vmax=1,
            xticklabels=baselines,
            yticklabels=p_labels,
            linewidths=0.6,
            linecolor="#DDDDDD",
            ax=ax,
            annot_kws={"size": 11, "weight": "bold"},
            cbar_kws={"shrink": 0.85, "label": "Spearman ρ"},
        )

        ax.set_title("Spearman Rank Correlation ρ (PAVS vs Baselines)", pad=12)
        ax.set_ylabel("")
        ax.tick_params(axis="x", rotation=0)
        ax.tick_params(axis="y", rotation=0)

        note = ("ρ ≈ 0: PAVS differs meaningfully from baseline (desirable)     "
                "ρ ≈ 1: PAVS ≈ baseline (no added value)")
        fig.text(0.5, -0.04, note, ha="center", fontsize=7.5,
                 style="italic", color="#555555")

        plt.tight_layout()
        out = CHARTS_DIR / "spearman_heatmap.png"
        plt.savefig(out, bbox_inches="tight")
        plt.close()
    print(f"[visualizer] Saved {out}")


# ── Chart 4: PTI Quality ──────────────────────────────────────────────────────

def chart_pti(summary: dict, per_product: list):
    """
    Left: pie chart — real vs simulated price history %.
    Right: horizontal bar chart — R² per product, coloured by real(blue)/simulated(grey).
    Orange dashed line at R²=0.5, red at R²=0.3.
    """
    pti_summary = summary.get("pti", {})
    if not pti_summary and not per_product:
        print("[visualizer] chart_pti: no PTI data, skipping.")
        return

    real_pct = pti_summary.get("avg_real_history_pct", 0.0)
    sim_pct  = 100.0 - real_pct

    with plt.rc_context(IEEE_RC):
        fig, axes = plt.subplots(1, 2, figsize=(11, max(3.5, 0.55 * len(per_product) + 1.5)))

        # ── Left: pie ─────────────────────────────────────────────────────────
        wedge_props = {"edgecolor": "white", "linewidth": 2.0}
        axes[0].pie(
            [real_pct, sim_pct],
            labels=[f"Real\n({real_pct:.1f}%)", f"Simulated\n({sim_pct:.1f}%)"],
            colors=[COLORS["real"], COLORS["simulated"]],
            startangle=90,
            wedgeprops=wedge_props,
            textprops={"fontsize": 10},
            autopct="%1.1f%%",
            pctdistance=0.65,
        )
        axes[0].set_title("Price History Source\n(across all products)", fontsize=11)

        # ── Right: R² per product ─────────────────────────────────────────────
        if per_product:
            product_labels = []
            r2_values      = []
            bar_colors     = []

            for r in per_product:
                pti = r.get("pti", {})
                label     = r.get("label", "Unknown")
                r2        = pti.get("mean_r2", 0.0)
                real_cnt  = pti.get("real_history_count", 0)
                product_labels.append(label)
                r2_values.append(r2 if r2 is not None else 0.0)
                bar_colors.append(COLORS["real"] if real_cnt > 0 else COLORS["simulated"])

            y = np.arange(len(product_labels))
            axes[1].barh(y, r2_values, color=bar_colors, height=0.6, zorder=3)
            axes[1].set_yticks(y)
            axes[1].set_yticklabels(product_labels, fontsize=8)
            axes[1].set_xlim(0, 1.05)
            axes[1].set_xlabel("R² Score")
            axes[1].axvline(0.5, color="darkorange", linestyle="--",
                            linewidth=1.2, zorder=4, label="R²=0.5 (reliable)")
            axes[1].axvline(0.3, color="red",        linestyle="--",
                            linewidth=1.2, zorder=4, label="R²=0.3 (minimum)")
            axes[1].set_title("PTI Trend Confidence (R²)\nper Product", fontsize=11)
            axes[1].xaxis.grid(True, linestyle="--", alpha=0.5, zorder=0)
            axes[1].set_axisbelow(True)

            real_patch = mpatches.Patch(color=COLORS["real"],      label="Real price history")
            sim_patch  = mpatches.Patch(color=COLORS["simulated"], label="Simulated fallback")
            axes[1].legend(handles=[real_patch, sim_patch,
                                    mpatches.Patch(color="darkorange", label="R²=0.5 (reliable)"),
                                    mpatches.Patch(color="red",        label="R²=0.3 (minimum)")],
                           fontsize=7.5, loc="lower right")

            # Value labels
            for i, v in enumerate(r2_values):
                axes[1].text(v + 0.01, i, f"{v:.3f}",
                             va="center", ha="left", fontsize=7.5)
        else:
            axes[1].text(0.5, 0.5, "No per-product data available",
                         ha="center", va="center", transform=axes[1].transAxes,
                         fontsize=10, color="gray")
            axes[1].set_axis_off()

        plt.suptitle("Price Trend Indicator (PTI) — Data Quality",
                     fontsize=13, fontweight="bold", y=1.02)
        plt.tight_layout()
        out = CHARTS_DIR / "pti_quality.png"
        plt.savefig(out, bbox_inches="tight")
        plt.close()
    print(f"[visualizer] Saved {out}")


# ── Chart 5: Category-wise Satisfaction Comparison ───────────────────────────

def chart_category_comparison(by_category: dict):
    """
    3 subplots (one per persona), x-axis = category,
    grouped bars = PAVS vs price-only vs rating-only.
    Skipped if no by_category data is available.
    """
    if not by_category:
        # Attempt to infer categories from per-product labels if by_category is empty
        print("[visualizer] chart_category_comparison: no by_category data, skipping.")
        return

    personas = PERSONA_KEYS
    p_labels = [PERSONA_LABELS[k] for k in personas]
    categories = sorted(by_category.keys())

    if not categories:
        print("[visualizer] chart_category_comparison: by_category is empty, skipping.")
        return

    x     = np.arange(len(categories))
    width = 0.25

    with plt.rc_context(IEEE_RC):
        fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), sharey=True)

        for col, (persona, p_label) in enumerate(zip(personas, p_labels)):
            ax = axes[col]

            pavs_vals   = []
            price_vals  = []
            rating_vals = []

            for cat in categories:
                cat_data = by_category.get(cat, {})
                # Personas are nested under cat_data["personas"][persona]
                pdata = cat_data.get("personas", {}).get(persona, {})

                pavs_vals.append(pdata.get("avg_sat_pavs",        0.0))
                price_vals.append(pdata.get("avg_sat_price_only",  0.0))
                rating_vals.append(pdata.get("avg_sat_rating_only", 0.0))

            b1 = ax.bar(x - width, pavs_vals,   width,
                        color=COLORS["pavs"],       label="SmartPick (PAVS)", zorder=3)
            b2 = ax.bar(x,         price_vals,  width,
                        color=COLORS["price_only"], label="Price-only",       zorder=3)
            b3 = ax.bar(x + width, rating_vals, width,
                        color=COLORS["rating_only"], label="Rating-only",     zorder=3)

            ax.set_title(p_label, fontsize=11)
            ax.set_xticks(x)
            ax.set_xticklabels([c.title() for c in categories],
                               rotation=20, ha="right", fontsize=8)
            ax.set_ylim(0, 1.15)
            if col == 0:
                ax.set_ylabel("Satisfaction Score (0–1)")
            if col == 1:
                ax.set_xlabel("Category")
            if col == 2:
                ax.legend(loc="upper right", fontsize=7)

            # Value labels
            for bars in [b1, b2, b3]:
                for bar in bars:
                    h = bar.get_height()
                    if h > 0.01:
                        ax.text(bar.get_x() + bar.get_width() / 2.0,
                                h + 0.012, f"{h:.2f}",
                                ha="center", va="bottom", fontsize=6.5)

        fig.suptitle("Category-wise Satisfaction Comparison",
                     fontsize=13, fontweight="bold", y=1.02)
        plt.tight_layout()
        out = CHARTS_DIR / "category_comparison.png"
        plt.savefig(out, bbox_inches="tight")
        plt.close()
    print(f"[visualizer] Saved {out}")


# ── Flask helper (base64 inline chart) ───────────────────────────────────────

def price_trend_base64(price_history: list, trend_label: str = "") -> str:
    """
    Generate a small sparkline of price history and return as base64 PNG.
    Used by Flask product detail route.
    """
    import base64, io
    prices = [p["price"] for p in price_history if "price" in p]
    if not prices:
        return ""

    with plt.rc_context(IEEE_RC):
        fig, ax = plt.subplots(figsize=(5, 2.2))
        ax.plot(prices, color=COLORS["pavs"], linewidth=1.5)
        ax.fill_between(range(len(prices)), prices,
                        alpha=0.15, color=COLORS["pavs"])
        if trend_label:
            ax.set_title(f"Price History — {trend_label}", fontsize=10)
        ax.set_xlabel("Day", fontsize=9)
        ax.set_ylabel("Price (₹)", fontsize=9)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=120)
        plt.close()
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        report = load_report()
    except FileNotFoundError as e:
        print(f"[visualizer] ERROR: {e}")
        return

    summary     = report["summary"]
    per_product = report["per_product"]
    by_category = report.get("by_category", {})

    chart_satisfaction(summary)
    chart_lift(summary)
    chart_spearman(summary)
    chart_pti(summary, per_product)
    chart_category_comparison(by_category)

    print(f"\n[visualizer] All charts saved to {CHARTS_DIR}/")


if __name__ == "__main__":
    main()
