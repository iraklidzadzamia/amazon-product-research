# Directive: Find Hacker News Leads

## Goal
Find potential customers on Hacker News who need AI automation for customer messaging, CRM integration, or appointment booking.

## Product Context
**What we sell:** AI agents that:
- Handle customer messages across FB Messenger, Instagram DM, Telegram, WhatsApp
- Use custom knowledge base (prices, addresses, FAQs)
- Integrate with CRM systems
- Book appointments to CRM or Google Calendar

## Why Hacker News
- Tech-savvy entrepreneurs and startup founders
- People launching businesses who need tools
- Discussions about automation, chatbots, customer service
- **FREE API - no authentication required**

## Search Keywords
```
"automation", "chatbot", "customer service", "too many messages"
"appointment booking", "scheduling", "CRM", "customer support"
"AI assistant", "virtual assistant", "automate responses"
"small business", "startup", "SaaS"
```

## Execution Tools
| Script | Purpose |
|--------|---------|
| `execution/hackernews_lead_scraper.py` | Search HN for matching posts |
| `execution/export_to_sheets.py` | Export leads to Google Sheets |

## Steps
1. Run `hackernews_lead_scraper.py`
2. Script searches Algolia HN API (free, no auth)
3. Filters by keywords and relevance score
4. Saves to `.tmp/hn_leads.json`
5. Optionally export to Google Sheets

## Output Format
| Column | Description |
|--------|-------------|
| Username | HN username |
| Title | Post/comment title |
| URL | Direct link to HN |
| Snippet | Key text showing their need |
| Score | Relevance score (1-10) |
| Points | HN upvotes |
| Date | When posted |
| Status | For tracking |

## API Info
- Endpoint: `https://hn.algolia.com/api/v1/search`
- No authentication required
- Rate limit: Generous (1000+/hour)

## Learnings
<!-- Updated during self-annealing -->
