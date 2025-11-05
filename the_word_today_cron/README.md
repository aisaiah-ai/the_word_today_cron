# The Word Today - Automated Google Cloud Function Cron

This project automates the daily fetching and storage of scripture videos from YouTube to Firebase Firestore. The service runs automatically via Google Cloud Scheduler, triggered at 4 AM and 9 AM Eastern Time.

## 📋 Overview

This Cloud Function:
- Fetches daily scripture videos from YouTube (The Word Today, CFC Only By Grace Reflections, Brother Bo FULLTANK)
- Updates Firebase Firestore with video URLs for today and tomorrow
- Runs automatically via Cloud Scheduler at scheduled times
- Deploys automatically via GitHub Actions on every push to `main`
- **Completely self-contained** - no external service file dependencies

## 🏗️ Architecture

```
GitHub Repository
    ↓ (on push to main)
GitHub Actions Workflow
    ↓
Deploy Cloud Function (Gen2)
    ↓
Create/Update Cloud Scheduler Jobs
    ↓
Daily Execution (4 AM ET & 9 AM ET)
    ↓
The Word Today Service (self-contained in main.py)
    ↓
Firebase Firestore
```

## 🚀 Quick Start (Automated Setup)

### Option 1: Complete Automated Setup (Recommended)

Run the complete setup script that handles both GCP and GitHub:

```bash
cd the_word_today_cron
chmod +x setup_complete.sh
./setup_complete.sh
```

This will:
1. Set up all GCP resources (APIs, service accounts, IAM roles)
2. Configure GitHub secrets automatically
3. Generate the service account key file

### Option 2: Step-by-Step Setup

#### Step 1: GCP Setup

```bash
cd the_word_today_cron
chmod +x setup_gcp.sh
./setup_gcp.sh
```

This script will:
- Enable required APIs (Cloud Functions, Scheduler, Build, Logging)
- Create service account for GitHub Actions
- Grant necessary IAM roles
- Generate service account key file

#### Step 2: GitHub Setup

```bash
chmod +x setup_github.sh
./setup_github.sh
```

This script will:
- Check for GitHub CLI installation
- Prompt for repository and credentials
- Set all required GitHub Secrets automatically

## 📁 Project Structure

```
the_word_today_cron/
├── main.py                    # Self-contained Cloud Function entry point
├── requirements.txt           # Python dependencies
├── setup_gcp.sh              # GCP automation script
├── setup_github.sh           # GitHub automation script
├── setup_complete.sh         # Master setup script
├── .github/
│   └── workflows/
│       └── deploy.yml        # CI/CD pipeline
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

## 🔧 Manual Setup (Alternative)

If you prefer manual setup or the scripts don't work for your environment:

### Prerequisites

1. **Google Cloud Project** with billing enabled
2. **GitHub Repository** with Actions enabled
3. **Required GCP APIs enabled**:
   - Cloud Functions API
   - Cloud Scheduler API
   - Cloud Build API
   - Cloud Logging API

### 1. Enable Required APIs

```bash
gcloud services enable \
  cloudfunctions.googleapis.com \
  cloudscheduler.googleapis.com \
  cloudbuild.googleapis.com \
  logging.googleapis.com
```

### 2. Create Service Account for GitHub Actions

```bash
# Create service account
gcloud iam service-accounts create github-actions-deploy \
  --display-name="GitHub Actions Deployment Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:github-actions-deploy@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudfunctions.developer"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:github-actions-deploy@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudscheduler.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:github-actions-deploy@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:github-actions-deploy@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# Create and download key
gcloud iam service-accounts keys create key.json \
  --iam-account=github-actions-deploy@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### 3. Configure GitHub Secrets

In your GitHub repository, go to **Settings → Secrets and variables → Actions** and add:

| Secret Name | Description | Example |
|------------|-------------|---------|
| `GCP_PROJECT_ID` | Your GCP Project ID | `my-project-123456` |
| `GCP_SA_KEY` | Service account JSON key (entire file content) | `{"type": "service_account", ...}` |
| `YOUTUBE_API_KEY` | YouTube Data API key | `AIzaSy...` |
| `FIREBASE_CREDENTIALS_JSON` | Firebase service account JSON as single-line string | `{"type":"service_account",...}` |
| `DRY_RUN` | (Optional) Set to `True` for testing | `False` |

**Using GitHub CLI:**

```bash
gh secret set GCP_PROJECT_ID --repo owner/repo --body "your-project-id"
gh secret set GCP_SA_KEY --repo owner/repo < key.json
gh secret set YOUTUBE_API_KEY --repo owner/repo --body "your-youtube-key"
gh secret set FIREBASE_CREDENTIALS_JSON --repo owner/repo --body "$(cat firebase-key.json | jq -c .)"
gh secret set DRY_RUN --repo owner/repo --body "False"
```

### 4. Deploy

Simply push to the `main` branch:

