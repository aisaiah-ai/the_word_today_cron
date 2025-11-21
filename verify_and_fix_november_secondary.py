#!/usr/bin/env python3
"""
Verify and fix November 2025 documents in secondary Firebase
Checks if each document has correct unique data, not default/duplicate data
"""

import os
import sys
from datetime import date, timedelta

# Add daily_readings_seeder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'daily_readings_seeder'))

import firebase_admin
from firebase_admin import credentials, firestore
from daily_readings_seeder.main import seed_daily_reading

print("═══════════════════════════════════════════════════════════")
print("🔍 VERIFYING NOVEMBER 2025 IN SECONDARY FIREBASE")
print("═══════════════════════════════════════════════════════════")
print()

# Initialize SECONDARY Firebase
print("🟢 Connecting to SECONDARY Firebase (aisaiah-sfa-dev-app)...")
try:
    os.environ['FIREBASE_PROJECT_ID_SECONDARY'] = 'aisaiah-sfa-dev-app'
    os.environ['GCP_PROJECT_ID_SECONDARY'] = 'aisaiah-sfa-dev-app'
    cred = credentials.ApplicationDefault()
    app = firebase_admin.initialize_app(cred, name='secondary', options={'projectId': 'aisaiah-sfa-dev-app'})
    db = firestore.client(app=app)
    print("✅ Connected to secondary Firebase")
except Exception as e:
    print(f"❌ Failed to connect: {e}")
    sys.exit(1)

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("📋 PHASE 1: CHECKING ALL NOVEMBER DOCUMENTS")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()

issues = []
correct_docs = []
missing_docs = []

for day in range(1, 31):
    doc_id = f"2025-11-{day:02d}"
    print(f"Checking {doc_id}...", end=" ", flush=True)
    
    try:
        doc_ref = db.collection('daily_scripture').document(doc_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            print("❌ MISSING")
            missing_docs.append(doc_id)
            continue
        
        data = doc.to_dict()
        
        # Check for issues:
        # 1. Default "John 3:16" for all days (incorrect)
        # 2. Missing gospel_verse
        # 3. Body is not in short format
        # 4. Missing responsorial_psalm_verse
        
        has_issues = False
        issue_reasons = []
        
        gospel_verse = data.get('gospel_verse', '')
        
        # Issue 1: All days have same gospel (John 3:16 default)
        if gospel_verse == 'John 3:16' and day != 13:  # Nov 13 might legitimately have this
            has_issues = True
            issue_reasons.append("default gospel")
        
        # Issue 2: Missing essential fields
        if not gospel_verse:
            has_issues = True
            issue_reasons.append("missing gospel_verse")
        
        if not data.get('responsorial_psalm_verse'):
            has_issues = True
            issue_reasons.append("missing psalm_verse")
        
        # Issue 3: Body should be short format like "Gospel: Luke 17:26-37"
        body = data.get('body', '')
        if body and len(body) > 100:  # Body is too long (has full text)
            has_issues = True
            issue_reasons.append("body too long")
        elif body and not body.startswith('Gospel:'):
            # Check if it's old format (has full text)
            if len(body.split()) > 10:  # More than 10 words = probably full text
                has_issues = True
                issue_reasons.append("body has full text")
        
        # Issue 4: Check if USCCB link exists
        if not data.get('usccb_link'):
            has_issues = True
            issue_reasons.append("missing usccb_link")
        
        if has_issues:
            print(f"❌ ISSUES: {', '.join(issue_reasons)}")
            issues.append({
                'doc_id': doc_id,
                'reasons': issue_reasons,
                'data': data
            })
        else:
            print("✅ OK")
            correct_docs.append(doc_id)
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        issues.append({
            'doc_id': doc_id,
            'reasons': [f'error: {e}'],
            'data': None
        })

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("📊 SUMMARY")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"✅ Correct: {len(correct_docs)}")
print(f"❌ Issues: {len(issues)}")
print(f"⚠️  Missing: {len(missing_docs)}")
print()

if correct_docs:
    print(f"✅ Correct documents: {', '.join(correct_docs[:5])}")
    if len(correct_docs) > 5:
        print(f"   ... and {len(correct_docs) - 5} more")
    print()

if issues:
    print("❌ Documents with issues:")
    for issue in issues[:10]:  # Show first 10
        print(f"   - {issue['doc_id']}: {', '.join(issue['reasons'])}")
    if len(issues) > 10:
        print(f"   ... and {len(issues) - 10} more")
    print()

if missing_docs:
    print(f"⚠️  Missing documents: {', '.join(missing_docs)}")
    print()

# Ask user if they want to fix
if issues or missing_docs:
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🔧 PHASE 2: FIXING ISSUES")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    
    docs_to_fix = [item['doc_id'] for item in issues] + missing_docs
    print(f"Will delete and reseed {len(docs_to_fix)} documents")
    print()
    
    response = input("Do you want to proceed with fixing? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        print()
        print("🗑️  Deleting incorrect documents...")
        deleted = 0
        for doc_id in docs_to_fix:
            try:
                doc_ref = db.collection('daily_scripture').document(doc_id)
                doc = doc_ref.get()
                if doc.exists:
                    doc_ref.delete()
                    print(f"  ✅ Deleted {doc_id}")
                    deleted += 1
                else:
                    print(f"  ⏭️  {doc_id} not found (will create)")
            except Exception as e:
                print(f"  ❌ Error deleting {doc_id}: {e}")
        
        print(f"\n✅ Deleted {deleted} documents")
        print()
        print("🌱 Reseeding...")
        print()
        
        successful = []
        failed = []
        
        for doc_id in docs_to_fix:
            # Parse date from doc_id
            year, month, day = doc_id.split('-')
            target_date = date(int(year), int(month), int(day))
            
            print(f"  Seeding {doc_id}...", end=" ", flush=True)
            
            try:
                result = seed_daily_reading(target_date, dry_run=False, project='secondary')
                
                if result['status'] == 'success':
                    print("✅")
                    successful.append(doc_id)
                else:
                    error = result.get('error', result.get('reason', 'unknown'))
                    print(f"❌ {error}")
                    failed.append({'doc_id': doc_id, 'error': error})
            except Exception as e:
                print(f"❌ {e}")
                failed.append({'doc_id': doc_id, 'error': str(e)})
        
        print()
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("🎉 FIXING COMPLETE!")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"✅ Successfully reseeded: {len(successful)}")
        print(f"❌ Failed: {len(failed)}")
        
        if failed:
            print()
            print("Failed documents:")
            for item in failed:
                print(f"  - {item['doc_id']}: {item['error']}")
    else:
        print("\n⏭️  Skipping fixes")
else:
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🎉 ALL DOCUMENTS ARE CORRECT!")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

print()
print("💡 TIP: Check Firebase Console to verify:")
print("   https://console.firebase.google.com/project/aisaiah-sfa-dev-app/firestore")


