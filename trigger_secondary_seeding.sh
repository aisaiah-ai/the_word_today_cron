#!/bin/bash

# Script to trigger secondary Firebase seeding
# Seeds daily readings for December 2025 (days 1-30)

set -e

PROJECT="aisaiah-sfa-dev-app"
FUNCTION="daily-readings-seeder-secondary"
REGION="us-central1"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  Triggering Secondary Firebase Seeding                       ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Project: $PROJECT"
echo "Function: $FUNCTION"
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
    echo "❌ Function not found or not accessible"
    echo ""
    echo "Check if function exists:"
    echo "  https://console.cloud.google.com/functions/list?project=$PROJECT"
    exit 1
fi

echo "✅ Function URL: $FUNCTION_URL"
echo ""

# Trigger seeding for December 2025
echo "Triggering seeding for December 2025 (days 1-30)..."
echo ""

curl -X GET "$FUNCTION_URL?start_date=2025-12-01&end_date=2025-12-30" \
  -H "Content-Type: application/json" \
  -w "\n\nHTTP Status: %{http_code}\n" \
  2>&1

echo ""
echo "✅ Seeding triggered!"
echo ""
echo "Check Firestore to verify data:"
echo "  https://console.firebase.google.com/project/$PROJECT/firestore"
echo ""
echo "Look for documents: 2025-12-01 through 2025-12-30"
echo "Collection: daily_scripture"

