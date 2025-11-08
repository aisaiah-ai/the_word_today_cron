# Terraform Configuration for GCP Setup

This Terraform configuration sets up all required GCP resources for deploying The Word Today Cloud Function.

## What This Sets Up

1. **Enables Required APIs:**
   - Cloud Functions API
   - Cloud Run API (required for Gen2 functions)
   - Cloud Build API
   - Cloud Scheduler API
   - Cloud Logging API
   - Artifact Registry API
   - Secret Manager API
   - IAM API
   - Service Usage API

2. **Creates Service Account:**
   - `github-actions-deploy` service account for GitHub Actions

3. **Grants IAM Roles:**
   - `roles/cloudfunctions.developer` - Deploy and manage Cloud Functions
   - `roles/cloudscheduler.admin` - Create and manage Cloud Scheduler jobs
   - `roles/iam.serviceAccountUser` - Use service accounts
   - `roles/storage.admin` - Access Cloud Storage
   - `roles/run.admin` - Deploy to Cloud Run (required for Gen2)
   - `roles/artifactregistry.writer` - Push container images
   - `roles/serviceusage.serviceUsageConsumer` - Use APIs

4. **Creates Artifact Registry Repository:**
   - Docker repository for storing Cloud Function container images

## Prerequisites

1. **Install Terraform:**
   ```bash
   # macOS
   brew install terraform
   
   # Or download from https://www.terraform.io/downloads
   ```

2. **Authenticate with GCP:**
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

3. **Set your project:**
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

## Usage

1. **Copy the example variables file:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. **Edit `terraform.tfvars` with your project ID:**
   ```hcl
   project_id = "your-gcp-project-id"
   region     = "us-central1"
   ```

3. **Initialize Terraform:**
   ```bash
   cd terraform
   terraform init
   ```

4. **Review the plan:**
   ```bash
   terraform plan
   ```

5. **Apply the configuration:**
   ```bash
   terraform apply
   ```

6. **Create service account key:**
   ```bash
   # Get the service account email from outputs
   terraform output service_account_email
   
   # Create the key
   gcloud iam service-accounts keys create ../gcp-sa-key.json \
     --iam-account=$(terraform output -raw service_account_email)
   ```

7. **Add secrets to GitHub:**
   - Go to your GitHub repository → Settings → Secrets and variables → Actions
   - Add the following secrets:
     - `GCP_SA_KEY`: Contents of `gcp-sa-key.json`
     - `GCP_PROJECT_ID`: Your project ID
     - `YOUTUBE_API_KEY`: Your YouTube API key
     - `FIREBASE_CREDENTIALS_JSON`: Your Firebase credentials JSON
     - `DRY_RUN`: `False` (or `True` for testing)

## Outputs

After applying, Terraform will output:
- Service account email
- Service account ID
- Artifact Registry repository name
- List of enabled APIs

## Destroying Resources

To remove all resources created by Terraform:
```bash
terraform destroy
```

**Note:** This will NOT delete:
- The Cloud Function itself (created by GitHub Actions)
- Cloud Scheduler jobs (created by GitHub Actions)
- Any data in Firestore

## Troubleshooting

### Error: "API not enabled"
If you get errors about APIs not being enabled, make sure you have the `roles/serviceusage.serviceUsageAdmin` role or are the project owner.

### Error: "Permission denied"
Make sure you're authenticated and have the necessary permissions:
```bash
gcloud auth login
gcloud auth application-default login
```

### Error: "Service account already exists"
If the service account already exists, Terraform will use it. If you want to recreate it, delete it first:
```bash
gcloud iam service-accounts delete github-actions-deploy@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

## Manual Setup Alternative

If you prefer not to use Terraform, you can use the shell scripts:
```bash
cd the_word_today_cron
./setup_gcp.sh
```

