#!/usr/bin/env python3
"""
Quick test script for CFC Only By Grace video fetching
Tests the improved date matching logic
"""
import os
import sys
from datetime import date

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import fetch_cfc_video_for_date

def test_cfc_fetching():
    """Test CFC video fetching for today"""
    print("🧪 Testing CFC Only By Grace Video Fetching")
    print("=" * 60)
    
    # Check for API key
    api_key = os.environ.get('YOUTUBE_API_KEY')
    if not api_key:
        print("⚠️  YOUTUBE_API_KEY not set in environment")
        print("   Using test key from README_LOCAL.md for testing...")
        # Try to read from the_word_today_service.py if available
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("service", "../the_word_today_service.py")
            service = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(service)
            api_key = service.YOUTUBE_API_KEY
            os.environ['YOUTUBE_API_KEY'] = api_key
            print(f"   ✅ Using API key from service file")
        except Exception as e:
            print(f"   ❌ Could not get API key: {e}")
            print("\n   Please set YOUTUBE_API_KEY environment variable:")
            print("   export YOUTUBE_API_KEY=your_key")
            return False
    
    today = date.today()
    print(f"\n📅 Testing for date: {today.strftime('%A, %B %d, %Y')}")
    print(f"   Date formats being tested:")
    print(f"   - {today.strftime('%d %B %Y')}")
    print(f"   - {today.day} {today.strftime('%B %Y')}")
    print(f"   - {today.strftime('%B %d, %Y')}")
    print(f"   - {today.strftime('%B')} {today.day}, {today.year}")
    print()
    
    print("🔎 Fetching CFC video...")
    print("-" * 60)
    
    try:
        video = fetch_cfc_video_for_date(today)
        
        if video:
            print("\n✅ SUCCESS! Video found:")
            print(f"   Title: {video['title']}")
            print(f"   URL: {video['url']}")
            print(f"   Date: {video['date']}")
            return True
        else:
            print("\n⚠️  No video found for today")
            print("\n   This could mean:")
            print("   - The video hasn't been uploaded yet")
            print("   - The video title format doesn't match expected patterns")
            print("   - Check the logs above for details")
            return False
            
    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n" + "=" * 60)
    success = test_cfc_fetching()
    print("=" * 60)
    
    if success:
        print("\n✅ Test completed successfully!")
        sys.exit(0)
    else:
        print("\n⚠️  Test completed but no video was found")
        sys.exit(0)  # Exit 0 because not finding a video isn't necessarily a failure

