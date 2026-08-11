"""
Persistent evaluation cache — avoids re-scraping and re-fetching price history
on repeated evaluate.py runs.

Cache file: data/eval_cache.json
TTL: 24 hours per entry
Key: source_url (the benchmark Amazon URL from TEST_PRODUCTS)
Value: {
    "cached_at": <unix timestamp>,
    "scraped_rows": [...],             # output of aggregator.scrape_all_sites()
    "price_history": {                 # keyed by buy_url
        "https://...": [ {"product_id": ..., "day": 0, "price": ...}, ... ]
    }
}
"""
import json
import time
from pathlib import Path

_CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "eval_cache.json"
_TTL_SECONDS = 86400  # 24 hours


def load_cache() -> dict:
    """Load cache from disk, purging entries older than TTL. Returns empty dict if file missing."""
    if not _CACHE_PATH.exists():
        return {}
    try:
        with open(_CACHE_PATH) as f:
            raw = json.load(f)
    except Exception:
        return {}
    now = time.time()
    return {k: v for k, v in raw.items() if now - v.get("cached_at", 0) < _TTL_SECONDS}


def save_cache(cache: dict) -> None:
    """Write cache to disk."""
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)


def get_cached(cache: dict, source_url: str):
    """
    Return (scraped_rows, price_history_dict) if a valid cache entry exists, else None.
    price_history_dict maps buy_url -> list of {product_id, day, price} dicts.
    """
    entry = cache.get(source_url)
    if not entry:
        return None
    return entry["scraped_rows"], entry["price_history"]


def set_cached(cache: dict, source_url: str, scraped_rows: list, price_history: dict) -> None:
    """Store scraped_rows and price_history for source_url with current timestamp."""
    cache[source_url] = {
        "cached_at": time.time(),
        "scraped_rows": scraped_rows,
        "price_history": price_history,
    }
