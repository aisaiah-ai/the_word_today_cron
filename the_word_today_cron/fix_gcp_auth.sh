#!/bin/bash

# Fix GCP Authentication for GitHub Actions
# This script regenerates the service account key and updates GitHub Secrets

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Fixing GCP Authentication for GitHub Actions${NC}"
echo "=================================================="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found.${NC}"
    echo "Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI (gh) not found.${NC}"
    echo "Please install GitHub CLI: https://cli.github.com/"
    exit 1
fi

# Get project ID
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ -n "$CURRENT_PROJECT" ]; then
    echo -e "${GREEN}📋 Found configured GCP project: ${CURRENT_PROJECT}${NC}"
    read -p "Enter GCP Project ID [$CURRENT_PROJECT]: " PROJECT_ID
    PROJECT_ID=${PROJECT_ID:-$CURRENT_PROJECT}
else
    read -p "Enter GCP Project ID: " PROJECT_ID
fi

# Set the project (only if different)
if [ "$CURRENT_PROJECT" != "$PROJECT_ID" ]; then
    echo "Setting project to: $PROJECT_ID"
    gcloud config set project "$PROJECT_ID" 2>&1 || {
        echo -e "${YELLOW}⚠️  Could not set project automatically. Please ensure you're authenticated:${NC}"
        echo "   gcloud auth login"
        exit 1
    }
else
    echo -e "${GREEN}✅ Project already set correctly: $PROJECT_ID${NC}"
fi

# Get GitHub repository (auto-detect or use environment variable)
CURRENT_REPO=""
if [ -n "$GITHUB_REPO" ]; then
    CURRENT_REPO="$GITHUB_REPO"
    echo -e "${GREEN}📋 Using repository from GITHUB_REPO: ${CURRENT_REPO}${NC}"
else
    # Try to detect from git remote
    if git remote get-url origin &> /dev/null; then
        GIT_REMOTE=$(git remote get-url origin 2>/dev/null | sed -E 's|.*github.com[:/]([^/]+/[^/]+?)(\.git)?$|\1|' | sed 's/\.git$//')
        if [ -n "$GIT_REMOTE" ]; then
            CURRENT_REPO="$GIT_REMOTE"
            echo -e "${GREEN}📋 Detected git repository: ${CURRENT_REPO}${NC}"
        fi
    fi
    
    # Try to detect from GitHub CLI
    if [ -z "$CURRENT_REPO" ] && command -v gh &> /dev/null; then
        GH_REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
        if [ -n "$GH_REPO" ]; then
            CURRENT_REPO="$GH_REPO"
            echo -e "${GREEN}📋 Detected GitHub repository: ${CURRENT_REPO}${NC}"
        fi
    fi
    
    # Use default if not detected
    if [ -z "$CURRENT_REPO" ]; then
        CURRENT_REPO="aisaiah-ai/the_word_today_cron"
        echo -e "${YELLOW}📋 Using default repository: ${CURRENT_REPO}${NC}"
    fi
fi

if [ -n "$CURRENT_REPO" ]; then
    read -p "Enter GitHub repository (format: owner/repo) [$CURRENT_REPO]: " REPO
    REPO=${REPO:-$CURRENT_REPO}
else
    read -p "Enter GitHub repository (format: owner/repo): " REPO
    if [ -z "$REPO" ]; then
        echo -e "${RED}❌ Repository name is required${NC}"
        exit 1
    fi
fi

# Service account details
SA_NAME="github-actions-deploy"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Check if service account exists
echo ""
echo -e "${BLUE}🔍 Checking service account...${NC}"
if ! gcloud iam service-accounts describe "$SA_EMAIL" &> /dev/null; then
    echo -e "${YELLOW}⚠️  Service account not found: $SA_EMAIL${NC}"
    echo "Creating service account..."
    
    gcloud iam service-accounts create "$SA_NAME" \
        --display-name="GitHub Actions Deployment Account" \
        --project="$PROJECT_ID"
    
    echo "✅ Service account created"
    
    # Grant necessary roles
    echo ""
    echo -e "${BLUE}🔐 Granting IAM roles...${NC}"
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/cloudfunctions.developer" \
        --condition=None 2>/dev/null || true
    
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/cloudscheduler.admin" \
        --condition=None 2>/dev/null || true
    
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/iam.serviceAccountUser" \
        --condition=None 2>/dev/null || true
    
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/storage.admin" \
        --condition=None 2>/dev/null || true
    
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/serviceusage.serviceUsageConsumer" \
        --condition=None 2>/dev/null || true
    
    echo "✅ IAM roles granted"
