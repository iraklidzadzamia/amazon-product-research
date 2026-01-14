#!/usr/bin/env python3
"""
Amazon Product Research - Main Analysis Script

Usage:
    python run_analysis.py --test              # Test API connection
    python run_analysis.py --category home-garden --max-results 20
    python run_analysis.py --all-categories --max-results 20
"""

import argparse
import json
import csv
import os
from datetime import datetime

from amazon_scraper import (
    scrape_market,
    save_results,
    load_results,
    test_connection,
    DEFAULT_CATEGORIES
)
from product_comparator import (
    compare_markets,
    opportunities_to_csv_rows
)


# Output directory
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')


def run_full_analysis(
    categories: list[str],
    max_results: int = 20,
    min_reviews: int = 1000,
    skip_scraping: bool = False
) -> dict:
    """
    Run full analysis: scrape US + JP, compare, find opportunities.
    
    Args:
        categories: List of category keys to analyze
        max_results: Max products per category per market
        min_reviews: Min JP reviews to consider as opportunity
        skip_scraping: If True, load from existing JSON files
    
    Returns:
        Dict with opportunities per category
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # File paths
    us_file = os.path.join(DATA_DIR, 'us_bestsellers.json')
    jp_file = os.path.join(DATA_DIR, 'jp_bestsellers.json')
    
    # =========================================================================
    # STEP 1: Scrape or Load Data
    # =========================================================================
    
    if skip_scraping:
        print("\n📂 Loading existing data...")
        us_data = load_results(us_file) if os.path.exists(us_file) else {}
        jp_data = load_results(jp_file) if os.path.exists(jp_file) else {}
    else:
        print("\n" + "=" * 60)
        print("📊 SCRAPING AMAZON BESTSELLERS")
        print("=" * 60)
        
        # Scrape US
        print("\n🇺🇸 Scraping Amazon US...")
        us_data = scrape_market(
            market="us",
            categories=categories,
            max_results=max_results
        )
        save_results(us_data, us_file)
        
        # Scrape JP
        print("\n🇯🇵 Scraping Amazon Japan...")
        jp_data = scrape_market(
            market="jp",
            categories=categories,
            max_results=max_results
        )
        save_results(jp_data, jp_file)
    
    # =========================================================================
    # STEP 2: Compare Markets
    # =========================================================================
    
    print("\n" + "=" * 60)
    print("🔍 COMPARING MARKETS")
    print("=" * 60)
    
    opportunities = compare_markets(
        us_data=us_data,
        jp_data=jp_data,
        min_reviews=min_reviews
    )
    
    # Save opportunities JSON
    opp_file = os.path.join(DATA_DIR, f'opportunities_{timestamp}.json')
    save_results(opportunities, opp_file)
    
    # =========================================================================
    # STEP 3: Export to CSV
    # =========================================================================
    
    print("\n" + "=" * 60)
    print("📝 EXPORTING RESULTS")
    print("=" * 60)
    
    csv_rows = opportunities_to_csv_rows(opportunities)
    csv_file = os.path.join(DATA_DIR, f'opportunities_{timestamp}.csv')
    
    if csv_rows:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
            writer.writeheader()
            writer.writerows(csv_rows)
        print(f"💾 Saved CSV: {csv_file}")
    
    # =========================================================================
    # STEP 4: Summary
    # =========================================================================
    
    print("\n" + "=" * 60)
    print("📈 ANALYSIS SUMMARY")
    print("=" * 60)
    
    total_opps = sum(len(opps) for opps in opportunities.values())
    print(f"\n🎯 Total opportunities found: {total_opps}")
    
    for category, opps in opportunities.items():
        if opps:
            print(f"\n📦 {category}: {len(opps)} opportunities")
            # Show top 3
            for opp in opps[:3]:
                jp = opp['jp_product']
                print(f"   • [{opp['opportunity_score']:.0f}] {jp.get('name', 'N/A')[:60]}...")
                print(f"     JP Reviews: {jp.get('reviewsCount', 0):,} | Stars: {jp.get('stars', 'N/A')}")
    
    print(f"\n📁 Files saved in: {DATA_DIR}/")
    
    return opportunities


def main():
    parser = argparse.ArgumentParser(
        description="Amazon Product Research Tool - Find JP→US opportunities"
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test Apify API connection only'
    )
    
    parser.add_argument(
        '--category', '-c',
        type=str,
        choices=list(DEFAULT_CATEGORIES.keys()),
        help='Single category to analyze'
    )
    
    parser.add_argument(
        '--all-categories', '-a',
        action='store_true',
        help='Analyze all default categories'
    )
    
    parser.add_argument(
        '--max-results', '-m',
        type=int,
        default=20,
        help='Max products per category (default: 20)'
    )
    
    parser.add_argument(
        '--min-reviews', '-r',
        type=int,
        default=1000,
        help='Min JP reviews to consider (default: 1000)'
    )
    
    parser.add_argument(
        '--skip-scraping', '-s',
        action='store_true',
        help='Skip scraping, use existing data files'
    )
    
    parser.add_argument(
        '--list-categories', '-l',
        action='store_true',
        help='List available categories'
    )
    
    args = parser.parse_args()
    
    # List categories
    if args.list_categories:
        print("\n📋 Available categories:")
        for key, urls in DEFAULT_CATEGORIES.items():
            print(f"   • {key}")
        return
    
    # Test mode
    if args.test:
        print("\n🧪 Testing Apify API connection...")
        success = test_connection()
        if success:
            print("\n✅ All tests passed! You're ready to run analysis.")
        return
    
    # Determine categories
    if args.all_categories:
        categories = list(DEFAULT_CATEGORIES.keys())
    elif args.category:
        categories = [args.category]
    else:
        print("❌ Please specify --category or --all-categories")
        print("   Use --list-categories to see options")
        return
    
    # Run analysis
    print("\n" + "=" * 60)
    print("🚀 AMAZON PRODUCT RESEARCH TOOL")
    print("=" * 60)
    print(f"Categories: {', '.join(categories)}")
    print(f"Max results per category: {args.max_results}")
    print(f"Min JP reviews: {args.min_reviews}")
    
    run_full_analysis(
        categories=categories,
        max_results=args.max_results,
        min_reviews=args.min_reviews,
        skip_scraping=args.skip_scraping
    )


if __name__ == "__main__":
    main()
