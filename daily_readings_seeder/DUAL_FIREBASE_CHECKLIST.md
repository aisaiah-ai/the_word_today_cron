# Dual Firebase Setup Checklist

## ✅ What's Updated

All JSON keys and environment variables are now configured for dual Firebase support.

### Code Changes

- [x] `main.py` - Dual Firebase initialization (`_get_firebase_credentials`, `initialize_firebase`)
- [x] `main.py` - `seed_daily_reading()` accepts `project` parameter
- [x] `main.py` - `delete_old_readings()` accepts `project` parameter
- [x] `main.py` - Main cron function checks for secondary credentials
- [x] `main.py` - Seeds to both projects when secondary is enabled
- [x] `main.py` - Cleans up both projects when secondary is enabled
- [x] Workflow - Passes secondary credentials to Cloud Function

### Environment Variables

**Primary Firebase:**
- [x] `FIREBASE_CREDENTIALS_JSON` (JSON string)
- [x] `FIREBASE_CREDENTIALS_JSON_B64` (base64 encoded - used in deployment)
- [x] `FIREBASE_CRED` (file path for local dev)

**Secondary Firebase (Optional):**
- [x] `FIREBASE_CREDENTIALS_JSON_SECONDARY` (JSON string)
- [x] `FIREBASE_CREDENTIALS_JSON_B64_SECONDARY` (base64 encoded - used in deployment)
- [x] `FIREBASE_CRED_SECONDARY` (file path for local dev)
- [x] `FIREBASE_PROJECT_ID_SECONDARY` (project ID for Application Default Credentials)

### GitHub Workflow

**File:** `.github/workflows/deploy-daily-readings-seeder.yml`

- [x] Encodes primary Firebase credentials to base64
- [x] Checks for `FIREBASE_CREDENTIALS_JSON_SECONDARY` secret
- [x] Encodes secondary Firebase credentials to base64 (if present)
- [x] Builds `ENV_VARS` string with both credentials
- [x] Passes both credentials to Cloud Function via `--set-env-vars`

## How to Enable Secondary Firebase

### Step 1: Add GitHub Secret

```bash
# Option A: Using service account key
gh secret set FIREBASE_CREDENTIALS_JSON_SECONDARY --body "$(cat secondary-firebase-key.json)"

# Option B: Using project ID only
gh secret set FIREBASE_PROJECT_ID_SECONDARY --body "your-secondary-project-id"
```

### Step 2: Deploy

```bash
# Merge branch or push to main
git checkout main
git merge seed_two_accounts
git push origin main
```

GitHub Actions will automatically deploy with secondary Firebase support.

### Step 3: Verify

Check the deployment logs:

```bash
# In GitHub Actions logs, look for:
✅ Secondary Firebase credentials detected - will seed both projects

# In Cloud Function logs, look for:
✅ Secondary Firebase initialized
🗑️  Deleting readings older than... from secondary
```

## How to Disable Secondary Firebase

Simply remove the GitHub secret:

```bash
gh secret delete FIREBASE_CREDENTIALS_JSON_SECONDARY
# or
gh secret delete FIREBASE_PROJECT_ID_SECONDARY
```

Next deployment will automatically skip secondary seeding.

## Testing Before Merge

Test the function locally with dual Firebase:

```bash
# Set environment variables
export FIREBASE_CRED=/path/to/primary-key.json
export FIREBASE_CRED_SECONDARY=/path/to/secondary-key.json
export DRY_RUN=True

# Run function
cd daily_readings_seeder
python3 main.py
```

Look for:
```
✅ Primary Firebase initialized
✅ Secondary Firebase initialized
🗑️  Deleting readings older than... from primary
🗑️  Deleting readings older than... from secondary
```

## Current Status

**Branch:** `seed_two_accounts`

**Ready to merge:** ✅ Yes

All JSON keys are properly configured:
- Primary credentials: `FIREBASE_CREDENTIALS_JSON_B64`
- Secondary credentials: `FIREBASE_CREDENTIALS_JSON_B64_SECONDARY` (optional)
- Workflow passes both to Cloud Function
- Function detects and uses secondary automatically

**Default behavior:** Seeds to primary only (backward compatible)

**When secondary is added:** Automatically seeds to both projects

