"""
Scoring and classification engine for AI deal posts.
Uses keyword matching, pattern recognition, and heuristic scoring to determine
whether a post is relevant (actual deal/discount info) and classify it by type.
"""

import re
from datetime import datetime, timezone, timedelta


# ============================================================
# KEYWORD DICTIONARIES
# ============================================================

# Target AI products
PRODUCT_KEYWORDS = {
    "chatgpt": {"product": "ChatGPT", "company": "OpenAI", "weight": 3},
    "gpt-4": {"product": "ChatGPT", "company": "OpenAI", "weight": 3},
    "gpt-4o": {"product": "ChatGPT", "company": "OpenAI", "weight": 3},
    "gpt plus": {"product": "ChatGPT", "company": "OpenAI", "weight": 4},
    "openai": {"product": "ChatGPT", "company": "OpenAI", "weight": 2},
    "claude": {"product": "Claude", "company": "Anthropic", "weight": 3},
    "claude pro": {"product": "Claude", "company": "Anthropic", "weight": 4},
    "anthropic": {"product": "Claude", "company": "Anthropic", "weight": 2},
    "gemini": {"product": "Gemini", "company": "Google", "weight": 3},
    "gemini pro": {"product": "Gemini", "company": "Google", "weight": 4},
    "gemini advanced": {"product": "Gemini", "company": "Google", "weight": 4},
    "google one ai": {"product": "Gemini", "company": "Google", "weight": 4},
    "copilot": {"product": "Copilot", "company": "Microsoft", "weight": 3},
    "copilot pro": {"product": "Copilot", "company": "Microsoft", "weight": 4},
    "midjourney": {"product": "Midjourney", "company": "Midjourney", "weight": 3},
    "cursor": {"product": "Cursor", "company": "Cursor", "weight": 3},
    "cursor pro": {"product": "Cursor", "company": "Cursor", "weight": 4},
}

# Deal type keywords (grouped by category)
DEAL_TYPE_KEYWORDS = {
    "regional_pricing": {
        "keywords": [
            "土耳其", "turkey", "阿根廷", "argentina", "印度", "india",
            "巴西", "brazil", "尼日利亚", "nigeria", "菲律宾", "philippines",
            "越南", "vietnam", "区域", "region", "低价区", "低价地区",
            "apple id", "appleid", "google play", "vpn订阅", "换区",
        ],
        "label": "区域套利",
        "label_en": "Regional Pricing",
        "weight": 5,
    },
    "group_buy": {
        "keywords": [
            "拼车", "合租", "共享", "家庭组", "family plan", "家庭版",
            "一起", "分摊", "shared", "group buy", "团购", "车位",
        ],
        "label": "拼车/合租",
        "label_en": "Group Buy",
        "weight": 4,
    },
    "promo_code": {
        "keywords": [
            "优惠码", "promo", "coupon", "促销码", "折扣码", "discount code",
            "邀请码", "referral", "invite", "兑换码", "redeem",
        ],
        "label": "优惠码",
        "label_en": "Promo Code",
        "weight": 5,
    },
    "student_edu": {
        "keywords": [
            "学生", "student", "教育", "edu", ".edu", "学校",
            "university", "academic", "教育优惠",
        ],
        "label": "学生/教育",
        "label_en": "Student/Edu",
        "weight": 4,
    },
    "gift_card": {
        "keywords": [
            "礼品卡", "gift card", "充值卡", "卡密", "兑换",
            "apple gift", "google play卡", "itunes",
        ],
        "label": "礼品卡",
        "label_en": "Gift Card",
        "weight": 4,
    },
    "free_trial": {
        "keywords": [
            "免费", "free", "trial", "试用", "白嫖", "0元",
            "free tier", "free credits", "赠送", "体验",
        ],
        "label": "免费/试用",
        "label_en": "Free/Trial",
        "weight": 4,
    },
    "price_drop": {
        "keywords": [
            "降价", "打折", "折扣", "促销", "特价", "deal",
            "sale", "discount", "cheaper", "便宜", "省钱",
            "划算", "性价比", "低价", "半价",
        ],
        "label": "降价/折扣",
        "label_en": "Price Drop",
        "weight": 4,
    },
    "workaround": {
        "keywords": [
            "薅羊毛", "羊毛", "bug", "漏洞", "技巧", "hack",
            "trick", "方法", "教程", "攻略", "秘密", "隐藏",
            "workaround", "bypass",
        ],
        "label": "薅羊毛/技巧",
        "label_en": "Workaround",
        "weight": 5,
    },
    "api_deal": {
        "keywords": [
            "api", "token", "key", "额度", "credit", "免费额度",
            "api key", "api 价格", "api pricing", "便宜api",
        ],
        "label": "API优惠",
        "label_en": "API Deal",
        "weight": 3,
    },
}

# Negative keywords (reduce score - off-topic)
NEGATIVE_KEYWORDS = [
    "招聘", "hiring", "job", "intern",
    "论文", "paper", "research",
    "开源", "open source",  # Open source is free by nature, not a "deal"
    "bug report", "issue",
    "comparison", "对比评测",
    "tutorial", "教程入门",  # General tutorials, not deal info
]

# Price pattern (detects specific prices being mentioned - good signal)
PRICE_PATTERNS = [
    r"\$\d+",
    r"¥\d+",
    r"\d+元",
    r"\d+美元",
    r"\d+刀",
    r"\d+\/月",
    r"\d+\/年",
    r"\$\d+.*month",
    r"\d+\s*rmb",
    r"\d+\s*cny",
    r"\d+\s*usd",
]


