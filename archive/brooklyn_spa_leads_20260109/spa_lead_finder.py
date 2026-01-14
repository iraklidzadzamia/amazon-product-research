#!/usr/bin/env python3
"""
Brooklyn Spa/Salon Lead Finder
Purpose: Find spa/salon businesses within 10 miles of Brooklyn ZIP 11204
         Analyze websites for team/junior-friendly signals
         Export to Google Sheets-ready TSV

Features:
- Grid-based search for full coverage
- Places API (New) with proper FieldMask
- Website crawling for contacts + signals
- Incremental saving (resume capability)
- Priority scoring + outreach buckets

Usage:
    python3 execution/spa_lead_finder.py [--test-mode] [--max-places N]
"""

import json
import csv
import re
import os
import ssl
import time
import math
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import urlencode, quote_plus
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# SSL bypass
ssl._create_default_https_context = ssl._create_unverified_context

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    'center_zip': '11204',
    'radius_miles': 10,
    'max_places': 600,
    'min_reviews_soft': 10,
    'grid_step_miles': 4.5,
    'crawl_timeout_sec': 10,
    'crawl_max_pages': 4,
    'crawl_delay_sec': 0.8,
    'save_frequency': 10,  # Save progress every N places
    'backup_frequency': 50,  # Backup every N places
}

QUERIES = [
    "medical spa",
    "day spa",
    "beauty salon",
    "skin care clinic",
    "laser hair removal",
    "waxing",
    "esthetician"
]

# Load environment
def load_env():
    """Load .env file manually"""
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

load_env()
API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# Output paths
PROGRESS_FILE = Path('.tmp/spa_leads_progress.tsv')
FINAL_FILE = Path('.tmp/spa_leads_final.tsv')
BACKUP_DIR = Path('.tmp/backups')
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# REGEX PATTERNS
# ============================================================================

EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
PHONE_PATTERN = re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
INSTAGRAM_PATTERN = re.compile(r'(?:instagram\.com|instagr\.am)/([a-zA-Z0-9_.]+)/?')
FACEBOOK_PATTERN = re.compile(r'facebook\.com/([a-zA-Z0-9.]+)/?')

# Signal patterns
TEAM_SIGNALS = [
    r'meet\s+(?:our|the)\s+team',
    r'our\s+(?:staff|estheticians|specialists|providers)',
    r'join\s+our\s+team',
    r'/team',
    r'/staff',
    r'careers',
    r'we\'?re\s+hiring',
]

SOLO_SIGNALS = [
    r'about\s+me',
    r'I\s+am',
    r'my\s+studio',
    r'owner[- ]operator',
    r'sole\s+proprietor',
    r'independent',
]

JUNIOR_SIGNALS_STRONG = [
    r'training\s+provided',
    r'mentorship\s+program',
    r'new\s+graduates?\s+welcome',
    r'no\s+experience\s+(?:required|necessary)',
    r'we\s+train',
    r'entry\s+level',
    r'internship',
    r'apprenticeship',
    r'academy',
]

JUNIOR_SIGNALS_MODERATE = [
    r'growing\s+team',
    r'expanding',
    r'career\s+development',
    r'supportive\s+environment',
    r'learn\s+and\s+grow',
]

# ============================================================================
# UTILITIES
# ============================================================================

def fetch_json(url: str, headers: Dict = None) -> Dict:
    """Fetch JSON from URL"""
    try:
        req = Request(url, headers=headers or {'User-Agent': 'SpaLeadFinder/1.0'})
        with urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"  ⚠️  fetch_json error: {e}")
        return {}

def fetch_html(url: str) -> str:
    """Fetch HTML from URL"""
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'})
        with urlopen(req, timeout=CONFIG['crawl_timeout_sec']) as response:
            return response.read().decode('utf-8', errors='ignore')
    except:
        return ''

