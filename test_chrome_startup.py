#!/usr/bin/env python3
"""
Test if Chrome startup is working
"""
import subprocess
import sys
import time
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.auto_login import start_chrome_with_debugging, CHROME_PATH

print("Testing Chrome startup...")
print(f"Chrome path: {CHROME_PATH}")
print(f"Chrome exists: {os.path.exists(CHROME_PATH)}")

# Test starting Chrome on port 9223
port = 9223
print(f"\nAttempting to start Chrome on port {port}...")

process = start_chrome_with_debugging(port)
if process:
    print(f"✓ Chrome started with PID: {process.pid}")
    print("Waiting 5 seconds to let it fully start...")
    time.sleep(5)
    
    # Check if it's still running
    if process.poll() is None:
        print("✓ Chrome is still running")
        
        # Try to connect
        try:
            import pychrome
            browser = pychrome.Browser(url=f"http://localhost:{port}")
            tabs = browser.list_tab()
            print(f"✓ Connected to Chrome, found {len(tabs)} tabs")
        except Exception as e:
            print(f"✗ Failed to connect: {e}")
        
        # Clean up
        print("\nTerminating Chrome...")
        process.terminate()
        process.wait()
        print("✓ Chrome terminated")
    else:
        print(f"✗ Chrome exited with code: {process.returncode}")
else:
    print("✗ Failed to start Chrome")

print("\nTest complete!")