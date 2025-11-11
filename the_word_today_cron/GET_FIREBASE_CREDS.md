# How to Get Firebase Service Account Credentials

## Step-by-Step Guide

### Method 1: Firebase Console (Easiest)

1. **Go to Firebase Console**
   - Visit: https://console.firebase.google.com
   - Sign in with your Google account

2. **Select Your Project**
   - Click on your Firebase project (or create a new one)
   - If you need a secondary project, create it first

3. **Open Project Settings**
   - Click the ⚙️ gear icon next to "Project Overview"
   - Select **Project settings**

4. **Go to Service Accounts Tab**
   - Click on the **Service accounts** tab
   - You'll see service accounts for your project

5. **Generate New Private Key**
   - Click **Generate new private key** button
   - A warning dialog will appear - click **Generate key**
   - A JSON file will download automatically (e.g., `your-project-firebase-adminsdk-xxxxx.json`)

6. **Save the File**
   - Keep this file secure - it contains sensitive credentials
   - **DO NOT** commit it to git

### Method 2: Google Cloud Console

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com
   - Select your Firebase project

2. **Navigate to Service Accounts**
   - Go to **IAM & Admin** → **Service Accounts**
   - Or use this direct link: https://console.cloud.google.com/iam-admin/serviceaccounts

3. **Find/Create Service Account**
   - Look for a service account with email like: `firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com`
   - If it doesn't exist, create one:
     - Click **+ CREATE SERVICE ACCOUNT**
     - Name: `firebase-adminsdk`
     - Grant role: **Firebase Admin SDK Administrator Service Agent**
     - Click **Done**

4. **Create Key**
   - Click on the service account
   - Go to **Keys** tab
   - Click **ADD KEY** → **Create new key**
   - Select **JSON** format
   - Click **Create**
   - JSON file downloads automatically

## What You'll Get

The downloaded JSON file contains:
- `type`: "service_account"
- `project_id`: Your Firebase project ID
- `private_key`: Private key for authentication
- `client_email`: Service account email
- And other authentication details

## Adding to GitHub Secrets

### Option 1: Copy-Paste Method

1. Open the downloaded JSON file in a text editor
2. Copy the **entire** content (all lines, including braces)
3. Go to GitHub: **Settings → Secrets and variables → Actions**
4. Click **New repository secret**
5. Name: `FIREBASE_CREDENTIALS_JSON_SECONDARY`
6. Value: Paste the entire JSON content
7. Click **Add secret**

### Option 2: Using GitHub CLI

```bash
# If you have the JSON file locally
gh secret set FIREBASE_CREDENTIALS_JSON_SECONDARY \
  --repo owner/repo \
  < path/to/firebase-adminsdk-xxxxx.json
```

### Option 3: Base64 Encoded (Alternative)

If you prefer base64 encoding:

```bash
# Encode the JSON file
cat firebase-adminsdk-xxxxx.json | base64 | tr -d '\n' > creds-b64.txt

# Add as secret
gh secret set FIREBASE_CREDENTIALS_JSON_B64_SECONDARY \
  --repo owner/repo \
  < creds-b64.txt
```

## Security Best Practices

⚠️ **IMPORTANT:**
- ✅ Store credentials in GitHub Secrets (encrypted)
- ✅ Use different service accounts for different projects
- ✅ Rotate keys periodically
- ❌ Never commit credentials to git
- ❌ Never share credentials publicly
- ❌ Don't hardcode credentials in code

## Verifying It Works

After adding the secret, the next deployment will:
1. Detect secondary credentials
2. Initialize both Firebase projects
3. Write to both projects
4. Log: `✅ Secondary Firebase credentials detected - will write to both projects`

Check the deployment logs to confirm both projects are being written to.

## Troubleshooting

### "Invalid credentials" error
- Make sure you copied the **entire** JSON file
- Check that the JSON is valid (no missing braces or quotes)
- Verify the service account has proper permissions

### "Permission denied" error
- Ensure the service account has **Firebase Admin SDK Administrator Service Agent** role
- Check that Firestore is enabled in the Firebase project

### Secondary Firebase not initializing
- Verify the secret name is exactly: `FIREBASE_CREDENTIALS_JSON_SECONDARY`
- Check deployment logs for initialization errors
- The service will continue with primary only if secondary fails

## Need Help?

- Firebase Docs: https://firebase.google.com/docs/admin/setup
- Service Account Guide: https://cloud.google.com/iam/docs/service-accounts

