# Daily Readings Seeder - Firebase Data Seeding

This Cloud Function seeds Firebase Firestore with daily scripture readings data, including:
- USCCB daily reading references and URLs (no full text due to licensing)
- Public domain scripture text for display
- Liturgical feast information
- Complete daily scripture data structure

## 📋 Overview

This function:
- Seeds daily scripture readings for days 1-30 of the next month
- Fetches USCCB reading references (NOT full text - licensing compliance)
- Fetches public domain scripture text (World English Bible, KJV, etc.)
- Extracts responsorial psalm verse, text, and response/refrain
- Links liturgical feast information
- Automatically deletes readings older than 2 months (cleanup)
- Runs monthly on the 15th via Cloud Scheduler to seed next month's readings
- Deploys automatically via GitHub Actions on push to `main`

## 🏗️ Architecture

```
GitHub Repository
    ↓ (on push to main)
GitHub Actions Workflow
    ↓
Deploy Cloud Function (Gen2)
    ↓
Create/Update Cloud Scheduler Job (Monthly)
    ↓
Monthly Execution (15th of each month)
    ↓
Daily Readings Seeder
    ↓
Seeds days 1-30 of next month
    ↓
Firebase Firestore (daily_scripture collection)
```

## 🚀 Quick Start

### Prerequisites

1. **Google Cloud Project** with billing enabled
2. **GitHub Repository** with Actions enabled
3. **Firebase Project** configured
4. **Required GCP APIs enabled**:
   - Cloud Functions API
   - Cloud Scheduler API
   - Cloud Build API
   - Cloud Logging API

### Deployment

The function deploys automatically when you push to `main`. Or deploy manually:

```bash
cd daily_readings_seeder
gcloud functions deploy daily-readings-seeder \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=seed_daily_readings_cron \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars DRY_RUN=False,FIREBASE_CREDENTIALS_JSON_B64='your-base64-encoded-credentials'
```

## ⏰ Schedule

The function runs automatically:
- **Monthly** on the 15th of each month at 2 AM Eastern Time (7 AM UTC)
- Seeds readings for days 1-30 of the next month
- Example: If run on November 15th, it seeds December 1-30
- Cleans up readings older than 2 months (keeps last 2 months only)
- Example: If run in November, deletes all readings before September 1

## 📊 Data Model

### Daily Scripture Document (`daily_scripture/{yyyy-MM-dd}`)

```json
{
  "id": "2025-11-05",
  "title": "Daily Scripture",
  "reference": "John 3:16",
  "body": "[Gospel text]",
  "gospel": "[Gospel text]",
  "gospel_verse": "John 3:16",
  "first_reading": "[First reading text or null]",
  "first_reading_verse": "[Reference or null]",
  "second_reading": "[Second reading text or null]",
  "second_reading_verse": "[Reference or null]",
  "responsorial_psalm": "[Psalm text from bible-api.com]",
  "responsorial_psalm_verse": "Psalm 112:1b-2, 4-5, 9",
  "responsorial_psalm_response": "Blessed the man who is gracious and lends to those in need.",
  "usccb_link": "https://bible.usccb.org/bible/readings/110525.cfm",
  "theWordTodayUrl": "[Video URL]",
  "cfcOnlyByGraceReflectionsUrl": "[Video URL]",
  "boSanchezFullTank": "[Video URL]",
  "feast": null,
  "updatedAt": "2025-11-05T10:00:00Z"
}
```

## 🔧 Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `FIREBASE_CREDENTIALS_JSON_B64` | Primary Firebase credentials (base64) | - | ✅ Yes* |
| `FIREBASE_CREDENTIALS_JSON` | Primary Firebase credentials (JSON string) | - | No* |
| `FIREBASE_CRED` | Primary Firebase credentials file path (local) | - | No* |
| `FIREBASE_CREDENTIALS_JSON_B64_SECONDARY` | Secondary Firebase credentials (base64) | - | No** |
| `FIREBASE_CREDENTIALS_JSON_SECONDARY` | Secondary Firebase credentials (JSON) | - | No** |
| `FIREBASE_CRED_SECONDARY` | Secondary Firebase credentials file path | - | No** |
| `FIREBASE_PROJECT_ID_SECONDARY` | Secondary Firebase project ID | - | No** |
| `DRY_RUN` | If `True`, don't write to Firestore | `False` | No |

*Primary Firebase credentials: The function tries `FIREBASE_CREDENTIALS_JSON_B64` first, then `FIREBASE_CREDENTIALS_JSON`, then `FIREBASE_CRED` file path, then Application Default Credentials.

**Secondary Firebase (Optional): If ANY of these are set, the function will seed to both primary and secondary Firebase projects. If NONE are set, only primary is used.

### ⚠️ Important: Getting Firebase Service Account Keys

**DO NOT use gcloud CLI to create Firebase keys** - it will fail due to organizational policy:
```
ERROR: Key creation is not allowed on this service account
```

**ONLY working method:** Download from Firebase Console (Project Settings → Service Accounts → Generate New Private Key)

## 🔍 Testing

### Local Testing

```bash
cd daily_readings_seeder

# Set environment variables
export FIREBASE_CRED=/path/to/firebase-key.json
export DRY_RUN=True  # Test without writing

# Run locally
python3 main.py
```

### Manual Invocation

```bash
# Get function URL
FUNCTION_URL=$(gcloud functions describe daily-readings-seeder \
  --gen2 \
  --region=us-central1 \
  --format="value(serviceConfig.uri)")

# Invoke function (seeds days 1-30 of next month)
curl "$FUNCTION_URL"
```

## 📝 Implementation Notes

### USCCB Data (References Only)

- **DO NOT** store USCCB text content (licensing restrictions)
- **DO** store USCCB reading references and URLs
- Parse USCCB HTML to extract references only
- Link to USCCB page for users who want official text

### Public Domain Scripture Text

- Uses public domain sources (World English Bible, KJV)
- Stores in `body` field of `daily_scripture` documents
- Matches references to fetch corresponding verses

### Feast Data

- Looks up feast information from `feasts` collection
- Stores feast name and type in daily scripture document
- Links to feast documents if needed

## 🔐 Security Best Practices

1. **Never commit secrets** to the repository
2. **Use base64 encoding** for Firebase credentials in GitHub Secrets
3. **Use DRY_RUN mode** for testing
4. **Monitor function logs** for errors
5. **Validate data** before writing to Firestore

## 🛠️ Troubleshooting

### Function deployment fails

- Check that all required APIs are enabled
- Verify service account has correct permissions
- Check GitHub Actions logs for detailed error messages
- Ensure Firebase credentials are correctly encoded

### Scheduler job not running

- Verify job was created: `gcloud scheduler jobs list`
- Check job status: `gcloud scheduler jobs describe daily-readings-seeder-monthly-15th`
- Review Cloud Scheduler logs in GCP Console
- Job should run on the 15th of each month at 2 AM ET (7 AM UTC)

### Function execution errors

- Check Cloud Function logs for detailed error messages
- Verify Firebase credentials are correctly configured
- Ensure HTML parsing is working for USCCB data
- Check that public domain scripture API is accessible

## 📚 Related Documentation

- `CURSOR_PROMPT_FIREBASE_DAILY_READINGS_SEED.md` - Detailed data model specification
- `the_word_today_cron/README.md` - The Word Today video seeder documentation

## 🤝 Contributing

1. Make changes to the code
2. Test locally with `DRY_RUN=True`
3. Push to `main` branch
4. GitHub Actions will automatically deploy

---

**Note**: This seeder respects USCCB licensing by storing only references and URLs, not full text content. Public domain scripture text is used for display purposes.

