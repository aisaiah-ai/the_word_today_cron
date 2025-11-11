#!/bin/bash
# Script to set up cross-project Firebase access (Option 2)
# No service account keys needed

set -e

echo "================================================"
echo "Setting up Cross-Project Firebase Access"
echo "================================================"
echo ""

# Step 1: Grant permissions
echo "Step 1: Granting Cloud Function access to secondary Firebase..."
gcloud projects add-iam-policy-binding aisaiah-sfa-dev-app \
  --member="serviceAccount:938552047954-compute@developer.gserviceaccount.com" \
  --role="roles/datastore.user"

echo ""
echo "✅ Permissions granted"
echo ""

# Step 2: Switch to primary project
echo "Step 2: Switching to primary project..."
gcloud config set project aisaiahconferencefb

echo ""

# Step 3: Deploy function with secondary project ID
echo "Step 3: Deploying function with secondary Firebase project ID..."
gcloud functions deploy daily-readings-seeder \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=daily_readings_seeder \
  --entry-point=seed_daily_readings_cron \
  --trigger-http \
  --allow-unauthenticated \
  --memory=512MB \
  --timeout=540s \
  --max-instances=10 \
  --set-env-vars="DRY_RUN=False,FIREBASE_PROJECT_ID_SECONDARY=aisaiah-sfa-dev-app"

echo ""
echo "✅ Function deployed"
echo ""

# Step 4: Test
echo "Step 4: Testing dual Firebase seeding..."
FUNCTION_URL=$(gcloud functions describe daily-readings-seeder \
  --gen2 \
  --region=us-central1 \
  --format="value(serviceConfig.uri)")

echo "Function URL: $FUNCTION_URL"
echo ""
echo "Seeding Dec 25 to both Firebase projects..."

curl -X GET "$FUNCTION_URL?start_date=2025-12-25&end_date=2025-12-25"

echo ""
echo ""
echo "================================================"
echo "✅ Setup Complete"
echo "================================================"
echo ""
echo "The function will now seed to BOTH Firebase projects:"
echo "  - Primary: aisaiahconferencefb"
echo "  - Secondary: aisaiah-sfa-dev-app"
echo ""
echo "To disable secondary seeding:"
echo "  gcloud functions deploy daily-readings-seeder --update-env-vars FIREBASE_PROJECT_ID_SECONDARY=''"
echo ""

