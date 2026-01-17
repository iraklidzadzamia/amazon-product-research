# Scraping Amazon Bestsellers

## Goal
Scrape bestseller products from Amazon marketplaces (US, JP, UK, DE, etc.) for market comparison.

## Inputs
- **Market Code**: `us`, `jp`, `de`, `uk`, `fr`, `it`, `es`
- **Category**: `home-garden`, `pet-supplies`, `office-products`, `sports-outdoors`, `toys-games`, `adult`
- **Max Results**: Products per category (default: 20)

## Tools
- `execution/amazon_scraper.py` → `scrape_bestsellers()`
- Uses **Apify Actor**: `junglee/amazon-bestsellers`

## Process
1. Get category URL from `CATEGORY_URLS[category][market]`
2. Call Apify actor with parameters:
   - `categoryUrls`: [url]
   - `maxItemsPerStartUrl`: max_results
   - `depthOfCrawl`: 1
   - `scrapeProductDetails`: False (saves credits)
3. Wait for actor to complete
4. Fetch results from dataset

## API Configuration
```python
run_input = {
    "categoryUrls": [category_url],
    "maxItemsPerStartUrl": max_results,
    "depthOfCrawl": 1,
    "language": "en",
    "scrapeProductDetails": False,  # Important: saves Apify credits
}
```

## Outputs
List of product dictionaries:
```python
{
    "asin": "B08XYZ123",
    "name": "Product Title",
    "price": {"value": 29.99, "currency": "$"},
    "stars": 4.5,
    "reviewsCount": 15000,
    "position": 1,
    "url": "https://amazon.com/dp/...",
    "thumbnailUrl": "https://..."
}
```

## Caching
Results are cached for 1 hour using `@st.cache_data(ttl=3600)` to avoid repeated API calls.

## Edge Cases
- Network timeout → Retry once
- Empty results → Return empty list
- Rate limit → Wait and retry (Apify handles this)
