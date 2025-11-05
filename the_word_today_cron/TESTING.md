# Testing Guide for The Word Today Cloud Function

## Running Tests Locally

### Prerequisites
1. Install dependencies:
   ```bash
   cd the_word_today_cron
   pip install -r requirements.txt
   ```

2. Set environment variables (optional for unit tests):
   ```bash
   export YOUTUBE_API_KEY=your_key
   export FIREBASE_CRED=/path/to/firebase-key.json
   # OR
   export FIREBASE_CREDENTIALS_JSON='{"type":"service_account",...}'
   ```

### Unit Tests
Run the unit test suite:
```bash
cd the_word_today_cron
python -m pytest test_main.py -v
```

### Local Function Test
Test the Cloud Function locally with actual API calls:
```bash
cd the_word_today_cron
python test_local.py
```

Or make it executable and run directly:
```bash
chmod +x test_local.py
./test_local.py
```

### Running with Functions Framework
Test the function using Google Functions Framework (simulates Cloud Functions):
```bash
cd the_word_today_cron
pip install functions-framework

# Set environment variables
export YOUTUBE_API_KEY=your_key
export FIREBASE_CRED=/path/to/firebase-key.json
export DRY_RUN=True

# Run the function locally
functions-framework --target=the_word_today_cron --port=8080

# In another terminal, test it:
curl http://localhost:8080
```

## Test Coverage

### Unit Tests (`test_main.py`)
- ✅ Firebase initialization with different credential methods
- ✅ Video fetching functions
- ✅ Cloud Function entry point
- ✅ Error handling
- ✅ Dry run mode

### Local Test (`test_local.py`)
- ✅ Environment variable validation
- ✅ Firebase initialization
- ✅ Full function execution
- ✅ Response validation

## Continuous Integration

Tests run automatically in GitHub Actions before deployment:
- Unit tests execute before deployment
- If tests fail, deployment is skipped

## Troubleshooting

### Tests fail with "Module not found"
```bash
pip install -r requirements.txt
```

### Firebase initialization fails
- Set `FIREBASE_CRED` environment variable pointing to your Firebase key file
- Or set `FIREBASE_CREDENTIALS_JSON` with the JSON content
- Or use Application Default Credentials (for GCP environments)

### YouTube API errors
- Ensure `YOUTUBE_API_KEY` is set
- Check API quota limits
- Verify API key has correct permissions

### Dry run mode
Set `DRY_RUN=True` to test without writing to Firestore:
```bash
export DRY_RUN=True
python test_local.py
```

