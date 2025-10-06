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
import logging
from . import chrome_logger
import tempfile
from pathlib import Path
from .utils.core import (
    get_project_root,
    find_chrome_executable,
    load_json_config,
    setup_logging
)

# Set up logger for this module using centralized logging setup
logger = setup_logging(level="INFO")

# Configuration

# Global variables for logging (set by start_all.py)
log_directory = None
terminal_callback = None
register_chrome_logger = None

# Global variables for robust cleanup coordination
shutdown_event = threading.Event()
cleanup_status = {
    'instances_total': 0,
    'instances_stopped': 0,
    'threads_total': 0,
    'threads_stopped': 0,
    'cleanup_complete': False
}
cleanup_lock = threading.Lock()
cleanup_status_file = None

def set_log_directory(directory):
    """Set the log directory for Chrome console logging"""
    global log_directory
    log_directory = directory
    print(f"Log directory set to: {log_directory}")

def set_terminal_callback(callback):
    """Set the terminal callback for real-time Chrome console output"""
    global terminal_callback
    terminal_callback = callback
    print("Terminal callback set for real-time console output")

def set_register_chrome_logger(register_func):
    """Set the function to register ChromeLoggers with start_all.py"""
    global register_chrome_logger
    register_chrome_logger = register_func
    print("ChromeLogger registration function set")

def update_cleanup_status(key, value):
    """Thread-safe update of cleanup status"""
    global cleanup_status
    with cleanup_lock:
        cleanup_status[key] = value
        write_cleanup_status()

def write_cleanup_status():
    """Write cleanup status to file for parent process monitoring"""
    if cleanup_status_file:
        try:
            with open(cleanup_status_file, 'w') as f:
                json.dump(cleanup_status, f)
        except Exception as e:
            logger.error(f"Error writing cleanup status: {e}")

def init_cleanup_coordination():
    """Initialize cleanup coordination with parent process"""
    global cleanup_status_file
    # Create a temporary file for cleanup status
    temp_dir = tempfile.gettempdir()
    cleanup_status_file = os.path.join(temp_dir, f"tradovate_cleanup_{os.getpid()}.json")
    logger.info(f"Cleanup status file: {cleanup_status_file}")
    write_cleanup_status()
    return cleanup_status_file

def create_log_file_path(username, port):
    """Create a unique log file path for a Chrome instance"""
    if not log_directory:
        return None
    return os.path.join(log_directory, f"chrome_console_{username}_{port}.log")

CHROME_PATH = find_chrome_executable()
BASE_DEBUGGING_PORT = 9223  # Changed from 9222 to protect that port
TRADOVATE_URL = "https://trader.tradovate.com"
WAIT_TIME = 5  # Seconds to wait for Chrome to start

# Global variables for logging (set by start_all.py)
log_directory = None
terminal_callback = None
register_chrome_logger = None

def set_log_directory(directory):
    """Set the log directory for Chrome console logging"""
    global log_directory
    log_directory = directory
    logger.info(f"Log directory set to: {log_directory}")

def set_terminal_callback(callback):
    """Set the terminal callback for real-time Chrome console output"""
    global terminal_callback
    terminal_callback = callback
    logger.info("Terminal callback set for real-time console output")

def set_register_chrome_logger(register_func):
    """Set the function to register ChromeLoggers with start_all.py"""
    global register_chrome_logger
    register_chrome_logger = register_func
    logger.info("ChromeLogger registration function set")

def create_log_file_path(username, port):
    """Create a unique log file path for a Chrome instance"""
    if not log_directory:
        return None
    return os.path.join(log_directory, f"chrome_console_{username}_{port}.log")


