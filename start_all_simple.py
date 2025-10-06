#!/usr/bin/env python3
"""
Simple startup script for Tradovate Interface.
Just launches processes and tracks PIDs for cleanup.
"""
import sys
import os
import time
import subprocess
import argparse
import re
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src import pid_tracker

# Constants
NGROK_DOMAIN = "mike-development.ngrok-free.app"


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


def main():
    parser = argparse.ArgumentParser(description="Start Tradovate Interface")
    parser.add_argument("--wait", type=int, default=15, 
                        help="Seconds to wait between auto-login and dashboard (default: 15)")
    parser.add_argument("--ngrok", action="store_true",
                        help="Enable ngrok tunnel to mike-development.ngrok-free.app")
    parser.add_argument("--optimize", action="store_true",
                        help="Enable CPU optimization mode (GPU acceleration, power saving)")
    args = parser.parse_args()
    
    # Setup signal handler for Ctrl+C
    pid_tracker.setup_signal_handler()
    
    # Track this process
    pid_tracker.add_pid(os.getpid(), "start_all")
    
    print("\n=== Starting Tradovate Interface ===")
    print("Press Ctrl+C to stop all processes\n")
    
    # Start auto-login process with console logging
    print("Starting auto-login with console logging...")
    
    # Create a Python command that sets up logging and runs auto_login
    optimize_mode = "True" if args.optimize else "False"
    auto_login_cmd = f"""
import sys
import os
from datetime import datetime
from src.auto_login import main as auto_login_main, set_terminal_callback

# Set optimization mode
os.environ['OPTIMIZE_MODE'] = '{optimize_mode}'

# Simple terminal callback for console logs
def terminal_callback(entry):
    colors = {{
        'ERROR': '\\033[31m',    # Red
        'WARNING': '\\033[33m',  # Yellow
        'INFO': '\\033[32m',     # Green
        'LOG': '\\033[0m'        # Default
    }}
    reset = '\\033[0m'
    
    level = entry.get('level', 'LOG')
    text = entry.get('text', '')
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    color = colors.get(level, '\\033[0m')
    print(f"[{{timestamp}}] {{color}}[{{level}}]{{reset}} {{text}}")

# Set the callback and run
set_terminal_callback(terminal_callback)
print("Console logging enabled")
if '{optimize_mode}' == 'True':
    print("🚀 CPU Optimization mode enabled for auto-login Chrome instances")
sys.exit(auto_login_main())
"""
    
    auto_login = subprocess.Popen(
        [sys.executable, "-c", auto_login_cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    pid_tracker.add_pid(auto_login.pid, "auto_login")
    
    # Print auto-login output
    def print_output(proc):
        for line in iter(proc.stdout.readline, ''):
            if line:
                print(f"[auto_login] {line.rstrip()}")
    
    import threading
    output_thread = threading.Thread(target=print_output, args=(auto_login,))
    output_thread.daemon = True
    output_thread.start()
    
    # Wait for Chrome to start and login
    print(f"\nWaiting {args.wait} seconds for login...")
    time.sleep(args.wait)
    
    # Start dashboard
    print("\nStarting dashboard...")
    flask = subprocess.Popen(
        [sys.executable, "-c", 
         "from src.dashboard import run_flask_dashboard; run_flask_dashboard()"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    pid_tracker.add_pid(flask.pid, "flask_dashboard")
    
    # Wait a moment for Flask to start
    time.sleep(2)
    
    # Open dashboard in Chrome
    dashboard_url = "http://localhost:6001"
    dashboard_port = 9321
    
    # Build Chrome command with optimization flags if requested
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
    
    if args.optimize:
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
    
    dashboard_chrome = subprocess.Popen(chrome_cmd, 
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL)
    pid_tracker.add_pid(dashboard_chrome.pid, "dashboard_chrome")
    
    print(f"\nDashboard opened at {dashboard_url}")
    
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
        # Signal handler will handle cleanup
        pass


if __name__ == "__main__":
    main()