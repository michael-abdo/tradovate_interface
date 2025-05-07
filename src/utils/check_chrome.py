#!/usr/bin/env python3
"""
Check Chrome executable path without actually starting Chrome
"""
import platform
import os
import subprocess

def find_chrome_path():
    """Find the Chrome executable path based on the operating system"""
    print(f"Operating system: {platform.system()}")
    
    if platform.system() == "Darwin":  # macOS
        # Try multiple possible paths
        paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
            # Add any other possible macOS Chrome paths here
        ]
    elif platform.system() == "Windows":
        # Try multiple possible paths
        paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Users\%USERNAME%\AppData\Local\Google\Chrome\Application\chrome.exe",
            # Add any other possible Windows Chrome paths here
        ]
    else:  # Linux and others
        # Try multiple possible paths
        paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
            # Add any other possible Linux Chrome paths here
        ]
    
    # Try each path
    for path in paths:
        print(f"Checking path: {path}")
        if os.path.exists(path):
            print(f"Found Chrome at: {path}")
            return path
        else:
            print(f"  - Not found")
    
    # If Chrome is not found in the common paths, try to find it in PATH
    try:
        print("Trying to find Chrome in PATH...")
        if platform.system() == "Windows":
            result = subprocess.run(["where", "chrome"], capture_output=True, text=True)
        else:
            result = subprocess.run(["which", "google-chrome"], capture_output=True, text=True)
            
            if result.returncode != 0:
                result = subprocess.run(["which", "chrome"], capture_output=True, text=True)
            
            if result.returncode != 0:
                result = subprocess.run(["which", "chromium"], capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            path = result.stdout.strip()
            print(f"Found Chrome in PATH: {path}")
            return path
        else:
            print(f"Chrome not found in PATH: {result.stderr}")
    except Exception as e:
        print(f"Error finding Chrome in PATH: {e}")
    
    # Default path as fallback
    default_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    print(f"Chrome not found, will try with default path: {default_path}")
    return default_path

if __name__ == "__main__":
    chrome_path = find_chrome_path()
    print(f"\nSelected Chrome path: {chrome_path}")
    
    # Try to get Chrome version without running it
    try:
        result = subprocess.run([chrome_path, "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Chrome version: {result.stdout.strip()}")
        else:
            print(f"Failed to get Chrome version: {result.stderr}")
    except Exception as e:
        print(f"Error getting Chrome version: {e}")