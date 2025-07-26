#!/bin/bash

# Save and Reuse Ngrok URL (Free Version)
# This saves the current ngrok URL so you can reference it later

NGROK_URL_FILE="/Users/Mike/trading/tradovate_interface/current_ngrok_url.txt"

# Function to get current ngrok URL
get_ngrok_url() {
    curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data['tunnels']:
        print(data['tunnels'][0]['public_url'])
    else:
        print('')
except:
    print('')
" 2>/dev/null
}

# Function to save ngrok URL
save_url() {
    local url=$(get_ngrok_url)
    if [ ! -z "$url" ]; then
        echo "$url" > "$NGROK_URL_FILE"
        echo "✅ Saved ngrok URL: $url"
        echo "📝 Saved to: $NGROK_URL_FILE"
    else
        echo "❌ No ngrok tunnel found"
    fi
}

# Function to show saved URL
show_saved_url() {
    if [ -f "$NGROK_URL_FILE" ]; then
        local saved_url=$(cat "$NGROK_URL_FILE")
        echo "📋 Previously saved URL: $saved_url"
        
        # Check if it's still active
        if curl -s -f "$saved_url" > /dev/null 2>&1; then
            echo "✅ URL is still active"
        else
            echo "❌ URL is no longer active"
        fi
    else
        echo "📝 No saved URL found"
    fi
}

# Main logic
case "$1" in
    "save")
        save_url
        ;;
    "show")
        show_saved_url
        ;;
    "current")
        current_url=$(get_ngrok_url)
        if [ ! -z "$current_url" ]; then
            echo "🔗 Current ngrok URL: $current_url"
        else
            echo "❌ No active ngrok tunnel"
        fi
        ;;
    *)
        echo "Usage: $0 {save|show|current}"
        echo ""
        echo "Commands:"
        echo "  save     - Save current ngrok URL"
        echo "  show     - Show previously saved URL and check if active"
        echo "  current  - Show current active ngrok URL"
        echo ""
        echo "Examples:"
        echo "  $0 save     # Save current URL for later reference"
        echo "  $0 show     # Check if saved URL still works"
        echo "  $0 current  # Get current active URL"
        ;;
esac