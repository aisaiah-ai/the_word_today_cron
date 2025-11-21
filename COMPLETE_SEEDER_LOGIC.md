# Daily Scripture Readings Seeder - Complete Logic & Implementation Guide

## 📋 Overview

This document contains the complete logic for a Cloud Function that seeds daily Catholic scripture readings from USCCB.org into Firebase Firestore. Use this as a prompt to recreate or understand the seeder.

---

## 🎯 Core Requirements

### 1. **Data Source**
- **Primary Source:** USCCB.org (United States Conference of Catholic Bishops)
- **URL Pattern:** `https://bible.usccb.org/bible/readings/MMDDYY.cfm`
- **Example:** `https://bible.usccb.org/bible/readings/111425.cfm` (Nov 14, 2025)

### 2. **Data Structure**
Each document in Firestore (`daily_scripture` collection) should have:

```javascript
{
  // Identifiers
  "id": "2025-11-14",                    // Document ID (YYYY-MM-DD)
  "title": "Daily Scripture",
  
  // Links
  "usccb_link": "https://bible.usccb.org/bible/readings/111425.cfm",
  
  // First Reading
  "first_reading_verse": "Wisdom 13:1-9",
  "first_reading": "[Full text from public domain API]",
  
  // Second Reading (Sundays/Solemnities only)
  "second_reading_verse": "Colossians 1:12-20",  // Optional
  "second_reading": "[Full text from public domain API]",  // Optional
  
  // Responsorial Psalm
  "responsorial_psalm_verse": "Psalm 19:2-3, 4-5ab",
  "responsorial_psalm": "[Full psalm text from public domain API]",
  "responsorial_psalm_response": "The heavens proclaim the glory of God.",
  
  // Gospel
  "gospel_verse": "Luke 17:26-37",
  "gospel": "[Full text from public domain API]",
  
  // Body (SHORT FORMAT - KEY REQUIREMENT)
  "body": "Gospel: Luke 17:26-37",  // NOT the full gospel text!
  
  // Reference (legacy field)
  "reference": "Luke 17:26-37",
  
  // Timestamps
  "createdAt": SERVER_TIMESTAMP,
  "updatedAt": SERVER_TIMESTAMP
}
```

---

## 🔑 KEY LOGIC #1: Body Field Must Be SHORT

### ❌ WRONG (Old Approach):
```python
# DO NOT DO THIS - Body should NOT contain full gospel text
new_doc_data['body'] = gospel_text  # This makes body 500-2000 characters!
```

### ✅ CORRECT (New Approach):
```python
# Body should be a SHORT one-liner with just the reference
gospel_ref = usccb_data.get('gospel', {}).get('reference', '')
new_doc_data['body'] = f"Gospel: {gospel_ref}"  # Only 15-30 characters
```

### Why This Matters:
- **Storage Efficiency:** Reduces document size by 95%
- **Bandwidth:** Faster reads for mobile apps
- **Display:** Apps show reference, not full text by default
- **Full Text:** Still available in the `gospel` field if needed

---

## 🔑 KEY LOGIC #2: Responsorial Psalm Implementation

