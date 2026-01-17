# Scraping AliExpress Products

## Goal
Scrape bestseller products from AliExpress Russia for arbitrage analysis with Amazon USA.

## Inputs
- **Category ID**: One of `home-garden`, `pet-supplies`, `office-products`, `sports-outdoors`, `toys-games`, `adult`
- **Product Limit**: Number of products to scrape (default: 20)

## Tools
- `execution/universal_adapter.py` → `UniversalAdapter.scrape_products()`
- Uses **Firecrawl API** for scraping

## Process
1. Get category URL from `ALIEXPRESS_CATEGORY_MAP`
2. Call Firecrawl with **scroll actions** to bypass "Peak Sales" promo section
3. Parse markdown output with regex to extract:
   - Product name
   - Price (in RUB, converted to USD)
   - Image URL
   - Product URL
   - Sales count

## Key Learnings (Updated 2026-01-17)

### ⚠️ Critical: "Peak Sales" Section
The first products on category page are from "На пике продаж" (Peak Sales) promo carousel with only 50-200 sales. **Real bestsellers** (100k+ sales) are below. Solution: scroll 3x before scraping.

### Price Conversion
- AliExpress shows prices in RUB (₽)
- Convert to USD: `price_usd = price_rub / 90`

### Sales Count Parsing
Look for patterns: `(\d[\d\s]*)\s*sold` or `(\d[\d\s]*)\s*продано`

## Outputs
List of normalized product dictionaries with:
```python
{
    "asin": "fc_1_12345",  # Generated ID
    "name": "Product Name",
    "price": {"value": 5.50, "currency": "$"},
    "salesCount": 566627,
    "url": "https://aliexpress.ru/item/...",
    "thumbnailUrl": "https://..."
}
```

## Edge Cases
- Empty markdown → Return empty list
- Price parsing fails → Default to 0
- Name extraction fails → Use "AliExpress Product #N"
