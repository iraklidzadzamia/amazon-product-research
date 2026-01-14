# Directive: Find Reddit Leads

## Goal
Find potential customers on Reddit who need AI automation for customer messaging (FB/IG/Telegram/WhatsApp), CRM integration, or appointment booking.

## Product Context
**What we sell:** AI agents that:
- Handle customer messages across FB Messenger, Instagram DM, Telegram, WhatsApp
- Use custom knowledge base (prices, addresses, FAQs)
- Integrate with CRM systems
- Book appointments to CRM or Google Calendar

## Target Subreddits
| Category | Subreddits |
|----------|------------|
| Business | r/smallbusiness, r/Entrepreneur, r/startups, r/SaaS |
| Marketing | r/marketing, r/digitalmarketing, r/socialmedia |
| Industries | r/realtors, r/RealEstate, r/veterinarian, r/restaurateur, r/salons, r/dental, r/fitness |
| Tech | r/automation, r/nocode, r/ChatGPT |

## Search Keywords
```
"too many messages", "overwhelmed with DMs", "can't keep up with customers"
"need chatbot", "looking for automation", "customer service help"
"appointment booking", "scheduling nightmare", "missed appointments"
"CRM integration", "automate responses", "AI for business"
"Instagram DMs", "Facebook messages", "WhatsApp business"
```

## Execution Tools
| Script | Purpose |
|--------|---------|
| `execution/reddit_lead_scraper.py` | Search Reddit for matching posts/comments |
| `execution/export_to_sheets.py` | Export leads to Google Sheets |

## Steps
1. Run `reddit_lead_scraper.py` with subreddits and keywords
2. Script filters posts from last 30 days with engagement
3. Scores leads by relevance (keyword matches, upvotes, comment sentiment)
4. Export to Google Sheets with `export_to_sheets.py`

## Output Format (Google Sheets columns)
| Column | Description |
|--------|-------------|
| Username | Reddit username |
| Subreddit | Where found |
| Post Title | Title of their post |
| Post URL | Direct link |
| Snippet | Key text showing their need |
| Score | Relevance score (1-10) |
| Date | When posted |
| Status | For tracking (New/Contacted/Responded) |

## Edge Cases
- **Rate limits:** Reddit allows 60 requests/min. Script handles this.
- **Deleted posts:** Skip gracefully
- **Banned subreddits:** Log and continue with others

## Future Enhancements
- [ ] Auto-DM sending via `reddit_dm_sender.py`
- [ ] Sentiment analysis to prioritize frustrated users
- [ ] Competitor mention tracking

## Learnings
<!-- Updated during self-annealing -->
