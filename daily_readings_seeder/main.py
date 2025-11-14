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
_db_secondary = None


def _get_firebase_credentials(env_var_json, env_var_b64, env_var_path, app_name='default'):
    """
    Helper function to get Firebase credentials from various sources.
    Returns credentials object or None if not found.
    """
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
    
    # Try to get from file path (for local development)
    firebase_cred_path = os.environ.get(env_var_path)
    if firebase_cred_path and os.path.exists(firebase_cred_path):
        cred = credentials.Certificate(firebase_cred_path)
        logger.info(f"✅ Initialized Firebase {app_name} from file: {firebase_cred_path}")
        return cred
    
    # No credentials found - return None (caller will handle Application Default Credentials)
    return None


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
            _firebase_initialized = True
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
            cred = _get_firebase_credentials(
                'FIREBASE_CREDENTIALS_JSON_SECONDARY',
                'FIREBASE_CREDENTIALS_JSON_B64_SECONDARY',
                'FIREBASE_CRED_SECONDARY',
                'secondary'
            )
            
            # If no credentials provided, use Application Default Credentials
            if cred is None:
                # Get project ID from environment or use default
                project_id = os.environ.get('FIREBASE_PROJECT_ID_SECONDARY') or os.environ.get('GCP_PROJECT_ID_SECONDARY')
                if project_id:
                    logger.info(f"ℹ️ No secondary Firebase credentials found, using Application Default Credentials for project: {project_id}")
                    # Use Application Default Credentials with explicit project ID
                    cred = credentials.ApplicationDefault()
                else:
                    logger.info("ℹ️ No secondary Firebase credentials found, using Application Default Credentials")
                    cred = credentials.ApplicationDefault()
            
            # Initialize secondary Firebase app
            try:
                app = firebase_admin.get_app('secondary')
            except ValueError:
                # Get project ID for initialization
                project_id = os.environ.get('FIREBASE_PROJECT_ID_SECONDARY') or os.environ.get('GCP_PROJECT_ID_SECONDARY')
                if project_id:
                    firebase_admin.initialize_app(cred, name='secondary', options={'projectId': project_id})
                else:
                    firebase_admin.initialize_app(cred, name='secondary')
            
            _db_secondary = firestore.client(app=firebase_admin.get_app('secondary'))
            logger.info("✅ Secondary Firebase initialized using Application Default Credentials")
            return _db_secondary
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize secondary Firebase: {str(e)}")
            raise
    else:
        raise ValueError(f"Invalid project: {project}. Must be 'primary' or 'secondary'")


