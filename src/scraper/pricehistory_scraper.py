"""
PriceHistory.app integration — fetches real price history for Amazon and Flipkart products.

Discovered API (reverse-engineered from browser JS):
  POST /api/search  {url: product_url}  → {status, code, name}
  POST /api/price/{code}  {}            → {History: {Price: [{y: price, x: date}, ...]}, ...}

Uses Firefox + playwright-stealth to bypass Cloudflare and get real cookies,
then calls the API endpoints from within the browser context.
Supports both Amazon (https://pricehistory.app/amazon-price-tracker) and
Flipkart (https://pricehistory.app/flipkart-price-tracker).
"""
import sys
import json
import re
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent))


_TRACKER_URLS = {
    "amazon":   "https://pricehistory.app/amazon-price-tracker",
    "flipkart": "https://pricehistory.app/flipkart-price-tracker",
}


def _get_browser_session(site: str = "amazon"):
    """Launch Firefox with stealth and return (browser, context, page) after loading the platform-specific tracker page."""
    from playwright.sync_api import sync_playwright
    from playwright_stealth import Stealth

    stealth = Stealth(navigator_webdriver=False)
    p = sync_playwright().start()
    browser = p.firefox.launch(headless=True)
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) "
            "Gecko/20100101 Firefox/125.0"
        ),
        locale="en-IN",
        viewport={"width": 1366, "height": 768},
    )
    page = context.new_page()
    stealth.apply_stealth_sync(page)
    # Load platform-specific tracker page to get valid session cookies
    tracker_url = _TRACKER_URLS.get(site, _TRACKER_URLS["amazon"])
    page.goto(tracker_url, timeout=20000, wait_until="domcontentloaded")
    page.wait_for_timeout(1500)
    return p, browser, page


def get_product_code(product_url: str, site: str = "amazon") -> tuple[str, str]:
    """
    Search pricehistory.app for a product by Amazon or Flipkart URL.
    Returns (product_code, product_name) or ("", "") if not found.
    """
    p, browser, page = _get_browser_session(site)
    try:
        result = page.evaluate(f'''
            async () => {{
                const r = await fetch("https://pricehistory.app/api/search", {{
                    method: "POST",
                    headers: {{"Content-Type": "application/json"}},
                    body: JSON.stringify({{url: "{product_url}"}})
                }});
                return await r.text();
            }}
        ''')
        data = json.loads(result)
        if data.get("status"):
            return data.get("code", ""), data.get("name", "")
        return "", ""
    except Exception as e:
        print(f"[pricehistory] search error: {e}")
        return "", ""
    finally:
        browser.close()
        p.stop()


def get_price_history(product_code: str, site: str = "amazon") -> list:
    """
    Fetch full price history for a product code.
    Returns list of (date_str, price) tuples sorted oldest→newest,
    trimmed to last 30 data points.
    """
    p, browser, page = _get_browser_session(site)
    try:
        # Navigate to the product page to get valid session
        page.goto(
            f"https://pricehistory.app/p/{product_code}",
            timeout=20000,
            wait_until="domcontentloaded",
        )
        page.wait_for_timeout(2000)

        # Call the price API from within browser context (uses real cookies/headers)
        short_code = product_code.split("-")[-1]
        result = page.evaluate(f'''
            async () => {{
                const r = await fetch("https://pricehistory.app/api/price/{short_code}", {{
                    method: "post",
                    headers: FetchHeaders
                }});
                return await r.text();
            }}
        ''')
        data = json.loads(result)
        history_raw = data.get("History", {}).get("Price", [])

        # Parse [{y: price, x: "2024-01-15 10:00:00"}, ...]
        history = []
        for item in history_raw:
            try:
                price = float(item["y"])
                date_str = item["x"][:10]  # YYYY-MM-DD
                history.append((date_str, price))
            except Exception:
                continue

        # Sort by date, keep last 30 unique days
        history.sort(key=lambda x: x[0])
        seen_dates = {}
        for date, price in history:
            seen_dates[date] = price  # keep latest price per day
        history = sorted(seen_dates.items())[-30:]

        # Also extract summary stats
        price_info = data.get("Price", {})
        summary = {
            "current_price": price_info.get("Price"),
            "min_price": price_info.get("MinPrice"),
            "max_price": price_info.get("MaxPrice"),
            "min_price_on": price_info.get("MinPriceOn", "")[:10],
            "max_price_on": price_info.get("MaxPriceOn", "")[:10],
            "total_records": price_info.get("Count", 0),
        }

        print(f"[pricehistory] Got {len(history)} days of price history "
              f"(total records: {summary['total_records']})")
        return history, summary

    except Exception as e:
        print(f"[pricehistory] price fetch error: {e}")
        return [], {}
    finally:
        browser.close()
        p.stop()


def get_price_history_for_url(product_url: str, site: str = "amazon") -> tuple[list, dict]:
    """
    Full flow: Amazon or Flipkart URL → product code → price history.
    Returns (history, summary) where history = [(date, price), ...]
    """
    print(f"[pricehistory] Looking up ({site}): {product_url[:60]}")
    code, name = get_product_code(product_url, site)
    if not code:
        print("[pricehistory] Product not found in pricehistory.app database")
        return [], {}
    print(f"[pricehistory] Found: {name} ({code})")
    return get_price_history(code, site)


# Backwards-compatible alias
def get_price_history_for_asin(amazon_url: str) -> tuple[list, dict]:
    return get_price_history_for_url(amazon_url, site="amazon")


def history_to_pti_format(history: list, product_id: str) -> list:
    """
    Convert [(date, price), ...] to the format pti.fit_price_trends() expects:
    list of {product_id, day, price} dicts.
    """
    if not history:
        return []
    records = []
    for day_idx, (date, price) in enumerate(history):
        records.append({
            "product_id": product_id,
            "day": day_idx,
            "price": price,
        })
    return records
