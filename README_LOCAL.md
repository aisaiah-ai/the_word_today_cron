# Running The Word Today Service Locally

This guide explains how to run the service locally as an agent.

## Quick Start

### Run Once (Foreground)
```bash
./run_local_service.sh run
```

### Run as Background Agent
```bash
# Start the service in background
./run_local_service.sh start

# Check status
./run_local_service.sh status

# View logs
./run_local_service.sh logs

# Stop the service
./run_local_service.sh stop
```

## Alternative: Direct Python Execution

You can also run the service directly:

```bash
python3 the_word_today_service.py
```

## Setting Up a Cron Job (Scheduled Execution)

To run the service automatically at specific times (like the Cloud Scheduler), you can set up a local cron job:

### 1. Edit your crontab
```bash
crontab -e
```

### 2. Add scheduled jobs (example: 4 AM and 9 AM ET)
```bash
# Run at 4 AM Eastern Time (9 AM UTC)
0 9 * * * /Users/Shared/users/AMDShared/WorkspaceShared/python-cron/run_local_service.sh run >> /Users/Shared/users/AMDShared/WorkspaceShared/python-cron/cron.log 2>&1

# Run at 9 AM Eastern Time (2 PM UTC)
0 14 * * * /Users/Shared/users/AMDShared/WorkspaceShared/python-cron/run_local_service.sh run >> /Users/Shared/users/AMDShared/WorkspaceShared/python-cron/cron.log 2>&1
```

**Note:** Adjust the paths and times according to your timezone.

### 3. Verify cron job
```bash
crontab -l
```

## Service Files

- `the_word_today_service.py` - Main service script
- `run_local_service.sh` - Service runner script
- `service.log` - Service execution logs (created automatically)
- `service.pid` - Process ID file when running in background (created automatically)

## Monitoring

### Check if service is running
```bash
./run_local_service.sh status
```

### View recent logs
```bash
tail -n 50 service.log
```

### View live logs
```bash
./run_local_service.sh logs
```

## Troubleshooting

### Service won't start
- Check that Python 3 is installed: `python3 --version`
- Verify the service file exists: `ls -la the_word_today_service.py`
- Check for errors in the log file: `cat service.log`

### Background service not responding
- Check the process: `ps aux | grep the_word_today_service`
- Check logs: `cat service.log`
- Stop and restart: `./run_local_service.sh stop && ./run_local_service.sh start`

### Firebase credentials
Make sure the Firebase credentials path in `the_word_today_service.py` is correct:
```python
FIREBASE_CRED = "/Users/acthercop/.keys/aisaiahconferencefb-firebase-adminsdk-fbsvc-ed4ace66d0.json"
```

### YouTube API Key
Ensure the YouTube API key is valid in `the_word_today_service.py`:
```python
YOUTUBE_API_KEY = "AIzaSyDx8mRf6ssB1bUYhhL6bRBYI31CMavs1_4"
```

## Differences from Cloud Function

The local service (`the_word_today_service.py`) is a standalone script that:
- Runs directly with Python
- Uses hardcoded credentials (be careful with secrets!)
- Can be run manually or via cron
- Logs to console and file

The Cloud Function version (`the_word_today_cron/main.py`) is designed for:
- Google Cloud Functions (serverless)
- Environment variable-based configuration
- Automatic deployment via GitHub Actions
- Cloud Scheduler triggers