def generate_usccb_url(target_date: date) -> str:
    """Generate USCCB daily readings URL in MMDDYY format"""
    month = str(target_date.month).zfill(2)
    day = str(target_date.day).zfill(2)
    year = str(target_date.year)[-2:]  # Last 2 digits of year
    return f"https://bible.usccb.org/bible/readings/{month}{day}{year}.cfm"


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
    
    # Special handling for Thanksgiving (Nov 27 in 2025)
    # Try Thanksgiving URL first for this date
    if target_date.month == 11 and target_date.day == 27:
        url = url.replace('.cfm', '-Thanksgiving.cfm')
        logger.info(f"🦃 Using Thanksgiving URL: {url}")
    else:
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
            'responsorialPsalm': {'title': 'Responsorial Psalm', 'reference': '', 'response': ''},
            'gospel': {'title': 'Gospel', 'reference': ''}
        }
        
        # USCCB uses <div class="address"> tags for Bible references
        # Structure: <h3 class="name">Reading 1</h3> <div class="address"><a>Reference</a></div>
        
        # Find all content-header sections
        headers = soup.find_all('div', class_='content-header')
        
        for header in headers:
            # Get the name/title
            name_elem = header.find('h3', class_='name')
            if not name_elem:
                continue
            
            section_name = name_elem.get_text().strip()
            
            # Get the reference from the address div
            address_elem = header.find('div', class_='address')
            if not address_elem:
                continue
            
            # The reference is in an <a> tag inside the address div
            ref_link = address_elem.find('a')
            if ref_link:
                reference = ref_link.get_text().strip()
                
                # Match to the appropriate section (case-insensitive, flexible matching)
                section_lower = section_name.lower().strip()
                
                if 'reading 1' in section_lower or 'first reading' in section_lower or section_lower == 'reading i':
                    result['reading1']['reference'] = reference
                    logger.info(f"✅ Found Reading 1: {reference}")
                elif 'responsorial psalm' in section_lower or section_lower == 'responsorial psalm':
                    result['responsorialPsalm']['reference'] = reference
                    logger.info(f"✅ Found Responsorial Psalm: {reference}")
                    
                    # Extract the psalm response/refrain (e.g., "R. In you, O Lord, I have found my peace.")
                    # Look for the psalm content after the header
                    content_body = header.find_next_sibling('div', class_='content-body')
                    if content_body:
                        # Find text that starts with "R." or "R. ("
                        response_match = re.search(r'R\.\s*(?:\([^)]+\)\s*)?(.+?)(?:\n|$)', content_body.get_text(), re.MULTILINE)
                        if response_match:
                            response = response_match.group(1).strip()
                            # Remove any trailing asterisks or special chars
                            response = re.sub(r'\*+$', '', response).strip()
                            result['responsorialPsalm']['response'] = response
                            logger.info(f"✅ Found Psalm Response: {response}")
                    
                elif 'gospel' in section_lower:
                    result['gospel']['reference'] = reference
                    logger.info(f"✅ Found Gospel: {reference}")
                elif 'reading 2' in section_lower or 'second reading' in section_lower or section_lower == 'reading ii':
                    # Add reading2 if present
                    result['reading2'] = {'title': 'Reading 2', 'reference': reference}
                    logger.info(f"✅ Found Reading 2: {reference}")
        
        # If we didn't find responsorial psalm, return None
        if not result['responsorialPsalm']['reference']:
            logger.warning(f"⚠️  Could not extract responsorial psalm reference from USCCB page for {target_date}")
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
    # Handle complex formats like "Psalm 98:5-6, 7-8, 9"
    # For bible-api.com, simplify to first and last verse
    if len(verses) == 0:
        logger.warning(f"⚠️  No verses found in reference: {reference}")
        return ""
    elif len(verses) == 1:
        verse_ref = f"{chapter}:{verses[0]}"
    else:
        # Use first and last verse to create a simple range
        verse_ref = f"{chapter}:{verses[0]}-{verses[-1]}"
    
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


