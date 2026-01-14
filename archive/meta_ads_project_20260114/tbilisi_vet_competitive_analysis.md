# Directive: Tbilisi Vet Clinic Competitive Analysis

## Client
**BioNika Veterinary Clinic**
- Location: Isani, Tbilisi
- Services: Vaccination, surgery, grooming, hospitalization
- Target audience: Dog & cat owners (no exotic animals), Russian/Kazakh/Ukrainian relocants
- Unique feature: AI chatbot 24/7 (Instagram, WhatsApp, Facebook) with booking capability

## Goal
Analyze competitor vet clinics in Tbilisi to identify best-performing social media content and create 3 high-quality creative concepts for BioNika.

## Deliverables
1. **Competitor Analysis Report**:
   - Top 15 vet clinics in Tbilisi (Instagram)
   - 5 recent posts from each (75 posts total)
   - Engagement metrics (likes, comments, ER%)
   - Top 10 best-performing posts with analysis

2. **Creative Concepts** (3 total):
   - Georgian text copy
   - Visual concept description
   - Format recommendation (post/stories/carousel)
   - Based on proven patterns from competitor analysis

## Research Methodology

### Step 1: Setup Meta Ad Library API (5 min)
**Method**: Meta Ad Library API integration
- Access Graph API Explorer: https://developers.facebook.com/tools/explorer/
- Copy User Access Token
- Add to `.env` file as `META_ACCESS_TOKEN`
- Test connection: `python3 meta_ad_library.py --test`

### Step 2: Collect Ads (10 min)
**Automated collection via API**:
- Search keywords (Georgian, Russian, English):
  - `ვეტერინარია`, `ვეტკლინიკა`, `ვეტერინარი`
  - `ветеринар`, `ветклиника`
  - `vet clinic`
- Filter by country: Georgia (GE)
- Collect all active and recent ads
- Run: `python3 meta_ad_library.py --all-keywords`

**Data collected**:
- Ad copy text (Georgian/Russian/English)
- Creative URLs (images/videos)
- Start/end dates
- Advertiser name
- Impressions/spend ranges
- Active status

### Step 3: Analyze Performance (15 min)
**Automated categorization**:
- Run: `python3 analyze_vet_ads.py`

**Categories**:
- Promotional (discounts, offers)
- Educational (pet care tips)
- Emotional (rescue stories, testimonials)
- Service-focused (vaccination, surgery)
- Emergency/24-7

**Performance scoring**:
- Long-running ads (>30 days = proven winners)
- High impressions (>10,000)
- Currently active
- Has spend data (serious advertisers)

**Pattern identification**:
- Text length (short vs long)
- Emoji usage
- Call-to-action presence
- Visual style
- Language preference

### Step 4: Create Concepts (20 min)
Based on top-performing patterns from analysis:

**Concept 1**: Highest-performing category
**Concept 2**: Second-best category
**Concept 3**: Unique angle (featuring AI bot)

Each concept includes:
- Georgian caption (50-150 words)
- Visual description for designer
- Format (post/stories/carousel)
- Expected engagement prediction

## Success Metrics
- Identify clear patterns in successful ads
- 3 actionable creative concepts
- Georgian text ready to use
- Visual guidelines for implementation

## Advantages Over Manual Instagram Search
- **Faster**: 30 min vs 70 min
- **More data**: Impressions, spend, exact dates
- **Broader coverage**: All advertisers, not just organic posts
- **Performance metrics**: Proven winners (long-running ads)
- **Scalable**: Can collect hundreds of ads automatically

## Timeline
- Setup: 5 min
- Collection: 10 min
- Analysis: 15 min
- Creation: 20 min
- **Total**: ~50 minutes (vs 70 min manual)

