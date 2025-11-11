#!/usr/bin/env python3
"""
Check if November 2025 documents have responsorial psalm fields
"""
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
FIREBASE_CRED = "/Users/acthercop/.keys/aisaiahconferencefb-firebase-adminsdk-fbsvc-ed4ace66d0.json"
cred = credentials.Certificate(FIREBASE_CRED)
firebase_admin.initialize_app(cred)
db = firestore.client()

print("Checking November 2025 documents for responsorial psalm...\n")

# Check a sample of documents
sample_dates = ['2025-11-01', '2025-11-08', '2025-11-11', '2025-11-15', '2025-11-20', '2025-11-25', '2025-11-30']

for doc_id in sample_dates:
    doc_ref = db.collection('daily_scripture').document(doc_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        print(f"❌ {doc_id}: Document does not exist")
        continue
    
    data = doc.to_dict()
    
    has_psalm = data.get('responsorial_psalm')
    has_psalm_verse = data.get('responsorial_psalm_verse')
    has_gospel = data.get('gospel')
    has_first_reading = data.get('first_reading')
    
    print(f"\n{doc_id}:")
    print(f"  Gospel: {'✅' if has_gospel else '❌'}")
    print(f"  First Reading: {'✅' if has_first_reading else '❌'}")
    print(f"  Responsorial Psalm: {'✅' if has_psalm else '❌'}")
    print(f"  Responsorial Psalm Verse: {'✅' if has_psalm_verse else '❌'}")
    
    if has_psalm_verse:
        print(f"  Psalm Ref: {has_psalm_verse}")
    if has_psalm:
        print(f"  Psalm Text Length: {len(has_psalm)} chars")

print("\n\nDone!")

