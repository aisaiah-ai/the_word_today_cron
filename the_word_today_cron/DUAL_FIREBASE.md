# Dual Firebase Support

The Word Today service now supports writing to **two different Firebase projects** simultaneously. This allows you to sync data across multiple Firebase projects.

## How It Works

The service automatically detects if secondary Firebase credentials are provided and writes to both projects:

1. **Primary Firebase** - Always writes (required)
2. **Secondary Firebase** - Writes only if credentials are provided (optional)

## Configuration

### Primary Firebase (Required)

Set up as before using one of these environment variables:
- `FIREBASE_CREDENTIALS_JSON` - JSON string
- `FIREBASE_CREDENTIALS_JSON_B64` - Base64 encoded JSON
- `FIREBASE_CRED` - Path to credentials file

### Secondary Firebase (Optional)

To enable dual Firebase writes, provide secondary credentials using one of these:

**Environment Variables:**
- `FIREBASE_CREDENTIALS_JSON_SECONDARY` - JSON string
- `FIREBASE_CREDENTIALS_JSON_B64_SECONDARY` - Base64 encoded JSON  
- `FIREBASE_CRED_SECONDARY` - Path to credentials file

**GitHub Secrets:**
- `FIREBASE_CREDENTIALS_JSON_SECONDARY` - JSON string of secondary Firebase service account key

## GitHub Actions Setup

### Option 1: Using GitHub Secrets (Recommended)

1. Go to your GitHub repository → **Settings → Secrets and variables → Actions**
2. Add a new secret:
   - Name: `FIREBASE_CREDENTIALS_JSON_SECONDARY`
   - Value: The entire JSON content of your secondary Firebase service account key file

The deployment workflow will automatically:
- Detect the secondary credentials
- Base64 encode them
- Pass them to the Cloud Function as `FIREBASE_CREDENTIALS_JSON_B64_SECONDARY`

### Option 2: Manual Environment Variable

You can also set the environment variable directly in the Cloud Function:

```bash
gcloud functions deploy the-word-today-cron \
  --gen2 \
  --set-env-vars "FIREBASE_CREDENTIALS_JSON_B64_SECONDARY=<base64-encoded-json>"
```

## Behavior

### With Secondary Credentials

When secondary credentials are provided:
- ✅ Writes to **both** Firebase projects
- ✅ If secondary write fails, continues with primary (logs warning)
- ✅ Logs indicate which project each write goes to: `[primary]` or `[secondary]`

### Without Secondary Credentials

When secondary credentials are NOT provided:
- ✅ Writes only to primary Firebase (normal operation)
- ✅ No errors or warnings
- ✅ Backward compatible with existing deployments

## Example Logs

### With Dual Firebase:
```
✅ Primary Firebase initialized
✅ Secondary Firebase credentials detected - will write to both projects
✅ Secondary Firebase initialized
🔄 Updated 2025-11-08 [primary] with theWordTodayUrl → https://...
🔄 Updated 2025-11-08 [secondary] with theWordTodayUrl → https://...
```

### Without Secondary Firebase:
```
✅ Primary Firebase initialized
🔄 Updated 2025-11-08 [primary] with theWordTodayUrl → https://...
```

## Use Cases

- **Backup/Sync**: Keep a backup copy of data in a second Firebase project
- **Multi-Environment**: Write to both production and staging
- **Multi-App**: Sync data between different applications
- **Migration**: Gradually migrate data to a new Firebase project

## Error Handling

- If secondary Firebase initialization fails, the service continues with primary only
- If a write to secondary fails, it logs a warning but continues processing
- Primary Firebase writes always take priority

## Testing

### Test Locally

```bash
# Set both credentials
export FIREBASE_CREDENTIALS_JSON='{"type":"service_account",...}'
export FIREBASE_CREDENTIALS_JSON_SECONDARY='{"type":"service_account",...}'

# Run the service
python3 the_word_today_service.py
```

### Test in Cloud Function

Set `DRY_RUN=True` to see what would be written without actually saving:

```bash
gcloud functions deploy the-word-today-cron \
  --set-env-vars "DRY_RUN=True"
```

## Security Notes

- Both credentials are stored securely in GitHub Secrets
- Credentials are base64 encoded during deployment
- Never commit credentials to the repository
- Use service account keys with minimal required permissions

