#!/usr/bin/env python3
"""
Test script for autoriskManagement.js functionality.
This script will:
1. Start Chrome with remote debugging
2. Set up the Chrome logger to capture console logs
3. Log in to Tradovate
4. Inject and run the autoriskManagement.js script
5. Analyze logs to verify behavior
"""
import os
import sys
import time
import json
import argparse
import tempfile
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import required modules
from src.auto_login import start_chrome_with_debugging, connect_to_chrome, inject_login_script
from src.chrome_logger import create_logger

class LogCapture:
    """Utility class to capture and verify logs"""
    
    def __init__(self, log_file=None):
        self.log_file = log_file
        self.captured_logs = []
    
    def log_callback(self, entry):
        """Callback to receive log entries"""
        self.captured_logs.append(entry)
        
        # Print logs with colors based on level
        level_colors = {
            'DEBUG': '\033[36m',  # Cyan
            'INFO': '\033[32m',   # Green
            'LOG': '\033[32m',    # Green
            'WARNING': '\033[33m', # Yellow
            'ERROR': '\033[31m',  # Red
            'CRITICAL': '\033[41m\033[37m'  # White on red background
        }
        reset = '\033[0m'
        
        level = entry['level']
        color = level_colors.get(level, '')
        print(f"{color}[{level}]{reset} {entry['text']}")
    
    def get_logs(self):
        """Get all captured log entries"""
        return self.captured_logs
    
    def get_logs_by_level(self, level):
        """Get captured logs of a specific level"""
        return [entry for entry in self.captured_logs if entry["level"] == level.upper()]
    
    def get_logs_containing(self, text, case_sensitive=False):
        """Get captured logs containing specific text"""
        if case_sensitive:
            return [entry for entry in self.captured_logs if text in entry["text"]]
        else:
            return [entry for entry in self.captured_logs if text.lower() in entry["text"].lower()]
    
    def wait_for_log(self, pattern=None, level=None, timeout=5.0):
        """Wait for a specific log message to appear"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            for entry in self.captured_logs:
                if level and entry["level"] != level.upper():
                    continue
                if pattern and pattern.lower() not in entry["text"].lower():
                    continue
                return entry
            time.sleep(0.1)
        return None

def main():
    parser = argparse.ArgumentParser(description="Test autoriskManagement.js functionality")
    parser.add_argument("--username", help="Tradovate username")
    parser.add_argument("--password", help="Tradovate password")
    parser.add_argument("--port", type=int, default=9222, help="Chrome debugging port (default: 9222)")
    parser.add_argument("--log-file", help="Path to save logs (default: temp file)")
    parser.add_argument("--headless", action="store_true", help="Run Chrome in headless mode")
    args = parser.parse_args()
    
    # If username/password not provided, check environment or config
    if not args.username or not args.password:
        try:
            config_path = os.path.join(project_root, 'config/credentials.json')
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        creds = json.load(f)
                        # Use first credential entry
                        if isinstance(creds, dict):
                            for username, password in creds.items():
                                args.username = username
                                args.password = password
                                break
                except json.JSONDecodeError:
                    # Try custom parsing for potentially malformed JSON
                    with open(config_path, 'r') as f:
                        content = f.read()
                        import re
                        # Extract username/password pairs
                        pairs = re.findall(r'"([^"]+)"\s*:\s*"([^"]+)"', content)
                        if pairs:
                            args.username, args.password = pairs[0]
        except Exception as e:
            print(f"Error loading credentials: {e}")
        
        # For testing, use default credentials if none found
        if not args.username or not args.password:
            args.username = "testuser"
            args.password = "testpassword"
            print(f"Using default test credentials: {args.username}/{args.password}")
    
    # Create log file
    if not args.log_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = os.path.join(project_root, "logs", "tests")
        os.makedirs(log_dir, exist_ok=True)
        args.log_file = os.path.join(log_dir, f"autorisk_test_{timestamp}.log")
    
    print(f"Testing autoriskManagement.js functionality")
    print(f"Log file: {args.log_file}")
    
    # Step 1: Start Chrome with remote debugging
    print("\n=== Starting Chrome with remote debugging ===")
    chrome_process = start_chrome_with_debugging(args.port)
    if not chrome_process:
        print("Failed to start Chrome")
        return 1
    
    try:
        # Step 2: Connect to Chrome
        print("\n=== Connecting to Chrome ===")
        browser, tab = connect_to_chrome(args.port)
        if not tab:
            print("Failed to connect to Chrome tab")
            return 1
        
        # Step 3: Set up logging
        print("\n=== Setting up Chrome logger ===")
        log_capture = LogCapture(args.log_file)
        logger = create_logger(tab, args.log_file, log_capture.log_callback)
        if not logger:
            print("Failed to create logger")
            return 1
        
        print(f"Chrome logger started, writing to {args.log_file}")
        
        # Step 4: Log in to Tradovate
        print("\n=== Logging in to Tradovate ===")
        result = inject_login_script(tab, args.username, args.password)
        if not result:
            print("Failed to inject login script")
            return 1
        
        # Wait for login to complete
        print("\n=== Waiting for login to complete ===")
        login_complete = False
        for _ in range(30):  # Wait up to 30 seconds
            try:
                eval_result = tab.Runtime.evaluate(expression="""
                (function() {
                    // Check if we're logged in
                    const isLoggedIn = document.querySelector(".bar--heading") || 
                                    document.querySelector(".app-bar--account-menu-button") ||
                                    document.querySelector(".dashboard--container") ||
                                    document.querySelector(".pane.account-selector");
                    return isLoggedIn ? "logged_in" : "not_logged_in";
                })();
                """)
                status = eval_result.get("result", {}).get("value", "")
                if status == "logged_in":
                    login_complete = True
                    print("Successfully logged in to Tradovate")
                    break
            except Exception as e:
                print(f"Error checking login status: {e}")
            time.sleep(1)
            print(".", end="", flush=True)
        
        if not login_complete:
            print("\nFailed to log in within the timeout period")
            return 1
        
        print("\n\n=== Running autoriskManagement.js ===")
        # Load the script
        script_path = os.path.join(project_root, 'scripts/tampermonkey/autoriskManagement.js')
        with open(script_path, 'r') as f:
            script_content = f.read()
        
        # Extract the core functionality (remove the IIFE wrapper)
        # Simplified approach - directly use the script content
        core_content = script_content.replace("(function() {", "").replace("})();", "").strip()
        
        if core_content.startswith("Error"):
            print(f"Failed to extract script content: {core_content}")
            return 1
        
        # Execute the script
        print("Injecting and executing autoriskManagement.js...")
        try:
            # Inject simple console log to detect Chrome liveness
            try:
                tab.Runtime.evaluate(expression="console.log('Test log: Auto Risk Management test starting');")
            except Exception as test_e:
                print(f"Warning: Test log failed: {test_e}")
            
            # Execute the main script
            tab.Runtime.evaluate(expression=core_content.replace('performAccountActions();', '// Commented out potentially destructive account actions for testing\n// performAccountActions();'))
            print("Script executed successfully")
        except Exception as e:
            print(f"Error executing script: {e}")
            return 1
        
        # Wait for logs related to auto risk management
        print("\n=== Waiting for auto risk management logs ===")
        for _ in range(30):  # Wait up to 30 seconds
            time.sleep(1)
            
            # Check for important logs
            risk_logs = log_capture.get_logs_containing("Auto Risk Management")
            table_logs = log_capture.get_logs_containing("getTableData")
            phase_logs = log_capture.get_logs_containing("updateUserColumnPhaseStatus")
            action_logs = log_capture.get_logs_containing("performAccountActions")
            
            if risk_logs and table_logs and phase_logs and action_logs:
                print("\nDetected all required log types:")
                print(f"- Auto Risk Management logs: {len(risk_logs)}")
                print(f"- Table data logs: {len(table_logs)}")
                print(f"- Phase status logs: {len(phase_logs)}")
                print(f"- Account action logs: {len(action_logs)}")
                break
        
        # Wait a moment to capture remaining logs
        time.sleep(3)
        
        # Step 6: Analyze logs
        print("\n=== Analyzing logs ===")
        all_logs = log_capture.get_logs()
        print(f"Total log entries captured: {len(all_logs)}")
        
        # Check for errors
        error_logs = log_capture.get_logs_by_level("ERROR")
        if error_logs:
            print(f"\nFound {len(error_logs)} error logs:")
            for i, error in enumerate(error_logs[:5], 1):  # Show first 5 errors
                print(f"{i}. {error['text']}")
            if len(error_logs) > 5:
                print(f"...and {len(error_logs) - 5} more errors")
        else:
            print("No error logs detected")
        
        # Check for specific function executions
        key_functions = [
            "getTableData", 
            "updateUserColumnPhaseStatus", 
            "analyzePhase",
            "performAccountActions"
        ]
        
        for func in key_functions:
            func_logs = log_capture.get_logs_containing(func)
            if func_logs:
                print(f"\nFunction '{func}' was called {len(func_logs)} times")
                # Show first log entry for this function
                if func_logs:
                    first_log = func_logs[0]
                    print(f"First log: {first_log['text']}")
            else:
                print(f"\nWARNING: No logs found for function '{func}'")
        
        # Show summary of autoriskManagement results
        print("\n=== Auto Risk Management Summary ===")
        completion_logs = log_capture.get_logs_containing("Initial risk assessment completed")
        if completion_logs:
            print("Auto risk management completed successfully")
        else:
            print("WARNING: No completion message found for auto risk management")
        
        print(f"\nLogs saved to: {args.log_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        # Clean up
        if 'logger' in locals():
            logger.stop()
        if 'chrome_process' in locals() and chrome_process:
            try:
                chrome_process.terminate()
                print("Chrome terminated")
            except Exception as e:
                print(f"Error terminating Chrome: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())