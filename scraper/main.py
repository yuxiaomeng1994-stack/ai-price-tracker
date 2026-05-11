"""
Main scraper runner.
Aggregates all data sources, scores/filters, and outputs to data/deals.json.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper import reddit, v2ex, hackernews, smzdm
from scraper.scorer import filter_and_rank, deduplicate


OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_FILE = OUTPUT_DIR / "deals.json"
HISTORY_FILE = OUTPUT_DIR / "history.json"

# Minimum relevance score to include
MIN_SCORE = 8
# Maximum number of deals to keep in output
MAX_DEALS = 200
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
    """Merge existing and new deals, keeping newest and highest-scored."""
    by_id = {}

    # Add existing first
    for deal in existing:
        by_id[deal["id"]] = deal

    # New deals override existing (fresher data)
    for deal in new:
        by_id[deal["id"]] = deal

    all_deals = list(by_id.values())

    # Filter out very old deals
    cutoff = datetime.now(timezone.utc).isoformat()
    # Sort by relevance score, then by recency
    all_deals.sort(key=lambda x: (x.get("relevance_score", 0), x.get("created_at", "")), reverse=True)

    return all_deals[:MAX_DEALS]


def run_scrapers() -> list[dict]:
    """Run all scrapers and collect raw items."""
    all_items = []

    print("=" * 60)
    print(f"AI Deal Tracker - Scraping at {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    # Reddit
    print("\n[1/4] Scraping Reddit...")
    try:
        items = reddit.scrape()
        all_items.extend(items)
    except Exception as e:
        print(f"  ERROR: {e}")

    # V2EX
    print("\n[2/4] Scraping V2EX...")
    try:
        items = v2ex.scrape()
        all_items.extend(items)
    except Exception as e:
        print(f"  ERROR: {e}")

    # HackerNews
    print("\n[3/4] Scraping HackerNews...")
    try:
        items = hackernews.scrape()
        all_items.extend(items)
    except Exception as e:
        print(f"  ERROR: {e}")

    # SMZDM
    print("\n[4/4] Scraping SMZDM...")
    try:
        items = smzdm.scrape()
        all_items.extend(items)
    except Exception as e:
        print(f"  ERROR: {e}")

    print(f"\n{'=' * 60}")
    print(f"Total raw items collected: {len(all_items)}")
    return all_items


def main():
    """Main entry point."""
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Run scrapers
    raw_items = run_scrapers()

    # Deduplicate
    unique_items = deduplicate(raw_items)
    print(f"After deduplication: {len(unique_items)}")

    # Score and filter
    deals = filter_and_rank(unique_items, min_score=MIN_SCORE)
    print(f"After scoring (min_score={MIN_SCORE}): {len(deals)} deals")

    # Merge with existing deals
    existing_deals = load_existing_deals()
    if existing_deals:
        print(f"Existing deals in file: {len(existing_deals)}")
    merged = merge_deals(existing_deals, deals)
    print(f"Final deal count: {len(merged)}")

    # Build output
    output = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total_deals": len(merged),
        "sources": {
            "reddit": len([d for d in merged if d.get("source") == "reddit"]),
            "v2ex": len([d for d in merged if d.get("source") == "v2ex"]),
            "hackernews": len([d for d in merged if d.get("source") == "hackernews"]),
            "smzdm": len([d for d in merged if d.get("source") == "smzdm"]),
        },
        "deals": merged,
    }

    # Write output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nOutput written to: {OUTPUT_FILE}")
    print(f"Top 5 deals:")
    for d in merged[:5]:
        print(f"  [{d.get('relevance_score', 0):3d}] [{', '.join(d.get('tags', [])[:3])}] {d['title'][:60]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
