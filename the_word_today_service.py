import requests
import datetime
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Updating theWordTodayUrl
# Updating cfcOnlyByGraceReflectionsUrl
# 🔑 Replace with your YouTube API key
YOUTUBE_API_KEY = "AIzaSyDx8mRf6ssB1bUYhhL6bRBYI31CMavs1_4"
# ✅ Correct channel ID for The Word Today TV
CHANNEL_ID = "UC9gpFF4p56T4wQtinfAT3Eg"
# ✅ Correct channel ID for Couples for Christ Media
CFC_CHANNEL_ID = "UCVb6g46-SKkTLTHTF-wO8Kw"
# ✅ Correct channel ID for Brother Bo Sanchez
BO_CHANNEL_ID = "UCFoHFFBWDwxbpa1bYH736RA"

BASE_URL = "https://www.googleapis.com/youtube/v3/search"

# 🔑 Path to your Firebase service account key JSON
# FIREBASE_CRED = "serviceAccountKey.json"
FIREBASE_CRED = "/Users/acthercop/.keys/aisaiahconferencefb-firebase-adminsdk-fbsvc-ed4ace66d0.json"
# PROJ = "aisaiahconferencefb"

# DRY_RUN = "True"
DRY_RUN = ""
# Initialize Firebase
cred = credentials.Certificate(FIREBASE_CRED)
firebase_admin.initialize_app(cred)
db = firestore.client()


def build_search_url(target_date: datetime.date):
    """Build YouTube Data API search URL with date string"""
    date_str = target_date.strftime("%A, %B %d, %Y").replace(f" 0{target_date.day},", f" {target_date.day},")  # e.g. "Tuesday, October 1, 2025"
    query = f"Today's Catholic Mass Readings & Gospel Reflection {date_str}"
    encoded_query = requests.utils.quote(query)

    url = (
        f"{BASE_URL}?part=snippet"
        f"&channelId={CHANNEL_ID}"
        f"&q={encoded_query}"
        f"&key={YOUTUBE_API_KEY}"
        f"&maxResults=5&type=video&order=date"
    )
    return url, date_str


def fetch_video_for_date(target_date: datetime.date):
    url, date_str = build_search_url(target_date)
    print(f"\n🔎 Fetching video for {date_str}")
    print(f"Request URL: {url}\n")

    response = requests.get(url)
    data = response.json()

    # Debug print: full JSON response
    # print("📦 Raw API response:")
    # print(json.dumps(data, indent=2))
    # print("----------------------------------------------------")

    if "items" not in data or not data["items"]:
        return None

    for item in data["items"]:
        title = item["snippet"]["title"]
        if date_str in title:
            video_id = item["id"]["videoId"]
            return {
                "date": date_str,
                "title": title,
                "url": f"https://www.youtube.com/watch?v={video_id}"
            }

    return None


def build_cfc_search_url(target_date: datetime.date):
    """Build YouTube Data API search URL for CFC Only By Grace Reflections"""
    date_str = target_date.strftime("%d %B %Y")  # e.g. "01 October 2025"
    query = f"{date_str} - Only By Grace Reflections"
    encoded_query = requests.utils.quote(query)

    url = (
        f"{BASE_URL}?part=snippet"
        f"&channelId={CFC_CHANNEL_ID}"
        f"&q={encoded_query}"
        f"&key={YOUTUBE_API_KEY}"
        f"&maxResults=5&type=video&order=date"
    )
    return url, date_str


