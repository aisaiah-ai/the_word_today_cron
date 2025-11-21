#!/bin/bash
# Trigger primary daily readings seeder for November 2025

PROJECT_ID="aisaiahconferencefb"
FUNCTION_NAME="daily-readings-seeder"
REGION="us-central1"
START_DATE="2025-11-01"
END_DATE="2025-11-30"

echo "🚀 Triggering PRIMARY seeder for November 2025..."
echo "Project: $PROJECT_ID"
echo "Function: $FUNCTION_NAME"
echo "Date range: $START_DATE to $END_DATE"
echo ""

# Get function URL
FUNCTION_URL=$(gcloud functions describe $FUNCTION_NAME \
  --gen2 \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format="value(serviceConfig.uri)" 2>/dev/null)

if [ -z "$FUNCTION_URL" ]; then
  echo "❌ Could not get function URL. Trying alternative method..."
  FUNCTION_URL="https://$REGION-$PROJECT_ID.cloudfunctions.net/$FUNCTION_NAME"
fi

echo "Function URL: $FUNCTION_URL"
echo ""

# Trigger with date parameters
curl -X POST \
  "$FUNCTION_URL?start_date=$START_DATE&end_date=$END_DATE" \
  -H "Authorization: bearer $(gcloud auth print-identity-token --project=$PROJECT_ID)" \
  -H "Content-Type: application/json" \
  -d '{}' \
  -v 2>&1 | grep -E "HTTP|success|error|✅|❌" || echo "Request sent"

echo ""
echo "✅ Primary seeder triggered!"
