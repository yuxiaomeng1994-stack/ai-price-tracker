"""
HackerNews scraper for AI subscription deals.
Uses Algolia's HN Search API (no auth needed, very reliable).
"""

import requests
import time
from datetime import datetime, timezone


ALGOLIA_URL = "https://hn.algolia.com/api/v1/search_by_date"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AIDealTracker/1.0)"
}

SEARCH_QUERIES = [
    "ChatGPT Plus cheap",
    "Claude Pro subscription",
    "Gemini Pro deal",
    "OpenAI pricing",
    "Anthropic pricing",
    "Google AI pricing",
    "ChatGPT Turkey",
    "ChatGPT Argentina",
    "AI subscription deal",
    "ChatGPT discount",
    "Claude discount",
    "Gemini discount",
    "ChatGPT student",
    "AI free tier",
    "GPT-4 cheap",
    "Claude free",
]


def search_hn(query: str, limit: int = 20) -> list[dict]:
    """Search HackerNews via Algolia API."""
    params = {
        "query": query,
        "tags": "(story,comment)",
        "hitsPerPage": limit,
        "numericFilters": "created_at_i>{}".format(
            int(time.time()) - 30 * 24 * 3600  # Last 30 days
        ),
    }

    try:
        resp = requests.get(ALGOLIA_URL, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("hits", [])
    except Exception as e:
        print(f"[HackerNews] Error searching '{query}': {e}")
        return []


def parse_hit(hit: dict) -> dict:
    """Parse an Algolia HN hit into a standardized deal format."""
    object_id = hit.get("objectID", "")
    story_id = hit.get("story_id") or object_id
    created_at = hit.get("created_at", "")

    # Determine the best URL
    if hit.get("url"):
        source_url = hit["url"]
    elif hit.get("story_id"):
        source_url = f"https://news.ycombinator.com/item?id={hit['story_id']}"
    else:
        source_url = f"https://news.ycombinator.com/item?id={object_id}"

    title = hit.get("title") or hit.get("story_title") or ""
    body = hit.get("comment_text") or hit.get("story_text") or ""

    return {
        "id": f"hn_{object_id}",
        "source": "hackernews",
        "subreddit": "",  # Not applicable for HN
        "title": title,
        "body": body[:500] if body else "",
        "url": source_url,
        "author": hit.get("author", ""),
        "score": hit.get("points") or 0,
        "num_comments": hit.get("num_comments") or 0,
        "created_at": created_at,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def scrape() -> list[dict]:
    """Main scrape function. Returns list of deal candidates from HackerNews."""
    seen_ids = set()
    results = []

    for query in SEARCH_QUERIES:
        hits = search_hn(query, limit=20)
        for hit in hits:
            parsed = parse_hit(hit)
            if parsed["id"] not in seen_ids:
                seen_ids.add(parsed["id"])
                results.append(parsed)
        time.sleep(0.5)  # Algolia is generous with rate limits

    print(f"[HackerNews] Scraped {len(results)} items")
    return results


if __name__ == "__main__":
    deals = scrape()
    for d in deals[:5]:
        print(f"  {d['title'][:80]} ({d['score']} pts)")
