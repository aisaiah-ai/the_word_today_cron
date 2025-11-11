#!/bin/bash

# Script to check if the cron job is running daily
# This checks Cloud Scheduler jobs and their execution history

# Don't exit on error - we want to show all checks even if some fail
set +e

# Configuration
FUNCTION_NAME="the-word-today-cron"
REGION="us-central1"
# Try to get project ID from terraform config, then env var, then gcloud config
if [ -f "terraform/terraform.tfvars" ]; then
    TERRAFORM_PROJECT=$(grep -E "^project_id\s*=" terraform/terraform.tfvars | head -1 | sed 's/.*= *"\(.*\)".*/\1/' | tr -d ' ')
    if [ -n "$TERRAFORM_PROJECT" ]; then
        DEFAULT_PROJECT="$TERRAFORM_PROJECT"
    fi
fi
PROJECT_ID="${GCP_PROJECT_ID:-${DEFAULT_PROJECT:-}}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Checking Cron Job Status${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Error: gcloud CLI is not installed${NC}"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${YELLOW}⚠️  Warning: Not authenticated to GCP${NC}"
    echo "Running: gcloud auth login"
    gcloud auth login
fi

# Set project if provided and different from current
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
if [ -n "$PROJECT_ID" ] && [ "$PROJECT_ID" != "$CURRENT_PROJECT" ]; then
    echo -e "${BLUE}Setting GCP project to: ${PROJECT_ID}${NC}"
    gcloud config set project "$PROJECT_ID" 2>/dev/null || {
        echo -e "${YELLOW}⚠️  Could not set project (auth may be expired)${NC}"
    }
elif [ -z "$PROJECT_ID" ]; then
    PROJECT_ID="$CURRENT_PROJECT"
    if [ -z "$PROJECT_ID" ]; then
        echo -e "${RED}❌ Error: GCP_PROJECT_ID not set and no default project configured${NC}"
        echo "Please set GCP_PROJECT_ID environment variable or run: gcloud config set project YOUR_PROJECT_ID"
        exit 1
    fi
fi

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Error: Could not determine GCP project${NC}"
    exit 1
fi

echo -e "${BLUE}Using GCP project: ${PROJECT_ID}${NC}"

# Test authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | grep -q .; then
    echo -e "${RED}❌ Error: Not authenticated to GCP${NC}"
    echo ""
    echo "Please authenticate first:"
    echo "  gcloud auth login"
    echo ""
    echo "Or if using a service account:"
    echo "  gcloud auth activate-service-account --key-file=path/to/key.json"
    exit 1
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}1. Checking Cloud Scheduler Jobs${NC}"
echo -e "${BLUE}========================================${NC}"

# List scheduler jobs
JOBS=$(gcloud scheduler jobs list --location="$REGION" --filter="name~$FUNCTION_NAME" --format="value(name)" 2>/dev/null || echo "")

if [ -z "$JOBS" ]; then
    echo -e "${RED}❌ No scheduler jobs found for ${FUNCTION_NAME}${NC}"
    echo ""
    echo "This could mean:"
    echo "  1. The deployment workflow hasn't run yet"
    echo "  2. The scheduler jobs failed to create"
    echo "  3. The function name doesn't match"
    echo ""
    echo "To fix:"
    echo "  1. Check GitHub Actions deployment logs"
    echo "  2. Manually create scheduler jobs (see deploy.yml)"
    exit 1
fi

echo -e "${GREEN}✅ Found scheduler jobs:${NC}"
gcloud scheduler jobs list --location="$REGION" --filter="name~$FUNCTION_NAME" --format="table(name,schedule,timeZone,state,lastAttemptTime)"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}2. Checking Job Execution History${NC}"
echo -e "${BLUE}========================================${NC}"

