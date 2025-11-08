"""
Google Cloud Function entry point for The Word Today service.
This function runs the daily scripture video fetching and Firestore update logic.
Completely self-contained - no external dependencies.
"""
import os
import json
import logging
import requests
import base64
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
_db_secondary = None


def _get_firebase_credentials(env_var_json, env_var_b64, env_var_path, app_name='default'):
    """Helper function to get Firebase credentials from various sources"""
    # Try to get credentials from environment variable (JSON string)
    firebase_creds_json = os.environ.get(env_var_json)
    
    # If not found, try base64 encoded version
    if not firebase_creds_json:
        firebase_creds_b64 = os.environ.get(env_var_b64)
        if firebase_creds_b64:
            firebase_creds_json = base64.b64decode(firebase_creds_b64).decode('utf-8')
            logger.info(f"✅ Decoded Firebase credentials from base64 for {app_name}")
    
    if firebase_creds_json:
        # Parse JSON string
        cred_dict = json.loads(firebase_creds_json)
        cred = credentials.Certificate(cred_dict)
        logger.info(f"✅ Initialized Firebase {app_name} from {env_var_json}")
        return cred
    else:
        # Try to get from file path (for local development)
        firebase_cred_path = os.environ.get(env_var_path)
        if firebase_cred_path and os.path.exists(firebase_cred_path):
            cred = credentials.Certificate(firebase_cred_path)
            logger.info(f"✅ Initialized Firebase {app_name} from file: {firebase_cred_path}")
            return cred
        else:
            # Use Application Default Credentials (for Cloud Functions)
            cred = credentials.ApplicationDefault()
            logger.info(f"✅ Initialized Firebase {app_name} using Application Default Credentials")
            return cred