def miles_to_meters(miles: float) -> float:
    """Convert miles to meters"""
    return miles * 1609.34

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in miles between two points"""
    R = 3959  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon/2)**2)
    c = 2 * math.asin(math.sqrt(a))
    return R * c

# ============================================================================
# STEP 1: GEOCODING
# ============================================================================

def geocode_zip(zipcode: str) -> Optional[Tuple[float, float]]:
    """Convert ZIP to lat/lng"""
    print(f"\n🗺️  Geocoding ZIP {zipcode}...")
    params = {
        'address': zipcode,
        'components': 'country:US',  # Ensure US ZIP codes
        'key': API_KEY
    }
    url = f'https://maps.googleapis.com/maps/api/geocode/json?{urlencode(params)}'
    
    data = fetch_json(url)
    if data.get('status') == 'OK' and data.get('results'):
        location = data['results'][0]['geometry']['location']
        lat, lng = location['lat'], location['lng']
        address = data['results'][0].get('formatted_address', '')
        print(f"   ✅ Center: {lat:.4f}, {lng:.4f}")
        print(f"   📍 Location: {address}")
        return (lat, lng)
    
    print(f"   ❌ Geocoding failed: {data.get('status')}")
    return None

# ============================================================================
# STEP 2: GRID GENERATION
# ============================================================================

def generate_search_grid(center: Tuple[float, float], radius_miles: float, step_miles: float) -> List[Tuple[float, float]]:
    """Generate grid of search centers"""
    print(f"\n🔲 Generating search grid (radius={radius_miles}mi, step={step_miles}mi)...")
    
    centers = [center]  # Start with main center
    lat_center, lng_center = center
    
    # Convert miles to degrees (approximate)
    lat_per_mile = 1 / 69.0
    lng_per_mile = 1 / (69.0 * math.cos(math.radians(lat_center)))
    
    lat_step = step_miles * lat_per_mile
    lng_step = step_miles * lng_per_mile
    
    # Generate offsets in all directions
    max_offset = int(radius_miles / step_miles) + 1
    
    for lat_mult in range(-max_offset, max_offset + 1):
        for lng_mult in range(-max_offset, max_offset + 1):
            if lat_mult == 0 and lng_mult == 0:
                continue  # Skip center (already added)
            
            lat = lat_center + (lat_mult * lat_step)
            lng = lng_center + (lng_mult * lng_step)
            
            # Check if within radius
            dist = haversine_distance(lat_center, lng_center, lat, lng)
            if dist <= radius_miles:
                centers.append((lat, lng))
    
    print(f"   ✅ Generated {len(centers)} search centers")
    return centers

# ============================================================================
# STEP 3: PLACES DISCOVERY
# ============================================================================

def search_places(grid_centers: List[Tuple[float, float]], queries: List[str], max_places: int) -> Dict[str, Dict]:
    """Search Places API for all grid centers and queries"""
    print(f"\n🔍 Searching Places API...")
    print(f"   Grid centers: {len(grid_centers)}")
    print(f"   Queries: {len(queries)}")
    print(f"   Max places: {max_places}")
    
    all_places = {}  # place_id -> place_data
    
    for i, (lat, lng) in enumerate(grid_centers):
        for query in queries:
            if len(all_places) >= max_places:
                print(f"   🛑 Reached max places limit ({max_places})")
                return all_places
            
            # Text Search API (legacy but stable)
            params = {
                'query': f'{query} near {lat},{lng}',
                'location': f'{lat},{lng}',
                'radius': int(miles_to_meters(CONFIG["grid_step_miles"] * 0.7)),
                'key': API_KEY
            }
            
            url = f'https://maps.googleapis.com/maps/api/place/textsearch/json?{urlencode(params)}'
            
            try:
                data = fetch_json(url)
                
                if data.get('status') == 'OK' and 'results' in data:
                    for place in data['results']:
                        place_id = place.get('place_id')
                        if place_id and place_id not in all_places:
                            all_places[place_id] = place
                    
                    print(f"   [{i+1}/{len(grid_centers)}] {query}: +{len(data['results'])} (total: {len(all_places)})")
                elif data.get('status') == 'ZERO_RESULTS':
                    pass  # Expected for some grid points
                else:
                    print(f"   ⚠️  {query}: {data.get('status')}")
                
                time.sleep(0.3)  # Rate limiting
                
            except Exception as e:
                print(f"   ⚠️  Search error for {query}: {e}")
                continue
    
    print(f"   ✅ Found {len(all_places)} unique places")
    return all_places

# ============================================================================
# STEP 4: PLACE DETAILS ENRICHMENT
# ============================================================================

def get_place_details(place_id: str) -> Dict:
    """Fetch additional place details including website"""
    fields = 'name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,url'
    params = {'place_id': place_id, 'fields': fields, 'key': API_KEY}
    url = f'https://maps.googleapis.com/maps/api/place/details/json?{urlencode(params)}'
    
    data = fetch_json(url)
    if data.get('status') == 'OK':
        return data.get('result', {})
    return {}

def enrich_places_with_details(raw_places: Dict[str, Dict]) -> Dict[str, Dict]:
    """Enrich raw places with Place Details API data"""
    print(f"\n📞 Enriching {len(raw_places)} places with details...")
    
    enriched = {}
    count = 0
    
    for place_id, place in raw_places.items():
        count += 1
        if count % 10 == 0:
            print(f"   [{count}/{len(raw_places)}]")
        
        details = get_place_details(place_id)
        
        # Merge details into place data
        enriched_place = {**place}
        if details:
            enriched_place['website'] = details.get('website', '')
            enriched_place['formatted_phone_number'] = details.get('formatted_phone_number', '') or place.get('formatted_phone_number', '')
        
        enriched[place_id] = enriched_place
        time.sleep(0.1)  # Rate limiting
    
    print(f"   ✅ Enriched all places")
    return enriched

# ============================================================================
# STEP 5: WEBSITE CRAWLING & SIGNAL DETECTION
# ============================================================================

def extract_emails(html: str) -> List[str]:
    """Extract emails from HTML"""
    emails = EMAIL_PATTERN.findall(html.lower())
    return [e for e in emails if not any(x in e for x in ['example', 'domain', '.png', '.jpg', 'wix', 'sentry'])]

def extract_phones(html: str) -> List[str]:
    """Extract phone numbers from HTML"""
    return PHONE_PATTERN.findall(html)

def extract_social(html: str) -> Dict[str, str]:
    """Extract Instagram and Facebook URLs"""
    result = {'instagram': '', 'facebook': ''}
    
    ig_match = INSTAGRAM_PATTERN.search(html)
    if ig_match and ig_match.group(1) not in ['p', 'reel', 'stories', 'explore']:
        result['instagram'] = f"instagram.com/{ig_match.group(1)}"
    
    fb_match = FACEBOOK_PATTERN.search(html)
    if fb_match and fb_match.group(1) not in ['sharer', 'share', 'plugins']:
        result['facebook'] = f"facebook.com/{fb_match.group(1)}"
    
    return result

def find_contact_form(html: str, base_url: str) -> str:
    """Find contact form URL"""
    patterns = [r'href=["\']([^"\']*(?:contact|get-in-touch|reach-us)[^"\']*)["\']']
    for pattern in patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        if matches:
            url = matches[0]
            if url.startswith('/'):
                from urllib.parse import urlparse
                parsed = urlparse(base_url)
                url = f"{parsed.scheme}://{parsed.netloc}{url}"
            return url
    return ''

def detect_team_solo(html: str) -> str:
    """Detect if TEAM or SOLO"""
    html_lower = html.lower()
    
    team_score = sum(1 for pattern in TEAM_SIGNALS if re.search(pattern, html_lower, re.IGNORECASE))
    solo_score = sum(1 for pattern in SOLO_SIGNALS if re.search(pattern, html_lower, re.IGNORECASE))
    
    if team_score >= 2:
        return 'TEAM'
    elif solo_score >= 2:
        return 'SOLO'
    elif team_score > solo_score:
        return 'TEAM'
    elif solo_score > team_score:
        return 'SOLO'
    else:
        return 'UNKNOWN'

def detect_junior_friendly(html: str) -> str:
    """Detect if junior-friendly"""
    html_lower = html.lower()
    
    strong_score = sum(1 for pattern in JUNIOR_SIGNALS_STRONG if re.search(pattern, html_lower, re.IGNORECASE))
    moderate_score = sum(1 for pattern in JUNIOR_SIGNALS_MODERATE if re.search(pattern, html_lower, re.IGNORECASE))
    
    if strong_score >= 1:
        return 'YES'
    elif moderate_score >= 2:
        return 'MAYBE'
    elif moderate_score >= 1:
        return 'MAYBE'
    else:
        return 'NO'

def crawl_website(url: str, center_lat: float, center_lng: float) -> Dict:
    """Crawl website for contacts and signals"""
    result = {
        'site_email': '',
        'site_phone': '',
        'contact_form_url': '',
        'instagram_url': '',
        'facebook_url': '',
        'team_label': 'UNKNOWN',
        'junior_label': 'NO',
        'spa_type': '',
        'crawl_status': 'NO_SITE',
    }
    
    if not url:
        return result
    
    try:
        html = fetch_html(url)
        if not html:
            result['crawl_status'] = 'TIMEOUT'
            return result
        
        # Extract contacts
        emails = extract_emails(html)
        if emails:
            result['site_email'] = '; '.join(emails[:3])
        
        phones = extract_phones(html)
        if phones:
            result['site_phone'] = phones[0]
        
        social = extract_social(html)
        result['instagram_url'] = social['instagram']
        result['facebook_url'] = social['facebook']
        
        result['contact_form_url'] = find_contact_form(html, url)
        
        # Detect signals
        result['team_label'] = detect_team_solo(html)
        result['junior_label'] = detect_junior_friendly(html)
        
        # Detect spa type
        html_lower = html.lower()
        if 'medical spa' in html_lower or 'medspa' in html_lower:
            result['spa_type'] = 'medical spa'
        elif 'day spa' in html_lower:
            result['spa_type'] = 'day spa'
        else:
            result['spa_type'] = 'salon'
        
        result['crawl_status'] = 'OK'
        
    except Exception as e:
        result['crawl_status'] = 'ERROR'
    
    return result

# ============================================================================
# STEP 5: SCORING & BUCKETING
# ============================================================================

def calculate_score(place_data: Dict, crawl_data: Dict) -> int:
    """Calculate priority score (0-100)"""
    score = 0
    
    # Junior-friendly (most important)
    if crawl_data['junior_label'] == 'YES':
        score += 30
    elif crawl_data['junior_label'] == 'MAYBE':
        score += 15
    
    # Team vs Solo
    if crawl_data['team_label'] == 'TEAM':
        score += 25
    
    # Medical spa (matches candidate background)
    if crawl_data['spa_type'] == 'medical spa':
        score += 15
    
    # Contact methods
    if crawl_data['site_email']:
        score += 15
    if crawl_data['contact_form_url']:
        score += 10
    if crawl_data['instagram_url'] or crawl_data['facebook_url']:
        score += 8
    if crawl_data['site_phone'] or place_data.get('phone'):
        score += 5
    if place_data.get('website'):
        score += 5
    
    # Reviews
    review_count = place_data.get('review_count', 0)
    if review_count >= 100:
        score += 10
    elif review_count >= 30:
        score += 7
    elif review_count >= 10:
        score += 4
    
    # Rating
    try:
        rating = float(place_data.get('rating', 0) or 0)
    except (ValueError, TypeError):
        rating = 0
    
    if rating >= 4.5:
        score += 6
    elif rating >= 4.0:
        score += 3
    
    return min(score, 100)

def determine_bucket(score: int, team_label: str, junior_label: str, has_contact: bool) -> str:
    """Determine outreach bucket A/B/C/D"""
    if junior_label == 'YES' and team_label == 'TEAM' and has_contact:
        return 'A'
    elif team_label == 'TEAM' and junior_label == 'MAYBE' and has_contact:
        return 'B'
    elif team_label == 'TEAM' and has_contact:
        return 'C'
    else:
        return 'D'

def determine_contact_method(crawl_data: Dict, place_data: Dict) -> str:
    """Determine primary contact method"""
    if crawl_data['site_email']:
        return 'email'
    elif crawl_data['contact_form_url']:
        return 'form'
    elif crawl_data['instagram_url'] or crawl_data['facebook_url']:
        return 'social'
    elif crawl_data['site_phone'] or place_data.get('phone'):
        return 'phone'
    else:
        return 'manual'

# ============================================================================
# STEP 6: SAVING & LOADING
# ============================================================================

TSV_HEADERS = [
    'place_id', 'name', 'address', 'distance_miles', 'google_phone', 'website', 
    'google_maps_url', 'rating', 'review_count', 'site_email', 'site_phone',
    'contact_form_url', 'instagram_url', 'facebook_url', 'spa_type', 
    'team_label', 'junior_label', 'priority_score', 'contact_method',
    'outreach_bucket', 'outreach_status', 'notes', 'crawl_status'
]

def save_to_tsv(results: List[Dict], filepath: Path):
    """Save results to TSV"""
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=TSV_HEADERS, delimiter='\t', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(results)

def load_from_tsv(filepath: Path) -> List[Dict]:
    """Load results from TSV"""
    if not filepath.exists():
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        return list(reader)

def backup_progress(results: List[Dict]):
    """Create timestamped backup"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = BACKUP_DIR / f'spa_leads_backup_{timestamp}.tsv'
    save_to_tsv(results, backup_path)
    print(f"   💾 Backup saved: {backup_path.name}")

