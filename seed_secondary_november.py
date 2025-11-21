#!/usr/bin/env python3
"""Seed November 2025 to secondary Firebase using local execution"""

import os
import sys

# Add daily_readings_seeder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'daily_readings_seeder'))

from datetime import date, timedelta
from daily_readings_seeder.main import initialize_firebase, seed_daily_reading

# Set environment variables for secondary project
os.environ['FIREBASE_PROJECT_ID_SECONDARY'] = 'aisaiah-sfa-dev-app'
os.environ['GCP_PROJECT_ID_SECONDARY'] = 'aisaiah-sfa-dev-app'

print("🌱 Seeding November 2025 to SECONDARY Firebase")
print("Project: aisaiah-sfa-dev-app")
print("Date range: 2025-11-01 to 2025-11-30")
print("")

# Initialize secondary Firebase
try:
    db = initialize_firebase('secondary')
    print("✅ Secondary Firebase initialized")
except Exception as e:
    print(f"❌ Failed to initialize secondary Firebase: {e}")
    sys.exit(1)

# Seed all days in November 2025
start_date = date(2025, 11, 1)
end_date = date(2025, 11, 30)

successful = []
errors = []

current_date = start_date
while current_date <= end_date:
    date_str = current_date.strftime('%Y-%m-%d')
    print(f"📅 Processing {date_str}...", end=" ")
    
    try:
        result = seed_daily_reading(current_date, dry_run=False, project='secondary')
        
        if result['status'] == 'success':
            print("✅ success")
            successful.append(date_str)
        elif result['status'] == 'skipped':
            reason = result.get('reason', 'unknown')
            print(f"⏭️  skipped ({reason})")
        else:
            error = result.get('error', 'unknown')
            print(f"❌ error: {error}")
            errors.append({'date': date_str, 'error': error})
    except Exception as e:
        print(f"❌ exception: {e}")
        errors.append({'date': date_str, 'error': str(e)})
    
    current_date += timedelta(days=1)

print("")
print("═══════════════════════════════════════════════════════════")
print("📊 SUMMARY")
print("═══════════════════════════════════════════════════════════")
print(f"✅ Successful: {len(successful)}")
print(f"❌ Errors: {len(errors)}")

if errors:
    print("")
    print("Errors:")
    for err in errors:
        print(f"  - {err['date']}: {err['error']}")


