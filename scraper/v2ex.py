"""
V2EX scraper for AI subscription deals.
Uses V2EX's public API and search.
"""

import requests
import time
from datetime import datetime, timezone


HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AIDealTracker/1.0)"
}

# V2EX nodes related to AI / deals
NODES = ["openai", "apple", "google", "ai", "programmer", "deals"]

SEARCH_KEYWORDS = [
    "ChatGPT Plus",
    "Claude Pro",
    "Gemini Pro",
    "订阅",
    "土耳其",
    "阿根廷",
    "印度",
    "便宜",
    "优惠",
    "薅羊毛",
    "拼车",
    "合租",
    "学生优惠",
    "礼品卡",
    "gift card",
    "代充",
    "低价",
    "家庭版",
    "API",
    "省钱",
]


def get_node_topics(node: str, page: int = 1) -> list[dict]:
    """Get topics from a V2EX node."""
    url = f"https://www.v2ex.com/api/v2/nodes/{node}/topics"
    params = {"p": page}

    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("result", [])
        # Fallback to v1 API
        url_v1 = "https://www.v2ex.com/api/topics/show.json"
        resp = requests.get(url_v1, headers=HEADERS, params={"node_name": node}, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[V2EX] Error getting node '{node}': {e}")
        return []


def search_topics(keyword: str) -> list[dict]:
    """Search V2EX using SOV2EX (third-party search engine for V2EX)."""
    url = "https://www.sov2ex.com/api/search"
    params = {
        "q": keyword,
        "sort": "created",
        "order": 0,  # desc
        "size": 20,
    }

    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("hits", [])
        return []
    except Exception as e:
        print(f"[V2EX] Error searching '{keyword}': {e}")
        return []


def parse_topic_v2(topic: dict) -> dict:
    """Parse a V2EX v2 API topic."""
    created = topic.get("created", 0)
    topic_id = topic.get("id", "")

    return {
        "id": f"v2ex_{topic_id}",
        "source": "v2ex",
        "subreddit": topic.get("node", {}).get("name", "") if isinstance(topic.get("node"), dict) else "",
        "title": topic.get("title", ""),
        "body": (topic.get("content", "") or "")[:500],
        "url": f"https://www.v2ex.com/t/{topic_id}",
        "author": topic.get("member", {}).get("username", "") if isinstance(topic.get("member"), dict) else "",
        "score": topic.get("votes", 0),
        "num_comments": topic.get("replies", 0),
        "created_at": datetime.fromtimestamp(created, tz=timezone.utc).isoformat() if created else "",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def parse_search_hit(hit: dict) -> dict:
    """Parse a SOV2EX search result."""
    source = hit.get("_source", {})
    topic_id = source.get("id", hit.get("_id", ""))
    created = source.get("created", "")

    return {
        "id": f"v2ex_{topic_id}",
        "source": "v2ex",
        "subreddit": source.get("node", ""),
        "title": source.get("title", ""),
        "body": (source.get("content", "") or "")[:500],
        "url": f"https://www.v2ex.com/t/{topic_id}",
        "author": source.get("member", ""),
        "score": 0,
        "num_comments": source.get("replies", 0),
        "created_at": created if isinstance(created, str) else datetime.fromtimestamp(created, tz=timezone.utc).isoformat() if created else "",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def scrape() -> list[dict]:
    """Main scrape function. Returns list of deal candidates from V2EX."""
    seen_ids = set()
    results = []

    # Get from relevant nodes
    for node in NODES:
        topics = get_node_topics(node)
        for topic in topics:
            parsed = parse_topic_v2(topic)
            if parsed["id"] not in seen_ids:
                seen_ids.add(parsed["id"])
                results.append(parsed)
        time.sleep(1)

    # Search with keywords
    for keyword in SEARCH_KEYWORDS:
        hits = search_topics(keyword)
        for hit in hits:
            parsed = parse_search_hit(hit)
            if parsed["id"] not in seen_ids:
                seen_ids.add(parsed["id"])
                results.append(parsed)
        time.sleep(1)

    print(f"[V2EX] Scraped {len(results)} topics")
    return results


if __name__ == "__main__":
    deals = scrape()
    for d in deals[:5]:
        print(f"  [{d['subreddit']}] {d['title'][:80]}")
