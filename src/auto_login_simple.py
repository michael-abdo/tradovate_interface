#!/usr/bin/env python3
"""
Simplified auto-login script that:
1. Launches Chrome instances for each account
2. Logs them in automatically
3. Monitors and re-logs in every 30 seconds
"""
import os
import sys
import time
import json
import subprocess
import threading
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src import pid_tracker
from src.utils.core import get_project_root

# Import pychrome for Chrome DevTools Protocol
try:
    import pychrome
except ImportError:
    print("ERROR: pychrome not installed. Run: pip install pychrome")
    sys.exit(1)


def load_credentials():
    """Load credentials from config file"""
    config_path = get_project_root() / "config" / "credentials.json"
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return {}


def start_chrome(port, username):
    """Start Chrome with remote debugging"""
    user_dir = f"/tmp/tradovate_debug_profile_{port}"
    
    chrome_cmd = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_dir}",
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
        "https://trader.tradovate.com"
    ]
    
    print(f"Starting Chrome for {username} on port {port}...")
    process = subprocess.Popen(chrome_cmd,
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
    
    pid_tracker.add_pid(process.pid, f"chrome_{username}_{port}")
    return process


def connect_to_chrome(port, retries=20):
    """Connect to Chrome DevTools"""
    for i in range(retries):
        try:
            browser = pychrome.Browser(url=f"http://127.0.0.1:{port}")
            tabs = browser.list_tab()
            if tabs:
                tab = tabs[0]
                tab.start()
                return browser, tab
        except Exception:
            if i < retries - 1:
                time.sleep(1)
            else:
                print(f"Failed to connect to Chrome on port {port}")
    return None, None


def inject_login_script(tab, username, password):
    """Inject script to fill login form"""
    login_script = f"""
    (function() {{
        console.log('Attempting login for {username}');
        
        // Fill email
        const emailInput = document.getElementById('name-input');
        if (emailInput) {{
            emailInput.value = '{username}';
            emailInput.dispatchEvent(new Event('input', {{bubbles: true}}));
            emailInput.dispatchEvent(new Event('change', {{bubbles: true}}));
        }}
        
        // Fill password  
        const passwordInput = document.getElementById('password-input');
        if (passwordInput) {{
            passwordInput.value = '{password}';
            passwordInput.dispatchEvent(new Event('input', {{bubbles: true}}));
            passwordInput.dispatchEvent(new Event('change', {{bubbles: true}}));
        }}
        
        // Click login button after a delay
        setTimeout(() => {{
            const loginButton = document.querySelector('button[type="submit"], button.btn-primary');
            if (loginButton) {{
                loginButton.click();
                console.log('Login button clicked');
            }}
        }}, 500);
    }})();
    """
    
    try:
        tab.Runtime.evaluate(expression=login_script)
        print(f"Login script executed for {username}")
    except Exception as e:
        print(f"Error injecting login script: {e}")


def check_page_status(tab):
    """Check what page we're on"""
    check_script = """
    (function() {
        // Login page check
        if (document.getElementById('name-input')) return 'login';
        
        // Account selection check  
        const buttons = Array.from(document.querySelectorAll('button'));
        if (buttons.some(b => b.textContent.includes('Access Simulation'))) return 'account_selection';
        
        // Logged in check (dashboard or trading view)
        if (document.querySelector('.dashboard--container') || 
            document.querySelector('.bar--heading') ||
            document.querySelector('[class*="workspace"]')) return 'logged_in';
            
        return 'unknown';
    })();
    """
    
    try:
        result = tab.Runtime.evaluate(expression=check_script)
        return result.get('result', {}).get('value', 'unknown')
    except:
        return 'error'


def click_access_simulation(tab):
    """Click the Access Simulation button"""
    click_script = """
    (function() {
        const buttons = Array.from(document.querySelectorAll('button'));
        const simButton = buttons.find(b => b.textContent.includes('Access Simulation'));
        if (simButton) {
            simButton.click();
            console.log('Clicked Access Simulation');
            return true;
        }
        return false;
    })();
    """
    
    try:
        tab.Runtime.evaluate(expression=click_script)
        print("Clicked Access Simulation button")
    except Exception as e:
        print(f"Error clicking button: {e}")


def monitor_and_login(tab, username, password, stop_event):
    """Monitor login status and re-login if needed"""
    while not stop_event.is_set():
        try:
            # Wait 30 seconds between checks
            if stop_event.wait(30):
                break
                
            # Check page status
            status = check_page_status(tab)
            
            if status == 'login':
                print(f"Login page detected for {username}, logging in...")
                inject_login_script(tab, username, password)
                
            elif status == 'account_selection':
                print(f"Account selection detected for {username}")
                click_access_simulation(tab)
                
            elif status == 'logged_in':
                # Already logged in, nothing to do
                pass
                
            elif status == 'error':
                print(f"Connection error for {username}, will retry...")
                time.sleep(5)
                
        except Exception as e:
            # Connection lost or other error
            if "WebSocket" in str(e) or "Connection" in str(e):
                print(f"Connection lost for {username}, exiting monitor")
                break
            time.sleep(5)


def main():
    print("\n=== Tradovate Auto-Login (Simplified) ===\n")
    
    # Load credentials
    credentials = load_credentials()
    if not credentials:
        print("No credentials found!")
        return 1
    
    print(f"Found {len(credentials)} accounts to manage")
    
    # Track Chrome instances
    instances = []
    
    # Start Chrome for each account
    for idx, (username, password) in enumerate(credentials.items()):
        port = 9223 + idx
        
        # Start Chrome
        process = start_chrome(port, username)
        time.sleep(2)  # Give Chrome time to start
        
        # Connect to Chrome
        browser, tab = connect_to_chrome(port)
        if not tab:
            print(f"Failed to connect to Chrome for {username}")
            continue
            
        # Initial login attempt
        time.sleep(2)  # Let page load
        status = check_page_status(tab)
        
        if status == 'login':
            inject_login_script(tab, username, password)
        elif status == 'account_selection':
            click_access_simulation(tab)
            
        # Start monitoring thread
        stop_event = threading.Event()
        monitor_thread = threading.Thread(
            target=monitor_and_login,
            args=(tab, username, password, stop_event),
            daemon=True
        )
        monitor_thread.start()
        
        instances.append({
            'username': username,
            'process': process,
            'stop_event': stop_event
        })
        
        print(f"Started monitoring for {username}")
    
    if not instances:
        print("No Chrome instances started!")
        return 1
        
    print(f"\n{len(instances)} Chrome instances running")
    print("Auto-login monitoring active (checking every 30 seconds)")
    
    # Keep running until parent process dies
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        # Set stop events for monitor threads
        for instance in instances:
            instance['stop_event'].set()
        # Let parent process handle PID cleanup
    
    return 0


if __name__ == "__main__":
    sys.exit(main())