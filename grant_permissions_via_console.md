# How to Grant Cloud Build Permissions via Console

Since CLI access is restricted, use the GCP Console:

## Step 1: Go to IAM & Admin

**Link:** https://console.cloud.google.com/iam-admin/iam?project=aisaiah-sfa-dev-app

## Step 2: Find the Service Account

Look for: `512102198745-compute@developer.gserviceaccount.com`

This is the **Cloud Build service account** (automatically created by GCP).

## Step 3: Grant Required Roles

Click the **pencil icon (Edit)** next to the service account.

Add these roles:
1. ✅ **Cloud Build Service Account** (`roles/cloudbuild.builds.builder`)
2. ✅ **Cloud Functions Admin** (`roles/cloudfunctions.admin`)
3. ✅ **Service Account User** (`roles/iam.serviceAccountUser`)

Click **Save**.

## Step 4: Verify

After granting permissions, wait 1-2 minutes for propagation.

Then check GitHub Actions:
https://github.com/aisaiah-ai/the_word_today_cron/actions

Re-run the secondary deployment workflow if needed.

## Alternative: Grant via Project Owner

If you don't have console access either, ask the project owner to run:

```bash
gcloud projects add-iam-policy-binding aisaiah-sfa-dev-app \
  --member="serviceAccount:512102198745-compute@developer.gserviceaccount.com" \
  --role="roles/cloudbuild.builds.builder"

gcloud projects add-iam-policy-binding aisaiah-sfa-dev-app \
  --member="serviceAccount:512102198745-compute@developer.gserviceaccount.com" \
  --role="roles/cloudfunctions.admin"

gcloud projects add-iam-policy-binding aisaiah-sfa-dev-app \
  --member="serviceAccount:512102198745-compute@developer.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

