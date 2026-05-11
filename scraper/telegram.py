"""
Telegram 公开频道爬虫（通过 RSSHub / t.me/s/ 预览页）。
不需要 Bot Token，直接抓取公开频道的消息预览。
"""

import requests
import time
import re
from datetime import datetime, timezone
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 公开的 AI 优惠 / 羊毛频道（通过 t.me/s/ 预览页抓取，不需要登录）
CHANNELS = [
    "AI_GongJuXiang",     # AI 工具箱
    "chatgpt_deals_cn",   # ChatGPT 优惠（示例）
    "AIGongJuKu",         # AI 工具库
    "gpt_free",           # GPT 免费资源（示例）
    "yangmao_daily",      # 羊毛日报（示例）
]

# AI 相关关键词过滤
KEYWORDS = [
    "chatgpt", "gpt", "claude", "gemini", "openai",
    "anthropic", "copilot", "midjourney", "cursor",
    "ai", "人工智能", "订阅", "plus", "pro",
]


def fetch_channel(channel: str) -> list[dict]:
    """抓取 Telegram 公开频道预览页。"""
    url = f"https://t.me/s/{channel}"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        messages = []

        msg_blocks = soup.select(".tgme_widget_message_wrap")
        for block in msg_blocks[:30]:
            text_el = block.select_one(".tgme_widget_message_text")
            if not text_el:
                continue

            text = text_el.get_text(separator=" ", strip=True)
            if not text or len(text) < 20:
                continue

            # Filter by AI-related keywords
            text_lower = text.lower()
            if not any(kw in text_lower for kw in KEYWORDS):
                continue

            # Get message link
            link_el = block.select_one(".tgme_widget_message_date")
            msg_url = link_el.get("href", "") if link_el else f"https://t.me/{channel}"

            # Get message datetime
            time_el = block.select_one("time.time")
            msg_time = time_el.get("datetime", "") if time_el else ""

            # Extract title (first line or first 80 chars)
            title = text.split("\n")[0] if "\n" in text else text[:80]
            if len(title) > 120:
                title = title[:120] + "..."

            messages.append({
                "title": title,
                "body": text[:500],
                "url": msg_url,
                "created_at": msg_time,
            })

        return messages
    except Exception as e:
        print(f"[Telegram] Error fetching {channel}: {e}")
        return []


def scrape() -> list[dict]:
    """主抓取函数。"""
    seen_ids = set()
    results = []

    for channel in CHANNELS:
        messages = fetch_channel(channel)
        for msg in messages:
            deal_id = f"tg_{hash(msg['url']) & 0xFFFFFFFF:08x}"
            if deal_id in seen_ids:
                continue
            seen_ids.add(deal_id)

            results.append({
                "id": deal_id,
                "source": "telegram",
                "subreddit": f"@{channel}",
                "title": msg["title"],
                "body": msg.get("body", ""),
                "url": msg["url"],
                "author": channel,
                "score": 0,
                "num_comments": 0,
                "created_at": msg.get("created_at", datetime.now(timezone.utc).isoformat()),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })
        time.sleep(1.5)

    print(f"[Telegram] Scraped {len(results)} items")
    return results


if __name__ == "__main__":
    deals = scrape()
    for d in deals[:5]:
        print(f"  [@{d['author']}] {d['title'][:80]}")