def seed_daily_reading(target_date: date, dry_run: bool = False, project='primary') -> Dict:
    """
    Seed responsorial psalm for a daily reading document
    Only adds responsorial_psalm and responsorial_psalm_verse fields
    Preserves ALL other existing data
    
    Args:
        target_date: Date to seed
        dry_run: If True, don't write to Firestore
        project: 'primary' or 'secondary' - which Firebase project to write to
    
    Returns:
        Dict with seeding results
    """
    db = initialize_firebase(project)
    
    doc_id = target_date.strftime("%Y-%m-%d")
    logger.info(f"📅 Processing {doc_id} for daily readings")
    
    # Check if document exists
    doc_ref = db.collection('daily_scripture').document(doc_id)
    existing_doc = doc_ref.get()
    
    # Fetch USCCB data first (needed for both creating and updating)
    usccb_reading = fetch_usccb_reading_data(target_date)
    if not usccb_reading:
        logger.error(f"❌ Could not fetch USCCB data for {doc_id}")
        return {'status': 'error', 'doc_id': doc_id, 'error': 'Could not fetch USCCB data'}
    
    # If document doesn't exist, create it with all fields
    if not existing_doc.exists:
        logger.info(f"🆕 Document {doc_id} does not exist - creating new document with all readings")
        
        # Build complete document data
        reading1_ref = usccb_reading.get('reading1', {}).get('reference', '')
        reading2_ref = usccb_reading.get('reading2', {}).get('reference', '') if 'reading2' in usccb_reading else ''
        gospel_ref = usccb_reading.get('gospel', {}).get('reference', '')
        psalm_ref = usccb_reading.get('responsorialPsalm', {}).get('reference', '')
        psalm_response = usccb_reading.get('responsorialPsalm', {}).get('response', '')
        
        # Fetch scripture text for readings
        first_reading_text = fetch_public_scripture_text(reading1_ref) if reading1_ref else ''
        second_reading_text = fetch_public_scripture_text(reading2_ref) if reading2_ref else ''
        gospel_text = fetch_public_scripture_text(gospel_ref) if gospel_ref else ''
        psalm_text = fetch_public_scripture_text(psalm_ref) if psalm_ref else ''
        
        # Build new document
        new_doc_data = {
        'id': doc_id,
        'title': 'Daily Scripture',
            'reference': gospel_ref or reading1_ref or '',
            'usccb_link': usccb_reading.get('url', ''),
        'updatedAt': firestore.SERVER_TIMESTAMP,
            'createdAt': firestore.SERVER_TIMESTAMP
        }
        
        # Add first reading
        if reading1_ref:
            new_doc_data['first_reading_verse'] = reading1_ref
            if first_reading_text:
                new_doc_data['first_reading'] = first_reading_text
            else:
                new_doc_data['first_reading'] = None
        
        # Add second reading (if present)
        if reading2_ref:
            new_doc_data['second_reading_verse'] = reading2_ref
            if second_reading_text:
                new_doc_data['second_reading'] = second_reading_text
            else:
                new_doc_data['second_reading'] = None
        
        # Add gospel
        if gospel_ref:
            new_doc_data['gospel_verse'] = gospel_ref
            if gospel_text:
                new_doc_data['gospel'] = gospel_text
                new_doc_data['body'] = gospel_text  # Also set body to gospel for compatibility
            else:
                new_doc_data['gospel'] = None
                new_doc_data['body'] = None
        
        # Add responsorial psalm
        if psalm_ref:
            new_doc_data['responsorial_psalm_verse'] = psalm_ref
            if psalm_response:
                new_doc_data['responsorial_psalm_response'] = psalm_response
            if psalm_text:
                new_doc_data['responsorial_psalm'] = psalm_text
            else:
                new_doc_data['responsorial_psalm'] = f"[Text not available - see {psalm_ref} at USCCB]"
        
        if dry_run:
            logger.info(f"🧪 DRY RUN: Would create document {doc_id} with all readings")
            return {'status': 'dry_run', 'doc_id': doc_id}
        
        try:
            doc_ref.set(new_doc_data, merge=False)  # Create new document
            logger.info(f"✅ Created new document {doc_id} with all daily readings")
            return {'status': 'success', 'doc_id': doc_id}
        except Exception as e:
            logger.error(f"❌ Error creating document {doc_id}: {str(e)}")
            return {'status': 'error', 'doc_id': doc_id, 'error': str(e)}
    
    # Document exists - update it with missing fields
    existing_data = existing_doc.to_dict()
    
    # Check if responsorial psalm and response already exist
    has_psalm = existing_data.get('responsorial_psalm')
    has_psalm_verse = existing_data.get('responsorial_psalm_verse')
    has_psalm_response = existing_data.get('responsorial_psalm_response')
    
    # Skip only if ALL three fields exist
    if has_psalm and has_psalm_verse and has_psalm_response:
        logger.info(f"⏭️  Document {doc_id} already has complete responsorial psalm - skipping")
        return {'status': 'skipped', 'doc_id': doc_id, 'reason': 'already_exists'}
    
    # Try to get responsorial psalm reference and response from USCCB
    usccb_reading = fetch_usccb_reading_data(target_date)
    psalm_ref = usccb_reading.get('responsorialPsalm', {}).get('reference', '') if usccb_reading else ''
    psalm_response = usccb_reading.get('responsorialPsalm', {}).get('response', '') if usccb_reading else ''
    
    if not psalm_ref or psalm_ref == 'TBD':
        logger.warning(f"⚠️  No responsorial psalm reference found for {doc_id}")
        return {'status': 'skipped', 'doc_id': doc_id, 'reason': 'no_reference_found'}
    
    # Prepare update data - only add missing fields
    update_data = {
        'updatedAt': firestore.SERVER_TIMESTAMP
    }
    
    # Add psalm verse if missing
    if not has_psalm_verse:
        update_data['responsorial_psalm_verse'] = psalm_ref
        logger.info(f"📖 Adding responsorial psalm verse: {psalm_ref}")
    
    # Add psalm response/refrain if missing and found
    if not has_psalm_response and psalm_response:
        update_data['responsorial_psalm_response'] = psalm_response
        logger.info(f"📖 Adding responsorial psalm response: {psalm_response}")
    
    # Add psalm text if missing (try to fetch, but don't fail if unavailable)
    if not has_psalm:
        psalm_text = fetch_public_scripture_text(psalm_ref)
        if psalm_text:
            update_data['responsorial_psalm'] = psalm_text
            logger.info(f"📖 Adding responsorial psalm text: {psalm_ref}")
        else:
            # For Deuterocanonical texts not available in public domain APIs
            # Still save verse and response, but leave text empty or with note
            logger.warning(f"⚠️  Could not fetch text for {psalm_ref} - Deuterocanonical or unsupported format")
            update_data['responsorial_psalm'] = f"[Text not available - see {psalm_ref} at USCCB]"
            logger.info(f"📝 Added placeholder note for Deuterocanonical text: {psalm_ref}")
    
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


