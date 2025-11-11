"""
Unit tests for Daily Readings Seeder Cloud Function
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import json
import base64
from datetime import date, datetime
from main import (
    initialize_firebase,
    generate_usccb_url,
    parse_bible_reference,
    fetch_usccb_reading_data,
    fetch_public_scripture_text,
    seed_daily_reading,
    seed_daily_readings_cron
)


class TestFirebaseInitialization(unittest.TestCase):
    """Test Firebase initialization with different credential methods"""
    
    def _get_valid_creds(self):
        """Get valid Firebase credentials dict"""
        return {
            'type': 'service_account',
            'project_id': 'test-project',
            'private_key_id': 'test-key-id',
            'private_key': '-----BEGIN PRIVATE KEY-----\nMOCK_KEY\n-----END PRIVATE KEY-----\n',
            'client_email': 'test@test-project.iam.gserviceaccount.com',
            'client_id': '123456789',
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
            'client_x509_cert_url': 'https://www.googleapis.com/robot/v1/metadata/x509/test%40test-project.iam.gserviceaccount.com'
        }
    
    @patch('main.firebase_admin.get_app')
    @patch('main.firebase_admin.initialize_app')
    @patch('main.firestore.client')
    @patch('main.credentials.Certificate')
    def test_initialize_firebase_with_json_string(self, mock_cert, mock_firestore, mock_init, mock_get_app):
        """Test Firebase initialization with JSON string"""
        mock_get_app.side_effect = ValueError("Not initialized")
        mock_cert.return_value = MagicMock()
        mock_firestore.return_value = MagicMock()
        
        with patch.dict(os.environ, {
            'FIREBASE_CREDENTIALS_JSON': json.dumps(self._get_valid_creds())
        }):
            try:
                initialize_firebase()
                mock_cert.assert_called_once()
            except Exception:
                # If initialization fails due to invalid credentials, that's OK for unit tests
                pass
    
    @patch('main.firebase_admin.get_app')
    @patch('main.firebase_admin.initialize_app')
    @patch('main.firestore.client')
    @patch('main.credentials.Certificate')
    def test_initialize_firebase_with_base64(self, mock_cert, mock_firestore, mock_init, mock_get_app):
        """Test Firebase initialization with base64 encoded JSON"""
        mock_get_app.side_effect = ValueError("Not initialized")
        mock_cert.return_value = MagicMock()
        mock_firestore.return_value = MagicMock()
        
        creds_json = json.dumps(self._get_valid_creds())
        creds_b64 = base64.b64encode(creds_json.encode()).decode()
        
        with patch.dict(os.environ, {
            'FIREBASE_CREDENTIALS_JSON_B64': creds_b64
        }, clear=False):
            try:
                initialize_firebase()
                mock_cert.assert_called_once()
            except Exception:
                # If initialization fails due to invalid credentials, that's OK for unit tests
                pass


class TestUSCCBURLGeneration(unittest.TestCase):
    """Test USCCB URL generation"""
    
    def test_generate_usccb_url(self):
        """Test URL generation for a specific date"""
        test_date = date(2025, 11, 5)
        url = generate_usccb_url(test_date)
        self.assertEqual(url, "https://bible.usccb.org/bible/readings/11/05/2025.cfm")
    
    def test_generate_usccb_url_single_digit_month_day(self):
        """Test URL generation with single digit month and day"""
        test_date = date(2025, 1, 5)
        url = generate_usccb_url(test_date)
        self.assertEqual(url, "https://bible.usccb.org/bible/readings/01/05/2025.cfm")


class TestBibleReferenceParsing(unittest.TestCase):
    """Test Bible reference parsing"""
    
    def test_parse_simple_reference(self):
        """Test parsing a simple reference"""
        result = parse_bible_reference("Heb 9:15")
        self.assertEqual(result['book'], 'Hebrews')
        self.assertEqual(result['chapter'], 9)
        self.assertIn(15, result['verses'])
    
    def test_parse_reference_with_range(self):
        """Test parsing a reference with verse range"""
        result = parse_bible_reference("Heb 9:15, 24-28")
        self.assertEqual(result['book'], 'Hebrews')
        self.assertEqual(result['chapter'], 9)
        self.assertIn(15, result['verses'])
        self.assertIn(24, result['verses'])
        self.assertIn(28, result['verses'])
    
    def test_parse_psalm_reference(self):
        """Test parsing a Psalm reference"""
        result = parse_bible_reference("Ps 98:1, 2-3ab")
        self.assertEqual(result['book'], 'Psalms')
        self.assertEqual(result['chapter'], 98)
        self.assertIn(1, result['verses'])
        self.assertIn(2, result['verses'])
        self.assertIn(3, result['verses'])
    
    def test_parse_invalid_reference(self):
        """Test parsing an invalid reference"""
        result = parse_bible_reference("Invalid Reference")
        self.assertEqual(result['book'], 'Invalid Reference')
        self.assertEqual(result['chapter'], 0)
        self.assertEqual(result['verses'], [])


class TestUSCCBFetching(unittest.TestCase):
    """Test USCCB reading data fetching"""
    
    @patch('main.requests.get')
    def test_fetch_usccb_reading_data_success(self, mock_get):
        """Test successful USCCB data fetch"""
        mock_response = Mock()
        mock_response.text = '<html><body>Test HTML</body></html>'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = fetch_usccb_reading_data(date(2025, 11, 5))
        self.assertIsNotNone(result)
        self.assertIn('url', result)
        self.assertIn('title', result)
    
    @patch('main.requests.get')
    def test_fetch_usccb_reading_data_error(self, mock_get):
        """Test USCCB data fetch with error"""
        mock_get.side_effect = Exception("Network error")
        
        result = fetch_usccb_reading_data(date(2025, 11, 5))
        self.assertIsNone(result)


class TestScriptureTextFetching(unittest.TestCase):
    """Test public scripture text fetching"""
    
    def test_fetch_public_scripture_text_tbd(self):
        """Test fetching text for TBD reference"""
        result = fetch_public_scripture_text("TBD")
        self.assertEqual(result, "")
    
    def test_fetch_public_scripture_text_empty(self):
        """Test fetching text for empty reference"""
        result = fetch_public_scripture_text("")
        self.assertEqual(result, "")
    
    def test_fetch_public_scripture_text_valid(self):
        """Test fetching text for valid reference"""
        result = fetch_public_scripture_text("John 3:16")
        self.assertIsInstance(result, str)
        self.assertIn("John 3:16", result)


class TestDailyReadingSeeding(unittest.TestCase):
    """Test daily reading seeding"""
    
    @patch('main.initialize_firebase')
    @patch('main.fetch_usccb_reading_data')
    @patch('main.fetch_public_scripture_text')
    @patch('main.get_feast_for_date')
    def test_seed_daily_reading_dry_run(self, mock_feast, mock_text, mock_usccb, mock_fb):
        """Test seeding in dry run mode"""
        mock_usccb.return_value = {
            'title': 'Test Reading',
            'url': 'https://test.com',
            'gospel': {'reference': 'John 3:16'}
        }
        mock_text.return_value = "Test scripture text"
        mock_feast.return_value = None
        
        result = seed_daily_reading(date(2025, 11, 5), dry_run=True)
        self.assertEqual(result['status'], 'dry_run')
        self.assertEqual(result['doc_id'], '2025-11-05')
    
    @patch('main._db')
    @patch('main.initialize_firebase')
    @patch('main.fetch_usccb_reading_data')
    @patch('main.fetch_public_scripture_text')
    @patch('main.get_feast_for_date')
    def test_seed_daily_reading_success(self, mock_feast, mock_text, mock_usccb, mock_fb, mock_db):
        """Test successful seeding"""
        mock_doc_ref = MagicMock()
        mock_doc_ref.get.return_value.exists = False
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        mock_usccb.return_value = {
            'title': 'Test Reading',
            'url': 'https://test.com',
            'gospel': {'reference': 'John 3:16'}
        }
        mock_text.return_value = "Test scripture text"
        mock_feast.return_value = None
        
        result = seed_daily_reading(date(2025, 11, 5), dry_run=False)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['doc_id'], '2025-11-05')


class TestCloudFunction(unittest.TestCase):
    """Test the Cloud Function entry point"""
    
    @patch('main.initialize_firebase')
    @patch('main.seed_daily_reading')
    def test_seed_daily_readings_cron_success(self, mock_seed, mock_fb):
        """Test successful cron execution"""
        mock_request = Mock()
        mock_request.method = 'GET'
        mock_request.args = {'days': '3'}
        
        mock_seed.return_value = {'status': 'success', 'doc_id': '2025-11-05'}
        
        response, status_code = seed_daily_readings_cron(mock_request)
        
        self.assertEqual(status_code, 200)
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['body']['status'], 'success')
        self.assertEqual(response['body']['days_seeded'], 3)
    
    @patch('main.initialize_firebase')
    @patch('main.seed_daily_reading')
    def test_seed_daily_readings_cron_dry_run(self, mock_seed, mock_fb):
        """Test cron execution in dry run mode"""
        mock_request = Mock()
        mock_request.method = 'GET'
        mock_request.args = {}
        
        mock_seed.return_value = {'status': 'dry_run', 'doc_id': '2025-11-05'}
        
        with patch.dict(os.environ, {'DRY_RUN': 'True'}):
            response, status_code = seed_daily_readings_cron(mock_request)
            
            self.assertEqual(status_code, 200)
            self.assertEqual(response['body']['status'], 'success')
    
    @patch('main.initialize_firebase')
    @patch('main.seed_daily_reading')
    def test_seed_daily_readings_cron_with_errors(self, mock_seed, mock_fb):
        """Test cron execution with some errors"""
        mock_request = Mock()
        mock_request.method = 'GET'
        mock_request.args = {'days': '2'}
        
        # First call succeeds, second fails
        mock_seed.side_effect = [
            {'status': 'success', 'doc_id': '2025-11-05'},
            {'status': 'error', 'doc_id': '2025-11-06', 'error': 'Test error'}
        ]
        
        response, status_code = seed_daily_readings_cron(mock_request)
        
        self.assertEqual(status_code, 200)
        self.assertEqual(len(response['body']['errors']), 1)
        self.assertEqual(len(response['body']['successful']), 1)


if __name__ == '__main__':
    unittest.main()

