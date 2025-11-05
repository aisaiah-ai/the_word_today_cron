"""
Google Cloud Function entry point for The Word Today service.
This function runs the daily scripture video fetching and Firestore update logic.
Completely self-contained - no external dependencies.
"""
import os
import json
import logging
import requests
from datetime import datetime, date, timedelta
import firebase_admin
from firebase_admin import credentials, firestore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment variables
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY', '')
CHANNEL_ID = os.environ.get('CHANNEL_ID', 'UC9gpFF4p56T4wQtinfAT3Eg')  # The Word Today TV
CFC_CHANNEL_ID = os.environ.get('CFC_CHANNEL_ID', 'UCVb6g46-SKkTLTHTF-wO8Kw')  # Couples for Christ Media
BO_CHANNEL_ID = os.environ.get('BO_CHANNEL_ID', 'UCFoHFFBWDwxbpa1bYH736RA')  # Brother Bo Sanchez
BASE_URL = "https://www.googleapis.com/youtube/v3/search"

# Firebase initialization (lazy - only once)
_firebase_initialized = False
_db = None


def initialize_firebase():
    """Initialize Firebase Admin SDK from environment variable or Secret Manager"""
    global _firebase_initialized, _db
    
    if _firebase_initialized:
        return _db
    
    try:
        # Try to get credentials from environment variable (JSON string)
        firebase_creds_json = os.environ.get('FIREBASE_CREDENTIALS_JSON')
        
        if firebase_creds_json:
            # Parse JSON string
            cred_dict = json.loads(firebase_creds_json)
            cred = credentials.Certificate(cred_dict)
            logger.info("✅ Initialized Firebase from FIREBASE_CREDENTIALS_JSON")
        else:
            # Try to get from file path (for local development)
            firebase_cred_path = os.environ.get('FIREBASE_CRED')
            if firebase_cred_path and os.path.exists(firebase_cred_path):
                cred = credentials.Certificate(firebase_cred_path)
                logger.info(f"✅ Initialized Firebase from file: {firebase_cred_path}")
            else:
                # Use Application Default Credentials (for Cloud Functions)
                cred = credentials.ApplicationDefault()
                logger.info("✅ Initialized Firebase using Application Default Credentials")
        
        # Initialize Firebase only if not already initialized
        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app(cred)
        
        _db = firestore.client()
        _firebase_initialized = True
        return _db
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Firebase: {str(e)}")
        raise


def build_search_url(target_date: date, channel_id: str, query_suffix: str):
    """Build YouTube Data API search URL with date string"""
    date_str = target_date.strftime("%A, %B %d, %Y").replace(f" 0{target_date.day},", f" {target_date.day},")
    query = f"{query_suffix} {date_str}"
    encoded_query = requests.utils.quote(query)
    
    url = (
        f"{BASE_URL}?part=snippet"
        f"&channelId={channel_id}"
        f"&q={encoded_query}"
        f"&key={YOUTUBE_API_KEY}"
        f"&maxResults=5&type=video&order=date"
    )
    return url, date_str


