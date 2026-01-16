import os
import json
from typing import Optional, List, Dict
from firecrawl import FirecrawlApp
from dotenv import load_dotenv

load_dotenv()

class UniversalAdapter:
    def __init__(self):
        self.api_key = os.getenv("FIRECRAWL_API_KEY")
        if not self.api_key:
            raise ValueError("FIRECRAWL_API_KEY not found in .env")
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
        
        print(f"🤖 Universal Agent launching on: {url}")
        print(f"   Objective: {prompt}")

        try:
            # Use scrape with markdown format - most reliable for parsing
            data = self.app.scrape_url(
                url,
                params={
                    "formats": ["markdown"],
                    "waitFor": 3000,  # Wait for JS to load
                }
            )
            
            markdown_content = data.get("markdown", "")
            print(f"DEBUG: Got {len(markdown_content)} chars of markdown")
            
            if not markdown_content:
                print("❌ No markdown content returned")
                return []
            
            # Parse products from markdown
            # Pattern matches: [![](image_url)\n\nPRICE](product_url)
            # AliExpress format: [![](https://ae04.alicdn.com/kf/xxx.jpg)\n\n179 ₽527 ₽](https://aliexpress.ru/item/xxx.html)
            
            product_pattern = r'\[!\[\]\((https://ae\d+\.alicdn\.com/[^)]+)\)[^\]]*\]\((https://aliexpress\.ru/item/[^)]+)\)'
            price_pattern = r'(\d[\d\s]*)\s*₽'
            
            matches = re.findall(product_pattern, markdown_content)
            print(f"DEBUG: Found {len(matches)} product matches")
            
            normalized_products = []
            for i, (image_url, product_url) in enumerate(matches[:limit]):
                # Extract price from nearby context
                # Find the markdown section around this product
                idx = markdown_content.find(product_url)
                context = markdown_content[max(0, idx-200):idx+100]
                price_match = re.search(price_pattern, context)
                price = float(price_match.group(1).replace(' ', '')) if price_match else 0
                
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
            print(f"❌ Firecrawl Error: {e}")
            return []

if __name__ == "__main__":
    # Test stub
    adapter = UniversalAdapter()
    # print(adapter.scrape_products("https://www.kickstarter.com/discover/popular", "Find top tech projects"))
