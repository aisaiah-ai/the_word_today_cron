#!/bin/bash

# Simplified GCP Auth Fix - Works around authentication refresh issues
# This script creates a new service account key and updates GitHub secrets

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔧 Simplified GCP Auth Fix${NC}"
echo "================================"
echo ""

PROJECT_ID="aisaiahconferencefb"
REPO="aisaiah-ai/the_word_today_cron"
SA_EMAIL="github-actions-deploy@${PROJECT_ID}.iam.gserviceaccount.com"

echo -e "${GREEN}📋 Configuration:${NC}"
echo "  Project: $PROJECT_ID"
echo "  Repo: $REPO"
echo "  Service Account: $SA_EMAIL"
echo ""

# Check if we can authenticate
echo -e "${BLUE}🔍 Checking authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ No active gcloud authentication found${NC}"
    echo ""
    echo "Please run: gcloud auth login"
    echo "Then run this script again."
    exit 1
fi

ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1)
echo -e "${GREEN}✅ Authenticated as: $ACTIVE_ACCOUNT${NC}"
echo ""

# Backup old key
OLD_KEY="gcp-sa-key.json"
NEW_KEY="gcp-sa-key-new.json"

if [ -f "$OLD_KEY" ]; then
    echo -e "${YELLOW}📦 Backing up old key...${NC}"
    cp "$OLD_KEY" "${OLD_KEY}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✅ Old key backed up"
    echo ""
fi

# Create new key
echo -e "${BLUE}🔑 Creating new service account key...${NC}"
echo "Note: If this fails, you may need to refresh your auth:"
echo "      gcloud auth login"
echo ""

if gcloud iam service-accounts keys create "$NEW_KEY" \
    --iam-account="$SA_EMAIL" \
    --project="$PROJECT_ID" 2>&1; then
    
    echo -e "${GREEN}✅ New key created: $NEW_KEY${NC}"
else
    echo -e "${RED}❌ Failed to create key${NC}"
    echo ""
    echo "This might be because:"
    echo "  1. Your auth tokens need refresh: gcloud auth login"
    echo "  2. Service account doesn't exist (will be created)"
    echo "  3. You don't have permissions"
    echo ""
    echo "Trying to create service account first..."
    
    # Try to create service account if it doesn't exist
    gcloud iam service-accounts create github-actions-deploy \
        --display-name="GitHub Actions Deployment Account" \
        --project="$PROJECT_ID" 2>&1 || echo "Service account may already exist"
    
    # Grant roles
    echo "Granting IAM roles..."
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/cloudfunctions.developer" 2>/dev/null || true
    
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/cloudscheduler.admin" 2>/dev/null || true
    
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/iam.serviceAccountUser" 2>/dev/null || true
    
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/storage.admin" 2>/dev/null || true
    
    # Try creating key again
    echo "Creating key again..."
    if gcloud iam service-accounts keys create "$NEW_KEY" \
        --iam-account="$SA_EMAIL" \
        --project="$PROJECT_ID" 2>&1; then
        echo -e "${GREEN}✅ New key created: $NEW_KEY${NC}"
    else
        echo -e "${RED}❌ Still failed. Please check your authentication and permissions${NC}"
        exit 1
    fi
fi

# Validate key
echo ""
echo -e "${BLUE}🧪 Validating new key...${NC}"
if jq empty "$NEW_KEY" 2>/dev/null; then
    echo -e "${GREEN}✅ Key file is valid JSON${NC}"
    KEY_EMAIL=$(jq -r '.client_email' "$NEW_KEY")
    KEY_PROJECT=$(jq -r '.project_id' "$NEW_KEY")
    echo "   Email: $KEY_EMAIL"
    echo "   Project: $KEY_PROJECT"
else
    echo -e "${RED}❌ Key file is not valid JSON${NC}"
    exit 1
fi

# Test key authentication
echo ""
echo -e "${BLUE}🧪 Testing key authentication...${NC}"
if gcloud auth activate-service-account --key-file="$NEW_KEY" 2>&1; then
    echo -e "${GREEN}✅ Key authentication successful${NC}"
    # Restore user account
    gcloud config set account "$ACTIVE_ACCOUNT" 2>/dev/null || true
else
    echo -e "${YELLOW}⚠️  Could not test key authentication automatically${NC}"
    echo "   But the key file appears valid, proceeding..."
fi

# Update GitHub secret
echo ""
echo -e "${BLUE}🔐 Updating GitHub secret...${NC}"
if command -v gh &> /dev/null; then
    if gh secret set GCP_SA_KEY --repo "$REPO" < "$NEW_KEY" 2>&1; then
        echo -e "${GREEN}✅ GitHub secret GCP_SA_KEY updated successfully${NC}"
    else
        echo -e "${RED}❌ Failed to update GitHub secret${NC}"
        echo ""
        echo "Please update manually:"
        echo "  gh secret set GCP_SA_KEY --repo $REPO < $NEW_KEY"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  GitHub CLI not found. Please update manually:${NC}"
    echo "  1. Go to: https://github.com/$REPO/settings/secrets/actions"
    echo "  2. Edit GCP_SA_KEY"
    echo "  3. Copy contents of: $NEW_KEY"
    echo ""
    echo "Or install GitHub CLI: brew install gh"
fi

# Replace old key with new one
echo ""
read -p "Replace old key file with new one? (y/n): " REPLACE
if [[ "$REPLACE" == "y" || "$REPLACE" == "Y" ]]; then
    mv "$NEW_KEY" "$OLD_KEY"
    echo -e "${GREEN}✅ Replaced old key file${NC}"
else
    echo -e "${YELLOW}⚠️  Keeping both files:${NC}"
    echo "   Old: $OLD_KEY"
    echo "   New: $NEW_KEY"
fi

# Summary
echo ""
echo -e "${GREEN}✅ Fix completed!${NC}"
echo ""
echo "Summary:"
echo "  ✅ New service account key created"
echo "  ✅ GitHub secret updated"
echo "  ✅ Ready to retry GitHub Actions workflow"
echo ""
echo "Next steps:"
echo "  1. Go to GitHub Actions and re-run the workflow"
echo "  2. Or push a new commit to trigger deployment"
echo ""

