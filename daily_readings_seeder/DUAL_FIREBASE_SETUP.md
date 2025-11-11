# Dual Firebase Setup for Daily Readings Seeder

The Daily Readings Seeder now supports seeding to **two Firebase projects simultaneously**.

## How It Works

The seeder will:
1. Always seed to the **primary** Firebase project
2. Optionally seed to a **secondary** Firebase project if configured
3. Clean up old readings (>2 months) from both projects

## Enabling Secondary Firebase

To enable seeding to a second Firebase project, set one of these environment variables:

### Option 1: Using Service Account Credentials (Recommended for Production)

Add the following GitHub Secrets:

```bash
# Secondary Firebase credentials (base64 encoded)
FIREBASE_CREDENTIALS_JSON_B64_SECONDARY=<base64-encoded-json>

# OR as raw JSON
FIREBASE_CREDENTIALS_JSON_SECONDARY=<json-string>
```

### Option 2: Using Application Default Credentials

Set the project ID:

```bash
FIREBASE_PROJECT_ID_SECONDARY=<your-secondary-project-id>
```

The function will use Application Default Credentials to access the secondary project.

### Option 3: Local Development

For local testing:

```bash
export FIREBASE_CRED_SECONDARY=/path/to/secondary-firebase-key.json
```

## Disabling Secondary Firebase

To disable secondary Firebase seeding:

1. **Remove** or **don't set** any of these environment variables:
   - `FIREBASE_CREDENTIALS_JSON_B64_SECONDARY`
   - `FIREBASE_CREDENTIALS_JSON_SECONDARY`
   - `FIREBASE_PROJECT_ID_SECONDARY`
   - `FIREBASE_CRED_SECONDARY`

2. If none of these are set, the seeder will **only** seed to the primary Firebase project.

## GitHub Actions Deployment

Update `.github/workflows/deploy-daily-readings-seeder.yml`:

```yaml
- name: 📤 Deploy Cloud Function
  env:
    DRY_RUN: ${{ secrets.DRY_RUN || 'False' }}
  run: |
    # ... existing Firebase primary encoding ...
    
    # Process secondary Firebase credentials if provided (optional)
    ENV_VARS="DRY_RUN=${DRY_RUN},FIREBASE_CREDENTIALS_JSON_B64='${FIREBASE_CREDENTIALS_B64}'"
    
    if [ -n "${{ secrets.FIREBASE_CREDENTIALS_JSON_SECONDARY }}" ]; then
      echo "✅ Secondary Firebase credentials detected - will seed both projects"
      printf '%s\n' '${{ secrets.FIREBASE_CREDENTIALS_JSON_SECONDARY }}' > /tmp/firebase-creds-secondary.json
      
      if [ -s /tmp/firebase-creds-secondary.json ]; then
        FIREBASE_CREDENTIALS_B64_SECONDARY=$(cat /tmp/firebase-creds-secondary.json | base64 -w 0 2>/dev/null || cat /tmp/firebase-creds-secondary.json | base64 | tr -d '\n')
        ENV_VARS="${ENV_VARS},FIREBASE_CREDENTIALS_JSON_B64_SECONDARY=${FIREBASE_CREDENTIALS_B64_SECONDARY}"
        rm -f /tmp/firebase-creds-secondary.json
      fi
    else
      echo "ℹ️ No secondary Firebase credentials provided - will only seed primary project"
    fi
    
    # Deploy with credentials
    gcloud functions deploy daily-readings-seeder \
      --set-env-vars "${ENV_VARS}"
```

## Environment Variables Summary

### Primary Firebase (Required)

| Variable | Description |
|----------|-------------|
| `FIREBASE_CREDENTIALS_JSON` | Firebase credentials (JSON string) |
| `FIREBASE_CREDENTIALS_JSON_B64` | Firebase credentials (base64 encoded) |
| `FIREBASE_CRED` | Firebase credentials file path (local dev) |

### Secondary Firebase (Optional)

| Variable | Description |
|----------|-------------|
| `FIREBASE_CREDENTIALS_JSON_SECONDARY` | Secondary Firebase credentials (JSON string) |
| `FIREBASE_CREDENTIALS_JSON_B64_SECONDARY` | Secondary Firebase credentials (base64 encoded) |
| `FIREBASE_CRED_SECONDARY` | Secondary Firebase credentials file path (local dev) |
| `FIREBASE_PROJECT_ID_SECONDARY` | Secondary Firebase project ID (for Application Default Credentials) |

## Testing Dual Firebase

### Test Locally

```bash
# Set primary Firebase
export FIREBASE_CRED=/path/to/primary-firebase-key.json

# Set secondary Firebase (optional)
export FIREBASE_CRED_SECONDARY=/path/to/secondary-firebase-key.json

# Run in dry run mode
export DRY_RUN=True

# Test the function
python3 main.py
```

### Deploy and Test

1. Set GitHub Secrets for secondary Firebase
2. Push to main (or trigger workflow manually)
3. Check function logs to verify both projects are being seeded:

```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=daily-readings-seeder" \
  --limit=50
```

Look for log messages like:
- ✅ Secondary Firebase credentials detected
- ✅ Secondary Firebase initialized
- 🗑️  Deleting readings older than... from secondary

## Response Format

When dual Firebase is enabled, the response will indicate both projects:

```json
{
  "body": {
    "firebase_projects": ["primary", "secondary"],
    "cleanup": {
      "primary": {
        "deleted_count": 42,
        "errors": []
      },
      "secondary": {
        "deleted_count": 42,
        "errors": []
      }
    },
    "successful": ["2025-12-01", "2025-12-02", ...]
  }
}
```

## Quick Enable/Disable

**To enable secondary seeding:**
```bash
# Add GitHub secret
gh secret set FIREBASE_CREDENTIALS_JSON_B64_SECONDARY --body "$(cat secondary-key.json | base64)"
```

**To disable secondary seeding:**
```bash
# Remove GitHub secret
gh secret delete FIREBASE_CREDENTIALS_JSON_B64_SECONDARY
```

The next deployment will automatically adapt to the presence or absence of secondary credentials.

