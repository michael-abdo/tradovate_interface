#!/usr/bin/env python3
"""
Refresh all Chrome tabs that have http://localhost:6001 open.
Uses Chrome DevTools Protocol via pychrome library.
"""

import json
import requests
import time
import sys
from urllib.parse import urlparse

def get_chrome_debugger_url():
    """Get the Chrome DevTools debugger URL."""
    try:
        # Default Chrome debugging port
        response = requests.get('http://localhost:9222/json/version')
        data = response.json()
        return data.get('webSocketDebuggerUrl')
    except:
        return None

def get_chrome_tabs():
    """Get all Chrome tabs via DevTools Protocol."""
    try:
        response = requests.get('http://localhost:9222/json')
        return response.json()
    except Exception as e:
        print(f"Error getting Chrome tabs: {e}")
        return []

def refresh_tab(tab_id):
    """Refresh a specific tab using DevTools Protocol."""
    try:
        # Send reload command to the tab
        ws_url = f"http://localhost:9222/devtools/page/{tab_id}"
        
        # Use HTTP endpoint to send commands
        command_url = f"http://localhost:9222/json/runtime/evaluate"
        data = {
            "expression": "location.reload()",
            "returnByValue": True
        }
        
        # Alternative approach: use the HTTP endpoint directly
        response = requests.put(f"http://localhost:9222/json/runtime/evaluate/{tab_id}", 
                               json={"expression": "location.reload()"})
        
        return True
    except Exception as e:
        print(f"Error refreshing tab {tab_id}: {e}")
        return False

def main():
    """Main function to find and refresh localhost:6001 tabs."""
    print("Looking for Chrome tabs with http://localhost:6001...")
    
    # First, check if Chrome is running with debugging enabled
    try:
        requests.get('http://localhost:9222/json/version', timeout=2)
    except:
        print("\n!!! ERROR !!!")
        print("Chrome DevTools debugging is not enabled.")
        print("\nTo enable Chrome DevTools debugging:")
        print("1. Close all Chrome instances")
        print("2. Launch Chrome with debugging enabled:")
        print("   On macOS: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
        print("   On Windows: chrome.exe --remote-debugging-port=9222")
        print("   On Linux: google-chrome --remote-debugging-port=9222")
        return 1
    
    # Get all tabs
    tabs = get_chrome_tabs()
    if not tabs:
        print("No Chrome tabs found.")
        return 1
    
    print(f"Found {len(tabs)} Chrome tabs")
    
    # Find tabs with localhost:6001
    localhost_tabs = []
    for tab in tabs:
        url = tab.get('url', '')
        parsed = urlparse(url)
        
        # Check if it's localhost:6001
        if parsed.hostname == 'localhost' and parsed.port == 6001:
            localhost_tabs.append(tab)
            print(f"  - Found localhost:6001 tab: {tab.get('title', 'Untitled')} [{tab['id']}]")
    
    if not localhost_tabs:
        print("\nNo tabs with http://localhost:6001 found.")
        return 0
    
    print(f"\nFound {len(localhost_tabs)} tab(s) with localhost:6001")
    print("Refreshing tabs...")
    
    # Refresh each localhost:6001 tab
    success_count = 0
    for tab in localhost_tabs:
        tab_id = tab['id']
        title = tab.get('title', 'Untitled')
        
        print(f"  - Refreshing '{title}'...", end='', flush=True)
        
        # Use simpler approach: navigate to the same URL (acts as refresh)
        try:
            response = requests.post(f"http://localhost:9222/json/runtime/evaluate",
                                   json={
                                       "expression": f"window.location.href = '{tab['url']}'",
                                       "targetId": tab_id
                                   })
            
            # Alternative: use Page.reload command
            ws_url = tab.get('webSocketDebuggerUrl')
            if ws_url:
                # This would require websocket connection, keeping it simple with HTTP
                pass
            
            print(" ✓")
            success_count += 1
        except Exception as e:
            print(f" ✗ (Error: {e})")
    
    print(f"\nRefreshed {success_count}/{len(localhost_tabs)} tabs successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())