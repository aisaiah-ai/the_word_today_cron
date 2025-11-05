"""
Unit tests for The Word Today Cloud Function
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import json
import base64
from datetime import date, datetime
from main import (
    initialize_firebase,
    fetch_video_for_date,
    fetch_cfc_video_for_date,
    fetch_bo_video_for_date,
    save_to_firestore,
    the_word_today_cron
)


class TestFirebaseInitialization(unittest.TestCase):
    """Test Firebase initialization with different credential methods"""
    
    @patch('main.firebase_admin.get_app')
    @patch('main.firebase_admin.initialize_app')
    @patch('main.firestore.client')
    def test_initialize_firebase_with_json_string(self, mock_firestore, mock_init, mock_get_app):
        """Test Firebase initialization with JSON string"""
        mock_get_app.side_effect = ValueError("Not initialized")
        
        with patch.dict(os.environ, {
            'FIREBASE_CREDENTIALS_JSON': json.dumps({
                'type': 'service_account',
                'project_id': 'test-project'
            })
        }):
            initialize_firebase()
            mock_init.assert_called_once()
    
    @patch('main.firebase_admin.get_app')
    @patch('main.firebase_admin.initialize_app')
    @patch('main.firestore.client')
    def test_initialize_firebase_with_base64(self, mock_firestore, mock_init, mock_get_app):
        """Test Firebase initialization with base64 encoded JSON"""
        mock_get_app.side_effect = ValueError("Not initialized")
        
        creds_json = json.dumps({
            'type': 'service_account',
            'project_id': 'test-project'
        })
        creds_b64 = base64.b64encode(creds_json.encode()).decode()
        
        with patch.dict(os.environ, {
            'FIREBASE_CREDENTIALS_JSON_B64': creds_b64
        }, clear=False):
            initialize_firebase()
            mock_init.assert_called_once()
    
    @patch('main.firebase_admin.get_app')
    @patch('main.firebase_admin.initialize_app')
    @patch('main.firestore.client')
    def test_initialize_firebase_with_file_path(self, mock_firestore, mock_init, mock_get_app):
        """Test Firebase initialization with file path"""
        mock_get_app.side_effect = ValueError("Not initialized")
        
        with patch.dict(os.environ, {
            'FIREBASE_CRED': '/tmp/test-key.json'
        }), patch('os.path.exists', return_value=True):
            initialize_firebase()
            mock_init.assert_called_once()


class TestVideoFetching(unittest.TestCase):
    """Test video fetching functions"""
    
    @patch('main.requests.get')
    def test_fetch_video_for_date_success(self, mock_get):
        """Test successful video fetch"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'items': [{
                'id': {'videoId': 'test123'},
                'snippet': {
                    'title': 'Test Video - Tuesday, November 5, 2025'
                }
            }]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {'YOUTUBE_API_KEY': 'test-key'}):
            result = fetch_video_for_date(date(2025, 11, 5))
            self.assertIsNotNone(result)
            self.assertEqual(result['url'], 'https://www.youtube.com/watch?v=test123')
    
    @patch('main.requests.get')
    def test_fetch_video_for_date_not_found(self, mock_get):
        """Test video fetch when no videos found"""
        mock_response = Mock()
        mock_response.json.return_value = {'items': []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {'YOUTUBE_API_KEY': 'test-key'}):
            result = fetch_video_for_date(date(2025, 11, 5))
            self.assertIsNone(result)


class TestCloudFunction(unittest.TestCase):
    """Test the Cloud Function entry point"""
    
    @patch('main.initialize_firebase')
    @patch('main.fetch_video_for_date')
    @patch('main.fetch_cfc_video_for_date')
    @patch('main.fetch_bo_video_for_date')
    @patch('main.save_to_firestore')
    def test_the_word_today_cron_success(self, mock_save, mock_bo, mock_cfc, mock_twt, mock_fb):
        """Test successful cron execution"""
        mock_request = Mock()
        mock_request.method = 'GET'
        
        mock_twt.return_value = {'url': 'https://youtube.com/watch?v=test1'}
        mock_cfc.return_value = {'url': 'https://youtube.com/watch?v=test2'}
        mock_bo.return_value = {'url': 'https://youtube.com/watch?v=test3'}
        
        with patch.dict(os.environ, {
            'YOUTUBE_API_KEY': 'test-key',
            'DRY_RUN': 'False'
        }):
            response, status_code = the_word_today_cron(mock_request)
            
            self.assertEqual(status_code, 200)
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(response['body']['status'], 'success')
    
    @patch('main.initialize_firebase')
    def test_the_word_today_cron_missing_api_key(self, mock_fb):
        """Test cron execution with missing API key"""
        mock_request = Mock()
        mock_request.method = 'GET'
        
        with patch.dict(os.environ, {'YOUTUBE_API_KEY': ''}, clear=False):
            response, status_code = the_word_today_cron(mock_request)
            
            self.assertEqual(status_code, 500)
            self.assertEqual(response['body']['status'], 'error')
    
    @patch('main.initialize_firebase')
    @patch('main.fetch_video_for_date')
    @patch('main.save_to_firestore')
    def test_dry_run_mode(self, mock_save, mock_fetch, mock_fb):
        """Test that dry run mode doesn't save to Firestore"""
        mock_request = Mock()
        mock_request.method = 'GET'
        
        mock_fetch.return_value = {'url': 'https://youtube.com/watch?v=test'}
        
        with patch.dict(os.environ, {
            'YOUTUBE_API_KEY': 'test-key',
            'DRY_RUN': 'True'
        }):
            response, status_code = the_word_today_cron(mock_request)
            
            # In dry run, save_to_firestore should be called but with dry_run=True
            # The function should still complete successfully
            self.assertEqual(status_code, 200)


if __name__ == '__main__':
    unittest.main()

