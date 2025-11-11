# Separate Deployments Approach (Recommended)

## Overview

Instead of one Cloud Function accessing two Firebase projects, deploy **two separate Cloud Functions**:

- **Primary Function** → Deployed to primary GCP project → Seeds primary Firebase
- **Secondary Function** → Deployed to secondary GCP project → Seeds secondary Firebase

## Why This is Better

✅ **No cross-project permissions needed**
✅ **No service account keys needed** - Uses Application Default Credentials
✅ **No organizational policy restrictions**
✅ **Each function runs in same project as its Firebase database**
✅ **Easy to enable/disable** - Just enable/disable the workflow
✅ **Independent scaling and monitoring**

## Architecture

```
PRIMARY DEPLOYMENT
GitHub → Workflow (deploy.yml) → GCP Project: aisaiahconferencefb
                                   ↓
                              Cloud Function: daily-readings-seeder
                                   ↓
                              Cloud Scheduler (monthly on 15th)
                                   ↓
                              Firebase: aisaiahconferencefb

SECONDARY DEPLOYMENT (Optional)
GitHub → Workflow (deploy-secondary.yml) → GCP Project: aisaiah-sfa-dev-app
                                            ↓
                                       Cloud Function: daily-readings-seeder-secondary
                                            ↓
                                       Cloud Scheduler (monthly on 15th)
                                            ↓
                                       Firebase: aisaiah-sfa-dev-app
```

## Setup

### Prerequisites

You need two GitHub Secrets:

1. **Primary Project** (already set):
   - `GCP_SA_KEY` - Service account for aisaiahconferencefb
   - `GCP_PROJECT_ID` - `aisaiahconferencefb`
   - `FIREBASE_CREDENTIALS_JSON` - Primary Firebase credentials

2. **Secondary Project** (new):
   - `GCP_SA_KEY_SECONDARY` - Service account for aisaiah-sfa-dev-app
   - `GCP_PROJECT_ID_SECONDARY` - `aisaiah-sfa-dev-app`

### Enable Secondary Deployment

**File:** `.github/workflows/deploy-daily-readings-seeder-secondary.yml`

This workflow:
- Deploys to the secondary GCP project
- Uses `GCP_SA_KEY_SECONDARY` for authentication
- Creates a separate Cloud Function
- Creates a separate Cloud Scheduler job
- No Firebase credentials needed (uses Application Default Credentials)

### Disable Secondary Deployment

**Option A: Rename workflow file**
```bash
mv .github/workflows/deploy-daily-readings-seeder-secondary.yml \
   .github/workflows/deploy-daily-readings-seeder-secondary.yml.disabled
```

**Option B: Delete the workflow file**
```bash
git rm .github/workflows/deploy-daily-readings-seeder-secondary.yml
```

**Option C: Delete the Cloud Function and Scheduler**
```bash
gcloud functions delete daily-readings-seeder-secondary \
  --region=us-central1 \
  --project=aisaiah-sfa-dev-app

gcloud scheduler jobs delete daily-readings-seeder-secondary-monthly-15th \
  --location=us-central1 \
  --project=aisaiah-sfa-dev-app
```

## Required GitHub Secrets for Secondary

### 1. GCP_SA_KEY_SECONDARY

Service account key for deploying to `aisaiah-sfa-dev-app` project.

**Get it from:**
1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts?project=aisaiah-sfa-dev-app
2. Create or use existing service account for GitHub Actions
3. Generate key (this is for GitHub Actions, NOT Firebase - should work)
4. Add to GitHub:
   ```bash
   gh secret set GCP_SA_KEY_SECONDARY --body "$(cat github-actions-key.json)"
   ```

### 2. GCP_PROJECT_ID_SECONDARY

```bash
gh secret set GCP_PROJECT_ID_SECONDARY --body "aisaiah-sfa-dev-app"
```

## Benefits

### No Firebase Keys Needed

The Cloud Function uses **Application Default Credentials** because:
- Function runs in the same GCP project as Firebase
- Automatically has access to Firebase in the same project
- No manual key management

### Independent Management

- Each deployment is independent
- Can disable secondary without touching primary
- Separate logs and monitoring
- Separate billing tracking

### No Organizational Policy Issues

- No cross-project permissions needed
- No Firebase Admin SDK key creation
- Service account for GitHub Actions deployment still works (different restriction)

## Testing

### Test Primary Only
```bash
# Just push code - only primary workflow runs
git push origin main
```

### Test Both Deployments
```bash
# Add secondary secrets
gh secret set GCP_SA_KEY_SECONDARY --body "$(cat secondary-github-actions-key.json)"
gh secret set GCP_PROJECT_ID_SECONDARY --body "aisaiah-sfa-dev-app"

# Push code - both workflows run
git push origin main
```

## Verification

### Check Primary Function
```bash
curl "https://daily-readings-seeder-lwvp6j7v6q-uc.a.run.app?start_date=2025-12-25&end_date=2025-12-25"
```

### Check Secondary Function
```bash
# Get secondary function URL
gcloud functions describe daily-readings-seeder-secondary \
  --gen2 \
  --region=us-central1 \
  --project=aisaiah-sfa-dev-app \
  --format="value(serviceConfig.uri)"

# Test it
curl "<secondary-function-url>?start_date=2025-12-25&end_date=2025-12-25"
```

### Check Both Firestore Databases

**Primary:** https://console.firebase.google.com/project/aisaiahconferencefb/firestore

**Secondary:** https://console.firebase.google.com/project/aisaiah-sfa-dev-app/firestore

Both should have the same `daily_scripture` documents with responsorial psalm data.

## Summary

**Elegant Solution:**
- Two independent deployments
- No cross-project complexity
- No Firebase key management
- Easy enable/disable
- Bypasses all organizational policies
- Each function runs in its own GCP project, accessing its own Firebase naturally

This is the **recommended approach** for multi-Firebase seeding with organizational restrictions.