def fetch_cfc_video_for_date(target_date: datetime.date):
    url, date_str = build_cfc_search_url(target_date)
    print(f"\n🔎 Fetching CFC video for {date_str}")
    print(f"Request URL: {url}\n")

    response = requests.get(url)
    data = response.json()

    if "items" not in data or not data["items"]:
        print(f"⚠️ No videos returned from API for query: {date_str} - Only By Grace Reflections")
        return None

    print(f"📹 Found {len(data['items'])} video(s) in search results:")
    for idx, item in enumerate(data["items"], 1):
        title = item["snippet"]["title"]
        video_id = item["id"]["videoId"]
        print(f"   {idx}. {title}")
        print(f"      Video ID: {video_id}")
        print(f"      Date check: '{date_str}' in title? {date_str in title}")
        print(f"      'Only By Grace Reflections' in title? {'Only By Grace Reflections' in title}")
    
    # Try multiple date formats and matching strategies
    day_no_zero = str(target_date.day)  # "8" instead of "08"
    date_formats = [
        date_str,  # "08 November 2025"
        target_date.strftime("%d %b %Y"),  # "08 Nov 2025" (abbreviated month)
        f"{day_no_zero} {target_date.strftime('%B %Y')}",  # "8 November 2025" (no leading zero)
        target_date.strftime("%d-%m-%Y"),  # "08-11-2025"
        target_date.strftime("%Y-%m-%d"),  # "2025-11-08"
    ]
    
    # First pass: Look for exact date match
    for item in data["items"]:
        title = item["snippet"]["title"]
        video_id = item["id"]["videoId"]
        
        # Check if it's an "Only By Grace Reflections" video
        if "Only By Grace Reflections" in title or "Only By Grace" in title:
            # Try matching with different date formats
            for date_format in date_formats:
                if date_format in title:
                    print(f"✅ Matched video with exact date: {title}")
                    return {
                        "date": date_str,
                        "title": title,
                        "url": f"https://www.youtube.com/watch?v={video_id}"
                    }
    
    # Second pass: If no exact match, return the first "Only By Grace" video (most recent)
    for item in data["items"]:
        title = item["snippet"]["title"]
        video_id = item["id"]["videoId"]
        
        if "Only By Grace Reflections" in title or "Only By Grace" in title:
            print(f"⚠️ No exact date match found, using most recent: {title}")
            return {
                "date": date_str,
                "title": title,
                "url": f"https://www.youtube.com/watch?v={video_id}"
            }

    print(f"⚠️ No matching CFC Only By Grace Reflections video found")
    return None


def save_to_firestore(video: dict, target_date: datetime.date, dry_run: bool = False):
    """Save video metadata into daily_scripture, create if missing."""
    doc_id = target_date.strftime("%Y-%m-%d")
    
    if dry_run:
        print(f"🧪 DRY RUN: Would save to document {doc_id}:")
        print(f"   theWordTodayUrl: {video['url']}")
        return
    
    doc_ref = db.collection("daily_scripture").document(doc_id)

    doc = doc_ref.get()
    if doc.exists:
        # ✅ Update existing document
        doc_ref.set({
            "theWordTodayUrl": video["url"]
        }, merge=True)
        print(f"🔄 Updated {doc_id} with theWordTodayUrl → {video['url']}")
    else:
        # 🆕 Create new document
        doc_ref.set({
            "title": "Daily Reading",
            "reference": doc_id,
            "theWordTodayUrl": video["url"]
        })
        print(f"🆕 Created {doc_id} with new Daily Reading + theWordTodayUrl")


def build_bo_search_url(target_date: datetime.date):
    """Build YouTube Data API search URL for Brother Bo FULLTANK with day of week"""
    day_name = target_date.strftime("%A").upper()  # e.g. "WEDNESDAY", "THURSDAY"
    query = f"FULLTANK {day_name}"
    encoded_query = requests.utils.quote(query)

    url = (
        f"{BASE_URL}?part=snippet"
        f"&channelId={BO_CHANNEL_ID}"
        f"&q={encoded_query}"
        f"&key={YOUTUBE_API_KEY}"
        f"&maxResults=5&type=video&order=date"
    )
    return url, day_name


