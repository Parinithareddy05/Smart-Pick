"""
Scrapes Amazon and Flipkart concurrently.
Filters results by 80% similarity to the original product name.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from concurrent.futures import ThreadPoolExecutor, as_completed
from config import SCRAPER_MAX_PER_SITE, SCRAPER_MAX_TOTAL_TIME

from scraper import amazon_scraper, flipkart_scraper
from scraper.matcher import filter_by_similarity

SCRAPERS = {
    "amazon":   amazon_scraper.search_products,
    "flipkart": flipkart_scraper.search_products,
}


def scrape_all_sites(
    query: str,
    original_name: str = "",
    max_per_site: int = SCRAPER_MAX_PER_SITE,
) -> list:
    """
    Scrape Amazon + Flipkart in parallel.
    Filters to ≥80% match with original_name (relaxes to 55% if too few results).
    """
    all_results = []
    site_counts = {}

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(fn, query, max_per_site): site
            for site, fn in SCRAPERS.items()
        }
        for future in as_completed(futures, timeout=SCRAPER_MAX_TOTAL_TIME):
            site = futures[future]
            try:
                rows = future.result()
                site_counts[site] = len(rows)
                all_results.extend(rows)
            except Exception as e:
                print(f"[aggregator] {site} failed: {e}")
                site_counts[site] = 0

    print(f"[aggregator] Amazon={site_counts.get('amazon',0)} "
          f"Flipkart={site_counts.get('flipkart',0)} "
          f"Total={len(all_results)}")

    if original_name and all_results:
        all_results = filter_by_similarity(original_name, all_results)

    return all_results
