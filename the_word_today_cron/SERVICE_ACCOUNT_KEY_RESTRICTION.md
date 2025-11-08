# Service Account Key Creation Restricted - Solutions

If you see the error: **"Key creation is not allowed on this service account"**, your organization has restricted service account key creation. Here are solutions:

## Solution 1: Use Workload Identity Federation (Recommended)

Workload Identity Federation allows GitHub Actions to authenticate without service account keys. This is more secure and works even when key creation is restricted.

### Setup Steps:

1. **Enable Workload Identity Federation API**
```bash
gcloud services enable iamcredentials.googleapis.com --project=YOUR_PROJECT_ID
```

2. **Create Workload Identity Pool**
```bash
gcloud iam workload-identity-pools create "github-pool" \
  --project="YOUR_PROJECT_ID" \
  --location="global" \
  --display-name="GitHub Actions Pool"
```

3. **Create Workload Identity Provider**
```bash
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project="YOUR_PROJECT_ID" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

4. **Grant Service Account Access**
```bash
# Get the provider resource name
PROVIDER_NAME="projects/YOUR_PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider"

# Grant access to your service account
gcloud iam service-accounts add-iam-policy-binding \
  SERVICE_ACCOUNT_EMAIL@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/YOUR_PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/YOUR_GITHUB_ORG/YOUR_REPO"
```

5. **Update GitHub Actions Workflow**

Update `.github/workflows/deploy.yml` to use Workload Identity:

```yaml
- name: 🔐 Authenticate to Google Cloud
  uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: 'projects/YOUR_PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider'
    service_account: 'SERVICE_ACCOUNT_EMAIL@YOUR_PROJECT_ID.iam.gserviceaccount.com'
```

## Solution 2: Use Application Default Credentials (If Same Project)

If your Cloud Function runs in the same GCP project, you can use Application Default Credentials instead of a service account key.

### For Secondary Firebase:

Update the code to use Application Default Credentials when no key is provided:

The code already supports this! If `FIREBASE_CREDENTIALS_JSON_SECONDARY` is not set, it will try to use Application Default Credentials.

### Setup:

1. **Grant the Cloud Function's service account access to the secondary Firebase project**
```bash
# Get the Cloud Function's service account (usually compute@developer.gserviceaccount.com)
FUNCTION_SA="YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com"

# Grant Firebase Admin role in the secondary project
gcloud projects add-iam-policy-binding SECONDARY_PROJECT_ID \
  --member="serviceAccount:${FUNCTION_SA}" \
  --role="roles/firebase.admin"
```

2. **Remove the need for secondary credentials secret**
   - The code will automatically use Application Default Credentials
   - No GitHub secret needed!

## Solution 3: Request Policy Exception

Contact your organization administrator to:
1. Allow service account key creation for your specific service account
2. Or create an exception policy for your project

## Solution 4: Use Existing Service Account Key

If a key was created before the restriction:
1. Check if you have an existing key file
2. Use that key instead of creating a new one
3. Rotate it periodically if possible

## Solution 5: Use Service Account Impersonation

If you have permission to impersonate service accounts:

```bash
# Impersonate the service account
gcloud auth activate-service-account --impersonate-service-account=SERVICE_ACCOUNT_EMAIL@PROJECT.iam.gserviceaccount.com

# Then use Application Default Credentials
```

## Recommended Approach

**For GitHub Actions**: Use **Workload Identity Federation** (Solution 1)
- ✅ More secure (no keys to manage)
- ✅ Works with organization restrictions
- ✅ Industry best practice
- ✅ Automatic token rotation

**For Secondary Firebase**: Use **Application Default Credentials** (Solution 2)
- ✅ No keys needed
- ✅ Works if Cloud Function has access
- ✅ Simpler setup

## Quick Fix for Now

If you need a quick solution and can't set up Workload Identity Federation:

1. **Use the same Firebase project** (primary and secondary point to same project)
   - No secondary credentials needed
   - Data still gets written (just to one project)

2. **Or skip secondary Firebase** for now
   - The code works fine with just primary Firebase
   - Add secondary later when you can set up Workload Identity Federation

## Need Help?

- Workload Identity Docs: https://cloud.google.com/iam/docs/workload-identity-federation
- Service Account Impersonation: https://cloud.google.com/iam/docs/impersonating-service-accounts

