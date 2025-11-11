# Get Secondary Firebase Service Account Key

## Issue

The `firebase-adminsdk` service account in the secondary project (`aisaiah-sfa-dev-app`) has key creation disabled by organizational policy.

## Solution: Download from Firebase Console

### Step 1: Go to Firebase Console

1. Visit: https://console.firebase.google.com/
2. Select project: **AIsaiah SFA Dev** (aisaiah-sfa-dev-app)

### Step 2: Generate Service Account Key

1. Click on **Project Settings** (gear icon)
2. Go to **Service Accounts** tab
3. Click **Generate New Private Key**
4. Save the JSON file as: `/Users/acthercop/.keys/aisaiah-sfa-dev-app-firebase-key.json`

### Step 3: Add to GitHub Secrets

```bash
# Base64 encode and add to GitHub secrets
gh secret set FIREBASE_CREDENTIALS_JSON_SECONDARY \
  --body "$(cat /Users/acthercop/.keys/aisaiah-sfa-dev-app-firebase-key.json)"
```

### Step 4: Deploy

The workflow will automatically encode it to base64 and pass it to the Cloud Function.

```bash
git push origin main
```

## Alternative: Use Existing Method

If you already have the secondary Firebase key downloaded:

```bash
# Find existing secondary Firebase key
ls -la /Users/acthercop/.keys/ | grep -i "sfa\|dev"

# If found, use it
gh secret set FIREBASE_CREDENTIALS_JSON_SECONDARY \
  --body "$(cat /path/to/secondary-firebase-key.json)"
```

## Verify It's Working

After deployment, test the function:

```bash
curl "https://daily-readings-seeder-lwvp6j7v6q-uc.a.run.app?start_date=2025-12-25&end_date=2025-12-25"
```

Look for:
```json
{
  "firebase_projects": ["primary", "secondary"]
}
```

Check logs for:
```
✅ Secondary Firebase credentials detected
✅ Secondary Firebase initialized
```

## Quick Test (Local)

If you have the key file, test locally:

```bash
export FIREBASE_CRED=/Users/acthercop/.keys/aisaiahconferencefb-firebase-adminsdk-fbsvc-ed4ace66d0.json
export FIREBASE_CRED_SECONDARY=/path/to/secondary-key.json
export DRY_RUN=True

cd daily_readings_seeder
python3 -c "from main import initialize_firebase; initialize_firebase('primary'); initialize_firebase('secondary'); print('✅ Both Firebase instances initialized')"
```

