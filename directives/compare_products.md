# Product Comparison & Matching

## Goal
Compare products between Source market (JP/AliExpress) and Target market (US) to find arbitrage opportunities.

## Inputs
- **Source Products**: List from JP Amazon or AliExpress
- **Target Products**: List from US Amazon
- **Mode**: `standard` (JP→US) or `universal` (AliExpress→US)

## Tools
- `execution/product_comparator.py`
  - `find_similar_in_list()` - Find matching products
  - `ai_semantic_match()` - AI-powered matching for Japanese/weird names
  - `find_opportunities()` - Main comparison logic
  - `calculate_opportunity_score()` - Score opportunities 0-100

## Matching Methods

### 1. Keyword Matching (Legacy)
```python
# Jaccard similarity on extracted keywords
keywords1 = {"kitchen", "towel", "set"}
keywords2 = {"kitchen", "towel", "pack"}
similarity = len(intersection) / len(union)
```
**Threshold**: 30% similarity = match

### 2. AI Semantic Matching (Preferred)
Used when:
- Product name contains Japanese/Chinese characters
- `force_ai=True` (AliExpress products)

```python
ai_semantic_match(jp_product_name, us_products)
# GPT reads whole name, understands product type, finds match
```

## Opportunity Types

### Standard Mode (JP → US)
1. **No Match Found** → High opportunity (product doesn't exist in US)
2. **Match with 3x+ Review Difference** → Medium opportunity (JP more popular)

### Universal Mode (AliExpress → US)
1. **Similar Product Found** → Calculate markup (source vs target price)
2. **No Similar** → Compare with category bestseller (reduced score)

## Scoring Factors
| Factor | Points |
|--------|--------|
| Reviews ≥ 50,000 | +30 |
| Reviews ≥ 10,000 | +25 |
| Rating ≥ 4.5 | +25 |
| Rating ≥ 4.0 | +20 |
| Top 5 position | +25 |
| No US match | +20 |

## Currency Conversion
All prices converted to USD:
- ¥ (JPY) → ×0.0067
- ₽ (RUB) → ×0.011
- € (EUR) → ×1.08
- £ (GBP) → ×1.27
- GEL → ×0.37

## Key Learnings

### ⚠️ Japanese Names
Keyword matching FAILS for Japanese text. Always use AI semantic matching.

### ⚠️ AliExpress Names
Even English names on AliExpress are weird ("Cup Mug Water Coffee DIY"). Use `force_ai=True`.

### ⚠️ Division by Zero
When calculating review ratio, use `max(us_reviews, 1)` to avoid division by zero.
