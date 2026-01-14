# INSTRUCTIONS: Meta Ad Library API Setup

## Step 1: Copy Your Access Token

1. Go back to Graph API Explorer: https://developers.facebook.com/tools/explorer/
2. You should see your Access Token in the right panel (starts with "EAAA...")
3. Click the copy icon next to it

## Step 2: Create .env File

Create a file called `.env` in this directory with the following content:

```
META_ACCESS_TOKEN=PASTE_YOUR_TOKEN_HERE
```

Replace `PASTE_YOUR_TOKEN_HERE` with the token you copied.

## Step 3: Test the Connection

Run this command to test if everything works:

```bash
cd "/Users/iraklidzadzamia/Desktop/fromyoutube video reddit/execution"
python3 meta_ad_library.py --test
```

If successful, you'll see: ✅ Connection successful!

## Step 4: Collect All Ads

Once the test passes, run the full collection:

```bash
python3 meta_ad_library.py --all-keywords
```

This will:
- Search all 6 keywords (Georgian, Russian, English)
- Collect all unique ads from Georgian vet clinics
- Save results to `.tmp/vet_ads_georgia.tsv`

## Troubleshooting

**If you get "META_ACCESS_TOKEN not found":**
- Make sure the `.env` file is in the root directory: `/Users/iraklidzadzamia/Desktop/fromyoutube video reddit/.env`
- Check that there are no spaces around the `=` sign
- Make sure the file is named exactly `.env` (not `.env.txt`)

**If you get API errors:**
- Your token might have expired (they last 1-2 hours by default)
- Generate a new token from Graph API Explorer
- For long-term use, you can convert to a long-lived token (60 days)
