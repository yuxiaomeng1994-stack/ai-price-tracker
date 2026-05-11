"""
价格历史记录模块。
每次运行时记录各产品优惠数量和最低价格，输出 data/history.json 供前端绘图。
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path


HISTORY_FILE = Path(__file__).parent.parent / "data" / "history.json"
MAX_DAYS = 90
PRODUCTS = ["ChatGPT", "Claude", "Gemini", "Copilot", "Midjourney", "Cursor"]

PRICE_PATTERNS_CNY = [
    (r"(\d+)\s*[元块]", 1),
    (r"[¥￥]\s*(\d+)", 1),
    (r"(\d+)\s*(?:rmb|RMB|人民币)", 1),
    (r"\$(\d+)", 7.2),
    (r"(\d+)\s*(?:美元|刀|USD|usd)", 7.2),
]


def extract_price_cny(text: str) -> int | None:
    for pattern, multiplier in PRICE_PATTERNS_CNY:
        match = re.search(pattern, text)
        if match:
            try:
                value = int(match.group(1))
                price = int(value * multiplier)
                if 1 <= price <= 2000:
                    return price
            except (ValueError, IndexError):
                continue
    return None


def load_history() -> dict:
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"last_updated": "", "daily": [], "price_snapshots": []}


def update_history(deals: list[dict]):
    """Update history.json with today's deal counts and best prices."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    history = load_history()

    # Daily counts
    daily_entry = {"date": today, "total": len(deals)}
    for product in PRODUCTS:
        daily_entry[product] = len([d for d in deals if product in d.get("products", [])])
    scores = [d.get("relevance_score", 0) for d in deals]
    daily_entry["avg_score"] = round(sum(scores) / max(len(scores), 1), 1)

    daily = [d for d in history.get("daily", []) if d.get("date") != today]
    daily.append(daily_entry)
    daily.sort(key=lambda x: x["date"])
    history["daily"] = daily[-MAX_DAYS:]

    # Price snapshots
    snapshots = [s for s in history.get("price_snapshots", []) if s.get("date") != today]
    for product in PRODUCTS:
        product_deals = [d for d in deals if product in d.get("products", [])]
        if not product_deals:
            continue
        best_price = None
        best_deal_title = ""
        for deal in product_deals:
            text = f"{deal.get('title', '')} {deal.get('body', '')}"
            price = extract_price_cny(text)
            if price and (best_price is None or price < best_price):
                best_price = price
                best_deal_title = deal.get("title", "")[:80]
        if best_price:
            snapshots.append({
                "date": today, "product": product,
                "est_price_cny": best_price, "best_deal": best_deal_title,
            })

    snapshots.sort(key=lambda x: x.get("date", ""))
    cutoff_dates = sorted(set(s["date"] for s in snapshots))[-MAX_DAYS:]
    history["price_snapshots"] = [s for s in snapshots if s.get("date") in cutoff_dates]

    history["last_updated"] = datetime.now(timezone.utc).isoformat()
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    print(f"[History] Updated: {len(history['daily'])} days, {len(history['price_snapshots'])} price snapshots")
