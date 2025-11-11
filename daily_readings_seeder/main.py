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
import re
from datetime import datetime, date, timedelta
from typing import Dict, Optional, List
import firebase_admin
from firebase_admin import credentials, firestore
from bs4 import BeautifulSoup

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
    Parses HTML to extract actual Bible references
    """
    url = generate_usccb_url(target_date)
    logger.info(f"🔎 Fetching USCCB reading data from {url}")
    
    try:
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; Daily Readings Seeder/1.0)'
        })
        response.raise_for_status()
        
        # Parse HTML to extract references
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Initialize result structure
        result = {
            'title': f"Readings for {target_date.strftime('%A, %B %d, %Y')}",
            'url': url,
            'reading1': {'title': 'Reading 1', 'reference': ''},
            'responsorialPsalm': {'title': 'Responsorial Psalm', 'reference': ''},
            'gospel': {'title': 'Gospel', 'reference': ''}
        }
        
        # USCCB page structure: Look for reading references in various formats
        # Common patterns: "Reading 1", "Responsorial Psalm", "Gospel"
        # References are usually in <p> tags or <div> tags with class names
        
        # Try to find reading references in the HTML
        # Look for common patterns like "Rom 9:1-5" or "Luke 14:1-6"
        bible_ref_pattern = r'\b([1-3]?\s*(?:[A-Z][a-z]+|Cor|Thess|Tim|Jn|Jn|Mk|Mt|Lk|Ps|Rom|Heb|Gal|Eph|Phil|Col|Jas|Pet|Rev|Gen|Ex|Lev|Num|Deut|Josh|Judg|Ruth|Sam|Kgs|Chr|Ezra|Neh|Esth|Job|Prov|Eccl|Song|Is|Jer|Lam|Ezek|Dan|Hos|Joel|Amos|Obad|Jonah|Mic|Nah|Hab|Zeph|Hag|Zech|Mal))\s+\d+:\d+(?:-\d+)?(?:\s*,\s*\d+)?(?:\s*-\s*\d+[a-z]*)?'
        
        # Find all potential Bible references in the page
        page_text = soup.get_text()
        all_refs = re.findall(bible_ref_pattern, page_text, re.IGNORECASE)
        
        # Look for specific sections
        # Reading 1 is usually first, Responsorial Psalm second, Gospel last
        
        # Try to find reading sections by looking for headings
        reading1_ref = ''
        psalm_ref = ''
        gospel_ref = ''
        
        # Look for "Reading 1" or "First Reading" section
        reading1_section = soup.find(string=re.compile(r'Reading\s+1|First\s+Reading', re.I))
        if reading1_section:
            parent = reading1_section.find_parent()
            if parent:
                text = parent.get_text()
                refs = re.findall(bible_ref_pattern, text, re.IGNORECASE)
                if refs:
                    reading1_ref = refs[0]
        
        # Look for "Responsorial Psalm" or "Psalm" section
        psalm_section = soup.find(string=re.compile(r'Responsorial\s+Psalm|Psalm\s+Response', re.I))
        if psalm_section:
            parent = psalm_section.find_parent()
            if parent:
                text = parent.get_text()
                refs = re.findall(bible_ref_pattern, text, re.IGNORECASE)
                if refs:
                    psalm_ref = refs[0]
        
        # Look for "Gospel" section
        gospel_section = soup.find(string=re.compile(r'Gospel', re.I))
        if gospel_section:
            parent = gospel_section.find_parent()
            if parent:
                text = parent.get_text()
                refs = re.findall(bible_ref_pattern, text, re.IGNORECASE)
                if refs:
                    gospel_ref = refs[0]
        
        # Fallback: if we found references but couldn't match to sections, assign in order
        if not reading1_ref and not psalm_ref and not gospel_ref and all_refs:
            # Assign first reference to reading1, look for Psalm, last to gospel
            reading1_ref = all_refs[0] if len(all_refs) > 0 else ''
            # Look for Psalm reference (usually contains "Ps" or "Psalm")
            psalm_candidates = [r for r in all_refs if 'ps' in r.lower() or 'psalm' in r.lower()]
            psalm_ref = psalm_candidates[0] if psalm_candidates else (all_refs[1] if len(all_refs) > 1 else '')
            gospel_ref = all_refs[-1] if len(all_refs) > 2 else (all_refs[-1] if len(all_refs) > 1 and not psalm_ref else '')
        
        # Update result with found references
        if reading1_ref:
            result['reading1']['reference'] = reading1_ref
            logger.info(f"✅ Found Reading 1: {reading1_ref}")
        
        if psalm_ref:
            result['responsorialPsalm']['reference'] = psalm_ref
            logger.info(f"✅ Found Responsorial Psalm: {psalm_ref}")
        
        if gospel_ref:
            result['gospel']['reference'] = gospel_ref
            logger.info(f"✅ Found Gospel: {gospel_ref}")
        
        # If we didn't find any references, log warning but still return structure
        if not reading1_ref and not psalm_ref and not gospel_ref:
            logger.warning(f"⚠️  Could not extract references from USCCB page for {target_date}")
            # Return None to indicate failure
            return None
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error fetching USCCB data: {str(e)}")
        return None


def fetch_public_scripture_text(reference: str) -> str:
    """
    Fetch public domain scripture text for a given reference
    Uses bible-api.com (KJV - public domain)
    """
    if not reference or reference == 'TBD':
        return ""
    
    parsed = parse_bible_reference(reference)
    
    # Format reference for bible-api.com: "John 3:16" or "Romans 9:1-5"
    # The API expects format like: "John+3:16" or "Romans+9:1-5"
    book = parsed.get('book', '')
    chapter = parsed.get('chapter', 0)
    verses = parsed.get('verses', [])
    
    if not book or chapter == 0 or not verses:
        logger.warning(f"⚠️  Could not parse reference: {reference}")
        return ""
    
    # Build verse range string
    if len(verses) == 1:
        verse_ref = f"{chapter}:{verses[0]}"
    elif len(verses) > 1:
        verse_ref = f"{chapter}:{verses[0]}-{verses[-1]}"
    else:
        logger.warning(f"⚠️  No verses found in reference: {reference}")
        return ""
    
    # Format book name for API (handle abbreviations)
    # bible-api.com uses full book names
    book_map = {
        'Romans': 'Romans', 'Rom': 'Romans',
        'Luke': 'Luke', 'Lk': 'Luke',
        'John': 'John', 'Jn': 'John',
        'Matthew': 'Matthew', 'Mt': 'Matthew',
        'Mark': 'Mark', 'Mk': 'Mark',
        'Hebrews': 'Hebrews', 'Heb': 'Hebrews',
        'Psalms': 'Psalms', 'Ps': 'Psalms', 'Psalm': 'Psalms',
        'Wisdom': 'Wisdom', 'Wis': 'Wisdom',
        '1 Corinthians': '1 Corinthians', '1Cor': '1 Corinthians', '1 Cor': '1 Corinthians',
        '2 Corinthians': '2 Corinthians', '2Cor': '2 Corinthians', '2 Cor': '2 Corinthians',
        'Galatians': 'Galatians', 'Gal': 'Galatians',
        'Ephesians': 'Ephesians', 'Eph': 'Ephesians',
        'Philippians': 'Philippians', 'Phil': 'Philippians',
        'Colossians': 'Colossians', 'Col': 'Colossians',
        '1 Thessalonians': '1 Thessalonians', '1Thess': '1 Thessalonians', '1 Thess': '1 Thessalonians',
        '2 Thessalonians': '2 Thessalonians', '2Thess': '2 Thessalonians', '2 Thess': '2 Thessalonians',
        '1 Timothy': '1 Timothy', '1Tim': '1 Timothy', '1 Tim': '1 Timothy',
        '2 Timothy': '2 Timothy', '2Tim': '2 Timothy', '2 Tim': '2 Timothy',
        'Titus': 'Titus',
        'Philemon': 'Philemon', 'Phlm': 'Philemon',
        'James': 'James', 'Jas': 'James',
        '1 Peter': '1 Peter', '1Pet': '1 Peter', '1 Pet': '1 Peter',
        '2 Peter': '2 Peter', '2Pet': '2 Peter', '2 Pet': '2 Peter',
        '1 John': '1 John', '1Jn': '1 John', '1 Jn': '1 John',
        '2 John': '2 John', '2Jn': '2 John', '2 Jn': '2 John',
        '3 John': '3 John', '3Jn': '3 John', '3 Jn': '3 John',
        'Jude': 'Jude',
        'Revelation': 'Revelation', 'Rev': 'Revelation',
        'Acts': 'Acts',
        'Genesis': 'Genesis', 'Gen': 'Genesis',
        'Exodus': 'Exodus', 'Ex': 'Exodus',
        'Leviticus': 'Leviticus', 'Lev': 'Leviticus',
        'Numbers': 'Numbers', 'Num': 'Numbers',
        'Deuteronomy': 'Deuteronomy', 'Deut': 'Deuteronomy',
        'Joshua': 'Joshua', 'Josh': 'Joshua',
        'Judges': 'Judges', 'Judg': 'Judges',
        'Ruth': 'Ruth',
        '1 Samuel': '1 Samuel', '1Sam': '1 Samuel', '1 Sam': '1 Samuel',
        '2 Samuel': '2 Samuel', '2Sam': '2 Samuel', '2 Sam': '2 Samuel',
        '1 Kings': '1 Kings', '1Kgs': '1 Kings', '1 Kgs': '1 Kings',
        '2 Kings': '2 Kings', '2Kgs': '2 Kings', '2 Kgs': '2 Kings',
        '1 Chronicles': '1 Chronicles', '1Chr': '1 Chronicles', '1 Chr': '1 Chronicles',
        '2 Chronicles': '2 Chronicles', '2Chr': '2 Chronicles', '2 Chr': '2 Chronicles',
        'Ezra': 'Ezra',
        'Nehemiah': 'Nehemiah', 'Neh': 'Nehemiah',
        'Esther': 'Esther', 'Esth': 'Esther',
        'Job': 'Job',
        'Proverbs': 'Proverbs', 'Prov': 'Proverbs',
        'Ecclesiastes': 'Ecclesiastes', 'Eccl': 'Ecclesiastes',
        'Song of Songs': 'Song of Songs', 'Song': 'Song of Songs',
        'Isaiah': 'Isaiah', 'Is': 'Isaiah',
        'Jeremiah': 'Jeremiah', 'Jer': 'Jeremiah',
        'Lamentations': 'Lamentations', 'Lam': 'Lamentations',
        'Ezekiel': 'Ezekiel', 'Ezek': 'Ezekiel',
        'Daniel': 'Daniel', 'Dan': 'Daniel',
        'Hosea': 'Hosea', 'Hos': 'Hosea',
        'Joel': 'Joel',
        'Amos': 'Amos',
        'Obadiah': 'Obadiah', 'Obad': 'Obadiah',
        'Jonah': 'Jonah',
        'Micah': 'Micah', 'Mic': 'Micah',
        'Nahum': 'Nahum', 'Nah': 'Nahum',
        'Habakkuk': 'Habakkuk', 'Hab': 'Habakkuk',
        'Zephaniah': 'Zephaniah', 'Zeph': 'Zephaniah',
        'Haggai': 'Haggai', 'Hag': 'Haggai',
        'Zechariah': 'Zechariah', 'Zech': 'Zechariah',
        'Malachi': 'Malachi', 'Mal': 'Malachi',
    }
    
    api_book = book_map.get(book, book)
    
    # Build API URL
    api_ref = f"{api_book}+{verse_ref}"
    api_url = f"https://bible-api.com/{api_ref}"
    
    logger.info(f"📖 Fetching scripture text for {reference} from bible-api.com")
    
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract text from API response
        if 'text' in data:
            # Clean up the text (remove verse numbers if present, normalize whitespace)
            text = data['text'].strip()
            # Remove verse number markers like "1 " at start of lines if present
            text = re.sub(r'^\d+\s+', '', text, flags=re.MULTILINE)
            text = ' '.join(text.split())  # Normalize whitespace
            logger.info(f"✅ Fetched {len(text)} characters for {reference}")
            return text
        else:
            logger.warning(f"⚠️  No text field in API response for {reference}")
            return ""
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error fetching scripture text for {reference}: {str(e)}")
        return ""
    except Exception as e:
        logger.error(f"❌ Unexpected error fetching scripture text for {reference}: {str(e)}")
        return ""


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
    Seed responsorial psalm for a daily reading document
    Only adds responsorial_psalm and responsorial_psalm_verse fields
    Preserves ALL other existing data
    
    Args:
        target_date: Date to seed
        dry_run: If True, don't write to Firestore
    
    Returns:
        Dict with seeding results
    """
    if not _firebase_initialized:
        initialize_firebase()
    
    doc_id = target_date.strftime("%Y-%m-%d")
    logger.info(f"📅 Processing {doc_id} for responsorial psalm")
    
    # Check if document exists
    doc_ref = _db.collection('daily_scripture').document(doc_id)
    existing_doc = doc_ref.get()
    
    if not existing_doc.exists:
        logger.warning(f"⚠️  Document {doc_id} does not exist - skipping")
        return {'status': 'skipped', 'doc_id': doc_id, 'reason': 'document_not_found'}
    
    existing_data = existing_doc.to_dict()
    
    # Check if responsorial psalm already exists
    if existing_data.get('responsorial_psalm') and existing_data.get('responsorial_psalm_verse'):
        logger.info(f"⏭️  Document {doc_id} already has responsorial psalm - skipping")
        return {'status': 'skipped', 'doc_id': doc_id, 'reason': 'already_exists'}
    
    # Try to get responsorial psalm reference from USCCB
    usccb_reading = fetch_usccb_reading_data(target_date)
    psalm_ref = usccb_reading.get('responsorialPsalm', {}).get('reference', '') if usccb_reading else ''
    
    if not psalm_ref or psalm_ref == 'TBD':
        logger.warning(f"⚠️  No responsorial psalm reference found for {doc_id}")
        return {'status': 'skipped', 'doc_id': doc_id, 'reason': 'no_reference_found'}
    
    # Fetch scripture text
    psalm_text = fetch_public_scripture_text(psalm_ref)
    
    if not psalm_text:
        logger.warning(f"⚠️  Could not fetch text for {psalm_ref}")
        return {'status': 'skipped', 'doc_id': doc_id, 'reason': 'no_text_fetched'}
    
    # Prepare update data - ONLY responsorial psalm fields
    update_data = {
        'responsorial_psalm': psalm_text,
        'responsorial_psalm_verse': psalm_ref,
        'updatedAt': firestore.SERVER_TIMESTAMP
    }
    
    logger.info(f"📖 Adding responsorial psalm: {psalm_ref}")
    
    # Preserve existing fields - don't overwrite them
    if dry_run:
        logger.info(f"🧪 DRY RUN: Would update document {doc_id}")
        logger.info(f"   Existing fields preserved: {list(existing_data.keys())}")
        logger.info(f"   Fields to add/update: {list(update_data.keys())}")
        return {'status': 'dry_run', 'doc_id': doc_id}
    
    try:
        # Only update if there are fields to add
        if update_data:
            doc_ref.set(update_data, merge=True)
            logger.info(f"✅ Updated document {doc_id} with new fields: {list(update_data.keys())}")
        else:
            logger.info(f"⏭️  Document {doc_id} already has all fields, skipping update")
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
        
        # Check if custom date range is provided via query parameters
        start_date_param = request.args.get('start_date')
        end_date_param = request.args.get('end_date')
        
        if start_date_param:
            # Parse custom start date
            try:
                start_date = datetime.strptime(start_date_param, '%Y-%m-%d').date()
                logger.info(f"📅 Using custom start date: {start_date}")
            except ValueError:
                logger.error(f"❌ Invalid start_date format: {start_date_param}. Use YYYY-MM-DD")
                return {
                    'statusCode': 400,
                    'body': {'status': 'error', 'message': 'Invalid start_date format. Use YYYY-MM-DD'}
                }, 400
        else:
            # Calculate next month (default behavior)
            if today.month == 12:
                next_month = 1
                next_year = today.year + 1
            else:
                next_month = today.month + 1
                next_year = today.year
            
            # Start date is the 1st of next month
            start_date = date(next_year, next_month, 1)
        
        # Determine end date
        if end_date_param:
            try:
                end_date = datetime.strptime(end_date_param, '%Y-%m-%d').date()
                logger.info(f"📅 Using custom end date: {end_date}")
                days_to_seed = (end_date - start_date).days + 1
            except ValueError:
                logger.error(f"❌ Invalid end_date format: {end_date_param}. Use YYYY-MM-DD")
                return {
                    'statusCode': 400,
                    'body': {'status': 'error', 'message': 'Invalid end_date format. Use YYYY-MM-DD'}
                }, 400
        else:
            # Default: Seed days 1-30 of the target month
            target_month = start_date.month
            target_year = start_date.year
            days_to_seed = 30
        
        dry_run = os.environ.get('DRY_RUN', '').lower() == 'true'
        
        if dry_run:
            logger.info("🧪 Running in DRY RUN mode - no data will be saved to Firestore")
        
        if start_date_param or end_date_param:
            logger.info(f"📅 Seeding custom date range: {start_date} to {start_date + timedelta(days=days_to_seed-1)}")
        else:
            logger.info(f"📅 Seeding days 1-30 of next month: {start_date.strftime('%B %Y')}")
        
        target_month = start_date.month
        target_year = start_date.year
        
        results = {
            'status': 'success',
            'start_date': start_date.isoformat(),
            'target_month': f"{target_year}-{target_month:02d}",
            'days_to_seed': days_to_seed,
            'processed_dates': [],
            'successful': [],
            'errors': []
        }
        
        # Seed readings for the specified date range
        for i in range(days_to_seed):
            target_date = start_date + timedelta(days=i)
            
            # Skip if we've gone past the end date (when using custom range)
            if end_date_param and target_date > end_date:
                logger.info(f"⏭️  Skipping {target_date.strftime('%Y-%m-%d')} - past end date")
                break
            
            # Skip if we've gone past the end of the month (for default behavior with months < 30 days)
            if not end_date_param and target_date.month != target_month:
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

