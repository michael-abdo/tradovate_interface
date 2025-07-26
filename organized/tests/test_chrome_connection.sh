#!/usr/bin/env bash

# Test script for Chrome remote debugging connection
# This script verifies Chrome DevTools connectivity and can launch Chrome
# with remote debugging if needed for testing

CHROME_PATH=""
DEBUG_PORT=9222
PROJECT_ROOT=$(dirname "$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)")
LOG_DIR="$PROJECT_ROOT/logs/tests"

# Determine Chrome path based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    CHROME_PATH=$(which google-chrome 2>/dev/null || which chromium-browser 2>/dev/null || which chromium 2>/dev/null)
elif [[ "$OSTYPE" == "msys"* || "$OSTYPE" == "cygwin"* ]]; then
    # Windows via GitBash/Cygwin
    CHROME_PATH="/c/Program Files/Google/Chrome/Application/chrome.exe"
    if [ ! -f "$CHROME_PATH" ]; then
        CHROME_PATH="/c/Program Files (x86)/Google/Chrome/Application/chrome.exe"
    fi
fi

# Create logs directory
mkdir -p "$LOG_DIR"

# Function to check if Chrome is running with remote debugging
check_chrome_connection() {
    echo "Testing Chrome remote debugging connection on port $DEBUG_PORT..."
    connection_result=$(curl -s "http://localhost:$DEBUG_PORT/json" | python -m json.tool 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$connection_result" ]; then
        echo "✅ Chrome connection successful!"
        echo "$connection_result"
        return 0
    else
        echo "❌ Chrome connection failed!"
        return 1
    fi
}

# Function to start Chrome with remote debugging
start_chrome_for_testing() {
    local timestamp=$(date "+%Y%m%d_%H%M%S")
    local profile_dir="/tmp/chrome_test_profile_$timestamp"
    
    # Kill any existing Chrome instances using this port
    if [[ "$OSTYPE" == "msys"* || "$OSTYPE" == "cygwin"* ]]; then
        # Windows
        taskkill //F //IM chrome.exe //T > /dev/null 2>&1
    else
        # macOS/Linux
        pkill -f "remote-debugging-port=$DEBUG_PORT" > /dev/null 2>&1
    fi
    
    echo "Starting Chrome with remote debugging on port $DEBUG_PORT..."
    echo "Chrome path: $CHROME_PATH"
    echo "Profile directory: $profile_dir"
    
    # Launch Chrome with remote debugging
    "$CHROME_PATH" \
        --remote-debugging-port=$DEBUG_PORT \
        --user-data-dir="$profile_dir" \
        --no-first-run \
        --no-default-browser-check \
        --disable-popup-blocking \
        --disable-translate \
        --disable-notifications \
        --disable-sync \
        --window-size=1200,800 \
        about:blank > "$LOG_DIR/chrome_launch_$timestamp.log" 2>&1 &
    
    CHROME_PID=$!
    echo "Chrome started with PID $CHROME_PID"
    
    # Wait for Chrome to initialize
    for i in {1..10}; do
        sleep 1
        echo "Waiting for Chrome to initialize... ($i/10)"
        if check_chrome_connection; then
            echo "Chrome is ready for testing!"
            echo "You can now run the tests that require a Chrome instance"
            echo ""
            echo "When finished, terminate this Chrome instance by:"
            echo "1. Closing all Chrome windows manually, or"
            echo "2. Running: kill $CHROME_PID"
            echo ""
            echo "Press Ctrl+C to exit this script (Chrome will continue running)"
            echo "Logs available at: $LOG_DIR/chrome_launch_$timestamp.log"
            return 0
        fi
    done
    
    echo "❌ Chrome failed to initialize properly"
    return 1
}

# Main script logic
if [ "$1" == "start" ]; then
    start_chrome_for_testing
    # Keep the script running to maintain the Chrome instance
    while true; do
        sleep 1
    done
else
    # Just check the connection
    check_chrome_connection
fi