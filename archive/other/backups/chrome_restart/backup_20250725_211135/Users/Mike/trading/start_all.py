#!/usr/bin/env python3
"""
All-in-one startup script for Tradovate Interface:
1. Auto-launch Chrome instances with watchdog protection
2. Automatically log in to all accounts
3. Start the dashboard

This script handles the complete startup flow in a single command.
The Chrome Process Watchdog automatically monitors ports 9223+ for crashes.
"""
import sys
import os
import time
import threading
import subprocess
import argparse
import signal
import atexit
import platform

# Add the project root to the path so we can import from src
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import watchdog to check availability
sys.path.insert(0, os.path.join(project_root, 'tradovate_interface', 'src'))
try:
    from utils.process_monitor import ChromeProcessMonitor
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

# Global variables to track resources for proper cleanup
auto_login_process = None
chrome_processes = []
chrome_termination_lock = threading.Lock()

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

def collect_chrome_processes():
    """
    Track only Chrome processes started by this script (ports 9223+)
    NEVER track port 9222 or other existing Chrome instances
    """
    global chrome_processes
    
    try:
        # Only track Chrome processes on our specific ports (9223+)
        # This respects CLAUDE.md Rule #0: NEVER START/STOP CHROME on port 9222
        for port in range(9223, 9243):  # Only our range, not 9222
            try:
                if platform.system() == "Darwin":  # macOS
                    cmd = ["pgrep", "-f", f"remote-debugging-port={port}"]
                else:  # Linux
                    cmd = ["pgrep", "-f", f"remote-debugging-port={port}"]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        if pid.isdigit():  # Ensure it's a valid PID
                            chrome_processes.append(int(pid))
            except Exception:
                continue  # Skip if port check fails
                
        print(f"Tracking {len(chrome_processes)} Chrome processes for cleanup (ports 9223+)")
    except Exception as e:
        print(f"Error collecting Chrome processes: {e}")

def cleanup_chrome_instances():
    """
    Terminate all Chrome instances properly
    This function will be called by both signal handlers and atexit
    """
    global chrome_processes, chrome_termination_lock
    
    with chrome_termination_lock:
        # Check if we've already cleaned up
        if not chrome_processes:
            return
            
        print("\nShutting down Chrome instances...")
        
        # First try graceful termination through auto_login process if available
        if auto_login_process and auto_login_process.poll() is None:
            try:
                print("Sending termination signal to auto_login process...")
                if platform.system() == "Windows":
                    auto_login_process.terminate()
                else:
                    auto_login_process.send_signal(signal.SIGINT)
                # Give it a moment to clean up
                auto_login_process.wait(timeout=5)
            except Exception as e:
                print(f"Error stopping auto_login process: {e}")
        
        # Fallback: Directly terminate Chrome processes we've tracked
        for pid in chrome_processes:
            try:
                print(f"Terminating Chrome process with PID: {pid}")
                if platform.system() == "Windows":
                    subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
                else:
                    os.kill(pid, signal.SIGTERM)
            except Exception as e:
                print(f"Error terminating Chrome process {pid}: {e}")
        
        # Last resort: Use pkill as a safety net (NEVER touch port 9222)
        # Only target specific trading ports to comply with CLAUDE.md Rule #0
        try:
            if platform.system() != "Windows":
                print("Running targeted pkill for ports 9223+ only...")
                # Kill only specific ports 9223, 9224, 9225, etc - NEVER 9222
                for port in [9223, 9224, 9225, 9226, 9227, 9228, 9229, 9230]:
                    subprocess.run(["pkill", "-f", f"remote-debugging-port={port}"], capture_output=True)
        except Exception as e:
            print(f"Error running pkill: {e}")
            
        # Clear the list after termination
        chrome_processes.clear()
        print("Chrome instances terminated")

def signal_handler(sig, frame):
    """Handle termination signals by cleaning up and exiting"""
    print(f"\nReceived signal {sig}, initiating graceful shutdown...")
    cleanup_chrome_instances()
    sys.exit(0)

def show_watchdog_status():
    """Display Chrome Process Watchdog status"""
    if WATCHDOG_AVAILABLE:
        print("\n" + "="*60)
        print("🛡️  Chrome Process Watchdog: ENABLED")
        print("   - Monitoring Chrome instances on ports 9223+")
        print("   - Automatic crash recovery in <30 seconds")
        print("   - Port 9222 is protected from monitoring")
        print("="*60 + "\n")
    else:
        print("\n" + "="*60)
        print("⚠️  Chrome Process Watchdog: NOT AVAILABLE")
        print("   Chrome instances will not have crash protection")
        print("="*60 + "\n")

def main():
    global auto_login_process
    
    # NOTE: Cleanup handlers disabled - Chrome instances will persist after script exit
    # This allows trading to continue even if dashboard script is stopped
    # Uncomment below to enable cleanup on script exit:
    # atexit.register(cleanup_chrome_instances)
    # signal.signal(signal.SIGINT, signal_handler)
    # signal.signal(signal.SIGTERM, signal_handler)
    
    parser = argparse.ArgumentParser(description="Start the complete Tradovate Interface stack")
    parser.add_argument("--wait", type=int, default=15, 
                        help="Seconds to wait between auto-login and dashboard start (default: 15)")
    parser.add_argument("--background", action="store_true", 
                        help="Run auto-login in the background")
    parser.add_argument("--no-watchdog", action="store_true",
                        help="Disable Chrome Process Watchdog monitoring")
    args = parser.parse_args()
    
    # Show watchdog status
    if not args.no_watchdog:
        show_watchdog_status()
    
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
        
        # Collect Chrome processes for proper cleanup
        collect_chrome_processes()
        
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
        
        # Collect Chrome processes for proper cleanup
        collect_chrome_processes()
        
        # Start dashboard in the main thread
        run_dashboard()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # The signal_handler will handle this
        pass
    except Exception as e:
        print(f"\nError in main program: {e}")
        # Ensure Chrome cleanup even on unexpected errors
        cleanup_chrome_instances()
        sys.exit(1)