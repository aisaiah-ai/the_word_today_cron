#!/bin/bash
# Delete all November 2025 documents from secondary Firebase

PROJECT_ID="aisaiah-sfa-dev-app"
COLLECTION="daily_scripture"

echo "🗑️  Deleting all November 2025 documents from secondary Firebase..."
echo "Project: $PROJECT_ID"
echo "Collection: $COLLECTION"
echo ""

# Use gcloud to delete documents
for day in {1..30}; do
  date_str=$(printf "2025-11-%02d" $day)
  echo "Deleting $date_str..."
  gcloud firestore documents delete "projects/$PROJECT_ID/databases/(default)/documents/$COLLECTION/$date_str" 2>&1 | grep -v "NOT_FOUND" || echo "  (not found, skipping)"
done

echo ""
echo "✅ Deletion complete!"
