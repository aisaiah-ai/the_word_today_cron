#!/bin/bash

# Script to check if the daily readings seeder cron jobs are running
# Checks both primary and secondary Cloud Scheduler jobs

set +e

# Configuration
PRIMARY_FUNCTION="daily-readings-seeder"
SECONDARY_FUNCTION="daily-readings-seeder-secondary"
PRIMARY_PROJECT="aisaiahconferencefb"
SECONDARY_PROJECT="aisaiah-sfa-dev-app"
REGION="us-central1"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Daily Readings Seeder - Cron Job Status Check              ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | grep -q .; then
    echo -e "${YELLOW}⚠️  gcloud authentication expired or not configured${NC}"
    echo ""
    echo "To authenticate, run:"
    echo "  gcloud auth login"
    echo ""
    echo "Or check status via GCP Console (links below)"
    echo ""
    SKIP_CLI=true
else
    SKIP_CLI=false
fi

if [ "$SKIP_CLI" = false ]; then
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}PRIMARY PROJECT: ${PRIMARY_PROJECT}${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    # Check primary scheduler
    PRIMARY_JOB="${PRIMARY_FUNCTION}-monthly-15th"
    echo "Checking scheduler job: ${PRIMARY_JOB}"
    
    gcloud config set project "$PRIMARY_PROJECT" 2>/dev/null
    
    PRIMARY_STATUS=$(gcloud scheduler jobs describe "$PRIMARY_JOB" \
        --location="$REGION" \
        --project="$PRIMARY_PROJECT" \
        --format="value(state)" 2>/dev/null || echo "NOT_FOUND")
    
    if [ "$PRIMARY_STATUS" = "ENABLED" ]; then
        echo -e "${GREEN}✅ Status: ENABLED${NC}"
        
        LAST_ATTEMPT=$(gcloud scheduler jobs describe "$PRIMARY_JOB" \
            --location="$REGION" \
            --project="$PRIMARY_PROJECT" \
            --format="value(lastAttemptTime)" 2>/dev/null || echo "")
        
        if [ -n "$LAST_ATTEMPT" ]; then
            echo -e "${GREEN}Last execution: ${LAST_ATTEMPT}${NC}"
        else
            echo -e "${YELLOW}⚠️  No execution history yet${NC}"
        fi
        
        SCHEDULE=$(gcloud scheduler jobs describe "$PRIMARY_JOB" \
            --location="$REGION" \
            --project="$PRIMARY_PROJECT" \
            --format="value(schedule)" 2>/dev/null || echo "")
        echo "Schedule: ${SCHEDULE} (15th of each month at 2 AM ET)"
        
    elif [ "$PRIMARY_STATUS" = "NOT_FOUND" ]; then
        echo -e "${RED}❌ Scheduler job not found!${NC}"
        echo "   The job may not have been created yet."
    elif [ "$PRIMARY_STATUS" = "PAUSED" ]; then
        echo -e "${RED}❌ Status: PAUSED (Job is paused and won't run)${NC}"
    elif [ "$PRIMARY_STATUS" = "DISABLED" ]; then
        echo -e "${RED}❌ Status: DISABLED (Job is disabled and won't run)${NC}"
    else
        echo -e "${YELLOW}⚠️  Status: ${PRIMARY_STATUS}${NC}"
    fi
    
    # Check primary function
    echo ""
    echo "Checking Cloud Function: ${PRIMARY_FUNCTION}"
    PRIMARY_FUNC_STATE=$(gcloud functions describe "$PRIMARY_FUNCTION" \
        --gen2 \
        --region="$REGION" \
        --project="$PRIMARY_PROJECT" \
        --format="value(state)" 2>/dev/null || echo "NOT_FOUND")
    
    if [ "$PRIMARY_FUNC_STATE" = "ACTIVE" ]; then
        echo -e "${GREEN}✅ Function: ACTIVE${NC}"
    else
        echo -e "${YELLOW}⚠️  Function state: ${PRIMARY_FUNC_STATE}${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}SECONDARY PROJECT: ${SECONDARY_PROJECT}${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    # Check secondary scheduler
    SECONDARY_JOB="${SECONDARY_FUNCTION}-monthly-15th"
    echo "Checking scheduler job: ${SECONDARY_JOB}"
    
    gcloud config set project "$SECONDARY_PROJECT" 2>/dev/null
    
    SECONDARY_STATUS=$(gcloud scheduler jobs describe "$SECONDARY_JOB" \
        --location="$REGION" \
        --project="$SECONDARY_PROJECT" \
        --format="value(state)" 2>/dev/null || echo "NOT_FOUND")
    
    if [ "$SECONDARY_STATUS" = "ENABLED" ]; then
        echo -e "${GREEN}✅ Status: ENABLED${NC}"
        
        LAST_ATTEMPT=$(gcloud scheduler jobs describe "$SECONDARY_JOB" \
            --location="$REGION" \
            --project="$SECONDARY_PROJECT" \
            --format="value(lastAttemptTime)" 2>/dev/null || echo "")
        
        if [ -n "$LAST_ATTEMPT" ]; then
            echo -e "${GREEN}Last execution: ${LAST_ATTEMPT}${NC}"
        else
            echo -e "${YELLOW}⚠️  No execution history yet${NC}"
        fi
        
        SCHEDULE=$(gcloud scheduler jobs describe "$SECONDARY_JOB" \
            --location="$REGION" \
            --project="$SECONDARY_PROJECT" \
            --format="value(schedule)" 2>/dev/null || echo "")
        echo "Schedule: ${SCHEDULE} (15th of each month at 2 AM ET)"
        
    elif [ "$SECONDARY_STATUS" = "NOT_FOUND" ]; then
        echo -e "${YELLOW}⚠️  Scheduler job not found${NC}"
        echo "   Secondary deployment may not be set up yet."
    elif [ "$SECONDARY_STATUS" = "PAUSED" ]; then
        echo -e "${RED}❌ Status: PAUSED (Job is paused and won't run)${NC}"
    elif [ "$SECONDARY_STATUS" = "DISABLED" ]; then
        echo -e "${RED}❌ Status: DISABLED (Job is disabled and won't run)${NC}"
    else
        echo -e "${YELLOW}⚠️  Status: ${SECONDARY_STATUS}${NC}"
    fi
    
    # Check secondary function
    echo ""
    echo "Checking Cloud Function: ${SECONDARY_FUNCTION}"
    SECONDARY_FUNC_STATE=$(gcloud functions describe "$SECONDARY_FUNCTION" \
        --gen2 \
        --region="$REGION" \
        --project="$SECONDARY_PROJECT" \
        --format="value(state)" 2>/dev/null || echo "NOT_FOUND")
    
    if [ "$SECONDARY_FUNC_STATE" = "ACTIVE" ]; then
        echo -e "${GREEN}✅ Function: ACTIVE${NC}"
    else
        echo -e "${YELLOW}⚠️  Function state: ${SECONDARY_FUNC_STATE}${NC}"
    fi
fi

echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  GCP Console Links (Check Manually)                         ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}PRIMARY PROJECT (${PRIMARY_PROJECT}):${NC}"
echo "  Cloud Scheduler:"
echo "    https://console.cloud.google.com/cloudscheduler?project=${PRIMARY_PROJECT}"
echo ""
echo "  Cloud Function:"
echo "    https://console.cloud.google.com/functions/details/${REGION}/${PRIMARY_FUNCTION}?project=${PRIMARY_PROJECT}"
echo ""
echo "  Function Logs:"
echo "    https://console.cloud.google.com/functions/details/${REGION}/${PRIMARY_FUNCTION}?project=${PRIMARY_PROJECT}&tab=logs"
echo ""
echo "  Firestore (verify data):"
echo "    https://console.firebase.google.com/project/${PRIMARY_PROJECT}/firestore"
echo ""

