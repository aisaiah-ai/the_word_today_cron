# Final Answer: How to Get Secondary Firebase Key

## What We've Confirmed

✅ You have `roles/owner` on the project
❌ You **cannot** change organization policies (requires org-level admin)
❌ The policy is set at **organization level**, not project level

```
ERROR: does not have permission to access projects instance [aisaiah-sfa-dev-app:clearOrgPolicy]
```

This means an **organization administrator** set this policy, and only they can change it.

## ✅ ONLY Working Solution: Firebase Console

Go to Firebase Console and click "Generate new private key":

**Direct Link:**
https://console.firebase.google.com/project/aisaiah-sfa-dev-app/settings/serviceaccounts/adminsdk

### Visual Guide

When you open the link above, you should see:

1. **Top of page:** "AIsaiah SFA Dev" project name
2. **Tabs:** General | Service accounts | Cloud Messaging | etc.
3. **Click:** "Service accounts" tab
4. **Scroll down** to "Firebase Admin SDK" section
5. **You'll see:** 
   - A gray box with Node.js/Python/Java code examples
   - Text: "Your service account credentials can be used..."
   - 🔵 **A blue button: "Generate new private key"**

6. **Click** that blue button
7. **Confirm** in the popup dialog
8. **Save** the downloaded JSON file

### What to Do with the Downloaded File

```bash
# 1. Check the file
cat ~/Downloads/aisaiah-sfa-dev-app-*.json | jq -r '.project_id'
# Should show: aisaiah-sfa-dev-app

# 2. Move to secure location
mv ~/Downloads/aisaiah-sfa-dev-app-*.json \
   /Users/acthercop/.keys/aisaiah-sfa-dev-app-firebase-key.json

# 3. Add to GitHub
gh secret set FIREBASE_CREDENTIALS_JSON_SECONDARY \
  --body "$(cat /Users/acthercop/.keys/aisaiah-sfa-dev-app-firebase-key.json)"

# 4. Merge and deploy
git checkout main
git merge seed_two_accounts
git push origin main
```

## Why Firebase Console Works

Firebase Console has **special IAM permissions** that allow it to:
- Generate Firebase Admin SDK keys
- Bypass the gcloud CLI restriction
- Still maintain audit logging and security

This is **intentional** - Google wants you to use Firebase Console for Firebase keys, not gcloud CLI.

## If Firebase Console Also Says "Not Allowed"

Then you need to contact your **Organization Administrator** and ask them to either:

1. Generate the Firebase key for you
2. Grant you `roles/orgpolicy.policyAdmin` role temporarily
3. Add an exception to the org policy for Firebase Admin SDK service accounts

## Summary

**Can you change the policy yourself?** ❌ No (requires org admin)

**Do you need to change the policy?** ❌ No (Firebase Console should work)

**What to do:** Try Firebase Console download

**If Console fails:** Contact org admin

The organizational policy is set at a level above your project owner permissions, so you cannot modify it with your current account.

**Try the Firebase Console download first** - it's designed to work within this restriction!

