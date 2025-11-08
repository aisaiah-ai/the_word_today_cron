#!/bin/bash

# Terraform-based GCP Setup Script
# This script uses Terraform to set up all GCP resources

set -e

echo "🚀 Terraform-based GCP Setup for The Word Today Cron"
echo "====================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ Terraform not found.${NC}"
    echo "Please install Terraform: https://www.terraform.io/downloads"
    echo ""
    echo "macOS: brew install terraform"
    echo "Linux: See https://www.terraform.io/downloads"
    exit 1
fi

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found.${NC}"
    echo "Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get project ID
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
if [ -n "$CURRENT_PROJECT" ]; then
    echo -e "${GREEN}📋 Found configured GCP project: ${CURRENT_PROJECT}${NC}"
    read -p "Enter GCP Project ID [$CURRENT_PROJECT]: " PROJECT_ID
    PROJECT_ID=${PROJECT_ID:-$CURRENT_PROJECT}
else
    read -p "Enter GCP Project ID: " PROJECT_ID
fi

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Project ID is required${NC}"
    exit 1
fi

# Set the project
echo ""
echo -e "${GREEN}📋 Setting GCP project...${NC}"
gcloud config set project "$PROJECT_ID"
echo "✅ Project set to: $PROJECT_ID"

# Check authentication
echo ""
echo -e "${BLUE}🔐 Checking authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${YELLOW}⚠️  Not authenticated with GCP.${NC}"
    echo "Authenticating..."
    gcloud auth login
    gcloud auth application-default login
fi

# Navigate to terraform directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    echo ""
    echo -e "${YELLOW}⚠️  terraform.tfvars not found. Creating from example...${NC}"
    cat > terraform.tfvars <<EOF
project_id = "$PROJECT_ID"
region     = "us-central1"
EOF
    echo "✅ Created terraform.tfvars"
fi

# Initialize Terraform
echo ""
echo -e "${GREEN}🔧 Initializing Terraform...${NC}"
terraform init

# Plan
echo ""
echo -e "${GREEN}📋 Planning Terraform changes...${NC}"
terraform plan -out=tfplan

# Ask for confirmation
echo ""
read -p "Do you want to apply these changes? (y/n): " CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    echo "Cancelled."
    exit 0
fi

# Apply
echo ""
echo -e "${GREEN}🚀 Applying Terraform configuration...${NC}"
terraform apply tfplan

# Get service account email
SA_EMAIL=$(terraform output -raw service_account_email)

# Create service account key
echo ""
echo -e "${GREEN}🔑 Creating service account key...${NC}"
KEY_FILE="../gcp-sa-key.json"
gcloud iam service-accounts keys create "$KEY_FILE" \
    --iam-account="$SA_EMAIL" \
    --project="$PROJECT_ID"

echo "✅ Service account key created: $KEY_FILE"

# Output summary
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📋 Summary:"
echo "  Project ID: $PROJECT_ID"
echo "  Service Account: $SA_EMAIL"
echo "  Key File: $KEY_FILE"
echo ""
echo "📝 Next Steps:"
echo "  1. Add the following secrets to GitHub:"
echo "     - GCP_SA_KEY: Contents of $KEY_FILE"
echo "     - GCP_PROJECT_ID: $PROJECT_ID"
echo "     - YOUTUBE_API_KEY: Your YouTube API key"
echo "     - FIREBASE_CREDENTIALS_JSON: Your Firebase credentials JSON"
echo "     - DRY_RUN: False (or True for testing)"
echo ""
echo "  2. Push to main branch to trigger deployment!"
echo ""

