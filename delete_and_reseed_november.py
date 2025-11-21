#!/usr/bin/env python3
"""Delete all November 2025 documents from secondary Firebase and reseed"""

import os
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import date

# Initialize Firebase for secondary project
PROJECT_ID = "aisaiah-sfa-dev-app"

# Use Application Default Credentials
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, options={'projectId': PROJECT_ID})

db = firestore.client()

print(f"🗑️  Deleting all November 2025 documents from {PROJECT_ID}...")

deleted_count = 0
for day in range(1, 31):
    doc_id = f"2025-11-{day:02d}"
    try:
        doc_ref = db.collection('daily_scripture').document(doc_id)
        doc = doc_ref.get()
        if doc.exists:
            doc_ref.delete()
            print(f"  ✅ Deleted {doc_id}")
            deleted_count += 1
        else:
            print(f"  ⏭️  {doc_id} not found, skipping")
    except Exception as e:
        print(f"  ❌ Error deleting {doc_id}: {e}")

print(f"\n✅ Deleted {deleted_count} documents")
print("\nNow trigger the seeder to reseed all dates...")
