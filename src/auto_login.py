#!/usr/bin/env python3
import os
import time
import subprocess
import pychrome
import signal
import sys
import json
import random

# Configuration
CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"  # Update for your OS
BASE_DEBUGGING_PORT = 9222
TRADOVATE_URL = "https://trader.tradovate.com"
WAIT_TIME = 5  # Seconds to wait for Chrome to start

class ChromeInstance:
    def __init__(self, port, username, password):
        self.port = port
        self.username = username
        self.password = password
        self.process = None
        self.browser = None
        self.tab = None
        
    def start(self):
        """Start Chrome with remote debugging on the specified port"""
        self.process = start_chrome_with_debugging(self.port)
        if self.process:
            self.browser, self.tab = connect_to_chrome(self.port)
            if self.tab:
                inject_login_script(self.tab, self.username, self.password)
                disable_alerts(self.tab)
                return True
        return False
        
    def stop(self):
        """Stop this Chrome instance"""
        if self.process:
            try:
                self.process.terminate()
                print(f"Chrome on port {self.port} terminated")
            except Exception as e:
                print(f"Error terminating Chrome: {e}")

def start_chrome_with_debugging(port):
    """Start a *new* isolated Chrome instance with remote-debugging enabled."""
    print(f"Starting Chrome with remote debugging on port {port}...")

    # Separate profile → forces a brand-new Chrome process even if one is already open
    profile_dir = os.path.join("/tmp", f"tradovate_debug_profile_{port}")
    os.makedirs(profile_dir, exist_ok=True)

    # Stop any Chrome that's already using this debugging port
    subprocess.run(["pkill", "-f", f"remote-debugging-port={port}"],
                   capture_output=True)

    chrome_cmd = [
        CHROME_PATH,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--new-window",
        "--disable-notifications",
        "--disable-popup-blocking",
        "--disable-infobars",
        "--disable-session-crashed-bubble",
        "--disable-save-password-bubble",
        TRADOVATE_URL,
    ]

    try:
        process = subprocess.Popen(chrome_cmd,
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
        print(f"Chrome started with PID: {process.pid}")
        return process
    except Exception as e:
        print(f"Failed to start Chrome: {e}")
        return None

def connect_to_chrome(port):
    """Connect to Chrome via remote debugging protocol"""
    print(f"Connecting to Chrome on port {port}...")
    browser = pychrome.Browser(url=f"http://localhost:{port}")
    
    # Make sure Chrome is ready
    time.sleep(WAIT_TIME)
    
    # List tabs and find the Tradovate tab
    tabs = browser.list_tab()
    target_tab = None
    
    for tab in tabs:
        try:
            tab.start()
            tab.Page.enable()
            result = tab.Runtime.evaluate(expression="document.location.href")
            url = result.get("result", {}).get("value", "")
            print(f"Found tab with URL: {url}")
            
            if "tradovate" in url:
                target_tab = tab
                print("Found Tradovate tab")
            else:
                tab.stop()
        except Exception as e:
            print(f"Error checking tab: {e}")
            tab.stop()
    
    if not target_tab:
        # If no Tradovate tab found, try to create one
        print("No Tradovate tab found, creating one...")
        target_tab = browser.new_tab(url=TRADOVATE_URL)
        target_tab.start()
        target_tab.Page.enable()
        time.sleep(3)  # Wait for page to load
    
    return browser, target_tab

def inject_login_script(tab, username, password):
    """Inject and execute auto-login script with specific credentials"""
    print(f"Injecting auto-login script for {username}...")
    
    # Create a simple login function
    auto_login_js = '''
    function login(username, password) {
        console.log("Auto login function executing...");
        
        const emailInput = document.getElementById("name-input");
        const passwordInput = document.getElementById("password-input");
        if (!emailInput || !passwordInput) {
            console.error("Input fields not found!");
            return;
        }
        
        const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
        nativeSetter.call(emailInput, username);
        emailInput.dispatchEvent(new Event("input", { bubbles: true }));
        nativeSetter.call(passwordInput, password);
        passwordInput.dispatchEvent(new Event("input", { bubbles: true }));
        
        setTimeout(() => {
            const loginButton = document.querySelector("button.MuiButton-containedPrimary");
            if (loginButton) {
                loginButton.click();
                console.log("Login button clicked");
            } else {
                console.error("Login button not found!");
            }
        }, 500);
    }
    
    function waitForAccessSimulation() {
        const interval = setInterval(() => {
            const buttons = document.querySelectorAll("button.tm");
            for (const btn of buttons) {
                if (btn.textContent.trim() === "Access Simulation" || btn.textContent.trim() === "Launch") {
                    console.log("Clicking Access Simulation button");
                    btn.click();
                    clearInterval(interval);
                    break;
                }
            }
        }, 500);
    }
    
    // Execute the login function with credentials
    const username = "%USERNAME%";
    const password = "%PASSWORD%";
    
    // Wait for the page to be ready
    setTimeout(() => {
        login(username, password);
        waitForAccessSimulation();
    }, 1000);
    '''
    
    # Replace placeholders with actual credentials
    auto_login_js = auto_login_js.replace('%USERNAME%', username)
    auto_login_js = auto_login_js.replace('%PASSWORD%', password)
    
    # Execute the login script in the browser
    try:
        print("Executing login script...")
        result = tab.Runtime.evaluate(expression=auto_login_js)
        
        # Append test element to DOM to verify script is running
        test_script = f'''
        const testDiv = document.createElement('div');
        testDiv.id = 'claude-test-element';
        testDiv.style.position = 'fixed';
        testDiv.style.top = '10px';
        testDiv.style.right = '10px';
        testDiv.style.background = 'red';
        testDiv.style.color = 'white';
        testDiv.style.padding = '10px';
        testDiv.style.zIndex = '9999';
        testDiv.innerHTML = 'Auto-login script connected: {username}';
        document.body.appendChild(testDiv);
        console.log("Test element added to DOM");
        '''
        tab.Runtime.evaluate(expression=test_script)
        
        print(f"Login script executed for {username}")
        return result
    except Exception as e:
        print(f"Error executing login script: {e}")
        return None

def disable_alerts(tab):
    """Disable browser alerts and confirmations"""
    disable_js = '''
    // Override window.alert
    window.alert = function(message) {
        console.log("Alert suppressed:", message);
        return true;
    };
    
    // Override window.confirm
    window.confirm = function(message) {
        console.log("Confirm suppressed:", message);
        return true;
    };
    
    // Override window.prompt
    window.prompt = function(message, defaultValue) {
        console.log("Prompt suppressed:", message);
        return defaultValue || "";
    };
    
    console.log("All browser alerts and confirmations have been disabled");
    '''
    
    try:
        tab.Runtime.evaluate(expression=disable_js)
        print("Disabled browser alerts and confirmations")
        return True
    except Exception as e:
        print(f"Error disabling alerts: {e}")
        return False

def load_credentials():
    """Load all credentials from JSON file, allowing duplicates"""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        credentials_path = os.path.join(project_root, 'credentials.json')
        print(f"Loading credentials from {credentials_path}")
        
        with open(credentials_path, 'r') as file:
            file_content = file.read()
            # Use json.loads instead of json.load to handle potential duplicate keys
            # When there are duplicate keys, the last occurrence will be used
            try:
                credentials = json.loads(file_content)
            except json.JSONDecodeError:
                print("Error parsing JSON, attempting custom parsing for duplicate keys")
                # Custom parsing for duplicate keys
                # This creates a list of all key-value pairs in the order they appear
                import re
                # Extract all key-value pairs including duplicates
                pairs = re.findall(r'"([^"]+)"\s*:\s*"([^"]+)"', file_content)
                credentials = dict()
                for username, password in pairs:
                    credentials[username] = password
        
        # Parse credentials into list of username/password pairs
        # For duplicate usernames, we'll include multiple instances
        cred_pairs = []
        
        if isinstance(credentials, dict):
            # Handle flat dictionary with username as keys
            # For duplicate usernames in the original JSON, we have lost them by now
            # since dictionaries can't have duplicate keys
            for username, password in credentials.items():
                if username and password:
                    # Count occurrences in the original file to handle duplicates
                    occurrences = file_content.count(f'"{username}"')
                    for _ in range(max(1, occurrences)):
                        cred_pairs.append((username, password))
                        
        elif isinstance(credentials, dict) and 'users' in credentials:
            # If it has a 'users' array
            for user in credentials['users']:
                username = user.get('username')
                password = user.get('password')
                if username and password:
                    cred_pairs.append((username, password))
                    
        if not cred_pairs:
            # Fallback to environment variables
            username = os.environ.get('TRADOVATE_USERNAME', '')
            password = os.environ.get('TRADOVATE_PASSWORD', '')
            if username and password:
                cred_pairs.append((username, password))
        
        print(f"Loaded {len(cred_pairs)} credential pairs (including duplicates)")            
        return cred_pairs
    except Exception as e:
        print(f"Error loading credentials from file: {e}")
        # Fall back to environment variables
        username = os.environ.get('TRADOVATE_USERNAME', '')
        password = os.environ.get('TRADOVATE_PASSWORD', '')
        if username and password:
            return [(username, password)]
        return []

def handle_exit(chrome_instances):
    """Clean up before exiting"""
    print("Cleaning up and exiting...")
    for instance in chrome_instances:
        instance.stop()

def main():
    chrome_instances = []
    
    try:
        # Load credential pairs
        credentials = load_credentials()
        if not credentials:
            print("No credentials found, exiting")
            return 1
            
        print(f"Found {len(credentials)} credential pair(s)")
        
        # Make sure any existing Chrome instances are stopped
        subprocess.run(["pkill", "-f", f"remote-debugging-port={BASE_DEBUGGING_PORT}"],
                      capture_output=True)
        
        # Start Chrome instances for each credential pair
        for idx, (username, password) in enumerate(credentials):
            # Assign a unique port for each Chrome instance
            port = BASE_DEBUGGING_PORT + idx
            print(f"\nStarting Chrome instance {idx+1} for {username} on port {port}")
            
            # Add a small delay between starting instances to avoid conflicts
            if idx > 0:
                time.sleep(1.5)
                
            # Create and start a new Chrome instance
            instance = ChromeInstance(port, username, password)
            if instance.start():
                chrome_instances.append(instance)
                print(f"Chrome instance for {username} started successfully")
            else:
                print(f"Failed to start Chrome instance for {username}")
        
        if not chrome_instances:
            print("Failed to start any Chrome instances, exiting")
            return 1
        
        # Print summary
        print(f"\n{len(chrome_instances)} Chrome instances running:")
        for idx, instance in enumerate(chrome_instances):
            print(f"  {idx+1}: {instance.username} - Port: {instance.port}")
            
        print("\nPress Ctrl+C to exit and close all Chrome instances")
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\nExiting due to user interrupt...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        handle_exit(chrome_instances)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())