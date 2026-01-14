# Meta Ad Library API - Troubleshooting Guide

## ❌ Problem: OAuthException Error 500

When running the collection script, you may encounter:
```
ERROR: 500 - {"error":{"message":"An unknown error has occurred.","type":"OAuthException","code":1}}
```

## 🔍 Root Cause

The Access Token is **valid** but **lacks permissions** for Ad Library API access.

**Why?** Meta requires **identity verification** to access Ad Library API, even though the data is public.

## ✅ Diagnostic Results

- ✅ Token is valid (works for Graph API)
- ✅ User authenticated: Irakli Dzadzamia
- ❌ Ad Library API access: **DENIED**

## 🎯 Solutions

### Option 1: Complete Identity Verification (Recommended for long-term use)

**Time**: 10-15 minutes  
**Benefit**: Full API access, automated data collection

**Steps**:
1. Go to: https://www.facebook.com/business/help/2058515294227817
2. Follow Meta's identity verification process:
   - Upload government-issued ID (passport, driver's license)
   - Take a selfie
   - Provide proof of residency
3. Wait for approval (usually 24-48 hours)
4. Generate new Access Token after approval
5. Run the collection script again

### Option 2: Browser Automation (Quick alternative)

**Time**: Works immediately  
**Benefit**: No verification needed

**How it works**:
- Script opens Ad Library in browser
- Automatically searches keywords
- Collects visible ad data
- Exports to TSV

**Trade-offs**:
- Slower than API
- Limited to visible data
- Requires browser interaction

### Option 3: Manual Collection (Fallback)

**Time**: 30-60 minutes  
**Benefit**: Always works

**Steps**:
1. Visit: https://www.facebook.com/ads/library/
2. Set country: Georgia
3. Search each keyword manually:
   - ვეტერინარია
   - ვეტკლინიკა
   - ვეტერინარი
   - ветеринар
   - ветклиника
   - vet clinic
4. Screenshot/note top performing ads
5. Analyze patterns manually

## 💡 Recommendation

**For BioNika project**:
- Use **Option 3** (manual) for immediate insights
- Start **Option 1** (verification) in parallel for future use
- Skip Option 2 unless you need repeated automated collection

## 📊 What You Can Do Right Now

Even without API access, you can:

1. **Manual Ad Library Research** (30 min):
   - Visit https://www.facebook.com/ads/library/
   - Filter: Country = Georgia
   - Search: ვეტერინარია
   - Review top 10-15 ads
   - Note patterns (text length, visuals, offers)

2. **Create Concepts** based on manual research:
   - Identify most common ad types
   - Note successful messaging patterns
   - Create 3 concepts for BioNika

3. **Start verification** for future automation

## 🔧 Technical Details

**Error Code**: OAuthException Code 1  
**Meaning**: Token lacks required permissions  
**Required Permission**: Ad Library API access (requires verified identity)  
**Workaround**: Browser automation or manual collection
