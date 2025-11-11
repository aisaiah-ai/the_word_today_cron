#!/usr/bin/env python3
"""
Check specific November 2025 documents for responsorial psalm fields
"""
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
FIREBASE_CRED = "/Users/acthercop/.keys/aisaiahconferencefb-firebase-adminsdk-fbsvc-ed4ace66d0.json"
cred = credentials.Certificate(FIREBASE_CRED)
firebase_admin.initialize_app(cred)
db = firestore.client()

# Check multiple dates including ones with Deuterocanonical texts
dates_to_check = ['2025-11-01', '2025-11-04', '2025-11-08', '2025-11-11', '2025-11-25', '2025-11-30']

for doc_id in dates_to_check:
    print(f"\n{'='*60}")
    print(f"Document: {doc_id}")
    print('='*60)
    
    doc_ref = db.collection('daily_scripture').document(doc_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        print(f"❌ Document does not exist")
        continue
    
    data = doc.to_dict()
    
    # Print responsorial psalm fields
    print(f"\nResponsorial Psalm Fields:")
    psalm_verse = data.get('responsorial_psalm_verse', 'NOT SET')
    psalm_response = data.get('responsorial_psalm_response', 'NOT SET')
    psalm_text = data.get('responsorial_psalm')
    
    print(f"  responsorial_psalm_verse: {psalm_verse}")
    print(f"  responsorial_psalm_response: {psalm_response}")
    
    if psalm_text:
        print(f"  responsorial_psalm (text): {psalm_text[:100]}..." if len(psalm_text) > 100 else f"  responsorial_psalm (text): {psalm_text}")
    else:
        print(f"  responsorial_psalm (text): NOT SET")
    
    # Summary
    has_all = psalm_verse != 'NOT SET' and psalm_response != 'NOT SET' and psalm_text
    print(f"\n  ✅ Complete!" if has_all else f"  ⚠️  Missing fields")
    
    # Print other key fields
    print(f"\nOther Fields:")
    print(f"  gospel_verse: {data.get('gospel_verse', 'NOT SET')}")
    print(f"  first_reading_verse: {data.get('first_reading_verse', 'NOT SET')}")

print("\n" + "="*60)
print("Done!")