### Step 1: Fetch USCCB Data
```python
def fetch_usccb_reading_data(target_date: date) -> Optional[Dict]:
    """
    Scrape USCCB website to extract Bible references (NOT full text)
    Returns structured data with references only
    """
    url = generate_usccb_url(target_date)
    response = requests.get(url, timeout=30)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    result = {
        'title': f"Readings for {target_date.strftime('%A, %B %d, %Y')}",
        'url': url,
        'reading1': {'title': 'Reading 1', 'reference': ''},
        'responsorialPsalm': {
            'title': 'Responsorial Psalm', 
            'reference': '',
            'response': ''  # The refrain/antiphon
        },
        'gospel': {'title': 'Gospel', 'reference': ''}
    }
    
    # Find all content-header sections
    headers = soup.find_all('div', class_='content-header')
    
    for header in headers:
        name_elem = header.find('h3', class_='name')
        if not name_elem:
            continue
        
        section_name = name_elem.get_text().strip()
        address_elem = header.find('div', class_='address')
        
        if not address_elem:
            continue
        
        ref_link = address_elem.find('a')
        if ref_link:
            reference = ref_link.get_text().strip()
            
            # Match sections
            section_lower = section_name.lower().strip()
            
            if 'reading 1' in section_lower or 'first reading' in section_lower:
                result['reading1']['reference'] = reference
            
            elif 'responsorial psalm' in section_lower:
                result['responsorialPsalm']['reference'] = reference
                
                # CRITICAL: Extract the psalm response/refrain
                # Look for the psalm content after the header
                content_body = header.find_next_sibling('div', class_='content-body')
                if content_body:
                    # Find text that starts with "R."
                    response_match = re.search(
                        r'R\.\s*(?:\([^)]+\)\s*)?(.+?)(?:\n|$)', 
                        content_body.get_text(), 
                        re.MULTILINE
                    )
                    if response_match:
                        response = response_match.group(1).strip()
                        # Remove trailing asterisks
                        response = re.sub(r'\*+$', '', response).strip()
                        result['responsorialPsalm']['response'] = response
            
            elif 'gospel' in section_lower:
                result['gospel']['reference'] = reference
            
            elif 'reading 2' in section_lower or 'second reading' in section_lower:
                result['reading2'] = {'title': 'Reading 2', 'reference': reference}
    
    # Validation: Must have at least gospel and responsorial psalm
    if not result['responsorialPsalm']['reference']:
        logger.warning(f"Could not extract responsorial psalm for {target_date}")
        return None
    
    return result
```

### Step 2: Fetch Public Domain Text
```python
def fetch_public_scripture_text(reference: str) -> str:
    """
    Fetch public domain scripture text from bible-api.com (KJV)
    
    Args:
        reference: e.g., "Psalm 19:2-3, 4-5ab"
    
    Returns:
        Plain text of the scripture passage
    """
    if not reference or reference == 'TBD':
        return ""
    
    parsed = parse_bible_reference(reference)
    
    book = parsed.get('book', '')
    chapter = parsed.get('chapter', 0)
    verses = parsed.get('verses', [])
    
    if not book or chapter == 0 or not verses:
        return ""
    
    # Build verse range string
    if len(verses) == 1:
        verse_ref = f"{chapter}:{verses[0]}"
    else:
        verse_ref = f"{chapter}:{verses[0]}-{verses[-1]}"
    
    # Build API URL
    api_ref = f"{book}+{verse_ref}"
    api_url = f"https://bible-api.com/{api_ref}"
    
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'text' in data:
            text = data['text'].strip()
            # Remove verse number markers
            text = re.sub(r'^\d+\s+', '', text, flags=re.MULTILINE)
            text = ' '.join(text.split())  # Normalize whitespace
            return text
        else:
            return ""
    except Exception as e:
        logger.error(f"Error fetching scripture text: {e}")
        return ""
```

### Step 3: Store All Three Components
```python
# In the seed_daily_reading function:

# Get responsorial psalm data
psalm_ref = usccb_reading.get('responsorialPsalm', {}).get('reference', '')
psalm_response = usccb_reading.get('responsorialPsalm', {}).get('response', '')

# Store all three fields:
if psalm_ref:
    # 1. The verse reference
    new_doc_data['responsorial_psalm_verse'] = psalm_ref
    
    # 2. The response/refrain (the part people repeat)
    if psalm_response:
        new_doc_data['responsorial_psalm_response'] = psalm_response
    
    # 3. The full psalm text
    psalm_text = fetch_public_scripture_text(psalm_ref)
    if psalm_text:
        new_doc_data['responsorial_psalm'] = psalm_text
    else:
        # Fallback for Deuterocanonical texts not in public APIs
        new_doc_data['responsorial_psalm'] = f"[Text not available - see {psalm_ref} at USCCB]"
```

---

## 🔑 KEY LOGIC #3: Complete Document Creation

