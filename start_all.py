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
import signal
import atexit
import platform
from datetime import datetime

# Add the project root to the path so we can import from src
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Global variables to track resources for proper cleanup
auto_login_process = None
chrome_processes = []
chrome_termination_lock = threading.Lock()
log_directory = None
chrome_loggers = []  # Track ChromeLogger instances for cleanup

def create_log_directory():
    """Create timestamped log directory for this session"""
    global log_directory
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_directory = os.path.join(project_root, 'logs', timestamp)
    
    try:
        os.makedirs(log_directory, exist_ok=True)
        print(f"Created log directory: {log_directory}")
        return log_directory
    except Exception as e:
        print(f"Error creating log directory: {e}")
        return None

def verify_log_directory():
    """Verify log directory exists and is writable"""
    if not log_directory:
        print("!!! ERROR !!! No log directory available")
        return False
    
    if not os.path.exists(log_directory):
        print(f"!!! ERROR !!! Log directory does not exist: {log_directory}")
        return False
    
    if not os.access(log_directory, os.W_OK):
        print(f"!!! ERROR !!! Log directory is not writable: {log_directory}")
        return False
    
    print(f"Log directory verified: {log_directory}")
    return True


def test_chrome_debugging_connections():
    """Test Chrome debugging connections before starting logging"""
    print("Testing Chrome debugging connections...")
    
    try:
        import pychrome
        
        # Test base debugging port and a few others
        base_port = 9223
        test_ports = [base_port + i for i in range(3)]  # Test first 3 ports
        
        active_connections = []
        for port in test_ports:
            try:
                browser = pychrome.Browser(url=f"http://localhost:{port}")
                tabs = browser.list_tab()
                if tabs:
                    active_connections.append(port)
                    print(f"Chrome debugging active on port {port} ({len(tabs)} tabs)")
            except Exception:
                pass  # Port not active, which is expected
        
        if active_connections:
            print(f"Chrome debugging connections verified on ports: {active_connections}")
            return True
        else:
            print("No active Chrome debugging connections found (this is normal before Chrome starts)")
            return True  # This is not an error, Chrome hasn't started yet
            
    except Exception as e:
        print(f"Error testing Chrome debugging connections: {e}")
        return False

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

def register_chrome_logger(chrome_logger):
    """Register a ChromeLogger instance for centralized cleanup"""
    global chrome_loggers
    if chrome_logger and chrome_logger not in chrome_loggers:
        chrome_loggers.append(chrome_logger)
        print(f"Registered ChromeLogger for cleanup (total: {len(chrome_loggers)})")

def cleanup_chrome_loggers():
    """Clean up all ChromeLogger instances"""
    global chrome_loggers
    if chrome_loggers:
        print(f"Cleaning up {len(chrome_loggers)} ChromeLogger instances...")
        for logger in chrome_loggers:
            try:
                logger.stop()
            except Exception as e:
                print(f"Error stopping ChromeLogger: {e}")
        chrome_loggers.clear()
        print("All ChromeLoggers cleaned up")

def run_auto_login():
    """Run the auto_login process to start Chrome and log in"""
    from src.auto_login import main as auto_login_main, set_log_directory, set_terminal_callback, set_register_chrome_logger
    print("Starting Chrome and auto-login process...")
    
    # Set the log directory for Chrome console logging
    if log_directory:
        set_log_directory(log_directory)
        print("Chrome console logging enabled")
        
        # Set terminal callback for real-time output
        terminal_callback = create_terminal_callback()
        set_terminal_callback(terminal_callback)
        print("Real-time console output enabled")
        
        # Set ChromeLogger registration function
        set_register_chrome_logger(register_chrome_logger)
        print("ChromeLogger registration enabled")
    else:
        print("Warning: No log directory available for Chrome console logging")
    
    # Run auto login
    result = auto_login_main()
    
    # Dashboard window will be opened by run_dashboard() after Flask starts
    
    return result

