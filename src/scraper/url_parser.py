"""
Extract product name + source site from any of the 4 supported URLs.
Used as the cross-site search query.
"""
import re
import requests
from urllib.parse import urlparse, unquote
from bs4 import BeautifulSoup

SITE_MAP = {
    "amazon.in":        "amazon",
    "www.amazon.in":    "amazon",
    "flipkart.com":     "flipkart",
    "www.flipkart.com": "flipkart",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}

# Generic noise words to strip from product name before using as search query
_NOISE = re.compile(
    r"\b(assorted|multicolour|multicolor|combo|pack of \d+|free delivery|"
    r"with mic|wired|wireless|new launch|latest|genuine|official)\b",
    re.IGNORECASE,
)


def extract_query(url: str) -> tuple[str, str]:
    """
    Returns (search_query, site_name).
    Also returns the raw product name for use in similarity matching.
    Raises ValueError if URL is not from a supported site.
    """
    parsed = urlparse(url.strip())
    source_site = None
    for key, site in SITE_MAP.items():
        if key in parsed.netloc.lower():
            source_site = site
            break
    if not source_site:
        raise ValueError("Unsupported URL. Please paste a product link from Amazon.in or Flipkart.com.")

    name = _extract_by_site(source_site, parsed)
    if not name or len(name.split()) < 2:
        name = _fetch_title(url)

    if not name:
        raise ValueError("Could not extract product name from URL.")

    query = _clean_query(name)
    return query, source_site


def extract_full_name(url: str) -> str:
    """Return the raw product name from URL (used for similarity matching)."""
    parsed = urlparse(url.strip())
    source_site = None
    for key, site in SITE_MAP.items():
        if key in parsed.netloc.lower():
            source_site = site
            break
    if not source_site:
        return ""
    name = _extract_by_site(source_site, parsed)
    if not name or len(name.split()) < 2:
        name = _fetch_title(url)
    return name.strip()


def _extract_by_site(site: str, parsed) -> str:
    path = unquote(parsed.path)
    try:
        if site == "amazon":
            # /Product-Name-Slug/dp/ASIN → take slug before /dp/
            m = re.search(r"/([^/]+)/dp/", path)
            if m:
                return m.group(1).replace("-", " ")

        elif site == "flipkart":
            # /product-name/p/itm... → take first segment before /p/
            parts = [p for p in path.split("/") if p and p not in ("p",)]
            if parts:
                return parts[0].replace("-", " ")

        elif site == "snapdeal":
            parts = [p for p in path.split("/") if p and p != "product"]
            if parts:
                return parts[0].replace("-", " ")

        elif site in ("croma", "reliance"):
            # /brand-model-name or /search
            parts = [p for p in path.split("/") if p and p not in ("search", "product", "products")]
            if parts:
                return parts[-1].replace("-", " ")

    except Exception:
        pass
    return ""


def _fetch_title(url: str) -> str:
    """Fetch page and extract <title> as fallback."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "lxml")
        title = soup.title.string if soup.title else ""
        for suffix in [" - Amazon.in", " | Flipkart", " - Snapdeal",
                       " | Croma", " - Reliance Digital"]:
            title = title.replace(suffix, "")
        return title.strip()
    except Exception:
        return ""


def _clean_query(name: str) -> str:
    """
    Clean product name for use as a search query.
    - Preserve model numbers and alphanumerics (e.g., WH-1000XM5, BassHeads 100)
    - Remove noise words (colors, generic adjectives)
    - Keep up to 10 meaningful words
    """
    # Remove noise phrases
    name = _NOISE.sub(" ", name)
    # Keep alphanumeric + hyphens (preserves model numbers)
    name = re.sub(r"[^\w\s\-]", " ", name)
    # Collapse spaces
    name = re.sub(r"\s+", " ", name).strip()
    words = [w for w in name.split() if len(w) > 1]
    return " ".join(words[:10])
