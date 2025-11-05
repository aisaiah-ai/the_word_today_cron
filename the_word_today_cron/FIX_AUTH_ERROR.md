# Fixing GCP Authentication Error in GitHub Actions

## Error Message
```
Error: google-github-actions/setup-gcloud failed with: failed to execute command `gcloud --quiet config set project ***`: ERROR: (gcloud.config.set) There was a problem refreshing auth tokens for account github-actions-deploy@***.iam.gserviceaccount.com: ('invalid_grant: Invalid JWT Signature.'
```

## What This Means
The service account key stored in GitHub Secrets (`GCP_SA_KEY`) is invalid, corrupted, or expired. This can happen if:
- The key was manually edited
- The key was rotated/deleted in GCP
- The key was copied incorrectly
- The key expired

## Quick Fix

### Option 1: Automated Fix Script (Recommended)

Run the fix script:

```bash
cd the_word_today_cron
./fix_gcp_auth.sh
```

This script will:
1. ✅ Check/create the service account
2. ✅ Generate a new service account key
3. ✅ Test the key locally
4. ✅ Update the GitHub secret automatically
5. ✅ Optionally delete old keys

### Option 2: Manual Fix

#### Step 1: Get Your GCP Project ID
```bash
gcloud config get-value project
```

#### Step 2: Create a New Service Account Key
```bash
# Replace PROJECT_ID with your actual project ID
PROJECT_ID="your-project-id"
SA_EMAIL="github-actions-deploy@${PROJECT_ID}.iam.gserviceaccount.com"

# Create new key
gcloud iam service-accounts keys create gcp-sa-key-new.json \
    --iam-account="$SA_EMAIL" \
    --project="$PROJECT_ID"
```

#### Step 3: Update GitHub Secret
```bash
# Replace owner/repo with your GitHub repository
REPO="owner/repo"

# Update the secret
gh secret set GCP_SA_KEY --repo "$REPO" < gcp-sa-key-new.json
```

#### Step 4: Verify the Secret
```bash
gh secret list --repo "$REPO"
```

#### Step 5: Test the Workflow
```bash
# Re-run the GitHub Actions workflow
gh workflow run deploy.yml --repo "$REPO"
```

## Alternative: Using GitHub Web UI

If you don't have GitHub CLI:

1. **Create New Key** (same as Step 2 above)
2. **Go to GitHub Repository** → Settings → Secrets and variables → Actions
3. **Edit `GCP_SA_KEY` secret**
4. **Copy entire contents** of `gcp-sa-key-new.json` file
5. **Paste into the secret value** (keep it as a single-line JSON)
6. **Save the secret**
7. **Re-run the workflow**

## Verify the Fix

After updating the secret, check your GitHub Actions workflow:

1. Go to your repository → Actions tab
2. Re-run the failed workflow or push a new commit
3. Check the logs - authentication should now succeed

## Prevention

To avoid this in the future:

1. **Never manually edit** service account keys
2. **Use the setup scripts** (`setup_gcp.sh`, `setup_github.sh`) to create keys
3. **Rotate keys regularly** (every 90 days is recommended)
4. **Delete old keys** after creating new ones

## Troubleshooting

### If the script fails:

1. **Check gcloud authentication**:
   ```bash
   gcloud auth list
   gcloud config get-value project
   ```

2. **Verify service account exists**:
   ```bash
   gcloud iam service-accounts describe github-actions-deploy@PROJECT_ID.iam.gserviceaccount.com
   ```

3. **Check GitHub CLI authentication**:
   ```bash
   gh auth status
   ```

4. **Verify repository access**:
   ```bash
   gh repo view owner/repo
   ```

### If GitHub secret update fails:

- Make sure you have admin access to the repository
- Verify the GitHub CLI is authenticated: `gh auth login`
- Check the secret name is exactly `GCP_SA_KEY` (case-sensitive)

### If the key file is invalid:

- Ensure the file is valid JSON: `jq . gcp-sa-key-new.json`
- Make sure the entire file content is copied (including all braces)
- Check for any extra spaces or newlines

## Need Help?

If you're still having issues:

1. Check the service account has the required roles:
   ```bash
   gcloud projects get-iam-policy PROJECT_ID \
       --flatten="bindings[].members" \
       --filter="bindings.members:serviceAccount:github-actions-deploy@PROJECT_ID.iam.gserviceaccount.com"
   ```

2. Verify the service account key format:
   ```bash
   cat gcp-sa-key-new.json | jq -r '.type, .project_id, .private_key_id'
   ```

3. Test the key locally:
   ```bash
   gcloud auth activate-service-account --key-file=gcp-sa-key-new.json
   gcloud config get-value project
   ```

