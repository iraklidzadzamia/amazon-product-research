# Directive: Find Vet Clinics via Google Maps

## Goal
Find veterinary clinics in a target city, collect contact info, and extract social media links from their websites.

## Product Context
**What we sell:** AI agents for customer messaging automation in vet clinics.

## Data Collected

### From Google Maps API
| Field | Description |
|-------|-------------|
| place_id | Unique Google ID (for deduplication) |
| Название | Clinic name |
| Адрес | Full address |
| Телефон | Phone number |
| Сайт | Website URL |
| Рейтинг | Star rating (1-5) |
| Отзывы | Number of reviews |
| Часы работы | Business hours |
| Google Maps | Direct link to Maps |

### From Website Scraping
| Field | Description |
|-------|-------------|
| Email | Contact email (info@, contact@, etc.) |
| Instagram | Instagram handle/link |
| Facebook | Facebook page link |

## Execution Tools
| Script | Purpose |
|--------|---------|
| `execution/gmaps_lead_scraper.py` | Search Google Maps + scrape websites |
| `execution/export_to_sheets.py` | Export to Google Sheets |

## Steps
1. Search Google Maps for "veterinary clinic" in target city
2. Collect up to 600 results with pagination
3. For each clinic with a website, scrape for socials/email
4. Deduplicate by place_id
5. Export to CSV

## Configuration
```
City: New York
Category: Veterinary clinic
Max results: 600
```

## API Cost Estimate
- ~10 Text Search requests = $0.32
- ~600 Place Details = $10.20
- **Total: ~$10.50 (within $200 free tier)**

## Learnings
<!-- Updated during self-annealing -->
