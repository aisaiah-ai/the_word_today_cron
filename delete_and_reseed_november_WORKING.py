#!/usr/bin/env python3
"""Delete and reseed November 2025 for BOTH Firebase projects - PROPERLY"""

import os
import sys
import json
import time
from datetime import date, timedelta

# Add daily_readings_seeder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'daily_readings_seeder'))

import firebase_admin
from firebase_admin import credentials, firestore

print("═══════════════════════════════════════════════════════════")
print("🗑️  DELETING & RESEEDING NOVEMBER 2025")
print("═══════════════════════════════════════════════════════════")
print()

# Initialize PRIMARY Firebase
print("🔵 Initializing PRIMARY Firebase...")
try:
    cred_primary = credentials.Certificate('/Users/Shared/users/AMDShared/WorkspaceShared/python-cron/the_word_today_cron/gcp-sa-key.json')
    app_primary = firebase_admin.initialize_app(cred_primary, name='primary')
    db_primary = firestore.client(app=app_primary)
    print("✅ PRIMARY Firebase connected")
except Exception as e:
    print(f"❌ Failed to connect to primary: {e}")
    sys.exit(1)

# Initialize SECONDARY Firebase
print("🟢 Initializing SECONDARY Firebase...")
try:
    os.environ['FIREBASE_PROJECT_ID_SECONDARY'] = 'aisaiah-sfa-dev-app'
    os.environ['GCP_PROJECT_ID_SECONDARY'] = 'aisaiah-sfa-dev-app'
    cred_secondary = credentials.ApplicationDefault()
    app_secondary = firebase_admin.initialize_app(cred_secondary, name='secondary', options={'projectId': 'aisaiah-sfa-dev-app'})
    db_secondary = firestore.client(app=app_secondary)
    print("✅ SECONDARY Firebase connected")
    has_secondary = True
except Exception as e:
    print(f"⚠️  Could not connect to secondary: {e}")
    print("   Will only process PRIMARY")
    has_secondary = False

print()
print("═══════════════════════════════════════════════════════════")
print("🗑️  PHASE 1: DELETING NOVEMBER DOCUMENTS")
print("═══════════════════════════════════════════════════════════")
print()

# Delete from PRIMARY
print("🔵 PRIMARY Firebase (aisaiahconferencefb)")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
deleted_primary = 0
for day in range(1, 31):
    doc_id = f"2025-11-{day:02d}"
    try:
        doc_ref = db_primary.collection('daily_scripture').document(doc_id)
        doc = doc_ref.get()
        if doc.exists:
            doc_ref.delete()
            print(f"  ✅ Deleted {doc_id}")
            deleted_primary += 1
        else:
            print(f"  ⏭️  {doc_id} not found")
    except Exception as e:
        print(f"  ❌ Error deleting {doc_id}: {e}")

print(f"✅ Deleted {deleted_primary} documents from PRIMARY")
print()

# Delete from SECONDARY
if has_secondary:
    print("🟢 SECONDARY Firebase (aisaiah-sfa-dev-app)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    deleted_secondary = 0
    for day in range(1, 31):
        doc_id = f"2025-11-{day:02d}"
        try:
            doc_ref = db_secondary.collection('daily_scripture').document(doc_id)
            doc = doc_ref.get()
            if doc.exists:
                doc_ref.delete()
                print(f"  ✅ Deleted {doc_id}")
                deleted_secondary += 1
            else:
                print(f"  ⏭️  {doc_id} not found")
        except Exception as e:
            print(f"  ❌ Error deleting {doc_id}: {e}")
    
    print(f"✅ Deleted {deleted_secondary} documents from SECONDARY")
    print()

print("═══════════════════════════════════════════════════════════")
print("🌱 PHASE 2: RESEEDING NOVEMBER DOCUMENTS")
print("═══════════════════════════════════════════════════════════")
print()
print("Waiting 3 seconds before reseeding...")
time.sleep(3)

# Import seeding functions
from daily_readings_seeder.main import seed_daily_reading

# Seed PRIMARY
print("🔵 SEEDING PRIMARY Firebase")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
successful_primary = []
errors_primary = []

for day in range(1, 31):
    target_date = date(2025, 11, day)
    date_str = target_date.strftime('%Y-%m-%d')
    print(f"  {date_str}...", end=" ", flush=True)
    
    try:
        result = seed_daily_reading(target_date, dry_run=False, project='primary')
        if result['status'] == 'success':
            print("✅")
            successful_primary.append(date_str)
        else:
            error = result.get('error', result.get('reason', 'unknown'))
            print(f"❌ {error}")
            errors_primary.append({'date': date_str, 'error': error})
    except Exception as e:
        print(f"❌ {e}")
        errors_primary.append({'date': date_str, 'error': str(e)})

print(f"✅ PRIMARY: {len(successful_primary)} successful, {len(errors_primary)} errors")
print()

# Seed SECONDARY
if has_secondary:
    print("🟢 SEEDING SECONDARY Firebase")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    successful_secondary = []
    errors_secondary = []
    
    for day in range(1, 31):
        target_date = date(2025, 11, day)
        date_str = target_date.strftime('%Y-%m-%d')
        print(f"  {date_str}...", end=" ", flush=True)
        
        try:
            result = seed_daily_reading(target_date, dry_run=False, project='secondary')
            if result['status'] == 'success':
                print("✅")
                successful_secondary.append(date_str)
            else:
                error = result.get('error', result.get('reason', 'unknown'))
                print(f"❌ {error}")
                errors_secondary.append({'date': date_str, 'error': error})
        except Exception as e:
            print(f"❌ {e}")
            errors_secondary.append({'date': date_str, 'error': str(e)})
    
    print(f"✅ SECONDARY: {len(successful_secondary)} successful, {len(errors_secondary)} errors")
    print()

print("═══════════════════════════════════════════════════════════")
print("🎉 COMPLETE!")
print("═══════════════════════════════════════════════════════════")
print()
print(f"PRIMARY:")
print(f"  - Deleted: {deleted_primary}")
print(f"  - Seeded: {len(successful_primary)}")
print(f"  - Errors: {len(errors_primary)}")
if has_secondary:
    print()
    print(f"SECONDARY:")
    print(f"  - Deleted: {deleted_secondary}")
    print(f"  - Seeded: {len(successful_secondary)}")
    print(f"  - Errors: {len(errors_secondary)}")


