#!/bin/bash

# Script to fix IAM permissions for secondary Firebase deployment
# This grants the Cloud Build service account the necessary roles

set -e

PROJECT_ID="aisaiah-sfa-dev-app"
SERVICE_ACCOUNT="512102198745-compute@developer.gserviceaccount.com"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  Fixing IAM Permissions for Secondary Deployment              ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Project: $PROJECT_ID"
echo "Service Account: $SERVICE_ACCOUNT"
echo ""

# Check if authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Not authenticated. Please run: gcloud auth login"
    exit 1
fi

# Set project
gcloud config set project "$PROJECT_ID"

echo "Granting roles to Cloud Build service account..."
echo ""

# Grant Cloud Build Builder role
echo "1. Granting roles/cloudbuild.builds.builder..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/cloudbuild.builds.builder" \
  --condition=None

# Grant Cloud Functions Admin role
echo "2. Granting roles/cloudfunctions.admin..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/cloudfunctions.admin" \
  --condition=None

# Grant Service Account User role
echo "3. Granting roles/iam.serviceAccountUser..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/iam.serviceAccountUser" \
  --condition=None

echo ""
echo "✅ Permissions granted successfully!"
echo ""
echo "Next steps:"
echo "1. Wait 2-5 minutes for any in-progress deployments to finish"
echo "2. Re-run the secondary deployment workflow:"
echo "   https://github.com/aisaiah-ai/the_word_today_cron/actions"
echo ""
echo "Or trigger manually:"
echo "   gh workflow run 'Deploy Daily Readings Seeder (Secondary Firebase)' --ref main"

