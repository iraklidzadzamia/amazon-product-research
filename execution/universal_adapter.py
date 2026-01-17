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
            # Use scrape with markdown format + scroll actions
            # We need to scroll past the "Peak Sales" promo section to get real bestsellers
            # The real bestsellers (with 100k+ sales) are below the promo carousel
            data = self.app.scrape(
                url,
                formats=["markdown"],
                wait_for=3000,  # Wait for JS to load
                actions=[
                    {"type": "wait", "milliseconds": 2000},  # Wait for page load
                    {"type": "scroll", "direction": "down"},  # Scroll to load more content
                    {"type": "wait", "milliseconds": 1000},
                    {"type": "scroll", "direction": "down"},  # Scroll again
                    {"type": "wait", "milliseconds": 1000},
                    {"type": "scroll", "direction": "down"},  # Scroll more to get bestsellers
                    {"type": "wait", "milliseconds": 1000},
                    {"type": "scrape"}  # Now scrape the full page
                ]
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
            # AliExpress format in markdown:
            # [![](image.jpg)\n\n462 ₽480 ₽\n\nМерный стакан G3.3 боросиликатное стекло 50 мл](https://aliexpress.ru/item/...)
            # We need to extract: image_url, price, product_name, product_url
            
            # Pattern to match the full product block including name
            # Format: [![](IMAGE)\n\nPRICE\n\nNAME](URL)
            full_pattern = r'\[!\[\]\((https://ae\d+\.alicdn\.com/[^)]+)\)[^\]]*?(\d[\d\s\xa0]*)\s*₽[^\]]*?([^\]₽\n][^\]]{10,}?)\]\((https://aliexpress\.ru/item/[^)]+)\)'
            
            matches = re.findall(full_pattern, markdown_content, re.DOTALL)
            
            # Fallback: simpler pattern if full pattern doesn't work
            if len(matches) < 3:
                # Try alternative parsing method
                simple_pattern = r'\[!\[\]\((https://ae\d+\.alicdn\.com/[^)]+)\)[^\]]*\]\((https://aliexpress\.ru/item/[^)]+)\)'
                simple_matches = re.findall(simple_pattern, markdown_content)
                
                # Extract names from context for simple matches
                matches = []
                for image_url, product_url in simple_matches:
                    idx = markdown_content.find(product_url)
                    # Get context before the URL to find name
                    context = markdown_content[max(0, idx-300):idx]
                    
                    # Find price
                    price_pattern = r'(\d[\d\s\xa0]*)\s*₽'
                    price_match = re.search(price_pattern, context)
                    price_str = price_match.group(1) if price_match else "0"
                    
                    # Find name - text after last price, before the closing bracket
                    # Name is usually the last text block before ](url)
                    name_pattern = r'[\n\\]+([^\n\[\]₽]{10,}?)\s*$'
                    name_match = re.search(name_pattern, context)
                    name = name_match.group(1).strip() if name_match else ""
                    
                    # Clean up name
                    name = re.sub(r'^[\s\\n]+', '', name)
                    name = re.sub(r'[\s\\n]+$', '', name)
                    
                    matches.append((image_url, price_str, name, product_url))
            
            st.info(f"🔍 Regex found {len(matches)} product matches")
            
            normalized_products = []
            for i, match in enumerate(matches[:limit]):
                if len(match) == 4:
                    image_url, price_str, product_name, product_url = match
                else:
                    # Fallback for 2-element matches
                    image_url, product_url = match[0], match[1]
                    price_str = "0"
                    product_name = ""
                
                # Clean price string
                price_str = str(price_str).replace(' ', '').replace('\xa0', '')
                try:
                    price = float(price_str) if price_str else 0
                except:
                    price = 0
                
                # Convert RUB to USD (approximate)
                price_usd = round(price / 90, 2)  # 1 USD ≈ 90 RUB
                
                # Clean product name
                product_name = product_name.strip() if product_name else f"AliExpress Product #{i+1}"
                product_name = re.sub(r'\\n|\\t|\s+', ' ', product_name).strip()
                if len(product_name) < 5:
                    product_name = f"AliExpress Product #{i+1}"
                
                # Try to extract sales count from context around the product URL
                idx = markdown_content.find(product_url) if product_url else -1
                sales_count = 0
                if idx > 0:
                    sales_context = markdown_content[max(0, idx-500):idx+200]
                    # Pattern for "566 627 sold" or "566627 sold" or "продано"
                    sales_patterns = [
                        r'(\d[\d\s\xa0]*)\s*sold',  # English: "566 627 sold"
                        r'(\d[\d\s\xa0]*)\s*продано',  # Russian: "566 627 продано"
                        r'\*\s*(\d[\d\s\xa0]+)\s*\*',  # ** 566 627 **
                    ]
                    for sp in sales_patterns:
                        sales_match = re.search(sp, sales_context, re.IGNORECASE)
                        if sales_match:
                            sales_str = sales_match.group(1).replace(' ', '').replace('\xa0', '')
                            try:
                                sales_count = int(sales_str)
                                break
                            except:
                                pass
                
                norm = {
                    "asin": f"fc_{i+1}_{abs(hash(product_url)) % 100000}",
                    "name": product_name[:100],  # Limit name length
                    "price": {
                        "value": price_usd,
                        "currency": "$"
                    },
                    "sem_price": price_usd,
                    "sem_currency": "$",
                    "stars": 4.5,  # Default
                    "reviewsCount": sales_count if sales_count > 0 else 1000,  # Use real sales or default
                    "salesCount": sales_count,  # Store actual sales count
                    "url": product_url,
                    "thumbnailUrl": image_url,
                    "is_universal": True,
                    "original_price_rub": price
                }
                normalized_products.append(norm)
            
            # Debug: show first product name
            if normalized_products:
                st.info(f"📝 First product name: {normalized_products[0].get('name', 'N/A')[:50]}...")
            
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
