#!/bin/bash

# GCP Setup Automation Script
# This script automates the setup of Google Cloud Platform resources

set -e

echo "🚀 GCP Setup Automation for The Word Today Cron"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found.${NC}"
    echo "Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${YELLOW}⚠️  Not authenticated with GCP.${NC}"
    echo "Please authenticate..."
    gcloud auth login
fi

# Get project ID (check for existing config first)
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ -n "$CURRENT_PROJECT" ]; then
    echo -e "${GREEN}📋 Found configured GCP project: ${CURRENT_PROJECT}${NC}"
    read -p "Enter GCP Project ID [$CURRENT_PROJECT]: " PROJECT_ID
    PROJECT_ID=${PROJECT_ID:-$CURRENT_PROJECT}
else
    read -p "Enter GCP Project ID: " PROJECT_ID
fi

# Set the project
echo ""
echo -e "${GREEN}📋 Setting GCP project...${NC}"
gcloud config set project "$PROJECT_ID"
echo "✅ Project set to: $PROJECT_ID"

# Enable required APIs
echo ""
echo -e "${GREEN}🔌 Enabling required APIs...${NC}"
gcloud services enable cloudfunctions.googleapis.com
echo "✅ Cloud Functions API enabled"

gcloud services enable run.googleapis.com
echo "✅ Cloud Run API enabled (required for Gen2 functions)"

gcloud services enable cloudscheduler.googleapis.com
echo "✅ Cloud Scheduler API enabled"

gcloud services enable cloudbuild.googleapis.com
echo "✅ Cloud Build API enabled"

gcloud services enable logging.googleapis.com
echo "✅ Cloud Logging API enabled"

gcloud services enable artifactregistry.googleapis.com
echo "✅ Artifact Registry API enabled (for function images)"

gcloud services enable secretmanager.googleapis.com
echo "✅ Secret Manager API enabled (optional, for Firebase credentials)"

# Create service account for GitHub Actions
echo ""
echo -e "${GREEN}👤 Creating service account for GitHub Actions...${NC}"
SA_NAME="github-actions-deploy"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Check if service account already exists
if gcloud iam service-accounts describe "$SA_EMAIL" &> /dev/null; then
    echo -e "${YELLOW}⚠️  Service account already exists: $SA_EMAIL${NC}"
    read -p "Do you want to recreate it? (y/n): " RECREATE
    if [[ "$RECREATE" == "y" || "$RECREATE" == "Y" ]]; then
        gcloud iam service-accounts delete "$SA_EMAIL" --quiet || true
        gcloud iam service-accounts create "$SA_NAME" \
            --display-name="GitHub Actions Deployment Account"
        echo "✅ Service account recreated"
    fi
else
    gcloud iam service-accounts create "$SA_NAME" \
        --display-name="GitHub Actions Deployment Account"
    echo "✅ Service account created: $SA_EMAIL"
fi

# Grant necessary roles
echo ""
echo -e "${GREEN}🔐 Granting IAM roles...${NC}"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/cloudfunctions.developer" \
    --condition=None

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/cloudscheduler.admin" \
    --condition=None

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/iam.serviceAccountUser" \
    --condition=None

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/storage.admin" \
    --condition=None

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/run.admin" \
    --condition=None

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/artifactregistry.writer" \
    --condition=None

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/serviceusage.serviceUsageConsumer" \
    --condition=None

echo "✅ IAM roles granted"

# Create and download key
echo ""
echo -e "${GREEN}🔑 Creating service account key...${NC}"
KEY_FILE="gcp-sa-key.json"
gcloud iam service-accounts keys create "$KEY_FILE" \
    --iam-account="$SA_EMAIL"

echo "✅ Service account key created: $KEY_FILE"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: Keep this key file secure!${NC}"
echo "   You'll need to add it to GitHub Secrets as GCP_SA_KEY"
echo ""

# Summary
echo ""
echo -e "${GREEN}✅ GCP setup completed!${NC}"
echo ""
echo "Summary:"
echo "  Project ID: $PROJECT_ID"
echo "  Service Account: $SA_EMAIL"
echo "  Key File: $KEY_FILE"
echo ""
echo "Next steps:"
echo "1. Add the key file content to GitHub Secrets:"
echo "   cat $KEY_FILE | gh secret set GCP_SA_KEY --repo YOUR_REPO"
echo ""
echo "2. Or use the setup_github.sh script for automated setup"
echo ""
