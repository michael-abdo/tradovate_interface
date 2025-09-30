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

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src import pid_tracker


def main():
    parser = argparse.ArgumentParser(description="Start Tradovate Interface")
    parser.add_argument("--wait", type=int, default=15, 
                        help="Seconds to wait between auto-login and dashboard (default: 15)")
    args = parser.parse_args()
    
    # Setup signal handler for Ctrl+C
    pid_tracker.setup_signal_handler()
    
    # Track this process
    pid_tracker.add_pid(os.getpid(), "start_all")
    
    print("\n=== Starting Tradovate Interface ===")
    print("Press Ctrl+C to stop all processes\n")
    
    # Start auto-login process
    print("Starting auto-login...")
    auto_login = subprocess.Popen(
        [sys.executable, "-m", "src.auto_login"],
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
        "--no-crash-upload",
        "--disable-backgrounding-occluded-windows",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        dashboard_url
    ]
    
    dashboard_chrome = subprocess.Popen(chrome_cmd, 
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL)
    pid_tracker.add_pid(dashboard_chrome.pid, "dashboard_chrome")
    
    print(f"\nDashboard opened at {dashboard_url}")
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