def delete_old_readings(cutoff_date: date, dry_run: bool = False, project='primary') -> Dict:
    """
    Delete readings older than the cutoff date
    
    Args:
        cutoff_date: Delete all documents before this date
        dry_run: If True, don't actually delete
        project: 'primary' or 'secondary' - which Firebase project to clean up
    
    Returns:
        Dict with deletion results
    """
    db = initialize_firebase(project)
    
    logger.info(f"🗑️  Deleting readings older than {cutoff_date} from {project} Firebase")
    
    deleted_count = 0
    errors = []
    
    try:
        # Query for documents before cutoff date
        # Document IDs are in format YYYY-MM-DD, so we can use string comparison
        cutoff_id = cutoff_date.strftime("%Y-%m-%d")
        
        # Get all documents
        docs = db.collection('daily_scripture').stream()
        
        for doc in docs:
            doc_id = doc.id
            
            # Skip if not in date format or if >= cutoff
            if not re.match(r'\d{4}-\d{2}-\d{2}', doc_id):
                continue
            
            if doc_id < cutoff_id:
                if dry_run:
                    logger.info(f"🧪 DRY RUN: Would delete {doc_id} from {project}")
                    deleted_count += 1
                else:
                    try:
                        db.collection('daily_scripture').document(doc_id).delete()
                        logger.info(f"🗑️  Deleted {doc_id} from {project}")
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"❌ Error deleting {doc_id} from {project}: {str(e)}")
                        errors.append({'doc_id': doc_id, 'error': str(e)})
        
        logger.info(f"✅ Deleted {deleted_count} old documents")
        return {
            'status': 'success',
            'deleted_count': deleted_count,
            'errors': errors
        }
        
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {str(e)}")
        return {
            'status': 'error',
            'deleted_count': deleted_count,
            'errors': [{'error': str(e)}]
        }


