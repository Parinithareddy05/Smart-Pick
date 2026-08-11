"""Flipkart scraper — Playwright (handles anti-bot JS challenge)."""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from urllib.parse import quote_plus

SEARCH_URL = "https://www.flipkart.com/search?q={query}&sort=relevance"


def _make_product_id(url: str) -> str:
    m = re.search(r"/p/(itm[A-Za-z0-9]+)", url)
    if m:
        return f"flipkart_{m.group(1)}"
    return f"flipkart_{abs(hash(url)) % 999999}"


def _parse_price(text: str) -> float:
    try:
        return float(re.sub(r"[^\d.]", "", text))
    except Exception:
        return 0.0


def _parse_reviews(text: str) -> int:
    """Parse '14,83,849' → 1483849 or '14L' → 1400000."""
    text = text.replace(",", "").strip()
    try:
        if text.endswith("L"):
            return int(float(text[:-1]) * 100000)
        if text.endswith("K"):
            return int(float(text[:-1]) * 1000)
        return int(text)
    except Exception:
        return 0


def search_products(query: str, max_results: int = 8) -> list:
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        print("[flipkart] playwright not installed — skipping")
        return []

    url = SEARCH_URL.format(query=quote_plus(query))
    results = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="en-IN",
            )
            page = context.new_page()
            page.goto(url, timeout=20000)

            # Dismiss login popup
            try:
                page.wait_for_selector("button._2KpZ6l._2doB4z", timeout=3000)
                page.click("button._2KpZ6l._2doB4z")
            except PWTimeout:
                pass

            page.wait_for_timeout(3000)

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page.content(), "lxml")
            browser.close()

        seen_urls = set()
        product_links = soup.select("a[href*='/p/']")

        for link in product_links:
            href = link.get("href", "")
            if not href.startswith("http"):
                href = "https://www.flipkart.com" + href
            if href in seen_urls:
                continue

            # Walk up to find the product card container
            # Look for a div that contains price (₹) and rating
            card = link.find_parent("div")
            if not card:
                continue

            # Keep going up until card has a ₹ symbol
            for _ in range(5):
                if card and "₹" in card.get_text():
                    break
                card = card.find_parent("div") if card else None
            if not card:
                continue

            card_text = card.get_text(strip=True)

            # Product name: prefer title attribute, then clean text
            name = link.get("title", "").strip()
            if not name:
                name = link.get_text(separator=" ", strip=True)
            # Strip junk prefixes Flipkart injects
            name = re.sub(r"^(Add to Compare\s*)+", "", name, flags=re.IGNORECASE).strip()
            name = re.sub(r"^\d+\.\s*", "", name).strip()
            # Strip trailing "Add to Compare" too
            name = re.sub(r"\s*(Add to Compare\s*)+$", "", name, flags=re.IGNORECASE).strip()
            if not name or len(name) < 5:
                continue

            # Price: find the discounted price element (first ₹ div with short text)
            price = 0.0
            # Look for the discounted price div (class hZ3P6w or similar short price)
            for el in card.find_all(["div", "span"]):
                t = el.get_text(strip=True)
                # Match patterns like "₹299" (not "₹299₹99970% off")
                if re.match(r"^₹[\d,]+$", t):
                    price = _parse_price(t)
                    if price > 0:
                        break

            # Fallback: parse first price from card text
            if price <= 0:
                m = re.search(r"₹([\d,]+)", card_text)
                if m:
                    price = _parse_price(m.group(1))
            if price <= 0 or price > 100000:
                continue

            # Rating: find a div/span with a single float 1.0–5.0
            rating = 0.0
            for el in card.find_all(["div", "span"]):
                t = el.get_text(strip=True)
                if re.match(r"^\d\.\d$", t):
                    v = float(t)
                    if 1.0 <= v <= 5.0:
                        rating = v
                        break

            # Review count: find pattern like "(14,83,849)" or "4.3(14,83,849)"
            reviews = 0
            m = re.search(r"\(([\d,L]+)\)", card_text)
            if m:
                reviews = _parse_reviews(m.group(1))

            seen_urls.add(href)
            results.append({
                "product_id":   _make_product_id(href),
                "product_name": name[:150],
                "price":        price,
                "raw_rating":   rating if rating > 0 else 3.5,
                "review_count": reviews if reviews > 0 else 1,
                "buy_url":      href,
                "site":         "flipkart",
            })
            if len(results) >= max_results:
                break

    except Exception as e:
        print(f"[flipkart] Error: {e}")

    print(f"[flipkart] Found {len(results)} products for '{query}'")
    return results
