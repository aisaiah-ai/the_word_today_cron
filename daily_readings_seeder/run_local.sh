#!/bin/bash

# Local Service Runner for Daily Readings Seeder
# This script runs the seeder locally for testing

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SERVICE_FILE="$SCRIPT_DIR/main.py"
TEST_FILE="$SCRIPT_DIR/test_local.py"
LOG_FILE="$SCRIPT_DIR/seeder.log"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed or not in PATH${NC}"
    exit 1
fi

# Function to run the test script
run_test() {
    echo -e "${GREEN}🚀 Running Daily Readings Seeder Test${NC}"
    echo "Timestamp: $(date)" | tee -a "$LOG_FILE"
    echo "----------------------------------------" | tee -a "$LOG_FILE"
    
    cd "$SCRIPT_DIR"
    python3 "$TEST_FILE" 2>&1 | tee -a "$LOG_FILE"
    
    EXIT_CODE=$?
    echo "----------------------------------------" | tee -a "$LOG_FILE"
    echo "Exit code: $EXIT_CODE at $(date)" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    
    return $EXIT_CODE
}

# Function to seed specific dates
seed_dates() {
    DAYS=${1:-14}
    echo -e "${GREEN}🌱 Seeding daily readings for $DAYS days${NC}"
    
    cd "$SCRIPT_DIR"
    
    # Create a simple test script
    python3 << EOF
import os
import sys
from datetime import date, timedelta
from main import seed_daily_reading

start_date = date.today()
dry_run = os.environ.get('DRY_RUN', '').lower() != 'true'

for i in range($DAYS):
    target_date = start_date + timedelta(days=i)
    print(f"Seeding {target_date}...")
    result = seed_daily_reading(target_date, dry_run=dry_run)
    print(f"  Result: {result['status']}")

print(f"\n✅ Seeded $DAYS days of readings")
EOF
}

# Main command handler
case "${1:-test}" in
    test)
        run_test
        ;;
    seed)
        DAYS=${2:-14}
        seed_dates "$DAYS"
        ;;
    logs)
        if [ -f "$LOG_FILE" ]; then
            tail -f "$LOG_FILE"
        else
            echo -e "${YELLOW}⚠️  Log file not found: $LOG_FILE${NC}"
        fi
        ;;
    *)
        echo "Usage: $0 {test|seed [days]|logs}"
        echo ""
        echo "Commands:"
        echo "  test     - Run the test script (default)"
        echo "  seed     - Seed readings for specified days (default: 14)"
        echo "  logs     - Tail the log file"
        echo ""
        echo "Examples:"
        echo "  $0 test           # Run tests"
        echo "  $0 seed 30       # Seed 30 days"
        echo "  $0 seed           # Seed 14 days (default)"
        echo "  DRY_RUN=True $0 seed  # Test without writing"
        exit 1
        ;;
esac