def seed_daily_readings_cron(request):
    """
    Cloud Function entry point for seeding daily readings
    Runs monthly on the 15th to seed days 1-30 of the next month
    Also cleans up readings older than 2 months
    
    Args:
        request: Flask request object (from Functions Framework)
    
    Returns:
        tuple: (response dict, status code)
    """
    try:
        logger.info("🚀 Starting Daily Readings Seeder cron job")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        
        # Check if this is running in secondary project (secondary function deployment)
        # If FIREBASE_PROJECT_ID_SECONDARY is set, we're running as secondary function
        secondary_project_id = os.environ.get('FIREBASE_PROJECT_ID_SECONDARY') or os.environ.get('GCP_PROJECT_ID_SECONDARY')
        is_secondary_function = secondary_project_id is not None
        
        # Also check if we have primary credentials - if not, we're definitely secondary
        has_primary_creds = (
            os.environ.get('FIREBASE_CREDENTIALS_JSON') or
            os.environ.get('FIREBASE_CREDENTIALS_JSON_B64') or
            (os.environ.get('FIREBASE_CRED') and os.path.exists(os.environ.get('FIREBASE_CRED', '')))
        )
        
        # If no primary credentials AND secondary project ID is set, we're secondary function
        if not has_primary_creds and secondary_project_id:
            is_secondary_function = True
        
        # Initialize Firebase based on deployment type
        has_primary = False
        has_secondary = False
        
        if is_secondary_function:
            # This is the secondary function - only initialize secondary
            logger.info(f"🔵 Running as secondary function (project: {secondary_project_id})")
            logger.info("🔵 No primary credentials found - this is definitely the secondary function")
            try:
                initialize_firebase('secondary')
                has_secondary = True
                logger.info("✅ Secondary Firebase initialized using Application Default Credentials - will seed secondary project only")
            except Exception as e:
                logger.error(f"❌ Secondary Firebase initialization failed: {str(e)}")
                logger.error(f"❌ Error details: {type(e).__name__}: {str(e)}")
                raise
        else:
            # This is the primary function - initialize primary, optionally secondary
            try:
                initialize_firebase('primary')
                has_primary = True
                logger.info("✅ Primary Firebase initialized")
            except Exception as e:
                logger.error(f"❌ Primary Firebase initialization failed: {str(e)}")
                raise
            
            # Check if secondary Firebase should also be used
            has_secondary_creds = (
                os.environ.get('FIREBASE_CREDENTIALS_JSON_SECONDARY') or
                os.environ.get('FIREBASE_CREDENTIALS_JSON_B64_SECONDARY') or
                (os.environ.get('FIREBASE_CRED_SECONDARY') and os.path.exists(os.environ.get('FIREBASE_CRED_SECONDARY', '')))
            )
            
            if has_secondary_creds or secondary_project_id:
                try:
                    initialize_firebase('secondary')
                    has_secondary = True
                    if has_secondary_creds:
                        logger.info("✅ Secondary Firebase credentials detected - will seed both projects")
                    else:
                        logger.info(f"✅ Secondary Firebase initialized using Application Default Credentials (project: {secondary_project_id}) - will seed both projects")
                except Exception as e:
                    logger.warning(f"⚠️ Secondary Firebase initialization failed (will continue with primary only): {str(e)}")
                    has_secondary = False
            else:
                logger.info("ℹ️ No secondary Firebase configured - seeding primary project only")
        
        # Clean up old readings (older than 2 months)
        today = date.today()
        # Calculate 2 months prior
        if today.month <= 2:
            cutoff_month = today.month + 10  # Go back to previous year
            cutoff_year = today.year - 1
        else:
            cutoff_month = today.month - 2
            cutoff_year = today.year
        
        cutoff_date = date(cutoff_year, cutoff_month, 1)
        
        dry_run = os.environ.get('DRY_RUN', '').lower() == 'true'
        
        # Clean up old readings based on which projects are initialized
        cleanup_result_primary = None
        cleanup_result_secondary = None
        
        if has_primary:
            logger.info(f"🗑️  Cleaning up readings older than {cutoff_date} from primary")
            cleanup_result_primary = delete_old_readings(cutoff_date, dry_run, 'primary')
        
        if has_secondary:
            try:
                logger.info(f"🗑️  Cleaning up readings older than {cutoff_date} from secondary")
                cleanup_result_secondary = delete_old_readings(cutoff_date, dry_run, 'secondary')
            except Exception as e:
                logger.warning(f"⚠️ Secondary cleanup failed: {str(e)}")
                cleanup_result_secondary = {'status': 'error', 'deleted_count': 0, 'errors': [{'error': str(e)}]}
        
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
        
        # Build firebase_projects list based on what's initialized
        firebase_projects = []
        if has_primary:
            firebase_projects.append('primary')
        if has_secondary:
            firebase_projects.append('secondary')
        
        results = {
            'status': 'success',
            'start_date': start_date.isoformat(),
            'target_month': f"{target_year}-{target_month:02d}",
            'days_to_seed': days_to_seed,
            'processed_dates': [],
            'successful': [],
            'errors': [],
            'firebase_projects': firebase_projects,
            'cleanup': {}
        }
        
        # Add cleanup results for initialized projects
        if has_primary and cleanup_result_primary:
            results['cleanup']['primary'] = {
                'cutoff_date': cutoff_date.isoformat(),
                'deleted_count': cleanup_result_primary.get('deleted_count', 0),
                'errors': cleanup_result_primary.get('errors', [])
            }
        
        if has_secondary and cleanup_result_secondary:
            results['cleanup']['secondary'] = {
                'cutoff_date': cutoff_date.isoformat(),
                'deleted_count': cleanup_result_secondary.get('deleted_count', 0),
                'errors': cleanup_result_secondary.get('errors', [])
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
            
            # Seed based on which projects are initialized
            result = None
            result_secondary = None
            
            if has_primary:
                # Seed to primary Firebase
                result = seed_daily_reading(target_date, dry_run, 'primary')
            
            if has_secondary:
                # Seed to secondary Firebase
                try:
                    result_secondary = seed_daily_reading(target_date, dry_run, 'secondary')
                    if result_secondary['status'] != 'success':
                        logger.warning(f"⚠️ Secondary seeding failed for {date_str}: {result_secondary.get('reason', 'Unknown')}")
                except Exception as e:
                    logger.warning(f"⚠️ Secondary seeding failed for {date_str}: {str(e)}")
                    result_secondary = {'status': 'error', 'error': str(e)}
            
            # Determine overall result based on which projects were seeded
            if is_secondary_function:
                # For secondary function, use secondary result ONLY
                if not result_secondary:
                    logger.error(f"❌ No secondary result for {date_str} - this should not happen!")
                    result = {'status': 'error', 'error': 'Secondary seeding returned no result'}
                else:
                    result = result_secondary
                    logger.info(f"✅ Secondary seeding result for {date_str}: {result.get('status', 'unknown')}")
            elif has_primary and has_secondary:
                # For primary function with both, consider it success if either succeeds
                if result and result['status'] == 'success':
                    pass  # Use primary result
                elif result_secondary and result_secondary['status'] == 'success':
                    result = result_secondary  # Use secondary result if primary failed
                elif result:
                    pass  # Use primary result even if it failed
                else:
                    result = result_secondary if result_secondary else {'status': 'error', 'error': 'No result'}
            
            if result and result['status'] == 'success':
                results['successful'].append(date_str)
                logger.info(f"✅ Successfully seeded {date_str}")
            elif result and result['status'] == 'dry_run':
                results['successful'].append(date_str)
                logger.info(f"🧪 Dry run completed for {date_str}")
            elif result and result['status'] == 'skipped':
                # Skipped is okay - document doesn't exist or already has data
                logger.info(f"⏭️  Skipped {date_str}: {result.get('reason', 'Unknown reason')}")
            else:
                error_msg = result.get('error', result.get('reason', 'Unknown error')) if result else 'No result from seeding'
                results['errors'].append({
                    'date': date_str,
                    'error': error_msg
                })
                logger.error(f"❌ Failed to seed {date_str}: {error_msg}")
            
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

