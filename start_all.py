#!/usr/bin/env python3
"""
All-in-one startup script for Tradovate Interface:
1. Auto-launch Chrome instances
2. Automatically log in to all accounts
3. Start the dashboard

This script handles the complete startup flow in a single command.
"""
import sys
import os
import time
import threading
import subprocess
import argparse

# Add the project root to the path so we can import from src
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def run_auto_login():
    """Run the auto_login process to start Chrome and log in"""
    from src.auto_login import main as auto_login_main
    print("Starting Chrome and auto-login process...")
    return auto_login_main()

def run_dashboard():
    """Run the dashboard process"""
    from src.dashboard import run_flask_dashboard
    print("Starting dashboard...")
    run_flask_dashboard()

def main():
    parser = argparse.ArgumentParser(description="Start the complete Tradovate Interface stack")
    parser.add_argument("--wait", type=int, default=15, 
                        help="Seconds to wait between auto-login and dashboard start (default: 15)")
    parser.add_argument("--background", action="store_true", 
                        help="Run auto-login in the background")
    args = parser.parse_args()
    
    if args.background:
        # Start auto-login in the background
        print("Starting auto-login process in the background...")
        auto_login_process = subprocess.Popen(
            [sys.executable, "-m", "src.auto_login"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        print(f"Auto-login started (PID: {auto_login_process.pid})")
        
        # Wait for Chrome instances to start and log in
        print(f"Waiting {args.wait} seconds for login to complete...")
        time.sleep(args.wait)
        
        # Start the dashboard in the foreground
        run_dashboard()
    else:
        # Start auto-login in a separate thread
        auto_login_thread = threading.Thread(target=run_auto_login)
        auto_login_thread.daemon = True
        auto_login_thread.start()
        
        # Wait for Chrome instances to start and log in
        print(f"Waiting {args.wait} seconds for login to complete...")
        time.sleep(args.wait)
        
        # Start dashboard in the main thread
        run_dashboard()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutting down...")
        # Try to find and kill Chrome processes
        try:
            subprocess.run(["pkill", "-f", "remote-debugging-port"], 
                          capture_output=True)
            print("Chrome instances terminated")
        except Exception as e:
            print(f"Error terminating Chrome: {e}")
        sys.exit(0)