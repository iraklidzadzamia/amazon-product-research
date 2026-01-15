"""
AI Product Analyzer - GPT-powered market analysis

Uses OpenAI GPT to analyze product opportunities and provide
professional seller insights on cultural fit, market potential,
and recommendations.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_openai_client():
    """Get OpenAI client with API key."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    return OpenAI(api_key=api_key)


def format_products_for_analysis(opportunities: dict, source_market: str, target_market: str) -> str:
    """Format product opportunities into a structured text for AI analysis."""
    lines = []
    
    for category, opps in opportunities.items():
        if not opps:
            continue
            
        lines.append(f"\n## Category: {category}")
        
        for i, opp in enumerate(opps[:10], 1):  # Limit to top 10 per category
            jp = opp['jp_product']
            
            lines.append(f"\n### Product {i}: {jp.get('name', 'Unknown')[:100]}")
            lines.append(f"- Opportunity Score: {opp['opportunity_score']}/100")
            lines.append(f"- Reviews in {source_market}: {jp.get('reviewsCount', 0):,}")
            lines.append(f"- Rating: {jp.get('stars', 'N/A')} stars")
            lines.append(f"- Price: {jp.get('price', {}).get('currency', '')}{jp.get('price', {}).get('value', '')}")
            lines.append(f"- Reason: {opp['reason']}")
            
            if opp.get('us_match'):
                us = opp['us_match']
                lines.append(f"- Similar product in {target_market}: {us.get('name', '')[:50]}")
                lines.append(f"- {target_market} reviews: {us.get('reviewsCount', 0):,}")
    
    return "\n".join(lines)


def analyze_opportunities(
    opportunities: dict,
    source_market: str,
    target_market: str,
    source_country: str = "Japan",
    target_country: str = "USA"
) -> str:
    """
    Analyze product opportunities using GPT-4 and provide professional insights.
    
    Args:
        opportunities: Dict of category -> opportunity list
        source_market: Source market code (e.g., 'jp')
        target_market: Target market code (e.g., 'us')
        source_country: Full country name for source
        target_country: Full country name for target
    
    Returns:
        AI-generated analysis text in markdown format
    """
    client = get_openai_client()
    
    # Format products for analysis
    products_text = format_products_for_analysis(opportunities, source_market, target_market)
    
    # Count total opportunities
    total_opps = sum(len(opps) for opps in opportunities.values())
    
    system_prompt = f"""You are an expert Amazon FBA seller and cross-border e-commerce consultant with 10+ years of experience.
You specialize in identifying product opportunities between different markets, understanding cultural differences, and predicting market success.

Your task is to analyze products that are popular in {source_country} but not widely available in {target_country}.
Provide actionable recommendations for sellers looking to import these products to {target_country}.

Your analysis should be:
- Data-driven and practical
- Consider cultural differences between {source_country} and {target_country}
- Identify universal products vs culture-specific products
- Highlight potential challenges (regulations, competition, localization needs)
- Provide clear BUY/SKIP recommendations with reasoning

Respond in Russian language. Use markdown formatting with emojis for better readability."""

    user_prompt = f"""Analyze these {total_opps} product opportunities from {source_country} Amazon bestsellers that could be sold in {target_country}:

{products_text}

Please provide:

1. **📊 Общий обзор** - краткий анализ найденных возможностей

2. **🏆 ТОП-3 рекомендуемых продукта** - какие продукты стоит продавать и почему:
   - Культурная универсальность
   - Потенциал рынка
   - Конкурентные преимущества

3. **⚠️ Продукты, которые лучше пропустить** - какие продукты не подходят для {target_country} и почему:
   - Культурные ограничения
   - Регуляторные барьеры
   - Слишком специфичный спрос

4. **🌍 Культурный анализ** - как культурные различия между {source_country} и {target_country} влияют на эти продукты

5. **💡 Рекомендации по запуску** - практические советы по выходу на {target_country} рынок с этими продуктами

Be specific and reference the actual products in your analysis."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=3000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"❌ Ошибка AI анализа: {str(e)}"


def test_connection() -> bool:
    """Test if OpenAI API connection works."""
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Say 'OK' if you can read this."}],
            max_tokens=10
        )
        return "OK" in response.choices[0].message.content.upper()
    except Exception as e:
        print(f"OpenAI connection error: {e}")
        return False


if __name__ == "__main__":
    # Test the connection
    print("Testing OpenAI connection...")
    if test_connection():
        print("✅ OpenAI connection successful!")
    else:
        print("❌ OpenAI connection failed")
