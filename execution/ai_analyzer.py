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
You are evaluating products from {source_country} (AliExpress) for potential sale on Amazon {target_country}.

## CRITICAL: UNDERSTAND THE DATA

The products below show:
- **Source Price**: What we BUY the product for on AliExpress (the listed price like $3, $5, $10)
- **Market Leader Price**: What SIMILAR products SELL FOR on Amazon USA (the comparison price like $29.94)
- **Markup**: How much higher Amazon price is vs AliExpress (e.g., 7.3x = 7.3 times higher)

## YOUR PROFESSIONAL EVALUATION FRAMEWORK (2025)

### ⚠️ CRITICAL PRICING RULES (for AMAZON SELLING PRICE, NOT source price!):
- **Sweet Spot**: Want to SELL at $30-$100 on Amazon
- **Under $20 SELLING price**: REJECT - FBA fixed fees make it unprofitable
- **BUT: Low SOURCE price ($3-$10) is GOOD if Amazon SELLS at $30+!**

### 💰 ARBITRAGE MATH:
- Source $5 → Sells for $30 on Amazon = **EXCELLENT** (6x markup, enough for profit)
- Source $5 → Sells for $10 on Amazon = **BAD** (2x markup, not enough after fees)
- Need minimum **3-4x markup** to be profitable after FBA fees

### PROFITABILITY CALCULATION:
If Amazon sells at $30:
- FBA Fees: ~$10-12 (Referral 15% + Fulfillment ~$5)
- If source cost $5, profit = $30 - $5 - $12 = $13 (43% margin) = GOOD
- If source cost $15, profit = $30 - $15 - $12 = $3 (10% margin) = BAD

### COMPETITION ANALYSIS:
- If US competitor has >50,000 reviews = VERY HARD to compete
- If US competitor has >10,000 reviews = HARD but possible with differentiation
- If US competitor has <1000 reviews = OPPORTUNITY
- Check if the Amazon match makes sense - sometimes algorithm matches wrong products

### SIZE & LOGISTICS:
- Standard Size = PREFERRED (lower fees)
- Oversize = CAUTION (significantly higher fees)
- Fragile items (glass, ceramics) = extra packaging costs

### IP & LEGAL RED FLAGS:
- Famous brand names in product = likely IP protected, SKIP
- Unique patented designs = risky
- Generic/commodity products = safer

### DECISION MATRIX:
**BUY** if: Markup 4x+, Amazon price $30+, manageable competition, no IP issues
**MAYBE** if: Markup 3-4x, needs more research on exact fees
**SKIP** if: Markup <3x, Amazon price <$20, famous brand, 100k+ competitor reviews

Respond in Russian. Use markdown + emojis. Be brutally honest - seller's capital is at stake."""

    user_prompt = f"""Проанализируй эти {total_opps} продуктовых возможностей из {source_country} для продажи на Amazon {target_country}:

{products_text}

Предоставь профессиональный анализ:

## 📊 EXECUTIVE SUMMARY
- Сколько продуктов заслуживают внимания
- Общее качество найденных возможностей (низкое/среднее/высокое)

## 🟢 РЕКОМЕНДУЮ К ЗАКУПКЕ (BUY)
Для каждого продукта укажи:
- Почему подходит (цена, маржа, конкуренция)
- Потенциальная маржа (оценка)
- Риски и как их минимизировать
- Конкретные action items

## 🟡 ВОЗМОЖНЫЕ ВАРИАНТЫ (MAYBE)  
Продукты с потенциалом, но требующие дополнительного исследования

## 🔴 ПРОПУСТИТЬ (SKIP)
- Конкретные причины отказа (цена слишком низкая, высокая конкуренция, IP риски)
- Чем рискует продавец

## 💰 ЮНИТ-ЭКОНОМИКА
Для TOP-3 лучших продуктов рассчитай примерную структуру:
- Закупка (оценка)
- FBA fees (оценка)
- Ожидаемая прибыль на единицу

## ⚡ QUICK WINS
Какие 2-3 продукта можно запустить быстрее всего с минимальным риском?

Будь конкретным. Ссылайся на реальные продукты из списка. Честная оценка важнее оптимизма."""

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
