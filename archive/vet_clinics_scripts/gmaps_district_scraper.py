#!/usr/bin/env python3
"""
Script: gmaps_district_scraper.py
Purpose: Search multiple districts for vet clinics and scrape websites in PARALLEL.
         Saves incrementally to prevent data loss.

Usage:
    python execution/gmaps_district_scraper.py

Target: ~600 clinics
"""

import json
import os
import re
import ssl
import time
import csv
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed

# Bypass SSL issues
ssl._create_default_https_context = ssl._create_unverified_context

# Load env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Manual fallback
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
if not API_KEY:
    # Try reading from directives/.env just in case
    env_path = Path('directives/.env')
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# Patterns
EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
INSTAGRAM_PATTERN = re.compile(r'(?:instagram\.com|instagr\.am)/([a-zA-Z0-9_.]+)')
FACEBOOK_PATTERN = re.compile(r'facebook\.com/([a-zA-Z0-9.]+)')

DISTRICTS = [
    'Manhattan, New York',
    'Brooklyn, New York', 
    'Queens, New York',
    'Bronx, New York',
    'Staten Island, New York',
    'Harlem, New York',
    'Upper East Side, New York',
    'Upper West Side, New York'
]

QUERIES = ['veterinary clinic', 'animal hospital', 'pet hospital']

OUTPUT_FILE = Path('.tmp/vet_clinics_all.json')
TSV_FILE = Path('.tmp/vet_clinics_all.tsv')

def fetch_json(url):
    try:
        req = Request(url, headers={'User-Agent': 'LeadFinder/1.0'})
        with urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"fetch_json error: {e}")
        return {}

def fetch_html(url):
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'})
        with urlopen(req, timeout=5) as response:  # 5s timeout for speed
            return response.read().decode('utf-8', errors='ignore')
    except:
        return ''

def scrape_website(url):
    result = {'email': '', 'instagram': '', 'facebook': ''}
    if not url: return result
    
    html = fetch_html(url)
    if not html: return result
    
    # Emails
    emails = EMAIL_PATTERN.findall(html)
    for email in emails:
        if not any(x in email.lower() for x in ['example', 'domain', 'sentry', '.png', '.jpg', 'wix']):
            result['email'] = email
            break
            
    # Instagram
    ig = INSTAGRAM_PATTERN.search(html)
    if ig and ig.group(1) not in ['p', 'reel', 'stories', 'explore']:
        result['instagram'] = f"@{ig.group(1)}"
        
    # Facebook
    fb = FACEBOOK_PATTERN.search(html)
    if fb and fb.group(1) not in ['sharer', 'share', 'plugins']:
        result['facebook'] = f"facebook.com/{fb.group(1)}"
        
    return result

def get_place_details(place_id):
    fields = 'name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,url'
    url = f'https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields={fields}&key={API_KEY}'
    data = fetch_json(url)
    if data.get('status') == 'OK':
        return data.get('result', {})
    return {}

def process_clinic(item):
    """Process a single clinic (thread worker function)."""
    pid = item['place']['place_id']
    district = item['district']
    
    details = get_place_details(pid)
    website = details.get('website', '')
    
    # Scrape website (slow part)
    socials = {'email': '', 'instagram': '', 'facebook': ''}
    if website:
        socials = scrape_website(website)
    
    return {
        'place_id': pid,
        'Название': details.get('name', item['place'].get('name')),
        'Район': district.split(',')[0],
        'Адрес': details.get('formatted_address', ''),
        'Телефон': details.get('formatted_phone_number', ''),
        'Сайт': website,
        'Email': socials['email'],
        'Instagram': socials['instagram'],
        'Facebook': socials['facebook'],
        'Рейтинг': details.get('rating', ''),
        'Отзывы': details.get('user_ratings_total', 0),
        'Google Maps': details.get('url', ''),
        'Статус': 'Новый'
    }

def save_data(results):
    """Save both JSON and TSV."""
    # JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    # TSV
    with open(TSV_FILE, 'w', encoding='utf-8') as f:
        headers = ['Название', 'Район', 'Адрес', 'Телефон', 'Сайт', 'Email', 'Instagram', 'Facebook', 'Рейтинг', 'Отзывы', 'Google Maps', 'Статус']
        f.write('\t'.join(headers) + '\n')
        for row in results:
            values = [str(row.get(h, '')) for h in headers]
            f.write('\t'.join(values) + '\n')

def main():
    if not API_KEY:
        print("❌ Error: GOOGLE_MAPS_API_KEY not found")
        return

    # Load existing
    existing_ids = set()
    processed_results = []
    
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, 'r') as f:
                processed_results = json.load(f)
                existing_ids = {r['place_id'] for r in processed_results}
            print(f"📋 Loaded {len(processed_results)} existing clinics")
        except:
            pass

    # Step 1: Search (Fast)
    print("\n🔎 Searching districts...")
    if API_KEY:
        print(f"   API Key loaded: {API_KEY[:5]}...")
    else:
        print("   ❌ API Key is NONE")

    all_raw_places = []
    
    for district in DISTRICTS:
        for query in QUERIES:
            params = {
                'query': f'{query} in {district}',
                'key': API_KEY
            }
            url = f'https://maps.googleapis.com/maps/api/place/textsearch/json?{urlencode(params)}'
            print(f"   Querying: {query} in {district}...")  # Debug
            data = fetch_json(url)
            
            if data.get('status') == 'OK':
                results = data.get('results', [])
                print(f"     Found {len(results)} results")
                for p in results:
                    all_raw_places.append({'place': p, 'district': district})
            
            time.sleep(0.2)
            
    # Deduplicate
    unique_to_process = []
    seen = set(existing_ids)
    
    for item in all_raw_places:
        pid = item['place']['place_id']
        if pid not in seen:
            seen.add(pid)
            unique_to_process.append(item)
            
    print(f"📊 Found {len(all_raw_places)} total places")
    print(f"🆕 New unique to process: {len(unique_to_process)}")
    
    if not unique_to_process:
        print("✅ No new clinics to process.")
        return

    # Step 2: Process in Parallel (Fast)
    print(f"\n🚀 Processing {len(unique_to_process)} clinics with 10 threads...")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_clinic = {executor.submit(process_clinic, item): item for item in unique_to_process}
        
        completed = 0
        for future in as_completed(future_to_clinic):
            try:
                data = future.result()
                processed_results.append(data)
                completed += 1
                
                # Show progress
                extras = []
                if data['Email']: extras.append('📧')
                if data['Instagram']: extras.append('📸')
                if data['Facebook']: extras.append('📘')
                
                print(f"[{completed}/{len(unique_to_process)}] {data['Название'][:30]}... {' '.join(extras)}")
                
                # Incremental Save every 5 items
                if completed % 5 == 0:
                    save_data(processed_results)
                    
            except Exception as e:
                print(f"Error: {e}")

    # Final Save
    save_data(processed_results)
    
    print("\n✅ Done!")
    print(f"Total clinics collection: {len(processed_results)}")
    
    # Stats
    with_email = sum(1 for r in processed_results if r.get('Email'))
    print(f"📧 Emails: {with_email}")
    print(f"📸 Instagrams: {sum(1 for r in processed_results if r.get('Instagram'))}")

if __name__ == "__main__":
    main()
