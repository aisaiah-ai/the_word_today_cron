#!/usr/bin/env python3
"""Test seeding a single day to verify secondary reading is working"""

import os
import sys
from datetime import date

# Add daily_readings_seeder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'daily_readings_seeder'))

from daily_readings_seeder.main import seed_daily_reading, initialize_firebase
import firebase_admin
from firebase_admin import credentials, firestore

# Test date - November 17, 2025 should have a second reading (it's Sunday)
TEST_DATE = date(2025, 11, 17)  # Sunday - should have 2nd reading
# TEST_DATE = date(2025, 11, 27)  # Thursday Thanksgiving - should have 2nd reading

print("═══════════════════════════════════════════════════════════")
print(f"🧪 TESTING SINGLE DAY SEED: {TEST_DATE.strftime('%Y-%m-%d')}")
print("═══════════════════════════════════════════════════════════")
print()

# Initialize Firebase
print("🔵 Connecting to PRIMARY Firebase...")
try:
    db = initialize_firebase('primary')
    print("✅ Connected to PRIMARY Firebase")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("📅 SEEDING...")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()

# Seed the date
result = seed_daily_reading(TEST_DATE, dry_run=False, project='primary')

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("📊 RESULT")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"Status: {result['status']}")
if result['status'] != 'success':
    print(f"Error/Reason: {result.get('error', result.get('reason', 'unknown'))}")
print()

# Retrieve and display the document
doc_id = TEST_DATE.strftime('%Y-%m-%d')
print(f"🔍 Fetching document: {doc_id}")
print()

try:
    doc_ref = db.collection('daily_scripture').document(doc_id)
    doc = doc_ref.get()
    
    if doc.exists:
        data = doc.to_dict()
        print("✅ Document found!")
        print()
        
        # Display key fields
        print("📖 READINGS:")
        print(f"  First Reading: {data.get('first_reading_verse', 'N/A')}")
        if data.get('first_reading'):
            print(f"    Text: {data.get('first_reading')[:100]}...")
        
        print()
        print(f"  Second Reading: {data.get('second_reading_verse', 'N/A')}")
        if data.get('second_reading'):
            print(f"    Text: {data.get('second_reading')[:100]}...")
            print("    ✅ SECOND READING IS PRESENT!")
        else:
            print("    ⚠️  No second reading (might be a weekday)")
        
        print()
        print(f"  Gospel: {data.get('gospel_verse', 'N/A')}")
        if data.get('gospel'):
            print(f"    Text: {data.get('gospel')[:100]}...")
        
        print()
        print(f"  Responsorial Psalm: {data.get('responsorial_psalm_verse', 'N/A')}")
        if data.get('responsorial_psalm_response'):
            print(f"    Response: {data.get('responsorial_psalm_response')}")
        
        print()
        print(f"  Body (should be short): {data.get('body', 'N/A')}")
        
        print()
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("✅ TEST COMPLETE!")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # Check if it has second reading
        if data.get('second_reading_verse'):
            print("🎉 SUCCESS: Second reading field is populated!")
        else:
            print("⚠️  This date doesn't have a second reading (likely a weekday)")
            print("   Try a Sunday date to test second reading functionality")
    else:
        print(f"❌ Document {doc_id} not found!")
        
except Exception as e:
    print(f"❌ Error fetching document: {e}")

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("💡 TIP: Change TEST_DATE at the top of this script to test different days")
print("   Sundays usually have second readings")
print("   Weekdays usually don't have second readings")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

