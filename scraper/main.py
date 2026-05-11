"""
Main scraper runner.
Aggregates all data sources, scores/filters, optionally runs LLM second-pass filter,
and outputs to data/deals.json.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper import reddit, v2ex, hackernews, smzdm, chiphell, telegram, nga, twitter
from scraper.scorer import filter_and_rank, deduplicate
from scraper import llm_filter
from scraper.notify import notify_hot_deals
from scraper.history import update_history


OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_FILE = OUTPUT_DIR / "deals.json"

# Minimum relevance score to include
MIN_SCORE = 8
# Maximum number of deals to keep in output
MAX_DEALS = 300
# Maximum age in days for deals to be displayed
MAX_AGE_DAYS = 30


def load_existing_deals() -> list[dict]:
    """Load existing deals from the output file."""
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("deals", [])
        except (json.JSONDecodeError, IOError):
            return []
    return []


def merge_deals(existing: list[dict], new: list[dict]) -> list[dict]:
    """Merge existing and new deals, deduping by id; newer wins."""
    by_id = {}
    for deal in existing:
        by_id[deal["id"]] = deal
    for deal in new:
        by_id[deal["id"]] = deal

    all_deals = list(by_id.values())
    all_deals.sort(
        key=lambda x: (x.get("relevance_score", 0), x.get("created_at", "")),
        reverse=True,
    )
    return all_deals[:MAX_DEALS]


def run_scrapers() -> list[dict]:
    """Run all scrapers and collect raw items."""
    all_items = []

    print("=" * 60)
    print(f"AI Deal Tracker - Scraping at {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    scrapers = [
        ("Reddit", reddit),
        ("V2EX", v2ex),
        ("HackerNews", hackernews),
        ("SMZDM", smzdm),
        ("Chiphell", chiphell),
        ("Telegram", telegram),
        ("NGA", nga),
        ("Twitter/X", twitter),
    ]

    for i, (name, module) in enumerate(scrapers, 1):
        print(f"\n[{i}/{len(scrapers)}] Scraping {name}...")
        try:
            items = module.scrape()
            all_items.extend(items)
        except Exception as e:
            print(f"  ERROR: {e}")

    print(f"\n{'=' * 60}")
    print(f"Total raw items collected: {len(all_items)}")
    return all_items


def main():
    """Main entry point."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Run scrapers
    raw_items = run_scrapers()

    # 2. Deduplicate
    unique_items = deduplicate(raw_items)
    print(f"After deduplication: {len(unique_items)}")

    # 3. Keyword-based scoring and filtering
    deals = filter_and_rank(unique_items, min_score=MIN_SCORE)
    print(f"After scoring (min_score={MIN_SCORE}): {len(deals)} deals")

    # 4. Optional LLM second-pass filter
    if llm_filter.is_llm_enabled():
        print("\n[LLM] Running LLM second-pass filter...")
        deals = llm_filter.batch_filter(deals)
        print(f"After LLM filter: {len(deals)}")

    # 5. Merge with existing deals
    existing_deals = load_existing_deals()
    if existing_deals:
        print(f"Existing deals in file: {len(existing_deals)}")
    merged = merge_deals(existing_deals, deals)
    print(f"Final deal count: {len(merged)}")

    # 6. Build output
    sources_count = {}
    for d in merged:
        src = d.get("source", "unknown")
        sources_count[src] = sources_count.get(src, 0) + 1

    output = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total_deals": len(merged),
        "sources": sources_count,
        "llm_filtered": llm_filter.is_llm_enabled(),
        "deals": merged,
    }

    # 7. Write output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nOutput written to: {OUTPUT_FILE}")

    # 8. Update history (price trend data)
    update_history(merged)

    # 9. Telegram push notifications for hot deals
    notify_hot_deals(merged)

    print(f"\nTop 5 deals:")
    for d in merged[:5]:
        print(f"  [{d.get('relevance_score', 0):3d}] [{', '.join(d.get('tags', [])[:3])}] {d['title'][:60]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
