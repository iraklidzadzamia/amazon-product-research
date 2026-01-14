#!/usr/bin/env python3
"""
Script: gmaps_lead_scraper.py
Purpose: Find vet clinics via Google Maps and scrape their websites for contact info

Usage:
    python execution/gmaps_lead_scraper.py --city "New York" --max-results 600

Related Directive: directives/find_vet_clinics.md
"""

import argparse
import json
import os
import re
import ssl
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import urlencode, quote
from urllib.error import URLError, HTTPError

# Bypass SSL issues on Mac
ssl._create_default_https_context = ssl._create_unverified_context

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed, reading from environment directly")

# Configuration
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Patterns for scraping
EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
INSTAGRAM_PATTERN = re.compile(r'(?:instagram\.com|instagr\.am)/([a-zA-Z0-9_.]+)')
FACEBOOK_PATTERN = re.compile(r'facebook\.com/([a-zA-Z0-9.]+)')


def fetch_json(url: str) -> dict:
    """Fetch JSON from URL."""
    try:
        req = Request(url, headers={"User-Agent": "LeadFinder/1.0"})
        with urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"  API Error: {e}")
        return {}


def fetch_html(url: str) -> str:
    """Fetch HTML from website."""
    try:
        # Add https if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
        with urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return ""


def search_places(query: str, location: str, api_key: str, max_results: int = 60) -> list:
    """
    Search Google Maps for places.
    
    Uses Text Search API which returns up to 60 results per query.
    """
    all_places = []
    next_page_token = None
    
    while len(all_places) < max_results:
        params = {
            "query": f"{query} in {location}",
            "key": api_key
        }
        
        if next_page_token:
            params["pagetoken"] = next_page_token
            time.sleep(2)  # Required delay for page token
        
        url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?{urlencode(params)}"
        
        data = fetch_json(url)
        
        if data.get("status") != "OK":
            error = data.get("error_message", data.get("status", "Unknown error"))
            print(f"  Search error: {error}")
            break
        
        results = data.get("results", [])
        all_places.extend(results)
        
        print(f"  Found {len(results)} places (total: {len(all_places)})")
        
        next_page_token = data.get("next_page_token")
        if not next_page_token:
            break
    
    return all_places[:max_results]


def get_place_details(place_id: str, api_key: str) -> dict:
    """Get detailed info for a place."""
    fields = "name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,opening_hours,url"
    
    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields={fields}&key={api_key}"
    
    data = fetch_json(url)
    
    if data.get("status") == "OK":
        return data.get("result", {})
    return {}


def scrape_website(url: str) -> dict:
    """Scrape website for email and social links."""
    result = {
        "email": "",
        "instagram": "",
        "facebook": ""
    }
    
    if not url:
        return result
    
    html = fetch_html(url)
    if not html:
        return result
    
    # Find emails (exclude common false positives)
    emails = EMAIL_PATTERN.findall(html)
    for email in emails:
        if not any(x in email.lower() for x in ['example', 'domain', 'email', '.png', '.jpg', '.gif', 'wix', 'wordpress']):
            result["email"] = email
            break
    
    # Find Instagram
    ig_matches = INSTAGRAM_PATTERN.findall(html)
    for ig in ig_matches:
        if ig not in ['p', 'reel', 'stories', 'explore', 'accounts']:
            result["instagram"] = f"@{ig}"
            break
    
    # Find Facebook
    fb_matches = FACEBOOK_PATTERN.findall(html)
    for fb in fb_matches:
        if fb not in ['sharer', 'share', 'plugins', 'dialog']:
            result["facebook"] = f"facebook.com/{fb}"
            break
    
    return result


def process_clinic(place: dict, api_key: str, scrape_sites: bool = True) -> dict:
    """Process a single clinic - get details and scrape website."""
    place_id = place.get("place_id")
    
    # Get detailed info
    details = get_place_details(place_id, api_key)
    
    website = details.get("website", "")
    
    # Scrape website for socials
    socials = {"email": "", "instagram": "", "facebook": ""}
    if scrape_sites and website:
        socials = scrape_website(website)
    
    # Build hours string
    hours = ""
    if details.get("opening_hours", {}).get("weekday_text"):
        hours = " | ".join(details["opening_hours"]["weekday_text"][:3]) + "..."
    
    return {
        "place_id": place_id,
        "Название": details.get("name", place.get("name", "")),
        "Адрес": details.get("formatted_address", ""),
        "Телефон": details.get("formatted_phone_number", ""),
        "Сайт": website,
        "Email": socials["email"],
        "Instagram": socials["instagram"],
        "Facebook": socials["facebook"],
        "Рейтинг": details.get("rating", ""),
        "Отзывы": details.get("user_ratings_total", 0),
        "Часы": hours,
        "Google Maps": details.get("url", ""),
        "Статус": "Новый"
    }


