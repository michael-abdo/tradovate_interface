#!/usr/bin/env python3
import os
import sys
import time
import threading
import json

# Add project root to path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.auto_login import start_chrome_with_debugging, connect_to_chrome

# Configuration
BASE_DEBUGGING_PORT = 9223

def load_credentials():
    """Load credentials directly from JSON file"""
    config_dir = os.path.join(project_root, 'config')
    credentials_file = os.path.join(config_dir, 'credentials.json')
    
    if not os.path.exists(credentials_file):
        print(f"Credentials file not found: {credentials_file}")
        return []
    
    try:
        with open(credentials_file, 'r') as f:
            creds_dict = json.load(f)
            return list(creds_dict.items())
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return []

def test_chrome_startup(idx, username, password, results):
    """Test starting a single Chrome instance"""
    port = BASE_DEBUGGING_PORT + idx
    print(f"Thread {idx}: Starting Chrome for {username} on port {port}")
    
    try:
        # Start Chrome process
        process = start_chrome_with_debugging(port)
        if not process:
            print(f"Thread {idx}: Failed to start Chrome process")
            results.append((idx, False, "Failed to start Chrome process"))
            return
        
        print(f"Thread {idx}: Chrome started with PID {process.pid}")
        
        # Wait for Chrome to be ready
        time.sleep(5)
        
        # Test connection
        browser, tab = connect_to_chrome(port)
        if not tab:
            print(f"Thread {idx}: Failed to connect to Chrome")
            results.append((idx, False, "Failed to connect to Chrome"))
            return
            
        print(f"Thread {idx}: Connected to Chrome successfully")
        
        # Test page status
        try:
            result = tab.Runtime.evaluate(expression="document.location.href")
            url = result.get("result", {}).get("value", "")
            print(f"Thread {idx}: Current URL: {url}")
            
            # Test login page detection
            check_js = '''
            (function() {
                const emailInput = document.getElementById("name-input");
                const passwordInput = document.getElementById("password-input");
                const loginButton = document.querySelector("button.MuiButton-containedPrimary");
                
                if (emailInput && passwordInput && loginButton) {
                    return "login_page";
                }
                return "other";
            })();
            '''
            result = tab.Runtime.evaluate(expression=check_js)
            page_status = result.get("result", {}).get("value", "unknown")
            print(f"Thread {idx}: Page status: {page_status}")
            
            results.append((idx, True, f"Success - URL: {url}, Status: {page_status}"))
            
        except Exception as e:
            print(f"Thread {idx}: Error testing page: {e}")
            results.append((idx, False, f"Page test error: {e}"))
            
    except Exception as e:
        print(f"Thread {idx}: Exception: {e}")
        import traceback
        traceback.print_exc()
        results.append((idx, False, f"Exception: {e}"))

def main():
    print("Testing Chrome threading startup...")
    
    # Load credentials
    credentials = load_credentials()
    if not credentials:
        print("No credentials found")
        return
        
    print(f"Found {len(credentials)} credential pairs")
    
    # Clean up any existing Chrome instances
    for i in range(len(credentials)):
        port = BASE_DEBUGGING_PORT + i
        os.system(f"pkill -f 'remote-debugging-port={port}' 2>/dev/null")
    
    time.sleep(2)
    
    # Start threads
    threads = []
    results = []
    
    print(f"Starting {len(credentials)} threads...")
    for idx, (username, password) in enumerate(credentials):
        print(f"Creating thread {idx} for {username}")
        thread = threading.Thread(
            target=test_chrome_startup,
            args=(idx, username, password, results)
        )
        threads.append(thread)
        thread.start()
        print(f"Thread {idx} started")
    
    # Wait for completion
    print("Waiting for threads to complete...")
    for idx, thread in enumerate(threads):
        print(f"Joining thread {idx}...")
        thread.join()
        print(f"Thread {idx} completed")
    
    print(f"\nResults ({len(results)} total):")
    for idx, success, message in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"Thread {idx}: {status} - {message}")

if __name__ == "__main__":
    main()