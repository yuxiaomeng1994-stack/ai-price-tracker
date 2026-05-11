"""
什么值得买 (SMZDM) scraper for AI subscription deals.
Uses RSS feed and search page.
"""

import requests
import time
from datetime import datetime, timezone

try:
    import feedparser
except ImportError:
    feedparser = None

from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

SEARCH_KEYWORDS = [
    "ChatGPT",
    "Claude",
    "Gemini",
    "OpenAI",
    "AI 订阅",
    "GPT Plus",
    "AI 会员",
]

RSS_FEEDS = [
    "https://www.smzdm.com/feed",
]


def search_smzdm(keyword: str) -> list[dict]:
    """Search SMZDM for deals related to keyword."""
    url = "https://search.smzdm.com/"
    params = {
        "c": "home",
        "s": keyword,
        "order": "time",
        "v": "b",
    }

    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if resp.status_code != 200:
            print(f"[SMZDM] Search returned status {resp.status_code} for '{keyword}'")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        items = []

        # Parse search results
        feed_items = soup.select(".feed-row-wide, .z-feed-content, li.feed-row-wide")
        if not feed_items:
            feed_items = soup.select("[class*='feed']")

        for item in feed_items[:20]:
            title_el = item.select_one("h5 a, .feed-block-title a, a.feed-nowrap")
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            link = title_el.get("href", "")
            if not link.startswith("http"):
                link = f"https:{link}" if link.startswith("//") else f"https://www.smzdm.com{link}"

            desc_el = item.select_one(".feed-block-descripe, .feed-block-desc")
            desc = desc_el.get_text(strip=True) if desc_el else ""

            items.append({
                "title": title,
                "url": link,
                "body": desc[:500],
            })

        return items
    except Exception as e:
        print(f"[SMZDM] Error searching '{keyword}': {e}")
        return []


def parse_rss() -> list[dict]:
    """Parse SMZDM RSS feeds."""
    if not feedparser:
        print("[SMZDM] feedparser not installed, skipping RSS")
        return []

    results = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:50]:
                title = entry.get("title", "")
                # Only keep AI-related entries
                keywords_match = any(
                    kw.lower() in title.lower()
                    for kw in ["chatgpt", "claude", "gemini", "openai", "gpt", "ai"]
                )
                if not keywords_match:
                    continue

                results.append({
                    "title": title,
                    "url": entry.get("link", ""),
                    "body": entry.get("summary", "")[:500],
                    "published": entry.get("published", ""),
                })
        except Exception as e:
            print(f"[SMZDM] Error parsing RSS {feed_url}: {e}")

    return results


def scrape() -> list[dict]:
    """Main scrape function. Returns list of deal candidates from SMZDM."""
    seen_ids = set()
    results = []

    # Search
    for keyword in SEARCH_KEYWORDS:
        items = search_smzdm(keyword)
        for item in items:
            deal_id = f"smzdm_{hash(item['url']) & 0xFFFFFFFF:08x}"
            if deal_id in seen_ids:
                continue
            seen_ids.add(deal_id)

            results.append({
                "id": deal_id,
                "source": "smzdm",
                "subreddit": "",
                "title": item["title"],
                "body": item.get("body", ""),
                "url": item["url"],
                "author": "",
                "score": 0,
                "num_comments": 0,
                "created_at": item.get("published", datetime.now(timezone.utc).isoformat()),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })
        time.sleep(2)  # Be polite to SMZDM

    # RSS
    rss_items = parse_rss()
    for item in rss_items:
        deal_id = f"smzdm_{hash(item['url']) & 0xFFFFFFFF:08x}"
        if deal_id in seen_ids:
            continue
        seen_ids.add(deal_id)

        results.append({
            "id": deal_id,
            "source": "smzdm",
            "subreddit": "",
            "title": item["title"],
            "body": item.get("body", ""),
            "url": item["url"],
            "author": "",
            "score": 0,
            "num_comments": 0,
            "created_at": item.get("published", datetime.now(timezone.utc).isoformat()),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        })

    print(f"[SMZDM] Scraped {len(results)} items")
    return results


if __name__ == "__main__":
    deals = scrape()
    for d in deals[:5]:
        print(f"  {d['title'][:80]}")
