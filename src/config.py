from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "results"
SRC_DIR = BASE_DIR / "src"

PERSONAS = {
    "budget":   {"wp": 0.63, "wr": 0.27, "wt": 0.10, "label": "Budget Buyer"},
    "quality":  {"wp": 0.22, "wr": 0.68, "wt": 0.10, "label": "Quality Buyer"},
    "balanced": {"wp": 0.45, "wr": 0.45, "wt": 0.10, "label": "Balanced Buyer"},
}

PTI_THRESHOLD = 0.002       # normalized slope threshold for trend classification
PRICE_HISTORY_DAYS = 30
TOP_K = 20                  # top-K products for satisfaction simulation
RANDOM_SEED = 42
MIN_PRODUCTS = 500
MAX_PRODUCTS = 1000

CONFIDENCE_THRESHOLDS = {"high": 0.75, "medium": 0.40}

# Kaggle column name variants → our standard names
# ── Scraper settings ──────────────────────────────────────────────────────────
SCRAPER_MAX_PER_SITE   = 8
SCRAPER_REQUEST_DELAY  = (1.5, 3.5)
SCRAPER_TIMEOUT        = 12
SCRAPER_MAX_TOTAL_TIME = 45
DB_PATH = BASE_DIR / "data" / "price_history.db"

# ── Kaggle ─────────────────────────────────────────────────────────────────────
KAGGLE_COLUMN_MAP = {
    "discounted_price": "price",
    "actual_price":     "original_price",
    "rating":           "raw_rating",
    "rating_count":     "review_count",
    "product_name":     "product_name",
    "category":         "category",
    "product_id":       "product_id",
}