echo -e "${BLUE}SECONDARY PROJECT (${SECONDARY_PROJECT}):${NC}"
echo "  Cloud Scheduler:"
echo "    https://console.cloud.google.com/cloudscheduler?project=${SECONDARY_PROJECT}"
echo ""
echo "  Cloud Function:"
echo "    https://console.cloud.google.com/functions/details/${REGION}/${SECONDARY_FUNCTION}?project=${SECONDARY_PROJECT}"
echo ""
echo "  Function Logs:"
echo "    https://console.cloud.google.com/functions/details/${REGION}/${SECONDARY_FUNCTION}?project=${SECONDARY_PROJECT}&tab=logs"
echo ""
echo "  Firestore (verify data):"
echo "    https://console.firebase.google.com/project/${SECONDARY_PROJECT}/firestore"
echo ""

echo -e "${BLUE}GitHub Actions (Check Deployment Status):${NC}"
echo "  https://github.com/aisaiah-ai/the_word_today_cron/actions"
echo ""

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  What to Check in Console                                    ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "1. ✅ Scheduler Job Status:"
echo "   - Should be ENABLED (not PAUSED or DISABLED)"
echo "   - Schedule: '0 7 15 * *' (15th of month at 2 AM ET)"
echo "   - Check 'Last execution' - should show recent runs"
echo ""
echo "2. ✅ Function Status:"
echo "   - Should be ACTIVE"
echo "   - Check logs for errors"
echo ""
echo "3. ✅ Firestore Data:"
echo "   - Check 'daily_scripture' collection"
echo "   - Should have documents for dates (format: YYYY-MM-DD)"
echo "   - Should include responsorial_psalm fields"
echo ""
echo "4. ✅ Next Run Date:"
echo "   - Should run on the 15th of each month"
echo "   - Seeds days 1-30 of the NEXT month"
echo ""

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Troubleshooting                                              ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "If scheduler is PAUSED or DISABLED:"
echo "  gcloud scheduler jobs resume ${PRIMARY_JOB} --location=${REGION} --project=${PRIMARY_PROJECT}"
echo ""
echo "If scheduler job doesn't exist:"
echo "  Check GitHub Actions deployment logs"
echo "  Re-run deployment workflow if needed"
echo ""
echo "To manually trigger a test run:"
echo "  gcloud scheduler jobs run ${PRIMARY_JOB} --location=${REGION} --project=${PRIMARY_PROJECT}"
echo ""


