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

# Note: Chrome Process Monitor was moved to archive with tradovate_interface
# Disable watchdog functionality for now
print("Warning: Chrome Process Monitor not available. Running without watchdog protection.")
WATCHDOG_AVAILABLE = False

# Import connection health monitoring and Chrome Communication Framework
from src.utils.chrome_stability import ChromeStabilityMonitor
from src.utils.chrome_communication import safe_evaluate, OperationType

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
BASE_DEBUGGING_PORT = 9223  # Start from 9223 to avoid 9222 (Rule #0)
TRADOVATE_URL = "https://trader.tradovate.com"
WAIT_TIME = 5  # Seconds to wait for Chrome to start

class ChromeInstance:
    def __init__(self, port, username, password, account_name=None, process_monitor=None):
        self.port = port
        self.username = username
        self.password = password
        self.account_name = account_name or f"Account_{port-BASE_DEBUGGING_PORT+1}"
        self.process_monitor = process_monitor
        self.process = None
        self.browser = None
        self.tab = None
        self.login_check_interval = 30  # Check login status every 30 seconds
        self.login_monitor_thread = None
        self.is_running = False
        
    def start(self):
        """Start Chrome with remote debugging on the specified port"""
        # SAFETY: Never start Chrome on port 9222 - protected port
        if self.port == 9222:
            print(f"REFUSING to start Chrome on protected port 9222 for {self.account_name}")
            return False
            
        # Register for startup monitoring before launching Chrome
        if self.process_monitor and WATCHDOG_AVAILABLE:
            print(f"Registering {self.account_name} for startup monitoring on port {self.port}")
            if not self.process_monitor.register_for_startup_monitoring(self.account_name, self.port):
                print(f"Failed to register startup monitoring for {self.account_name}")
            else:
                # Update startup phase to LAUNCHING
                self.process_monitor.update_startup_phase(
                    self.account_name, 
                    StartupPhase.LAUNCHING, 
                    f"About to launch Chrome for {self.username}"
                )
        
        # Launch Chrome process
        print(f"Starting Chrome for {self.account_name} ({self.username}) on port {self.port}")
        self.process = start_chrome_with_debugging(self.port)
        
        if self.process:
            # Update startup phase with PID
            if self.process_monitor and WATCHDOG_AVAILABLE:
                self.process_monitor.update_startup_phase(
                    self.account_name,
                    StartupPhase.CONNECTING,
                    f"Chrome process started with PID {self.process.pid}",
                    pid=self.process.pid
                )
            
            # Connect to Chrome debugging protocol
            print(f"Connecting to Chrome for {self.account_name}")
            self.browser, self.tab = connect_to_chrome(self.port)
            
            if self.tab:
                # Update startup phase to LOADING
                if self.process_monitor and WATCHDOG_AVAILABLE:
                    self.process_monitor.update_startup_phase(
                        self.account_name,
                        StartupPhase.LOADING,
                        f"Connected to Chrome, tab available for {self.username}"
                    )
                
                # Check if we're on the login page and log in if needed
                login_attempted = self.check_and_login_if_needed()
                
                # Update startup phase to AUTHENTICATING
                if self.process_monitor and WATCHDOG_AVAILABLE:
                    phase_detail = f"Login attempted: {login_attempted}" if login_attempted else "Already authenticated"
                    self.process_monitor.update_startup_phase(
                        self.account_name,
                        StartupPhase.AUTHENTICATING,
                        phase_detail
                    )
                
                # Disable browser alerts
                disable_alerts(self.tab)
                
                # Validate startup completion
                startup_valid = True
                if self.process_monitor and WATCHDOG_AVAILABLE:
                    startup_valid = self.process_monitor.validate_startup_completion(self.account_name)
                    if startup_valid:
                        self.process_monitor.update_startup_phase(
                            self.account_name,
                            StartupPhase.READY,
                            f"Startup validation successful for {self.username}"
                        )
                        print(f"Startup monitoring completed successfully for {self.account_name}")
                    else:
                        print(f"Startup validation failed for {self.account_name}")
                
                # Start login monitoring thread
                self.is_running = True
                self.login_monitor_thread = threading.Thread(
                    target=self.monitor_login_status,
                    daemon=True
                )
                self.login_monitor_thread.start()
                
                return startup_valid
            else:
                # Failed to connect to tab
                if self.process_monitor and WATCHDOG_AVAILABLE:
                    self.process_monitor.update_startup_phase(
                        self.account_name,
                        StartupPhase.CONNECTING,
                        f"Failed to connect to Chrome tab for {self.username}"
                    )
                print(f"Failed to connect to Chrome tab for {self.account_name}")
        else:
            # Failed to start Chrome process
            if self.process_monitor and WATCHDOG_AVAILABLE:
                self.process_monitor.update_startup_phase(
                    self.account_name,
                    StartupPhase.LAUNCHING,
                    f"Failed to start Chrome process for {self.username}"
                )
            print(f"Failed to start Chrome process for {self.account_name}")
            
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
            
            # Use safe_evaluate to check page status
            result = safe_evaluate(
                tab=self.tab,
                js_code=check_js,
                operation_type=OperationType.IMPORTANT,
                description=f"Check page status for {self.username}"
            )
            page_status = result.value if result.success else "unknown"
            
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
                # Use safe_evaluate to handle access request
                result = safe_evaluate(
                    tab=self.tab,
                    js_code=access_js,
                    operation_type=OperationType.CRITICAL,
                    description=f"Handle access request for {self.username}"
                )
                if result.success:
                    return True
                else:
                    print(f"Failed to handle access request for {self.username}: {result.error}")
                    return False
                
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
    
    def check_connection_health(self) -> dict:
        """Check the health of this Chrome instance connection"""
        health_status = {
            'account': self.username,
            'port': self.port,
            'healthy': False,
            'checks': {},
            'errors': []
        }
        
        try:
            # Check if process is still running
            if self.process and self.process.poll() is None:
                health_status['checks']['process_running'] = True
            else:
                health_status['checks']['process_running'] = False
                health_status['errors'].append("Chrome process not running")
                return health_status
            
            # Check if browser connection is available
            if self.browser:
                try:
                    tabs = self.browser.list_tab()
                    health_status['checks']['browser_responsive'] = True
                    health_status['checks']['tab_count'] = len(tabs)
                except Exception as e:
                    health_status['checks']['browser_responsive'] = False
                    health_status['errors'].append(f"Browser not responsive: {e}")
                    return health_status
            else:
                health_status['checks']['browser_responsive'] = False
                health_status['errors'].append("No browser connection")
                return health_status
            
            # Check if tab is accessible
            if self.tab:
                try:
                    # Test JavaScript execution using safe_evaluate
                    result = safe_evaluate(
                        tab=self.tab,
                        js_code="1 + 1",
                        operation_type=OperationType.NON_CRITICAL,
                        description=f"Test JavaScript execution for {self.username}"
                    )
                    if result.success and result.value == 2:
                        health_status['checks']['javascript_execution'] = True
                    else:
                        health_status['checks']['javascript_execution'] = False
                        health_status['errors'].append("JavaScript execution failed")
                except Exception as e:
                    health_status['checks']['javascript_execution'] = False
                    health_status['errors'].append(f"Tab not accessible: {e}")
                    return health_status
            else:
                health_status['checks']['javascript_execution'] = False
                health_status['errors'].append("No tab available")
                return health_status
            
            # Check Tradovate application status
            try:
                app_check_js = """
                ({
                    url: window.location.href,
                    authenticated: !document.querySelector('#name-input'),
                    tradingReady: typeof window.autoTrade === 'function'
                })
                """
                # Use safe_evaluate to check application status
                result = safe_evaluate(
                    tab=self.tab,
                    js_code=app_check_js,
                    operation_type=OperationType.NON_CRITICAL,
                    description=f"Check application status for {self.username}"
                )
                app_status = result.value if result.success else {}
                
                health_status['checks']['tradovate_loaded'] = "tradovate.com" in app_status.get('url', '')
                health_status['checks']['authenticated'] = app_status.get('authenticated', False)
                health_status['checks']['trading_ready'] = app_status.get('tradingReady', False)
                
                # Overall health assessment
                critical_checks = ['process_running', 'browser_responsive', 'javascript_execution']
                health_status['healthy'] = all(health_status['checks'].get(check, False) for check in critical_checks)
                
            except Exception as e:
                health_status['errors'].append(f"Application check failed: {e}")
        
        except Exception as e:
            health_status['errors'].append(f"Health check exception: {e}")
        
        return health_status
        
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

    # SAFETY: NEVER kill port 9222 - only kill trading ports 9223+
    if port != 9222:
        subprocess.run(["pkill", "-f", f"remote-debugging-port={port}"],
                       capture_output=True)
    else:
        print(f"SAFETY: Skipping cleanup for protected port {port}")

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
        # GPU-related flags to prevent crashes
        "--disable-gpu-sandbox",
        "--disable-software-rasterizer",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-gpu-compositing",
        "--enable-features=SharedArrayBuffer",
        "--disable-web-security",
        "--disable-features=IsolateOrigins,site-per-process",
        # Additional stability flags
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-features=TranslateUI",
        "--disable-ipc-flooding-protection",
        # Memory and performance flags
        "--max_old_space_size=4096",
        "--js-flags=--max-old-space-size=4096",
        "--force-color-profile=srgb",
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
            # Use safe_evaluate to get URL
            result = safe_evaluate(
                tab=tab,
                js_code="document.location.href",
                operation_type=OperationType.NON_CRITICAL,
                description="Get tab URL for validation"
            )
            url = result.value if result.success else ""
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
        # Use safe_evaluate to execute login script
        result = safe_evaluate(
            tab=tab,
            js_code=auto_login_js,
            operation_type=OperationType.CRITICAL,
            description=f"Execute login script for {username}"
        )
        
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
        # Use safe_evaluate to execute test script
        safe_evaluate(
            tab=tab,
            js_code=test_script,
            operation_type=OperationType.NON_CRITICAL,
            description=f"Execute test script for {username}"
        )
        
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
        # Use safe_evaluate to disable alerts
        result = safe_evaluate(
            tab=tab,
            js_code=disable_js,
            operation_type=OperationType.NON_CRITICAL,
            description="Disable browser alerts and confirmations"
        )
        if result.success:
            print("Disabled browser alerts and confirmations")
            return True
        else:
            print(f"Failed to disable alerts: {result.error}")
            return False
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

