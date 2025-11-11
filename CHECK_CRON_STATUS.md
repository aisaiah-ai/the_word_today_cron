# How to Check if the Cron Job is Running Daily

This guide explains how to verify that your Cloud Scheduler cron jobs are running daily.

## Quick Check Script

Run the automated check script:

```bash
./check_cron_status.sh
```

This script will:
1. ✅ Check if Cloud Scheduler jobs exist
2. ✅ Show job status (ENABLED/PAUSED/DISABLED)
3. ✅ Display last execution time
4. ✅ Show recent function logs
5. ✅ Provide manual verification steps

## Manual Verification Steps

### 1. Check Cloud Scheduler Jobs

```bash
# List all scheduler jobs
gcloud scheduler jobs list --location=us-central1

# Check specific job status
gcloud scheduler jobs describe the-word-today-cron-4am-et --location=us-central1
gcloud scheduler jobs describe the-word-today-cron-6am-et --location=us-central1
```

**Expected Output:**
- Status should be `ENABLED`
- Schedule should show `0 9 * * *` (4 AM ET) or `0 11 * * *` (6 AM ET)
- `lastAttemptTime` should show recent execution times

### 2. Check Execution History

```bash
# View execution history for a job
gcloud scheduler jobs describe the-word-today-cron-4am-et \
  --location=us-central1 \
  --format="yaml(lastAttemptTime,state,schedule)"
```

### 3. Check Cloud Function Logs

```bash
# View recent function logs
gcloud functions logs read the-word-today-cron \
  --gen2 \
  --region=us-central1 \
  --limit=50

# Or check Cloud Run logs (Gen2 functions run on Cloud Run)
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=the-word-today-cron" \
  --limit=20 \
  --format=json
```

### 4. Check GCP Console

**Cloud Scheduler:**
- Go to: https://console.cloud.google.com/cloudscheduler?project=aisaiahconferencefb
- Look for jobs: `the-word-today-cron-4am-et` and `the-word-today-cron-6am-et`
- Check their status and execution history

**Cloud Function Logs:**
- Go to: https://console.cloud.google.com/functions/details/us-central1/the-word-today-cron?project=aisaiahconferencefb&tab=logs
- Look for recent executions around 4 AM and 6 AM ET

**Firestore Data:**
- Go to: https://console.cloud.google.com/firestore?project=aisaiahconferencefb
- Check the `daily_scripture` collection
- Verify documents are being updated daily with new video URLs

### 5. Manually Trigger the Function

Test if the function works by triggering it manually:

```bash
# Get function URL
FUNCTION_URL=$(gcloud functions describe the-word-today-cron \
  --gen2 \
  --region=us-central1 \
  --format="value(serviceConfig.uri)")

# Invoke function
curl "$FUNCTION_URL"

# Or trigger via scheduler
gcloud scheduler jobs run the-word-today-cron-4am-et --location=us-central1
```

## Troubleshooting

### Job Status is PAUSED or DISABLED

If a job is paused or disabled, it won't run:

```bash
# Enable the job
gcloud scheduler jobs resume the-word-today-cron-4am-et --location=us-central1
```

### No Execution History

If there's no execution history, check:

1. **Job was created recently** - Wait for the next scheduled time
2. **Job is enabled** - Check `state` field
3. **Function URL is accessible** - Verify function is deployed and public
4. **Permissions** - Ensure Cloud Scheduler has permission to invoke the function

### Function Errors

If the function is being triggered but failing:

1. Check Cloud Function logs for error messages
2. Verify environment variables are set correctly
3. Check Firebase credentials
4. Verify YouTube API key is valid

### Check Function Deployment

```bash
# Verify function exists
gcloud functions describe the-word-today-cron \
  --gen2 \
  --region=us-central1

# Check function URL
gcloud functions describe the-word-today-cron \
  --gen2 \
  --region=us-central1 \
  --format="value(serviceConfig.uri)"
```

## Expected Behavior

The cron jobs should:
- ✅ Run daily at 4 AM ET (09:00 UTC) and 6 AM ET (11:00 UTC)
- ✅ Update Firestore with video URLs for today and tomorrow
- ✅ Log successful executions in Cloud Function logs
- ✅ Show execution history in Cloud Scheduler

## Schedule Details

From `deploy.yml`:
- **4 AM ET Job**: `the-word-today-cron-4am-et`
  - Schedule: `0 9 * * *` (09:00 UTC)
  - Timezone: `America/New_York`
  
- **6 AM ET Job**: `the-word-today-cron-6am-et`
  - Schedule: `0 11 * * *` (11:00 UTC)
  - Timezone: `America/New_York`

## Quick Commands Reference

```bash
# Set project (if needed)
export GCP_PROJECT_ID=aisaiahconferencefb
gcloud config set project aisaiahconferencefb

# Run status check
./check_cron_status.sh

# List scheduler jobs
gcloud scheduler jobs list --location=us-central1 --filter="name~the-word-today-cron"

# View job details
gcloud scheduler jobs describe the-word-today-cron-4am-et --location=us-central1

# View recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=the-word-today-cron" --limit=10

# Manually trigger
gcloud scheduler jobs run the-word-today-cron-4am-et --location=us-central1
```

