"""
Telegram Bot 推送模块。
高分优惠（得分≥50）自动推送到指定 Telegram 频道/群组。

启用方式：设置环境变量：
  TELEGRAM_BOT_TOKEN — Bot Token（从 @BotFather 获取）
  TELEGRAM_CHAT_ID — 频道/群组/个人 Chat ID
可选：
  TELEGRAM_MIN_SCORE — 最低推送分数，默认 50
"""

import os
import json
import time
import requests
from datetime import datetime, timezone
from pathlib import Path


def is_enabled() -> bool:
    return bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"))


def get_config():
    return {
        "bot_token": os.environ.get("TELEGRAM_BOT_TOKEN", ""),
        "chat_id": os.environ.get("TELEGRAM_CHAT_ID", ""),
        "min_score": int(os.environ.get("TELEGRAM_MIN_SCORE", "50")),
    }


SENT_FILE = Path(__file__).parent.parent / "data" / ".sent_deals.json"

TYPE_EMOJIS = {
    "区域套利": "🌍", "拼车/合租": "🚗", "优惠码": "🎫",
    "学生/教育": "🎓", "免费/试用": "🆓", "降价/折扣": "💰",
    "薅羊毛/技巧": "🐑", "API优惠": "⚡", "礼品卡": "🎁",
}

SOURCE_NAMES = {
    "reddit": "Reddit", "v2ex": "V2EX", "hackernews": "HackerNews",
    "smzdm": "什么值得买", "chiphell": "Chiphell", "telegram": "Telegram",
    "nga": "NGA", "twitter": "Twitter/X",
}


def load_sent_ids() -> set:
    if SENT_FILE.exists():
        try:
            with open(SENT_FILE, "r") as f:
                return set(json.load(f).get("sent_ids", []))
        except (json.JSONDecodeError, IOError):
            pass
    return set()


def save_sent_ids(sent_ids: set):
    ids_list = list(sent_ids)[-500:]
    SENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SENT_FILE, "w") as f:
        json.dump({"sent_ids": ids_list, "last_updated": datetime.now(timezone.utc).isoformat()}, f)


def escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_message(deal: dict) -> str:
    score = deal.get("relevance_score", 0)
    title = deal.get("title", "无标题")
    url = deal.get("url", "")
    source = SOURCE_NAMES.get(deal.get("source", ""), deal.get("source", ""))
    products = ", ".join(deal.get("products", []))
    deal_types = deal.get("deal_types", [])
    types_str = " ".join(f"{TYPE_EMOJIS.get(t, '🏷️')}{t}" for t in deal_types)
    body = deal.get("body", "")[:200]

    score_badge = "🔥🔥🔥" if score >= 70 else "🔥" if score >= 50 else ""

    lines = [
        f"{score_badge} <b>{escape_html(title)}</b>",
        "",
        f"📊 评分: <b>{score}</b> | 来源: {escape_html(source)}",
    ]
    if products:
        lines.append(f"🏷️ 产品: {escape_html(products)}")
    if types_str:
        lines.append(f"📂 类型: {types_str}")
    if body:
        lines.extend(["", f"📝 {escape_html(body)}"])
    if url:
        lines.extend(["", f'🔗 <a href="{url}">查看原文</a>'])
    lines.extend(["", "━━━━━━━━━━━━━━━━━━", "🐑 AI 羊毛雷达 自动推送"])

    return "\n".join(lines)


def send_message(bot_token: str, chat_id: str, text: str) -> bool:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": False}
    try:
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            return True
        print(f"[Notify] Telegram API error: {resp.status_code} - {resp.text[:200]}")
        return False
    except Exception as e:
        print(f"[Notify] Error sending message: {e}")
        return False


def notify_hot_deals(deals: list[dict]):
    """Send Telegram notifications for new hot deals (score >= min_score)."""
    if not is_enabled():
        print("[Notify] Telegram Bot 未配置，跳过推送")
        return

    config = get_config()
    min_score = config["min_score"]
    sent_ids = load_sent_ids()

    hot_deals = [
        d for d in deals
        if d.get("relevance_score", 0) >= min_score and d.get("id") not in sent_ids
    ]

    if not hot_deals:
        print(f"[Notify] 没有新的高分(≥{min_score})优惠需要推送")
        return

    print(f"[Notify] 发现 {len(hot_deals)} 条新热门优惠，开始推送...")

    sent_count = 0
    for deal in hot_deals[:10]:
        msg = format_message(deal)
        success = send_message(config["bot_token"], config["chat_id"], msg)
        if success:
            sent_ids.add(deal["id"])
            sent_count += 1
            time.sleep(1)

    save_sent_ids(sent_ids)
    print(f"[Notify] 成功推送 {sent_count}/{len(hot_deals)} 条")
