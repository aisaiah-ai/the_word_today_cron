#!/bin/bash

# Complete Setup Automation Script
# This script runs both GCP and GitHub setup in sequence

set -e

echo "🚀 Complete Setup Automation for The Word Today Cron"
echo "===================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Step 1: GCP Setup
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 1: GCP Setup${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ -f "$SCRIPT_DIR/setup_gcp.sh" ]; then
    chmod +x "$SCRIPT_DIR/setup_gcp.sh"
    bash "$SCRIPT_DIR/setup_gcp.sh"
else
    echo -e "${RED}❌ setup_gcp.sh not found${NC}"
    exit 1
fi

# Get the key file path
KEY_FILE="${SCRIPT_DIR}/../gcp-sa-key.json"
if [ ! -f "$KEY_FILE" ]; then
    KEY_FILE="${SCRIPT_DIR}/gcp-sa-key.json"
fi

if [ ! -f "$KEY_FILE" ]; then
    read -p "Enter path to the GCP service account key file: " KEY_FILE
fi

if [ ! -f "$KEY_FILE" ]; then
    echo -e "${RED}❌ Key file not found: $KEY_FILE${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 2: GitHub Setup${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Update setup_github.sh to use the key file
if [ -f "$SCRIPT_DIR/setup_github.sh" ]; then
    chmod +x "$SCRIPT_DIR/setup_github.sh"
    
    # Export key file path so setup_github.sh can use it
    export GCP_SA_KEY_FILE="$KEY_FILE"
    
    echo -e "${GREEN}Using GCP key file: $KEY_FILE${NC}"
    echo ""
    bash "$SCRIPT_DIR/setup_github.sh"
else
    echo -e "${RED}❌ setup_github.sh not found${NC}"
    exit 1
fi

# Final summary
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Complete Setup Finished!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Next steps:"
echo "1. Review the configuration in .github/workflows/deploy.yml"
echo "2. Commit and push your code to the main branch:"
echo "   git add ."
echo "   git commit -m 'Setup automated deployment'"
echo "   git push origin main"
echo ""
echo "3. GitHub Actions will automatically:"
echo "   - Deploy the Cloud Function"
echo "   - Create Cloud Scheduler jobs for 4 AM and 9 AM ET"
echo ""
echo "4. Monitor the deployment:"
echo "   - GitHub Actions tab in your repository"
echo "   - GCP Cloud Functions console"
echo "   - GCP Cloud Scheduler console"
echo ""
echo -e "${YELLOW}⚠️  Remember to clean up the key file after adding it to GitHub Secrets!${NC}"
echo ""
