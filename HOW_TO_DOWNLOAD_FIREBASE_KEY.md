# How to Download Firebase Service Account Key

## Step-by-Step Instructions

### Step 1: Open Firebase Console

Click this link:
https://console.firebase.google.com/project/aisaiah-sfa-dev-app/settings/serviceaccounts/adminsdk

Or manually:
1. Go to https://console.firebase.google.com/
2. Click on **AIsaiah SFA Dev** project
3. Click gear icon (⚙️) at top left → **Project settings**
4. Click **Service accounts** tab

### Step 2: Generate New Private Key

You should see a page with:
- **Admin SDK configuration snippet** (code example)
- A section that says **"Firebase Admin SDK"**
- A button that says **"Generate new private key"**

**Click the "Generate new private key" button**

### Step 3: Confirm Download

A dialog will appear warning you:

```
Generate new private key?

This key can be used to authenticate your app to Firebase
services. Keep it confidential and never store it in a public
repository.
```

**Click "Generate key"** button

### Step 4: Save the Downloaded File

Your browser will download a JSON file with a name like:
```
aisaiah-sfa-dev-app-firebase-adminsdk-fbsvc-a1b2c3d4e5.json
```

**Save it to:**
```
/Users/acthercop/.keys/aisaiah-sfa-dev-app-firebase-key.json
```

Or save anywhere and rename it later.

### Step 5: Verify the Downloaded File

```bash
# Check if file exists and is valid JSON
cat /Users/acthercop/.keys/aisaiah-sfa-dev-app-firebase-key.json | jq -r '.project_id'
```

Should output: `aisaiah-sfa-dev-app`

### Step 6: Add to GitHub Secrets

```bash
gh secret set FIREBASE_CREDENTIALS_JSON_SECONDARY \
  --body "$(cat /Users/acthercop/.keys/aisaiah-sfa-dev-app-firebase-key.json)"
```

You should see:
```
✓ Set secret FIREBASE_CREDENTIALS_JSON_SECONDARY for aisaiah-ai/the_word_today_cron
```

### Step 7: Deploy

```bash
git checkout main
git merge seed_two_accounts
git push origin main
```

GitHub Actions will automatically:
- Encode the secondary key to base64
- Pass it to the Cloud Function
- Deploy with dual Firebase support

### Step 8: Verify

After deployment completes, test the function:

```bash
curl "https://daily-readings-seeder-lwvp6j7v6q-uc.a.run.app?start_date=2025-12-26&end_date=2025-12-26"
```

Look for:
```json
{
  "firebase_projects": ["primary", "secondary"]
}
```

Check both Firebase databases:
- Primary: https://console.firebase.google.com/project/aisaiahconferencefb/firestore
- Secondary: https://console.firebase.google.com/project/aisaiah-sfa-dev-app/firestore

Both should have document `2025-12-26` with responsorial psalm data.

## Troubleshooting

### "I don't see the Generate new private key button"

Make sure you're on the correct tab:
- Click **"Service accounts"** tab (not "General" or "Cloud Messaging")
- Scroll down to the **"Firebase Admin SDK"** section
- The button should be below the code snippet

### "The downloaded file has a different name"

That's fine - just rename it:
```bash
mv ~/Downloads/aisaiah-sfa-dev-app-firebase-adminsdk-*.json \
   /Users/acthercop/.keys/aisaiah-sfa-dev-app-firebase-key.json
```

### "Can I use an existing Firebase key?"

If you already have a Firebase key for `aisaiah-sfa-dev-app` downloaded previously, you can use that instead of generating a new one.

## Security Note

Keep this key secure:
- ✅ Store in `/Users/acthercop/.keys/` (not in git repository)
- ✅ Add to GitHub Secrets (encrypted)
- ❌ Never commit to git
- ❌ Never share publicly

The workflow automatically encodes it to base64 before passing to the Cloud Function.

## Summary

**Yes, you need to generate a new key** (or use an existing one if you have it).

**This is the ONLY way** to get a Firebase service account key for the secondary project given the organizational restrictions.

Once you download it and add to GitHub secrets, the dual Firebase seeding will work automatically!

