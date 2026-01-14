# Directive: Brooklyn Spa & Salon Lead Finder (ZIP 11204)

## Goal
Find and analyze spa/salon businesses within 10 miles of Brooklyn ZIP 11204 for potential employment opportunities for a newly licensed esthetician with medical background.

## Output: Google Sheets-ready TSV file with:
- Business details (name, address, phone, website, Google Maps link)
- Contact information (email, contact form, Instagram, Facebook)
- AI-analyzed signals: TEAM vs SOLO, Junior-friendly
- Priority scoring for outreach
- CRM fields for tracking

## Key Requirements
- Use Google Places API (New) with proper FieldMask
- Grid-based search to cover full 10-mile radius (~200-400 expected results)
- Website crawling for contact info + team/junior signals
- Incremental saving (every 10 places) to prevent data loss
- Deduplicate strictly by place_id
- Max 600 places total (safety limit)

## Configuration
```python
center_zip = "11204"
radius_miles = 10
max_places = 600
min_reviews_soft = 10

queries = [
    "medical spa",
    "day spa",
    "beauty salon",
    "skin care clinic",
    "laser hair removal",
    "waxing",
    "esthetician"
]
```

## Candidate Profile (for signal detection)
- **Name**: Irma Pipiya
- **License**: NY Licensed Esthetician (2025, 600 hours)
- **Background**: Doctor of Dentistry (strong medical/clinical background)
- **Skills**: 
  - Facials, skin analysis, professional devices
  - High frequency, LED therapy, skin scrubber
  - Waxing, lash extensions
  - Medical-grade sanitation protocols
- **Seeking**: Junior-friendly team environment, preferably medical spa

## Signal Detection Strategy

### TEAM vs SOLO Detection:
**TEAM signals** (look for on website):
- URLs: `/team`, `/staff`, `/about-us`
- Phrases: "meet our team", "our estheticians", "our specialists", "our providers"
- Multiple staff photos/bios
- "join our team", "careers", "we're hiring"

**SOLO signals**:
- "about me", "I am", "my studio", "owner-operator"
- Single person photos only
- "sole proprietor", "independent", "private practice"

### JUNIOR-FRIENDLY Detection:
**Strong signals** (+30 points):
- "training provided", "mentorship program", "new graduates welcome"
- "no experience required", "we train", "entry level"
- "internship", "apprenticeship", "academy"

**Moderate signals** (+15 points):
- "growing team", "expanding", "career development"
- "supportive environment", "learn and grow"

## Contact Method Priority
1. **Email** (+15 points) - best for professional outreach
2. **Contact Form** (+10 points) - structured, reliable
3. **Instagram/Facebook** (+8 points) - informal but works for salons
4. **Phone only** (+5 points) - time-consuming
5. **None** (+0 points) - requires manual research

## Scoring Formula (0-100)
```
Base score = 0
+ 30  if junior_label == "YES"
+ 25  if team_label == "TEAM"
+ 15  if business type == "medical spa" (matches candidate background)
+ 15  if email found
+ 10  if contact form found
+ 10  if reviews >= 100
+ 8   if Instagram/Facebook found
+ 5   if phone found
+ 5   if website exists
+ 0-6 based on rating (4.5+ gets +6, 4.0-4.4 gets +3, <4.0 gets +0)
```

## Outreach Buckets
- **A (Priority)**: junior=YES + team=TEAM + contact method
- **B (Follow-up)**: team=TEAM + junior=MAYBE + contact method
- **C (Manual review)**: team=TEAM but no clear signals or missing contacts
- **D (Low priority)**: solo=SOLO or reviews < min_reviews_soft or no contacts

## Output Schema (TSV columns)
1. place_id
2. name
3. address
4. distance_miles
5. google_phone
6. website
7. google_maps_url
8. rating
9. review_count
10. site_email
11. site_phone
12. contact_form_url
13. instagram_url
14. facebook_url
15. spa_type (medical spa / day spa / salon)
16. team_label (TEAM / SOLO / UNKNOWN)
17. junior_label (YES / MAYBE / NO)
18. priority_score (0-100)
19. contact_method (email/form/social/phone/manual)
20. outreach_bucket (A/B/C/D)
21. outreach_status (blank - for manual tracking)
22. notes (blank - for manual notes)
23. crawl_status (OK/NO_SITE/TIMEOUT/ERROR)

## Execution Strategy
1. Geocode ZIP 11204 to lat/lng
2. Generate grid of search centers (step ~4.5 miles)
3. For each center + query: Places Text Search (New)
4. Collect unique places, deduplicate by place_id
5. For each place: crawl website for contacts + signals
6. Score and bucket all places
7. Save incremental progress every 10 places
8. Export final TSV: `.tmp/spa_leads_final.tsv`

## Safety & Performance
- Incremental save: `.tmp/spa_leads_progress.tsv` (every 10 places)
- Backup: `.tmp/backups/spa_leads_backup_TIMESTAMP.tsv` (every 50 places)
- Resume capability: load progress file on restart
- API throttling: exponential backoff on 429/5xx
- Crawl politeness: 0.8s delay between requests, 10s timeout
- Max 4 pages per domain

## Success Criteria
- 200-400 unique businesses found within 10-mile radius
- 80%+ with at least one contact method
- 30%+ with email or contact form
- Clear TEAM/SOLO classification for 70%+ of results
- Ready-to-use TSV for Google Sheets import (Cmd+A, Cmd+C, Cmd+V)

## Non-Goals
- No job board scraping (Indeed, LinkedIn)
- No automated email sending
- No Google Sheets API (manual import is simpler)
- No storage of Places content beyond policy (place_id is safe)