```bash
git add .
git commit -m "Initial deployment setup"
git push origin main
```

GitHub Actions will automatically:
1. Deploy the Cloud Function
2. Create/update the Cloud Scheduler jobs
3. Verify the deployment

## ⏰ Schedule

The function runs automatically:
- **4:00 AM Eastern Time** (09:00 UTC)
- **9:00 AM Eastern Time** (14:00 UTC)

Both schedules update Firestore with videos for today and tomorrow.

## 🔍 Monitoring

### View Function Logs

```bash
gcloud functions logs read the-word-today-cron \
  --region=us-central1 \
  --limit=50
```

Or in the [GCP Console](https://console.cloud.google.com/functions/list).

### View Scheduler Job Status

```bash
gcloud scheduler jobs list --location=us-central1
```

### Test Function Manually

```bash
# Get function URL
FUNCTION_URL=$(gcloud functions describe the-word-today-cron \
  --gen2 \
  --region=us-central1 \
  --format="value(serviceConfig.uri)")

# Invoke function
curl $FUNCTION_URL
```

## 🔧 Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `YOUTUBE_API_KEY` | YouTube Data API key | - | ✅ Yes |
| `FIREBASE_CREDENTIALS_JSON` | Firebase service account JSON (string) | - | ✅ Yes* |
| `FIREBASE_CRED` | Firebase credentials file path (local dev) | - | No* |
| `DRY_RUN` | If `True`, don't write to Firestore | `False` | No |
| `CHANNEL_ID` | The Word Today YouTube channel ID | `UC9gpFF4p56T4wQtinfAT3Eg` | No |
| `CFC_CHANNEL_ID` | CFC channel ID | `UCVb6g46-SKkTLTHTF-wO8Kw` | No |
| `BO_CHANNEL_ID` | Brother Bo Sanchez channel ID | `UCFoHFFBWDwxbpa1bYH736RA` | No |

*Firebase credentials: The function tries `FIREBASE_CREDENTIALS_JSON` first, then `FIREBASE_CRED` file path, then Application Default Credentials (for Cloud Functions).

## 🛠️ Troubleshooting

### Function deployment fails

- Check that all required APIs are enabled
- Verify service account has correct permissions
- Check GitHub Actions logs for detailed error messages
- Ensure all GitHub Secrets are set correctly

### Scheduler jobs not running

- Verify jobs were created: `gcloud scheduler jobs list`
- Check job status: `gcloud scheduler jobs describe JOB_NAME`
- Review Cloud Scheduler logs in GCP Console
- Ensure function URL is accessible (not private)

### Function execution errors

- Check Cloud Function logs for detailed error messages
- Verify Firebase credentials are correctly configured
- Ensure YouTube API key is valid and has quota remaining
- Check that environment variables are set correctly

### Authentication errors

- Verify service account key is valid
- Check IAM roles are correctly assigned
- Ensure GitHub Secrets contain valid JSON (no formatting issues)

## 🔐 Security Best Practices

1. **Never commit secrets** to the repository
2. **Use Secret Manager** for sensitive credentials in production
3. **Restrict IAM permissions** to minimum required
4. **Enable audit logs** for production deployments
5. **Use least privilege** for service accounts
6. **Rotate keys regularly**
7. **Monitor for unauthorized access**

## 📝 Manual Deployment (Alternative)

If you prefer to deploy manually:

```bash
# Deploy function
gcloud functions deploy the-word-today-cron \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=the_word_today_cron \
  --entry-point=the_word_today_cron \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars YOUTUBE_API_KEY=your-key,FIREBASE_CREDENTIALS_JSON='your-json'

# Get function URL
FUNCTION_URL=$(gcloud functions describe the-word-today-cron \
  --gen2 \
  --region=us-central1 \
  --format="value(serviceConfig.uri)")

# Create scheduler jobs
gcloud scheduler jobs create http the-word-today-cron-4am-et \
  --location=us-central1 \
  --schedule="0 9 * * *" \
  --uri="$FUNCTION_URL" \
  --http-method=GET \
  --time-zone="America/New_York"
```

## 📚 Additional Resources

- [Cloud Functions Gen2 Documentation](https://cloud.google.com/functions/docs/2nd-gen/overview)
- [Cloud Scheduler Documentation](https://cloud.google.com/scheduler/docs)
- [GitHub Actions for GCP](https://github.com/google-github-actions)
- [Firebase Admin SDK](https://firebase.google.com/docs/admin/setup)
- [YouTube Data API](https://developers.google.com/youtube/v3)

## 🤝 Contributing

1. Make changes to the code
2. Test locally if possible
3. Push to `main` branch
4. GitHub Actions will automatically deploy

## 📄 License

[Your License Here]

---

**Note:** This setup provides zero-touch deployment. Once configured, every push to `main` automatically deploys to production. The solution is completely self-contained - no external service files required!
