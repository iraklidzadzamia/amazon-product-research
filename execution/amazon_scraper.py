"""
Amazon Bestsellers Scraper using Apify API

This module provides functions to scrape Amazon bestsellers 
from different marketplaces (US, Japan) using the Apify platform.
"""

import os
import json
from typing import Optional
from dotenv import load_dotenv
from apify_client import ApifyClient

# Load environment variables
load_dotenv()

# Apify Actor ID for Amazon Bestsellers Scraper
ACTOR_ID = "junglee/amazon-bestsellers"

# Market configurations
MARKETS = {
    "us": {
        "name": "USA",
        "flag": "🇺🇸",
        "base_url": "https://www.amazon.com",
        "language": "en",
        "currency": "$"
    },
    "jp": {
        "name": "Japan",
        "flag": "🇯🇵",
        "base_url": "https://www.amazon.co.jp",
        "language": "en",
        "currency": "¥"
    },
    "de": {
        "name": "Germany",
        "flag": "🇩🇪",
        "base_url": "https://www.amazon.de",
        "language": "en",
        "currency": "€"
    },
    "uk": {
        "name": "UK",
        "flag": "🇬🇧",
        "base_url": "https://www.amazon.co.uk",
        "language": "en",
        "currency": "£"
    },
    "fr": {
        "name": "France",
        "flag": "🇫🇷",
        "base_url": "https://www.amazon.fr",
        "language": "en",
        "currency": "€"
    },
    "it": {
        "name": "Italy",
        "flag": "🇮🇹",
        "base_url": "https://www.amazon.it",
        "language": "en",
        "currency": "€"
    },
    "es": {
        "name": "Spain",
        "flag": "🇪🇸",
        "base_url": "https://www.amazon.es",
        "language": "en",
        "currency": "€"
    }
}

# Category URLs for each market
CATEGORY_URLS = {
    "home-garden": {
        "us": "https://www.amazon.com/Best-Sellers-Home-Kitchen/zgbs/home-garden",
        "jp": "https://www.amazon.co.jp/gp/bestsellers/kitchen/",
        "de": "https://www.amazon.de/gp/bestsellers/kitchen/",
        "uk": "https://www.amazon.co.uk/gp/bestsellers/kitchen/",
        "fr": "https://www.amazon.fr/gp/bestsellers/kitchen/",
        "it": "https://www.amazon.it/gp/bestsellers/kitchen/",
        "es": "https://www.amazon.es/gp/bestsellers/kitchen/"
    },
    "pet-supplies": {
        "us": "https://www.amazon.com/Best-Sellers-Pet-Supplies/zgbs/pet-supplies",
        "jp": "https://www.amazon.co.jp/gp/bestsellers/pet-supplies/",
        "de": "https://www.amazon.de/gp/bestsellers/pet-supplies/",
        "uk": "https://www.amazon.co.uk/gp/bestsellers/pet-supplies/",
        "fr": "https://www.amazon.fr/gp/bestsellers/pet-supplies/",
        "it": "https://www.amazon.it/gp/bestsellers/pet-supplies/",
        "es": "https://www.amazon.es/gp/bestsellers/pet-supplies/"
    },
    "office-products": {
        "us": "https://www.amazon.com/Best-Sellers-Office-Products/zgbs/office-products",
        "jp": "https://www.amazon.co.jp/gp/bestsellers/office-products/",
        "de": "https://www.amazon.de/gp/bestsellers/office-products/",
        "uk": "https://www.amazon.co.uk/gp/bestsellers/office-products/",
        "fr": "https://www.amazon.fr/gp/bestsellers/office-products/",
        "it": "https://www.amazon.it/gp/bestsellers/office-products/",
        "es": "https://www.amazon.es/gp/bestsellers/office-products/"
    },
    "sports-outdoors": {
        "us": "https://www.amazon.com/Best-Sellers-Sports-Outdoors/zgbs/sporting-goods",
        "jp": "https://www.amazon.co.jp/gp/bestsellers/sports/",
        "de": "https://www.amazon.de/gp/bestsellers/sports/",
        "uk": "https://www.amazon.co.uk/gp/bestsellers/sports/",
        "fr": "https://www.amazon.fr/gp/bestsellers/sports/",
        "it": "https://www.amazon.it/gp/bestsellers/sports/",
        "es": "https://www.amazon.es/gp/bestsellers/sports/"
    },
    "toys-games": {
        "us": "https://www.amazon.com/Best-Sellers-Toys-Games/zgbs/toys-and-games",
        "jp": "https://www.amazon.co.jp/gp/bestsellers/toys/",
        "de": "https://www.amazon.de/gp/bestsellers/toys/",
        "uk": "https://www.amazon.co.uk/gp/bestsellers/toys/",
        "fr": "https://www.amazon.fr/gp/bestsellers/toys/",
        "it": "https://www.amazon.it/gp/bestsellers/toys/",
        "es": "https://www.amazon.es/gp/bestsellers/toys/"
    }
}

