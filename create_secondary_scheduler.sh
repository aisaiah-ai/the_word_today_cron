#!/bin/bash

# Script to create the secondary scheduler job manually

set -e

PROJECT="aisaiah-sfa-dev-app"
FUNCTION="daily-readings-seeder-secondary"
REGION="us-central1"
JOB_NAME="daily-readings-seeder-secondary-monthly-15th"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  Creating Secondary Scheduler Job                             ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Project: $PROJECT"
echo "Function: $FUNCTION"
echo "Job Name: $JOB_NAME"
echo ""

# Check if authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Not authenticated. Please run: gcloud auth login"
    exit 1
fi

# Set project
gcloud config set project "$PROJECT"

# Get function URL
echo "Getting function URL..."
FUNCTION_URL=$(gcloud functions describe "$FUNCTION" \
  --gen2 \
  --region="$REGION" \
  --format="value(serviceConfig.uri)" 2>/dev/null)

if [ -z "$FUNCTION_URL" ]; then
    echo "❌ Function not found!"
    echo "Check if function exists:"
    echo "  https://console.cloud.google.com/functions/list?project=$PROJECT"
    exit 1
fi

echo "✅ Function URL: $FUNCTION_URL"
echo ""

# Create scheduler job
echo "Creating scheduler job..."
gcloud scheduler jobs create http "$JOB_NAME" \
  --location="$REGION" \
  --schedule="0 7 15 * *" \
  --uri="$FUNCTION_URL" \
  --http-method=GET \
  --time-zone="America/New_York" \
  --description="Monthly seeding of daily readings on 15th - seeds days 1-30 of next month (SECONDARY)" \
  --attempt-deadline=600s \
  --project="$PROJECT" \
  2>&1 || {
    echo ""
    echo "Job might already exist, trying to update..."
    gcloud scheduler jobs update http "$JOB_NAME" \
      --location="$REGION" \
      --schedule="0 7 15 * *" \
      --uri="$FUNCTION_URL" \
      --http-method=GET \
      --time-zone="America/New_York" \
      --attempt-deadline=600s \
      --project="$PROJECT"
}

echo ""
echo "✅ Scheduler job created/updated!"
echo ""
echo "Verify in console:"
echo "  https://console.cloud.google.com/cloudscheduler?project=$PROJECT"
echo ""
echo "Job details:"
gcloud scheduler jobs describe "$JOB_NAME" \
  --location="$REGION" \
  --project="$PROJECT" \
  --format="table(name,schedule,timeZone,state,lastAttemptTime)"

