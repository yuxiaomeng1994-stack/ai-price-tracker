"""
RSS feed 生成器 - 将顶部优惠导出为 RSS 2.0 feed。
输出到 data/feed.xml，供用户通过 RSS 阅读器订阅。
"""

from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape


FEED_FILE = Path(__file__).parent.parent / "data" / "feed.xml"
MAX_ITEMS = 50

SITE_URL = "https://yuxiaomeng1994-stack.github.io/ai-price-tracker/"
FEED_TITLE = "AI 羊毛雷达 - 最新优惠"
FEED_DESCRIPTION = "自动追踪全网 Claude/ChatGPT/Gemini 等 AI 订阅优惠信息"


def format_rfc822(iso_str: str) -> str:
    """ISO 8601 -> RFC 822 (RSS standard)."""
    if not iso_str:
        return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
    except (ValueError, AttributeError):
        return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")


def build_description(deal: dict) -> str:
    """Build HTML description for RSS item."""
    products = ", ".join(deal.get("products", []))
    types = ", ".join(deal.get("deal_types", []))
    body = deal.get("body", "")
    source = deal.get("source", "")
    score = deal.get("relevance_score", 0)

    lines = [
        f"<p><strong>评分:</strong> {score} | <strong>来源:</strong> {escape(source)}</p>",
    ]
    if products:
        lines.append(f"<p><strong>产品:</strong> {escape(products)}</p>")
    if types:
        lines.append(f"<p><strong>类型:</strong> {escape(types)}</p>")
    if body:
        lines.append(f"<p>{escape(body)}</p>")

    return "".join(lines)


def generate_feed(deals: list) -> None:
    """Generate RSS 2.0 feed from top deals."""
    FEED_FILE.parent.mkdir(parents=True, exist_ok=True)

    sorted_deals = sorted(
        deals,
        key=lambda d: (d.get("relevance_score", 0), d.get("created_at", "")),
        reverse=True,
    )[:MAX_ITEMS]

    now_rfc = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

    items_xml = []
    for deal in sorted_deals:
        title = escape(deal.get("title", "无标题"))
        link = escape(deal.get("url", SITE_URL))
        guid = escape(deal.get("id", deal.get("url", "")))
        pub_date = format_rfc822(deal.get("created_at", ""))
        description = build_description(deal)

        categories = []
        for cat in deal.get("products", []) + deal.get("deal_types", []):
            categories.append(f"<category>{escape(cat)}</category>")

        items_xml.append(f"""
    <item>
      <title>{title}</title>
      <link>{link}</link>
      <guid isPermaLink="false">{guid}</guid>
      <pubDate>{pub_date}</pubDate>
      <description><![CDATA[{description}]]></description>
      {''.join(categories)}
    </item>""")

    rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{escape(FEED_TITLE)}</title>
    <link>{escape(SITE_URL)}</link>
    <description>{escape(FEED_DESCRIPTION)}</description>
    <language>zh-CN</language>
    <lastBuildDate>{now_rfc}</lastBuildDate>
    <atom:link href="{escape(SITE_URL)}data/feed.xml" rel="self" type="application/rss+xml" />
    {''.join(items_xml)}
  </channel>
</rss>
"""

    with open(FEED_FILE, "w", encoding="utf-8") as f:
        f.write(rss_xml)

    print(f"[RSS] Generated feed with {len(sorted_deals)} items -> {FEED_FILE}")
