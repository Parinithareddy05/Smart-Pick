"""
Post-scrape similarity filter — keeps products matching the original product name.
User requirement: at least 80% match to the original product.

Scoring = 40% SequenceMatcher + 60% key-token overlap
Token overlap is weighted more because model numbers (BassHeads 100, WH-1000XM5)
are the most important signal for exact product matching.
"""
import re
from difflib import SequenceMatcher

# Generic words removed before comparing — only brand + model tokens count
NOISE_WORDS = {
    "assorted", "multicolour", "multicolor", "combo", "pack", "of", "with",
    "and", "for", "the", "a", "an", "in", "ear", "wired", "wireless",
    "new", "latest", "original", "genuine", "official", "free", "delivery",
    "black", "white", "red", "blue", "green", "gold", "silver", "pink",
    "grey", "grey", "purple", "yellow", "orange", "edition", "special",
    "1", "2", "3", "pack", "piece", "set", "buy", "online",
    # Product category words — too generic
    "headphones", "earphones", "earbuds", "headset", "speaker", "speakers",
    "laptop", "mobile", "phone", "smartphone", "tablet", "camera", "watch",
    "charger", "cable", "neckband", "buds", "audio", "sound", "music",
    "electronics", "india", "review", "ratings",
}


def _tokenize(name: str) -> set:
    """Lowercase, strip punctuation, remove noise words."""
    name = name.lower()
    name = re.sub(r"[^\w\s-]", " ", name)
    tokens = set(name.split())
    return tokens - NOISE_WORDS


def _similarity(a: str, b: str) -> float:
    """
    Returns similarity score 0.0–1.0.
    Higher score = names are more similar = more likely same product.
    """
    a_clean = a.lower().strip()
    b_clean = b.lower().strip()

    # Sequence similarity (character-level)
    seq = SequenceMatcher(None, a_clean, b_clean).ratio()

    # Token overlap (brand + model number matching)
    a_tok = _tokenize(a)
    b_tok = _tokenize(b)
    if a_tok and b_tok:
        overlap = len(a_tok & b_tok) / max(len(a_tok), len(b_tok))
    else:
        overlap = 0.0

    # 40% sequence + 60% token overlap
    return 0.4 * seq + 0.6 * overlap


def filter_by_similarity(
    original_name: str,
    scraped_rows: list,
    threshold: float = 0.45,
    min_results: int = 2,
) -> list:
    """
    Keep only products with similarity >= 80% to the original product name.
    Sorted by similarity score descending.

    If fewer than min_results pass 80%, relax to 55% (still strict — filters
    completely different models, keeps same product with minor name differences).
    Never relaxes below 55% to ensure relevance.
    """
    if not scraped_rows or not original_name:
        return scraped_rows

    scored = []
    for row in scraped_rows:
        name = row.get("product_name", "")
        score = _similarity(original_name, name)
        scored.append((score, row))

    # Primary filter: 80%
    filtered = [(s, r) for s, r in scored if s >= threshold]

    # Relaxed fallback: 55% — still filters different models
    if len(filtered) < min_results:
        filtered = [(s, r) for s, r in scored if s >= 0.55]
        if filtered:
            print(f"[matcher] Relaxed to 55% — found {len(filtered)} results")

    # Last resort: return top 3 by score (never empty-handed)
    if len(filtered) < min_results:
        filtered = sorted(scored, key=lambda x: x[0], reverse=True)[:min_results]
        print(f"[matcher] Using top {min_results} by score")

    # Sort best match first
    filtered.sort(key=lambda x: x[0], reverse=True)

    result = []
    for score, row in filtered:
        row = dict(row)
        row["similarity_score"] = round(score, 3)
        row["match_pct"] = f"{score*100:.0f}%"
        result.append(row)

    kept = len(result)
    total = len(scraped_rows)
    best = result[0]["match_pct"] if result else "0%"
    print(f"[matcher] {kept}/{total} products kept · best match: {best}")
    return result
