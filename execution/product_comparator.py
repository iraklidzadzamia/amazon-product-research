"""
Product Comparator - Find Missing Products

Compares Amazon bestsellers between US and Japan markets
to identify product opportunities (items popular in JP but not in US).
"""

import json
import re
from typing import Optional
from difflib import SequenceMatcher


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    if not text:
        return ""
    # Lowercase, remove special characters, extra spaces
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_keywords(product_name: str, min_length: int = 3) -> set[str]:
    """Extract meaningful keywords from product name."""
    # Common words to ignore
    stop_words = {
        'the', 'and', 'for', 'with', 'from', 'pack', 'set', 'size',
        'inch', 'inches', 'new', 'best', 'sale', 'free', 'shipping',
        'amazon', 'brand', 'basics', 'color', 'black', 'white', 'gray',
        'grey', 'blue', 'red', 'green', 'pink', 'yellow', 'purple',
        'small', 'medium', 'large', 'count', 'piece', 'pieces'
    }
    
    normalized = normalize_text(product_name)
    words = normalized.split()
    
    keywords = {w for w in words if len(w) >= min_length and w not in stop_words}
    return keywords


def calculate_similarity(name1: str, name2: str) -> float:
    """
    Calculate similarity score between two product names.
    Returns value between 0 (no match) and 1 (identical).
    """
    # Method 1: Direct string similarity
    norm1 = normalize_text(name1)
    norm2 = normalize_text(name2)
    
    if not norm1 or not norm2:
        return 0.0
    
    string_sim = SequenceMatcher(None, norm1, norm2).ratio()
    
    # Method 2: Keyword overlap (Jaccard similarity)
    kw1 = extract_keywords(name1)
    kw2 = extract_keywords(name2)
    
    if not kw1 or not kw2:
        return string_sim
    
    intersection = len(kw1 & kw2)
    union = len(kw1 | kw2)
    keyword_sim = intersection / union if union > 0 else 0
    
    # Combined score (weighted average)
    combined = (string_sim * 0.4) + (keyword_sim * 0.6)
    
    return combined


def find_similar_in_list(
    product: dict,
    product_list: list[dict],
    threshold: float = 0.3
) -> Optional[dict]:
    """
    Find most similar product in a list.
    
    Args:
        product: Product to find match for
        product_list: List of products to search
        threshold: Minimum similarity score (0-1)
    
    Returns:
        Best matching product or None if no match above threshold
    """
    product_name = product.get('name', '')
    if not product_name:
        return None
    
    best_match = None
    best_score = 0
    
    for candidate in product_list:
        candidate_name = candidate.get('name', '')
        score = calculate_similarity(product_name, candidate_name)
        
        if score > best_score and score >= threshold:
            best_score = score
            best_match = {
                **candidate,
                '_similarity_score': score
            }
    
    return best_match


def find_opportunities(
    jp_products: list[dict],
    us_products: list[dict],
    similarity_threshold: float = 0.3,
    min_reviews: int = 1000
) -> list[dict]:
    """
    Find products that are popular in Japan but not in US.
    
    Args:
        jp_products: Bestsellers from Japan
        us_products: Bestsellers from US
        similarity_threshold: Below this = considered "not in US"
        min_reviews: Minimum JP reviews to consider
    
    Returns:
        List of opportunity products with analysis
    """
    opportunities = []
    
    for jp_product in jp_products:
        # Filter by minimum reviews
        jp_reviews = jp_product.get('reviewsCount', 0) or 0
        if jp_reviews < min_reviews:
            continue
        
        # Check if similar product exists in US
        us_match = find_similar_in_list(jp_product, us_products, similarity_threshold)
        
        if us_match is None:
            # No match found - this is an opportunity!
            opportunity = {
                'jp_product': {
                    'asin': jp_product.get('asin'),
                    'name': jp_product.get('name'),
                    'price': jp_product.get('price'),
                    'stars': jp_product.get('stars'),
                    'reviewsCount': jp_product.get('reviewsCount'),
                    'position': jp_product.get('position'),
                    'url': jp_product.get('url'),
                    'thumbnailUrl': jp_product.get('thumbnailUrl'),
                },
                'us_match': None,
                'similarity_score': 0,
                'opportunity_score': calculate_opportunity_score(jp_product, None),
                'reason': 'No similar product found in US market'
            }
            opportunities.append(opportunity)
        else:
            # Match found but might still be opportunity if US version underperforms
            us_reviews = us_match.get('reviewsCount', 0) or 0
            score = us_match.get('_similarity_score', 0)
            
            # If JP has significantly more reviews, it's still an opportunity
            if jp_reviews > us_reviews * 3:  # JP has 3x more reviews
                opportunity = {
                    'jp_product': {
                        'asin': jp_product.get('asin'),
                        'name': jp_product.get('name'),
                        'price': jp_product.get('price'),
                        'stars': jp_product.get('stars'),
                        'reviewsCount': jp_reviews,
                        'position': jp_product.get('position'),
                        'url': jp_product.get('url'),
                    },
                    'us_match': {
                        'asin': us_match.get('asin'),
                        'name': us_match.get('name'),
                        'reviewsCount': us_reviews,
                        'url': us_match.get('url'),
                    },
                    'similarity_score': score,
                    'opportunity_score': calculate_opportunity_score(jp_product, us_match),
                    'reason': f'JP product has {jp_reviews/us_reviews:.1f}x more reviews than US equivalent'
                }
                opportunities.append(opportunity)
    
    # Sort by opportunity score
    opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)
    
    return opportunities


