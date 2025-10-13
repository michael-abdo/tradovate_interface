#!/usr/bin/env python3
"""
Unified startup script for Tradovate Interface:
1. Auto-launch Chrome instances and log in
2. Start the dashboard
3. Optional ngrok tunnel for remote access
4. Optional Chrome optimization

Combines functionality from previous start_all.py and start_all_simple.py
with simplified PID-based cleanup.
"""
import sys
import os
import time
import subprocess
import argparse
import re
import threading
from datetime import datetime

# Add the project root to the path so we can import from src
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src import pid_tracker
from src.chrome_logger import ChromeLogger

# Constants
NGROK_DOMAIN = "mike-development.ngrok-free.app"
WAIT_TIME = 30  # Increased from 15 to allow all accounts to load properly

# Global list to track ChromeLogger instances for cleanup
chrome_loggers = []

def register_chrome_logger(chrome_logger):
    """Register a ChromeLogger instance for cleanup"""
    if chrome_logger and chrome_logger not in chrome_loggers:
        chrome_loggers.append(chrome_logger)
        print(f"[ChromeLogger] Registered for cleanup (total: {len(chrome_loggers)})")


def start_ngrok(port):
    """Start ngrok tunnel and return the public URL"""
    try:
        print(f"Starting ngrok tunnel to {NGROK_DOMAIN}...")
        ngrok_process = subprocess.Popen(
            ["ngrok", "http", "--domain", NGROK_DOMAIN, str(port), "--log", "stdout"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        
        # Track the ngrok process
        pid_tracker.add_pid(ngrok_process.pid, "ngrok")
        
        # Parse output to find the URL
        url_pattern = re.compile(r"url=(https?://[^\s]+)")
        for _ in range(60):  # Wait up to 6 seconds
            if ngrok_process.poll() is not None:
                print("Error: ngrok process terminated unexpectedly")
                return None
            
            line = ngrok_process.stdout.readline()
            match = url_pattern.search(line)
            if match and NGROK_DOMAIN in match.group(1):
                url = match.group(1)
                print(f"✓ Ngrok tunnel established: {url}")
                return url
            
            time.sleep(0.1)
        
        print("Error: Timeout waiting for ngrok to start")
        return None
        
    except FileNotFoundError:
        print("Error: ngrok not found. Please install ngrok: https://ngrok.com/download")
        return None
    except Exception as e:
        print(f"Error starting ngrok: {e}")
        return None


def create_terminal_callback():
    """Create a callback function to display Chrome console logs in terminal"""
    def terminal_log_callback(entry):
        """Display console log entry in terminal with color coding"""
        level_colors = {
            'DEBUG': '\033[36m',      # Cyan
            'INFO': '\033[32m',       # Green
            'LOG': '\033[32m',        # Green
            'WARNING': '\033[33m',    # Yellow
            'ERROR': '\033[31m',      # Red
            'CRITICAL': '\033[41m\033[37m'  # White on red background
        }
        reset = '\033[0m'
        
        level = entry.get('level', 'INFO')
        source = entry.get('source', 'unknown')
        text = entry.get('text', '')
        
        # Format timestamp
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Get color for level
        color = level_colors.get(level, '')
        
        # Print formatted log entry
        print(f"[{timestamp}] {color}[{source}:{level}]{reset} {text}")
    
    return terminal_log_callback


def run_auto_login(optimize_mode):
    """Run the auto_login process to start Chrome and log in"""
    print("Starting Chrome and auto-login process...")
    
    # Create a Python command that sets up logging and runs auto_login
    auto_login_cmd = f"""
import sys
import os
from datetime import datetime
from src.auto_login import main as auto_login_main, set_terminal_callback, set_register_chrome_logger

# Set optimization mode
os.environ['OPTIMIZE_MODE'] = '{optimize_mode}'

# Simple terminal callback for console logs
def terminal_callback(entry):
    colors = {{
        'ERROR': '\\033[31m',    # Red
        'WARNING': '\\033[33m',  # Yellow
        'INFO': '\\033[32m',     # Green
        'LOG': '\\033[96m'       # Bright Cyan - highly visible for detailed logs
    }}
    reset = '\\033[0m'
    
    level = entry.get('level', 'LOG')
    text = entry.get('text', '')
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    color = colors.get(level, '\\033[0m')
    print(f"[{{timestamp}}] {{color}}[{{level}}]{{reset}} {{text}}")

# Dummy registration function (since we're in subprocess)
def register_chrome_logger(logger):
    pass

# Set the callback and registration function
set_terminal_callback(terminal_callback)
set_register_chrome_logger(register_chrome_logger)
print("Console logging enabled")
if '{optimize_mode}' == 'True':
    print("🚀 CPU Optimization mode enabled for auto-login Chrome instances")
sys.exit(auto_login_main())
"""
    
    # Start auto-login as subprocess
    auto_login_process = subprocess.Popen(
        [sys.executable, "-u", "-c", auto_login_cmd],  # -u flag for unbuffered output
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    pid_tracker.add_pid(auto_login_process.pid, "auto_login")
    
    # Print auto-login output in real-time
    def print_output(proc):
        for line in iter(proc.stdout.readline, ''):
            if line:
                print(f"[auto_login] {line.rstrip()}")
    
    output_thread = threading.Thread(target=print_output, args=(auto_login_process,))
    output_thread.daemon = True
    output_thread.start()
    
    return auto_login_process


def run_dashboard():
    """Run the dashboard process"""
    print("Starting dashboard server...")
    flask_process = subprocess.Popen(
        [sys.executable, "-u", "-c",  # -u for unbuffered output
         "from src.dashboard import run_flask_dashboard; run_flask_dashboard()"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Combine stderr with stdout
        text=True
    )
    pid_tracker.add_pid(flask_process.pid, "flask_dashboard")
    
    # Start a thread to print Flask output
    def print_flask_output(proc):
        for line in iter(proc.stdout.readline, ''):
            if line:
                print(f"[flask_dashboard] {line.rstrip()}")
    
    flask_thread = threading.Thread(target=print_flask_output, args=(flask_process,))
    flask_thread.daemon = True
    flask_thread.start()
    
    # Wait a moment for Flask to start
    time.sleep(2)
    return flask_process


def open_dashboard_window(optimize_mode):
    """Open dashboard in Chrome with optional optimization and Chrome logging"""
    dashboard_url = "http://localhost:6001"
    dashboard_port = 9321
    
    # Build Chrome command
    chrome_cmd = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        f"--remote-debugging-port={dashboard_port}",
        f"--user-data-dir=/tmp/tradovate_dashboard_profile_{dashboard_port}",
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
        "--no-crash-upload"
    ]
    
    if optimize_mode:
        # Add CPU optimization flags
        chrome_cmd.extend([
            # Enable GPU acceleration
            "--enable-gpu-rasterization",
            "--enable-zero-copy",
            "--enable-accelerated-video-decode",
            "--ignore-gpu-blocklist",
            
            # Enable power saving features
            "--enable-features=HighEfficiencyModeAvailable,BatterySaverModeAvailable",
            "--force-fieldtrials=HighEfficiencyModeAvailable/Enabled",
            
            # Enable background throttling
            "--enable-background-timer-throttling",
            "--enable-backgrounding-occluded-windows",
            
            # Reduce memory usage
            "--max-old-space-size=512",
            "--memory-pressure-off",
            
            # Disable unnecessary features
            "--disable-background-networking",
            "--disable-component-update",
            "--disable-domain-reliability",
            "--disable-features=TranslateUI",
            "--disable-sync"
        ])
        print("🚀 CPU Optimization mode enabled - GPU acceleration and power saving active")
    else:
        # Use original performance-oriented flags
        chrome_cmd.extend([
            "--disable-backgrounding-occluded-windows",
            "--disable-dev-shm-usage",
            "--no-sandbox"
        ])
    
    chrome_cmd.append(dashboard_url)
    
    # Clean up any existing Chrome instance on this port
    print(f"Cleaning up any existing Chrome instances on port {dashboard_port}...")
    subprocess.run(["pkill", "-f", f"remote-debugging-port={dashboard_port}"], capture_output=True)
    time.sleep(1)
    
    dashboard_chrome = subprocess.Popen(chrome_cmd, 
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL)
    pid_tracker.add_pid(dashboard_chrome.pid, "dashboard_chrome")
    
    print(f"Dashboard opened at {dashboard_url}")
    
    # Wait a moment for Chrome to start up
    time.sleep(3)
    
    # Set up Chrome logging for the dashboard
    print("Setting up Chrome logging for dashboard...")
    terminal_callback = create_terminal_callback()
    
    try:
        import pychrome
        
        # Connect to Chrome DevTools
        browser = pychrome.Browser(url=f"http://127.0.0.1:{dashboard_port}")
        tabs = browser.list_tab()
        
        if tabs:
            # Since Chrome on port 9321 should only have the dashboard tab, use the first one
            dashboard_tab = tabs[0]
            
            if dashboard_tab:
                # Start the tab first
                dashboard_tab.start()
                
                from src.chrome_logger import create_logger
                dashboard_logger = create_logger(
                    tab=dashboard_tab,
                    callback=terminal_callback,
                    account_name="dashboard"
                )
                
                if dashboard_logger:
                    # Register for cleanup
                    register_chrome_logger(dashboard_logger)
                    print("✓ Chrome logging connected to dashboard")
                else:
                    print("⚠️  Warning: Failed to start Chrome logger for dashboard")
            else:
                print("⚠️  Warning: Could not find dashboard tab for logging")
        else:
            print("⚠️  Warning: No Chrome tabs found for dashboard logging")
        
    except Exception as e:
        print(f"⚠️  Warning: Failed to set up Chrome logging for dashboard: {e}")
        print("   Dashboard will still work, but console logs won't appear in terminal")
    
    return dashboard_chrome


def main():
    parser = argparse.ArgumentParser(description="Start the complete Tradovate Interface stack")
    parser.add_argument("--ngrok", action="store_true",
                        help="Enable ngrok tunnel for remote access")
    parser.add_argument("--optimize", action="store_true",
                        help="Enable CPU optimization mode (GPU acceleration, power saving)")
    args = parser.parse_args()
    
    # Setup PID tracker signal handler for cleanup
    pid_tracker.setup_signal_handler()
    
    # Track this main process
    pid_tracker.add_pid(os.getpid(), "start_all")
    
    print("\n=== Starting Tradovate Interface ===")
    print("Press Ctrl+C to stop all processes\n")
    
    # Start auto-login process
    auto_login_process = run_auto_login(args.optimize)
    
    # Wait for Chrome instances to start and log in (hardcoded wait time)
    print(f"\nWaiting {WAIT_TIME} seconds for login to complete...")
    time.sleep(WAIT_TIME)
    
    # Start dashboard
    flask_process = run_dashboard()
    
    # Open dashboard window
    dashboard_chrome = open_dashboard_window(args.optimize)
    
    # Start ngrok tunnel if requested
    if args.ngrok:
        ngrok_url = start_ngrok(6001)
        if ngrok_url:
            print(f"\n🌐 Dashboard also accessible at: {ngrok_url}")
            print("   Share this URL for remote access")
        else:
            print("\n⚠️  Warning: Failed to start ngrok tunnel")
            print("   Dashboard is still accessible locally")
    
    print("\nSystem is running. Press Ctrl+C to stop.")
    
    # Keep running until interrupted
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Clean up Chrome loggers
        print("\nCleaning up Chrome loggers...")
        for logger in chrome_loggers:
            try:
                logger.stop()
            except Exception as e:
                print(f"Error stopping Chrome logger: {e}")
        
        # PID tracker signal handler will handle process cleanup
        pass


if __name__ == "__main__":
    main()