def fetch_video_for_date(target_date: date):
    """Fetch The Word Today video for a specific date"""
    date_str = target_date.strftime("%A, %B %d, %Y").replace(f" 0{target_date.day},", f" {target_date.day},")
    query = f"Today's Catholic Mass Readings & Gospel Reflection {date_str}"
    encoded_query = requests.utils.quote(query)
    
    url = (
        f"{BASE_URL}?part=snippet"
        f"&channelId={CHANNEL_ID}"
        f"&q={encoded_query}"
        f"&key={YOUTUBE_API_KEY}"
        f"&maxResults=5&type=video&order=date"
    )
    
    logger.info(f"🔎 Fetching The Word Today video for {date_str}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
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
    except Exception as e:
        logger.error(f"❌ Error fetching The Word Today video: {str(e)}")
    
    return None


def fetch_cfc_video_for_date(target_date: date):
    """Fetch CFC Only By Grace Reflections video for a specific date"""
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
    
    logger.info(f"🔎 Fetching CFC Only By Grace video for {date_str}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "items" not in data or not data["items"]:
            return None
        
        for item in data["items"]:
            title = item["snippet"]["title"]
            if date_str in title and "Only By Grace Reflections" in title:
                video_id = item["id"]["videoId"]
                return {
                    "date": date_str,
                    "title": title,
                    "url": f"https://www.youtube.com/watch?v={video_id}"
                }
    except Exception as e:
        logger.error(f"❌ Error fetching CFC video: {str(e)}")
    
    return None


def fetch_bo_video_for_date(target_date: date):
    """Fetch Brother Bo FULLTANK video for a specific date"""
    day_name = target_date.strftime("%A").upper()  # e.g. "WEDNESDAY"
    query = f"FULLTANK {day_name}"
    encoded_query = requests.utils.quote(query)
    
    url = (
        f"{BASE_URL}?part=snippet"
        f"&channelId={BO_CHANNEL_ID}"
        f"&q={encoded_query}"
        f"&key={YOUTUBE_API_KEY}"
        f"&maxResults=5&type=video&order=date"
    )
    
    logger.info(f"🔎 Fetching Brother Bo FULLTANK {day_name} video")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
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
    except Exception as e:
        logger.error(f"❌ Error fetching Bo Sanchez video: {str(e)}")
    
    return None


def save_to_firestore(video: dict, target_date: date, field_name: str, dry_run: bool = False):
    """Save video URL to Firestore"""
    if not _firebase_initialized:
        initialize_firebase()
    
    doc_id = target_date.strftime("%Y-%m-%d")
    
    if dry_run:
        logger.info(f"🧪 DRY RUN: Would save to document {doc_id}:")
        logger.info(f"   {field_name}: {video['url']}")
        return
    
    try:
        doc_ref = _db.collection("daily_scripture").document(doc_id)
        doc = doc_ref.get()
        
        if doc.exists:
            doc_ref.set({field_name: video["url"]}, merge=True)
            logger.info(f"🔄 Updated {doc_id} with {field_name} → {video['url']}")
        else:
            doc_ref.set({
                "title": "Daily Reading",
                "reference": doc_id,
                field_name: video["url"]
            })
            logger.info(f"🆕 Created {doc_id} with new Daily Reading + {field_name}")
    except Exception as e:
        logger.error(f"❌ Error saving to Firestore: {str(e)}")
        raise


def the_word_today_cron(request):
    """
    Cloud Function entry point that runs the daily scripture video service.
    
    Args:
        request: Flask request object (from Functions Framework)
    
    Returns:
        tuple: (response dict, status code)
    """
    try:
        logger.info("🚀 Starting The Word Today cron job")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        
        # Validate required environment variables
        if not YOUTUBE_API_KEY:
            raise ValueError("YOUTUBE_API_KEY environment variable is not set")
        
        # Initialize Firebase
        initialize_firebase()
        
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        dry_run = os.environ.get('DRY_RUN', '').lower() == 'true'
        
        if dry_run:
            logger.info("🧪 Running in DRY RUN mode - no data will be saved to Firestore")
        
        results = {
            'status': 'success',
            'date': today.isoformat(),
            'processed_dates': [],
            'processed_videos': [],
            'errors': []
        }
        
        # Process today and tomorrow
        for target_date in [today, tomorrow]:
            date_str = target_date.strftime('%Y-%m-%d')
            logger.info(f"📅 Processing date: {date_str}")
            results['processed_dates'].append(date_str)
            
            # Fetch The Word Today video
            try:
                video = fetch_video_for_date(target_date)
                if video:
                    save_to_firestore(video, target_date, 'theWordTodayUrl', dry_run)
                    logger.info(f"✅ The Word Today video saved for {date_str}")
                    results['processed_videos'].append(f"The Word Today - {date_str}")
                else:
                    logger.warning(f"⚠️ No The Word Today video found for {target_date.strftime('%A, %B %d, %Y')}")
                    results['errors'].append(f"No The Word Today video for {date_str}")
            except Exception as e:
                logger.error(f"❌ Error processing The Word Today for {date_str}: {str(e)}")
                results['errors'].append(f"The Word Today error for {date_str}: {str(e)}")
            
            # Fetch CFC Only By Grace Reflections video
            try:
                cfc_video = fetch_cfc_video_for_date(target_date)
                if cfc_video:
                    save_to_firestore(cfc_video, target_date, 'cfcOnlyByGraceReflectionsUrl', dry_run)
                    logger.info(f"✅ CFC Only By Grace video saved for {date_str}")
                    results['processed_videos'].append(f"CFC Only By Grace - {date_str}")
                else:
                    logger.warning(f"⚠️ No CFC Only By Grace Reflections video found for {target_date.strftime('%d %B %Y')}")
                    results['errors'].append(f"No CFC video for {date_str}")
            except Exception as e:
                logger.error(f"❌ Error processing CFC video for {date_str}: {str(e)}")
                results['errors'].append(f"CFC video error for {date_str}: {str(e)}")
            
            # Fetch Brother Bo FULLTANK video
            try:
                bo_video = fetch_bo_video_for_date(target_date)
                if bo_video:
                    save_to_firestore(bo_video, target_date, 'boSanchezFullTank', dry_run)
                    logger.info(f"✅ Brother Bo FULLTANK video saved for {date_str}")
                    results['processed_videos'].append(f"Brother Bo FULLTANK - {date_str}")
                else:
                    day_name = target_date.strftime("%A")
                    logger.warning(f"⚠️ No FULLTANK {day_name.upper()} video found for {target_date.strftime('%A, %B %d, %Y')}")
                    results['errors'].append(f"No Bo Sanchez video for {date_str}")
            except Exception as e:
                logger.error(f"❌ Error processing Bo Sanchez video for {date_str}: {str(e)}")
                results['errors'].append(f"Bo Sanchez video error for {date_str}: {str(e)}")
        
        logger.info("✅ Cron job completed successfully")
        logger.info(f"Results: {json.dumps(results, indent=2)}")
        
        return {
            'statusCode': 200,
            'body': results
        }, 200
        
    except Exception as e:
        logger.error(f"❌ Fatal error in cron job: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': {
                'status': 'error',
                'message': str(e)
            }
        }, 500
