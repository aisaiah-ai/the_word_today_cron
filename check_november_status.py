#!/usr/bin/env python3
"""Check what November documents exist in both Firebase databases"""

import firebase_admin
from firebase_admin import credentials, firestore

# Initialize primary Firebase
try:
    cred_primary = credentials.Certificate('/Users/Shared/users/AMDShared/WorkspaceShared/python-cron/the_word_today_cron/gcp-sa-key.json')
    app_primary = firebase_admin.initialize_app(cred_primary, name='primary')
    db_primary = firestore.client(app=app_primary)
    print("✅ Connected to PRIMARY Firebase")
except Exception as e:
    print(f"❌ Failed to connect to primary: {e}")
    db_primary = None

# Initialize secondary Firebase with ADC
try:
    cred_secondary = credentials.ApplicationDefault()
    app_secondary = firebase_admin.initialize_app(cred_secondary, name='secondary', options={'projectId': 'aisaiah-sfa-dev-app'})
    db_secondary = firestore.client(app=app_secondary)
    print("✅ Connected to SECONDARY Firebase")
except Exception as e:
    print(f"❌ Failed to connect to secondary: {e}")
    db_secondary = None

print()

# Check PRIMARY
if db_primary:
    print("=== PRIMARY Firebase (aisaiahconferencefb) ===")
    docs_found = []
    for day in range(1, 31):
        doc_id = f"2025-11-{day:02d}"
        doc = db_primary.collection('daily_scripture').document(doc_id).get()
        if doc.exists:
            docs_found.append(doc_id)
    
    if docs_found:
        print(f"✅ Found {len(docs_found)} November documents:")
        for doc_id in docs_found[:5]:
            print(f"   - {doc_id}")
        if len(docs_found) > 5:
            print(f"   ... and {len(docs_found) - 5} more")
    else:
        print("❌ NO November documents found!")
    print()

# Check SECONDARY
if db_secondary:
    print("=== SECONDARY Firebase (aisaiah-sfa-dev-app) ===")
    docs_found = []
    try:
        for day in range(1, 31):
            doc_id = f"2025-11-{day:02d}"
            doc = db_secondary.collection('daily_scripture').document(doc_id).get()
            if doc.exists:
                docs_found.append(doc_id)
        
        if docs_found:
            print(f"✅ Found {len(docs_found)} November documents:")
            for doc_id in docs_found[:5]:
                print(f"   - {doc_id}")
            if len(docs_found) > 5:
                print(f"   ... and {len(docs_found) - 5} more")
        else:
            print("❌ NO November documents found!")
    except Exception as e:
        print(f"❌ Error reading secondary: {e}")