def run_dashboard():
    """Run the dashboard process"""
    from src.dashboard import run_flask_dashboard
    
    # Start dashboard in a thread so we can open the window after it's running
    def start_flask():
        print("Starting dashboard server...")
        run_flask_dashboard()
    
    dashboard_thread = threading.Thread(target=start_flask)
    dashboard_thread.daemon = True
    dashboard_thread.start()
    
    # Wait for Flask to start
    print("Waiting for dashboard server to start...")
    time.sleep(2)
    
    # NOW open the dashboard window
    print("\n=== OPENING DASHBOARD WINDOW (after server started) ===")
    try:
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        dashboard_url = "http://localhost:6001"
        dashboard_port = 9321  # Fixed port for dashboard
        profile_dir = os.path.join("/tmp", f"tradovate_dashboard_profile_{dashboard_port}")
        
        print(f"Chrome path exists: {os.path.exists(chrome_path)}")
        print(f"Dashboard URL: {dashboard_url}")
        print(f"Profile dir: {profile_dir}")
        
        os.makedirs(profile_dir, exist_ok=True)
        
        chrome_cmd = [
            chrome_path,
            f"--remote-debugging-port={dashboard_port}",
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
            dashboard_url,
        ]
        
        print(f"Executing command: {' '.join(chrome_cmd[:3])}...")
        
        # Try running without suppressing output to see errors
        process = subprocess.Popen(chrome_cmd)
        print(f"Dashboard process started with PID: {process.pid}")
        
        # Check if process is still running after a brief moment
        time.sleep(0.5)
        if process.poll() is None:
            print(f"Dashboard window opened successfully at {dashboard_url}")
        else:
            print(f"Dashboard process exited with code: {process.poll()}")
            
    except Exception as e:
        print(f"EXCEPTION opening dashboard window: {e}")
        import traceback
        traceback.print_exc()
    
    # Keep the main thread alive
    dashboard_thread.join()

def collect_chrome_processes():
    """Find all Chrome processes with remote-debugging-port>=9223 and track them"""
    global chrome_processes
    
    try:
        # Get all Chrome processes with debugging ports
        if platform.system() == "Darwin":  # macOS
            cmd = ["ps", "aux"]
        elif platform.system() == "Windows":
            cmd = ["wmic", "process", "where", "name='chrome.exe'", "get", "ProcessId,CommandLine", "/FORMAT:CSV"]
        else:  # Linux
            cmd = ["ps", "aux"]
            
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            # Parse output to find only Chrome instances on ports 9223+
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if "remote-debugging-port=" in line:
                    # Extract port number
                    import re
                    port_match = re.search(r'remote-debugging-port=(\d+)', line)
                    if port_match:
                        port = int(port_match.group(1))
                        if port >= 9223:  # Only track ports 9223 and above
                            # Extract PID
                            pid_match = re.match(r'\S+\s+(\d+)', line)
                            if pid_match:
                                pid = int(pid_match.group(1))
                                chrome_processes.append(pid)
                                print(f"Tracking Chrome process on port {port} (PID: {pid})")
                        else:
                            print(f"Skipping Chrome process on protected port {port}")
            
            if chrome_processes:
                print(f"Tracking {len(chrome_processes)} Chrome processes (ports 9223+) for cleanup")
            else:
                print("No Chrome processes found on ports 9223+")
    except Exception as e:
        print(f"Error collecting Chrome processes: {e}")

def list_chrome_instances():
    """List all Chrome debugging instances, marking port 9222 as protected"""
    print("=== Chrome Debugging Instances ===")
    print("Protected port: 9222 (will never be touched)")
    print("Managed ports: 9223+")
    print("")
    
    found = False
    try:
        if platform.system() == "Darwin":  # macOS
            cmd = ["ps", "aux"]
        else:  # Linux
            cmd = ["ps", "aux"]
            
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            chrome_instances = []
            
            for line in lines:
                if "remote-debugging-port=" in line and "grep" not in line:
                    import re
                    port_match = re.search(r'remote-debugging-port=(\d+)', line)
                    if port_match:
                        port = int(port_match.group(1))
                        pid_match = re.match(r'\S+\s+(\d+)', line)
                        if pid_match:
                            pid = int(pid_match.group(1))
                            chrome_instances.append((port, pid))
            
            # Sort by port number
            chrome_instances.sort(key=lambda x: x[0])
            
            for port, pid in chrome_instances:
                if port == 9222:
                    print(f"[PROTECTED] Port {port} - PID: {pid}")
                else:
                    print(f"[MANAGED]   Port {port} - PID: {pid}")
                found = True
                
    except Exception as e:
        print(f"Error listing Chrome instances: {e}")
    
    if not found:
        print("No Chrome instances with remote debugging found.")

