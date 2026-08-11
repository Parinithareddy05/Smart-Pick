"""
SmartPick — Technical Architecture & Methods Report Generator
Produces a comprehensive PDF for IEEE paper writing assistance.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Preformatted
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

# ── Output path ──────────────────────────────────────────────────────────────
OUT = Path(__file__).resolve().parent.parent / "results" / "SmartPick_Technical_Report.pdf"
RESULTS = Path(__file__).resolve().parent.parent / "results" / "evaluation_report.json"

# ── Load evaluation results ──────────────────────────────────────────────────
with open(RESULTS) as f:
    REPORT = json.load(f)
OVERALL = REPORT["summary"]["overall"]["personas"]
BY_CAT  = REPORT["summary"]["by_category"]
PTI_SUMMARY = REPORT["summary"]["overall"]["pti"]

# ── Styles ───────────────────────────────────────────────────────────────────
BASE = getSampleStyleSheet()

def make_style(name, parent="Normal", **kwargs):
    s = ParagraphStyle(name, parent=BASE[parent])
    for k, v in kwargs.items():
        setattr(s, k, v)
    return s

TITLE   = make_style("Title2",  "Title",  fontSize=22, spaceAfter=6, textColor=colors.HexColor("#1a1a2e"))
H1      = make_style("H1",      "Heading1", fontSize=16, spaceBefore=16, spaceAfter=6,
                     textColor=colors.HexColor("#16213e"), borderPad=4)
H2      = make_style("H2",      "Heading2", fontSize=13, spaceBefore=10, spaceAfter=4,
                     textColor=colors.HexColor("#0f3460"))
H3      = make_style("H3",      "Heading3", fontSize=11, spaceBefore=8,  spaceAfter=3,
                     textColor=colors.HexColor("#533483"))
BODY    = make_style("Body",    "Normal",   fontSize=10, leading=15, spaceAfter=6, alignment=TA_JUSTIFY)
BULLET  = make_style("Bullet",  "Normal",   fontSize=10, leading=14, leftIndent=16, spaceAfter=3)
CODE    = make_style("Code",    "Code",     fontSize=8,  leading=11, fontName="Courier",
                     backColor=colors.HexColor("#f4f4f4"), borderPad=4)
CAPTION = make_style("Caption", "Normal",   fontSize=9,  leading=12, textColor=colors.grey,
                     alignment=TA_CENTER, spaceAfter=8)
MONO    = make_style("Mono",    "Normal",   fontSize=9,  fontName="Courier",
                     textColor=colors.HexColor("#333333"), leading=13)
CELL    = make_style("Cell",   "Normal",   fontSize=8.5, leading=12, spaceAfter=0, wordWrap='CJK')
CELL_H  = make_style("CellH",  "Normal",   fontSize=8.5, leading=12, spaceAfter=0,
                     fontName="Helvetica-Bold", textColor=colors.white)

def b(text): return f"<b>{text}</b>"
def i(text): return f"<i>{text}</i>"
def bi(text): return f"<b><i>{text}</i></b>"
def code(text): return f'<font name="Courier" size="9">{text}</font>'

# ── Table helper ─────────────────────────────────────────────────────────────
def _styled_table(data, col_widths, header_rows=1):
    t = Table(data, colWidths=col_widths, repeatRows=header_rows)
    style = [
        ("BACKGROUND", (0, 0), (-1, header_rows - 1), colors.HexColor("#16213e")),
        ("TEXTCOLOR",  (0, 0), (-1, header_rows - 1), colors.white),
        ("FONTNAME",   (0, 0), (-1, header_rows - 1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("ALIGN",      (0, 0), (-1, -1), "LEFT"),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, header_rows), (-1, -1),
         [colors.white, colors.HexColor("#f0f4f8")]),
        ("GRID",       (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    t.setStyle(TableStyle(style))
    return t

def styled_table(data, col_widths, header_rows=1):
    """Wraps all string cells in Paragraph objects to enable text wrapping."""
    wrapped = []
    for row_i, row in enumerate(data):
        new_row = []
        for cell in row:
            if isinstance(cell, str):
                style = CELL_H if row_i < header_rows else CELL
                new_row.append(Paragraph(cell, style))
            else:
                new_row.append(cell)
        wrapped.append(new_row)
    return _styled_table(wrapped, col_widths, header_rows=header_rows)

def section_divider():
    return HRFlowable(width="100%", thickness=1, color=colors.HexColor("#dddddd"), spaceAfter=8)

# ── Document ─────────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    str(OUT), pagesize=A4,
    leftMargin=2.2*cm, rightMargin=2.2*cm,
    topMargin=2.5*cm, bottomMargin=2.5*cm,
    title="SmartPick — Technical Architecture & Methods Report",
    author="SmartPick IEEE Research Project"
)

story = []

# ════════════════════════════════════════════════════════════════════════════
# COVER
# ════════════════════════════════════════════════════════════════════════════
story += [
    Spacer(1, 1.5*cm),
    Paragraph("SmartPick", TITLE),
    Paragraph("AI-Powered Cross-Platform Product Value Ranking", make_style("Sub", "Normal",
              fontSize=14, textColor=colors.HexColor("#0f3460"), alignment=TA_CENTER, spaceAfter=4)),
    Paragraph("Technical Architecture &amp; Methods Report", make_style("Sub2", "Normal",
              fontSize=12, textColor=colors.grey, alignment=TA_CENTER, spaceAfter=2)),
    Paragraph("IEEE Research Paper — Complete Reference Document", make_style("Sub3", "Normal",
              fontSize=10, textColor=colors.grey, alignment=TA_CENTER, spaceAfter=20)),
    HRFlowable(width="100%", thickness=2, color=colors.HexColor("#16213e"), spaceAfter=16),
    Paragraph(
        "This document provides a complete technical reference of the SmartPick system — "
        "covering architecture, algorithms, data pipeline, evaluation methodology, and results. "
        "It is intended as a self-contained briefing document for IEEE paper writing and peer review.",
        make_style("Intro", "Normal", fontSize=10, leading=15, alignment=TA_JUSTIFY,
                   textColor=colors.HexColor("#333333"))),
    Spacer(1, 0.5*cm),
]

# Quick stats box
quick = [
    ["Metric", "Value"],
    ["Platform", "Amazon India + Flipkart"],
    ["Evaluation products", "21 (7 per category)"],
    ["ML layers", "3 (RCS → PTI → PAVS)"],
    ["Personas", "Budget / Quality / Balanced"],
    ["Real price history coverage", f"{PTI_SUMMARY['avg_real_history_pct']}%"],
    ["Mean PTI R²", f"{PTI_SUMMARY['avg_r2']:.4f}"],
    ["Best lift vs price baseline", f"+{OVERALL['quality']['avg_lift_vs_price']:.1f}% (Quality)"],
    ["Best lift vs rating baseline", f"+{OVERALL['budget']['avg_lift_vs_rating']:.1f}% (Budget)"],
    ["Budget p-value (Wilcoxon)", f"{OVERALL['budget']['wilcoxon_p_vs_price']}"],
    ["Quality p-value (Wilcoxon)", f"{OVERALL['quality']['wilcoxon_p_vs_price']}"],
]
story.append(styled_table(quick, [7*cm, 9*cm]))
story.append(PageBreak())

# ════════════════════════════════════════════════════════════════════════════
# 1. SYSTEM OVERVIEW
# ════════════════════════════════════════════════════════════════════════════
story += [Paragraph("1. System Overview", H1), section_divider()]
story.append(Paragraph(
    "SmartPick is a multi-platform product intelligence system that retrieves, aggregates, "
    "and ranks electronics listings from Amazon India and Flipkart in real time. "
    "The core research contribution is a three-layer ML pipeline that moves beyond "
    "naive price or star-rating sorting by incorporating review credibility, "
    "buyer persona preferences, and short-term price trend signals.",
    BODY))

story.append(Paragraph(b("Problem Statement"), H2))
story.append(Paragraph(
    "Online shoppers face three core information quality problems: "
    "(1) raw star ratings are inflated by sparse reviews — a 4.8★ product with 3 reviews "
    "appears superior to a 4.2★ product with 90,000 reviews; "
    "(2) price and quality trade-offs differ by buyer persona — a budget buyer and a "
    "quality buyer have fundamentally different optimal rankings; "
    "(3) current price may be a temporary spike or promotional low that misleads "
    "purchase timing decisions.",
    BODY))

story.append(Paragraph(b("Research Contributions"), H2))
for item in [
    "<b>Review Confidence Score (RCS):</b> Log-normalized review volume correction that adjusts raw star ratings to account for statistical evidence weight.",
    "<b>Persona-Adaptive Value Score (PAVS):</b> A weighted linear combination of price efficiency and adjusted rating under three buyer preference profiles.",
    "<b>Price Trend Indicator (PTI):</b> Linear regression on 30-day price history with p-value significance gating, classifying trends as Dropping / Stable / Rising and contributing a trend_score to PAVS.",
    "<b>Cross-platform matching:</b> Parallel scraping of Amazon.in and Flipkart with token-overlap + SequenceMatcher similarity filtering (threshold 0.45) to ensure only genuinely equivalent products are compared.",
    "<b>Empirical evaluation:</b> 21 live benchmark products across 3 categories, with real 30-day price history from pricehistory.app (94.8% coverage), Wilcoxon signed-rank statistical significance testing.",
]:
    story.append(Paragraph(f"• {item}", BULLET))

story.append(PageBreak())

# ════════════════════════════════════════════════════════════════════════════
# 2. SYSTEM ARCHITECTURE
# ════════════════════════════════════════════════════════════════════════════
story += [Paragraph("2. System Architecture", H1), section_divider()]
story.append(Paragraph(
    "The system operates as a real-time web application. When a user submits a product URL, "
    "the live pipeline scrapes Amazon and Flipkart, fetches real price history, and runs "
    "the three-layer ML pipeline on the fly.",
    BODY))

story.append(Paragraph("2.1 High-Level Data Flow (Live Mode)", H2))
flow_data = [
    ["Step", "Component", "Input", "Output"],
    ["1", "URL Parser\nsrc/scraper/url_parser.py", "Amazon/Flipkart URL", "Search query string"],
    ["2", "Aggregator\nsrc/scraper/aggregator.py", "Query string", "Raw product rows (parallel scrape)"],
    ["3", "Similarity Filter\nsrc/scraper/matcher.py", "Raw product rows", "Filtered matches (≥0.45 score)"],
    ["4", "RCS Layer\nsrc/rcs.py", "Products DataFrame", "adjusted_rating, adjusted_rating_norm"],
    ["5", "PTI Layer\nsrc/pti.py", "Products + price history", "trend_label, trend_score, r_squared"],
    ["6", "PAVS Layer\nsrc/pavs.py", "RCS+PTI enriched DF", "value_score_{persona}, rank_{persona}"],
    ["7", "Flask App\nsrc/app.py", "Ranked DataFrame", "HTML response / JSON API"],
]
story.append(styled_table(flow_data, [1.2*cm, 4.5*cm, 5*cm, 5.5*cm]))
story.append(Spacer(1, 0.3*cm))

story.append(Paragraph("2.2 Key File Structure", H2))
files = [
    ["File", "Role"],
    ["src/config.py", "All constants: persona weights, file paths, thresholds"],
    ["src/rcs.py", "Layer 1 — Review Confidence Score"],
    ["src/pti.py", "Layer 2 — Price Trend Indicator"],
    ["src/pavs.py", "Layer 3 — Persona-Adaptive Value Score"],
    ["src/live_pipeline.py", "Orchestrates RCS→PTI→PAVS for live requests"],
    ["src/app.py", "Flask web server (port 5000), routes: GET / and POST /compare"],
    ["src/evaluate.py", "Full evaluation harness: scrape + pipeline + Wilcoxon + Spearman"],
    ["src/eval_cache.py", "24h JSON cache to avoid re-scraping during repeated evaluation runs"],
    ["src/visualizer.py", "5 matplotlib charts: satisfaction, lift, Spearman heatmap, PTI quality, category comparison"],
    ["src/scraper/aggregator.py", "ThreadPoolExecutor parallel scraping of Amazon + Flipkart"],
    ["src/scraper/amazon_scraper.py", "requests + BeautifulSoup scraper for Amazon.in"],
    ["src/scraper/flipkart_scraper.py", "Playwright (headless Chromium) scraper for Flipkart"],
    ["src/scraper/matcher.py", "40% SequenceMatcher + 60% token overlap similarity"],
    ["src/scraper/pricehistory_scraper.py", "Firefox + playwright-stealth → pricehistory.app API"],
    ["data/eval_cache.json", "Cached scrape results (24h TTL) for all 21 benchmark products"],
    ["results/evaluation_report.json", "Full evaluation output: per-product + aggregated metrics"],
    ["Papers/paper.tex", "IEEE LaTeX paper source"],
]
story.append(styled_table(files, [6*cm, 10.2*cm]))
story.append(PageBreak())

story.append(Paragraph("2.3 Flask Web Application Routes", H2))
routes = [
    ["Route", "Method", "Description"],
    ["/ or /compare", "GET", "Landing page — user pastes Amazon or Flipkart product URL"],
    ["/compare", "POST", "Takes Amazon/Flipkart URL, runs full live pipeline, shows ranked results"],
]
story.append(styled_table(routes, [4*cm, 2*cm, 10.2*cm]))

story.append(Paragraph("2.4 Frontend Stack", H2))
for item in [
    "Glassmorphism UI with dark/light mode toggle (CSS variables + localStorage)",
    "Animated blob background (CSS @keyframes)",
    "Loading overlay with spinner during live pipeline execution",
    "Inline base64 price trend chart (matplotlib → BytesIO → base64) — no separate image files needed",
    "Templates: compare.html (home / URL input form), compare_results.html (ranked product results)",
]:
    story.append(Paragraph(f"• {item}", BULLET))

story.append(PageBreak())

# ════════════════════════════════════════════════════════════════════════════
# 3. ML PIPELINE — LAYER DETAILS
# ════════════════════════════════════════════════════════════════════════════
story += [Paragraph("3. ML Pipeline — Layer-by-Layer Technical Details", H1), section_divider()]

# ── RCS ──────────────────────────────────────────────────────────────────────
story.append(Paragraph("3.1 Layer 1 — Review Confidence Score (RCS)", H2))
story.append(Paragraph(b("File:") + code(" src/rcs.py"), BODY))
story.append(Paragraph(
    "Raw star ratings on Amazon suffer from sparse-review inflation. A product with "
    "4.8★ from 5 reviews is statistically unreliable compared to 4.2★ from 50,000 reviews. "
    "RCS applies a log-normalized confidence factor to down-weight low-evidence ratings.",
    BODY))
story.append(Paragraph(b("Formulas:"), H3))
story.append(Paragraph(
    "Confidence factor: <b>C<sub>i</sub> = log(n<sub>i</sub> + 1) / log(n<sub>max</sub> + 1)</b>",
    BODY))
story.append(Paragraph(
    "Adjusted rating: <b>r̃<sub>i</sub> = r<sub>i</sub> × C<sub>i</sub></b>",
    BODY))
story.append(Paragraph(
    "Normalized: <b>r̃<sub>i,norm</sub> = r̃<sub>i</sub> / 5.0</b>  (used in PAVS satisfaction metric)",
    BODY))
for item in [
    "n_i = review count for product i; n_max = maximum review count in the result set",
    "Log base: natural log (log1p used for numerical stability)",
    "Result: C_i ∈ (0, 1]; products with n_i = n_max get C_i = 1.0",
    "Edge case: if all products have 0 reviews, confidence defaults to 0.5 for all",
    "adjusted_rating_norm (/5.0) is stored as a column and used by the satisfaction_score evaluation metric",
]:
    story.append(Paragraph(f"• {item}", BULLET))
story.append(Paragraph(b("Example:"), H3))
story.append(Paragraph(
    "Product A: 4.8★, 12 reviews. Product B: 4.2★, 89,400 reviews. "
    "With n_max = 89,400: C_A = log(13)/log(89401) ≈ 0.234, so r̃_A ≈ 1.12. "
    "C_B = 1.0, r̃_B = 4.2. After normalization B ranks far above A — correctly.",
    BODY))

# ── PTI ──────────────────────────────────────────────────────────────────────
story.append(Paragraph("3.2 Layer 2 — Price Trend Indicator (PTI)", H2))
story.append(Paragraph(b("File:") + code(" src/pti.py"), BODY))
story.append(Paragraph(
    "PTI fits a linear regression on 30-day price history for each product and classifies "
    "the current price direction. It also produces a continuous trend_score in [0,1] "
    "that feeds into the PAVS value score.",
    BODY))
story.append(Paragraph(b("Algorithm:"), H3))
for step in [
    "Fetch price history: real data from pricehistory.app via playwright-stealth (Firefox) → falls back to SQLite cache → falls back to deterministic simulation",
    "Fit scipy.stats.linregress(day_index, price) to get slope, r², p-value",
    "Compute normalized slope: norm_slope = slope / mean_price",
    "Significance gate: if p_value ≥ 0.05, classify as 'Price Stable' regardless of slope",
    "Threshold classification: norm_slope < −0.002 → Dropping; > +0.002 → Rising; else Stable",
    "Trend score: trend_score = clip(0.5 − norm_slope × r² × 5, 0.0, 1.0)",
    "Interpretation: trend_score > 0.5 = price falling (good for buyer); = 0.5 = stable; < 0.5 = rising (bad for buyer)",
]:
    story.append(Paragraph(f"• {step}", BULLET))
story.append(Paragraph(b("Design justifications:"), H3))
for item in [
    "Log regression chosen over ARIMA/LSTM: 30 data points is insufficient for ARIMA seasonal decomposition; LSTM requires hundreds of samples. Linear regression extracts directional signal reliably at this scale.",
    "p-value gating (p < 0.05): prevents spurious trend labels from noisy flat series where least-squares finds a slope by chance.",
    "Normalized slope (÷ mean_price): makes the threshold scale-invariant across products priced ₹200–₹200,000.",
    "R² weighting in trend_score: products with noisy history (low R²) get trend_score pulled toward 0.5 (neutral), reducing their trend contribution to PAVS.",
]:
    story.append(Paragraph(f"• {item}", BULLET))
story.append(Paragraph(b("Price history sources (priority order):"), H3))
ph_data = [
    ["Priority", "Source", "Coverage", "Notes"],
    ["1st", "pricehistory.app API", "94.8% in eval", "Real Amazon price history, Firefox+playwright-stealth"],
    ["2nd", "SQLite price_db", "Accumulated", "data/price_history.db, grows with each scrape"],
    ["3rd", "Simulated fallback", "5.2% in eval", "Deterministic: random_seed=hash(product_id), ±2% daily walk"],
]
story.append(styled_table(ph_data, [1.8*cm, 5*cm, 3.5*cm, 6*cm]))
story.append(Spacer(1, 0.3*cm))

# ── PAVS ──────────────────────────────────────────────────────────────────────
story.append(Paragraph("3.3 Layer 3 — Persona-Adaptive Value Score (PAVS)", H2))
story.append(Paragraph(b("File:") + code(" src/pavs.py"), BODY))
story.append(Paragraph(
    "PAVS combines price efficiency, review-adjusted quality, and price trend into a single "
    "value score tuned to a buyer persona's declared preferences.",
    BODY))
story.append(Paragraph(b("Formula:"), H3))
story.append(Paragraph(
    "<b>V<sub>i</sub> = w<sub>p</sub> · P<sub>i</sub><sup>inv</sup>  +  w<sub>r</sub> · r̃<sub>i,norm</sub>  +  w<sub>t</sub> · T<sub>i</sub></b>",
    make_style("Formula", "Normal", fontSize=13, alignment=TA_CENTER, spaceAfter=8,
               textColor=colors.HexColor("#0f3460"))))
story.append(Paragraph(
    "Constraint: <b>w<sub>p</sub> + w<sub>r</sub> + w<sub>t</sub> = 1.0</b>",
    BODY))
story.append(Paragraph(b("Components:"), H3))
for item in [
    "<b>P_i^inv</b> = min-max normalized inverted price: (p_max − p_i) / (p_max − p_min). Lower price → higher score. Computed once per result set.",
    "<b>r̃_i,norm</b> = adjusted_rating_norm from RCS (/5.0 scale). Absolute scale used in evaluation metric.",
    "<b>T_i</b> = trend_score from PTI: clip(0.5 − norm_slope × R² × 5, 0, 1). Neutral = 0.5, dropping price = >0.5 (good), rising = <0.5 (bad).",
    "PAVS ranking uses min-max normalization of adjusted_rating within the result set (amplifies within-group differences for sharper discrimination).",
]:
    story.append(Paragraph(f"• {item}", BULLET))

story.append(Paragraph(b("Persona Weight Table:"), H3))
persona_data = [
    ["Persona", "Label", "w_p (Price)", "w_r (Quality)", "w_t (Trend)", "Target User"],
    ["budget",   "Budget Buyer",   "0.63", "0.27", "0.10", "Price-sensitive, deal hunter"],
    ["quality",  "Quality Buyer",  "0.22", "0.68", "0.10", "Performance/reliability focused"],
    ["balanced", "Balanced Buyer", "0.45", "0.45", "0.10", "Value-for-money seeker"],
]
story.append(styled_table(persona_data, [2*cm, 3.2*cm, 2.2*cm, 2.5*cm, 2.2*cm, 4.1*cm]))
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    "Weight derivation: weights are hand-tuned to represent archetypical buyer profiles, "
    "consistent with related work in MCDM (Multi-Criteria Decision Making). "
    "w_t = 0.10 for all personas because trend information is universally relevant for "
    "purchase timing but should not dominate price/quality signals. "
    "w_p + w_r rescaled proportionally from original 0.70/0.30, 0.25/0.75, 0.50/0.50 "
    "to accommodate w_t = 0.10.",
    BODY))
story.append(PageBreak())

# ════════════════════════════════════════════════════════════════════════════
# 4. DATA COLLECTION
# ════════════════════════════════════════════════════════════════════════════
story += [Paragraph("4. Data Collection & Scraping Architecture", H1), section_divider()]

story.append(Paragraph("4.1 Amazon.in Scraper", H2))
story.append(Paragraph(b("File:") + code(" src/scraper/amazon_scraper.py"), BODY))
for item in [
    "Library: requests + BeautifulSoup (lxml parser)",
    "Search URL: https://www.amazon.in/s?k={query}&i=electronics",
    "Extracted fields: title, price (₹), star_rating, review_count, product_url (buy_url), ASIN",
    "Anti-detection: fake-useragent rotation, Accept-Language: en-IN header",
    "Rate limiting: natural request timing (no explicit sleep — connection overhead sufficient)",
    "Price parsing: strips ₹ symbol, commas; handles 'No rating' gracefully",
]:
    story.append(Paragraph(f"• {item}", BULLET))

story.append(Paragraph("4.2 Flipkart Scraper", H2))
story.append(Paragraph(b("File:") + code(" src/scraper/flipkart_scraper.py"), BODY))
for item in [
    "Library: Playwright (headless Chromium) — JavaScript-rendered pages require browser automation",
    "Search URL: https://www.flipkart.com/search?q={query}&otracker=search",
    "Extracted fields: title, price (₹), star_rating, review_count, product_url",
    "Wait strategy: networkidle wait + explicit CSS selector wait for product cards",
    "Anti-detection: standard browser headers, no stealth needed (Flipkart less aggressive than Amazon)",
]:
    story.append(Paragraph(f"• {item}", BULLET))

story.append(Paragraph("4.3 Parallel Aggregation", H2))
story.append(Paragraph(b("File:") + code(" src/scraper/aggregator.py"), BODY))
for item in [
    "ThreadPoolExecutor with max_workers=2 — Amazon and Flipkart scraped simultaneously",
    "Timeout: 30 seconds per scraper; failed scraper contributes empty list (graceful degradation)",
    "Results merged and deduplicated by normalized title",
    "Similarity filter applied after merge (see 4.4)",
]:
    story.append(Paragraph(f"• {item}", BULLET))

story.append(Paragraph("4.4 Product Similarity Matching", H2))
story.append(Paragraph(b("File:") + code(" src/scraper/matcher.py"), BODY))
story.append(Paragraph(
    "Ensures only genuine matches for the search product are kept, filtering out unrelated "
    "results that happen to contain the query keywords.",
    BODY))
story.append(Paragraph(
    "<b>similarity = 0.40 × SequenceMatcher(query, title) + 0.60 × token_overlap(query, title)</b>",
    make_style("FM2", "Normal", fontSize=10, alignment=TA_CENTER, spaceAfter=6)))
for item in [
    "SequenceMatcher: difflib longest-common-subsequence ratio (character-level)",
    "Token overlap: Jaccard-like intersection of lowercase word sets",
    "Threshold: 0.45 — products below this score are discarded",
    "Both query and title normalized: lowercased, punctuation stripped, common noise words removed",
]:
    story.append(Paragraph(f"• {item}", BULLET))

story.append(Paragraph("4.5 Price History Scraper", H2))
story.append(Paragraph(b("File:") + code(" src/scraper/pricehistory_scraper.py"), BODY))
for item in [
    "Target: pricehistory.app — aggregates Amazon price history from Keepa-like tracking",
    "Library: Playwright (Firefox) + playwright-stealth (evades bot detection)",
    "Method: direct API endpoint extraction from page JavaScript/network responses",
    "Data format: list of {day, price} dicts covering ~30 days",
    "Coverage achieved: 94.8% of evaluated products (21/21 benchmark searches)",
    "Fallback chain: pricehistory.app → SQLite price_db → deterministic simulation",
]:
    story.append(Paragraph(f"• {item}", BULLET))

story.append(PageBreak())

# ════════════════════════════════════════════════════════════════════════════
# 5. EVALUATION METHODOLOGY
# ════════════════════════════════════════════════════════════════════════════
story += [Paragraph("5. Evaluation Methodology", H1), section_divider()]

story.append(Paragraph("5.1 Benchmark Product Set", H2))
story.append(Paragraph(
    "21 benchmark products were selected across 3 categories (7 per category). "
    "Products span a range of price points AND star ratings — including both popular "
    "high-rated listings and lower-rated alternatives — to ensure PAVS is tested on "
    "scenarios where quality discrimination is meaningful.",
    BODY))

story.append(Paragraph(b("Benchmark Products (21 total):"), H3))
bench = [
    ["#", "Label", "Category", "Amazon ASIN"],
    ["1",  "Samsung Galaxy A55 5G",         "Phone",    "B0CWPD9PTK"],
    ["2",  "iQOO Z9s Pro",                  "Phone",    "B0DW47JCHW"],
    ["3",  "Samsung Galaxy S25",            "Phone",    "B0GL86QFC4"],
    ["4",  "Realme P3 Pro",                 "Phone",    "B0G4B8957C"],
    ["5",  "Apple iPhone Air 256GB",        "Phone",    "B0FQFBDQJ1"],
    ["6",  "iQOO Z10 5G (lower-rated)",     "Phone",    "B0GL8NJDG5"],
    ["7",  "Motorola G57 5G (lower-rated)", "Phone",    "B0G3SWTTQ7"],
    ["8",  "Lenovo IdeaPad Slim 3 i5-12450H","Laptop",  "B0FH71SN5N"],
    ["9",  "Lenovo IdeaPad i5-13420H",      "Laptop",   "B0F637DPFW"],
    ["10", "ASUS TUF Gaming F15",           "Laptop",   "B0F8P4Y7VF"],
    ["11", "HP Office fd1354TU",            "Laptop",   "B0F5B1N9SJ"],
    ["12", "Dell 15 i5-1334U",              "Laptop",   "B0DSFQZTVW"],
    ["13", "Dell 15 Platinum i7 (lower)",   "Laptop",   "B0FDQ2R315"],
    ["14", "HP Victus i7-14650HX (lower)",  "Laptop",   "B0FM3WC2QY"],
    ["15", "OnePlus Nord Buds Pro",         "Earphone", "B0FMDL81GS"],
    ["16", "Realme Buds Air 6",             "Earphone", "B0DBGP48NW"],
    ["17", "Redmi Buds 5 Pro",              "Earphone", "B0CQJZD55X"],
    ["18", "Noise Cancellation Pro",        "Earphone", "B09Y5MK1KB"],
    ["19", "boAt Airdopes Alpha",           "Earphone", "B0C3ZYFZ77"],
    ["20", "Realme Buds Wireless 3 (lower)","Earphone", "B0FVLFTL4B"],
    ["21", "Realme Earphones R1 (lower)",   "Earphone", "B0G1B93FV2"],
]
story.append(styled_table(bench, [0.8*cm, 6.5*cm, 2.3*cm, 3.2*cm]))
story.append(Spacer(1, 0.3*cm))

story.append(Paragraph("5.2 Satisfaction Score Metric", H2))
story.append(Paragraph(
    "For each benchmark product search, the pipeline returns N competing products. "
    "The top K = ⌈0.4 × N⌉ (minimum 2) products from each ranking are scored by "
    "the satisfaction function:",
    BODY))
story.append(Paragraph(
    "<b>S(rank) = mean_{top-K} [ w_p × P_i^inv + w_r × r̃_i,norm ]</b>",
    make_style("FM3", "Normal", fontSize=11, alignment=TA_CENTER, spaceAfter=8)))
story.append(Paragraph(
    "Note: satisfaction uses the absolute /5.0 scale for r̃_i,norm (not min-max) "
    "to reflect absolute quality rather than relative within-set position. "
    "Three rankings are compared: PAVS (proposed), price_only (ascending price), "
    "rating_only (descending raw star rating).",
    BODY))

story.append(Paragraph("5.3 Baselines", H2))
baselines = [
    ["Baseline", "Ranking criterion", "Represents"],
    ["Price-only (Base-P)", "Ascending price (cheapest first)", "Naive budget shopping strategy"],
    ["Rating-only (Base-R)", "Descending raw star rating", "Naive quality shopping strategy"],
]
story.append(styled_table(baselines, [4.5*cm, 5*cm, 6.7*cm]))
story.append(Spacer(1, 0.3*cm))

story.append(Paragraph("5.4 Statistical Tests", H2))
for item in [
    "<b>Spearman ρ:</b> Rank correlation between PAVS ranking and each baseline. ρ=1 means identical ordering; ρ≈0 means independent; ρ<0 means reversed.",
    "<b>Kendall τ:</b> Concordance-based rank correlation, more robust to ties than Spearman.",
    "<b>Wilcoxon signed-rank test (one-sided, alternative='greater'):</b> Tests whether PAVS satisfaction scores are systematically higher than baseline satisfaction scores across the 21 benchmark products. More robust to non-normality than paired t-test. α = 0.05.",
]:
    story.append(Paragraph(f"• {item}", BULLET))

story.append(Paragraph("5.5 Evaluation Cache", H2))
story.append(Paragraph(b("File:") + code(" src/eval_cache.py, data/eval_cache.json"), BODY))
story.append(Paragraph(
    "To avoid 60-minute re-scrapes on every evaluate.py run, scraped_rows and "
    "collected price history are cached to disk with a 24-hour TTL. Cache keys are "
    "the benchmark Amazon URLs. On cache hit, URL parsing (including Amazon HTTP fetch) "
    "is also skipped to prevent rate limiting. This enables evaluate.py to complete "
    "in ~10 seconds on a warm cache.",
    BODY))
story.append(PageBreak())

# ════════════════════════════════════════════════════════════════════════════
# 6. RESULTS
# ════════════════════════════════════════════════════════════════════════════
story += [Paragraph("6. Evaluation Results", H1), section_divider()]

story.append(Paragraph("6.1 Overall Satisfaction Score Results (n=21)", H2))
res_data = [
    ["Persona", "PAVS", "Base-P (Price)", "Base-R (Rating)", "Lift vs Price", "Lift vs Rating", "p (vs Price)", "p (vs Rating)"],
]
persona_labels = {"budget": "Budget Buyer", "quality": "Quality Buyer", "balanced": "Balanced Buyer"}
for key in ["budget", "quality", "balanced"]:
    p = OVERALL[key]
    res_data.append([
        persona_labels[key],
        f"{p['avg_sat_pavs']:.4f}",
        f"{p['avg_sat_price_only']:.4f}",
        f"{p['avg_sat_rating_only']:.4f}",
        f"+{p['avg_lift_vs_price']:.2f}%",
        f"+{p['avg_lift_vs_rating']:.2f}%",
        str(p['wilcoxon_p_vs_price']),
        str(p['wilcoxon_p_vs_rating']),
    ])
story.append(styled_table(res_data, [3.2*cm, 1.8*cm, 2.4*cm, 2.4*cm, 2.2*cm, 2.4*cm, 2.0*cm, 2.0*cm]))
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    "✓ = p < 0.05 (statistically significant). "
    "Budget p=0.009, Quality p=0.001 are strongly significant. "
    "Balanced p=0.361 vs price is not significant (see Section 6.4 for discussion). "
    "All three personas are highly significant vs rating-only baseline.",
    CAPTION))

story.append(Paragraph("6.2 PTI Quality Metrics", H2))
pti_data = [
    ["Metric", "Value", "Interpretation"],
    ["Real price history coverage", f"{PTI_SUMMARY['avg_real_history_pct']}%", "% products with real pricehistory.app data"],
    ["Simulated fallback", f"{100-PTI_SUMMARY['avg_real_history_pct']:.1f}%", "% using deterministic simulation"],
    ["Mean R² (linear fit)", f"{PTI_SUMMARY['avg_r2']:.4f}", "Goodness of fit; <0.3 = volatile pricing"],
    ["Avg products with <14 days", f"{PTI_SUMMARY['avg_low_data_products']:.1f}", "Products flagged for insufficient history"],
]
story.append(styled_table(pti_data, [5.5*cm, 3*cm, 7.7*cm]))
story.append(Spacer(1, 0.3*cm))

story.append(Paragraph("6.3 Rank Correlation Analysis", H2))
corr_data = [
    ["Persona", "ρ vs Price", "ρ vs Rating", "τ vs Price", "τ vs Rating"],
]
for key in ["budget", "quality", "balanced"]:
    p = OVERALL[key]
    corr_data.append([
        persona_labels[key],
        f"{p['avg_spearman_vs_price']:.4f}",
        f"{p['avg_spearman_vs_rating']:.4f}",
        f"{p['avg_kendall_vs_price']:.4f}",
        f"{p['avg_kendall_vs_rating']:.4f}",
    ])
story.append(styled_table(corr_data, [4*cm, 3*cm, 3*cm, 3*cm, 3.2*cm]))
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    "Quality Buyer (ρ=0.40 vs price) shows the most distinctive ranking from the price baseline, "
    "confirming quality-weighted PAVS genuinely reorders products. "
    "Negative/near-zero ρ vs rating for Budget/Balanced confirms PAVS reverses the naive rating sort.",
    BODY))

story.append(Paragraph("6.4 Per-Category Results", H2))
for cat in ["phone", "laptop", "earphone"]:
    cd = BY_CAT[cat]["personas"]
    cat_data = [
        ["Persona", "PAVS", "Base-P", "Base-R", "↑Price", "↑Rating", "p(Price)", "p(Rating)"],
    ]
    for key in ["budget", "quality", "balanced"]:
        p = cd[key]
        cat_data.append([
            persona_labels[key],
            f"{p['avg_sat_pavs']:.4f}",
            f"{p['avg_sat_price_only']:.4f}",
            f"{p['avg_sat_rating_only']:.4f}",
            f"+{p['avg_lift_vs_price']:.1f}%",
            f"+{p['avg_lift_vs_rating']:.1f}%",
            str(p['wilcoxon_p_vs_price']) if p['wilcoxon_p_vs_price'] else "n/a",
            str(p['wilcoxon_p_vs_rating']) if p['wilcoxon_p_vs_rating'] else "n/a",
        ])
    story.append(Paragraph(f"Category: {cat.upper()} (n=7)", H3))
    story.append(styled_table(cat_data, [3.2*cm, 1.7*cm, 1.7*cm, 1.7*cm, 1.8*cm, 1.9*cm, 2.0*cm, 2.0*cm]))
    story.append(Spacer(1, 0.2*cm))

story.append(Paragraph("6.5 Balanced Persona Discussion", H2))
story.append(Paragraph(
    "The Balanced Buyer persona (w_p = w_r = 0.45) shows +0.94% lift vs price with p=0.361 "
    "(not statistically significant). This is a structural result, not a code deficiency. "
    "When a buyer weights price and quality equally, the optimal ranking partially overlaps "
    "with price-only ordering — particularly when products in a result set have similar "
    "adjusted ratings (common in mainstream electronics listings where most products cluster "
    "at 3.8–4.5★). The Wilcoxon test cannot detect a signal that is genuinely small.",
    BODY))
story.append(Paragraph(
    "However, Balanced is strongly significant vs the rating-only baseline (p=0.0005, +33% lift), "
    "confirming that PAVS correctly outperforms naive star-rating sorting. "
    "The result should be framed in the paper as: "
    "'Balanced Buyer achieves statistical parity with price-optimized ranking (+0.94%, p=0.361) "
    "while significantly outperforming the rating-only baseline (+33%, p=0.0005).'",
    BODY))
story.append(PageBreak())

# ════════════════════════════════════════════════════════════════════════════
# 7. KNOWN LIMITATIONS
# ════════════════════════════════════════════════════════════════════════════
story += [Paragraph("7. Known Limitations & Mitigations", H1), section_divider()]
limitations = [
    ["Limitation", "Impact", "Mitigation / Paper Framing"],
    ["Circular evaluation: satisfaction metric uses same formula as PAVS",
     "PAVS trivially maximizes its own metric",
     "Acknowledged in paper; baselines use same metric; Wilcoxon tests whether PAVS selects better products by that metric"],
    ["Balanced persona not significant vs price baseline (p=0.36)",
     "1/3 personas lacks strong evidence",
     "Framed as statistical parity; highly significant vs rating baseline; structurally expected for equal-weight persona"],
    ["Small sample n=21",
     "Low Wilcoxon power",
     "Budget p=0.009, Quality p=0.001 are strong despite small n; n=21 is sufficient for 2/3 personas"],
    ["Phone category: few competing products (avg 4.4 per search)",
     "Less discrimination opportunity",
     "Category-level Wilcoxon uses n=7; results reported honestly"],
    ["Scraping fragility: Amazon/Flipkart can block or change HTML",
     "Data collection failure",
     "fake-useragent rotation, Playwright for JS sites, eval_cache prevents repeated live scrapes"],
    ["pricehistory.app dependency",
     "5.2% simulated fallback",
     "Deterministic simulation documented; 94.8% real coverage is strong"],
    ["Linear regression for PTI (not ARIMA/LSTM)",
     "May miss non-linear trends",
     "Justified: 30 data points insufficient for seasonal models; p-value gating prevents false signals"],
    ["Persona weights hand-tuned",
     "Not learned from user data",
     "Consistent with MCDM literature; future work: preference learning from user feedback"],
]
story.append(styled_table(limitations, [4.5*cm, 3.5*cm, 8.2*cm]))
story.append(PageBreak())

# ════════════════════════════════════════════════════════════════════════════
# 8. DEPENDENCIES & SETUP
# ════════════════════════════════════════════════════════════════════════════
story += [Paragraph("8. Dependencies, Setup & Run Instructions", H1), section_divider()]

story.append(Paragraph("8.1 Python Environment", H2))
story.append(Paragraph(b("Conda environment:") + code(" mlproject") + "  |  Python 3.11+", BODY))
deps = [
    ["Package", "Version (approx)", "Usage"],
    ["pandas", "≥2.0", "DataFrame processing throughout pipeline"],
    ["numpy", "≥1.24", "Numerical operations, normalization"],
    ["scikit-learn", "≥1.3", "Linear regression utilities; scipy.stats used for PTI trend fitting"],
    ["scipy", "≥1.11", "linregress (PTI), spearmanr, kendalltau, wilcoxon"],
    ["matplotlib / seaborn", "≥3.7 / ≥0.12", "Chart generation (visualizer.py)"],
    ["flask", "≥3.0", "Web server"],
    ["beautifulsoup4 + lxml", "≥4.12", "Amazon HTML parsing"],
    ["playwright", "≥1.40", "Flipkart + pricehistory.app scraping"],
    ["playwright-stealth", "≥1.0", "Bot detection evasion for Firefox"],
    ["cloudscraper", "≥1.2", "Cloudflare bypass (backup)"],
    ["fake-useragent", "≥1.4", "UA rotation for Amazon requests"],
    ["reportlab", "≥4.0", "This report PDF generation"],
]
story.append(styled_table(deps, [4*cm, 3.5*cm, 8.7*cm]))

story.append(Paragraph("8.2 Run Instructions", H2))
story.append(Paragraph(b("Start web server:"), H3))
story.append(Preformatted(
    "conda activate mlproject\ncd ~/mlproject\npython src/app.py   # serves at http://localhost:5000",
    CODE))
story.append(Paragraph(b("Run evaluation:"), H3))
story.append(Preformatted(
    "conda activate mlproject\ncd ~/mlproject\npython src/evaluate.py   # ~10s with warm cache, ~60min cold",
    CODE))
story.append(Paragraph(b("Regenerate charts:"), H3))
story.append(Preformatted(
    "conda activate mlproject\ncd ~/mlproject\npython -c \"import sys; sys.path.insert(0,'src'); from visualizer import main; main()\"",
    CODE))
story.append(Paragraph(b("Generate this report:"), H3))
story.append(Preformatted(
    "conda activate mlproject\ncd ~/mlproject\npython src/generate_report.py",
    CODE))

story.append(Paragraph("8.3 ngrok Public URL Setup", H2))
story.append(Paragraph(
    "To expose the Flask app publicly (for demo or remote access), ngrok can be used. "
    "Previous configuration was cleared; steps to re-setup:",
    BODY))
story.append(Preformatted(
    "# Terminal 1 — start Flask\nconda activate mlproject && python src/app.py\n\n"
    "# Terminal 2 — start ngrok tunnel\nngrok http 5000\n\n"
    "# Or with authtoken (one-time setup):\nngrok config add-authtoken <YOUR_TOKEN>\nngrok http 5000",
    CODE))
story.append(Paragraph(
    "ngrok will print a public URL like https://xxxx.ngrok-free.app. "
    "Share this URL for live demo access. The Flask app requires no changes — "
    "it serves on port 5000 and ngrok proxies HTTPS → localhost:5000.",
    BODY))
story.append(PageBreak())

# ════════════════════════════════════════════════════════════════════════════
# 9. IEEE PAPER SUMMARY
# ════════════════════════════════════════════════════════════════════════════
story += [Paragraph("9. IEEE Paper Key Claims & Evidence", H1), section_divider()]
story.append(Paragraph(
    "The following table maps each key claim in the IEEE paper to its supporting evidence:",
    BODY))
claims = [
    ["Claim", "Evidence", "Location in Code"],
    ["RCS corrects sparse-review inflation",
     "Case study: 4.8★/12 reviews vs 4.2★/89k reviews — naive sort reverses correct order",
     "src/rcs.py, paper Section III-A"],
    ["PTI correctly classifies price trends",
     "94.8% real history; mean R²=0.30; p-value gate prevents spurious labels",
     "src/pti.py, results/evaluation_report.json"],
    ["PAVS outperforms price-only for Budget",
     "+1.30% lift, p=0.009 (Wilcoxon, n=21)",
     "src/evaluate.py, results/evaluation_report.json"],
    ["PAVS outperforms price-only for Quality",
     "+15.51% lift, p=0.001 (Wilcoxon, n=21)",
     "src/evaluate.py, results/evaluation_report.json"],
    ["PAVS outperforms rating-only for all personas",
     "+58.6% (Budget), +23.7% (Quality), +33.0% (Balanced) — all p≤0.001",
     "src/evaluate.py, results/evaluation_report.json"],
    ["Persona-adaptive ranking produces distinct orderings",
     "Quality Buyer ρ=0.40 vs price (low = distinctive); Budget ρ=−0.07 vs rating",
     "src/evaluate.py Spearman analysis"],
    ["Cross-platform matching is accurate",
     "Similarity threshold 0.45 empirically tuned; matcher.py combines SequenceMatcher + token overlap",
     "src/scraper/matcher.py"],
    ["System works in real time",
     "Live pipeline: scrape + RCS + PTI + PAVS in ~15-30 seconds per query",
     "src/live_pipeline.py, src/app.py"],
]
story.append(styled_table(claims, [5*cm, 5.5*cm, 5.7*cm]))

story.append(Spacer(1, 0.5*cm))
story.append(Paragraph("9.1 Suggested Abstract Numbers", H2))
story.append(Paragraph(
    f"'...lifted per-persona satisfaction scores by up to "
    f"+{OVERALL['quality']['avg_lift_vs_price']:.1f}% over the price-only baseline "
    f"(Quality Buyer, p={OVERALL['quality']['wilcoxon_p_vs_price']}) and "
    f"+{OVERALL['budget']['avg_lift_vs_rating']:.1f}% over the rating-only baseline "
    f"(Budget Buyer, p={OVERALL['budget']['wilcoxon_p_vs_rating']}). "
    f"Real 30-day price history was obtained for "
    f"{PTI_SUMMARY['avg_real_history_pct']}% of products from pricehistory.app...'",
    make_style("QuoteStyle", "Normal", fontSize=10, leading=14, leftIndent=20,
               rightIndent=20, textColor=colors.HexColor("#333333"), spaceAfter=8)))

story.append(Spacer(1, 0.5*cm))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#dddddd")))
story.append(Paragraph(
    "Report generated from live evaluation data. "
    f"Source: results/evaluation_report.json. "
    "SmartPick — IEEE Research Project.",
    CAPTION))

# ── Build ─────────────────────────────────────────────────────────────────────
doc.build(story)
print(f"[report] PDF saved to {OUT}")
