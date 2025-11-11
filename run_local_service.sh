#!/bin/bash

# Local Service Runner for The Word Today Service
# This script runs the service locally and can be used with cron or as a background agent

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SERVICE_FILE="$SCRIPT_DIR/the_word_today_service.py"
LOG_FILE="$SCRIPT_DIR/service.log"
PID_FILE="$SCRIPT_DIR/service.pid"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if service file exists
if [ ! -f "$SERVICE_FILE" ]; then
    echo -e "${RED}❌ Service file not found: $SERVICE_FILE${NC}"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed or not in PATH${NC}"
    exit 1
fi

# Function to run the service
run_service() {
    echo -e "${GREEN}🚀 Starting The Word Today Service${NC}"
    echo "Timestamp: $(date)" | tee -a "$LOG_FILE"
    echo "----------------------------------------" | tee -a "$LOG_FILE"
    
    cd "$SCRIPT_DIR"
    python3 "$SERVICE_FILE" 2>&1 | tee -a "$LOG_FILE"
    
    EXIT_CODE=$?
    echo "----------------------------------------" | tee -a "$LOG_FILE"
    echo "Exit code: $EXIT_CODE at $(date)" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    
    return $EXIT_CODE
}

# Function to check if service is running
check_status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Service is running (PID: $PID)${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  PID file exists but process is not running${NC}"
            rm -f "$PID_FILE"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️  Service is not running${NC}"
        return 1
    fi
}

# Function to start service in background
start_background() {
    if check_status > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Service is already running${NC}"
        return 1
    fi
    
    echo -e "${GREEN}🚀 Starting service in background...${NC}"
    nohup bash "$0" run > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    sleep 1
    
    if check_status > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Service started successfully (PID: $(cat $PID_FILE))${NC}"
        echo "Logs: $LOG_FILE"
    else
        echo -e "${RED}❌ Failed to start service${NC}"
        return 1
    fi
}

# Function to stop service
stop_service() {
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}⚠️  Service is not running${NC}"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}🛑 Stopping service (PID: $PID)...${NC}"
        kill "$PID"
        sleep 2
        
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${RED}⚠️  Process still running, force killing...${NC}"
            kill -9 "$PID"
        fi
        
        rm -f "$PID_FILE"
        echo -e "${GREEN}✅ Service stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  Process not found, cleaning up PID file${NC}"
        rm -f "$PID_FILE"
    fi
}

# Main command handler
case "${1:-run}" in
    run)
        run_service
        ;;
    start)
        start_background
        ;;
    stop)
        stop_service
        ;;
    status)
        check_status
        ;;
    logs)
        if [ -f "$LOG_FILE" ]; then
            tail -f "$LOG_FILE"
        else
            echo -e "${YELLOW}⚠️  Log file not found: $LOG_FILE${NC}"
        fi
        ;;
    *)
        echo "Usage: $0 {run|start|stop|status|logs}"
        echo ""
        echo "Commands:"
        echo "  run     - Run the service once (foreground)"
        echo "  start   - Start the service in background"
        echo "  stop    - Stop the background service"
        echo "  status  - Check if service is running"
        echo "  logs    - Tail the service log file"
        exit 1
        ;;
esac

