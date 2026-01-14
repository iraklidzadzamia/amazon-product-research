#!/usr/bin/env python3
"""
Meta Ad Library API Integration
Collects competitor vet clinic ads from Georgia for analysis
"""

import os
import json
import csv
import time
import ssl
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# SSL context to handle certificate verification
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Configuration
API_VERSION = "v24.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"
ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")

# Search keywords for Georgian vet clinics
KEYWORDS = [
    "ვეტერინარია",      # veterinary (Georgian)
    "ვეტკლინიკა",       # vet clinic (Georgian)
    "ვეტერინარი",       # veterinarian (Georgian)
    "ветеринар",        # veterinarian (Russian)
    "ветклиника",       # vet clinic (Russian)
    "vet clinic",       # English
]

# API fields to request
AD_FIELDS = [
    "id",
    "ad_creative_bodies",
    "ad_creative_link_captions",
    "ad_creative_link_titles",
    "ad_delivery_start_time",
    "ad_delivery_stop_time",
    "ad_snapshot_url",
    "funding_entity",
    "page_name",
    "impressions",
    "spend",
    "currency",
]


class MetaAdLibrary:
    """Interface to Meta Ad Library API"""
    
    def __init__(self, access_token: str):
        if not access_token:
            raise ValueError("META_ACCESS_TOKEN not found in environment variables")
        self.access_token = access_token
        self.ads_collected = []
    
    def search_ads(
        self,
        search_term: str,
        country: str = "GE",  # Georgia
        ad_active_status: str = "ALL",
        limit: int = 100
    ) -> List[Dict]:
        """
        Search for ads in Meta Ad Library
        
        Args:
            search_term: Keyword to search for
            country: Two-letter country code (GE for Georgia)
            ad_active_status: ALL, ACTIVE, or INACTIVE
            limit: Max results per request (max 100)
        
        Returns:
            List of ad dictionaries
        """
        endpoint = f"{BASE_URL}/ads_archive"
        
        params = {
            "access_token": self.access_token,
            "search_terms": search_term,
            "ad_reached_countries": country,
            "ad_active_status": ad_active_status,
            "limit": limit,
            "fields": ",".join(AD_FIELDS),
        }
        
        url = f"{endpoint}?{urllib.parse.urlencode(params)}"
        
        try:
            print(f"Searching for: '{search_term}' in {country}...")
            
            with urllib.request.urlopen(url, context=ssl_context) as response:
                data = json.loads(response.read().decode())
                
                ads = data.get("data", [])
                print(f"  Found {len(ads)} ads")
                
                return ads
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            print(f"  ERROR: {e.code} - {error_body}")
            return []
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            return []
    
    def collect_all_keywords(self, keywords: List[str]) -> List[Dict]:
        """
        Search for all keywords and collect unique ads
        
        Args:
            keywords: List of search terms
        
        Returns:
            List of unique ads
        """
        all_ads = []
        seen_ids = set()
        
        for keyword in keywords:
            ads = self.search_ads(keyword)
            
            # Deduplicate by ad ID
            for ad in ads:
                ad_id = ad.get("id")
                if ad_id and ad_id not in seen_ids:
                    seen_ids.add(ad_id)
                    all_ads.append(ad)
            
            # Rate limiting - be nice to the API
            time.sleep(1)
        
        print(f"\nTotal unique ads collected: {len(all_ads)}")
        return all_ads
    
    def extract_ad_data(self, ad: Dict) -> Dict:
        """
        Extract and normalize ad data for analysis
        
        Args:
            ad: Raw ad data from API
        
        Returns:
            Normalized ad dictionary
        """
        # Extract text content
        bodies = ad.get("ad_creative_bodies", [])
        captions = ad.get("ad_creative_link_captions", [])
        titles = ad.get("ad_creative_link_titles", [])
        
        ad_text = " | ".join(bodies) if bodies else ""
        ad_caption = " | ".join(captions) if captions else ""
        ad_title = " | ".join(titles) if titles else ""
        
        # Extract dates
        start_time = ad.get("ad_delivery_start_time", "")
        stop_time = ad.get("ad_delivery_stop_time", "")
        
        # Calculate days running
        days_running = 0
        if start_time:
            try:
                start_date = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                if stop_time:
                    stop_date = datetime.fromisoformat(stop_time.replace("Z", "+00:00"))
                else:
                    stop_date = datetime.now()
                days_running = (stop_date - start_date).days
            except:
                pass
        
        # Extract impressions/spend
        impressions = ad.get("impressions", {})
        spend = ad.get("spend", {})
        
        impressions_min = impressions.get("lower_bound", "") if isinstance(impressions, dict) else ""
        impressions_max = impressions.get("upper_bound", "") if isinstance(impressions, dict) else ""
        
        spend_min = spend.get("lower_bound", "") if isinstance(spend, dict) else ""
        spend_max = spend.get("upper_bound", "") if isinstance(spend, dict) else ""
        
        return {
            "ad_id": ad.get("id", ""),
            "advertiser": ad.get("funding_entity", ad.get("page_name", "Unknown")),
            "page_name": ad.get("page_name", ""),
            "ad_text": ad_text,
            "ad_caption": ad_caption,
            "ad_title": ad_title,
            "start_date": start_time,
            "stop_date": stop_time,
            "days_running": days_running,
            "is_active": "Yes" if not stop_time else "No",
            "impressions_min": impressions_min,
            "impressions_max": impressions_max,
            "spend_min": spend_min,
            "spend_max": spend_max,
            "currency": ad.get("currency", ""),
            "ad_snapshot_url": ad.get("ad_snapshot_url", ""),
        }
    
    def save_to_tsv(self, ads: List[Dict], output_path: str):
        """
        Save ads to TSV file
        
        Args:
            ads: List of normalized ad dictionaries
            output_path: Path to output TSV file
        """
        if not ads:
            print("No ads to save")
            return
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Extract and normalize all ads
        normalized_ads = [self.extract_ad_data(ad) for ad in ads]
        
        # Write to TSV
        fieldnames = normalized_ads[0].keys()
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
            writer.writeheader()
            writer.writerows(normalized_ads)
        
        print(f"\nSaved {len(normalized_ads)} ads to: {output_path}")
    
    def test_connection(self) -> bool:
        """
        Test API connection with a simple query
        
        Returns:
            True if connection successful
        """
        print("Testing Meta Ad Library API connection...")
        
        try:
            ads = self.search_ads("test", limit=1)
            print("✅ Connection successful!")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {str(e)}")
            return False


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Meta Ad Library API - Vet Clinic Competitor Analysis")
    parser.add_argument("--test", action="store_true", help="Test API connection")
    parser.add_argument("--keyword", type=str, help="Search for specific keyword")
    parser.add_argument("--limit", type=int, default=100, help="Max results per keyword")
    parser.add_argument("--all-keywords", action="store_true", help="Search all predefined keywords")
    parser.add_argument("--output", type=str, default=".tmp/vet_ads_georgia.tsv", help="Output file path")
    
    args = parser.parse_args()
    
    # Initialize API client
    api = MetaAdLibrary(ACCESS_TOKEN)
    
    # Test mode
    if args.test:
        api.test_connection()
        return
    
    # Single keyword search
    if args.keyword:
        ads = api.search_ads(args.keyword, limit=args.limit)
        api.save_to_tsv(ads, args.output)
        return
    
    # All keywords search (default)
    if args.all_keywords or (not args.keyword and not args.test):
        print("=" * 60)
        print("Meta Ad Library - Georgian Vet Clinic Competitor Analysis")
        print("=" * 60)
        print(f"\nSearching {len(KEYWORDS)} keywords...")
        print(f"Keywords: {', '.join(KEYWORDS)}\n")
        
        ads = api.collect_all_keywords(KEYWORDS)
        api.save_to_tsv(ads, args.output)
        
        print("\n" + "=" * 60)
        print("Collection complete!")
        print("=" * 60)


if __name__ == "__main__":
    main()
