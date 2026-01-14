# Meta Ad Library API - Quick Start Guide

## 🚀 Quick Start (3 Steps)

### 1. Get Your Access Token
1. Open: https://developers.facebook.com/tools/explorer/
2. Copy the Access Token (starts with "EAAA...")
3. Create `.env` file in project root:
   ```bash
   cd "/Users/iraklidzadzamia/Desktop/fromyoutube video reddit"
   echo "META_ACCESS_TOKEN=YOUR_TOKEN_HERE" > .env
   ```

### 2. Test Connection
```bash
cd execution
python3 meta_ad_library.py --test
```

Expected output: `✅ Connection successful!`

### 3. Collect All Ads
```bash
python3 meta_ad_library.py --all-keywords
```

This will:
- Search 6 keywords (Georgian, Russian, English)
- Collect all vet clinic ads from Georgia
- Save to `.tmp/vet_ads_georgia.tsv`

---

## 📊 Analyze Results

After collection, run analysis:

```bash
python3 analyze_vet_ads.py
```

This will:
- Categorize ads by type
- Calculate performance scores
- Identify top performers
- Save analyzed data to `.tmp/vet_ads_analyzed.tsv`

---

## 📁 Output Files

- **`.tmp/vet_ads_georgia.tsv`** - Raw collected ads
- **`.tmp/vet_ads_analyzed.tsv`** - Analyzed with categories and scores

Import into Google Sheets for review!

---

## 🔍 Search Options

**Test single keyword:**
```bash
python3 meta_ad_library.py --keyword "ვეტერინარია" --limit 10
```

**Custom output location:**
```bash
python3 meta_ad_library.py --all-keywords --output custom_path.tsv
```

---

## ⚠️ Troubleshooting

**"META_ACCESS_TOKEN not found"**
- Ensure `.env` file exists in project root
- Check no spaces around `=` sign
- File must be named exactly `.env` (not `.env.txt`)

**API errors (400, 401)**
- Token expired (they last 1-2 hours)
- Generate new token from Graph API Explorer
- For long-term: convert to long-lived token (60 days)

**No ads found**
- Try different keywords
- Check country code is correct ('GE' for Georgia)
- Some keywords may have no active ads

---

## 📈 Next Steps

1. Review analyzed data in Google Sheets
2. Identify top-performing ad patterns
3. Create 3 creative concepts based on insights
4. Implement for BioNika campaign