else
    echo -e "${GREEN}✅ Service account exists: $SA_EMAIL${NC}"
fi

# List existing keys
echo ""
echo -e "${BLUE}🔑 Listing existing service account keys...${NC}"
EXISTING_KEYS=$(gcloud iam service-accounts keys list \
    --iam-account="$SA_EMAIL" \
    --format="value(name)" 2>/dev/null || echo "")

if [ -n "$EXISTING_KEYS" ]; then
    echo -e "${YELLOW}⚠️  Found existing keys. You may want to delete old ones after creating a new one.${NC}"
    echo "Existing keys:"
    echo "$EXISTING_KEYS" | while read key; do
        echo "  - $key"
    done
    echo ""
    read -p "Do you want to delete old keys after creating new one? (y/n): " DELETE_OLD
fi

# Create new key
echo ""
echo -e "${BLUE}🔑 Creating new service account key...${NC}"
KEY_FILE="gcp-sa-key-new.json"
gcloud iam service-accounts keys create "$KEY_FILE" \
    --iam-account="$SA_EMAIL" \
    --project="$PROJECT_ID"

echo -e "${GREEN}✅ New key created: $KEY_FILE${NC}"

# Verify key file is valid JSON
if ! jq empty "$KEY_FILE" 2>/dev/null; then
    echo -e "${RED}❌ Key file is not valid JSON${NC}"
    exit 1
fi

# Test the key locally
echo ""
echo -e "${BLUE}🧪 Testing new key...${NC}"
gcloud auth activate-service-account --key-file="$KEY_FILE"
TEST_PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ "$TEST_PROJECT" = "$PROJECT_ID" ]; then
    echo -e "${GREEN}✅ Key is valid and working${NC}"
else
    echo -e "${YELLOW}⚠️  Warning: Could not verify key automatically${NC}"
fi

# Update GitHub secret
echo ""
echo -e "${BLUE}🔐 Updating GitHub secret...${NC}"
if gh secret set GCP_SA_KEY --repo "$REPO" < "$KEY_FILE"; then
    echo -e "${GREEN}✅ GitHub secret GCP_SA_KEY updated successfully${NC}"
else
    echo -e "${RED}❌ Failed to update GitHub secret${NC}"
    echo "Please manually update the secret:"
    echo "  gh secret set GCP_SA_KEY --repo $REPO < $KEY_FILE"
    exit 1
fi

# Update GCP_PROJECT_ID if needed
echo ""
read -p "Do you want to update GCP_PROJECT_ID secret? (y/n): " UPDATE_PROJECT
if [[ "$UPDATE_PROJECT" == "y" || "$UPDATE_PROJECT" == "Y" ]]; then
    if gh secret set GCP_PROJECT_ID --repo "$REPO" --body "$PROJECT_ID"; then
        echo -e "${GREEN}✅ GitHub secret GCP_PROJECT_ID updated${NC}"
    else
        echo -e "${YELLOW}⚠️  Failed to update GCP_PROJECT_ID${NC}"
    fi
fi

# Delete old keys if requested
if [[ "$DELETE_OLD" == "y" || "$DELETE_OLD" == "Y" ]]; then
    echo ""
    echo -e "${BLUE}🗑️  Deleting old keys...${NC}"
    echo "$EXISTING_KEYS" | while read key; do
        if [ -n "$key" ]; then
            KEY_ID=$(basename "$key")
            gcloud iam service-accounts keys delete "$KEY_ID" \
                --iam-account="$SA_EMAIL" \
                --quiet 2>/dev/null || true
            echo "  Deleted: $KEY_ID"
        fi
    done
    echo -e "${GREEN}✅ Old keys deleted${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}✅ Authentication fix completed!${NC}"
echo ""
echo "Summary:"
echo "  Project ID: $PROJECT_ID"
echo "  Service Account: $SA_EMAIL"
echo "  New Key File: $KEY_FILE"
echo "  GitHub Repo: $REPO"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT:${NC}"
echo "  1. Keep the key file secure: $KEY_FILE"
echo "  2. The old key in GitHub Secrets has been replaced"
echo "  3. You can now retry your GitHub Actions workflow"
echo ""
echo "Next steps:"
echo "  1. Commit and push your changes"
echo "  2. Check GitHub Actions workflow - it should now work"
echo ""
echo "To test the workflow manually:"
echo "  gh workflow run deploy.yml --repo $REPO"

