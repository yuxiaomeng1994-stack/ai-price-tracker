"""
Reddit scraper for AI subscription deals.
Uses Reddit's public JSON API (no auth needed).
Targets: r/ChatGPT, r/ClaudeAI, r/Bard, r/singularity, r/ChatGPTPro
"""

import requests
import time
from datetime import datetime, timezone


SUBREDDITS = [
    "ChatGPT",
    "ClaudeAI",
    "Bard",
    "singularity",
    "ChatGPTPro",
    "OpenAI",
]

SEARCH_QUERIES = [
    "cheap subscription",
    "turkey",
    "argentina",
    "india price",
    "student discount",
    "family plan",
    "deal",
    "promo",
    "coupon",
    "free trial",
    "gift card",
    "cheaper",
    "save money",
    "vpn subscribe",
    "regional pricing",
    "plus discount",
    "pro discount",
    "shared account",
    "group buy",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AIDealTracker/1.0; +https://github.com/ai-price-tracker)"
}


def search_subreddit(subreddit: str, query: str, limit: int = 25) -> list[dict]:
    """Search a subreddit for posts matching a query."""
    url = f"https://www.reddit.com/r/{subreddit}/search.json"
    params = {
        "q": query,
        "restrict_sr": "on",
        "sort": "new",
        "t": "month",
        "limit": limit,
    }

    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if resp.status_code == 429:
            time.sleep(5)
            resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {}).get("children", [])
    except Exception as e:
        print(f"[Reddit] Error searching r/{subreddit} for '{query}': {e}")
        return []


def get_new_posts(subreddit: str, limit: int = 50) -> list[dict]:
    """Get newest posts from a subreddit."""
    url = f"https://www.reddit.com/r/{subreddit}/new.json"
    params = {"limit": limit}

    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if resp.status_code == 429:
            time.sleep(5)
            resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {}).get("children", [])
    except Exception as e:
        print(f"[Reddit] Error getting new posts from r/{subreddit}: {e}")
        return []


def parse_post(post_data: dict) -> dict:
    """Parse a Reddit post into a standardized deal format."""
    post = post_data.get("data", {})
    created_utc = post.get("created_utc", 0)

    return {
        "id": f"reddit_{post.get('id', '')}",
        "source": "reddit",
        "subreddit": post.get("subreddit", ""),
        "title": post.get("title", ""),
        "body": (post.get("selftext", "") or "")[:500],
        "url": f"https://reddit.com{post.get('permalink', '')}",
        "author": post.get("author", ""),
        "score": post.get("score", 0),
        "num_comments": post.get("num_comments", 0),
        "created_at": datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat(),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def scrape() -> list[dict]:
    """Main scrape function. Returns list of deal candidates from Reddit."""
    seen_ids = set()
    results = []

    for subreddit in SUBREDDITS:
        # Get new posts
        posts = get_new_posts(subreddit, limit=50)
        for post in posts:
            parsed = parse_post(post)
            if parsed["id"] not in seen_ids:
                seen_ids.add(parsed["id"])
                results.append(parsed)

        time.sleep(1)  # Rate limiting

        # Search with deal-related queries (sample a few to avoid rate limits)
        for query in SEARCH_QUERIES[:5]:
            posts = search_subreddit(subreddit, query, limit=10)
            for post in posts:
                parsed = parse_post(post)
                if parsed["id"] not in seen_ids:
                    seen_ids.add(parsed["id"])
                    results.append(parsed)
            time.sleep(1)

    print(f"[Reddit] Scraped {len(results)} posts from {len(SUBREDDITS)} subreddits")
    return results


if __name__ == "__main__":
    deals = scrape()
    for d in deals[:5]:
        print(f"  [{d['subreddit']}] {d['title'][:80]}")
