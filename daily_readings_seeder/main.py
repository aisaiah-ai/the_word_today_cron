"""
Firebase Daily Readings Seeder - Cloud Function
This function seeds daily scripture readings with USCCB links and public domain text.
Runs monthly on the 15th to seed days 1-30 of the next month.
"""
import os
import json
import logging
import requests
import base64
from datetime import datetime, date, timedelta
from typing import Dict, Optional, List
import firebase_admin
from firebase_admin import credentials, firestore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        
        # If not found, try base64 encoded version
        if not firebase_creds_json:
            firebase_creds_b64 = os.environ.get('FIREBASE_CREDENTIALS_JSON_B64')
            if firebase_creds_b64:
                firebase_creds_json = base64.b64decode(firebase_creds_b64).decode('utf-8')
                logger.info("✅ Decoded Firebase credentials from base64")
        
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


def generate_usccb_url(target_date: date) -> str:
    """Generate USCCB daily readings URL"""
    month = str(target_date.month).zfill(2)
    day = str(target_date.day).zfill(2)
    year = target_date.year
    return f"https://bible.usccb.org/bible/readings/{month}/{day}/{year}.cfm"


def parse_bible_reference(ref: str) -> Dict:
    """Parse Bible reference like 'Heb 9:15, 24-28' into structured data"""
    # Book abbreviation mapping
    book_map = {
        'Heb': 'Hebrews', 'Ps': 'Psalms', 'Jn': 'John', 'Mk': 'Mark',
        'Mt': 'Matthew', 'Lk': 'Luke', '1Jn': '1 John', '2Jn': '2 John',
        'Acts': 'Acts', 'Rom': 'Romans', '1Cor': '1 Corinthians',
        '2Cor': '2 Corinthians', 'Gal': 'Galatians', 'Eph': 'Ephesians',
        'Phil': 'Philippians', 'Col': 'Colossians', '1Thess': '1 Thessalonians',
        '2Thess': '2 Thessalonians', '1Tim': '1 Timothy', '2Tim': '2 Timothy',
        'Titus': 'Titus', 'Phlm': 'Philemon', 'Jas': 'James',
        '1Pet': '1 Peter', '2Pet': '2 Peter', 'Rev': 'Revelation',
        'Gen': 'Genesis', 'Ex': 'Exodus', 'Lev': 'Leviticus', 'Num': 'Numbers',
        'Deut': 'Deuteronomy', 'Josh': 'Joshua', 'Judg': 'Judges', 'Ruth': 'Ruth',
        '1Sam': '1 Samuel', '2Sam': '2 Samuel', '1Kgs': '1 Kings', '2Kgs': '2 Kings',
        '1Chr': '1 Chronicles', '2Chr': '2 Chronicles', 'Ezra': 'Ezra',
        'Neh': 'Nehemiah', 'Tob': 'Tobit', 'Jdt': 'Judith', 'Esth': 'Esther',
        '1Macc': '1 Maccabees', '2Macc': '2 Maccabees', 'Job': 'Job',
        'Prov': 'Proverbs', 'Eccl': 'Ecclesiastes', 'Song': 'Song of Songs',
        'Wis': 'Wisdom', 'Sir': 'Sirach', 'Is': 'Isaiah', 'Jer': 'Jeremiah',
        'Lam': 'Lamentations', 'Bar': 'Baruch', 'Ezek': 'Ezekiel', 'Dan': 'Daniel',
        'Hos': 'Hosea', 'Joel': 'Joel', 'Amos': 'Amos', 'Obad': 'Obadiah',
        'Jonah': 'Jonah', 'Mic': 'Micah', 'Nah': 'Nahum', 'Hab': 'Habakkuk',
        'Zeph': 'Zephaniah', 'Hag': 'Haggai', 'Zech': 'Zechariah', 'Mal': 'Malachi'
    }
    
    # Parse reference pattern: "Heb 9:15, 24-28" or "Ps 98:1, 2-3ab"
    import re
    match = re.match(r'(\w+)\s+(\d+):(.+)', ref.strip())
    if not match:
        return {'book': ref, 'chapter': 0, 'verses': []}
    
    abbrev = match.group(1)
    book = book_map.get(abbrev, abbrev)
    chapter = int(match.group(2))
    verses_str = match.group(3)
    
    # Parse verses: "15, 24-28" -> [15, 24, 25, 26, 27, 28]
    verses = []
    for part in verses_str.split(','):
        part = part.strip()
        if '-' in part:
            # Handle ranges like "24-28" or "2-3ab"
            range_match = re.match(r'(\d+)([a-z]*)-(\d+)([a-z]*)', part)
            if range_match:
                start = int(range_match.group(1))
                end = int(range_match.group(3))
                for v in range(start, end + 1):
                    verses.append(v)
        else:
            # Single verse
            verse_match = re.match(r'(\d+)([a-z]*)', part)
            if verse_match:
                verses.append(int(verse_match.group(1)))
    
    return {
        'book': book,
        'chapter': chapter,
        'verses': verses,
        'reference': ref
    }


