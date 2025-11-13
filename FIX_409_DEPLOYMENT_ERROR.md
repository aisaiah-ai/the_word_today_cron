# Fix: 409 Deployment Conflict Error

## Problem
```
ERROR: (gcloud.functions.deploy) ResponseError: status=[409], code=[Ok], message=[unable to queue the operation]
```

## Root Cause
A 409 conflict error means:
1. **Another deployment is in progress** - Cloud Functions can only have one deployment at a time
2. **Function is being updated/deleted** by another process
3. **Resource lock** - GCP has locked the function resource

## Solution

### Option 1: Wait and Retry (Recommended)
1. Wait 2-5 minutes for any in-progress deployments to complete
2. Check GitHub Actions: https://github.com/aisaiah-ai/the_word_today_cron/actions
3. Look for any "in progress" deployments
4. Once they complete, re-run the workflow

### Option 2: Cancel Conflicting Deployments
1. Go to Cloud Functions console:
   - Primary: https://console.cloud.google.com/functions/list?project=aisaiahconferencefb
   - Secondary: https://console.cloud.google.com/functions/list?project=aisaiah-sfa-dev-app
2. Check if any functions show "Deploying" status
3. Wait for them to complete

### Option 3: Manual Retry via GitHub Actions
1. Go to: https://github.com/aisaiah-ai/the_word_today_cron/actions
2. Find the failed workflow run
3. Click "Re-run failed jobs"

### Option 4: Check for Multiple Workflows Running
The error might be from the OLD workflow (`deploy.yml` deploying `the-word-today-cron`).

**Check which workflows are running:**
```bash
gh run list --repo aisaiah-ai/the_word_today_cron --limit=10
```

**For secondary Firebase, we need:**
- Workflow: "Deploy Daily Readings Seeder (Secondary Firebase)"
- Function: `daily-readings-seeder-secondary`
- Project: `aisaiah-sfa-dev-app`

## Verify Secondary Deployment

### Check if Secondary Function Exists
```bash
gcloud functions describe daily-readings-seeder-secondary \
  --gen2 --region=us-central1 \
  --project=aisaiah-sfa-dev-app
```

### Check Secondary Scheduler
```bash
gcloud scheduler jobs describe daily-readings-seeder-secondary-monthly-15th \
  --location=us-central1 \
  --project=aisaiah-sfa-dev-app
```

### Check Function Logs
```bash
gcloud functions logs read daily-readings-seeder-secondary \
  --gen2 --region=us-central1 \
  --project=aisaiah-sfa-dev-app \
  --limit=20
```

## Expected Behavior After Fix

Once the secondary function deploys successfully:
1. ✅ Function will be at: `daily-readings-seeder-secondary` in `aisaiah-sfa-dev-app`
2. ✅ Scheduler will be: `daily-readings-seeder-secondary-monthly-15th`
3. ✅ Function uses Application Default Credentials (no keys needed)
4. ✅ Will seed secondary Firebase automatically on 15th of each month

## Prevention

To avoid 409 errors:
1. **Don't trigger multiple deployments simultaneously**
2. **Wait for one deployment to complete before starting another**
3. **Use workflow_dispatch for manual triggers** instead of pushing multiple times quickly

## Quick Fix Command

If you need to force a fresh deployment:

```bash
# 1. Wait for any in-progress deployments (check console)

# 2. Re-run the workflow via GitHub Actions UI, OR:

# 3. Trigger manually via GitHub CLI:
gh workflow run "Deploy Daily Readings Seeder (Secondary Firebase)" --ref main
```