# ============================================================
# SCORING FUNCTION
# ============================================================

def score_deal(item: dict) -> dict:
    """
    Score and classify a deal item.

    Returns the item enriched with:
    - relevance_score: int (0-100, higher = more relevant deal)
    - deal_types: list of matched deal type labels
    - products: list of matched product names
    - tags: combined list of labels for display
    - is_deal: bool (whether this passes the threshold)
    """
    text = f"{item.get('title', '')} {item.get('body', '')}".lower()
    title_text = item.get("title", "").lower()

    score = 0
    deal_types = []
    deal_types_en = []
    products = set()
    companies = set()

    # 1. Product matching
    for keyword, info in PRODUCT_KEYWORDS.items():
        if keyword in text:
            products.add(info["product"])
            companies.add(info["company"])
            # Title match gets bonus
            if keyword in title_text:
                score += info["weight"] * 2
            else:
                score += info["weight"]

    # No product match = very unlikely to be relevant
    if not products:
        return {
            **item,
            "relevance_score": 0,
            "deal_types": [],
            "deal_types_en": [],
            "products": [],
            "companies": [],
            "tags": [],
            "is_deal": False,
        }

    # 2. Deal type matching
    for type_key, type_info in DEAL_TYPE_KEYWORDS.items():
        matched = False
        for kw in type_info["keywords"]:
            if kw in text:
                if not matched:
                    deal_types.append(type_info["label"])
                    deal_types_en.append(type_info["label_en"])
                    matched = True
                # Title match gets bonus
                if kw in title_text:
                    score += type_info["weight"] * 2
                else:
                    score += type_info["weight"]

    # 3. Price pattern matching (strong signal that pricing is being discussed)
    for pattern in PRICE_PATTERNS:
        if re.search(pattern, text):
            score += 3
            break  # Only count once

    # 4. Engagement signal (Reddit/HN score or comment count)
    post_score = item.get("score", 0)
    comments = item.get("num_comments", 0)
    if post_score > 50:
        score += 5
    elif post_score > 10:
        score += 3
    elif post_score > 3:
        score += 1

    if comments > 20:
        score += 3
    elif comments > 5:
        score += 1

    # 5. Negative keyword penalty
    for neg_kw in NEGATIVE_KEYWORDS:
        if neg_kw in text:
            score -= 3

    # 6. Recency bonus (posts within last 3 days get boost)
    try:
        created = item.get("created_at", "")
        if created:
            if isinstance(created, str):
                # Handle various date formats
                for fmt in ["%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S"]:
                    try:
                        created_dt = datetime.strptime(created, fmt)
                        if created_dt.tzinfo is None:
                            created_dt = created_dt.replace(tzinfo=timezone.utc)
                        break
                    except ValueError:
                        continue
                else:
                    created_dt = None

                if created_dt:
                    age = datetime.now(timezone.utc) - created_dt
                    if age < timedelta(days=1):
                        score += 5
                    elif age < timedelta(days=3):
                        score += 3
                    elif age < timedelta(days=7):
                        score += 1
    except Exception:
        pass

    # Normalize score to 0-100
    score = max(0, min(100, score))

    # Determine if this is a real deal (threshold)
    is_deal = score >= 8 and len(deal_types) > 0

    # Build tags
    tags = list(products) + deal_types

    return {
        **item,
        "relevance_score": score,
        "deal_types": deal_types,
        "deal_types_en": deal_types_en,
        "products": list(products),
        "companies": list(companies),
        "tags": tags,
        "is_deal": is_deal,
    }


def filter_and_rank(items: list[dict], min_score: int = 8) -> list[dict]:
    """
    Score all items, filter by minimum score, and rank by relevance.
    Returns only items that are classified as deals, sorted by score desc.
    """
    scored = [score_deal(item) for item in items]
    deals = [item for item in scored if item["is_deal"] and item["relevance_score"] >= min_score]
    deals.sort(key=lambda x: x["relevance_score"], reverse=True)
    return deals


# ============================================================
# UTILITIES
# ============================================================

def deduplicate(items: list[dict]) -> list[dict]:
    """Remove duplicates based on URL and similar titles."""
    seen_urls = set()
    seen_titles = set()
    unique = []

    for item in items:
        url = item.get("url", "")
        title = item.get("title", "").lower().strip()

        # Exact URL match
        if url in seen_urls:
            continue

        # Very similar title (first 40 chars)
        title_key = title[:40]
        if title_key in seen_titles and title_key:
            continue

        seen_urls.add(url)
        seen_titles.add(title_key)
        unique.append(item)

    return unique


if __name__ == "__main__":
    # Test with sample data
    test_items = [
        {
            "title": "土耳其区 ChatGPT Plus 只要70元/月，附教程",
            "body": "用土耳其Apple ID订阅ChatGPT Plus，换算下来大约70-80元人民币",
            "url": "https://example.com/1",
            "score": 25,
            "num_comments": 15,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "title": "GPT-4 vs Claude 3.5 对比评测",
            "body": "今天我们来对比一下两个模型的性能差异",
            "url": "https://example.com/2",
            "score": 100,
            "num_comments": 50,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "title": "Gemini Pro 学生免费使用方法",
            "body": "Google 对 .edu 邮箱用户提供免费 Gemini Advanced 体验",
            "url": "https://example.com/3",
            "score": 10,
            "num_comments": 8,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    ]

    results = filter_and_rank(test_items)
    for r in results:
        print(f"  [{r['relevance_score']:3d}] {r['title'][:60]}")
        print(f"        Tags: {r['tags']}")
        print()
