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
import json
import tempfile

# Add the project root to the path so we can import from src
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Global variables to track resources for proper cleanup
auto_login_process = None
flask_process = None  # Track Flask dashboard process for cleanup
dashboard_chrome_process = None  # Track dashboard Chrome window process for cleanup
chrome_processes = []
chrome_termination_lock = threading.Lock()
log_directory = None
chrome_loggers = []  # Track ChromeLogger instances for cleanup
cleanup_status_file = None  # Path to cleanup status file from auto_login.py
cleanup_in_progress = False  # Flag to prevent signal handler reentrancy

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
        base_port = 9223  # Changed from 9222 to protect that port
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

def read_cleanup_status():
    """Read the cleanup status from auto_login.py's status file"""
    if not cleanup_status_file or not os.path.exists(cleanup_status_file):
        return None
    
    try:
        with open(cleanup_status_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading cleanup status: {e}")
        return None

def wait_for_subprocess_cleanup(timeout=30):
    """Poll cleanup status file to monitor subprocess cleanup progress"""
    start_time = time.time()
    last_status = {}
    
    print(f"[CLEANUP] Starting cleanup monitor (timeout: {timeout}s)")
    
    while time.time() - start_time < timeout:
        elapsed = time.time() - start_time
        status = read_cleanup_status()
        
        if status:
            # Log progress if changed
            if status != last_status:
                instances_stopped = status.get('instances_stopped', 0)
                instances_total = status.get('instances_total', 0)
                threads_stopped = status.get('threads_stopped', 0)
                threads_total = status.get('threads_total', 0)
                
                print(f"[CLEANUP] Progress at {elapsed:.1f}s: "
                      f"{instances_stopped}/{instances_total} instances stopped, "
                      f"{threads_stopped}/{threads_total} threads stopped")
                last_status = status
            
            # Check if cleanup is complete
            if status.get('cleanup_complete', False):
                print(f"[CLEANUP] ✓ Subprocess cleanup completed successfully at {elapsed:.1f}s")
                
                # Clean up the temporary status file
                if cleanup_status_file and os.path.exists(cleanup_status_file):
                    try:
                        os.remove(cleanup_status_file)
                        print(f"[CLEANUP] ✓ Removed temporary status file: {cleanup_status_file}")
                    except Exception as e:
                        print(f"[CLEANUP] Warning: Could not remove status file: {e}")
                
                return True
        else:
            # No status file yet, log only occasionally
            if int(elapsed) % 5 == 0 and elapsed - int(elapsed) < 0.5:
                print(f"[CLEANUP] Waiting for cleanup status file at {elapsed:.0f}s...")
        
        time.sleep(0.5)  # Poll every 500ms
    
    print(f"[CLEANUP] ✗ Timeout waiting for subprocess cleanup after {timeout}s")
    
    # Try to clean up status file even on timeout
    if cleanup_status_file and os.path.exists(cleanup_status_file):
        try:
            os.remove(cleanup_status_file)
            print(f"[CLEANUP] Removed temporary status file after timeout")
        except Exception as e:
            print(f"[CLEANUP] Warning: Could not remove status file: {e}")
    
    return False

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
    global flask_process, dashboard_chrome_process
    
    # Run Flask dashboard as a separate process for proper shutdown control
    print("Starting dashboard server as separate process...")
    flask_process = subprocess.Popen(
        [sys.executable, "-c", 
         "from src.dashboard import run_flask_dashboard; run_flask_dashboard()"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        # Create new process group on Unix systems for proper signal handling
        preexec_fn=os.setsid if platform.system() != "Windows" else None
    )
    print(f"Dashboard server started (PID: {flask_process.pid})")
    
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
        
        # Kill any existing Chrome instance on the dashboard port to prevent merging
        print(f"Cleaning up any existing Chrome instances on port {dashboard_port}...")
        subprocess.run(["pkill", "-f", f"remote-debugging-port={dashboard_port}"], capture_output=True)
        time.sleep(1)  # Give it a moment to fully terminate
        
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
        dashboard_chrome_process = process  # Track for cleanup
        print(f"Dashboard process started with PID: {process.pid}")
        
        # Add dashboard Chrome process to cleanup list
        chrome_processes.append(process.pid)
        print(f"Added dashboard Chrome process (PID: {process.pid}) to cleanup list")
        
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
    
    # Keep the main thread alive - wait for Flask process
    try:
        flask_process.wait()
    except KeyboardInterrupt:
        print("Received interrupt signal, shutting down...")
        cleanup_chrome_instances()

def collect_chrome_processes():
    """Find Chrome processes with remote-debugging-port >= 9223 and track them"""
    global chrome_processes
    
    MIN_MANAGED_PORT = 9223  # We only manage ports 9223 and above
    
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
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if "remote-debugging-port=" in line:
                    # Extract port number
                    import re
                    port_match = re.search(r'remote-debugging-port=(\d+)', line)
                    if port_match:
                        port = int(port_match.group(1))
                        if port >= MIN_MANAGED_PORT:  # Only track ports 9223+
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
                print("No Chrome processes found on managed ports (9223+)")
    except Exception as e:
        print(f"Error collecting Chrome processes: {e}")

def cleanup_chrome_instances():
    """
    Terminate Chrome instances on ports 9223+ only (port 9222 is protected)
    This function will be called by both signal handlers and atexit
    """
    global chrome_processes, chrome_termination_lock, flask_process, dashboard_chrome_process
    
    with chrome_termination_lock:
        # FIRST: Signal auto_login to start graceful shutdown BEFORE killing anything else
        # This allows WebSocket connections to close cleanly
        if auto_login_process and auto_login_process.poll() is None:
            print("\nInitiating graceful shutdown of auto_login process...")
            try:
                if platform.system() == "Windows":
                    auto_login_process.terminate()
                else:
                    auto_login_process.send_signal(signal.SIGINT)
                
                # Give auto_login time to close WebSocket connections gracefully
                print("Waiting for auto_login to close connections...")
                time.sleep(2)
            except Exception as e:
                print(f"Error signaling auto_login: {e}")
        
        # SECOND: Clean up Flask dashboard process
        if flask_process and flask_process.poll() is None:
            try:
                print("Stopping Flask dashboard server...")
                flask_process.terminate()
                # Wait for graceful termination
                try:
                    flask_process.wait(timeout=5)
                    print("Flask dashboard stopped gracefully")
                except subprocess.TimeoutExpired:
                    print("Force killing Flask dashboard...")
                    flask_process.kill()
                    flask_process.wait()
            except Exception as e:
                print(f"Error stopping Flask dashboard: {e}")
        
        # THIRD: Clean up ChromeLoggers before terminating Chrome
        cleanup_chrome_loggers()
        
        # FOURTH: Terminate dashboard Chrome window
        if dashboard_chrome_process and dashboard_chrome_process.poll() is None:
            try:
                print("Terminating dashboard Chrome window...")
                dashboard_chrome_process.terminate()
                # Give it a moment to terminate gracefully
                try:
                    dashboard_chrome_process.wait(timeout=3)
                    print("Dashboard Chrome window terminated gracefully")
                except subprocess.TimeoutExpired:
                    print("Force killing dashboard Chrome window...")
                    dashboard_chrome_process.kill()
                    dashboard_chrome_process.wait()
            except Exception as e:
                print(f"Error terminating dashboard Chrome window: {e}")
        
        # Check if we've already cleaned up
        if not chrome_processes and not auto_login_process:
            return
            
        print("\nShutting down Chrome instances (ports 9223+ only)...")
        print("Port 9222 is protected and will not be affected.")
        
        # FIFTH: Complete auto_login termination if still running
        if auto_login_process and auto_login_process.poll() is None:
            try:
                # Use polling to wait for graceful cleanup
                if cleanup_status_file:
                    print(f"[CLEANUP] Monitoring cleanup status file: {cleanup_status_file}")
                    if wait_for_subprocess_cleanup(timeout=15):
                        print("[CLEANUP] ✓ Auto_login subprocess cleaned up gracefully")
                        # Wait for process to exit
                        try:
                            auto_login_process.wait(timeout=5)
                            print("[CLEANUP] ✓ Auto_login process exited cleanly")
                        except subprocess.TimeoutExpired:
                            print("[CLEANUP] Process still running after graceful cleanup")
                    else:
                        # Fallback: escalate to SIGTERM, then SIGKILL
                        print("[CLEANUP] ⚠ Graceful cleanup timed out, escalating to SIGTERM...")
                        # Kill process group if on Unix
                        if platform.system() != "Windows":
                            try:
                                os.killpg(os.getpgid(auto_login_process.pid), signal.SIGTERM)
                                print("[CLEANUP] Sent SIGTERM to process group")
                            except ProcessLookupError:
                                pass
                        else:
                            auto_login_process.terminate()
                        
                        try:
                            auto_login_process.wait(timeout=5)
                            print("[CLEANUP] ✓ Auto_login process terminated with SIGTERM")
                        except subprocess.TimeoutExpired:
                            print("[CLEANUP] ⚠ SIGTERM failed, force killing with SIGKILL...")
                            if platform.system() != "Windows":
                                try:
                                    os.killpg(os.getpgid(auto_login_process.pid), signal.SIGKILL)
                                    print("[CLEANUP] Sent SIGKILL to process group")
                                except ProcessLookupError:
                                    pass
                            else:
                                auto_login_process.kill()
                            auto_login_process.wait()
                            print("[CLEANUP] ✓ Auto_login process killed with SIGKILL")
                else:
                    print("[CLEANUP] Waiting for auto_login to complete shutdown...")
                    try:
                        auto_login_process.wait(timeout=10)
                        print("[CLEANUP] ✓ Auto_login process exited")
                    except subprocess.TimeoutExpired:
                        print("[CLEANUP] Sending SIGTERM...")
                        if platform.system() != "Windows":
                            try:
                                os.killpg(os.getpgid(auto_login_process.pid), signal.SIGTERM)
                                print("[CLEANUP] Sent SIGTERM to process group")
                            except ProcessLookupError:
                                pass
                        else:
                            auto_login_process.terminate()
                        
                        try:
                            auto_login_process.wait(timeout=5)
                            print("[CLEANUP] ✓ Auto_login process terminated with SIGTERM")
                        except subprocess.TimeoutExpired:
                            print("[CLEANUP] ⚠ SIGTERM failed, force killing with SIGKILL...")
                            if platform.system() != "Windows":
                                try:
                                    os.killpg(os.getpgid(auto_login_process.pid), signal.SIGKILL)
                                    print("[CLEANUP] Sent SIGKILL to process group")
                                except ProcessLookupError:
                                    pass
                            else:
                                auto_login_process.kill()
                            auto_login_process.wait()
                            print("[CLEANUP] ✓ Auto_login process killed with SIGKILL")
            except Exception as e:
                print(f"Error stopping auto_login process: {e}")
        
        # Terminate only the Chrome processes we've explicitly tracked (ports 9223+)
        print(f"[CLEANUP] Terminating {len(chrome_processes)} Chrome processes...")
        terminated_count = 0
        for pid in chrome_processes:
            try:
                print(f"[CLEANUP] Sending SIGTERM to Chrome process PID: {pid}")
                if platform.system() == "Windows":
                    subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
                else:
                    os.kill(pid, signal.SIGTERM)
                terminated_count += 1
            except ProcessLookupError:
                print(f"[CLEANUP] Process {pid} already gone")
            except Exception as e:
                print(f"[CLEANUP] ✗ Error terminating Chrome process {pid}: {e}")
        
        # Wait a bit for graceful termination
        time.sleep(1)
        
        # Force kill any that are still running
        force_killed = 0
        still_alive = 0
        for pid in chrome_processes[:]:  # Copy list to avoid modification during iteration
            try:
                # Check if process still exists
                os.kill(pid, 0)  # This will raise an exception if process doesn't exist
                print(f"[CLEANUP] ⚠ Force killing Chrome process {pid}")
                os.kill(pid, signal.SIGKILL)
                force_killed += 1
            except ProcessLookupError:
                pass  # Process already terminated
            except Exception as e:
                print(f"[CLEANUP] ✗ Error force killing Chrome process {pid}: {e}")
                still_alive += 1
            
        # Clear the list after termination
        chrome_processes.clear()
        
        # Summary
        print("[CLEANUP] ========================================")
        print(f"[CLEANUP] Cleanup Summary:")
        print(f"[CLEANUP]   Chrome processes terminated: {terminated_count}")
        print(f"[CLEANUP]   Chrome processes force killed: {force_killed}")
        if still_alive > 0:
            print(f"[CLEANUP]   ⚠ Chrome processes still alive: {still_alive}")
        print(f"[CLEANUP]   Protected port 9222: Not affected")
        print("[CLEANUP] =======================================")

def force_shutdown():
    """Force shutdown by killing all processes immediately"""
    print("\n!!! FORCE SHUTDOWN INITIATED !!!")
    print("Graceful shutdown timeout exceeded, force killing all processes...")
    
    try:
        # Try SIGTERM first (graceful), then SIGKILL (force) - best practice escalation
        processes_to_kill = [
            ("auto_login", auto_login_process),
            ("Flask", flask_process), 
            ("dashboard Chrome", dashboard_chrome_process)
        ]
        
        for name, process in processes_to_kill:
            if process and process.poll() is None:
                try:
                    print(f"Force terminating {name} process (PID: {process.pid})...")
                    # First try SIGTERM for graceful shutdown
                    process.terminate()
                    try:
                        process.wait(timeout=2)
                        print(f"{name} process terminated gracefully")
                    except subprocess.TimeoutExpired:
                        print(f"{name} process didn't respond to SIGTERM, using SIGKILL...")
                        process.kill()
                        process.wait(timeout=1)
                        print(f"{name} process killed")
                except Exception as e:
                    print(f"Error force killing {name}: {e}")
        
        # Force kill all tracked Chrome processes
        killed_count = 0
        for pid in chrome_processes:
            try:
                print(f"Force killing Chrome PID: {pid}")
                os.kill(pid, signal.SIGKILL)
                killed_count += 1
            except ProcessLookupError:
                print(f"Chrome PID {pid} already gone")
            except Exception as e:
                print(f"Error force killing Chrome PID {pid}: {e}")
        
        print(f"Force shutdown completed - killed {killed_count} Chrome processes")
        
        # Give a moment for processes to die, then exit
        time.sleep(0.5)
        
    except Exception as e:
        print(f"Error in force shutdown: {e}")
    finally:
        print("Force shutdown exiting...")
        # Call registered exit functions before immediate exit (best practice)
        try:
            import atexit
            atexit._run_exitfuncs()
        except Exception as e:
            print(f"Error running exit functions: {e}")
        os._exit(1)  # Exit immediately without cleanup

def signal_handler(sig, frame):
    """Handle termination signals by cleaning up and exiting"""
    global cleanup_in_progress
    
    print(f"\nReceived signal {sig}, initiating graceful shutdown...")
    
    # Prevent signal handler reentrancy
    if cleanup_in_progress:
        print("Cleanup already in progress, ignoring repeated signal")
        return
    
    cleanup_in_progress = True
    
    # Start 25-second timer for force shutdown (increased from 15 to allow proper sequencing)
    print("Starting 25-second graceful shutdown timer...")
    force_timer = threading.Timer(25.0, force_shutdown)
    force_timer.daemon = True
    force_timer.start()
    
    try:
        cleanup_chrome_instances()
        # If we get here, graceful shutdown succeeded
        force_timer.cancel()
        print("Graceful shutdown completed successfully")
        sys.exit(0)
    except Exception as e:
        print(f"Error during graceful shutdown: {e}")
        # Timer will handle force shutdown if we don't cancel it
        raise

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
    args = parser.parse_args()
    
    # Create log directory for this session
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
        
        # Start auto-login in the background with process group
        print("Starting auto-login process in the background...")
        # Create process in new session for better signal handling
        auto_login_process = subprocess.Popen(
            [sys.executable, "-m", "src.auto_login"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            # Create new process group on Unix systems
            preexec_fn=os.setsid if platform.system() != "Windows" else None
        )
        print(f"Auto-login started (PID: {auto_login_process.pid})")
        
        # Monitor auto_login output for cleanup status file path
        def monitor_auto_login_output():
            global cleanup_status_file
            try:
                for line in auto_login_process.stdout:
                    print(f"[auto_login] {line.rstrip()}")
                    if line.startswith("CLEANUP_STATUS_FILE:"):
                        cleanup_status_file = line.split(":", 1)[1].strip()
                        print(f"Detected cleanup status file: {cleanup_status_file}")
            except Exception as e:
                print(f"Error in output monitor: {e}")
        
        output_monitor = threading.Thread(target=monitor_auto_login_output, daemon=True)
        output_monitor.start()
        
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