def calculate_opportunity_score(jp_product: dict, us_match: Optional[dict]) -> float:
    """
    Calculate opportunity score for a product (0-100).
    Higher = better opportunity.
    """
    score = 0
    
    # Factor 1: JP reviews (more = more demand)
    jp_reviews = jp_product.get('reviewsCount', 0) or 0
    if jp_reviews >= 50000:
        score += 30
    elif jp_reviews >= 10000:
        score += 25
    elif jp_reviews >= 5000:
        score += 20
    elif jp_reviews >= 1000:
        score += 15
    
    # Factor 2: JP rating (higher = better quality)
    jp_stars = jp_product.get('stars', 0) or 0
    if jp_stars >= 4.5:
        score += 25
    elif jp_stars >= 4.0:
        score += 20
    elif jp_stars >= 3.5:
        score += 10
    
    # Factor 3: Position in JP (lower = more popular)
    jp_position = jp_product.get('position', 100) or 100
    if jp_position <= 5:
        score += 25
    elif jp_position <= 10:
        score += 20
    elif jp_position <= 20:
        score += 15
    elif jp_position <= 50:
        score += 10
    
    # Factor 4: No US competition (bonus)
    if us_match is None:
        score += 20
    else:
        us_reviews = us_match.get('reviewsCount', 0) or 0
        if us_reviews < jp_reviews / 10:
            score += 15
        elif us_reviews < jp_reviews / 3:
            score += 10
    
    return min(score, 100)


def compare_markets(
    us_data: dict[str, list[dict]],
    jp_data: dict[str, list[dict]],
    min_reviews: int = 1000
) -> dict[str, list[dict]]:
    """
    Compare all categories between US and JP markets.
    
    Args:
        us_data: Dict of category -> product list for US
        jp_data: Dict of category -> product list for JP
        min_reviews: Minimum reviews to consider
    
    Returns:
        Dict of category -> opportunities list
    """
    all_opportunities = {}
    
    for category in jp_data.keys():
        jp_products = jp_data.get(category, [])
        us_products = us_data.get(category, [])
        
        if not jp_products:
            print(f"⚠️ No JP products for {category}")
            continue
        
        print(f"\n🔍 Analyzing {category}:")
        print(f"   JP products: {len(jp_products)}, US products: {len(us_products)}")
        
        opportunities = find_opportunities(
            jp_products=jp_products,
            us_products=us_products,
            min_reviews=min_reviews
        )
        
        all_opportunities[category] = opportunities
        print(f"   Found {len(opportunities)} opportunities")
    
    return all_opportunities


# ============================================================================
# EXPORT
# ============================================================================

def opportunities_to_csv_rows(opportunities: dict[str, list[dict]]) -> list[dict]:
    """Convert opportunities to flat CSV-ready rows."""
    rows = []
    
    for category, opps in opportunities.items():
        for opp in opps:
            jp = opp['jp_product']
            us = opp.get('us_match') or {}
            
            row = {
                'category': category,
                'opportunity_score': opp['opportunity_score'],
                'reason': opp['reason'],
                'jp_name': jp.get('name', ''),
                'jp_asin': jp.get('asin', ''),
                'jp_price': f"{jp.get('price', {}).get('currency', '')}{jp.get('price', {}).get('value', '')}",
                'jp_stars': jp.get('stars', ''),
                'jp_reviews': jp.get('reviewsCount', ''),
                'jp_position': jp.get('position', ''),
                'jp_url': jp.get('url', ''),
                'us_match_name': us.get('name', ''),
                'us_match_reviews': us.get('reviewsCount', ''),
                'similarity_score': opp.get('similarity_score', 0),
            }
            rows.append(row)
    
    return rows


if __name__ == "__main__":
    # Test similarity function
    print("Testing similarity calculation...")
    
    test_cases = [
        ("Kitchen Towels Set of 5", "Kitchen Towel 5 Pack"),
        ("Japanese Rice Cooker", "Electric Rice Cooker"),
        ("Fluffy Bath Towel Gray", "Random Product Name"),
    ]
    
    for name1, name2 in test_cases:
        sim = calculate_similarity(name1, name2)
        print(f"  '{name1}' vs '{name2}': {sim:.2f}")
