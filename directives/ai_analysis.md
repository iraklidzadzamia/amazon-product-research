# AI Product Analysis

## Goal
Use GPT-4o to evaluate product opportunities and provide actionable recommendations (BUY/MAYBE/SKIP).

## Inputs
- **Opportunities**: List of matched products with scores
- **Source Market**: Where we buy (JP/AliExpress)
- **Target Market**: Where we sell (US)

## Tools
- `execution/ai_analyzer.py` → `analyze_opportunities()`
- Uses **OpenAI GPT-4o**

## System Prompt Structure

### Critical Pricing Rules
```
- Source Price = What we BUY for (AliExpress $5)
- Market Leader Price = What we SELL for (Amazon $30)
- Markup = Selling Price / Source Price (6x = good)

✅ GOOD: Buy $5, Sell $30 = 6x markup
❌ BAD: Buy $25, Sell $30 = 1.2x markup (no profit after FBA fees)
```

### Decision Matrix
| Scenario | Decision |
|----------|----------|
| Markup 4x+, Reviews 100k+ | **BUY** |
| Markup 3-4x, Reviews 50k+ | **MAYBE** |
| Markup <3x | **SKIP** |
| Selling price <$20 | **SKIP** (FBA fees kill margin) |

## Output Format
```markdown
## 🎯 TOP-3 РЕКОМЕНДАЦИИ

### 1. [Product Name]
- **Решение**: 🟢 ПОКУПАТЬ
- **Закупка**: $5.50 | **Продажа**: $32.99
- **Маржа**: 6x (отлично)
- **Почему**: 500k продаж, рейтинг 4.8, niche product
```

## Chat Feature
After initial analysis, users can continue conversation:
- Ask about specific products
- Request detailed calculations
- Discuss strategy

**Context passed to GPT:**
- Product data (first 3000 chars)
- Previous analysis (first 2000 chars)
- Last 10 chat messages

## Key Learnings

### ⚠️ Response Language
Always respond in Russian (user preference).

### ⚠️ Hallucination Prevention
Include actual product data in prompt so AI references real products, not imagined ones.

### ⚠️ Chat Rerun
After AI responds in chat, call `st.rerun()` to properly display conversation history.
