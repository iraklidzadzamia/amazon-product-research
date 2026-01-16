import os
import json
from typing import Optional, List, Dict
from firecrawl import FirecrawlApp
from dotenv import load_dotenv

load_dotenv()

class UniversalAdapter:
    def __init__(self):
        import streamlit as st
        # Try st.secrets first (Streamlit Cloud), then fallback to os.getenv (local)
        self.api_key = None
        self.api_key_source = None
        
        try:
            # st.secrets uses bracket notation, not .get()
            if "FIRECRAWL_API_KEY" in st.secrets:
                self.api_key = st.secrets["FIRECRAWL_API_KEY"]
                self.api_key_source = "st.secrets"
                st.info(f"🔑 API key loaded from: st.secrets (len={len(self.api_key)})")
        except Exception as e:
            st.warning(f"⚠️ Could not load from st.secrets: {e}")
        
        # Fallback to os.getenv for local development
        if not self.api_key:
            self.api_key = os.getenv("FIRECRAWL_API_KEY")
            if self.api_key:
                self.api_key_source = "os.getenv"
                st.info(f"🔑 API key loaded from: os.getenv (len={len(self.api_key)})")
        
        if not self.api_key:
            st.error("❌ FIRECRAWL_API_KEY not found in secrets or .env!")
            raise ValueError("FIRECRAWL_API_KEY not found in secrets or .env")
        
        self.app = FirecrawlApp(api_key=self.api_key)

    def get_category_url(self, category_id: str) -> str:
        """Map internal category ID to AliExpress Category URL (sorted by orders)."""
        # Updated 2026-01-16 09:53 - Using actual category pages from aliexpress.ru
        # Base URLs without session tokens - these are stable
        ALIEXPRESS_CATEGORY_MAP = {
            "home-garden": "https://aliexpress.ru/category/6/home-garden-office?SortType=total_tranpro_desc",
            "pet-supplies": "https://aliexpress.ru/category/858/pet-products?SortType=total_tranpro_desc",
            "office-products": "https://aliexpress.ru/category/16029/home-improvement-tools?SortType=total_tranpro_desc",
            "sports-outdoors": "https://aliexpress.ru/category/7/sports-entertainment?SortType=total_tranpro_desc",
            "toys-games": "https://aliexpress.ru/category/9/toys-hobbies?SortType=total_tranpro_desc",
            "adult": "https://aliexpress.ru/category/16002/adult-products?SortType=total_tranpro_desc"
        }
        # SortType=total_tranpro_desc = Sort by Orders (best sellers first)
        return ALIEXPRESS_CATEGORY_MAP.get(category_id, "https://aliexpress.ru/category/6/home-garden-office?SortType=total_tranpro_desc")


    def scrape_products(self, url: str, prompt: str, limit: int = 20) -> List[Dict]:
        """
        Scrapes products from AliExpress using markdown format and regex parsing.
        """
        import re
        import streamlit as st
        
        st.info(f"🤖 Calling Firecrawl scrape on: {url}")

        try:
            # Use scrape with markdown format - most reliable for parsing
            # Note: Pass options directly, not in params dict
            data = self.app.scrape(
                url,
                formats=["markdown"],
                wait_for=3000  # Wait for JS to load
            )
            
            # Firecrawl v2 returns a Document object (Pydantic model), not a dict
            # Access markdown via attribute, with fallback for dict compatibility
            if hasattr(data, 'markdown'):
                markdown_content = data.markdown or ""
            else:
                markdown_content = data.get("markdown", "") if isinstance(data, dict) else ""
            
            st.success(f"✅ Firecrawl responded! Markdown length: {len(markdown_content)} chars")
            
            # Show preview of markdown for debugging
            if markdown_content:
                st.info("📄 Markdown preview (first 1000 chars):")
                st.code(markdown_content[:1000], language="markdown")
            else:
                st.warning("⚠️ No markdown content in response!")
                st.text(str(data))  # Show raw response (works for both dict and Pydantic)
                return []
            
            # Parse products from markdown
            # Pattern matches: [![](image_url)\n\nPRICE](product_url)
            # AliExpress format: [![](https://ae04.alicdn.com/kf/xxx.jpg)\n\n179 ₽527 ₽](https://aliexpress.ru/item/xxx.html)
            
            product_pattern = r'\[!\[\]\((https://ae\d+\.alicdn\.com/[^)]+)\)[^\]]*\]\((https://aliexpress\.ru/item/[^)]+)\)'
            price_pattern = r'(\d[\d\s]*)\s*₽'
            
            matches = re.findall(product_pattern, markdown_content)
            st.info(f"🔍 Regex found {len(matches)} product matches")
            
            normalized_products = []
            for i, (image_url, product_url) in enumerate(matches[:limit]):
                # Extract price from nearby context
                # Find the markdown section around this product
                idx = markdown_content.find(product_url)
                context = markdown_content[max(0, idx-200):idx+100]
                price_match = re.search(price_pattern, context)
                # Russian prices use non-breaking space (\xa0) as thousand separator
                price_str = price_match.group(1).replace(' ', '').replace('\xa0', '') if price_match else "0"
                price = float(price_str) if price_str else 0
                
                # Convert RUB to USD (approximate)
                price_usd = round(price / 90, 2)  # 1 USD ≈ 90 RUB
                
                norm = {
                    "asin": f"fc_{i+1}_{abs(hash(product_url)) % 100000}",
                    "name": f"AliExpress Product #{i+1}",  # We'll improve this later
                    "price": {
                        "value": price_usd,
                        "currency": "$"
                    },
                    "sem_price": price_usd,
                    "sem_currency": "$",
                    "stars": 4.5,  # Default
                    "reviewsCount": 1000,  # Default for bestsellers
                    "url": product_url,
                    "thumbnailUrl": image_url,
                    "is_universal": True,
                    "original_price_rub": price
                }
                normalized_products.append(norm)
            
            print(f"✅ Extracted {len(normalized_products)} products")
            return normalized_products

        except Exception as e:
            import traceback
            st.error(f"❌ Firecrawl Exception: {type(e).__name__}: {e}")
            st.code(traceback.format_exc(), language="python")
            return []

if __name__ == "__main__":
    # Test stub
    adapter = UniversalAdapter()
    # print(adapter.scrape_products("https://www.kickstarter.com/discover/popular", "Find top tech projects"))
