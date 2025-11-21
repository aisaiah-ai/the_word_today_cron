#!/usr/bin/env python3
"""
AUTOMATED: Verify and fix November 2025 documents in secondary Firebase
Prerequisites: Download secondary Firebase key from Firebase Console first!
"""

import os
import sys
from datetime import date

# Add daily_readings_seeder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'daily_readings_seeder'))

# Check if secondary Firebase key exists
SECONDARY_KEY_PATH = '/Users/Shared/users/AMDShared/WorkspaceShared/python-cron/firebase-secondary-key.json'

if not os.path.exists(SECONDARY_KEY_PATH):
    print("═══════════════════════════════════════════════════════════")
    print("❌ MISSING FIREBASE KEY FOR SECONDARY PROJECT")
    print("═══════════════════════════════════════════════════════════")
    print()
    print("You need to download the Firebase Admin SDK key first:")
    print()
    print("1. Go to: https://console.firebase.google.com/project/aisaiah-sfa-dev-app/settings/serviceaccounts/adminsdk")
    print("2. Click 'Generate New Private Key'")
    print("3. Save it as: firebase-secondary-key.json")
    print("4. Move it to: /Users/Shared/users/AMDShared/WorkspaceShared/python-cron/")
    print()
    print("Then run this script again")
    sys.exit(1)

import firebase_admin
from firebase_admin import credentials, firestore
from daily_readings_seeder.main import seed_daily_reading, fetch_usccb_reading_data

print("═══════════════════════════════════════════════════════════")
print("🔍 AUTOMATED VERIFICATION & FIX")
print("═══════════════════════════════════════════════════════════")
print()

# Initialize secondary Firebase with the key
print("🟢 Connecting to SECONDARY Firebase...")
try:
    cred = credentials.Certificate(SECONDARY_KEY_PATH)
    app = firebase_admin.initialize_app(cred, name='secondary')
    db = firestore.client(app=app)
    print("✅ Connected successfully")
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

# Check all November documents
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
        has_issues = False
        issue_reasons = []
        
        gospel_verse = data.get('gospel_verse', '')
        
        # Check for default "John 3:16" on wrong days
        if gospel_verse == 'John 3:16' and day != 13:
            has_issues = True
            issue_reasons.append("default gospel")
        
        # Check for missing fields
        if not gospel_verse:
            has_issues = True
            issue_reasons.append("missing gospel_verse")
        
        if not data.get('responsorial_psalm_verse'):
            has_issues = True
            issue_reasons.append("missing psalm")
        
        # Check body format (should be short)
        body = data.get('body', '')
        if body and len(body) > 100:
            has_issues = True
            issue_reasons.append("body too long")
        
        if has_issues:
            print(f"❌ {', '.join(issue_reasons)}")
            issues.append(doc_id)
        else:
            print("✅")
            correct_docs.append(doc_id)
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        issues.append(doc_id)

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("📊 SUMMARY")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"✅ Correct: {len(correct_docs)}")
print(f"❌ Issues: {len(issues)}")
print(f"⚠️  Missing: {len(missing_docs)}")
print()

if correct_docs:
    print(f"✅ Correct: {', '.join(correct_docs)}")
    print()

docs_to_fix = issues + missing_docs

if not docs_to_fix:
    print("🎉 ALL DOCUMENTS ARE CORRECT!")
    sys.exit(0)

print(f"❌ Need to fix: {', '.join(docs_to_fix)}")
print()

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("🔧 PHASE 2: FIXING DOCUMENTS")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()

print(f"Will delete and reseed {len(docs_to_fix)} documents")
print()

# Delete incorrect documents
print("🗑️  Deleting...")
for doc_id in docs_to_fix:
    try:
        doc_ref = db.collection('daily_scripture').document(doc_id)
        doc = doc_ref.get()
        if doc.exists:
            doc_ref.delete()
            print(f"  ✅ Deleted {doc_id}")
        else:
            print(f"  ⏭️  {doc_id} not found")
    except Exception as e:
        print(f"  ❌ Error deleting {doc_id}: {e}")

print()
print("🌱 Reseeding...")
print()

successful = []
failed = []

# Reseed using the main seeding function
for doc_id in docs_to_fix:
    year, month, day = doc_id.split('-')
    target_date = date(int(year), int(month), int(day))
    
    print(f"  {doc_id}...", end=" ", flush=True)
    
    try:
        # Fetch USCCB data
        usccb_data = fetch_usccb_reading_data(target_date)
        
        if not usccb_data:
            print("❌ No USCCB data")
            failed.append({'doc_id': doc_id, 'error': 'No USCCB data'})
            continue
        
        # Create document data
        gospel_ref = usccb_data.get('gospel', {}).get('reference', '')
        
        doc_data = {
            'id': doc_id,
            'title': 'Daily Scripture',
            'reference': gospel_ref,
            'usccb_link': usccb_data.get('url', ''),
            'body': f"Gospel: {gospel_ref}",  # SHORT FORMAT
            'gospel_verse': gospel_ref,
            'responsorial_psalm_verse': usccb_data.get('responsorialPsalm', {}).get('reference', ''),
            'responsorial_psalm_response': usccb_data.get('responsorialPsalm', {}).get('response', ''),
            'first_reading_verse': usccb_data.get('reading1', {}).get('reference', ''),
            'createdAt': firestore.SERVER_TIMESTAMP,
            'updatedAt': firestore.SERVER_TIMESTAMP
        }
        
        # Add second reading if present (Sundays)
        if 'reading2' in usccb_data:
            doc_data['second_reading_verse'] = usccb_data['reading2'].get('reference', '')
        
        # Write to Firestore
        doc_ref = db.collection('daily_scripture').document(doc_id)
        doc_ref.set(doc_data, merge=False)
        
        print("✅")
        successful.append(doc_id)
        
    except Exception as e:
        print(f"❌ {e}")
        failed.append({'doc_id': doc_id, 'error': str(e)})

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("🎉 COMPLETE!")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"✅ Successfully fixed: {len(successful)}")
print(f"❌ Failed: {len(failed)}")

if failed:
    print()
    print("Failed:")
    for item in failed:
        print(f"  - {item['doc_id']}: {item['error']}")


