"""
Twitter/X 爬虫 - 通过公开的 Nitter 实例抓取推文。
Nitter 实例不稳定，代码会尝试多个实例做 fallback。
"""

import requests
import time
from datetime import datetime, timezone
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.woodland.cafe",
    "https://n.opnxng.com",
]

SEARCH_QUERIES = [
    "ChatGPT Plus cheap",
    "ChatGPT Turkey subscription",
    "Claude Pro discount",
    "Gemini Advanced deal",
    "AI subscription deal",
    "ChatGPT student discount",
]


def get_working_instance() -> str | None:
    """Find a working Nitter instance."""
    for instance in NITTER_INSTANCES:
        try:
            resp = requests.get(instance, headers=HEADERS, timeout=8)
            if resp.status_code == 200:
                return instance
        except Exception:
            continue
    return None


def fetch_search(instance: str, query: str) -> list[dict]:
    """Search tweets via Nitter."""
    url = f"{instance}/search"
    params = {"f": "tweets", "q": query}

    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        tweets = []

        items = soup.select(".timeline-item")
        for item in items[:20]:
            content_el = item.select_one(".tweet-content")
            if not content_el:
                continue

            text = content_el.get_text(strip=True)
            if not text or len(text) < 20:
                continue

            link_el = item.select_one("a.tweet-link")
            tweet_url = ""
            if link_el:
                href = link_el.get("href", "")
                tweet_url = f"https://twitter.com{href}" if href.startswith("/") else href

            user_el = item.select_one(".username")
            username = user_el.get_text(strip=True) if user_el else ""

            date_el = item.select_one("time")
            tweet_time = date_el.get("datetime", "") if date_el else ""

            title = text[:120] + ("..." if len(text) > 120 else "")
            tweets.append({
                "title": title, "body": text[:500],
                "url": tweet_url, "author": username, "time": tweet_time,
            })

        return tweets
    except Exception as e:
        print(f"[Twitter] Error searching '{query}': {e}")
        return []


def scrape() -> list[dict]:
    """主抓取函数。"""
    instance = get_working_instance()
    if not instance:
        print("[Twitter] No working Nitter instance found, skipping")
        return []

    print(f"[Twitter] Using instance: {instance}")
    seen_ids = set()
    results = []

    for query in SEARCH_QUERIES:
        tweets = fetch_search(instance, query)
        for tweet in tweets:
            deal_id = f"twitter_{hash(tweet['url'] or tweet['title']) & 0xFFFFFFFF:08x}"
            if deal_id in seen_ids:
                continue
            seen_ids.add(deal_id)
            results.append({
                "id": deal_id, "source": "twitter",
                "subreddit": f"@{tweet.get('author', '')}",
                "title": tweet["title"], "body": tweet.get("body", ""),
                "url": tweet.get("url", ""), "author": tweet.get("author", ""),
                "score": 0, "num_comments": 0,
                "created_at": tweet.get("time", datetime.now(timezone.utc).isoformat()),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })
        time.sleep(1.5)

    print(f"[Twitter] Scraped {len(results)} tweets")
    return results


if __name__ == "__main__":
    deals = scrape()
    for d in deals[:5]:
        print(f"  [{d['subreddit']}] {d['title'][:80]}")
