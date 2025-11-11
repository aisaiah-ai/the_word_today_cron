# Secondary Firebase Setup Without Service Account Keys

## Problem

Firebase Admin SDK service accounts have key creation disabled by organizational policy:
```
ERROR: Key creation is not allowed on this service account
```

## Solution Options

### ✅ Option 1: Download Key from Firebase Console (Recommended)

Even though gcloud CLI key creation is blocked, the Firebase Console usually allows downloading keys.

**Steps:**
1. Go to: https://console.firebase.google.com/project/aisaiah-sfa-dev-app/settings/serviceaccounts/adminsdk
2. Click **Generate New Private Key**
3. Download the JSON file
4. Save as: `/Users/acthercop/.keys/aisaiah-sfa-dev-app-firebase-key.json`
5. Add to GitHub:
   ```bash
   gh secret set FIREBASE_CREDENTIALS_JSON_SECONDARY \
     --body "$(cat /Users/acthercop/.keys/aisaiah-sfa-dev-app-firebase-key.json)"
   ```

### ✅ Option 2: Use Cross-Project Service Account

Grant the primary project's service account access to the secondary Firebase:

**Steps:**

1. Go to secondary project Firebase Console
2. Navigate to: Firestore → Rules or IAM & Admin → IAM
3. Add the primary service account with Firestore permissions:
   ```
   firebase-adminsdk-fbsvc@aisaiahconferencefb.iam.gserviceaccount.com
   ```
4. Grant role: `Cloud Datastore User` or `Firebase Admin`

5. In your deployment, don't set secondary credentials - just set the project ID:
   ```bash
   gh secret set FIREBASE_PROJECT_ID_SECONDARY --body "aisaiah-sfa-dev-app"
   ```

The function will use the primary credentials to access the secondary project.

### ✅ Option 3: Create Custom Service Account

Create a new service account (not Firebase Admin SDK) that doesn't have the restriction:

```bash
# Set to secondary project
gcloud config set project aisaiah-sfa-dev-app

# Create custom service account
gcloud iam service-accounts create firestore-writer \
  --display-name="Firestore Writer for Daily Readings"

# Grant Firestore access
gcloud projects add-iam-policy-binding aisaiah-sfa-dev-app \
  --member="serviceAccount:firestore-writer@aisaiah-sfa-dev-app.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

# Create key (this should work for custom service accounts)
gcloud iam service-accounts keys create \
  /Users/acthercop/.keys/aisaiah-sfa-dev-app-firestore-key.json \
  --iam-account=firestore-writer@aisaiah-sfa-dev-app.iam.gserviceaccount.com

# Add to GitHub
gh secret set FIREBASE_CREDENTIALS_JSON_SECONDARY \
  --body "$(cat /Users/acthercop/.keys/aisaiah-sfa-dev-app-firestore-key.json)"
```

### ✅ Option 4: Use Application Default Credentials (Cloud Functions Only)

If your Cloud Function is deployed in a GCP project that has access to both Firebase projects:

1. Grant the Cloud Function's service account access to secondary Firestore:
   ```bash
   gcloud projects add-iam-policy-binding aisaiah-sfa-dev-app \
     --member="serviceAccount:938552047954-compute@developer.gserviceaccount.com" \
     --role="roles/datastore.user"
   ```

2. Set only the project ID:
   ```bash
   gh secret set FIREBASE_PROJECT_ID_SECONDARY --body "aisaiah-sfa-dev-app"
   ```

The function will use Application Default Credentials (the Cloud Function's service account) to access the secondary Firebase.

## Recommended Approach

**For Production:** Use **Option 1** (Firebase Console download)

**For Quick Setup:** Use **Option 4** (Application Default Credentials)

## Testing

Once you have the key or have configured cross-project access:

```bash
# Deploy
git checkout main
git merge seed_two_accounts
git push origin main

# Test
curl "https://daily-readings-seeder-lwvp6j7v6q-uc.a.run.app?start_date=2025-12-25&end_date=2025-12-25"
```

Look for:
```json
{
  "firebase_projects": ["primary", "secondary"]
}
```

## Verify Data in Secondary Firebase

1. Go to: https://console.firebase.google.com/project/aisaiah-sfa-dev-app/firestore
2. Open collection: `daily_scripture`
3. Check if document `2025-12-25` exists with responsorial psalm data

## Current Implementation

The code is already configured to:
- ✅ Accept secondary credentials via multiple methods
- ✅ Fall back gracefully if secondary fails
- ✅ Use Application Default Credentials if no key provided
- ✅ Log which Firebase project is being used

Just need to provide valid credentials or configure cross-project access!

