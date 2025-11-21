#!/usr/bin/env python3
"""Test fetching USCCB data for a single day (no Firebase needed)"""

import sys
import os
from datetime import date

# Add daily_readings_seeder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'daily_readings_seeder'))

from daily_readings_seeder.main import fetch_usccb_reading_data, fetch_public_scripture_text

# Test date - November 23, 2025 (Sunday - should have 2nd reading)
TEST_DATE = date(2025, 11, 23)

print("═══════════════════════════════════════════════════════════")
print(f"🧪 FETCHING USCCB DATA FOR: {TEST_DATE.strftime('%A, %B %d, %Y')}")
print("═══════════════════════════════════════════════════════════")
print()
print("This test fetches data from USCCB.org without touching Firebase")
print()

# Fetch USCCB data
print("📡 Fetching from USCCB...")
usccb_data = fetch_usccb_reading_data(TEST_DATE)

if not usccb_data:
    print("❌ Failed to fetch USCCB data")
    sys.exit(1)

print("✅ Successfully fetched USCCB data")
print()

# Display what was found
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("📖 READINGS FOUND:")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()

# First Reading
if 'reading1' in usccb_data:
    ref = usccb_data['reading1'].get('reference', 'N/A')
    print(f"✅ First Reading: {ref}")
else:
    print("❌ First Reading: NOT FOUND")

# Second Reading
if 'reading2' in usccb_data:
    ref = usccb_data['reading2'].get('reference', 'N/A')
    print(f"✅ Second Reading: {ref}")
    print("   🎉 SECOND READING IS PRESENT!")
else:
    print("⚠️  Second Reading: NOT FOUND (might be a weekday)")

# Responsorial Psalm
if 'responsorialPsalm' in usccb_data:
    ref = usccb_data['responsorialPsalm'].get('reference', 'N/A')
    response = usccb_data['responsorialPsalm'].get('response', '')
    print(f"✅ Responsorial Psalm: {ref}")
    if response:
        print(f"   Response: {response}")
else:
    print("❌ Responsorial Psalm: NOT FOUND")

# Gospel
if 'gospel' in usccb_data:
    ref = usccb_data['gospel'].get('reference', 'N/A')
    print(f"✅ Gospel: {ref}")
else:
    print("❌ Gospel: NOT FOUND")

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("🔍 TESTING TEXT FETCHING:")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()

# Test fetching text for second reading if it exists
if 'reading2' in usccb_data:
    ref = usccb_data['reading2'].get('reference', '')
    if ref:
        print(f"📖 Fetching text for second reading: {ref}")
        text = fetch_public_scripture_text(ref)
        if text:
            print(f"✅ Got {len(text)} characters")
            print(f"   Preview: {text[:150]}...")
        else:
            print("⚠️  Could not fetch text (might be Deuterocanonical)")

# Test fetching gospel text
if 'gospel' in usccb_data:
    ref = usccb_data['gospel'].get('reference', '')
    if ref:
        print()
        print(f"📖 Fetching text for gospel: {ref}")
        text = fetch_public_scripture_text(ref)
        if text:
            print(f"✅ Got {len(text)} characters")
            print(f"   Preview: {text[:150]}...")
            print()
            print(f"📝 Body field would be: 'Gospel: {ref}'")
        else:
            print("⚠️  Could not fetch text")

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("✅ TEST COMPLETE - NO FIREBASE ACCESS NEEDED!")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()
print("💡 This shows what data WOULD be stored when seeding")
print("   The actual Cloud Function has permissions to write this data")

