# Body Field Update - Short One-Liner Version

## What Changed

The `body` field in the `daily_scripture` documents has been updated to contain **only a short one-liner** (the gospel reference) instead of the full gospel text.

## Before
```json
{
  "body": "In those days, Judas Maccabeus and his brothers said: \"See! Our enemies are crushed. Let us go up to purify the sanctuary and rededicate it.\" So the whole army assembled, and went up to Mount Zion...[full gospel text continues]"
}
```

## After
```json
{
  "body": "Gospel: Lk 19:45-48"
}
```

## Code Change

**File:** `daily_readings_seeder/main.py`

**Line 586-590:** Changed from storing full gospel text to just the reference:

```python
# OLD CODE:
new_doc_data['body'] = gospel_text  # Full text

# NEW CODE:
new_doc_data['body'] = f"Gospel: {gospel_ref}"  # Just reference
```

## Deployment Status

✅ **PRIMARY Function** (aisaiahconferencefb): 
- **DEPLOYED** ✅
- Revision: `daily-readings-seeder-00043-rur`
- URL: https://daily-readings-seeder-lwvp6j7v6q-uc.a.run.app
- Status: Active

⏳ **SECONDARY Function** (aisaiah-sfa-dev-app):
- **NOT DEPLOYED** (insufficient permissions)
- Needs to be deployed by someone with admin access to that project

## How to Apply Changes to Existing Documents

To update existing November documents with the new short body format:

### Option 1: Delete and Reseed (Recommended)

1. **Delete November documents via Firebase Console:**
   - Go to: https://console.firebase.google.com/project/aisaiahconferencefb/firestore
   - Navigate to `daily_scripture` collection
   - Select all documents from `2025-11-01` to `2025-11-30`
   - Click Delete

2. **Trigger the seeder:**
```bash
curl -X POST "https://daily-readings-seeder-lwvp6j7v6q-uc.a.run.app?start_date=2025-11-01&end_date=2025-11-30" \
  -H "Authorization: bearer $(gcloud auth print-identity-token --project=aisaiahconferencefb)" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Option 2: Update via Script

Create a script to update just the `body` field of existing documents:

```python
#!/usr/bin/env python3
import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('path/to/firebase-key.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

for day in range(1, 31):
    doc_id = f"2025-11-{day:02d}"
    doc_ref = db.collection('daily_scripture').document(doc_id)
    doc = doc_ref.get()
    
    if doc.exists:
        data = doc.to_dict()
        gospel_ref = data.get('gospel_verse', '')
        if gospel_ref:
            doc_ref.update({'body': f"Gospel: {gospel_ref}"})
            print(f"✅ Updated {doc_id}")
```

## Impact

- **Storage:** Significantly reduced document size (gospel text can be 500-2000 characters, now it's just 15-30 characters)
- **Bandwidth:** Faster document retrieval 
- **Display:** Apps will now only display the gospel reference in the body field, not the full text
- **Full Text:** Still available in the `gospel` field if needed

## Notes

- The full gospel text is STILL stored in the `gospel` field
- The `body` field was redundant (it duplicated the `gospel` field)
- Now `body` serves as a compact summary/reference
- All other fields remain unchanged (first_reading, second_reading, responsorial_psalm, etc.)

## For Secondary Project

Someone with admin access to `aisaiah-sfa-dev-app` needs to:

1. Deploy the updated function:
```bash
cd daily_readings_seeder
gcloud functions deploy daily-readings-seeder-secondary \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --project=aisaiah-sfa-dev-app \
  --source=. \
  --entry-point=seed_daily_readings_cron \
  --trigger-http \
  --set-env-vars="FIREBASE_PROJECT_ID_SECONDARY=aisaiah-sfa-dev-app"
```

2. Then trigger it for November:
```bash
# (once you have proper access)
curl -X POST "<secondary-function-url>?start_date=2025-11-01&end_date=2025-11-30" ...
```