# ============================================================================
# MAIN PIPELINE
# ============================================================================

def main(test_mode=False, max_places_override=None):
    """Main execution pipeline"""
    print("=" * 60)
    print("🌟 BROOKLYN SPA/SALON LEAD FINDER")
    print("=" * 60)
    
    if not API_KEY:
        print("❌ Error: GOOGLE_MAPS_API_KEY not found in .env")
        return
    
    # Override config for test mode
    if test_mode:
        CONFIG['max_places'] = 20
        print("\n⚠️  TEST MODE: Limited to 20 places")
    elif max_places_override:
        CONFIG['max_places'] = max_places_override
    
    # Step 1: Geocode
    center = geocode_zip(CONFIG['center_zip'])
    if not center:
        return
    
    # Step 2: Generate grid
    grid_centers = generate_search_grid(center, CONFIG['radius_miles'], CONFIG['grid_step_miles'])
    
    # Step 3: Search places
    raw_places = search_places(grid_centers, QUERIES, CONFIG['max_places'])
    
    if not raw_places:
        print("\n❌ No places found")
        return
    
    # Step 4: Enrich with Place Details (get websites)
    enriched_places = enrich_places_with_details(raw_places)
    
    # Load existing progress
    existing_results = load_from_tsv(PROGRESS_FILE)
    existing_ids = {r['place_id'] for r in existing_results}
    
    print(f"\n📊 Processing {len(enriched_places)} places...")
    if existing_ids:
        print(f"   Found {len(existing_ids)} existing entries (will skip)")
    
    all_results = existing_results.copy()
    count = 0
    
    # Step 5-6: Crawl and score each place
    for place_id, place in enriched_places.items():
        if place_id in existing_ids:
            continue
        
        count += 1
        name = place.get('name', 'Unknown')[:40]
        print(f"\n[{count}/{len(enriched_places) - len(existing_ids)}] {name}...")
        
        # Extract basic data from legacy API format
        geometry = place.get('geometry', {})
        location = geometry.get('location', {})
        lat, lng = location.get('lat', 0), location.get('lng', 0)
        distance = haversine_distance(center[0], center[1], lat, lng) if lat and lng else 0
        
        place_data = {
            'place_id': place_id,
            'name': name,
            'address': place.get('formatted_address', ''),
            'distance_miles': round(distance, 1),
            'google_phone': place.get('formatted_phone_number', ''),
            'website': place.get('website', ''),
            'google_maps_url': f"https://www.google.com/maps/place/?q=place_id:{place_id}",
            'rating': place.get('rating', ''),
            'review_count': place.get('user_ratings_total', 0),
            'phone': place.get('formatted_phone_number', ''),
        }
        
        # Crawl website
        crawl_data = crawl_website(place_data['website'], center[0], center[1])
        
        # Calculate score and bucket
        score = calculate_score(place_data, crawl_data)
        has_contact = bool(crawl_data['site_email'] or crawl_data['contact_form_url'] or 
                          crawl_data['instagram_url'] or crawl_data['facebook_url'] or place_data['phone'])
        bucket = determine_bucket(score, crawl_data['team_label'], crawl_data['junior_label'], has_contact)
        contact_method = determine_contact_method(crawl_data, place_data)
        
        # Combine all data
        result = {
            **place_data,
            **crawl_data,
            'priority_score': score,
            'contact_method': contact_method,
            'outreach_bucket': bucket,
            'outreach_status': '',
            'notes': '',
        }
        
        all_results.append(result)
        
        # Show found items
        found = []
        if crawl_data['site_email']: found.append('📧')
        if crawl_data['contact_form_url']: found.append('📝')
        if crawl_data['instagram_url']: found.append('📸')
        if crawl_data['facebook_url']: found.append('📘')
        if found:
            print(f"   Found: {' '.join(found)}")
        print(f"   Signals: {crawl_data['team_label']} | Junior: {crawl_data['junior_label']} | Score: {score} | Bucket: {bucket}")
        
        # Incremental save
        if count % CONFIG['save_frequency'] == 0:
            save_to_tsv(all_results, PROGRESS_FILE)
            print(f"   💾 Progress saved ({len(all_results)} total)")
        
        # Backup
        if count % CONFIG['backup_frequency'] == 0:
            backup_progress(all_results)
        
        time.sleep(CONFIG['crawl_delay_sec'])
    
    # Final save
    save_to_tsv(all_results, PROGRESS_FILE)
    save_to_tsv(all_results, FINAL_FILE)
    
    print("\n" + "=" * 60)
    print("✅ COMPLETE!")
    print("=" * 60)
    print(f"\n📊 Results Summary:")
    print(f"   Total places: {len(all_results)}")
    print(f"   With email: {sum(1 for r in all_results if r.get('site_email'))}")
    print(f"   With contact form: {sum(1 for r in all_results if r.get('contact_form_url'))}")
    print(f"   With Instagram: {sum(1 for r in all_results if r.get('instagram_url'))}")
    print(f"   Team businesses: {sum(1 for r in all_results if r.get('team_label') == 'TEAM')}")
    print(f"   Junior-friendly: {sum(1 for r in all_results if r.get('junior_label') in ['YES', 'MAYBE'])}")
    print(f"\n📁 Output files:")
    print(f"   {FINAL_FILE}")
    print(f"\n💡 To import to Google Sheets:")
    print(f"   1. Open file: {FINAL_FILE}")
    print(f"   2. Cmd+A to select all")
    print(f"   3. Cmd+C to copy")
    print(f"   4. Paste into Google Sheets (Cmd+V)")

if __name__ == "__main__":
    import sys
    test_mode = '--test-mode' in sys.argv
    max_places = None
    
    for arg in sys.argv:
        if arg.startswith('--max-places='):
            max_places = int(arg.split('=')[1])
    
    main(test_mode=test_mode, max_places_override=max_places)
