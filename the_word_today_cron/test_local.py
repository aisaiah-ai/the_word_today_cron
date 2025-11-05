#!/usr/bin/env python3
"""
Local test script for The Word Today Cloud Function
Tests the function locally without deploying to GCP
"""
import os
import sys
from unittest.mock import Mock
from datetime import date

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import the_word_today_cron, initialize_firebase


def create_mock_request(method='GET', path='/', headers=None):
    """Create a mock Flask request object"""
    request = Mock()
    request.method = method
    request.path = path
    request.headers = headers or {}
    request.args = {}
    request.json = None
    return request


def test_function_locally():
    """Test the Cloud Function locally"""
    print("🧪 Testing The Word Today Cloud Function Locally")
    print("=" * 60)
    
    # Check required environment variables
    print("\n📋 Checking environment variables...")
    required_vars = ['YOUTUBE_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
            print(f"  ❌ {var}: Not set")
        else:
            print(f"  ✅ {var}: Set")
    
    # Check Firebase credentials
    if os.environ.get('FIREBASE_CREDENTIALS_JSON'):
        print("  ✅ FIREBASE_CREDENTIALS_JSON: Set")
    elif os.environ.get('FIREBASE_CREDENTIALS_JSON_B64'):
        print("  ✅ FIREBASE_CREDENTIALS_JSON_B64: Set")
    elif os.environ.get('FIREBASE_CRED'):
        print(f"  ✅ FIREBASE_CRED: {os.environ.get('FIREBASE_CRED')}")
    else:
        print("  ⚠️  Firebase credentials: Not set (will use Application Default Credentials)")
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease set them before running:")
        for var in missing_vars:
            print(f"  export {var}=your_value")
        return False
    
    # Test Firebase initialization
    print("\n🔥 Testing Firebase initialization...")
    try:
        initialize_firebase()
        print("  ✅ Firebase initialized successfully")
    except Exception as e:
        print(f"  ⚠️  Firebase initialization warning: {str(e)}")
        print("  (This is OK if you're testing without Firebase)")
    
    # Test the function
    print("\n🚀 Testing Cloud Function...")
    print("-" * 60)
    
    try:
        mock_request = create_mock_request()
        response, status_code = the_word_today_cron(mock_request)
        
        print(f"\n✅ Function completed with status code: {status_code}")
        print(f"\n📊 Response:")
        print(f"  Status Code: {response.get('statusCode', 'N/A')}")
        
        body = response.get('body', {})
        print(f"  Status: {body.get('status', 'N/A')}")
        print(f"  Date: {body.get('date', 'N/A')}")
        print(f"  Processed Dates: {body.get('processed_dates', [])}")
        print(f"  Processed Videos: {len(body.get('processed_videos', []))}")
        print(f"  Errors: {len(body.get('errors', []))}")
        
        if body.get('errors'):
            print("\n⚠️  Errors encountered:")
            for error in body.get('errors', []):
                print(f"  - {error}")
        
        if body.get('processed_videos'):
            print("\n✅ Videos processed:")
            for video in body.get('processed_videos', []):
                print(f"  - {video}")
        
        return status_code == 200
        
    except Exception as e:
        print(f"\n❌ Function execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n" + "=" * 60)
    success = test_function_locally()
    print("=" * 60)
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)

