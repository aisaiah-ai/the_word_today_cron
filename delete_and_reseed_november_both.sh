#!/bin/bash
# Delete all November 2025 documents from BOTH primary and secondary Firebase, then reseed

set -e

PRIMARY_PROJECT="aisaiahconferencefb"
SECONDARY_PROJECT="aisaiah-sfa-dev-app"
COLLECTION="daily_scripture"
FUNCTION_NAME_PRIMARY="daily-readings-seeder"
FUNCTION_NAME_SECONDARY="daily-readings-seeder-secondary"
REGION="us-central1"
START_DATE="2025-11-01"
END_DATE="2025-11-30"

echo "═══════════════════════════════════════════════════════════"
echo "🗑️  DELETING ALL NOVEMBER 2025 DOCUMENTS"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Delete from PRIMARY Firebase
echo "🔵 PRIMARY PROJECT: $PRIMARY_PROJECT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
for day in {1..30}; do
  date_str=$(printf "2025-11-%02d" $day)
  echo -n "Deleting $date_str from primary... "
  gcloud firestore documents delete "projects/$PRIMARY_PROJECT/databases/(default)/documents/$COLLECTION/$date_str" \
    --project=$PRIMARY_PROJECT \
    --quiet 2>&1 | grep -q "NOT_FOUND" && echo "⏭️  (not found)" || echo "✅ deleted"
done
echo ""

# Delete from SECONDARY Firebase
echo "🟢 SECONDARY PROJECT: $SECONDARY_PROJECT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
for day in {1..30}; do
  date_str=$(printf "2025-11-%02d" $day)
  echo -n "Deleting $date_str from secondary... "
  gcloud firestore documents delete "projects/$SECONDARY_PROJECT/databases/(default)/documents/$COLLECTION/$date_str" \
    --project=$SECONDARY_PROJECT \
    --quiet 2>&1 | grep -q "NOT_FOUND" && echo "⏭️  (not found)" || echo "✅ deleted"
done
echo ""

echo "═══════════════════════════════════════════════════════════"
echo "✅ DELETION COMPLETE!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Waiting 5 seconds before reseeding..."
sleep 5
echo ""

echo "═══════════════════════════════════════════════════════════"
echo "🌱 RESEEDING NOVEMBER 2025"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Reseed PRIMARY Firebase
echo "🔵 TRIGGERING PRIMARY SEEDER"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Project: $PRIMARY_PROJECT"
echo "Function: $FUNCTION_NAME_PRIMARY"
echo "Date range: $START_DATE to $END_DATE"
echo ""

# Get function URL for primary
FUNCTION_URL_PRIMARY=$(gcloud functions describe $FUNCTION_NAME_PRIMARY \
  --gen2 \
  --region=$REGION \
  --project=$PRIMARY_PROJECT \
  --format="value(serviceConfig.uri)" 2>/dev/null)

if [ -z "$FUNCTION_URL_PRIMARY" ]; then
  echo "⚠️  Could not get function URL. Using default URL format..."
  FUNCTION_URL_PRIMARY="https://$REGION-$PRIMARY_PROJECT.cloudfunctions.net/$FUNCTION_NAME_PRIMARY"
fi

echo "Function URL: $FUNCTION_URL_PRIMARY"
echo ""
echo "Sending request..."

curl -X POST \
  "$FUNCTION_URL_PRIMARY?start_date=$START_DATE&end_date=$END_DATE" \
  -H "Authorization: bearer $(gcloud auth print-identity-token --project=$PRIMARY_PROJECT)" \
  -H "Content-Type: application/json" \
  -d '{}' \
  -w "\nHTTP Status: %{http_code}\n" \
  2>&1 | grep -E "HTTP|successful|status|✅|❌|error" || echo "Request sent to primary"

echo ""
echo "✅ Primary seeder triggered!"
echo ""

# Reseed SECONDARY Firebase
echo "🟢 TRIGGERING SECONDARY SEEDER"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Project: $SECONDARY_PROJECT"
echo "Function: $FUNCTION_NAME_SECONDARY"
echo "Date range: $START_DATE to $END_DATE"
echo ""

# Get function URL for secondary
FUNCTION_URL_SECONDARY=$(gcloud functions describe $FUNCTION_NAME_SECONDARY \
  --gen2 \
  --region=$REGION \
  --project=$SECONDARY_PROJECT \
  --format="value(serviceConfig.uri)" 2>/dev/null)

if [ -z "$FUNCTION_URL_SECONDARY" ]; then
  echo "⚠️  Could not get function URL. Trying alternative method..."
  # Try to get from Cloud Run
  FUNCTION_URL_SECONDARY=$(gcloud run services describe $FUNCTION_NAME_SECONDARY \
    --region=$REGION \
    --project=$SECONDARY_PROJECT \
    --format="value(status.url)" 2>/dev/null)
fi

if [ -z "$FUNCTION_URL_SECONDARY" ]; then
  echo "⚠️  Could not auto-detect URL. Using known URL..."
  FUNCTION_URL_SECONDARY="https://daily-readings-seeder-secondary-n6patcgpoa-uc.a.run.app"
fi

echo "Function URL: $FUNCTION_URL_SECONDARY"
echo ""
echo "Sending request..."

curl -X POST \
  "$FUNCTION_URL_SECONDARY?start_date=$START_DATE&end_date=$END_DATE" \
  -H "Authorization: bearer $(gcloud auth print-identity-token --project=$SECONDARY_PROJECT)" \
  -H "Content-Type: application/json" \
  -d '{}' \
  -w "\nHTTP Status: %{http_code}\n" \
  2>&1 | grep -E "HTTP|successful|status|✅|❌|error" || echo "Request sent to secondary"

echo ""
echo "✅ Secondary seeder triggered!"
echo ""

echo "═══════════════════════════════════════════════════════════"
echo "🎉 COMPLETE!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Summary:"
echo "  • Deleted all November 2025 documents from both projects"
echo "  • Triggered reseeding for both primary and secondary"
echo "  • Check Cloud Function logs for seeding progress"
echo ""
echo "To verify the results, run:"
echo "  ./verify_all_november.py"
echo ""


