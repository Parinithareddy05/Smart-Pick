"""Amazon India scraper — requests + BeautifulSoup."""
import re
import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, unquote
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import SCRAPER_TIMEOUT, SCRAPER_REQUEST_DELAY

SEARCH_URL = "https://www.amazon.in/s?k={query}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


def _extract_asin(href: str) -> str:
    """Extract ASIN from any Amazon URL including sspa/click redirects."""
    # Direct dp link
    m = re.search(r"/dp/([A-Z0-9]{10})", href)
    if m:
        return m.group(1)
    # sspa/click URL — the actual URL is URL-encoded in the query string
    decoded = unquote(href)
    m = re.search(r"/dp/([A-Z0-9]{10})", decoded)
    if m:
        return m.group(1)
    return ""


def _parse_review_count(text: str) -> int:
    """Parse Indian format: '4.3L' = 430000, '12K' = 12000, '1,234' = 1234."""
    text = text.strip().replace(",", "")
    try:
        if "L" in text.upper():
            return int(float(text.upper().replace("L", "")) * 100000)
        if "K" in text.upper():
            return int(float(text.upper().replace("K", "")) * 1000)
        m = re.search(r"[\d.]+", text)
        if m:
            return int(float(m.group()))
    except Exception:
        pass
    return 0


def search_products(query: str, max_results: int = 8) -> list:
    time.sleep(random.uniform(*SCRAPER_REQUEST_DELAY))
    url = SEARCH_URL.format(query=quote_plus(query))
    try:
        resp = requests.get(url, headers=HEADERS, timeout=SCRAPER_TIMEOUT)
        if resp.status_code != 200:
            print(f"[amazon] Status {resp.status_code}")
            return []
        if "captcha" in resp.text.lower() and len(resp.text) < 50000:
            print("[amazon] Captcha detected")
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        cards = soup.select("div[data-component-type='s-search-result']")
        results = []
        seen_asins = set()

        for card in cards:
            # Product name — find the longest non-empty anchor text in the card
            # (Amazon splits brand + model into separate links)
            name = ""
            for a in card.find_all("a", href=True):
                t = a.get_text(strip=True)
                if len(t) > len(name) and len(t) > 4 and "Sponsored" not in t and "stars" not in t:
                    name = t
            if not name:
                name_el = card.select_one("h2 span") or card.select_one("span.a-text-normal")
                if name_el:
                    name = name_el.get_text(strip=True)
            if not name or len(name) < 4:
                continue

            # ASIN + buy URL from any anchor in card
            asin = ""
            buy_url = ""
            for a in card.find_all("a", href=True):
                asin = _extract_asin(a["href"])
                if asin:
                    buy_url = f"https://www.amazon.in/dp/{asin}"
                    break
            if not asin or asin in seen_asins:
                continue
            seen_asins.add(asin)

            # Price
            price = 0.0
            price_el = card.select_one("span.a-price-whole")
            if price_el:
                try:
                    price = float(re.sub(r"[^\d]", "", price_el.get_text()))
                except Exception:
                    pass
            if price <= 0:
                continue

            # Rating
            rating = 0.0
            rating_el = card.select_one("span.a-icon-alt")
            if rating_el:
                m = re.search(r"([\d.]+)", rating_el.get_text())
                if m:
                    rating = float(m.group(1))

            # Review count — Amazon India uses (4.3L) format in card text
            reviews = 0
            card_text = card.get_text()
            m = re.search(r"\(([\d.,LKlk]+)\)", card_text)
            if m:
                reviews = _parse_review_count(m.group(1))

            results.append({
                "product_id":   f"amazon_{asin}",
                "product_name": name,
                "price":        price,
                "raw_rating":   rating if rating > 0 else 3.5,
                "review_count": reviews if reviews > 0 else 1,
                "buy_url":      buy_url,
                "site":         "amazon",
            })
            if len(results) >= max_results:
                break

        print(f"[amazon] Found {len(results)} products for '{query}'")
        return results

    except Exception as e:
        print(f"[amazon] Error: {e}")
        return []
