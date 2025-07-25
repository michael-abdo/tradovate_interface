#!/usr/bin/env python3
import os
import time
import subprocess
import pychrome
import signal
import sys
import json
import random
import threading

# Configuration
# Try to detect Chrome path based on OS
import platform

def find_chrome_path():
    """Find the Chrome executable path based on the operating system"""
    if platform.system() == "Darwin":  # macOS
        # Try multiple possible paths
        paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
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
        if os.path.exists(path):
            print(f"Found Chrome at: {path}")
            return path
    
    # If Chrome is not found in the common paths, try to find it in PATH
    try:
        import subprocess
        if platform.system() == "Windows":
            result = subprocess.run(["where", "chrome"], capture_output=True, text=True)
        else:
            result = subprocess.run(["which", "google-chrome"], capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            path = result.stdout.strip()
            print(f"Found Chrome in PATH: {path}")
            return path
    except Exception as e:
        print(f"Error finding Chrome in PATH: {e}")
    
    # Default path as fallback
    default_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    print(f"Chrome not found, will try with default path: {default_path}")
    return default_path

CHROME_PATH = find_chrome_path()
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
        self.login_check_interval = 30  # Check login status every 30 seconds
        self.login_monitor_thread = None
        self.is_running = False
        
    def start(self):
        """Start Chrome with remote debugging on the specified port"""
        self.process = start_chrome_with_debugging(self.port)
        if self.process:
            self.browser, self.tab = connect_to_chrome(self.port)
            if self.tab:
                # Check if we're on the login page and log in if needed
                self.check_and_login_if_needed()
                disable_alerts(self.tab)
                
                # Start a thread to monitor login status
                self.is_running = True
                self.login_monitor_thread = threading.Thread(
                    target=self.monitor_login_status,
                    daemon=True
                )
                self.login_monitor_thread.start()
                
                return True
        return False
    
    def check_and_login_if_needed(self):
        """Check if we're on the login page and log in if needed"""
        if not self.tab:
            return False
            
        try:
            # Check if we're on the login page by looking for the login form
            check_js = """
            (function() {
                // Check if we're on the login page
                const emailInput = document.getElementById("name-input");
                const passwordInput = document.getElementById("password-input");
                const loginButton = document.querySelector("button.MuiButton-containedPrimary");
                
                if (emailInput && passwordInput && loginButton) {
                    return "login_page";
                }
                
                // Check if we're on the account selection page
                const accessButtons = Array.from(document.querySelectorAll("button.tm"))
                    .filter(btn => 
                        btn.textContent.trim() === "Access Simulation" || 
                        btn.textContent.trim() === "Launch"
                    );
                    
                if (accessButtons.length > 0) {
                    return "account_selection";
                }
                
                // Check if we're logged in by looking for key elements
                const isLoggedIn = document.querySelector(".bar--heading") || 
                                document.querySelector(".app-bar--account-menu-button") ||
                                document.querySelector(".dashboard--container") ||
                                document.querySelector(".pane.account-selector");
                                
                return isLoggedIn ? "logged_in" : "unknown";
            })();
            """
            
            result = self.tab.Runtime.evaluate(expression=check_js)
            page_status = result.get("result", {}).get("value", "unknown")
            
            print(f"Current page status for {self.username}: {page_status}")
            
            if page_status == "login_page":
                print(f"Found login page for {self.username}, injecting login script")
                inject_login_script(self.tab, self.username, self.password)
                return True
                
            elif page_status == "account_selection":
                print(f"Found account selection page for {self.username}, clicking Access Simulation")
                access_js = """
                (function() {
                    const accessButtons = Array.from(document.querySelectorAll("button.tm"))
                        .filter(btn => 
                            btn.textContent.trim() === "Access Simulation" || 
                            btn.textContent.trim() === "Launch"
                        );
                        
                    if (accessButtons.length > 0) {
                        console.log("Clicking Access Simulation button");
                        accessButtons[0].click();
                        return true;
                    }
                    return false;
                })();
                """
                self.tab.Runtime.evaluate(expression=access_js)
                return True
                
            elif page_status == "logged_in":
                print(f"Already logged in for {self.username}")
                return False
                
            else:
                print(f"Unknown page status for {self.username}: {page_status}")
                return False
                
        except Exception as e:
            print(f"Error checking login status: {e}")
            return False
    
    def monitor_login_status(self):
        """Monitor login status and automatically log in again if logged out"""
        print(f"Starting login monitor for {self.username} on port {self.port}")
        
        while self.is_running and self.tab:
            try:
                # Sleep first to allow initial login to complete
                time.sleep(self.login_check_interval)
                
                if not self.is_running:
                    break
                    
                # Check and log in if needed
                self.check_and_login_if_needed()
                
            except Exception as e:
                print(f"Error in login monitor for {self.username}: {e}")
                time.sleep(5)  # Shorter sleep after error
        
        print(f"Login monitor stopped for {self.username}")
        
    def stop(self):
        """Stop this Chrome instance"""
        self.is_running = False
        
        # Stop the login monitor thread
        if self.login_monitor_thread and self.login_monitor_thread.is_alive():
            print(f"Stopping login monitor for {self.username}")
            self.login_monitor_thread.join(timeout=2)
            
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
    
    # Create a more robust login function with retries and DOM readiness checks
    auto_login_js = '''
    // More reliable way to set input values and trigger events
    function setInputValue(input, value) {
        const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
        nativeSetter.call(input, value);
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.dispatchEvent(new Event("change", { bubbles: true }));
    }
    
    // Main login function
    function login(username, password) {
        console.log("Auto login function executing for: " + username);
        
        // Wait for the DOM to fully load and login form to appear
        let retryCount = 0;
        const maxRetries = 10;
        
        function attemptLogin() {
            // Find login form elements
            const emailInput = document.getElementById("name-input");
            const passwordInput = document.getElementById("password-input");
            const loginButton = document.querySelector("button.MuiButton-containedPrimary");
            
            if (!emailInput || !passwordInput || !loginButton) {
                console.log("Login form not fully loaded yet, retry: " + retryCount);
                
                if (retryCount < maxRetries) {
                    retryCount++;
                    setTimeout(attemptLogin, 500);
                } else {
                    console.error("Input fields or login button not found after multiple attempts!");
                }
                return;
            }
            
            // Form is ready, fill and submit
            console.log("Login form found, filling credentials...");
            
            // Clear any existing values
            emailInput.value = "";
            passwordInput.value = "";
            
            // Set new values
            setInputValue(emailInput, username);
            setInputValue(passwordInput, password);
            
            // Give a moment for form validation to process
            setTimeout(() => {
                // Check if login button is enabled
                if (loginButton.disabled) {
                    console.log("Login button is disabled, waiting for form validation...");
                    // Wait and try again
                    setTimeout(() => {
                        const updatedLoginButton = document.querySelector("button.MuiButton-containedPrimary");
                        if (updatedLoginButton && !updatedLoginButton.disabled) {
                            console.log("Login button now enabled, clicking...");
                            updatedLoginButton.click();
                        } else {
                            console.error("Login button still disabled after waiting");
                        }
                    }, 1000);
                } else {
                    console.log("Clicking login button...");
                    loginButton.click();
                }
                
                // Start watching for the account selection page
                watchForAccountSelection();
            }, 500);
        }
        
        // Start the login attempt
        attemptLogin();
    }
    
    // Watch for account selection page and click the button when it appears
    function watchForAccountSelection() {
        console.log("Watching for account selection page...");
        
        let retryCount = 0;
        const maxRetries = 20; // Try for about 10 seconds
        const interval = setInterval(() => {
            const accessButtons = Array.from(document.querySelectorAll("button.tm"))
                .filter(btn => 
                    btn.textContent.trim() === "Access Simulation" || 
                    btn.textContent.trim() === "Launch"
                );
                
            if (accessButtons.length > 0) {
                console.log("Account selection page detected, clicking button...");
                clearInterval(interval);
                accessButtons[0].click();
            } else {
                retryCount++;
                if (retryCount >= maxRetries) {
                    console.log("Account selection page not found after multiple attempts");
                    clearInterval(interval);
                }
            }
        }, 500);
    }
    
    // Execute the login function with credentials
    const username = "%USERNAME%";
    const password = "%PASSWORD%";
    
    // Wait for the page to be ready
    console.log("Starting login process for: " + username);
    login(username, password);
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
        (function() {{
            // Remove existing test element if present
            const existingElement = document.getElementById('claude-test-element');
            if (existingElement) {{
                existingElement.remove();
            }}
            
            // Create new test element
            const testDiv = document.createElement('div');
            testDiv.id = 'claude-test-element';
            testDiv.style.position = 'fixed';
            testDiv.style.top = '10px';
            testDiv.style.right = '10px';
            testDiv.style.background = 'rgba(0, 128, 0, 0.8)';
            testDiv.style.color = 'white';
            testDiv.style.padding = '8px';
            testDiv.style.borderRadius = '4px';
            testDiv.style.fontSize = '12px';
            testDiv.style.fontFamily = 'Arial, sans-serif';
            testDiv.style.zIndex = '9999';
            testDiv.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
            testDiv.innerHTML = 'Auto-login active: {username}';
            
            // Add timestamp
            const timestamp = document.createElement('div');
            timestamp.style.fontSize = '10px';
            timestamp.style.marginTop = '4px';
            timestamp.style.opacity = '0.8';
            timestamp.innerText = new Date().toLocaleTimeString();
            testDiv.appendChild(timestamp);
            
            // Append to DOM
            document.body.appendChild(testDiv);
            console.log("Test element added to DOM");
            
            // Make it auto-update the timestamp every minute
            setInterval(() => {{
                const timestampElement = testDiv.querySelector('div');
                if (timestampElement) {{
                    timestampElement.innerText = new Date().toLocaleTimeString();
                }}
            }}, 60000);
        }})();
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
        credentials_path = os.path.join(project_root, 'config/credentials.json')
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
        
        # Start Chrome instances for each credential pair simultaneously using threads
        threads = []
        instances = []
        results = []  # To store results from threads
        
        def start_chrome_instance(idx, username, password):
            # Assign a unique port for each Chrome instance
            port = BASE_DEBUGGING_PORT + idx
            print(f"Preparing Chrome instance {idx+1} for {username} on port {port}")
            
            # Create and start a new Chrome instance
            instance = ChromeInstance(port, username, password)
            if instance.start():
                print(f"Chrome instance for {username} started successfully")
                results.append((instance, True))
            else:
                print(f"Failed to start Chrome instance for {username}")
                results.append((instance, False))
        
        # Create and start a thread for each credential pair
        for idx, (username, password) in enumerate(credentials):
            thread = threading.Thread(
                target=start_chrome_instance,
                args=(idx, username, password)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Process results
        for instance, success in results:
            if success:
                chrome_instances.append(instance)
        
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