#!/bin/bash
# Script to restart the webhook service
# This should be run with appropriate permissions

# Configuration
PROJECT_DIR="/Users/Mike/trading/tradovate_interface"
LOG_DIR="$PROJECT_DIR/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/webhook_restart_$TIMESTAMP.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Start the log
echo "=======================================" >> "$LOG_FILE"
echo "Webhook service restart initiated at $(date)" >> "$LOG_FILE"
echo "=======================================" >> "$LOG_FILE"

# Find and kill any existing webhook processes
echo "Finding existing webhook processes..." >> "$LOG_FILE"
PIDS=$(pgrep -f "python.*pinescript_webhook.py")

if [ -z "$PIDS" ]; then
    echo "No existing webhook processes found" >> "$LOG_FILE"
else
    echo "Found webhook processes: $PIDS" >> "$LOG_FILE"
    for PID in $PIDS; do
        echo "Killing process $PID..." >> "$LOG_FILE"
        kill -15 $PID
        sleep 2
        # Check if process still exists, kill forcefully if needed
        if ps -p $PID > /dev/null; then
            echo "Process $PID did not terminate gracefully, force killing..." >> "$LOG_FILE"
            kill -9 $PID
        fi
    done
    echo "All webhook processes terminated" >> "$LOG_FILE"
fi

# Kill any orphaned ngrok processes
echo "Finding existing ngrok processes..." >> "$LOG_FILE"
NGROK_PIDS=$(pgrep -f "ngrok")

if [ -z "$NGROK_PIDS" ]; then
    echo "No existing ngrok processes found" >> "$LOG_FILE"
else
    echo "Found ngrok processes: $NGROK_PIDS" >> "$LOG_FILE"
    for PID in $NGROK_PIDS; do
        echo "Killing ngrok process $PID..." >> "$LOG_FILE"
        kill -15 $PID
        sleep 1
        # Force kill if still running
        if ps -p $PID > /dev/null; then
            echo "Ngrok process $PID did not terminate gracefully, force killing..." >> "$LOG_FILE"
            kill -9 $PID
        fi
    done
    echo "All ngrok processes terminated" >> "$LOG_FILE"
fi

# Wait to ensure ports are freed
echo "Waiting for ports to be released..." >> "$LOG_FILE"
sleep 5

# Start the webhook service in the background
echo "Starting webhook service..." >> "$LOG_FILE"
cd "$PROJECT_DIR" || { echo "Failed to change to project directory" >> "$LOG_FILE"; exit 1; }

# Start the webhook service
nohup python3 -m src.pinescript_webhook > "$LOG_DIR/webhook_$TIMESTAMP.log" 2>&1 &
NEW_PID=$!

echo "Webhook service started with PID: $NEW_PID" >> "$LOG_FILE"
echo "Log file: $LOG_DIR/webhook_$TIMESTAMP.log" >> "$LOG_FILE"

# Check if service started successfully
sleep 5
if ps -p $NEW_PID > /dev/null; then
    echo "Webhook service is running" >> "$LOG_FILE"
    echo "Success: Webhook service restarted successfully" >> "$LOG_FILE"
    exit 0
else
    echo "ERROR: Webhook service failed to start" >> "$LOG_FILE"
    exit 1
fi