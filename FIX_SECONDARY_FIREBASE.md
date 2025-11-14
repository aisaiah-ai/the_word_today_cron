# Fix: Secondary Firebase Not Updating

## Problem
The secondary Firebase database (`aisaiah-sfa-dev-app`) is not being updated because the GitHub secret `FIREBASE_CREDENTIALS_JSON_SECONDARY` is missing.

## Root Cause
The primary Cloud Function runs in project `aisaiahconferencefb`. To write to the secondary Firebase project (`aisaiah-sfa-dev-app`), it needs explicit credentials because Application Default Credentials point to the primary project.

## Solution: Add Secondary Firebase Credentials

### Step 1: Download Firebase Key from Console

**IMPORTANT:** You cannot use `gcloud` to create keys - it's blocked by org policy!

**ONLY working method:** Download from Firebase Console

1. Go to Firebase Console:
   https://console.firebase.google.com/project/aisaiah-sfa-dev-app/settings/serviceaccounts/adminsdk

2. Click **"Generate new private key"** button

3. Save the downloaded JSON file (e.g., `aisaiah-sfa-dev-app-firebase-key.json`)

### Step 2: Add GitHub Secret

```bash
# Read the JSON file and set as secret
gh secret set FIREBASE_CREDENTIALS_JSON_SECONDARY \
  --body "$(cat aisaiah-sfa-dev-app-firebase-key.json)"
```

### Step 3: Redeploy the Function

The function will automatically redeploy when you push to main, OR:

1. Go to GitHub Actions:
   https://github.com/aisaiah-ai/the_word_today_cron/actions

2. Find "Deploy Daily Readings Seeder" workflow

3. Click "Run workflow" → "Run workflow"

### Step 4: Verify

After deployment, check the function logs:

1. Go to Cloud Function logs:
   https://console.cloud.google.com/functions/details/us-central1/daily-readings-seeder?project=aisaiahconferencefb&tab=logs

2. Look for this message:
   ```
   ✅ Secondary Firebase credentials detected - will seed both projects
   ```

3. Manually trigger a test run:
   ```bash
   # Get function URL
   FUNCTION_URL=$(gcloud functions describe daily-readings-seeder \
     --gen2 --region=us-central1 --project=aisaiahconferencefb \
     --format="value(serviceConfig.uri)")
   
   # Test with one date
   curl "$FUNCTION_URL?start_date=2025-12-26&end_date=2025-12-26"
   ```

4. Check secondary Firestore:
   https://console.firebase.google.com/project/aisaiah-sfa-dev-app/firestore
   
   Look for document: `2025-12-26` in `daily_scripture` collection

## Quick Commands

```bash
# 1. Download key from console (manual step - see link above)

# 2. Set secret
gh secret set FIREBASE_CREDENTIALS_JSON_SECONDARY \
  --body "$(cat /path/to/downloaded-key.json)"

# 3. Trigger redeployment
gh workflow run "Deploy Daily Readings Seeder" --ref main

# 4. Check status
./check_daily_readings_cron.sh
```

## Expected Behavior After Fix

- Function logs will show: `✅ Secondary Firebase credentials detected - will seed both projects`
- Both Firebase databases will be updated on each run
- Primary: `aisaiahconferencefb`
- Secondary: `aisaiah-sfa-dev-app`

## Troubleshooting

If it still doesn't work after adding the secret:

1. **Check secret was set correctly:**
   ```bash
   gh secret list --repo aisaiah-ai/the_word_today_cron | grep FIREBASE
   ```

2. **Check deployment logs:**
   - Go to GitHub Actions
   - Check the latest "Deploy Daily Readings Seeder" run
   - Look for: `✅ Secondary Firebase credentials detected`

3. **Check function environment variables:**
   ```bash
   gcloud functions describe daily-readings-seeder \
     --gen2 --region=us-central1 --project=aisaiahconferencefb \
     --format="yaml(serviceConfig.environmentVariables)"
   ```
   
   Should show: `FIREBASE_CREDENTIALS_JSON_B64_SECONDARY`

4. **Check function logs for errors:**
   https://console.cloud.google.com/functions/details/us-central1/daily-readings-seeder?project=aisaiahconferencefb&tab=logs