def load_existing(filepath: Path) -> set:
    """Load existing place_ids to avoid duplicates."""
    if not filepath.exists():
        return set()
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {item.get("place_id") for item in data if item.get("place_id")}
    except:
        return set()


def save_results(results: list, filepath: Path):
    """Save results to JSON and CSV."""
    # Save JSON
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Save CSV
    csv_path = filepath.with_suffix(".csv")
    import csv
    
    if results:
        # Exclude place_id from CSV
        fieldnames = [k for k in results[0].keys() if k != "place_id"]
        
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(results)
    
    print(f"  Saved: {filepath}")
    print(f"  Saved: {csv_path}")


def main():
    parser = argparse.ArgumentParser(description="Find vet clinics via Google Maps")
    parser.add_argument(
        "--city",
        type=str,
        default="New York",
        help="City to search in"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="veterinary clinic",
        help="Search query"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=60,
        help="Maximum results to collect"
    )
    parser.add_argument(
        "--no-scrape",
        action="store_true",
        help="Skip website scraping"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=".tmp/vet_clinics.json",
        help="Output file path"
    )
    args = parser.parse_args()
    
    # Check API key
    if not GOOGLE_MAPS_API_KEY:
        print("❌ Error: GOOGLE_MAPS_API_KEY not found in .env")
        print("   Add it to .env file in project root")
        return
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"🔍 Google Maps Lead Scraper")
    print(f"   Query: {args.query}")
    print(f"   City: {args.city}")
    print(f"   Max results: {args.max_results}")
    print(f"   Scrape websites: {not args.no_scrape}")
    print()
    
    # Load existing to avoid duplicates
    existing_ids = load_existing(output_path)
    if existing_ids:
        print(f"📋 Found {len(existing_ids)} existing entries (will skip duplicates)")
    
    # Search for places
    print(f"\n🔎 Searching Google Maps...")
    places = search_places(args.query, args.city, GOOGLE_MAPS_API_KEY, args.max_results)
    
    if not places:
        print("❌ No places found")
        return
    
    # Filter out duplicates
    new_places = [p for p in places if p.get("place_id") not in existing_ids]
    print(f"\n📊 Found {len(places)} places, {len(new_places)} new")
    
    # Process each place
    results = []
    
    # Load existing results to merge
    if output_path.exists():
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                results = json.load(f)
        except:
            pass
    
    print(f"\n⏳ Processing {len(new_places)} clinics...")
    
    for i, place in enumerate(new_places, 1):
        name = place.get("name", "Unknown")[:40]
        print(f"[{i}/{len(new_places)}] {name}...")
        
        try:
            clinic = process_clinic(place, GOOGLE_MAPS_API_KEY, not args.no_scrape)
            results.append(clinic)
            
            # Show what we found
            extras = []
            if clinic.get("Email"):
                extras.append(f"📧")
            if clinic.get("Instagram"):
                extras.append(f"📸")
            if clinic.get("Facebook"):
                extras.append(f"📘")
            if extras:
                print(f"         Found: {' '.join(extras)}")
            
        except Exception as e:
            print(f"         Error: {e}")
        
        # Small delay to be nice to APIs
        time.sleep(0.5)
    
    # Save results
    save_results(results, output_path)
    
    # Summary
    print(f"\n✅ Done!")
    print(f"   Total clinics: {len(results)}")
    
    with_email = sum(1 for r in results if r.get("Email"))
    with_ig = sum(1 for r in results if r.get("Instagram"))
    with_fb = sum(1 for r in results if r.get("Facebook"))
    
    print(f"   With email: {with_email}")
    print(f"   With Instagram: {with_ig}")
    print(f"   With Facebook: {with_fb}")


if __name__ == "__main__":
    main()