def stop_chrome_safe():
    """Stop Chrome instances on ports 9223+ only (port 9222 is protected)"""
    print("Stopping Chrome processes on ports 9223+ only...")
    print("Port 9222 will NOT be affected.")
    
    pids_to_stop = []
    
    try:
        if platform.system() == "Darwin":  # macOS
            cmd = ["ps", "aux"]
        else:  # Linux
            cmd = ["ps", "aux"]
            
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            
            for line in lines:
                if "remote-debugging-port=" in line and "grep" not in line:
                    import re
                    port_match = re.search(r'remote-debugging-port=(\d+)', line)
                    if port_match:
                        port = int(port_match.group(1))
                        if port >= 9223:  # Only stop ports 9223 and above
                            pid_match = re.match(r'\S+\s+(\d+)', line)
                            if pid_match:
                                pid = int(pid_match.group(1))
                                pids_to_stop.append((port, pid))
                                print(f"Found Chrome on port {port} (PID: {pid})")
                        else:
                            print(f"Skipping Chrome on port {port} (protected)")
    except Exception as e:
        print(f"Error finding Chrome processes: {e}")
        return
    
    if not pids_to_stop:
        print("No Chrome processes found on ports 9223+")
        return
    
    print(f"\nStopping {len(pids_to_stop)} Chrome process(es)...")
    
    # First try graceful termination
    for port, pid in pids_to_stop:
        try:
            print(f"Sending SIGTERM to port {port} (PID {pid})...")
            os.kill(pid, signal.SIGTERM)
        except Exception as e:
            print(f"Error sending SIGTERM to PID {pid}: {e}")
    
    # Wait a bit
    time.sleep(2)
    
    # Force kill if still running
    for port, pid in pids_to_stop:
        try:
            # Check if process still exists
            os.kill(pid, 0)  # This will raise an exception if process doesn't exist
            print(f"Force killing port {port} (PID {pid})...")
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass  # Process already terminated
        except Exception as e:
            print(f"Error force killing PID {pid}: {e}")
    
    print("\nChrome cleanup complete (ports 9223+ only)")

def check_port(port):
    """Check if a specific port is in use"""
    if port < 9223:
        print(f"Port {port} is protected and cannot be managed by this script.")
        if port == 9222:
            print("Port 9222 is reserved for external use and will never be touched.")
        return
    
    print(f"Checking port {port}...")
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f"Port {port} is in use")
            # Try to find which process is using it
            if platform.system() != "Windows":
                try:
                    cmd = ["lsof", "-i", f":{port}"]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.stdout:
                        print("Process details:")
                        print(result.stdout)
                except:
                    pass
        else:
            print(f"Port {port} is available")
    except Exception as e:
        print(f"Error checking port {port}: {e}")

def cleanup_chrome_instances():
    """
    Terminate all Chrome instances properly (only ports 9223+)
    This function will be called by both signal handlers and atexit
    """
    global chrome_processes, chrome_termination_lock
    
    with chrome_termination_lock:
        # First clean up ChromeLoggers before terminating Chrome
        cleanup_chrome_loggers()
        
        # Check if we've already cleaned up
        if not chrome_processes:
            return
            
        print("\nShutting down Chrome instances (ports 9223+ only)...")
        print("Port 9222 is protected and will not be affected.")
        
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
        
        # Fallback: Directly terminate Chrome processes we've tracked (only 9223+)
        for pid in chrome_processes:
            try:
                print(f"Terminating Chrome process with PID: {pid}")
                if platform.system() == "Windows":
                    subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
                else:
                    os.kill(pid, signal.SIGTERM)
            except Exception as e:
                print(f"Error terminating Chrome process {pid}: {e}")
        
        # Clear the list after termination
        chrome_processes.clear()
        print("Chrome instances terminated (9223+ only)")