def handle_exit(chrome_instances, process_monitor=None, health_monitor=None):
    """Clean up before exiting"""
    print("Cleaning up and exiting...")
    
    # Stop process monitor first if available
    if process_monitor:
        print("Stopping Chrome Process Monitor...")
        process_monitor.stop_monitoring()
    
    # Stop health monitoring first
    if health_monitor:
        print("Stopping connection health monitoring...")
        if hasattr(health_monitor, 'stop_health_monitoring'):
            health_monitor.stop_health_monitoring()
        else:
            print("Warning: health_monitor missing stop_health_monitoring method")
    
    # Stop Chrome instances
    for instance in chrome_instances:
        instance.stop()

def main():
    chrome_instances = []
    process_monitor = None
    health_monitor = None
    
    try:
        # Load credential pairs
        credentials = load_credentials()
        if not credentials:
            print("No credentials found, exiting")
            return 1
            
        print(f"Found {len(credentials)} credential pair(s)")
        
        # Initialize Chrome Process Monitor if available
        if WATCHDOG_AVAILABLE:
            print("Initializing Chrome Process Monitor...")
            process_monitor = ChromeProcessMonitor()
            process_monitor.start_monitoring()
            print("Chrome Process Monitor started")
        
        # SAFETY: NEVER kill port 9222 - only kill ports 9223+
        # Make sure any existing Chrome instances on trading ports are stopped
        for port in [9223, 9224, 9225, 9226, 9227, 9228, 9229, 9230]:
            subprocess.run(["pkill", "-f", f"remote-debugging-port={port}"],
                          capture_output=True)
        
        # Start Chrome instances for each credential pair simultaneously using threads
        threads = []
        instances = []
        results = []  # To store results from threads
        
        def start_chrome_instance(idx, username, password):
            # Assign a unique port for each Chrome instance
            port = BASE_DEBUGGING_PORT + idx
            account_name = f"Account_{idx+1}_{username.split('@')[0]}"  # Use email prefix for account name
            print(f"Preparing Chrome instance {idx+1} for {username} on port {port}")
            
            # Create and start a new Chrome instance with startup monitoring
            instance = ChromeInstance(
                port=port, 
                username=username, 
                password=password,
                account_name=account_name,
                process_monitor=process_monitor
            )
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
                
                # Register with regular process monitor if available (startup monitoring should have transitioned)
                if WATCHDOG_AVAILABLE and process_monitor and instance.process:
                    process_monitor.register_process(
                        account_name=instance.account_name,
                        pid=instance.process.pid,
                        port=instance.port,
                        profile_dir=f"/tmp/tradovate_debug_profile_{instance.port}"
                    )
                    print(f"Registered {instance.account_name} with regular Process Monitor")
        
        if not chrome_instances:
            print("Failed to start any Chrome instances, exiting")
            return 1
        
        # Initialize connection health monitoring
        print("Initializing connection health monitoring...")
        health_monitor = ChromeStabilityMonitor(log_dir="logs/connection_health")
        
        # Register each Chrome instance with health monitor
        for instance in chrome_instances:
            if hasattr(health_monitor, 'register_connection'):
                health_monitor.register_connection(instance.account_name, instance.port)
                print(f"Registered {instance.account_name} for health monitoring on port {instance.port}")
            else:
                print(f"Warning: health_monitor missing register_connection method")
        
        # Start health monitoring
        if hasattr(health_monitor, 'start_health_monitoring'):
            health_monitor.start_health_monitoring()
        else:
            print("Warning: health_monitor missing start_health_monitoring method")
        print("Connection health monitoring started")
        
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
        handle_exit(chrome_instances, process_monitor, health_monitor)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())