### Creating a New Document
```python
def seed_daily_reading(target_date: date, dry_run: bool = False, project='primary'):
    """
    Seed responsorial psalm and all readings for a daily reading document
    """
    db = initialize_firebase(project)
    doc_id = target_date.strftime("%Y-%m-%d")
    
    # Check if document exists
    doc_ref = db.collection('daily_scripture').document(doc_id)
    existing_doc = doc_ref.get()
    
    # Fetch USCCB data
    usccb_reading = fetch_usccb_reading_data(target_date)
    
    if not usccb_reading:
        logger.warning(f"Could not fetch USCCB data for {doc_id}")
        return {'status': 'error', 'doc_id': doc_id, 'error': 'No USCCB data'}
    
    # If document doesn't exist, create it
    if not existing_doc.exists:
        logger.info(f"Creating new document {doc_id} with all readings")
        
        # Extract references
        reading1_ref = usccb_reading.get('reading1', {}).get('reference', '')
        reading2_ref = usccb_reading.get('reading2', {}).get('reference', '') if 'reading2' in usccb_reading else ''
        gospel_ref = usccb_reading.get('gospel', {}).get('reference', '')
        psalm_ref = usccb_reading.get('responsorialPsalm', {}).get('reference', '')
        psalm_response = usccb_reading.get('responsorialPsalm', {}).get('response', '')
        
        # Fetch scripture texts from public domain APIs
        first_reading_text = fetch_public_scripture_text(reading1_ref) if reading1_ref else ''
        second_reading_text = fetch_public_scripture_text(reading2_ref) if reading2_ref else ''
        gospel_text = fetch_public_scripture_text(gospel_ref) if gospel_ref else ''
        psalm_text = fetch_public_scripture_text(psalm_ref) if psalm_ref else ''
        
        # Build document
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
        
        # Add second reading (Sundays/Solemnities only)
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
                # CRITICAL: Body is SHORT - just the reference!
                new_doc_data['body'] = f"Gospel: {gospel_ref}"
            else:
                new_doc_data['gospel'] = None
                new_doc_data['body'] = f"Gospel: {gospel_ref}"
        
        # Add responsorial psalm (all three components)
        if psalm_ref:
            new_doc_data['responsorial_psalm_verse'] = psalm_ref
            if psalm_response:
                new_doc_data['responsorial_psalm_response'] = psalm_response
            if psalm_text:
                new_doc_data['responsorial_psalm'] = psalm_text
            else:
                new_doc_data['responsorial_psalm'] = f"[Text not available - see {psalm_ref} at USCCB]"
        
        if dry_run:
            logger.info(f"DRY RUN: Would create document {doc_id}")
            return {'status': 'dry_run', 'doc_id': doc_id}
        
        try:
            doc_ref.set(new_doc_data, merge=False)
            logger.info(f"Created new document {doc_id} with all daily readings")
            return {'status': 'success', 'doc_id': doc_id}
        except Exception as e:
            logger.error(f"Error creating document {doc_id}: {str(e)}")
            return {'status': 'error', 'doc_id': doc_id, 'error': str(e)}
    
    # Document exists - check if it needs updating
    existing_data = existing_doc.to_dict()
    
    # Check for incorrect default data (all days have "John 3:16")
    existing_gospel_verse = existing_data.get('gospel_verse', '')
    if existing_gospel_verse == 'John 3:16' and target_date.day != 13:
        logger.warning(f"Document {doc_id} has incorrect default data - will overwrite")
        # Delete and recreate
        try:
            doc_ref.delete()
            logger.info(f"Deleted incorrect document {doc_id}, will recreate")
            # Recursively call to create new document
            return seed_daily_reading(target_date, dry_run, project)
        except Exception as e:
            logger.error(f"Error deleting incorrect document {doc_id}: {str(e)}")
            return {'status': 'error', 'doc_id': doc_id, 'error': str(e)}
    
    # Check if responsorial psalm already complete
    has_psalm = existing_data.get('responsorial_psalm')
    has_psalm_verse = existing_data.get('responsorial_psalm_verse')
    has_psalm_response = existing_data.get('responsorial_psalm_response')
    
    if has_psalm and has_psalm_verse and has_psalm_response:
        logger.info(f"Document {doc_id} already has complete responsorial psalm - skipping")
        return {'status': 'skipped', 'doc_id': doc_id, 'reason': 'already_exists'}
    
    # Update missing fields
    update_data = {
        'updatedAt': firestore.SERVER_TIMESTAMP
    }
    
    if not has_psalm_verse:
        update_data['responsorial_psalm_verse'] = psalm_ref
    
    if not has_psalm_response and psalm_response:
        update_data['responsorial_psalm_response'] = psalm_response
    
    if not has_psalm:
        psalm_text = fetch_public_scripture_text(psalm_ref)
        if psalm_text:
            update_data['responsorial_psalm'] = psalm_text
        else:
            update_data['responsorial_psalm'] = f"[Text not available - see {psalm_ref} at USCCB]"
    
    if dry_run:
        logger.info(f"DRY RUN: Would update document {doc_id}")
        return {'status': 'dry_run', 'doc_id': doc_id}
    
    try:
        if update_data:
            doc_ref.set(update_data, merge=True)
            logger.info(f"Updated document {doc_id} with missing fields")
        return {'status': 'success', 'doc_id': doc_id}
    except Exception as e:
        logger.error(f"Error seeding {doc_id}: {str(e)}")
        return {'status': 'error', 'doc_id': doc_id, 'error': str(e)}
```