def initialize_firebase(project='primary'):
    """
    Initialize Firebase Admin SDK from environment variable or Secret Manager.
    
    Args:
        project: 'primary' or 'secondary' - which Firebase project to initialize
    
    Returns:
        Firestore client instance
    """
    global _firebase_initialized, _db, _db_secondary
    
    if project == 'primary':
        if _db is not None:
            return _db
        
        try:
            cred = _get_firebase_credentials(
                'FIREBASE_CREDENTIALS_JSON',
                'FIREBASE_CREDENTIALS_JSON_B64',
                'FIREBASE_CRED',
                'primary'
            )
            
            # Initialize Firebase only if not already initialized
            try:
                app = firebase_admin.get_app('primary')
            except ValueError:
                firebase_admin.initialize_app(cred, name='primary')
            
            _db = firestore.client(app=firebase_admin.get_app('primary'))
            logger.info("✅ Primary Firebase initialized")
            return _db
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize primary Firebase: {str(e)}")
            raise
    
    elif project == 'secondary':
        if _db_secondary is not None:
            return _db_secondary
        
        try:
            # Try to get credentials from environment variables first
            cred = None
            try:
                cred = _get_firebase_credentials(
                    'FIREBASE_CREDENTIALS_JSON_SECONDARY',
                    'FIREBASE_CREDENTIALS_JSON_B64_SECONDARY',
                    'FIREBASE_CRED_SECONDARY',
                    'secondary'
                )
            except Exception as e:
                # If no credentials provided, try Application Default Credentials
                logger.info("ℹ️ No secondary Firebase credentials found, trying Application Default Credentials")
                cred = credentials.ApplicationDefault()
            
            # Initialize secondary Firebase app
            try:
                app = firebase_admin.get_app('secondary')
            except ValueError:
                firebase_admin.initialize_app(cred, name='secondary')
            
            _db_secondary = firestore.client(app=firebase_admin.get_app('secondary'))
            logger.info("✅ Secondary Firebase initialized")
            return _db_secondary
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize secondary Firebase: {str(e)}")
            raise
    else:
        raise ValueError(f"Invalid project: {project}. Must be 'primary' or 'secondary'")


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
    # Try multiple date formats that might appear in video titles
    day_no_zero = str(target_date.day)  # Without leading zero
    day_with_zero = target_date.strftime("%d")  # With leading zero
    month_name = target_date.strftime("%B")
    month_num = str(target_date.month)
    month_num_zero = target_date.strftime("%m")
    year = str(target_date.year)
    
    date_formats = [
        target_date.strftime("%d %B %Y"),  # e.g. "01 October 2025"
        f"{day_no_zero} {month_name} {year}",  # e.g. "1 October 2025" (no leading zero)
        target_date.strftime("%B %d, %Y"),  # e.g. "October 01, 2025"
        f"{month_name} {day_no_zero}, {year}",  # e.g. "October 1, 2025" (no leading zero)
        target_date.strftime("%d/%m/%Y"),  # e.g. "01/10/2025"
        f"{day_no_zero}/{month_num}/{year}",  # e.g. "1/10/2025"
    ]
    
    # Primary search query using the first format
    date_str = date_formats[0]
    query = f"{date_str} - Only By Grace Reflections"
    encoded_query = requests.utils.quote(query)
    
    url = (
        f"{BASE_URL}?part=snippet"
        f"&channelId={CFC_CHANNEL_ID}"
        f"&q={encoded_query}"
        f"&key={YOUTUBE_API_KEY}"
        f"&maxResults=10&type=video&order=date"
    )
    
    logger.info(f"🔎 Fetching CFC Only By Grace video for {date_str}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        video_found = False
        
        if "items" in data and data["items"]:
            # Log all found titles for debugging
            logger.info(f"📋 Found {len(data['items'])} video(s) in search results:")
            for item in data["items"]:
                title = item["snippet"]["title"]
                logger.info(f"   - {title}")
            
            # Try to match with any of the date formats
            for item in data["items"]:
                title = item["snippet"]["title"]
                # Check if "Only By Grace Reflections" is in the title
                if "Only By Grace Reflections" in title:
                    # Check if any date format matches
                    date_matched = False
                    for fmt in date_formats:
                        if fmt in title:
                            date_matched = True
                            logger.info(f"✅ Matched video with date format: {fmt}")
                            break
                    
                    # If no exact date match, check if title contains the date components
                    if not date_matched:
                        # Try matching date components separately as fallback
                        if month_name in title and year in title:
                            logger.info(f"✅ Matched video by date components (month: {month_name}, year: {year})")
                            date_matched = True
                    
                    if date_matched:
                        video_id = item["id"]["videoId"]
                        logger.info(f"✅ Found matching CFC video: {title}")
                        video_found = {
                            "date": date_str,
                            "title": title,
                            "url": f"https://www.youtube.com/watch?v={video_id}"
                        }
                        break
        else:
            logger.warning(f"⚠️ No search results returned for CFC video query")
        
        if video_found:
            return video_found
        
        logger.warning(f"⚠️ No CFC video found matching date formats and 'Only By Grace Reflections'")
        logger.info(f"🔄 Trying fallback search with broader query...")
        
        # Fallback: Try searching without date in query, but filter by date in results
        fallback_query = "Only By Grace Reflections"
        encoded_query = requests.utils.quote(fallback_query)
        fallback_url = (
            f"{BASE_URL}?part=snippet"
            f"&channelId={CFC_CHANNEL_ID}"
            f"&q={encoded_query}"
            f"&key={YOUTUBE_API_KEY}"
            f"&maxResults=20&type=video&order=date"
        )
        
        fallback_response = requests.get(fallback_url, timeout=30)
        fallback_response.raise_for_status()
        fallback_data = fallback_response.json()
        
        if "items" in fallback_data and fallback_data["items"]:
            logger.info(f"📋 Fallback search found {len(fallback_data['items'])} video(s):")
            for item in fallback_data["items"]:
                title = item["snippet"]["title"]
                logger.info(f"   - {title}")
                
                # Check if "Only By Grace Reflections" is in the title
                if "Only By Grace Reflections" in title:
                    # Try matching with any date format
                    for fmt in date_formats:
                        if fmt in title:
                            video_id = item["id"]["videoId"]
                            logger.info(f"✅ Found matching CFC video via fallback search: {title}")
                            return {
                                "date": date_str,
                                "title": title,
                                "url": f"https://www.youtube.com/watch?v={video_id}"
                            }
                    
                    # Try matching by date components
                    if month_name in title and year in title:
                        video_id = item["id"]["videoId"]
                        logger.info(f"✅ Found matching CFC video via fallback search (by components): {title}")
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


def save_to_firestore(video: dict, target_date: date, field_name: str, dry_run: bool = False, project='primary'):
    """
    Save video URL to Firestore
    
    Args:
        video: Video dictionary with url, title, etc.
        target_date: Target date for the video
        field_name: Field name to save (e.g., 'theWordTodayUrl', 'cfcOnlyByGraceReflectionsUrl')
        dry_run: If True, don't actually save
        project: 'primary' or 'secondary' - which Firebase project to write to
    """
    db = initialize_firebase(project)
    
    doc_id = target_date.strftime("%Y-%m-%d")
    
    if dry_run:
        logger.info(f"🧪 DRY RUN [{project}]: Would save to document {doc_id}:")
        logger.info(f"   {field_name}: {video['url']}")
        return
    
    try:
        doc_ref = db.collection("daily_scripture").document(doc_id)
        doc = doc_ref.get()
        
        if doc.exists:
            doc_ref.set({field_name: video["url"]}, merge=True)
            logger.info(f"🔄 Updated {doc_id} [{project}] with {field_name} → {video['url']}")
        else:
            doc_ref.set({
                "title": "Daily Reading",
                "reference": doc_id,
                field_name: video["url"]
            })
            logger.info(f"🆕 Created {doc_id} [{project}] with new Daily Reading + {field_name}")
    except Exception as e:
        logger.error(f"❌ Error saving to Firestore [{project}]: {str(e)}")
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
        
        # Initialize Firebase (primary)
        initialize_firebase('primary')
        
        # Initialize secondary Firebase if credentials are provided OR if using Application Default Credentials
        # Check if secondary project ID is specified (indicates we should try secondary)
        secondary_project_id = os.environ.get('FIREBASE_PROJECT_ID_SECONDARY')
        has_secondary_creds = (
            os.environ.get('FIREBASE_CREDENTIALS_JSON_SECONDARY') or
            os.environ.get('FIREBASE_CREDENTIALS_JSON_B64_SECONDARY') or
            (os.environ.get('FIREBASE_CRED_SECONDARY') and os.path.exists(os.environ.get('FIREBASE_CRED_SECONDARY')))
        )
        
        # Try to initialize secondary Firebase if credentials provided OR if project ID specified
        has_secondary = False
        if has_secondary_creds or secondary_project_id:
            try:
                initialize_firebase('secondary')
                has_secondary = True
                if has_secondary_creds:
                    logger.info("✅ Secondary Firebase credentials detected - will write to both projects")
                else:
                    logger.info("✅ Secondary Firebase initialized using Application Default Credentials - will write to both projects")
            except Exception as e:
                logger.warning(f"⚠️ Secondary Firebase initialization failed (will continue with primary only): {str(e)}")
                has_secondary = False
        
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
            'errors': [],
            'firebase_projects': ['primary'] + (['secondary'] if has_secondary else [])
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
                    # Save to primary Firebase
                    save_to_firestore(video, target_date, 'theWordTodayUrl', dry_run, 'primary')
                    # Save to secondary Firebase if available
                    if has_secondary:
                        try:
                            save_to_firestore(video, target_date, 'theWordTodayUrl', dry_run, 'secondary')
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to save to secondary Firebase: {str(e)}")
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
                    # Save to primary Firebase
                    save_to_firestore(cfc_video, target_date, 'cfcOnlyByGraceReflectionsUrl', dry_run, 'primary')
                    # Save to secondary Firebase if available
                    if has_secondary:
                        try:
                            save_to_firestore(cfc_video, target_date, 'cfcOnlyByGraceReflectionsUrl', dry_run, 'secondary')
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to save to secondary Firebase: {str(e)}")
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
                    # Save to primary Firebase
                    save_to_firestore(bo_video, target_date, 'boSanchezFullTank', dry_run, 'primary')
                    # Save to secondary Firebase if available
                    if has_secondary:
                        try:
                            save_to_firestore(bo_video, target_date, 'boSanchezFullTank', dry_run, 'secondary')
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to save to secondary Firebase: {str(e)}")
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
