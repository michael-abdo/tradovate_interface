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

def kill_process_on_port(port):
    """Kill any process using the specified port"""
    try:
        # Find process using the port
        result = subprocess.run(['lsof', '-i', f':{port}'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:  # Skip header line
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= 2:
                        pid = parts[1]
                        try:
                            subprocess.run(['kill', '-9', pid], check=True)
                            print(f"🔧 Killed process {pid} on port {port}")
                        except subprocess.CalledProcessError:
                            print(f"⚠️  Failed to kill process {pid} on port {port}")
        else:
            print(f"✅ Port {port} is available")
    except Exception as e:
        print(f"⚠️  Error checking port {port}: {e}")

def test_chrome_debugging_connections():
    """Test Chrome debugging connections before starting logging"""
    print("Testing Chrome debugging connections...")
    
    try:
        import pychrome
        
        # Test base debugging port and a few others
        base_port = 9222
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
    
    return auto_login_main()

def run_dashboard():
    """Run the dashboard process"""
    from src.dashboard import run_flask_dashboard
    print("Starting dashboard...")
    run_flask_dashboard()

def collect_chrome_processes():
    """Find all Chrome processes with remote-debugging-port and track them"""
    global chrome_processes
    
    try:
        if platform.system() == "Darwin":  # macOS
            cmd = ["pgrep", "-f", "remote-debugging-port"]
        elif platform.system() == "Windows":
            cmd = ["tasklist", "/FI", "IMAGENAME eq chrome.exe", "/FO", "CSV"]
        else:  # Linux
            cmd = ["pgrep", "-f", "remote-debugging-port"]
            
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid.isdigit():  # Ensure it's a valid PID
                    chrome_processes.append(int(pid))
            print(f"Tracking {len(chrome_processes)} Chrome processes for cleanup")
    except Exception as e:
        print(f"Error collecting Chrome processes: {e}")

def cleanup_chrome_instances():
    """
    Terminate all Chrome instances properly
    This function will be called by both signal handlers and atexit
    """
    global chrome_processes, chrome_termination_lock
    
    with chrome_termination_lock:
        # First clean up ChromeLoggers before terminating Chrome
        cleanup_chrome_loggers()
        
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
        
        # Last resort: Use pkill as a safety net
        try:
            if platform.system() != "Windows":
                print("Running pkill as final cleanup...")
                subprocess.run(["pkill", "-f", "remote-debugging-port"], capture_output=True)
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
                        help="Enable development mode with script reloader (HTTP server + file watcher + CDP injection)")
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
        print("🔧🔍🔥 Enabling 3-layer script reloader system:")
        print("🔧 LAYER 1: HTTP server for Tampermonkey script serving")
        print("🔍 LAYER 2: File watcher for automatic change detection") 
        print("🔥 LAYER 3: Chrome DevTools Protocol injection")
        print("📡 Real-time script updates across all Chrome instances")
        
        # Conditional imports for development mode only
        try:
            print("📦 Loading script reloader modules...")
            from scripts.tampermonkey.serve_scripts import ScriptServer
            from src.script_watcher import ScriptWatcher
            print("✅ Script reloader modules loaded successfully")
        except ImportError as e:
            print(f"🔴 ERROR: Failed to import script reloader modules: {e}")
            print("🔴 Script reloader will not be available")
            dev_mode = False  # Disable dev mode if imports fail
    else:
        print("🔒 Development mode disabled (use --dev to enable script reloader)")
    
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
        
        # Initialize script reloader in dev mode  
        if dev_mode:
            try:
                print("🚀 SCRIPT RELOADER: Starting initialization...")
                
                # Kill any existing process on port 8080
                kill_process_on_port(8080)
                
                # Initialize Layer 1: HTTP Server
                script_server = ScriptServer(port=8080)
                script_server.start()
                print("🔧 LAYER 1: HTTP server started on http://localhost:8080")
                
                # Initialize Layer 2: File Watcher  
                script_watcher = ScriptWatcher()
                script_watcher.start()
                print("🔍 LAYER 2: File watcher started monitoring scripts/tampermonkey")
                
                # Layer 2 → Layer 3 Connection: Register script_watcher with ChromeLogger system
                def dev_mode_chrome_logger_callback(chrome_logger):
                    """Connect new ChromeLoggers to the script watcher for Layer 2 → Layer 3 handoff"""
                    if chrome_logger:
                        script_watcher.add_chrome_logger(chrome_logger)
                        print(f"🔍→🔥 LAYER CONNECTION: ChromeLogger registered with script watcher")
                
                # Override the existing registration to include script watcher connection
                original_register_chrome_logger = register_chrome_logger
                def enhanced_register_chrome_logger(chrome_logger):
                    print(f"🔧 DEV MODE: Enhanced ChromeLogger registration called for {chrome_logger}")
                    # Call original registration for cleanup
                    original_register_chrome_logger(chrome_logger)
                    # Add to script watcher for Layer 2 → Layer 3 handoff
                    dev_mode_chrome_logger_callback(chrome_logger)
                    print(f"🔧 DEV MODE: ChromeLogger added to script watcher registry")
                
                # Replace the registration function for dev mode
                globals()['register_chrome_logger'] = enhanced_register_chrome_logger
                
                # Re-set the registration function in auto_login to use the enhanced version
                set_register_chrome_logger(enhanced_register_chrome_logger)
                print("🔧 DEV MODE: Enhanced registration function set in auto_login")
                
                print("✅ SCRIPT RELOADER: All layers initialized successfully")
                print("🔍→🔥 Layer 2 → Layer 3 connection established")
                
                # Register any existing ChromeLoggers that were created before script watcher
                print(f"🔧 DEV MODE: Checking for existing ChromeLoggers to register...")
                print(f"🔧 DEV MODE: Found {len(chrome_loggers)} existing ChromeLoggers")
                for chrome_logger in chrome_loggers:
                    print(f"🔧 DEV MODE: Registering existing ChromeLogger: {chrome_logger}")
                    dev_mode_chrome_logger_callback(chrome_logger)
                
            except Exception as e:
                print(f"🔴 SCRIPT RELOADER: ERROR during initialization: {e}")
                print("🔴 Script reloader disabled due to initialization failure")
        
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
        
        # Initialize script reloader in dev mode
        if dev_mode:
            try:
                print("🚀 SCRIPT RELOADER: Starting initialization...")
                
                # Kill any existing process on port 8080
                kill_process_on_port(8080)
                
                # Initialize Layer 1: HTTP Server  
                script_server = ScriptServer(port=8080)
                script_server.start()
                print("🔧 LAYER 1: HTTP server started on http://localhost:8080")
                
                # Initialize Layer 2: File Watcher
                script_watcher = ScriptWatcher()
                script_watcher.start()
                print("🔍 LAYER 2: File watcher started monitoring scripts/tampermonkey")
                
                # Layer 2 → Layer 3 Connection: Register script_watcher with ChromeLogger system
                def dev_mode_chrome_logger_callback(chrome_logger):
                    """Connect new ChromeLoggers to the script watcher for Layer 2 → Layer 3 handoff"""
                    if chrome_logger:
                        script_watcher.add_chrome_logger(chrome_logger)
                        print(f"🔍→🔥 LAYER CONNECTION: ChromeLogger registered with script watcher")
                
                # Override the existing registration to include script watcher connection
                original_register_chrome_logger = register_chrome_logger
                def enhanced_register_chrome_logger(chrome_logger):
                    print(f"🔧 DEV MODE: Enhanced ChromeLogger registration called for {chrome_logger}")
                    # Call original registration for cleanup
                    original_register_chrome_logger(chrome_logger)
                    # Add to script watcher for Layer 2 → Layer 3 handoff
                    dev_mode_chrome_logger_callback(chrome_logger)
                    print(f"🔧 DEV MODE: ChromeLogger added to script watcher registry")
                
                # Replace the registration function for dev mode
                globals()['register_chrome_logger'] = enhanced_register_chrome_logger
                
                # Re-set the registration function in auto_login to use the enhanced version
                set_register_chrome_logger(enhanced_register_chrome_logger)
                print("🔧 DEV MODE: Enhanced registration function set in auto_login")
                
                print("✅ SCRIPT RELOADER: All layers initialized successfully")
                print("🔍→🔥 Layer 2 → Layer 3 connection established")
                
                # Register any existing ChromeLoggers that were created before script watcher
                print(f"🔧 DEV MODE: Checking for existing ChromeLoggers to register...")
                print(f"🔧 DEV MODE: Found {len(chrome_loggers)} existing ChromeLoggers")
                for chrome_logger in chrome_loggers:
                    print(f"🔧 DEV MODE: Registering existing ChromeLogger: {chrome_logger}")
                    dev_mode_chrome_logger_callback(chrome_logger)
                
            except Exception as e:
                print(f"🔴 SCRIPT RELOADER: ERROR during initialization: {e}")
                print("🔴 Script reloader disabled due to initialization failure")
        
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