# Secondary Firebase Without Service Account Keys

If your organization restricts service account key creation, you can still use secondary Firebase using **Application Default Credentials**.

## Solution: Use Application Default Credentials

Instead of providing a service account key, grant the Cloud Function's service account access to your secondary Firebase project.

### Step 1: Get Your Cloud Function's Service Account

The Cloud Function uses a default compute service account. Find it:

```bash
# Get your project number
PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)")

# The service account email is:
FUNCTION_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "Cloud Function Service Account: $FUNCTION_SA"
```

### Step 2: Grant Access to Secondary Firebase Project

Grant the Cloud Function's service account Firebase Admin access in your secondary Firebase project:

```bash
# Set variables
PRIMARY_PROJECT_ID="your-primary-project-id"
SECONDARY_PROJECT_ID="your-secondary-firebase-project-id"
PROJECT_NUMBER=$(gcloud projects describe "$PRIMARY_PROJECT_ID" --format="value(projectNumber)")
FUNCTION_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Grant Firebase Admin role in secondary project
gcloud projects add-iam-policy-binding "$SECONDARY_PROJECT_ID" \
  --member="serviceAccount:${FUNCTION_SA}" \
  --role="roles/firebase.admin"
```

### Step 3: Set Secondary Project ID (Optional)

If your secondary Firebase project is different, set the project ID:

**In GitHub Secrets:**
- Add secret: `FIREBASE_PROJECT_ID_SECONDARY`
- Value: Your secondary Firebase project ID

**Or in Cloud Function environment variables:**
```bash
gcloud functions deploy the-word-today-cron \
  --set-env-vars "FIREBASE_PROJECT_ID_SECONDARY=your-secondary-project-id"
```

### Step 4: Deploy

That's it! No service account key needed. The Cloud Function will automatically use Application Default Credentials to access the secondary Firebase project.

## How It Works

1. Cloud Function runs with its default service account
2. That service account has Firebase Admin access to secondary project
3. Firebase Admin SDK uses Application Default Credentials automatically
4. No keys needed!

## Verify It Works

After deployment, check the logs:

```bash
gcloud functions logs read the-word-today-cron \
  --region=us-central1 \
  --limit=50
```

You should see:
```
✅ Secondary Firebase initialized using Application Default Credentials - will write to both projects
🔄 Updated 2025-11-08 [primary] with theWordTodayUrl → ...
🔄 Updated 2025-11-08 [secondary] with theWordTodayUrl → ...
```

## Benefits

- ✅ No service account keys needed
- ✅ Works with organization restrictions
- ✅ More secure (no keys to manage)
- ✅ Automatic credential rotation
- ✅ Simpler setup

## Troubleshooting

### "Permission denied" error

Make sure you granted the correct role:
```bash
# Check current bindings
gcloud projects get-iam-policy SECONDARY_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
```

### "Project not found" error

Set the `FIREBASE_PROJECT_ID_SECONDARY` environment variable to specify which project to use.

### Still not working?

Check that:
1. The Cloud Function's service account has `roles/firebase.admin` in secondary project
2. Firestore is enabled in the secondary Firebase project
3. The secondary project ID is correct

