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


def ai_semantic_match(jp_product_name: str, us_products: list[dict], use_ai: bool = True) -> Optional[dict]:
    """
    Use AI to semantically match a Japanese product with US products.
    AI reads the whole name and understands what type of product it is.
    
    Args:
        jp_product_name: Japanese product name (may contain Japanese characters)
        us_products: List of US products to compare against
        use_ai: If True, uses OpenAI for semantic matching
    
    Returns:
        Best matching US product or None
    """
    if not use_ai or not us_products:
        return None
    
    try:
        import os
        import streamlit as st
        from openai import OpenAI
        
        # Get API key
        api_key = None
        try:
            if "OPENAI_API_KEY" in st.secrets:
                api_key = st.secrets["OPENAI_API_KEY"]
        except:
            pass
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            return None
        
        client = OpenAI(api_key=api_key)
        
        # Build list of US products for AI to compare
        us_product_list = []
        for i, p in enumerate(us_products[:30]):  # Limit to 30 for token efficiency
            us_product_list.append(f"{i+1}. {p.get('name', 'Unknown')[:100]}")
        
        us_products_text = "\n".join(us_product_list)
        
        prompt = f"""You are a product matching expert. Your task is to find if a Japanese product has an equivalent or very similar product in the US list.

JAPANESE PRODUCT (may contain Japanese characters - understand what it is):
"{jp_product_name}"

US PRODUCTS LIST:
{us_products_text}

INSTRUCTIONS:
1. Read and understand what the Japanese product actually IS (translate mentally if needed)
2. Look for the SAME or VERY SIMILAR product type in the US list
3. Consider: same function, same use case, same category

RESPOND WITH ONLY:
- If match found: Just the number (e.g., "5")
- If no match: "0"

Do NOT explain. Just respond with the number."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Cheaper model for simple matching
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip()
        
        # Parse the result
        try:
            match_idx = int(result)
            if match_idx > 0 and match_idx <= len(us_products[:30]):
                matched_product = us_products[match_idx - 1].copy()
                matched_product['_similarity_score'] = 0.85  # AI match = high confidence
                matched_product['_match_type'] = 'ai_semantic'
                return matched_product
        except ValueError:
            pass
        
        return None
        
    except Exception as e:
        # Silently fall back to keyword matching
        return None


def find_similar_in_list(
    product: dict,
    product_list: list[dict],
    threshold: float = 0.3,
    use_ai_matching: bool = True
) -> Optional[dict]:
    """
    Find most similar product in a list.
    Uses AI semantic matching for Japanese names, falls back to keywords.
    
    Args:
        product: Product to find match for
        product_list: List of products to search
        threshold: Minimum similarity score (0-1)
        use_ai_matching: If True, try AI matching first for non-English names
    
    Returns:
        Best matching product or None if no match above threshold
    """
    product_name = product.get('name', '')
    if not product_name:
        return None
    
    # Check if name contains non-ASCII (Japanese, Chinese, etc.)
    has_non_ascii = any(ord(char) > 127 for char in product_name)
    
    # Try AI semantic matching first for non-English names
    if use_ai_matching and has_non_ascii:
        ai_match = ai_semantic_match(product_name, product_list)
        if ai_match:
            return ai_match
    
    # Fall back to keyword-based matching
    best_match = None
    best_score = 0
    
    for candidate in product_list:
        candidate_name = candidate.get('name', '')
        score = calculate_similarity(product_name, candidate_name)
        
        if score > best_score and score >= threshold:
            best_score = score
            best_match = {
                **candidate,
                '_similarity_score': score,
                '_match_type': 'keyword'
            }
    
    return best_match


def find_best_seller_match(products: list[dict]) -> Optional[dict]:
    """
    Find the best seller (top ranked product) from a list.
    Returns the product with position 1 or highest reviews if no position.
    """
    if not products:
        return None
    
    # Try to find position 1
    for p in products:
        if p.get('position') == 1:
            return p
    
    # Otherwise return the one with most reviews
    return max(products, key=lambda x: x.get('reviewsCount', 0) or 0, default=None)


def find_opportunities(
    jp_products: list[dict],
    us_products: list[dict],
    similarity_threshold: float = 0.3,
    min_reviews: int = 1000,
    is_universal_source: bool = False
) -> list[dict]:
    """
    Find products that are popular in Source but not in Target.
    If is_universal_source is True, compares Source Price vs Target Best Seller Price (Arbitrage).
    
    Args:
        jp_products: Products from Source Market
        us_products: Products from Target Market
        similarity_threshold: Match threshold
        min_reviews: Minimum reviews
        is_universal_source: If True, uses arbitrage logic
    
    Returns:
        List of opportunity products with analysis
    """
    opportunities = []
    
    for jp_product in jp_products:
        # Filter by minimum reviews (skip for Universal as scraped items are usually top already)
        jp_reviews = jp_product.get('reviewsCount', 0) or 0
        if not is_universal_source and jp_reviews < min_reviews:
            continue

        if is_universal_source:
            # === UNIVERSAL STRATEGY: ARBITRAGE with SIMILARITY MATCHING ===
            # First try to find a SIMILAR product in Target Market
            similar_match = find_similar_in_list(jp_product, us_products, threshold=0.2)
            
            # If no similar found, fall back to best seller for price reference
            if similar_match is None:
                best_seller = find_best_seller_match(us_products)
                if not best_seller:
                    continue
                us_match = best_seller
                match_type = "category_bestseller"
            else:
                us_match = similar_match
                match_type = "similar_product"
            
            # Price Arbitrage Calculation
            src_price_val = jp_product.get('price', {}).get('value', 0)
            if isinstance(src_price_val, str):
                try: src_price_val = float(src_price_val.replace(',',''))
                except: src_price_val = 0
                
            target_price_val = us_match.get('price', {}).get('value', 0)
            if isinstance(target_price_val, str):
                try: target_price_val = float(target_price_val.replace(',',''))
                except: target_price_val = 0
            
            if src_price_val <= 0 or target_price_val <= 0:
                continue
                
            margin_multiplier = target_price_val / src_price_val
            
            # Opportunity Score based on Margin and Match Quality
            # 3x markup = base 100 score. Adjusted by match quality.
            base_score = min(max((margin_multiplier - 1) * 50, 0), 100)
            
            # Boost score if we found a similar product, reduce if just bestseller
            similarity = us_match.get('_similarity_score', 0)
            if match_type == "similar_product" and similarity > 0.3:
                opp_score = base_score  # Good match, keep full score
            elif match_type == "similar_product":
                opp_score = base_score * 0.8  # Weak match, slight penalty
            else:
                opp_score = base_score * 0.5  # Bestseller comparison, big penalty
            
            # Create reason with match info
            if match_type == "similar_product":
                reason = f"Arbitrage: ${src_price_val:.2f} → ${target_price_val:.2f} ({margin_multiplier:.1f}x) | Similar: {us_match.get('name', '')[:40]}..."
            else:
                reason = f"Potential Arbitrage: ${src_price_val:.2f} vs Category Leader ${target_price_val:.2f} ({margin_multiplier:.1f}x) [No exact match found]"
            
            opportunity = {
                'jp_product': jp_product,
                'us_match': us_match,
                'similarity_score': similarity,
                'opportunity_score': opp_score,
                'match_type': match_type,
                'reason': reason
            }
            opportunities.append(opportunity)
            
        else:
            # === STANDARD STRATEGY: MISSING PRODUCTS ===
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
    min_reviews: int = 1000,
    universal_mode: bool = False
) -> dict[str, list[dict]]:
    """
    Compare all categories between US and JP markets (or Universal vs Target).
    
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
            min_reviews=min_reviews,
            is_universal_source=universal_mode
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
