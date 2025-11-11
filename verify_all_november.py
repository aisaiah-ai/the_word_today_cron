#!/usr/bin/env python3
"""
Verify all November 2025 documents have responsorial psalm fields
"""
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
FIREBASE_CRED = "/Users/acthercop/.keys/aisaiahconferencefb-firebase-adminsdk-fbsvc-ed4ace66d0.json"
cred = credentials.Certificate(FIREBASE_CRED)
firebase_admin.initialize_app(cred)
db = firestore.client()

print("Verifying all November 2025 documents...\n")

complete_count = 0
missing_count = 0
missing_dates = []

for day in range(1, 31):
    doc_id = f"2025-11-{day:02d}"
    doc_ref = db.collection('daily_scripture').document(doc_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        print(f"❌ {doc_id}: Document does not exist")
        missing_count += 1
        missing_dates.append(doc_id)
        continue
    
    data = doc.to_dict()
    
    has_psalm = data.get('responsorial_psalm')
    has_psalm_verse = data.get('responsorial_psalm_verse')
    has_psalm_response = data.get('responsorial_psalm_response')
    
    if has_psalm and has_psalm_verse and has_psalm_response:
        print(f"✅ {doc_id}: Complete - {has_psalm_response}")
        complete_count += 1
    else:
        missing_fields = []
        if not has_psalm: missing_fields.append('text')
        if not has_psalm_verse: missing_fields.append('verse')
        if not has_psalm_response: missing_fields.append('response')
        print(f"⚠️  {doc_id}: Missing {', '.join(missing_fields)}")
        missing_count += 1
        missing_dates.append(doc_id)

print(f"\n{'='*60}")
print(f"Summary:")
print(f"  Complete: {complete_count}/30")
print(f"  Missing: {missing_count}/30")
if missing_dates:
    print(f"  Missing dates: {', '.join(missing_dates)}")
print('='*60)

