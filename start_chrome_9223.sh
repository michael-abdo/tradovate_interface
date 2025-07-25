#!/bin/bash
# Safe Chrome launcher for port 9223 - COMPLETELY SEPARATE from port 9222

# Chrome executable path for macOS
CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Unique data directory for this instance (completely separate from 9222)
USER_DATA_DIR="/tmp/chrome-debug-9223"

# Clean up any old data
rm -rf "$USER_DATA_DIR"

echo "Starting Chrome on port 9223 (separate from 9222)..."
echo "User data directory: $USER_DATA_DIR"

# Launch Chrome with debugging on port 9223
"$CHROME_PATH" \
  --remote-debugging-port=9223 \
  --remote-allow-origins=* \
  --no-first-run \
  --no-default-browser-check \
  --user-data-dir="$USER_DATA_DIR" \
  --disable-blink-features=AutomationControlled \
  --disable-features=VizDisplayCompositor \
  --password-store=basic \
  --use-mock-keychain \
  --disable-extensions \
  --disable-plugins \
  --window-size=1200,800 \
  "https://trader.tradovate.com/welcome" &

CHROME_PID=$!
echo "Chrome started on port 9223 with PID: $CHROME_PID"
echo "This is COMPLETELY SEPARATE from your port 9222 Chrome instance"
echo "Press Ctrl+C to stop this Chrome instance"

# Wait for Chrome to start
sleep 3

# Verify it's running
if ps -p $CHROME_PID > /dev/null; then
    echo "✅ Chrome successfully started on port 9223"
    echo "📱 You can connect Python to port 9223 safely"
    echo "🔗 Debug URL: http://localhost:9223"
else
    echo "❌ Chrome failed to start"
    exit 1
fi

# Keep script running until user stops it
wait $CHROME_PID