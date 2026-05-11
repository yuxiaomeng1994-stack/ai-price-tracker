"""
Chiphell 爬虫 - 中文数码社区，有专门的优惠活动板块。
使用公开的论坛列表页。
"""

import requests
import time
from datetime import datetime, timezone
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Chiphell 相关板块
FORUM_URLS = [
    "https://www.chiphell.com/forum-419-1.html",  # 活动区
    "https://www.chiphell.com/forum-26-1.html",   # 软件区
]

SEARCH_KEYWORDS = [
    "ChatGPT",
    "Claude",
    "Gemini",
    "OpenAI",
    "AI 订阅",
]


def fetch_forum_page(url: str) -> list[dict]:
    """抓取 Chiphell 论坛列表页。"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        items = []

        # Chiphell 使用 Discuz 论坛
        threads = soup.select("tbody[id^='normalthread_'], tbody[id^='stickthread_']")
        for thread in threads[:30]:
            title_el = thread.select_one("a.xst, th a.s.xst, th a")
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            link = title_el.get("href", "")
            if link and not link.startswith("http"):
                link = f"https://www.chiphell.com/{link}"

            # Only keep AI-related
            keywords_match = any(
                kw.lower() in title.lower()
                for kw in ["chatgpt", "claude", "gemini", "openai", "gpt", "ai", "人工智能"]
            )
            if not keywords_match:
                continue

            author_el = thread.select_one("td.by cite a")
            author = author_el.get_text(strip=True) if author_el else ""

            replies_el = thread.select_one("td.num a.xi2")
            try:
                replies = int(replies_el.get_text(strip=True)) if replies_el else 0
            except ValueError:
                replies = 0

            items.append({
                "title": title,
                "url": link,
                "author": author,
                "replies": replies,
            })

        return items
    except Exception as e:
        print(f"[Chiphell] Error fetching {url}: {e}")
        return []


def scrape() -> list[dict]:
    """主抓取函数。"""
    seen_ids = set()
    results = []

    for url in FORUM_URLS:
        items = fetch_forum_page(url)
        for item in items:
            deal_id = f"chiphell_{hash(item['url']) & 0xFFFFFFFF:08x}"
            if deal_id in seen_ids:
                continue
            seen_ids.add(deal_id)

            results.append({
                "id": deal_id,
                "source": "chiphell",
                "subreddit": "",
                "title": item["title"],
                "body": "",
                "url": item["url"],
                "author": item.get("author", ""),
                "score": 0,
                "num_comments": item.get("replies", 0),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })
        time.sleep(2)

    print(f"[Chiphell] Scraped {len(results)} items")
    return results


if __name__ == "__main__":
    deals = scrape()
    for d in deals[:5]:
        print(f"  {d['title'][:80]}")