def fetch_bo_video_for_date(target_date: datetime.date):
    """Fetch Brother Bo FULLTANK video for any day of the week"""
    url, day_name = build_bo_search_url(target_date)
    print(f"\n🔎 Fetching Brother Bo FULLTANK {day_name} video")
    print(f"Request URL: {url}\n")

    response = requests.get(url)
    data = response.json()

    if "items" not in data or not data["items"]:
        return None

    for item in data["items"]:
        title = item["snippet"]["title"]
        if f"FULLTANK {day_name}" in title.upper():
            video_id = item["id"]["videoId"]
            return {
                "title": title,
                "url": f"https://www.youtube.com/watch?v={video_id}"
            }

    return None


def save_cfc_to_firestore(video: dict, target_date: datetime.date, dry_run: bool = False):
    """Save CFC video metadata into daily_scripture, create if missing."""
    doc_id = target_date.strftime("%Y-%m-%d")
    
    if dry_run:
        print(f"🧪 DRY RUN: Would save to document {doc_id}:")
        print(f"   cfcOnlyByGraceReflectionsUrl: {video['url']}")
        return
    
    doc_ref = db.collection("daily_scripture").document(doc_id)

    doc = doc_ref.get()
    if doc.exists:
        # ✅ Update existing document
        doc_ref.set({
            "cfcOnlyByGraceReflectionsUrl": video["url"]
        }, merge=True)
        print(f"🔄 Updated {doc_id} with cfcOnlyByGraceReflectionsUrl → {video['url']}")
    else:
        # 🆕 Create new document
        doc_ref.set({
            "title": "Daily Reading",
            "reference": doc_id,
            "cfcOnlyByGraceReflectionsUrl": video["url"]
        })
        print(f"🆕 Created {doc_id} with new Daily Reading + cfcOnlyByGraceReflectionsUrl")


def save_bo_to_firestore(video: dict, target_date: datetime.date, dry_run: bool = False):
    """Save Brother Bo video metadata into daily_scripture, create if missing."""
    doc_id = target_date.strftime("%Y-%m-%d")
    
    if dry_run:
        print(f"🧪 DRY RUN: Would save to document {doc_id}:")
        print(f"   boSanchezFullTank: {video['url']}")
        return
    
    doc_ref = db.collection("daily_scripture").document(doc_id)

    doc = doc_ref.get()
    if doc.exists:
        # ✅ Update existing document
        doc_ref.set({
            "boSanchezFullTank": video["url"]
        }, merge=True)
        print(f"🔄 Updated {doc_id} with boSanchezFullTank → {video['url']}")
    else:
        # 🆕 Create new document
        doc_ref.set({
            "title": "Daily Reading",
            "reference": doc_id,
            "boSanchezFullTank": video["url"]
        })
        print(f"🆕 Created {doc_id} with new Daily Reading + boSanchezFullTank")


if __name__ == "__main__":
    import sys
    
    # Check for dry run flag
    # dry_run = "--dry-run"
    dry_run = DRY_RUN
    if dry_run:
        print("🧪 Running in DRY RUN mode - no data will be saved to Firestore\n")
    
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    # Hardcoded dates (uncomment to use specific dates)
    # target_date = datetime.date(2025, 11, 7)
    # for target in [target_date]:

    for target in [today, tomorrow]:
        # Fetch The Word Today video
        video = fetch_video_for_date(target)
        if video:
            save_to_firestore(video, target, dry_run)
        else:
            print(f"⚠️ No The Word Today video found for {target.strftime('%A, %B %d, %Y')}")
        
        # Fetch CFC Only By Grace Reflections video
        cfc_video = fetch_cfc_video_for_date(target)
        if cfc_video:
            save_cfc_to_firestore(cfc_video, target, dry_run)
        else:
            print(f"⚠️ No CFC Only By Grace Reflections video found for {target.strftime('%d %B %Y')}")
        
        # Fetch Brother Bo FULLTANK video
        bo_video = fetch_bo_video_for_date(target)
        if bo_video:
            save_bo_to_firestore(bo_video, target, dry_run)
        else:
            day_name = target.strftime("%A")
            print(f"⚠️ No FULLTANK {day_name.upper()} video found for {target.strftime('%A, %B %d, %Y')}")