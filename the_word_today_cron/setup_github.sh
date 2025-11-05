#!/bin/bash

# GitHub Setup Automation Script
# This script helps automate the GitHub repository setup for The Word Today cron job

set -e

echo "🚀 GitHub Setup Automation for The Word Today Cron"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}⚠️  GitHub CLI (gh) not found.${NC}"
    echo "Installing GitHub CLI..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install gh
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update && sudo apt-get install gh -y
    else
        echo -e "${RED}❌ Please install GitHub CLI manually: https://cli.github.com/${NC}"
        exit 1
    fi
fi

# Check if jq is installed (needed for JSON processing)
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}⚠️  jq not found.${NC}"
    echo "Installing jq..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install jq
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update && sudo apt-get install jq -y
    else
        echo -e "${RED}❌ Please install jq manually: https://stedolan.github.io/jq/${NC}"
        exit 1
    fi
fi

# Check if user is logged in to GitHub
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to GitHub.${NC}"
    echo "Please authenticate with GitHub..."
    gh auth login
fi

# Get repository information
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}GitHub Repository Setup${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Try to detect current git repository
CURRENT_REPO=""
if [ -d "../.git" ]; then
    GIT_REMOTE=$(cd .. && git remote get-url origin 2>/dev/null | sed -E 's/.*github.com[:/]([^/]+\/[^/]+)(\.git)?$/\1/' | head -1)
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

# Default to aisaiah-ai/the_word_today_cron if nothing detected
if [ -z "$CURRENT_REPO" ]; then
    CURRENT_REPO="aisaiah-ai/the_word_today_cron"
    echo -e "${GREEN}📋 Using default repository: ${CURRENT_REPO}${NC}"
fi

if [ -n "$CURRENT_REPO" ]; then
    read -p "Enter GitHub repository (format: owner/repo) [$CURRENT_REPO]: " REPO
    REPO=${REPO:-$CURRENT_REPO}
else
    echo -e "${YELLOW}ℹ️  Repository format: username/repository-name${NC}"
    echo -e "${YELLOW}   Example: johnsmith/python-cron${NC}"
    echo -e "${YELLOW}   If you don't have a repo, create one at: https://github.com/new${NC}"
    echo ""
    read -p "Enter GitHub repository (format: owner/repo): " REPO
fi

# Get GCP Project ID (with detection)
GCP_PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -n "$GCP_PROJECT_ID" ]; then
    echo -e "${GREEN}📋 Detected GCP project: ${GCP_PROJECT_ID}${NC}"
    read -p "Enter GCP Project ID [$GCP_PROJECT_ID]: " GCP_PROJECT_INPUT
    GCP_PROJECT_ID=${GCP_PROJECT_INPUT:-$GCP_PROJECT_ID}
else
    read -p "Enter GCP Project ID: " GCP_PROJECT_ID
fi

echo ""
echo -e "${GREEN}📋 Setting up GitHub Secrets...${NC}"
echo ""

# Get GCP Service Account Key
if [ -n "$GCP_SA_KEY_FILE" ] && [ -f "$GCP_SA_KEY_FILE" ]; then
    SA_KEY_PATH="$GCP_SA_KEY_FILE"
    echo -e "${GREEN}Using provided GCP key file: $SA_KEY_PATH${NC}"
else
    read -p "Enter path to GCP Service Account JSON key file: " SA_KEY_PATH
    if [ ! -f "$SA_KEY_PATH" ]; then
        echo -e "${RED}❌ File not found: $SA_KEY_PATH${NC}"
        exit 1
    fi
fi

# Get YouTube API Key
read -p "Enter YouTube API Key: " YOUTUBE_API_KEY

# Get Firebase Credentials
read -p "Enter path to Firebase service account JSON file: " FIREBASE_KEY_PATH
if [ ! -f "$FIREBASE_KEY_PATH" ]; then
    echo -e "${RED}❌ File not found: $FIREBASE_KEY_PATH${NC}"
    exit 1
fi

# Convert Firebase JSON to single line
FIREBASE_CREDENTIALS_JSON=$(cat "$FIREBASE_KEY_PATH" | jq -c .)

# Optional DRY_RUN
read -p "Enable DRY_RUN mode? (y/n, default: n): " DRY_RUN_INPUT
DRY_RUN="False"
if [[ "$DRY_RUN_INPUT" == "y" || "$DRY_RUN_INPUT" == "Y" ]]; then
    DRY_RUN="True"
fi

# Set secrets using GitHub CLI
echo ""
echo -e "${GREEN}🔐 Setting GitHub secrets...${NC}"

gh secret set GCP_PROJECT_ID --repo "$REPO" --body "$GCP_PROJECT_ID"
echo "✅ Set GCP_PROJECT_ID"

gh secret set GCP_SA_KEY --repo "$REPO" < "$SA_KEY_PATH"
echo "✅ Set GCP_SA_KEY"

gh secret set YOUTUBE_API_KEY --repo "$REPO" --body "$YOUTUBE_API_KEY"
echo "✅ Set YOUTUBE_API_KEY"

echo "$FIREBASE_CREDENTIALS_JSON" | gh secret set FIREBASE_CREDENTIALS_JSON --repo "$REPO"
echo "✅ Set FIREBASE_CREDENTIALS_JSON"

gh secret set DRY_RUN --repo "$REPO" --body "$DRY_RUN"
echo "✅ Set DRY_RUN"

echo ""
echo -e "${GREEN}✅ All secrets have been configured!${NC}"
echo ""
echo "Next steps:"
echo "1. Push your code to the main branch"
echo "2. GitHub Actions will automatically deploy your Cloud Function"
echo ""
echo "To verify secrets were set correctly:"
echo "  gh secret list --repo $REPO"
echo ""
