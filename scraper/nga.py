"""
NGA (艾泽拉斯国家地理) 论坛爬虫。
NGA 有大量 AI 相关讨论，特别是数码区和软件区。
"""

import requests
import time
from datetime import datetime, timezone
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

FORUMS = {
    "数码": 414,
    "软件": 436,
    "AI": 691,
}

SEARCH_KEYWORDS = [
    "ChatGPT", "Claude", "Gemini", "GPT Plus",
    "订阅", "优惠", "便宜", "薅羊毛",
    "土耳其", "阿根廷", "拼车", "合租",
]


def fetch_forum_page(fid: int) -> list[dict]:
    """抓取 NGA 论坛板块帖子列表。"""
    url = "https://bbs.nga.cn/thread.php"
    params = {"fid": fid, "page": 1}

    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if resp.status_code != 200:
            return []

        resp.encoding = "gbk"
        soup = BeautifulSoup(resp.text, "html.parser")
        items = []

        rows = soup.select("tr.topicrow, tr[class*='topic']")
        for row in rows[:30]:
            title_el = row.select_one("a.topic, a[href*='read.php']")
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title:
                continue

            title_lower = title.lower()
            if not any(kw.lower() in title_lower for kw in [
                "chatgpt", "claude", "gemini", "openai", "gpt", "ai",
                "人工智能", "订阅", "plus", "pro", "优惠", "便宜",
                "薅羊毛", "拼车", "合租", "土耳其", "阿根廷"
            ]):
                continue

            link = title_el.get("href", "")
            if link and not link.startswith("http"):
                link = f"https://bbs.nga.cn/{link}"

            reply_el = row.select_one("a.replies, td.c3 a")
            replies = 0
            if reply_el:
                try:
                    replies = int(reply_el.get_text(strip=True))
                except ValueError:
                    pass

            author_el = row.select_one("a.author, td.c4 a")
            author = author_el.get_text(strip=True) if author_el else ""

            items.append({"title": title, "url": link, "author": author, "replies": replies})

        return items
    except Exception as e:
        print(f"[NGA] Error fetching forum fid={fid}: {e}")
        return []


def search_nga(keyword: str) -> list[dict]:
    """通过 NGA 搜索接口搜索帖子。"""
    url = "https://bbs.nga.cn/thread.php"
    params = {"key": keyword, "fid": 0, "page": 1}

    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if resp.status_code != 200:
            return []

        resp.encoding = "gbk"
        soup = BeautifulSoup(resp.text, "html.parser")
        items = []

        rows = soup.select("tr.topicrow, tr[class*='topic']")
        for row in rows[:15]:
            title_el = row.select_one("a.topic, a[href*='read.php']")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            link = title_el.get("href", "")
            if link and not link.startswith("http"):
                link = f"https://bbs.nga.cn/{link}"
            items.append({"title": title, "url": link, "author": "", "replies": 0})

        return items
    except Exception as e:
        print(f"[NGA] Error searching '{keyword}': {e}")
        return []


def scrape() -> list[dict]:
    """主抓取函数。"""
    seen_ids = set()
    results = []

    for name, fid in FORUMS.items():
        items = fetch_forum_page(fid)
        for item in items:
            deal_id = f"nga_{hash(item['url']) & 0xFFFFFFFF:08x}"
            if deal_id in seen_ids:
                continue
            seen_ids.add(deal_id)
            results.append({
                "id": deal_id, "source": "nga", "subreddit": name,
                "title": item["title"], "body": "", "url": item["url"],
                "author": item.get("author", ""), "score": 0,
                "num_comments": item.get("replies", 0),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })
        time.sleep(2)

    for keyword in SEARCH_KEYWORDS[:8]:
        items = search_nga(keyword)
        for item in items:
            deal_id = f"nga_{hash(item['url']) & 0xFFFFFFFF:08x}"
            if deal_id in seen_ids:
                continue
            seen_ids.add(deal_id)
            results.append({
                "id": deal_id, "source": "nga", "subreddit": "",
                "title": item["title"], "body": "", "url": item["url"],
                "author": item.get("author", ""), "score": 0,
                "num_comments": item.get("replies", 0),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })
        time.sleep(2)

    print(f"[NGA] Scraped {len(results)} items")
    return results


if __name__ == "__main__":
    deals = scrape()
    for d in deals[:5]:
        print(f"  [{d['subreddit']}] {d['title'][:80]}")
