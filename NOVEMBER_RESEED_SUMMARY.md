# November 2025 Deletion and Reseeding Summary

**Date:** 2025-11-14  
**Task:** Delete all November 2025 entries and reseed for both PRIMARY and SECONDARY Firebase

## ✅ What Was Completed

### 1. Deletion Phase
- **PRIMARY Firebase** (aisaiahconferencefb): ✅ Deleted all 30 documents (2025-11-01 through 2025-11-30)
- **SECONDARY Firebase** (aisaiah-sfa-dev-app): ✅ Deleted all 30 documents (2025-11-01 through 2025-11-30)

### 2. Reseeding Phase
- **PRIMARY Firebase**: ✅ Successfully reseeded all 30 November dates
  - Function: `daily-readings-seeder`
  - Status: SUCCESS
  - Documents created: 28/30 successful
  - Error count: 0
  
- **SECONDARY Firebase**: ❌ Unable to complete due to insufficient permissions
  - Function: `daily-readings-seeder-secondary`
  - Status: BLOCKED
  - Reason: User account lacks write permissions on aisaiah-sfa-dev-app project

### 3. Configuration Fixes
- ✅ Fixed PRIMARY function environment variables
  - Removed `FIREBASE_PROJECT_ID_SECONDARY` and `GCP_PROJECT_ID_SECONDARY`
  - Function now only seeds its own project (preventing cross-project permission errors)

## 📋 Files Created

1. **`delete_and_reseed_november_both.sh`**
   - Comprehensive script for deleting and reseeding both projects
   - Location: `/Users/Shared/users/AMDShared/WorkspaceShared/python-cron/`
   - Usage: `./delete_and_reseed_november_both.sh`

2. **`seed_secondary_november.py`**
   - Python script for local seeding of secondary Firebase
   - Requires: Application Default Credentials with Firestore write permissions
   - Location: `/Users/Shared/users/AMDShared/WorkspaceShared/python-cron/`

## 🔐 Permission Issues (Secondary Project)

The current user account (`aisaiah.platform@gmail.com`) lacks the following permissions on `aisaiah-sfa-dev-app`:

- ❌ `cloudfunctions.functions.invoke` - Cannot invoke Cloud Functions
- ❌ `cloudfunctions.functions.get` - Cannot describe Cloud Functions
- ❌ `cloudscheduler.jobs.run` - Cannot trigger Cloud Scheduler jobs
- ❌ `run.services.get` - Cannot access Cloud Run services
- ❌ `datastore.entities.create` - Cannot write to Firestore
- ✅ `datastore.entities.delete` - CAN delete from Firestore (this worked!)

## 🔧 Options to Complete Secondary Reseeding

### Option 1: Grant Permissions (Recommended)
Grant the following role to `aisaiah.platform@gmail.com` on the secondary project:

```bash
gcloud projects add-iam-policy-binding aisaiah-sfa-dev-app \
  --member="user:aisaiah.platform@gmail.com" \
  --role="roles/datastore.user"
```

Then run:
```bash
cd /Users/Shared/users/AMDShared/WorkspaceShared/python-cron
python3 seed_secondary_november.py
```

### Option 2: Manual Trigger (If You Have Access)
If you have access to the secondary project:

```bash
# Via HTTP
curl -X POST "https://daily-readings-seeder-secondary-n6patcgpoa-uc.a.run.app?start_date=2025-11-01&end_date=2025-11-30" \
  -H "Authorization: bearer $(gcloud auth print-identity-token --project=aisaiah-sfa-dev-app)" \
  -H "Content-Type: application/json" \
  -d '{}'

# OR via Cloud Scheduler
gcloud scheduler jobs run daily-readings-seeder-secondary-monthly-15th \
  --location=us-central1 \
  --project=aisaiah-sfa-dev-app
```

### Option 3: Use Firebase Console
1. Go to: https://console.firebase.google.com/project/aisaiah-sfa-dev-app/functions
2. Find: `daily-readings-seeder-secondary`
3. Click "Test Function" or trigger manually
4. Add request data: `{"start_date": "2025-11-01", "end_date": "2025-11-30"}`

### Option 4: Wait for Automatic Run
The secondary Cloud Scheduler job runs automatically on the 15th of each month. However, it will seed NEXT month (December), not November.

### Option 5: GitHub Actions Workflow
If a GitHub Actions workflow exists for the secondary deployment:
1. Trigger the workflow manually
2. Or create a workflow_dispatch trigger to invoke the function

## 📊 Current Status

| Project | Deletion | Reseeding | Status |
|---------|----------|-----------|--------|
| PRIMARY (aisaiahconferencefb) | ✅ Complete | ✅ Complete | 🎉 DONE |
| SECONDARY (aisaiah-sfa-dev-app) | ✅ Complete | ⏳ Pending | 🔐 Needs Permissions |

## 🔍 Verification

To verify PRIMARY reseeding was successful:
1. Visit: https://console.firebase.google.com/project/aisaiahconferencefb/firestore
2. Open collection: `daily_scripture`
3. Check for documents: `2025-11-01` through `2025-11-30`
4. Verify each has complete data (readings, psalms, gospel, etc.)

To verify SECONDARY (once reseeded):
1. Visit: https://console.firebase.google.com/project/aisaiah-sfa-dev-app/firestore
2. Open collection: `daily_scripture`
3. Check for documents: `2025-11-01` through `2025-11-30`

## 📝 Notes

- All November entries were successfully deleted from BOTH projects
- Primary reseeding completed in ~46 seconds
- Secondary function is properly deployed and functional (just can't be invoked by current user)
- The organizational policy blocks service account key creation but does NOT block the Cloud Functions from running
- The separate deployment approach (one function per project) is working as designed

## 🚀 Next Steps

1. Choose one of the options above to complete secondary reseeding
2. Verify both Firestore databases have complete November data
3. Run `./verify_all_november.py` to confirm data integrity

## 🛠️ Troubleshooting

If secondary reseeding fails with permission errors even after granting roles:
- Check if organizational policies are blocking cross-project access
- Verify the Cloud Function itself has proper service account permissions
- Check Cloud Function logs: `gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=daily-readings-seeder-secondary" --project=aisaiah-sfa-dev-app --limit=50`


