#!/usr/bin/env python3
"""
Test Meta Ad Library API access token
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")

print("=" * 60)
print("META AD LIBRARY API - TOKEN DIAGNOSTIC")
print("=" * 60)

# Check if token exists
if not ACCESS_TOKEN:
    print("\n❌ ERROR: META_ACCESS_TOKEN not found in .env file")
    print("\nPlease add your token to .env:")
    print("META_ACCESS_TOKEN=YOUR_TOKEN_HERE")
    exit(1)

print(f"\n✅ Token found (length: {len(ACCESS_TOKEN)} characters)")
print(f"Token preview: {ACCESS_TOKEN[:20]}...")

# Test 1: Validate token
print("\n" + "-" * 60)
print("TEST 1: Validating Access Token")
print("-" * 60)

url = f"https://graph.facebook.com/v24.0/me?access_token={ACCESS_TOKEN}"

try:
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Token is VALID")
        print(f"   User ID: {data.get('id', 'N/A')}")
        print(f"   Name: {data.get('name', 'N/A')}")
    else:
        print(f"❌ Token validation FAILED")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"❌ Error: {str(e)}")

# Test 2: Check Ad Library API access
print("\n" + "-" * 60)
print("TEST 2: Testing Ad Library API Access")
print("-" * 60)

# Try a simple search
url = "https://graph.facebook.com/v24.0/ads_archive"
params = {
    "access_token": ACCESS_TOKEN,
    "search_terms": "test",
    "ad_reached_countries": "US",  # Try US first (more ads)
    "limit": 1,
    "fields": "id,ad_creative_bodies"
}

try:
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        ads = data.get("data", [])
        print(f"✅ Ad Library API is ACCESSIBLE")
        print(f"   Found {len(ads)} ad(s) for test search in US")
    else:
        print(f"❌ Ad Library API access FAILED")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        # Parse error
        try:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", "Unknown error")
            error_code = error_data.get("error", {}).get("code", "N/A")
            print(f"\n   Error Message: {error_msg}")
            print(f"   Error Code: {error_code}")
            
            # Provide guidance
            if "OAuthException" in str(error_data):
                print("\n💡 SOLUTION:")
                print("   1. Your token may have expired (they last 1-2 hours)")
                print("   2. Go to: https://developers.facebook.com/tools/explorer/")
                print("   3. Generate a NEW Access Token")
                print("   4. Update .env file with the new token")
        except:
            pass
            
except Exception as e:
    print(f"❌ Error: {str(e)}")

# Test 3: Try Georgia specifically
print("\n" + "-" * 60)
print("TEST 3: Testing Georgia (GE) Search")
print("-" * 60)

params["ad_reached_countries"] = "GE"
params["search_terms"] = "ვეტერინარია"

try:
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        ads = data.get("data", [])
        print(f"✅ Georgia search WORKS")
        print(f"   Found {len(ads)} ad(s) for 'ვეტერინარია' in Georgia")
    else:
        print(f"❌ Georgia search FAILED")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"❌ Error: {str(e)}")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