# Check each job's execution history
for JOB_NAME in $JOBS; do
    echo ""
    echo -e "${YELLOW}Job: ${JOB_NAME}${NC}"
    echo "----------------------------------------"
    
    # Get job details
    JOB_STATE=$(gcloud scheduler jobs describe "$JOB_NAME" --location="$REGION" --format="value(state)" 2>/dev/null || echo "UNKNOWN")
    
    if [ "$JOB_STATE" = "ENABLED" ]; then
        echo -e "${GREEN}✅ Status: ENABLED${NC}"
    elif [ "$JOB_STATE" = "PAUSED" ]; then
        echo -e "${RED}❌ Status: PAUSED (Job is paused and won't run)${NC}"
    elif [ "$JOB_STATE" = "DISABLED" ]; then
        echo -e "${RED}❌ Status: DISABLED (Job is disabled and won't run)${NC}"
    else
        echo -e "${YELLOW}⚠️  Status: ${JOB_STATE}${NC}"
    fi
    
    # Get last execution time
    LAST_ATTEMPT=$(gcloud scheduler jobs describe "$JOB_NAME" --location="$REGION" --format="value(lastAttemptTime)" 2>/dev/null || echo "")
    if [ -n "$LAST_ATTEMPT" ]; then
        echo -e "${GREEN}Last execution: ${LAST_ATTEMPT}${NC}"
    else
        echo -e "${YELLOW}⚠️  No execution history found${NC}"
    fi
    
    # Get schedule
    SCHEDULE=$(gcloud scheduler jobs describe "$JOB_NAME" --location="$REGION" --format="value(schedule)" 2>/dev/null || echo "")
    if [ -n "$SCHEDULE" ]; then
        echo "Schedule: ${SCHEDULE}"
    fi
    
    # Get timezone
    TIMEZONE=$(gcloud scheduler jobs describe "$JOB_NAME" --location="$REGION" --format="value(timeZone)" 2>/dev/null || echo "")
    if [ -n "$TIMEZONE" ]; then
        echo "Timezone: ${TIMEZONE}"
    fi
done

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}3. Checking Cloud Function Logs (Last 24h)${NC}"
echo -e "${BLUE}========================================${NC}"

# Check Cloud Run logs (Gen2 functions run on Cloud Run)
echo "Fetching recent function execution logs..."
# Gen2 functions use Cloud Run, so we check Cloud Run logs
CLOUD_RUN_LOGS=$(gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=$FUNCTION_NAME" \
  --limit=20 \
  --format="table(timestamp,severity,textPayload)" \
  --project="$PROJECT_ID" 2>/dev/null || echo "")

if [ -n "$CLOUD_RUN_LOGS" ] && [ "$CLOUD_RUN_LOGS" != "" ]; then
    echo "$CLOUD_RUN_LOGS"
else
    echo -e "${YELLOW}⚠️  No recent logs found${NC}"
    echo ""
    echo "This could mean:"
    echo "  1. The function hasn't been invoked recently"
    echo "  2. Logs might be in a different format"
    echo ""
    echo "Try checking logs in GCP Console:"
    echo "  https://console.cloud.google.com/functions/details/${REGION}/${FUNCTION_NAME}?project=${PROJECT_ID}&tab=logs"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}4. Manual Verification Steps${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "To verify the cron is running daily:"
echo ""
echo "1. Check Cloud Scheduler in GCP Console:"
echo "   https://console.cloud.google.com/cloudscheduler?project=${PROJECT_ID}"
echo ""
echo "2. Check Cloud Function logs:"
echo "   https://console.cloud.google.com/functions/details/${REGION}/${FUNCTION_NAME}?project=${PROJECT_ID}&tab=logs"
echo ""
echo "3. Manually trigger the function to test:"
FUNCTION_URL=$(gcloud functions describe "$FUNCTION_NAME" --gen2 --region="$REGION" --format="value(serviceConfig.uri)" 2>/dev/null || echo "")
if [ -n "$FUNCTION_URL" ]; then
    echo "   curl $FUNCTION_URL"
    echo ""
    echo "   Or use gcloud:"
    echo "   gcloud scheduler jobs run ${FUNCTION_NAME}-4am-et --location=$REGION"
fi
echo ""
echo "4. Check Firestore to see if data is being updated:"
echo "   https://console.cloud.google.com/firestore?project=${PROJECT_ID}"
echo "   Look for documents in the 'daily_scripture' collection"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Check Complete!${NC}"
echo -e "${BLUE}========================================${NC}"