---

## 🔑 KEY LOGIC #4: Special Cases

### Thanksgiving Day
```python
# Thanksgiving has a special URL format
if target_date.month == 11 and target_date.day == 27:  # 2025 example
    url = url.replace('.cfm', '-Thanksgiving.cfm')
    logger.info(f"Using Thanksgiving URL: {url}")
```

### Sunday vs Weekday
```python
# Sundays/Solemnities have second readings, weekdays don't
if 'reading2' in usccb_data:
    # This is a Sunday or major feast day
    result['reading2'] = {'title': 'Reading 2', 'reference': reference}
```

### Deuterocanonical Books
```python
# Some books (Wisdom, Sirach, etc.) may not be in public APIs
if not psalm_text:
    logger.warning(f"Could not fetch text for {psalm_ref} - Deuterocanonical")
    new_doc_data['responsorial_psalm'] = f"[Text not available - see {psalm_ref} at USCCB]"
```

---

## 🏗️ Cloud Function Structure

### Entry Point
```python
def seed_daily_readings_cron(request):
    """
    Cloud Function entry point
    Runs monthly on 15th to seed next month's readings
    """
    # Get date range from request parameters or use default (next month)
    start_date_param = request.args.get('start_date')
    end_date_param = request.args.get('end_date')
    
    if start_date_param:
        start_date = datetime.strptime(start_date_param, '%Y-%m-%d').date()
    else:
        # Default: seed next month
        today = date.today()
        if today.month == 12:
            next_month = 1
            next_year = today.year + 1
        else:
            next_month = today.month + 1
            next_year = today.year
        start_date = date(next_year, next_month, 1)
    
    # Seed dates
    results = {
        'status': 'success',
        'processed_dates': [],
        'successful': [],
        'errors': []
    }
    
    current_date = start_date
    for i in range(30):  # Seed 30 days
        result = seed_daily_reading(current_date, dry_run=False, project='primary')
        
        if result['status'] == 'success':
            results['successful'].append(current_date.strftime('%Y-%m-%d'))
        else:
            results['errors'].append({
                'date': current_date.strftime('%Y-%m-%d'),
                'error': result.get('error', 'unknown')
            })
        
        results['processed_dates'].append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    
    return {'statusCode': 200, 'body': results}, 200
```

---

## 📦 Dependencies

### requirements.txt
```txt
firebase-admin==6.2.0
requests==2.31.0
beautifulsoup4==4.12.2
functions-framework==3.5.0
```

