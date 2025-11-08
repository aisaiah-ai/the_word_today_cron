#!/bin/bash

# Setup Workload Identity Federation for GitHub Actions
# This allows authentication without service account keys

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔐 Setting up Workload Identity Federation for GitHub Actions${NC}"
echo "================================================================"
echo ""

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    read -p "Enter GCP Project ID: " PROJECT_ID
fi

# Get project number
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
echo -e "${GREEN}📋 Project: $PROJECT_ID (Number: $PROJECT_NUMBER)${NC}"

# Get GitHub repository
if [ -n "$GITHUB_REPO" ]; then
    REPO="$GITHUB_REPO"
else
    REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
    if [ -z "$REPO" ]; then
        read -p "Enter GitHub repository (format: owner/repo): " REPO
    fi
fi

echo -e "${GREEN}📋 Repository: $REPO${NC}"
echo ""

# Service account
SA_NAME="github-actions-deploy"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Check if service account exists
if ! gcloud iam service-accounts describe "$SA_EMAIL" &>/dev/null; then
    echo -e "${YELLOW}⚠️  Service account not found. Creating...${NC}"
    gcloud iam service-accounts create "$SA_NAME" \
        --display-name="GitHub Actions Deployment Account" \
        --project="$PROJECT_ID"
    echo -e "${GREEN}✅ Service account created${NC}"
fi

# Enable required APIs
echo ""
echo -e "${BLUE}🔌 Enabling required APIs...${NC}"
gcloud services enable iamcredentials.googleapis.com --project="$PROJECT_ID" 2>/dev/null || true
gcloud services enable iam.googleapis.com --project="$PROJECT_ID" 2>/dev/null || true
echo -e "${GREEN}✅ APIs enabled${NC}"

# Create Workload Identity Pool
POOL_NAME="github-pool"
POOL_ID="projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL_NAME"

echo ""
echo -e "${BLUE}🏊 Creating Workload Identity Pool...${NC}"
if gcloud iam workload-identity-pools describe "$POOL_NAME" --location="global" --project="$PROJECT_ID" &>/dev/null; then
    echo -e "${YELLOW}⚠️  Pool already exists, skipping creation${NC}"
else
    gcloud iam workload-identity-pools create "$POOL_NAME" \
        --project="$PROJECT_ID" \
        --location="global" \
        --display-name="GitHub Actions Pool"
    echo -e "${GREEN}✅ Pool created${NC}"
fi

# Create Workload Identity Provider
PROVIDER_NAME="github-provider"
PROVIDER_ID="$POOL_ID/providers/$PROVIDER_NAME"

echo ""
echo -e "${BLUE}🔗 Creating Workload Identity Provider...${NC}"
if gcloud iam workload-identity-pools providers describe "$PROVIDER_NAME" \
    --workload-identity-pool="$POOL_NAME" \
    --location="global" \
    --project="$PROJECT_ID" &>/dev/null; then
    echo -e "${YELLOW}⚠️  Provider already exists, skipping creation${NC}"
else
    gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_NAME" \
        --project="$PROJECT_ID" \
        --location="global" \
        --workload-identity-pool="$POOL_NAME" \
        --display-name="GitHub Provider" \
        --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
        --issuer-uri="https://token.actions.githubusercontent.com"
    echo -e "${GREEN}✅ Provider created${NC}"
fi

# Grant service account access
echo ""
echo -e "${BLUE}🔐 Granting Workload Identity User role...${NC}"
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
    --project="$PROJECT_ID" \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/$POOL_ID/attribute.repository/$REPO" \
    --condition=None 2>/dev/null || echo -e "${YELLOW}⚠️  Policy binding may already exist${NC}"

echo -e "${GREEN}✅ IAM binding created${NC}"

# Output configuration
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Workload Identity Federation Setup Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📋 Configuration Details:"
echo "  Project ID: $PROJECT_ID"
echo "  Project Number: $PROJECT_NUMBER"
echo "  Repository: $REPO"
echo "  Service Account: $SA_EMAIL"
echo "  Pool: $POOL_ID"
echo "  Provider: $PROVIDER_ID"
echo ""
echo "📝 Next Steps:"
echo "  1. Update .github/workflows/deploy.yml to use Workload Identity"
echo "  2. Remove GCP_SA_KEY secret (no longer needed)"
echo "  3. Push changes to trigger deployment"
echo ""
echo "🔧 Provider Resource Name:"
echo "  $PROVIDER_ID"
echo ""

