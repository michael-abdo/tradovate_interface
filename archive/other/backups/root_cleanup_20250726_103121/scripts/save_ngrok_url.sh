#!/bin/bash

# Save and Reuse Ngrok URL (Free Version)
# This saves the current ngrok URL so you can reference it later

NGROK_URL_FILE="/Users/Mike/trading/current_ngrok_url.txt"
# BACKUP_URL_FILE="/Users/Mike/trading/tradovate_interface/current_ngrok_url.txt"  # Removed - using single file now

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

# Function to validate and auto-update URL
validate_and_update() {
    local saved_url=""
    if [ -f "$NGROK_URL_FILE" ]; then
        saved_url=$(cat "$NGROK_URL_FILE")
    fi
    
    local current_url=$(get_ngrok_url)
    
    if [ ! -z "$saved_url" ]; then
        echo "📋 Previously saved URL: $saved_url"
        
        # Check if saved URL is still active
        if curl -s -f "$saved_url" > /dev/null 2>&1; then
            echo "✅ Saved URL is still active"
            
            # Check if current running URL matches saved URL
            if [ "$saved_url" = "$current_url" ]; then
                echo "✅ Current ngrok matches saved URL"
            else
                echo "⚠️  Current ngrok URL differs from saved URL"
                echo "   Current: $current_url"
                echo "   Saved:   $saved_url"
            fi
        else
            echo "❌ Saved URL is no longer active"
            
            if [ ! -z "$current_url" ]; then
                echo "🔄 Auto-updating with current active URL: $current_url"
                save_url
            else
                echo "❌ No active ngrok tunnel found"
            fi
        fi
    else
        echo "📝 No saved URL found"
        if [ ! -z "$current_url" ]; then
            echo "🔄 Saving current active URL: $current_url"
            save_url
        fi
    fi
}

# Function to show saved URL
show_saved_url() {
    validate_and_update
}

# Function to get best available URL
get_best_url() {
    local saved_url=""
    if [ -f "$NGROK_URL_FILE" ]; then
        saved_url=$(cat "$NGROK_URL_FILE")
    fi
    
    local current_url=$(get_ngrok_url)
    
    # If saved URL is active, use it
    if [ ! -z "$saved_url" ] && curl -s -f "$saved_url" > /dev/null 2>&1; then
        echo "$saved_url"
    # Otherwise use current URL if available
    elif [ ! -z "$current_url" ]; then
        echo "$current_url"
    else
        echo ""
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
    "best")
        best_url=$(get_best_url)
        if [ ! -z "$best_url" ]; then
            echo "🎯 Best available URL: $best_url"
        else
            echo "❌ No available ngrok URL"
        fi
        ;;
    "validate")
        validate_and_update
        ;;
    *)
        echo "Usage: $0 {save|show|current|best|validate}"
        echo ""
        echo "Commands:"
        echo "  save      - Save current ngrok URL"
        echo "  show      - Show saved URL and auto-update if needed"
        echo "  current   - Show current active ngrok URL"
        echo "  best      - Get best available URL (saved or current)"
        echo "  validate  - Validate saved URL and auto-update if needed"
        echo ""
        echo "Examples:"
        echo "  $0 save     # Save current URL for later reference"
        echo "  $0 show     # Check saved URL and auto-update if stale"
        echo "  $0 best     # Get the best available URL right now"
        echo "  $0 validate # Validate and fix URL persistence"
        ;;
esac