class ChromeProcessManager:
    """Manages Chrome process lifecycle with consistent launch and cleanup."""
    
    def __init__(self, chrome_path: str = None):
        """Initialize ChromeProcessManager.
        
        Args:
            chrome_path: Path to Chrome executable. If None, will auto-detect.
        """
        self.chrome_path = chrome_path or find_chrome_executable()
        self.processes = {}  # port -> subprocess.Popen
        self.lock = threading.Lock()
    
    def launch_chrome(self, port: int, user_data_dir: str = None) -> subprocess.Popen:
        """Launch Chrome with remote debugging enabled.
        
        Args:
            port: Remote debugging port number
            user_data_dir: Optional Chrome user data directory
            
        Returns:
            subprocess.Popen: The Chrome process
            
        Raises:
            RuntimeError: If Chrome fails to start
        """
        with self.lock:
            # Check if already running on this port
            if port in self.processes and self.processes[port].poll() is None:
                logger.warning(f"Chrome already running on port {port}")
                return self.processes[port]
            
            # Build Chrome command
            chrome_cmd = [
                self.chrome_path,
                f'--remote-debugging-port={port}',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-popup-blocking',
                '--disable-blink-features=AutomationControlled'
            ]
            
            # Check if optimization mode is enabled
            if os.environ.get('OPTIMIZE_MODE') == 'True':
                # Add CPU optimization flags
                chrome_cmd.extend([
                    # Enable GPU acceleration
                    '--enable-gpu-rasterization',
                    '--enable-zero-copy',
                    '--enable-accelerated-video-decode',
                    '--ignore-gpu-blocklist',
                    
                    # Enable power saving
                    '--enable-features=HighEfficiencyModeAvailable,BatterySaverModeAvailable',
                    '--force-fieldtrials=HighEfficiencyModeAvailable/Enabled',
                    
                    # Enable background throttling
                    '--enable-background-timer-throttling',
                    '--enable-backgrounding-occluded-windows',
                    
                    # Reduce memory
                    '--max-old-space-size=512',
                    '--memory-pressure-off',
                    
                    # Disable unnecessary features
                    '--disable-background-networking',
                    '--disable-component-update',
                    '--disable-domain-reliability'
                ])
            else:
                # Use original performance flags
                chrome_cmd.extend([
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ])
            ]
            
            # Add user data directory if specified
            if user_data_dir:
                chrome_cmd.append(f'--user-data-dir={user_data_dir}')
            else:
                # Use a temporary directory for this instance
                temp_dir = tempfile.mkdtemp(prefix=f'chrome_{port}_')
                chrome_cmd.append(f'--user-data-dir={temp_dir}')
            
            # Launch Chrome
            try:
                logger.info(f"Launching Chrome on port {port}")
                process = subprocess.Popen(
                    chrome_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                # Store process reference
                self.processes[port] = process
                
                # Give Chrome time to start
                time.sleep(2)
                
                # Verify process is still running
                if process.poll() is not None:
                    raise RuntimeError(f"Chrome exited immediately with code {process.poll()}")
                
                return process
                
            except Exception as e:
                logger.error(f"Failed to launch Chrome on port {port}: {e}")
                raise RuntimeError(f"Chrome launch failed: {e}")
    
    def stop_chrome(self, port: int, timeout: int = 5) -> bool:
        """Stop Chrome process on specified port.
        
        Args:
            port: Remote debugging port number
            timeout: Seconds to wait for graceful shutdown
            
        Returns:
            bool: True if successfully stopped
        """
        with self.lock:
            if port not in self.processes:
                return True
            
            process = self.processes[port]
            if process.poll() is not None:
                # Already stopped
                del self.processes[port]
                return True
            
            try:
                # Try graceful termination first
                logger.info(f"Stopping Chrome on port {port}")
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    # Force kill if needed
                    logger.warning(f"Chrome on port {port} didn't stop gracefully, forcing")
                    process.kill()
                    process.wait()
                
                del self.processes[port]
                return True
                
            except Exception as e:
                logger.error(f"Error stopping Chrome on port {port}: {e}")
                return False
    
    def stop_all(self, timeout: int = 5) -> None:
        """Stop all managed Chrome processes.
        
        Args:
            timeout: Seconds to wait for each process to stop
        """
        ports = list(self.processes.keys())
        for port in ports:
            self.stop_chrome(port, timeout)
    
    def cleanup(self) -> None:
        """Clean up all Chrome processes and resources."""
        self.stop_all()
        self.processes.clear()


# Global ChromeProcessManager instance
chrome_manager = ChromeProcessManager()


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
        self.stop_event = threading.Event()  # Instance-specific stop event
        self.chrome_logger = None
        self.log_file_path = None
    
    def set_log_file_path(self, log_file_path):
        """Set the log file path for Chrome console logging"""
        self.log_file_path = log_file_path
        
    def start(self):
        """Start Chrome with remote debugging on the specified port"""
        self.process = start_chrome_with_debugging(self.port)
        if self.process:
            self.browser, self.tab = connect_to_chrome(self.port)
            if self.tab:
                # Initialize Chrome logger if log file path is set
                if self.log_file_path:
                    try:
                        logger.info(f"Initializing Chrome logger for {self.username}...")
                        self.chrome_logger = chrome_logger.create_logger(self.tab, self.log_file_path, terminal_callback)
                        if self.chrome_logger:
                            logger.info(f"Chrome logger started for {self.username} -> {self.log_file_path}")
                            # Register with start_all.py for centralized cleanup
                            if register_chrome_logger:
                                register_chrome_logger(self.chrome_logger)
                        else:
                            logger.error(f"Failed to start Chrome logger for {self.username}")
                    except Exception as e:
                        logger.error(f"Error initializing Chrome logger for {self.username}: {e}")
                        self.chrome_logger = None
                
                # Check if we're on the login page and log in if needed
                self.check_and_login_if_needed()
                disable_alerts(self.tab)
                
                # Start a thread to monitor login status
                self.login_monitor_thread = threading.Thread(
                    target=self.monitor_login_status,
                    daemon=False  # Not daemon so we can track it properly
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
                        btn.textContent.trim() === "Launch" ||
                        btn.textContent.trim() === "Start Simulated Trading"
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
            
            logger.debug(f"Current page status for {self.username}: {page_status}")
            
            if page_status == "login_page":
                logger.info(f"Found login page for {self.username}, injecting login script")
                inject_login_script(self.tab, self.username, self.password)
                return True
                
            elif page_status == "account_selection":
                logger.info(f"Found account selection page for {self.username}, clicking Access Simulation")
                access_js = """
                (function() {
                    const accessButtons = Array.from(document.querySelectorAll("button.tm"))
                        .filter(btn => 
                            btn.textContent.trim() === "Access Simulation" || 
                            btn.textContent.trim() === "Launch" ||
                            btn.textContent.trim() === "Start Simulated Trading"
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
                logger.info(f"Already logged in for {self.username}")
                # Inject autorisk management script if not already loaded
                self.inject_autorisk_script()
                return False
                
            else:
                logger.warning(f"Unknown page status for {self.username}: {page_status}")
                return False
                
        except Exception as e:
            error_msg = str(e)
            # Check for WebSocket disconnection - this should terminate the monitor thread
            if ("Connection to remote host was lost" in error_msg or 
                "WebSocketConnectionClosedException" in error_msg or
                "Tab has been stopped" in error_msg):
                logger.info(f"WebSocket connection lost for {self.username}, terminating monitor thread")
                self.stop_event.set()  # Signal thread to exit gracefully
                return None  # Special return value to indicate terminal condition
            else:
                logger.error(f"Error checking login status: {e}")
                return False
    
    def monitor_login_status(self):
        """Monitor login status and automatically log in again if logged out"""
        logger.info(f"Starting login monitor for {self.username} on port {self.port}")
        
        while not self.stop_event.is_set() and not shutdown_event.is_set():
            try:
                # Check if tab still exists before using it
                if not self.tab:
                    logger.info(f"Tab no longer exists for {self.username}, exiting monitor")
                    break
                
                # Use wait with timeout instead of sleep for responsive shutdown
                if self.stop_event.wait(timeout=self.login_check_interval):
                    # Event was set, exit loop
                    logger.info(f"Stop event triggered for {self.username}, exiting loop")
                    break
                
                # Check global shutdown event
                if shutdown_event.is_set():
                    break
                    
                # Check and log in if needed
                result = self.check_and_login_if_needed()
                # If None is returned, WebSocket connection was lost - exit gracefully
                if result is None:
                    logger.info(f"WebSocket disconnection detected for {self.username}, exiting monitor loop")
                    break
                
            except pychrome.exceptions.TabNotFoundError:
                logger.info(f"Tab not found for {self.username}, likely during shutdown")
                break
            except Exception as e:
                # Check for WebSocket exceptions that indicate shutdown
                error_msg = str(e)
                if any(x in error_msg for x in [
                    "Connection to remote host was lost",
                    "WebSocketConnectionClosedException", 
                    "Tab has been stopped"
                ]):
                    logger.info(f"WebSocket closed for {self.username}, exiting monitor gracefully")
                    break
                else:
                    logger.error(f"Error in login monitor for {self.username}: {e}")
                    # Use shorter wait on error
                    if self.stop_event.wait(timeout=5):
                        break
        
        logger.info(f"Login monitor stopped for {self.username}")
    
    def inject_autorisk_script(self):
        """Inject autorisk management script into logged-in Tradovate interface"""
        if not self.tab:
            return False
            
        try:
            # Check if script is already loaded
            check_script_js = """
            (function() {
                return typeof getTableData === 'function' && 
                       typeof updateUserColumnPhaseStatus === 'function' && 
                       typeof performAccountActions === 'function';
            })();
            """
            
            result = self.tab.Runtime.evaluate(expression=check_script_js)
            script_loaded = result.get("result", {}).get("value", False)
            
            if script_loaded:
                logger.info(f"Autorisk script already loaded for {self.username}")
                return True
            
            logger.info(f"Injecting autorisk management script for {self.username}")
            
            # Read the autorisk script from file
            autorisk_script_path = os.path.join(project_root, 'scripts/tampermonkey/autoriskManagement.js')
            with open(autorisk_script_path, 'r') as f:
                script_content = f.read()
            
            # Extract just the JavaScript content (skip the tampermonkey header)
            script_lines = script_content.split('\n')
            start_idx = None
            for i, line in enumerate(script_lines):
                if line.strip() == '(function() {':
                    start_idx = i
                    break
            
            if start_idx is None:
                logger.error(f"Could not find script start in autorisk file")
                return False
                
            # Get the JavaScript content
            js_content = '\n'.join(script_lines[start_idx:])
            
            # Execute the script
            self.tab.Runtime.evaluate(expression=js_content)
            logger.info(f"Autorisk script injected successfully for {self.username}")
            
            # Inject FPS throttling script if in optimization mode
            if os.environ.get('OPTIMIZE_MODE') == 'True':
                try:
                    fps_throttle_path = os.path.join(project_root, 'scripts/fps_throttle.js')
                    with open(fps_throttle_path, 'r') as f:
                        fps_throttle_script = f.read()
                    
                    self.tab.Runtime.evaluate(expression=fps_throttle_script)
                    logger.info(f"FPS throttling script injected for {self.username} - CPU optimization active")
                except Exception as e:
                    logger.warning(f"Failed to inject FPS throttle script: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error injecting autorisk script for {self.username}: {e}")
            return False
        
    def stop(self):
        """Stop this Chrome instance using event signaling"""
        logger.info(f"Initiating stop for {self.username}")
        
        # Set the stop event to signal the monitor thread to exit
        self.stop_event.set()
        
        # Close WebSocket connection cleanly if tab exists
        if self.tab:
            try:
                logger.info(f"Closing WebSocket connection for {self.username}")
                self.tab.stop()
                self.tab = None
            except Exception as e:
                logger.debug(f"Error closing WebSocket for {self.username}: {e}")
                # This is expected during shutdown
        
        # Stop Chrome logger if running
        if self.chrome_logger:
            try:
                logger.info(f"Stopping Chrome logger for {self.username}")
                self.chrome_logger.stop()
            except Exception as e:
                logger.error(f"Error stopping Chrome logger for {self.username}: {e}")
            finally:
                self.chrome_logger = None
        
        # Stop the login monitor thread
        if self.login_monitor_thread and self.login_monitor_thread.is_alive():
            logger.info(f"Waiting for login monitor thread to stop for {self.username}")
            self.login_monitor_thread.join(timeout=5)
            if self.login_monitor_thread.is_alive():
                logger.warning(f"Login monitor thread for {self.username} did not stop within timeout")
            else:
                logger.info(f"Login monitor thread for {self.username} stopped successfully")
            
        if self.process:
            try:
                self.process.terminate()
                logger.info(f"Chrome on port {self.port} terminated")
                # Give Chrome a moment to clean up
                try:
                    self.process.wait(timeout=2)
                    logger.info(f"Chrome process on port {self.port} exited with code: {self.process.returncode}")
                except subprocess.TimeoutExpired:
                    logger.warning(f"Chrome process on port {self.port} did not terminate gracefully, killing...")
                    self.process.kill()
                    # Always wait after kill to prevent zombie
                    self.process.wait()
                    logger.info(f"Chrome process on port {self.port} force killed")
            except Exception as e:
                logger.error(f"Error terminating Chrome: {e}")

def fix_chrome_crash_preferences(profile_dir):
    """Fix Chrome preferences to prevent 'restore pages' popup after crashes"""
    try:
        import json
        
        # Paths to Chrome preferences files
        preferences_file = os.path.join(profile_dir, "Preferences")
        local_state_file = os.path.join(profile_dir, "..", "Local State")
        
        # Fix main Preferences file
        if os.path.exists(preferences_file):
            try:
                with open(preferences_file, 'r') as f:
                    prefs = json.load(f)
                
                # Set clean exit flags
                if 'profile' not in prefs:
                    prefs['profile'] = {}
                prefs['profile']['exited_cleanly'] = True
                prefs['profile']['exit_type'] = 'Normal'
                
                with open(preferences_file, 'w') as f:
                    json.dump(prefs, f, indent=2)
                logger.debug(f"Fixed preferences file: {preferences_file}")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Could not modify preferences JSON: {e}")
                # Fallback to sed-like replacement
                try:
                    with open(preferences_file, 'r') as f:
                        content = f.read()
                    content = content.replace('"exited_cleanly":false', '"exited_cleanly":true')
                    content = content.replace('"exit_type":"Crashed"', '"exit_type":"Normal"')
                    with open(preferences_file, 'w') as f:
                        f.write(content)
                    logger.debug(f"Fixed preferences file using text replacement: {preferences_file}")
                except Exception as e2:
                    logger.warning(f"Failed to fix preferences file: {e2}")
        
        # Fix Local State file if it exists
        if os.path.exists(local_state_file):
            try:
                with open(local_state_file, 'r') as f:
                    local_state = json.load(f)
                
                if 'profile' not in local_state:
                    local_state['profile'] = {}
                local_state['profile']['exited_cleanly'] = True
                
                with open(local_state_file, 'w') as f:
                    json.dump(local_state, f, indent=2)
                logger.debug(f"Fixed local state file: {local_state_file}")
            except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
                logger.debug(f"Could not modify local state (this is normal for new profiles): {e}")
                
    except Exception as e:
        logger.warning(f"Error fixing Chrome crash preferences: {e}")

def start_chrome_with_debugging(port):
    """Start a *new* isolated Chrome instance with remote-debugging enabled."""
    logger.info(f"Starting Chrome with remote debugging on port {port}...")

    # Separate profile → forces a brand-new Chrome process even if one is already open
    profile_dir = os.path.join("/tmp", f"tradovate_debug_profile_{port}")
    os.makedirs(profile_dir, exist_ok=True)
    
    # Fix Chrome preferences to prevent crash restore dialogs
    fix_chrome_crash_preferences(profile_dir)

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
        "--disable-features=InfiniteSessionRestore",
        "--hide-crash-restore-bubble",
        "--no-crash-upload",
        "--disable-backgrounding-occluded-windows",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        TRADOVATE_URL,
    ]

    try:
        process = subprocess.Popen(chrome_cmd,
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
        logger.info(f"Chrome started with PID: {process.pid}")
        return process
    except Exception as e:
        logger.error(f"Failed to start Chrome: {e}")
        return None

def connect_to_chrome(port):
    """Connect to Chrome via remote debugging protocol"""
    logger.info(f"Connecting to Chrome on port {port}...")
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
            logger.debug(f"Found tab with URL: {url}")
            
            if "tradovate" in url:
                target_tab = tab
                logger.info("Found Tradovate tab")
            else:
                tab.stop()
        except Exception as e:
            logger.warning(f"Error checking tab: {e}")
            tab.stop()
    
    if not target_tab:
        # If no Tradovate tab found, try to create one
        logger.info("No Tradovate tab found, creating one...")
        target_tab = browser.new_tab(url=TRADOVATE_URL)
        target_tab.start()
        target_tab.Page.enable()
        time.sleep(3)  # Wait for page to load
    
    return browser, target_tab

def inject_login_script(tab, username, password):
    """Inject and execute auto-login script with specific credentials"""
    logger.info(f"Injecting auto-login script for {username}...")
    
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
                    btn.textContent.trim() === "Launch" ||
                    btn.textContent.trim() === "Start Simulated Trading"
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
        logger.info("Executing login script...")
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
        
        logger.info(f"Login script executed for {username}")
        return result
    except Exception as e:
        logger.error(f"Error executing login script: {e}")
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
        logger.info("Disabled browser alerts and confirmations")
        return True
    except Exception as e:
        logger.error(f"Error disabling alerts: {e}")
        return False

def load_credentials():
    """Load all credentials from JSON file, allowing duplicates"""
    try:
        credentials = load_json_config('config/credentials.json')
        logger.info("Loaded credentials successfully")
        
        # Parse credentials into list of username/password pairs
        cred_pairs = []
        
        if isinstance(credentials, dict):
            # Handle flat dictionary with username as keys
            for username, password in credentials.items():
                if username and password:
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
        
        logger.info(f"Loaded {len(cred_pairs)} credential pairs")
        return cred_pairs
    except Exception as e:
        logger.error(f"Error loading credentials from file: {e}")
        # Fall back to environment variables
        username = os.environ.get('TRADOVATE_USERNAME', '')
        password = os.environ.get('TRADOVATE_PASSWORD', '')
        if username and password:
            return [(username, password)]
        return []

def load_dashboard_config():
    """Load saved dashboard window configuration"""
    try:
        return load_json_config('config/dashboard_window.json')
    except Exception as e:
        logger.warning(f"Could not load dashboard config: {e}")
    
    # Default configuration
    return {
        "x": 100,
        "y": 100,
        "width": 1200,
        "height": 800
    }

def save_dashboard_config(config):
    """Save dashboard window configuration"""
    try:
        config_dir = get_project_root() / 'config'
        config_dir.mkdir(parents=True, exist_ok=True)
        
        config_path = config_dir / 'dashboard_window.json'
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not save dashboard config: {e}")

def open_dashboard_window():
    """Open a Chrome window for the dashboard at localhost:6001"""
    try:
        # Load saved window configuration
        config = load_dashboard_config()
        
        # Find the next available debugging port
        port = BASE_DEBUGGING_PORT + 99  # Use port 9321 for dashboard
        
        # Get Chrome path
        chrome_path = find_chrome_executable()
        if not chrome_path:
            logger.error("Chrome not found, cannot open dashboard")
            return None
        
        # Set up profile for dashboard
        user_data_dir = os.path.join(os.path.expanduser("~"), ".tradovate-dashboard")
        os.makedirs(user_data_dir, exist_ok=True)
        
        # Chrome command with window size and position
        chrome_cmd = [
            chrome_path,
            "--new-window",
            "http://localhost:6001",
            f"--window-size={config['width']},{config['height']}",
            f"--window-position={config['x']},{config['y']}",
            f"--user-data-dir={user_data_dir}",
            f"--remote-debugging-port={port}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-features=ChromeWhatsNewUI"
        ]
        
        # Start Chrome process
        process = subprocess.Popen(chrome_cmd,
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
        
        # Create a minimal ChromeInstance for the dashboard
        dashboard_instance = ChromeInstance(port, "dashboard", "")
        dashboard_instance.process = process
        
        # Note: We'll need to implement window position tracking later
        # For now, just save the initial config
        save_dashboard_config(config)
        
        return dashboard_instance
        
    except Exception as e:
        logger.error(f"Failed to open dashboard window: {e}")
        return None

def handle_exit(chrome_instances):
    """Clean up before exiting with proper tracking and detailed logging"""
    logger.info("==========================================================")
    logger.info("[CLEANUP] Starting graceful shutdown of all Chrome instances...")
    logger.info(f"[CLEANUP] Total instances to stop: {len(chrome_instances)}")
    logger.info("==========================================================")
    
    # Set the global shutdown event
    shutdown_event.set()
    logger.info("[CLEANUP] Global shutdown event set")
    
    # Update total counts
    update_cleanup_status('instances_total', len(chrome_instances))
    update_cleanup_status('threads_total', len(chrome_instances))  # Each instance has 1 monitor thread
    
    # Track cleanup progress
    stopped_count = 0
    failed_stops = []
    
    # Stop all instances
    logger.info("[CLEANUP] Phase 1: Stopping Chrome instances...")
    for idx, instance in enumerate(chrome_instances):
        logger.info(f"[CLEANUP]   [{idx+1}/{len(chrome_instances)}] Stopping {instance.username} on port {instance.port}")
        try:
            instance.stop()
            stopped_count += 1
            update_cleanup_status('instances_stopped', stopped_count)
            logger.info(f"[CLEANUP]   ✓ {instance.username} stopped successfully")
        except Exception as e:
            logger.error(f"[CLEANUP]   ✗ Error stopping {instance.username}: {e}")
            failed_stops.append(instance.username)
    
    logger.info(f"[CLEANUP] Phase 1 complete: {stopped_count}/{len(chrome_instances)} instances stopped")
    if failed_stops:
        logger.warning(f"[CLEANUP] Failed to stop: {', '.join(failed_stops)}")
    
    # Wait for all monitor threads to complete
    logger.info("[CLEANUP] Phase 2: Waiting for monitor threads to finish...")
    threads_stopped = 0
    threads_failed = []
    timeout = 10  # Total timeout for all threads
    start_time = time.time()
    
    for instance in chrome_instances:
        if instance.login_monitor_thread and instance.login_monitor_thread.is_alive():
            elapsed = time.time() - start_time
            remaining_time = timeout - elapsed
            if remaining_time > 0:
                logger.info(f"[CLEANUP]   Waiting for {instance.username} monitor thread (timeout: {remaining_time:.1f}s)...")
                instance.login_monitor_thread.join(timeout=remaining_time)
                if not instance.login_monitor_thread.is_alive():
                    threads_stopped += 1
                    update_cleanup_status('threads_stopped', threads_stopped)
                    logger.info(f"[CLEANUP]   ✓ {instance.username} monitor thread stopped")
                else:
                    logger.warning(f"[CLEANUP]   ⚠ {instance.username} monitor thread did not stop in time")
                    threads_failed.append(instance.username)
            else:
                logger.warning(f"[CLEANUP]   ⚠ Timeout reached, skipping {instance.username} monitor thread")
                threads_failed.append(instance.username)
        else:
            threads_stopped += 1
            update_cleanup_status('threads_stopped', threads_stopped)
    
    logger.info(f"[CLEANUP] Phase 2 complete: {threads_stopped}/{len(chrome_instances)} threads stopped")
    if threads_failed:
        logger.warning(f"[CLEANUP] Threads still running: {', '.join(threads_failed)}")
    
    # Mark cleanup as complete
    update_cleanup_status('cleanup_complete', True)
    
    # Final summary
    logger.info("==========================================================")
    logger.info("[CLEANUP] Cleanup Summary:")
    logger.info(f"[CLEANUP]   Chrome instances stopped: {stopped_count}/{len(chrome_instances)}")
    logger.info(f"[CLEANUP]   Monitor threads stopped: {threads_stopped}/{len(chrome_instances)}")
    logger.info(f"[CLEANUP]   Cleanup status: {'COMPLETE' if stopped_count == len(chrome_instances) and threads_stopped == len(chrome_instances) else 'PARTIAL'}")
    logger.info("==========================================================")

def main():
    chrome_instances = []
    cleanup_status_file_path = None
    
    # Set up signal handlers for graceful shutdown (only in main thread)
    if threading.current_thread().name == 'MainThread':
        def signal_handler(signum, frame):
            signal_names = {
                signal.SIGINT: "SIGINT (Ctrl+C)",
                signal.SIGTERM: "SIGTERM (termination request)"
            }
            signal_name = signal_names.get(signum, f"Signal {signum}")
            logger.info(f"[SIGNAL] Received {signal_name}, initiating graceful shutdown...")
            logger.info(f"[SIGNAL] Setting global shutdown event to stop all threads")
            shutdown_event.set()
            # Don't exit immediately - let the main loop handle cleanup
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        logger.info("[SIGNAL] Signal handlers installed for SIGINT and SIGTERM")
    else:
        logger.info(f"[SIGNAL] Running in thread '{threading.current_thread().name}' - signal handlers not installed (only work in main thread)")
    
    try:
        # Initialize cleanup coordination
        cleanup_status_file_path = init_cleanup_coordination()
        
        # Load credential pairs
        credentials = load_credentials()
        if not credentials:
            logger.error("No credentials found, exiting")
            return 1
            
        logger.info(f"Found {len(credentials)} credential pair(s)")
        
        # Make sure any existing Chrome instances on our managed ports are stopped
        # Kill Chrome instances on ports 9223, 9224, 9225, etc.
        for i in range(10):  # Support up to 10 instances
            port = BASE_DEBUGGING_PORT + i
            subprocess.run(["pkill", "-f", f"remote-debugging-port={port}"],
                          capture_output=True)
        
        # Start Chrome instances for each credential pair simultaneously using threads
        threads = []
        instances = []
        results = []  # To store results from threads
        
        def start_chrome_instance(idx, username, password):
            # Assign a unique port for each Chrome instance
            port = BASE_DEBUGGING_PORT + idx
            logger.info(f"Preparing Chrome instance {idx+1} for {username} on port {port}")
            
            # Create and start a new Chrome instance
            instance = ChromeInstance(port, username, password)
            
            # Set up log file path if log directory is available
            log_file_path = create_log_file_path(username, port)
            if log_file_path:
                instance.set_log_file_path(log_file_path)
                logger.info(f"Log file set for {username}: {log_file_path}")
            
            if instance.start():
                logger.info(f"Chrome instance for {username} started successfully")
                results.append((instance, True))
            else:
                logger.error(f"Failed to start Chrome instance for {username}")
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
            logger.error("Failed to start any Chrome instances, exiting")
            return 1
        
        # Print summary
        logger.info(f"{len(chrome_instances)} Chrome instances running:")
        for idx, instance in enumerate(chrome_instances):
            logger.info(f"  {idx+1}: {instance.username} - Port: {instance.port}")
        
        # Print cleanup status file path for parent process
        print(f"CLEANUP_STATUS_FILE:{cleanup_status_file_path}")
        
        logger.info("Press Ctrl+C to exit and close all Chrome instances")
        # Monitor for shutdown event instead of sleeping indefinitely
        while not shutdown_event.is_set():
            shutdown_event.wait(timeout=1)
    
    except KeyboardInterrupt:
        logger.info("Exiting due to user interrupt...")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        handle_exit(chrome_instances)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())