def signal_handler(sig, frame):
    """Handle termination signals by cleaning up and exiting"""
    print(f"\nReceived signal {sig}, initiating graceful shutdown...")
    cleanup_chrome_instances()
    sys.exit(0)

def main():
    global auto_login_process
    
    # Register cleanup handlers
    atexit.register(cleanup_chrome_instances)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    parser = argparse.ArgumentParser(description="Start the complete Tradovate Interface stack")
    parser.add_argument("--wait", type=int, default=15, 
                        help="Seconds to wait between auto-login and dashboard start (default: 15)")
    parser.add_argument("--background", action="store_true", 
                        help="Run auto-login in the background")
    parser.add_argument("--dev", action="store_true",
                        help="Enable development mode (reserved for future use)")
    
    # Chrome management commands
    parser.add_argument("--list-chrome", action="store_true",
                        help="List all Chrome debugging instances (port 9222 is protected)")
    parser.add_argument("--stop-chrome", action="store_true",
                        help="Stop Chrome instances on ports 9223+ only (port 9222 is protected)")
    parser.add_argument("--check-port", type=int,
                        help="Check if a specific port is in use")
    
    args = parser.parse_args()
    
    # Handle Chrome management commands first (don't need log directory for these)
    if args.list_chrome:
        list_chrome_instances()
        return 0
    
    if args.stop_chrome:
        stop_chrome_safe()
        return 0
    
    if args.check_port is not None:
        check_port(args.check_port)
        return 0
    
    # For normal operation, create log directory
    if not create_log_directory():
        print("Warning: Failed to create log directory, logging may be impaired")
        return 1
    
    # Verify log directory is accessible
    if not verify_log_directory():
        print("Warning: Log directory verification failed, logging may be impaired")
        return 1
    
    # Test Chrome debugging connections (fail fast)
    if not test_chrome_debugging_connections():
        print("Warning: Chrome debugging connection test failed")
        return 1
    
    # Check for development mode activation
    dev_mode = args.dev
    if dev_mode:
        print("🚀 DEVELOPMENT MODE ACTIVATED")
        print("📝 To reload scripts, run: python3 reload.py")
    
    if args.background:
        # Set the log directory for Chrome console logging
        if log_directory:
            from src.auto_login import set_log_directory, set_terminal_callback, set_register_chrome_logger
            set_log_directory(log_directory)
            print("Chrome console logging enabled")
            
            # Set terminal callback for real-time output
            terminal_callback = create_terminal_callback()
            set_terminal_callback(terminal_callback)
            print("Real-time console output enabled")
            
            # Set ChromeLogger registration function
            set_register_chrome_logger(register_chrome_logger)
            print("ChromeLogger registration enabled")
        else:
            print("Warning: No log directory available for Chrome console logging")
        
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
        
        # Dashboard window will be opened by run_dashboard() after Flask starts
        
        # Development mode reminder
        if dev_mode:
            print("📝 Development mode: To reload scripts, run: python3 reload.py")
        
        # Start the dashboard in the foreground
        run_dashboard()
    else:
        # Set the log directory for Chrome console logging
        if log_directory:
            from src.auto_login import set_log_directory, set_terminal_callback, set_register_chrome_logger
            set_log_directory(log_directory)
            print("Chrome console logging enabled")
            
            # Set terminal callback for real-time output
            terminal_callback = create_terminal_callback()
            set_terminal_callback(terminal_callback)
            print("Real-time console output enabled")
            
            # Set ChromeLogger registration function
            set_register_chrome_logger(register_chrome_logger)
            print("ChromeLogger registration enabled")
        else:
            print("Warning: No log directory available for Chrome console logging")
        
        # Development mode reminder
        if dev_mode:
            print("📝 Development mode: To reload scripts, run: python3 reload.py")
        
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