#!/usr/bin/env python3
"""
Local test script for Daily Readings Seeder
Tests the seeder function locally without deploying to GCP
"""
import os
import sys
from unittest.mock import Mock
from datetime import date, timedelta

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import seed_daily_readings_cron, seed_daily_reading, initialize_firebase


def create_mock_request(method='GET', path='/', args=None):
    """Create a mock Flask request object"""
    request = Mock()
    request.method = method
    request.path = path
    request.args = args or {}
    request.json = None
    return request


def test_seeder_locally():
    """Test the Daily Readings Seeder locally"""
    print("🧪 Testing Daily Readings Seeder Locally")
    print("=" * 60)
    
    # Check required environment variables
    print("\n📋 Checking environment variables...")
    
    # Check Firebase credentials
    if os.environ.get('FIREBASE_CREDENTIALS_JSON'):
        print("  ✅ FIREBASE_CREDENTIALS_JSON: Set")
    elif os.environ.get('FIREBASE_CREDENTIALS_JSON_B64'):
        print("  ✅ FIREBASE_CREDENTIALS_JSON_B64: Set")
    elif os.environ.get('FIREBASE_CRED'):
        print(f"  ✅ FIREBASE_CRED: {os.environ.get('FIREBASE_CRED')}")
    else:
        print("  ⚠️  Firebase credentials: Not set (will use Application Default Credentials)")
    
    # Test Firebase initialization
    print("\n🔥 Testing Firebase initialization...")
    try:
        initialize_firebase()
        print("  ✅ Firebase initialized successfully")
    except Exception as e:
        print(f"  ⚠️  Firebase initialization warning: {str(e)}")
        print("  (This is OK if you're testing without Firebase)")
    
    # Test single date seeding
    print("\n📅 Testing single date seeding...")
    print("-" * 60)
    
    try:
        test_date = date.today()
        result = seed_daily_reading(test_date, dry_run=True)
        
        print(f"\n✅ Single date seeding test completed")
        print(f"  Date: {test_date}")
        print(f"  Status: {result.get('status')}")
        
    except Exception as e:
        print(f"\n❌ Single date seeding failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test the full function
    print("\n🚀 Testing Cloud Function...")
    print("-" * 60)
    
    try:
        mock_request = create_mock_request(args={'days': '3'})  # Test with 3 days
        response, status_code = seed_daily_readings_cron(mock_request)
        
        print(f"\n✅ Function completed with status code: {status_code}")
        print(f"\n📊 Response:")
        print(f"  Status Code: {response.get('statusCode', 'N/A')}")
        
        body = response.get('body', {})
        print(f"  Status: {body.get('status', 'N/A')}")
        print(f"  Days Seeded: {body.get('days_seeded', 'N/A')}")
        print(f"  Processed Dates: {len(body.get('processed_dates', []))}")
        print(f"  Successful: {len(body.get('successful', []))}")
        print(f"  Errors: {len(body.get('errors', []))}")
        
        if body.get('errors'):
            print("\n⚠️  Errors encountered:")
            for error in body.get('errors', []):
                print(f"  - {error}")
        
        if body.get('successful'):
            print("\n✅ Successfully seeded dates:")
            for date_str in body.get('successful', [])[:5]:  # Show first 5
                print(f"  - {date_str}")
            if len(body.get('successful', [])) > 5:
                print(f"  ... and {len(body.get('successful', [])) - 5} more")
        
        return status_code == 200
        
    except Exception as e:
        print(f"\n❌ Function execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n" + "=" * 60)
    success = test_seeder_locally()
    print("=" * 60)
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)

