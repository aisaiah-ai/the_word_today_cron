# ⚠️ CRITICAL: Only Firebase Console Works for Secondary Firebase

## Organizational Policies Block All Automated Methods

Your organization has TWO security policies that prevent automated setup:

### 🚫 Policy 1: Key Creation Disabled
```
constraints/iam.disableServiceAccountKeyCreation
ERROR: Key creation is not allowed on this service account
```
**Impact:** Cannot use `gcloud iam service-accounts keys create`

### 🚫 Policy 2: Cross-Project Access Blocked
```
constraints/iam.allowedPolicyMemberDomains
ERROR: User not in permitted organization
```
**Impact:** Cannot grant service accounts from one project access to another

## ✅ ONLY Solution: Firebase Console

### Step-by-Step Instructions

1. **Open Firebase Console**
   - Go to: https://console.firebase.google.com/
   - Sign in if needed

2. **Select Secondary Project**
   - Click on: **AIsaiah SFA Dev** (aisaiah-sfa-dev-app)

3. **Navigate to Service Accounts**
   - Click the gear icon (⚙️) for **Project Settings**
   - Click the **Service Accounts** tab

4. **Generate Key**
   - Click the **"Generate New Private Key"** button
   - Confirm the download

5. **Save the Downloaded File**
   - Save as: `/Users/acthercop/.keys/aisaiah-sfa-dev-app-firebase-key.json`

6. **Add to GitHub Secrets**
   ```bash
   gh secret set FIREBASE_CREDENTIALS_JSON_SECONDARY \
     --body "$(cat /Users/acthercop/.keys/aisaiah-sfa-dev-app-firebase-key.json)"
   ```

7. **Merge and Deploy**
   ```bash
   git checkout main
   git merge seed_two_accounts
   git push origin main
   ```

## Why Firebase Console Works

Firebase Console has special permissions to generate keys for Firebase Admin SDK service accounts, bypassing the organizational restrictions that block gcloud CLI.

## Verification

After deployment, test:
```bash
curl "https://daily-readings-seeder-lwvp6j7v6q-uc.a.run.app?start_date=2025-12-25&end_date=2025-12-25"
```

You should see:
```json
{
  "firebase_projects": ["primary", "secondary"]
}
```

## To Disable Secondary Seeding

Simply remove the GitHub secret:
```bash
gh secret delete FIREBASE_CREDENTIALS_JSON_SECONDARY
```

Next deployment will automatically revert to primary-only seeding.

---

**All JSON keys are configured in the code. Just need the Firebase key from the console!**

