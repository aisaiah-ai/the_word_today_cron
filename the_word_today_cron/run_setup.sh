#!/bin/bash

# Simple setup runner that checks what's needed

cd "$(dirname "$0")"

echo "🚀 Setup Runner - The Word Today Cron"
echo "======================================"
echo ""

# Check what we have
GCP_PROJECT=$(gcloud config get-value project 2>/dev/null)
REPO="aisaiah-ai/the_word_today_cron"

echo "✅ Detected:"
echo "   GCP Project: ${GCP_PROJECT:-'NOT SET'}"
echo "   GitHub Repo: $REPO"
echo ""

# Check existing secrets
echo "📋 Checking GitHub Secrets..."
SECRETS=$(gh secret list --repo "$REPO" 2>/dev/null | grep -E "GCP_PROJECT_ID|YOUTUBE_API_KEY|FIREBASE_CREDENTIALS_JSON" || echo "")

if [ -n "$SECRETS" ]; then
    echo "   Some secrets already exist:"
    echo "$SECRETS" | sed 's/^/   - /'
    echo ""
    read -p "Do you want to update/recreate secrets? (y/n): " UPDATE
    if [[ "$UPDATE" != "y" && "$UPDATE" != "Y" ]]; then
        echo "Skipping secret setup. Run with existing secrets."
        exit 0
    fi
fi

echo ""
echo "📝 What's needed:"
echo ""
echo "1. YouTube API Key"
echo "   Get it at: https://console.cloud.google.com/apis/credentials?project=$GCP_PROJECT"
echo ""
read -p "   Enter YouTube API Key (or press Enter to skip): " YT_KEY

echo ""
echo "2. Firebase Service Account Key"
echo "   Get it at: https://console.firebase.google.com/project/$GCP_PROJECT/settings/serviceaccounts/adminsdk"
echo ""
read -p "   Enter path to Firebase JSON key file (or press Enter to skip): " FB_PATH

# Export for non-interactive script
if [ -n "$YT_KEY" ]; then
    export YOUTUBE_API_KEY="$YT_KEY"
fi

if [ -n "$FB_PATH" ] && [ -f "$FB_PATH" ]; then
    export FIREBASE_KEY_PATH="$FB_PATH"
fi

if [ -n "$YT_KEY" ] && [ -n "$FB_PATH" ] && [ -f "$FB_PATH" ]; then
    echo ""
    echo "🚀 Running full setup..."
    ./setup_non_interactive.sh
else
    echo ""
    echo "⚠️  Missing required values. Please run again with:"
    echo ""
    echo "export YOUTUBE_API_KEY='your-key'"
    echo "export FIREBASE_KEY_PATH='/path/to/firebase-key.json'"
    echo "./setup_non_interactive.sh"
    echo ""
    echo "Or run the interactive setup:"
    echo "./setup_complete.sh"
fi
