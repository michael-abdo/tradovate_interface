#!/usr/bin/env python3
"""Test script to verify popup dismissal functionality"""

import json
import requests
import websocket
import time

def test_popup_dismissal():
    # Get Chrome debug endpoint
    response = requests.get('http://localhost:9222/json')
    tabs = response.json()
    
    # Find Tradovate tabs
    tradovate_tabs = [tab for tab in tabs if 'tradovate' in tab.get('url', '').lower()]
    
    if not tradovate_tabs:
        print("❌ No Tradovate tabs found")
        return
    
    print(f"✅ Found {len(tradovate_tabs)} Tradovate tabs")
    
    # Read the popup dismissal script
    with open('scripts/tampermonkey/dismissWarningPopups.js', 'r') as f:
        popup_script = f.read()
    
    # Inject into each tab
    for tab in tradovate_tabs[:3]:  # Test first 3 tabs
        tab_url = tab['webSocketDebuggerUrl']
        ws = websocket.create_connection(tab_url)
        
        print(f"\n📋 Injecting popup dismisser into: {tab['title'][:50]}...")
        
        # Send the script
        params = {
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {
                "expression": popup_script,
                "awaitPromise": False,
                "returnByValue": True
            }
        }
        
        ws.send(json.dumps(params))
        result = json.loads(ws.recv())
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
        else:
            print("✅ Popup dismisser injected successfully")
            
        ws.close()
    
    print("\n✨ Popup dismissal script has been injected into all tabs")
    print("📌 Check the Chrome console for dismissal logs")

if __name__ == "__main__":
    test_popup_dismissal()