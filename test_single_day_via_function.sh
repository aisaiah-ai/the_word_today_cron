#!/bin/bash
# Test seeding a single day to verify secondary reading works

# November 17, 2025 is a Sunday - should have a second reading
TEST_DATE="2025-11-17"

echo "═══════════════════════════════════════════════════════════"
echo "🧪 TESTING SINGLE DAY SEED: $TEST_DATE"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "This will seed November 17, 2025 (Sunday - should have 2nd reading)"
echo ""

# Trigger PRIMARY function for just this one day
echo "🔵 Triggering PRIMARY Cloud Function..."
echo ""

RESPONSE=$(curl -s -X POST \
  "https://daily-readings-seeder-938552047954.us-central1.run.app?start_date=$TEST_DATE&end_date=$TEST_DATE" \
  -H "Authorization: bearer $(gcloud auth print-identity-token --project=aisaiahconferencefb)" \
  -H "Content-Type: application/json" \
  -d '{}')

echo "$RESPONSE" | jq -r '
  .body | 
  "Status: \(.status)\n" +
  "Processed: \(.processed_dates | join(", "))\n" +
  "Successful: \(.successful | join(", "))\n" +
  "Errors: \(.errors | length)"
'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Now checking the document to see if it has second reading..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Give it a second to write
sleep 2

# Try to fetch and display the document using gcloud (won't work due to permissions)
echo "⚠️  Cannot read Firestore directly due to permissions."
echo ""
echo "📋 To verify the document was created with second reading:"
echo ""
echo "Option 1: Check Firebase Console"
echo "  URL: https://console.firebase.google.com/project/aisaiahconferencefb/firestore/data/~2Fdaily_scripture~2F$TEST_DATE"
echo ""
echo "Option 2: Check Cloud Function logs"
echo "  gcloud logging read \\"
echo "    \"resource.type=cloud_run_revision AND resource.labels.service_name=daily-readings-seeder\" \\"
echo "    --project=aisaiahconferencefb \\"
echo "    --limit=50 \\"
echo "    --format=json | jq -r '.[] | .textPayload' | grep -A 5 -B 5 '$TEST_DATE'"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "What to look for in Firebase Console:"
echo "  ✅ first_reading_verse: (should be present)"
echo "  ✅ second_reading_verse: (should be present for Sunday)"
echo "  ✅ gospel_verse: (should be present)"
echo "  ✅ responsorial_psalm_verse: (should be present)"
echo "  ✅ body: Should be SHORT like 'Gospel: Jn 18:33b-37'"
echo ""