def fetch_usccb_reading_data(target_date: date) -> Optional[Dict]:
    """
    Fetch USCCB reading references (NOT full text due to licensing)
    Returns structured data with references only
    
    Note: This is a placeholder implementation. In production, you would:
    1. Fetch the USCCB HTML page
    2. Parse HTML using BeautifulSoup to extract references
    3. Extract reading titles and Bible references
    4. Return structured data without full text content
    """
    url = generate_usccb_url(target_date)
    logger.info(f"🔎 Fetching USCCB reading data from {url}")
    
    try:
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; Daily Readings Seeder/1.0)'
        })
        response.raise_for_status()
        
        # TODO: Parse HTML to extract references
        # For now, log that parsing is needed
        # In production, use BeautifulSoup to parse HTML structure:
        # from bs4 import BeautifulSoup
        # soup = BeautifulSoup(response.text, 'html.parser')
        # reading1_ref = extract_reference_from_html(soup, 'reading1')
        # etc.
        
        logger.warning("⚠️  USCCB HTML parsing not yet implemented - using placeholder")
        
        # Placeholder structure - actual implementation would parse HTML
        return {
            'title': f"Readings for {target_date.strftime('%A, %B %d, %Y')}",
            'url': url,
            'reading1': {
                'id': f"{int(target_date.strftime('%Y%m%d'))}-reading1",
                'title': 'Reading 1',
                'reference': 'TBD'  # Would be parsed from HTML
            },
            'responsorialPsalm': {
                'id': f"{int(target_date.strftime('%Y%m%d'))}-psalm",
                'title': 'Responsorial Psalm',
                'reference': 'TBD'  # Would be parsed from HTML
            },
            'gospel': {
                'id': f"{int(target_date.strftime('%Y%m%d'))}-gospel",
                'title': 'Gospel',
                'reference': 'TBD'  # Would be parsed from HTML
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching USCCB data: {str(e)}")
        return None


def fetch_public_scripture_text(reference: str) -> str:
    """
    Fetch public domain scripture text for a given reference
    Uses public domain sources like World English Bible or KJV
    """
    if not reference or reference == 'TBD':
        return ""
    
    parsed = parse_bible_reference(reference)
    
    # For now, return placeholder - would need API integration
    # Options:
    # 1. World English Bible API
    # 2. Local Bible text files
    # 3. Bible Gateway API (check licensing)
    
    logger.info(f"📖 Fetching scripture text for {reference}")
    
    # Placeholder - actual implementation would fetch from public domain source
    return f"[Public domain scripture text for {reference}]"


def get_feast_for_date(target_date: date) -> Optional[Dict]:
    """Get feast information for a given date"""
    if not _firebase_initialized:
        initialize_firebase()
    
    try:
        feasts_ref = _db.collection('feasts')
        # Query by date (would need to store date as timestamp)
        # For now, return None - would need proper feast data structure
        return None
    except Exception as e:
        logger.warning(f"⚠️  Could not fetch feast data: {str(e)}")
        return None


def generate_id() -> str:
    """Generate a unique ID"""
    return f"{int(datetime.now().timestamp() * 1000)}-{str(hash(datetime.now().isoformat()))[-9:]}"


def seed_daily_reading(target_date: date, dry_run: bool = False) -> Dict:
    """
    Seed a single day's reading data into Firestore
    
    Args:
        target_date: Date to seed
        dry_run: If True, don't write to Firestore
    
    Returns:
        Dict with seeding results
    """
    if not _firebase_initialized:
        initialize_firebase()
    
    doc_id = target_date.strftime("%Y-%m-%d")
    logger.info(f"📅 Seeding daily reading for {doc_id}")
    
    # Get USCCB reading data
    usccb_reading = fetch_usccb_reading_data(target_date)
    
    # Get feast data
    feast = get_feast_for_date(target_date)
    
    # Get public domain scripture text (use gospel reference)
    gospel_ref = usccb_reading.get('gospel', {}).get('reference', 'John 3:16') if usccb_reading else 'John 3:16'
    scripture_text = fetch_public_scripture_text(gospel_ref)
    
    # Construct daily scripture document
    daily_scripture_data = {
        'id': doc_id,
        'title': 'Daily Scripture',
        'reference': gospel_ref,
        'body': scripture_text,
        'updatedAt': firestore.SERVER_TIMESTAMP,
    }
    
    # Add USCCB reading data (references only, no full text)
    if usccb_reading:
        daily_scripture_data['usccbReading'] = {
            'id': generate_id(),
            'date': datetime.combine(target_date, datetime.min.time()),
            'title': usccb_reading.get('title', ''),
            'url': usccb_reading.get('url', ''),
            'reading1': {
                'id': generate_id(),
                'title': usccb_reading.get('reading1', {}).get('title', 'Reading 1'),
                'reference': usccb_reading.get('reading1', {}).get('reference', '')
            },
            'responsorialPsalm': {
                'id': generate_id(),
                'title': usccb_reading.get('responsorialPsalm', {}).get('title', 'Responsorial Psalm'),
                'reference': usccb_reading.get('responsorialPsalm', {}).get('reference', '')
            },
            'gospel': {
                'id': generate_id(),
                'title': usccb_reading.get('gospel', {}).get('title', 'Gospel'),
                'reference': usccb_reading.get('gospel', {}).get('reference', '')
            }
        }
        
        if 'reading2' in usccb_reading:
            daily_scripture_data['usccbReading']['reading2'] = {
                'id': generate_id(),
                'title': usccb_reading['reading2'].get('title', 'Reading 2'),
                'reference': usccb_reading['reading2'].get('reference', '')
            }
        
        if 'alleluia' in usccb_reading:
            daily_scripture_data['usccbReading']['alleluia'] = {
                'id': generate_id(),
                'title': usccb_reading['alleluia'].get('title', 'Alleluia'),
                'reference': usccb_reading['alleluia'].get('reference', '')
            }
    
    # Add feast data
    if feast:
        daily_scripture_data['feast'] = feast.get('name')
        daily_scripture_data['feastType'] = feast.get('type')
    
    if dry_run:
        logger.info(f"🧪 DRY RUN: Would seed document {doc_id}")
        logger.info(f"   Data: {json.dumps(daily_scripture_data, indent=2, default=str)}")
        return {'status': 'dry_run', 'doc_id': doc_id}
    
    try:
        doc_ref = _db.collection('daily_scripture').document(doc_id)
        doc_ref.set(daily_scripture_data, merge=True)
        logger.info(f"✅ Seeded daily reading for {doc_id}")
        return {'status': 'success', 'doc_id': doc_id}
    except Exception as e:
        logger.error(f"❌ Error seeding {doc_id}: {str(e)}")
        return {'status': 'error', 'doc_id': doc_id, 'error': str(e)}


def seed_daily_readings_cron(request):
    """
    Cloud Function entry point for seeding daily readings
    Runs monthly on the 15th to seed days 1-30 of the next month
    
    Args:
        request: Flask request object (from Functions Framework)
    
    Returns:
        tuple: (response dict, status code)
    """
    try:
        logger.info("🚀 Starting Daily Readings Seeder cron job")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        
        # Initialize Firebase
        initialize_firebase()
        
        # Get parameters from request or calculate next month's dates
        today = date.today()
        
        # Calculate next month
        if today.month == 12:
            next_month = 1
            next_year = today.year + 1
        else:
            next_month = today.month + 1
            next_year = today.year
        
        # Start date is the 1st of next month
        start_date = date(next_year, next_month, 1)
        
        # Seed days 1-30 of next month (handles months with 28-31 days)
        # We'll seed up to 30 days, but the actual end depends on the month
        days_to_seed = 30
        
        dry_run = os.environ.get('DRY_RUN', '').lower() == 'true'
        
        if dry_run:
            logger.info("🧪 Running in DRY RUN mode - no data will be saved to Firestore")
        
        logger.info(f"📅 Seeding days 1-30 of next month: {start_date.strftime('%B %Y')}")
        
        results = {
            'status': 'success',
            'start_date': start_date.isoformat(),
            'target_month': f"{next_year}-{next_month:02d}",
            'days_to_seed': days_to_seed,
            'processed_dates': [],
            'successful': [],
            'errors': []
        }
        
        # Seed readings for days 1-30 of next month
        for i in range(days_to_seed):
            target_date = start_date + timedelta(days=i)
            
            # Skip if we've gone past the end of the month (for months with < 30 days)
            if target_date.month != next_month:
                logger.info(f"⏭️  Skipping {target_date.strftime('%Y-%m-%d')} - past end of target month")
                break
            
            date_str = target_date.strftime('%Y-%m-%d')
            logger.info(f"📅 Processing date: {date_str}")
            
            result = seed_daily_reading(target_date, dry_run)
            
            if result['status'] == 'success':
                results['successful'].append(date_str)
                logger.info(f"✅ Successfully seeded {date_str}")
            elif result['status'] == 'dry_run':
                results['successful'].append(date_str)
                logger.info(f"🧪 Dry run completed for {date_str}")
            else:
                results['errors'].append({
                    'date': date_str,
                    'error': result.get('error', 'Unknown error')
                })
                logger.error(f"❌ Failed to seed {date_str}: {result.get('error')}")
            
            results['processed_dates'].append(date_str)
        
        logger.info("✅ Daily readings seeding completed")
        logger.info(f"Results: {json.dumps(results, indent=2, default=str)}")
        
        return {
            'statusCode': 200,
            'body': results
        }, 200
        
    except Exception as e:
        logger.error(f"❌ Fatal error in daily readings seeder: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': {
                'status': 'error',
                'message': str(e)
            }
        }, 500


if __name__ == '__main__':
    # For local testing
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/', methods=['GET', 'POST'])
    def test():
        class MockRequest:
            def __init__(self):
                self.method = 'GET'
                self.args = {}
        
        return seed_daily_readings_cron(MockRequest())
    
    app.run(port=8080, debug=True)

