#!/bin/bash

# Non-Interactive Setup Script
# Usage: 
#   export YOUTUBE_API_KEY="your-key"
#   export FIREBASE_KEY_PATH="/path/to/firebase-key.json"
#   ./setup_non_interactive.sh

set -e

echo "🚀 Non-Interactive Setup for The Word Today Cron"
echo "================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Detect values
GCP_PROJECT_ID=${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}
REPO=${REPO:-"aisaiah-ai/the_word_today_cron"}
YOUTUBE_API_KEY=${YOUTUBE_API_KEY:-""}
FIREBASE_KEY_PATH=${FIREBASE_KEY_PATH:-""}
DRY_RUN=${DRY_RUN:-"False"}

echo "📋 Detected/Configured Values:"
echo "   GCP Project: ${GCP_PROJECT_ID:-'NOT SET'}"
echo "   GitHub Repo: $REPO"
echo "   YouTube API Key: ${YOUTUBE_API_KEY:+'SET (hidden)'}${YOUTUBE_API_KEY:-'NOT SET'}"
echo "   Firebase Key: ${FIREBASE_KEY_PATH:-'NOT SET'}"
echo "   Dry Run: $DRY_RUN"
echo ""

# Validate required values
if [ -z "$GCP_PROJECT_ID" ]; then
    echo -e "${RED}❌ GCP_PROJECT_ID not set. Set it with: export GCP_PROJECT_ID=your-project${NC}"
    exit 1
fi

if [ -z "$YOUTUBE_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  YOUTUBE_API_KEY not set. Set it with: export YOUTUBE_API_KEY=your-key${NC}"
    echo "Getting from user..."
    read -sp "Enter YouTube API Key: " YOUTUBE_API_KEY
    echo ""
fi

if [ -z "$FIREBASE_KEY_PATH" ] || [ ! -f "$FIREBASE_KEY_PATH" ]; then
    echo -e "${YELLOW}⚠️  Firebase key file not found.${NC}"
    read -p "Enter path to Firebase service account JSON file: " FIREBASE_KEY_PATH
    if [ ! -f "$FIREBASE_KEY_PATH" ]; then
        echo -e "${RED}❌ File not found: $FIREBASE_KEY_PATH${NC}"
        exit 1
    fi
fi

# Run GCP setup with auto-accept
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 1: GCP Setup${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if service account exists
SA_NAME="github-actions-deploy"
SA_EMAIL="${SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

# Enable APIs
echo "🔌 Enabling APIs..."
gcloud services enable cloudfunctions.googleapis.com --project="$GCP_PROJECT_ID" 2>/dev/null || true
gcloud services enable cloudscheduler.googleapis.com --project="$GCP_PROJECT_ID" 2>/dev/null || true
gcloud services enable cloudbuild.googleapis.com --project="$GCP_PROJECT_ID" 2>/dev/null || true
gcloud services enable logging.googleapis.com --project="$GCP_PROJECT_ID" 2>/dev/null || true
echo "✅ APIs enabled"

# Create service account if needed
if ! gcloud iam service-accounts describe "$SA_EMAIL" --project="$GCP_PROJECT_ID" &>/dev/null; then
    echo "👤 Creating service account..."
    gcloud iam service-accounts create "$SA_NAME" \
        --display-name="GitHub Actions Deployment Account" \
        --project="$GCP_PROJECT_ID" 2>/dev/null || true
fi

# Grant roles
echo "🔐 Granting IAM roles..."
gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/cloudfunctions.developer" \
    --condition=None 2>/dev/null || true

gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/cloudscheduler.admin" \
    --condition=None 2>/dev/null || true

gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/iam.serviceAccountUser" \
    --condition=None 2>/dev/null || true

gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/storage.admin" \
    --condition=None 2>/dev/null || true

gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/serviceusage.serviceUsageConsumer" \
    --condition=None 2>/dev/null || true

echo "✅ IAM roles granted"

# Create key
KEY_FILE="gcp-sa-key.json"
if [ ! -f "$KEY_FILE" ]; then
    echo "🔑 Creating service account key..."
    gcloud iam service-accounts keys create "$KEY_FILE" \
        --iam-account="$SA_EMAIL" \
        --project="$GCP_PROJECT_ID" 2>/dev/null || true
    echo "✅ Key created: $KEY_FILE"
else
    echo "✅ Key file exists: $KEY_FILE"
fi

# Run GitHub setup
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 2: GitHub Secrets Setup${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Convert Firebase JSON to single line
if command -v jq &> /dev/null; then
    FIREBASE_CREDENTIALS_JSON=$(cat "$FIREBASE_KEY_PATH" | jq -c .)
else
    # Fallback: remove newlines manually
    FIREBASE_CREDENTIALS_JSON=$(cat "$FIREBASE_KEY_PATH" | tr -d '\n' | sed 's/  */ /g')
fi

# Set secrets
echo "🔐 Setting GitHub secrets..."

gh secret set GCP_PROJECT_ID --repo "$REPO" --body "$GCP_PROJECT_ID" 2>/dev/null || echo "⚠️  Failed to set GCP_PROJECT_ID"
echo "✅ Set GCP_PROJECT_ID"

gh secret set GCP_SA_KEY --repo "$REPO" < "$KEY_FILE" 2>/dev/null || echo "⚠️  Failed to set GCP_SA_KEY"
echo "✅ Set GCP_SA_KEY"

gh secret set YOUTUBE_API_KEY --repo "$REPO" --body "$YOUTUBE_API_KEY" 2>/dev/null || echo "⚠️  Failed to set YOUTUBE_API_KEY"
echo "✅ Set YOUTUBE_API_KEY"

echo "$FIREBASE_CREDENTIALS_JSON" | gh secret set FIREBASE_CREDENTIALS_JSON --repo "$REPO" 2>/dev/null || echo "⚠️  Failed to set FIREBASE_CREDENTIALS_JSON"
echo "✅ Set FIREBASE_CREDENTIALS_JSON"

gh secret set DRY_RUN --repo "$REPO" --body "$DRY_RUN" 2>/dev/null || echo "⚠️  Failed to set DRY_RUN"
echo "✅ Set DRY_RUN"

echo ""
echo -e "${GREEN}✅ Setup completed!${NC}"
echo ""
echo "Summary:"
echo "  Project: $GCP_PROJECT_ID"
echo "  Repo: $REPO"
echo "  Service Account: $SA_EMAIL"
echo ""
echo "Next: Push code to trigger deployment:"
echo "  git add ."
echo "  git commit -m 'Setup automated deployment'"
echo "  git push origin main"
echo ""