### Imports
```python
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
```

---

## 🚀 Deployment

### GCloud Command
```bash
gcloud functions deploy daily-readings-seeder \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=seed_daily_readings_cron \
  --trigger-http \
  --timeout=540s \
  --memory=512MB \
  --set-env-vars="FIREBASE_CREDENTIALS_JSON_B64=YOUR_BASE64_ENCODED_KEY"
```

---

## ✅ Validation Checklist

When verifying seeded documents, check:

1. **Body Field:**
   - ✅ Should be SHORT: `"Gospel: Luke 17:26-37"`
   - ❌ NOT long: Full gospel text (500+ chars)

2. **Responsorial Psalm - THREE Components:**
   - ✅ `responsorial_psalm_verse`: Reference (e.g., "Psalm 19:2-3, 4-5ab")
   - ✅ `responsorial_psalm_response`: Refrain (e.g., "The heavens proclaim...")
   - ✅ `responsorial_psalm`: Full text

3. **Unique Data:**
   - ✅ Each day should have DIFFERENT gospel_verse
   - ❌ NOT all "John 3:16" (indicates default/incorrect data)

4. **Required Fields:**
   - ✅ `usccb_link`
   - ✅ `first_reading_verse`
   - ✅ `gospel_verse`
   - ✅ `responsorial_psalm_verse`

5. **Optional Fields:**
   - `second_reading_verse` (Sundays only)
   - `second_reading` (Sundays only)

---

## 🐛 Common Issues & Solutions

### Issue 1: Body Too Long
**Problem:** Body contains full gospel text (500+ characters)
**Solution:** Change line to: `new_doc_data['body'] = f"Gospel: {gospel_ref}"`

### Issue 2: Missing Responsorial Psalm Response
**Problem:** No `responsorial_psalm_response` field
**Solution:** Ensure HTML scraping extracts text starting with "R."

### Issue 3: All Days Have Same Gospel
**Problem:** All documents have "John 3:16"
**Solution:** Add logic to detect and delete incorrect default data

### Issue 4: Deuterocanonical Text Not Available
**Problem:** Some books aren't in public APIs
**Solution:** Use placeholder: `"[Text not available - see {ref} at USCCB]"`

---

## 📊 Example Output

### Correct Document Structure:
```json
{
  "id": "2025-11-23",
  "title": "Daily Scripture",
  "usccb_link": "https://bible.usccb.org/bible/readings/112325.cfm",
  
  "first_reading_verse": "2 Samuel 5:1-3",
  "first_reading": "All the tribes of Israel came to David...",
  
  "second_reading_verse": "Colossians 1:12-20",
  "second_reading": "Giving thanks to the Father...",
  
  "responsorial_psalm_verse": "Psalm 122:1-2, 3-4, 4-5",
  "responsorial_psalm": "I rejoiced when they said to me...",
  "responsorial_psalm_response": "Let us go rejoicing to the house of the Lord.",
  
  "gospel_verse": "Luke 23:35-43",
  "gospel": "The people stood watching. The rulers...",
  
  "body": "Gospel: Luke 23:35-43",
  "reference": "Luke 23:35-43",
  
  "createdAt": "2025-11-14T12:00:00Z",
  "updatedAt": "2025-11-14T12:00:00Z"
}
```

---

## 🎓 Summary

### Three Critical Rules:
1. **Body = Short Reference** (NOT full text)
2. **Responsorial Psalm = Three Components** (verse, text, response)
3. **Unique Data Per Day** (detect and fix duplicates)

### Data Flow:
```
USCCB.org → Scrape References → bible-api.com → Fetch Public Text → Firestore
```

### Key Functions:
1. `fetch_usccb_reading_data()` - Scrape USCCB for references
2. `fetch_public_scripture_text()` - Get text from public API
3. `seed_daily_reading()` - Combine and store in Firestore

---

**Use this document as a complete reference to recreate the daily readings seeder from scratch!**


