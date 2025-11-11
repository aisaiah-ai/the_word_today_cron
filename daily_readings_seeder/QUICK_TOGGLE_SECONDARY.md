# Quick Guide: Enable/Disable Secondary Firebase

## Current Status

By default: **Secondary Firebase is DISABLED**

The seeder only writes to the primary Firebase project unless you explicitly enable secondary.

## To Enable Secondary Firebase

Add ONE of these GitHub secrets:

### Option A: Service Account Key (Recommended)

```bash
# Get your secondary Firebase service account JSON
# Then base64 encode and add as secret:
gh secret set FIREBASE_CREDENTIALS_JSON_B64_SECONDARY --body "$(cat secondary-firebase-key.json | base64)"
```

### Option B: Project ID Only (Uses Application Default Credentials)

```bash
gh secret set FIREBASE_PROJECT_ID_SECONDARY --body "your-secondary-project-id"
```

Push to main to trigger deployment:
```bash
git push origin main
```

## To Disable Secondary Firebase

Remove ALL secondary secrets:

```bash
gh secret delete FIREBASE_CREDENTIALS_JSON_B64_SECONDARY
gh secret delete FIREBASE_PROJECT_ID_SECONDARY
```

Push to main:
```bash
git push origin main
```

That's it! The function automatically detects and adapts.

## Verify Status

Check function logs after deployment:

```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=daily-readings-seeder AND textPayload:\"Firebase\"" \
  --limit=10 \
  --project=aisaiahconferencefb
```

**Look for:**
- ✅ "Secondary Firebase credentials detected - will seed both projects" (enabled)
- ℹ️ "No secondary Firebase configured - seeding primary project only" (disabled)

## What Gets Seeded to Secondary

When enabled, the secondary project gets:
- Same responsorial psalm data as primary
- Same cleanup (deletes readings >2 months old)
- All seeding happens in parallel with primary

## Environment Variables

The function checks for secondary Firebase in this order:

1. `FIREBASE_CREDENTIALS_JSON_SECONDARY` (JSON string)
2. `FIREBASE_CREDENTIALS_JSON_B64_SECONDARY` (base64 encoded)
3. `FIREBASE_CRED_SECONDARY` (file path - local dev only)
4. `FIREBASE_PROJECT_ID_SECONDARY` (uses Application Default Credentials)

If NONE are set → Secondary is disabled ✅