# Keep for backward compatibility
DEFAULT_CATEGORIES = {
    cat: {"us_url": urls["us"], "jp_url": urls["jp"]}
    for cat, urls in CATEGORY_URLS.items()
}


def get_client() -> ApifyClient:
    """Initialize and return Apify client."""
    token = os.getenv("APIFY_API_TOKEN")
    if not token:
        raise ValueError("APIFY_API_TOKEN not found in environment variables. "
                        "Please add it to your .env file.")
    return ApifyClient(token)


def scrape_bestsellers(
    category_url: str,
    max_results: int = 20,
    subcategories: int = 1,
    language: str = "en"
) -> list[dict]:
    """
    Scrape Amazon bestsellers from a category URL.
    
    Args:
        category_url: Full URL to Amazon bestsellers category
        max_results: Maximum number of products to retrieve (default: 20)
        subcategories: Depth of subcategory crawl (default: 1, min: 1)
        language: Output language (default: "en" for English)
    
    Returns:
        List of product dictionaries with keys:
        - asin: Amazon product ID
        - name: Product title
        - price: Dict with 'value' and 'currency'
        - stars: Rating (1-5)
        - reviewsCount: Number of reviews
        - position: Bestseller rank position
        - url: Product URL
        - thumbnailUrl: Product image URL
        - categoryName: Category name
    """
    client = get_client()
    
    # Ensure subcategories is at least 1 (Apify minimum)
    depth = max(1, subcategories)
    
    # Prepare input for the Apify actor (using correct parameter names)
    run_input = {
        "categoryUrls": [category_url],
        "maxItemsPerStartUrl": max_results,  # Correct name!
        "depthOfCrawl": depth,               # Correct name!
        "language": language,
        "detailedInformation": False, # Renamed in some versions
        "scrapeProductDetails": False, # EXPLICITLY disable deep crawling to save usage
        "useCaptchaSolver": False,
    }
    
    print(f"🔄 Scraping: {category_url}")
    print(f"   Max results: {max_results}, Depth: {depth}")
    
    # Run the actor and wait for it to finish
    run = client.actor(ACTOR_ID).call(run_input=run_input)
    
    # Fetch results from the dataset
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    
    print(f"✅ Retrieved {len(items)} products")
    
    return items


def scrape_market(
    market: str,
    categories: list[str] = None,
    max_results: int = 20
) -> dict[str, list[dict]]:
    """
    Scrape bestsellers for multiple categories in a market.
    
    Args:
        market: Market code ("us", "jp", "de", "uk", "fr", "it", "es")
        categories: List of category keys to scrape (default: all)
        max_results: Max products per category
    
    Returns:
        Dict mapping category names to product lists
    """
    if market not in MARKETS:
        raise ValueError(f"Invalid market: {market}. Use one of: {list(MARKETS.keys())}")
    
    if categories is None:
        categories = list(CATEGORY_URLS.keys())
    
    results = {}
    
    for category in categories:
        if category not in CATEGORY_URLS:
            print(f"⚠️ Unknown category: {category}, skipping...")
            continue
        
        if market not in CATEGORY_URLS[category]:
            print(f"⚠️ Category {category} not available for {market}, skipping...")
            continue
        
        category_url = CATEGORY_URLS[category][market]
        
        try:
            products = scrape_bestsellers(
                category_url=category_url,
                max_results=max_results
            )
            results[category] = products
        except Exception as e:
            print(f"❌ Error scraping {category} from {market}: {e}")
            results[category] = []
    
    return results


def save_results(data: dict, filepath: str) -> None:
    """Save scraping results to JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Saved results to {filepath}")


def load_results(filepath: str) -> dict:
    """Load scraping results from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


# ============================================================================
# TESTING
# ============================================================================

def test_connection():
    """Test Apify API connection."""
    try:
        client = get_client()
        # Just try to access the actor info
        actor = client.actor(ACTOR_ID)
        print("✅ Apify API connection successful!")
        print(f"   Actor: {ACTOR_ID}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def test_scrape():
    """Test scraping with a small sample."""
    print("\n🧪 Testing Amazon US scrape (5 products)...")
    
    products = scrape_bestsellers(
        category_url="https://www.amazon.com/Best-Sellers-Home-Kitchen/zgbs/home-garden",
        max_results=5
    )
    
    print("\n📦 Sample products:")
    for p in products[:3]:
        print(f"   #{p.get('position')}: {p.get('name', 'N/A')[:50]}...")
        print(f"       Price: {p.get('price', {}).get('currency', '')}{p.get('price', {}).get('value', 'N/A')}")
        print(f"       Stars: {p.get('stars', 'N/A')} | Reviews: {p.get('reviewsCount', 'N/A')}")
    
    return products


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("=" * 50)
        print("Amazon Scraper - Connection Test")
        print("=" * 50)
        test_connection()
        test_scrape()
    else:
        print("Usage: python amazon_scraper.py --test")
        print("\nThis module is meant to be imported. Run with --test to verify setup.")
