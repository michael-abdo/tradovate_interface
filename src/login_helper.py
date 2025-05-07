#!/usr/bin/env python3
import pychrome
import time
import json
import os
import sys
from src.auto_login import inject_login_script, disable_alerts

def login_to_existing_chrome(port=9222, username=None, password=None, tradovate_url="https://trader.tradovate.com"):
    """
    Login to Tradovate on an existing Chrome instance running with remote debugging.
    
    Args:
        port: The debugging port Chrome is running on
        username: Username for login (if None, will load from credentials.json)
        password: Password for login (if None, will load from credentials.json)
        tradovate_url: URL to check for (defaults to https://trader.tradovate.com)
        
    Returns:
        tuple: (success, tab_handle, browser) - Boolean success status, tab handle, and browser connection if successful
    """
    # If credentials not provided, try to load from file
    if not (username and password):
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            credentials_path = os.path.join(project_root, 'credentials.json')
            print(f"Loading credentials from {credentials_path}")
            
            with open(credentials_path, 'r') as file:
                credentials = json.load(file)
                if isinstance(credentials, dict):
                    # Get first credential from the dictionary
                    username = list(credentials.keys())[0]
                    password = credentials[username]
                    print(f"Using credentials for user: {username}")
        except Exception as e:
            print(f"Error loading credentials: {e}")
            return False, None, None
    
    # Connect to Chrome
    try:
        print(f"Connecting to Chrome on port {port}...")
        browser = pychrome.Browser(url=f"http://localhost:{port}")
        tabs = browser.list_tab()
        
        print(f"Found {len(tabs)} tabs")
        
        # Find or create Tradovate tab
        target_tab = None
        for tab in tabs:
            try:
                tab.start()
                tab.Page.enable()
                result = tab.Runtime.evaluate(expression="document.location.href")
                url = result.get("result", {}).get("value", "")
                print(f"Tab URL: {url}")
                
                if "tradovate" in url.lower():
                    target_tab = tab
                    print("Found Tradovate tab")
                    break
                else:
                    tab.stop()
            except Exception as e:
                print(f"Error checking tab: {e}")
                tab.stop()
        
        if not target_tab:
            print("No Tradovate tab found. Creating a new tab...")
            try:
                target_tab = browser.new_tab(url=tradovate_url)
                target_tab.start()
                target_tab.Page.enable()
                print("New tab created and navigated to Tradovate")
                # Wait for page to load
                time.sleep(3)
            except Exception as e:
                print(f"Error creating new tab: {e}")
                return False, None, None
        
        # Inject login script and disable alerts
        print(f"Injecting login script for {username}...")
        inject_login_script(target_tab, username, password)
        disable_alerts(target_tab)
        
        # Add a visual indicator that we're using the helper
        visual_indicator = """
        setTimeout(() => {
            const helperDiv = document.createElement('div');
            helperDiv.id = 'login-helper-indicator';
            helperDiv.style.position = 'fixed';
            helperDiv.style.bottom = '10px';
            helperDiv.style.right = '10px';
            helperDiv.style.background = 'green';
            helperDiv.style.color = 'white';
            helperDiv.style.padding = '5px 10px';
            helperDiv.style.borderRadius = '5px';
            helperDiv.style.zIndex = '9999';
            helperDiv.style.opacity = '0.7';
            helperDiv.innerHTML = 'Login Helper Active';
            document.body.appendChild(helperDiv);
        }, 2000);
        """
        target_tab.Runtime.evaluate(expression=visual_indicator)
        
        print("Login script injected successfully")
        return True, target_tab, browser
    
    except Exception as e:
        print(f"Error connecting to Chrome or logging in: {e}")
        return False, None, None

def wait_for_element(tab, selector, timeout=10, visible=True):
    """
    Wait for an element to appear in the DOM and optionally be visible
    
    Args:
        tab: The tab handle
        selector: CSS selector for the element
        timeout: Maximum time to wait in seconds
        visible: Whether to also check if the element is visible
        
    Returns:
        bool: True if element was found (and visible if required), False otherwise
    """
    print(f"Waiting for element: {selector}")
    check_script = f"""
    function checkElement() {{
        const element = document.querySelector('{selector}');
        if (!element) return false;
        
        if ({str(visible).lower()}) {{
            const rect = element.getBoundingClientRect();
            const style = window.getComputedStyle(element);
            return rect.width > 0 && 
                   rect.height > 0 && 
                   style.display !== 'none' && 
                   style.visibility !== 'hidden' &&
                   style.opacity !== '0';
        }}
        return true;
    }}
    checkElement();
    """
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            result = tab.Runtime.evaluate(expression=check_script)
            if result.get("result", {}).get("value", False):
                print(f"Element found: {selector}")
                return True
        except Exception as e:
            print(f"Error checking for element: {e}")
        
        time.sleep(0.5)
    
    print(f"Timed out waiting for element: {selector}")
    return False

def execute_js(tab, script):
    """Execute JavaScript in the tab and return the result"""
    try:
        result = tab.Runtime.evaluate(expression=script)
        return result.get("result", {})
    except Exception as e:
        print(f"Error executing script: {e}")
        return None

def main():
    """Simple CLI to test the login helper"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Login to Tradovate via Chrome DevTools Protocol")
    parser.add_argument("--port", type=int, default=9222, help="Chrome debugging port")
    parser.add_argument("--username", help="Tradovate username (optional, will use credentials.json if not provided)")
    parser.add_argument("--password", help="Tradovate password (optional)")
    args = parser.parse_args()
    
    success, tab, browser = login_to_existing_chrome(
        port=args.port,
        username=args.username,
        password=args.password
    )
    
    if success:
        print("Successfully logged in")
        
        # Wait for either the login button or dashboard to appear
        if wait_for_element(tab, ".desktop-dashboard", timeout=15) or wait_for_element(tab, ".login-button", timeout=5):
            print("Login page or dashboard loaded successfully")
        
        # Keep browser open
        print("Press Ctrl+C to exit")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Exiting...")
    else:
        print("Login failed")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())