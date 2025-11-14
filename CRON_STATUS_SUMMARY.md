# Daily Readings Seeder - Cron Job Status

## Current Status (as of check)

### Primary Project (aisaiahconferencefb)
- **Deployment**: ✅ SUCCESS (Nov 12, 01:46 UTC)
- **Function**: `daily-readings-seeder`
- **Scheduler**: `daily-readings-seeder-monthly-15th`
- **Schedule**: 15th of each month at 2 AM ET (7 AM UTC)
- **Status**: Check via console (gcloud auth expired)

**Console Links:**
- Scheduler: https://console.cloud.google.com/cloudscheduler?project=aisaiahconferencefb
- Function: https://console.cloud.google.com/functions/details/us-central1/daily-readings-seeder?project=aisaiahconferencefb
- Logs: https://console.cloud.google.com/functions/details/us-central1/daily-readings-seeder?project=aisaiahconferencefb&tab=logs
- Firestore: https://console.firebase.google.com/project/aisaiahconferencefb/firestore

### Secondary Project (aisaiah-sfa-dev-app)
- **Deployment**: ❌ FAILED (Nov 12, 01:46 UTC)
- **Function**: `daily-readings-seeder-secondary`
- **Scheduler**: `daily-readings-seeder-secondary-monthly-15th`
- **Status**: Deployment failed - needs investigation

**Console Links:**
- Scheduler: https://console.cloud.google.com/cloudscheduler?project=aisaiah-sfa-dev-app
- Function: https://console.cloud.google.com/functions/details/us-central1/daily-readings-seeder-secondary?project=aisaiah-sfa-dev-app
- Logs: https://console.cloud.google.com/functions/details/us-central1/daily-readings-seeder-secondary?project=aisaiah-sfa-dev-app&tab=logs
- Firestore: https://console.firebase.google.com/project/aisaiah-sfa-dev-app/firestore

## How to Check Status

### Option 1: Use the Check Script
```bash
./check_daily_readings_cron.sh
```
(Note: Requires `gcloud auth login` first)

### Option 2: Check GCP Console
Use the links above to check:
1. **Scheduler Status**: Should be ENABLED
2. **Last Execution**: Should show recent runs
3. **Function Status**: Should be ACTIVE
4. **Logs**: Check for errors

### Option 3: Check GitHub Actions
https://github.com/aisaiah-ai/the_word_today_cron/actions

## Troubleshooting

### If Primary Cron Not Running

1. **Check Scheduler Status**:
   - Go to Cloud Scheduler console
   - Verify job is ENABLED (not PAUSED/DISABLED)
   - Check "Last execution" time

2. **Check Function Logs**:
   - Look for errors in function execution
   - Verify Firebase credentials are valid
   - Check for API errors (USCCB, bible-api.com)

3. **Manually Trigger**:
   ```bash
   gcloud scheduler jobs run daily-readings-seeder-monthly-15th \
     --location=us-central1 \
     --project=aisaiahconferencefb
   ```

### If Secondary Deployment Failed

1. **Check GitHub Actions Logs**:
   - Find the failed workflow run
   - Look for error messages
   - Common issues:
     * Missing GitHub secrets
     * Workload Identity Federation not configured
     * Service account permissions

2. **Re-run Deployment**:
   - Go to GitHub Actions
   - Find "Deploy Daily Readings Seeder (Secondary Firebase)"
   - Click "Re-run failed jobs"

3. **Verify Workload Identity Setup**:
   - Check if Workload Identity Pool exists
   - Verify GitHub secrets are set:
     * WORKLOAD_IDENTITY_PROVIDER_SECONDARY
     * SERVICE_ACCOUNT_SECONDARY
     * GCP_PROJECT_ID_SECONDARY

## Expected Behavior

- **Schedule**: Runs on the 15th of each month at 2 AM ET
- **Action**: Seeds days 1-30 of the NEXT month
- **Data**: Creates/updates documents in `daily_scripture` collection
- **Fields**: Includes responsorial_psalm, responsorial_psalm_verse, responsorial_psalm_response

## Next Run Date

The cron runs on the **15th of each month**. 
- If today is before the 15th: Next run is this month's 15th
- If today is after the 15th: Next run is next month's 15th

Example: If today is Nov 12, 2025:
- Next run: Nov 15, 2025 at 2 AM ET
- Will seed: December 1-30, 2025

