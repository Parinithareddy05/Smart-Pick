"""
Flask web application — user pastes a product URL, scrapes Amazon + Flipkart,
fetches real price history, runs 3-layer ML pipeline, returns ranked results.

Usage:
    conda activate mlproject
    python src/app.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, render_template, request
from config import PERSONAS
import live_pipeline
from scraper import url_parser, aggregator
from scraper.url_parser import extract_full_name

app = Flask(
    __name__,
    template_folder=str(Path(__file__).parent.parent / "templates"),
    static_folder=str(Path(__file__).parent.parent / "static"),
)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
@app.route("/compare", methods=["GET"])
def index():
    return render_template("compare.html")


@app.route("/compare", methods=["POST"])
def compare():
    url     = request.form.get("url", "").strip()
    persona = request.form.get("persona", "balanced").lower()
    if persona not in PERSONAS:
        persona = "balanced"

    # 1. Parse URL → extract search query
    try:
        query, source_site = url_parser.extract_query(url)
    except ValueError as e:
        return render_template("compare.html", error=str(e))

    if not query:
        return render_template("compare.html", error="Could not extract product name from URL.")

    # 2. Get full product name for similarity matching
    original_name = extract_full_name(url)

    # 3. Scrape Amazon + Flipkart in parallel, filter by similarity
    scraped_rows = aggregator.scrape_all_sites(query, original_name=original_name)
    if not scraped_rows:
        return render_template("compare.html",
                               error="Could not retrieve products from any site. Please try again.")

    # 4. Run live ML pipeline: RCS → PTI → PAVS
    df = live_pipeline.run_live_pipeline(scraped_rows, persona=persona, source_url=url)
    if df.empty:
        return render_template("compare.html", error="No valid products found after processing.")

    # 5. Prepare display fields
    score_col = f"value_score_{persona}"
    products = df.to_dict(orient="records")
    for p in products:
        p["display_price"]    = f"₹{p['price']:,.0f}" if p.get("price") else "N/A"
        p["display_rating"]   = f"{p.get('raw_rating', 0):.1f}"
        p["display_reviews"]  = f"{int(p.get('review_count', 0)):,}"
        p["display_score"]    = f"{float(p.get(score_col, 0)) * 100:.1f}"
        p["trend_class"]      = _trend_css_class(p.get("trend_label", ""))
        p["confidence_class"] = _confidence_css_class(p.get("confidence_label", ""))
        p["site_label"]       = p.get("site", "").capitalize()

    return render_template(
        "compare_results.html",
        products=products,
        query=query,
        original_url=url,
        source_site=source_site,
        persona=persona,
        persona_label=PERSONAS[persona]["label"],
        total=len(products),
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _trend_css_class(trend_label: str) -> str:
    if "Dropping" in trend_label:
        return "trend-dropping"
    elif "Rising" in trend_label:
        return "trend-rising"
    return "trend-stable"


def _confidence_css_class(label: str) -> str:
    if "High" in label:
        return "conf-high"
    elif "Medium" in label:
        return "conf-medium"
    return "conf-low"


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os, argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=int(os.environ.get("FLASK_PORT", 5000)))
    args = parser.parse_args()
    app.run(debug=False, host="0.0.0.0", port=args.port)
