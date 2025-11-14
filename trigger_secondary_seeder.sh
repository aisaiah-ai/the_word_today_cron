#!/bin/bash
# Trigger secondary seeder using Workload Identity Federation
# This script uses the same authentication method as the deployment workflow

set -e

echo "🔐 Authenticating with Workload Identity Federation..."
echo "Using secrets: WORKLOAD_IDENTITY_PROVIDER_SECONDARY and SERVICE_ACCOUNT_SECONDARY"

# Note: This requires the secrets to be available
# In GitHub Actions, this is done via google-github-actions/auth@v2
# For local execution, you'd need to set up gcloud with Workload Identity

echo ""
echo "Triggering secondary function via HTTP with authentication..."
echo "Function: daily-readings-seeder-secondary"
echo "Project: aisaiah-sfa-dev-app"
echo "URL: https://daily-readings-seeder-secondary-n6patcgpoa-uc.a.run.app"
echo ""
echo "Since direct HTTP access requires authentication, we'll use:"
echo "1. Cloud Scheduler (if job exists)"
echo "2. Or gcloud functions call with proper auth"

