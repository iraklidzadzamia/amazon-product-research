#!/usr/bin/env python3
"""
Script: hackernews_lead_scraper.py
Purpose: Search Hacker News for potential customers needing AI automation

NO API KEYS REQUIRED - Uses HN's free Algolia API

Usage:
    python execution/hackernews_lead_scraper.py

Related Directive: directives/find_hackernews_leads.md
"""

import argparse
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import urlencode
import ssl

# Bypass SSL issues on Mac
ssl._create_default_https_context = ssl._create_unverified_context

# Keywords to search for
SEARCH_QUERIES = [
    "need automation",
    "chatbot recommendation",
    "customer service tool",
    "too many messages",
    "appointment booking",
    "CRM for small business",
    "automate customer support",
    "AI assistant business",
    "scheduling software",
    "WhatsApp business"
]

# Keywords for relevance scoring
RELEVANCE_KEYWORDS = [
    "automation", "automate", "chatbot", "bot",
    "customer service", "customer support", "messages", "DMs",
    "appointment", "booking", "scheduling", "calendar",
    "CRM", "small business", "startup",
    "overwhelmed", "too many", "can't keep up", "help",
    "Instagram", "Facebook", "WhatsApp", "Telegram",
    "AI", "assistant", "virtual assistant"
]


def fetch_hn_search(query: str, days_back: int = 30) -> list:
    """
    Search Hacker News using Algolia API.
    
    Args:
        query: Search term
        days_back: How many days back to search
        
    Returns:
        List of matching items
    """
    # Calculate timestamp for date filter
    cutoff = datetime.now() - timedelta(days=days_back)
    cutoff_ts = int(cutoff.timestamp())
    
    params = {
        "query": query,
        "tags": "(story,comment)",
        "numericFilters": f"created_at_i>{cutoff_ts}",
        "hitsPerPage": 50
    }
    
    url = f"https://hn.algolia.com/api/v1/search?{urlencode(params)}"
    
    try:
        req = Request(url, headers={"User-Agent": "LeadFinder/1.0"})
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get("hits", [])
    except Exception as e:
        print(f"  Error searching '{query}': {e}")
        return []


def calculate_relevance_score(text: str, points: int) -> int:
    """
    Calculate lead relevance score from 1-10.
    
    Args:
        text: Combined title and text
        points: HN upvotes
        
    Returns:
        Score from 1-10
    """
    text_lower = text.lower()
    score = 0
    
    # Keyword matches (up to 5 points)
    keyword_matches = sum(1 for kw in RELEVANCE_KEYWORDS if kw.lower() in text_lower)
    score += min(keyword_matches * 0.8, 5)
    
    # Engagement bonus (up to 2 points)
    if points > 5:
        score += 1
    if points > 20:
        score += 1
    
    # Urgency words (up to 2 points)
    urgency_words = ["need", "help", "looking for", "recommend", "urgent", "asap"]
    urgency_matches = sum(1 for word in urgency_words if word in text_lower)
    score += min(urgency_matches, 2)
    
    # Question indicator (1 point)
    if "?" in text or text_lower.startswith(("how", "what", "which", "any")):
        score += 1
    
    return min(int(score), 10)


def process_item(item: dict) -> dict:
    """Convert HN API item to our lead format."""
    title = item.get("title") or item.get("story_title") or ""
    text = item.get("comment_text") or item.get("story_text") or ""
    full_text = f"{title} {text}"
    
    # Clean HTML tags from text
    import re
    clean_text = re.sub(r'<[^>]+>', '', full_text)
    
    points = item.get("points") or item.get("story_points") or 0
    
    # Build URL
    if item.get("objectID"):
        url = f"https://news.ycombinator.com/item?id={item['objectID']}"
    else:
        url = item.get("url", "")
    
    # Parse date
    created_at = item.get("created_at", "")
    try:
        date = datetime.fromisoformat(created_at.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except:
        date = "Unknown"
    
    return {
        "username": item.get("author", "[unknown]"),
        "title": title[:100] if title else "(comment)",
        "url": url,
        "snippet": clean_text[:200],
        "score": calculate_relevance_score(clean_text, points),
        "points": points,
        "comments": item.get("num_comments", 0),
        "date": date,
        "status": "New",
        "source": "HackerNews"
    }


def deduplicate_leads(leads: list) -> list:
    """Remove duplicate leads based on URL."""
    seen_urls = set()
    unique_leads = []
    
    for lead in leads:
        if lead["url"] not in seen_urls:
            seen_urls.add(lead["url"])
            unique_leads.append(lead)
    
    return unique_leads


def main():
    parser = argparse.ArgumentParser(description="Search Hacker News for leads (no API key required)")
    parser.add_argument(
        "--output",
        type=str,
        default=".tmp/hn_leads.json",
        help="Output JSON file path"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="How many days back to search"
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=3,
        help="Minimum relevance score to include"
    )
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("🔍 Hacker News Lead Scraper")
    print(f"   Searching last {args.days} days")
    print(f"   Minimum score: {args.min_score}")
    print()
    
    # Collect leads from all searches
    all_leads = []
    
    for i, query in enumerate(SEARCH_QUERIES, 1):
        print(f"[{i}/{len(SEARCH_QUERIES)}] Searching: '{query}'...")
        
        items = fetch_hn_search(query, args.days)
        
        for item in items:
            lead = process_item(item)
            if lead["score"] >= args.min_score:
                all_leads.append(lead)
        
        print(f"   Found {len(items)} items")
        time.sleep(0.5)  # Be nice to API
    
    # Deduplicate and sort
    unique_leads = deduplicate_leads(all_leads)
    unique_leads.sort(key=lambda x: x["score"], reverse=True)
    
    # Save to JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(unique_leads, f, indent=2, ensure_ascii=False)
    
    print()
    print(f"✅ Found {len(unique_leads)} unique leads (score >= {args.min_score})")
    print(f"   Saved to: {output_path}")
    
    if unique_leads:
        print()
        print("Top 5 leads by relevance:")
        for lead in unique_leads[:5]:
            title = lead['title'][:45] + "..." if len(lead['title']) > 45 else lead['title']
            print(f"   [{lead['score']}/10] {title}")
            print(f"            → {lead['url']}")


if __name__ == "__main__":
    main()
