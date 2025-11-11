# Setup Workload Identity for Secondary Project (Keyless)

## Problem

**ALL service account key creation is blocked** in the secondary project (`aisaiah-sfa-dev-app`):
```
ERROR: Key creation is not allowed on this service account
constraints/iam.disableServiceAccountKeyCreation
```

This applies to:
- ❌ Firebase Admin SDK service accounts
- ❌ Custom service accounts
- ❌ GitHub Actions service accounts
- ❌ ALL service accounts

## ✅ Solution: Workload Identity Federation (Keyless)

Workload Identity Federation allows GitHub Actions to authenticate to GCP **without service account keys**.

### Setup Steps

Run these commands (requires admin access to aisaiah-sfa-dev-app):

```bash
# Set project
gcloud config set project aisaiah-sfa-dev-app

# Enable required APIs
gcloud services enable iamcredentials.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
gcloud services enable sts.googleapis.com

# Create Workload Identity Pool
gcloud iam workload-identity-pools create "github-pool" \
  --location="global" \
  --display-name="GitHub Actions Pool"

# Create Workload Identity Provider
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Create service account (if not exists)
gcloud iam service-accounts create github-actions-deploy \
  --display-name="GitHub Actions Deployment"

# Grant roles
gcloud projects add-iam-policy-binding aisaiah-sfa-dev-app \
  --member="serviceAccount:github-actions-deploy@aisaiah-sfa-dev-app.iam.gserviceaccount.com" \
  --role="roles/cloudfunctions.developer"

gcloud projects add-iam-policy-binding aisaiah-sfa-dev-app \
  --member="serviceAccount:github-actions-deploy@aisaiah-sfa-dev-app.iam.gserviceaccount.com" \
  --role="roles/cloudscheduler.admin"

gcloud projects add-iam-policy-binding aisaiah-sfa-dev-app \
  --member="serviceAccount:github-actions-deploy@aisaiah-sfa-dev-app.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding aisaiah-sfa-dev-app \
  --member="serviceAccount:github-actions-deploy@aisaiah-sfa-dev-app.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding aisaiah-sfa-dev-app \
  --member="serviceAccount:github-actions-deploy@aisaiah-sfa-dev-app.iam.gserviceaccount.com" \
  --role="roles/run.admin"

# Allow GitHub repository to impersonate service account
gcloud iam service-accounts add-iam-policy-binding \
  github-actions-deploy@aisaiah-sfa-dev-app.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/aisaiah-ai/the_word_today_cron"

# Get PROJECT_NUMBER first:
PROJECT_NUMBER=$(gcloud projects describe aisaiah-sfa-dev-app --format="value(projectNumber)")
echo "Project Number: $PROJECT_NUMBER"

# Then run the binding with actual project number:
gcloud iam service-accounts add-iam-policy-binding \
  github-actions-deploy@aisaiah-sfa-dev-app.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/attribute.repository/aisaiah-ai/the_word_today_cron"
```

### Get Workload Identity Provider Name

```bash
gcloud iam workload-identity-pools providers describe github-provider \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --format="value(name)"
```

This gives you: `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider`

### Update GitHub Workflow

Update `.github/workflows/deploy-daily-readings-seeder-secondary.yml`:

```yaml
- name: 🔐 Authenticate to Google Cloud (Secondary Project)
  uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: 'projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider'
    service_account: 'github-actions-deploy@aisaiah-sfa-dev-app.iam.gserviceaccount.com'
```

Remove the `credentials_json` line - Workload Identity doesn't need it!

### Add GitHub Secrets

```bash
gh secret set WORKLOAD_IDENTITY_PROVIDER_SECONDARY --body "projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider"

gh secret set SERVICE_ACCOUNT_SECONDARY --body "github-actions-deploy@aisaiah-sfa-dev-app.iam.gserviceaccount.com"

gh secret set GCP_PROJECT_ID_SECONDARY --body "aisaiah-sfa-dev-app"
```

## Benefits

✅ **No service account keys** - Keyless authentication
✅ **More secure** - Keys can't be leaked
✅ **Bypasses key creation restriction** - Doesn't need keys
✅ **Works with org policies** - Recommended by Google

## Alternative: Manual Deployment

If Workload Identity setup requires admin approval, you can manually deploy the secondary function:

```bash
gcloud config set project aisaiah-sfa-dev-app

# Authenticate
gcloud auth login

# Deploy function (uses your user credentials)
gcloud functions deploy daily-readings-seeder-secondary \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=daily_readings_seeder \
  --entry-point=seed_daily_readings_cron \
  --trigger-http \
  --allow-unauthenticated \
  --memory=512MB \
  --timeout=540s \
  --max-instances=10 \
  --set-env-vars="DRY_RUN=False"

# Create scheduler
FUNCTION_URL=$(gcloud functions describe daily-readings-seeder-secondary --gen2 --region=us-central1 --format="value(serviceConfig.uri)")

gcloud scheduler jobs create http daily-readings-seeder-secondary-monthly-15th \
  --location=us-central1 \
  --schedule="0 7 15 * *" \
  --uri="$FUNCTION_URL" \
  --http-method=GET \
  --time-zone="America/New_York" \
  --description="Monthly seeding of daily readings - secondary Firebase"
```

This deploys using your personal credentials. The function itself uses Application Default Credentials to access Firebase (no keys needed).

