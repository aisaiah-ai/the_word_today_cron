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
- Links liturgical feast information
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

## 📊 Data Model

### Daily Scripture Document (`daily_scripture/{yyyy-MM-dd}`)

```json
{
  "id": "2025-11-05",
  "title": "Daily Scripture",
  "reference": "Mk 3:22-30",
  "body": "[Public domain scripture text for Gospel]",
  "responsorialPsalmText": "[Public domain scripture text for Responsorial Psalm]",
  "updatedAt": "2025-11-05T10:00:00Z",
  "usccbReading": {
    "id": "unique-id",
    "date": "2025-11-05T00:00:00Z",
    "title": "Readings for Wednesday, November 5, 2025",
    "url": "https://bible.usccb.org/bible/readings/11/05/2025.cfm",
    "reading1": {
      "id": "unique-id",
      "title": "Reading 1",
      "reference": "Heb 9:15, 24-28"
    },
    "responsorialPsalm": {
      "id": "unique-id",
      "title": "Responsorial Psalm",
      "reference": "Ps 98:1, 2-3ab",
      "text": "[Public domain scripture text for Responsorial Psalm]"
    },
    "gospel": {
      "id": "unique-id",
      "title": "Gospel",
      "reference": "Mk 3:22-30"
    }
  },
  "feast": "Optional Memorial",
  "feastType": "Optional Memorial"
}
```

## 🔧 Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `FIREBASE_CREDENTIALS_JSON_B64` | Firebase credentials (base64 encoded) | - | ✅ Yes* |
| `FIREBASE_CREDENTIALS_JSON` | Firebase credentials (JSON string) | - | No* |
| `FIREBASE_CRED` | Firebase credentials file path (local dev) | - | No* |
| `DRY_RUN` | If `True`, don't write to Firestore | `False` | No |

*Firebase credentials: The function tries `FIREBASE_CREDENTIALS_JSON_B64` first, then `FIREBASE_CREDENTIALS_JSON`, then `FIREBASE_CRED` file path, then Application Default Credentials.

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

