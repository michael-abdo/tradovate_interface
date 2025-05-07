#!/usr/bin/env python3
"""
Chrome logger fixtures for pytest integration.
This module provides fixtures that automatically add logging capabilities to Chrome tests.
"""
import os
import time
import json
import pytest
from unittest.mock import MagicMock
from datetime import datetime

# Add project root to path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.chrome_logger import ChromeLogger, create_logger

class LogCapture:
    """Utility class to capture and verify logs during tests"""
    
    def __init__(self, log_file=None):
        self.log_file = log_file
        self.captured_logs = []
        self.verify_callbacks = {}
    
    def log_callback(self, entry):
        """Callback to receive log entries"""
        self.captured_logs.append(entry)
        
        # Process any registered verification callbacks
        for key, callback in self.verify_callbacks.items():
            if callback(entry):
                # If callback returns True, it indicates this entry matches a verification
                self.verify_callbacks.pop(key)
                break
    
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
    
    def clear_logs(self):
        """Clear captured logs"""
        self.captured_logs = []
    
    def verify_logs(self, expected_entries, partial_match=True):
        """
        Verify that expected log entries exist in captured logs
        
        Args:
            expected_entries: List of expected log entries or patterns
            partial_match: If True, check for substring matches instead of exact matches
            
        Returns:
            (bool, list): Success status and list of missing entries
        """
        missing = []
        
        for expected in expected_entries:
            found = False
            expected_level = expected.get("level", "").upper()
            expected_text = expected.get("text", "")
            
            for entry in self.captured_logs:
                # Match level if specified
                if expected_level and entry["level"] != expected_level:
                    continue
                
                # Match text
                if partial_match:
                    if expected_text.lower() in entry["text"].lower():
                        found = True
                        break
                else:
                    if entry["text"] == expected_text:
                        found = True
                        break
            
            if not found:
                missing.append(expected)
        
        return len(missing) == 0, missing
    
    def register_verification(self, key, verify_func):
        """
        Register a callback to verify when a specific log entry appears
        
        Args:
            key: Unique identifier for this verification
            verify_func: Function that takes a log entry and returns True if it matches
        """
        self.verify_callbacks[key] = verify_func
    
    def wait_for_log(self, pattern=None, level=None, timeout=5.0):
        """
        Wait for a specific log message to appear
        
        Args:
            pattern: Text pattern to match in the log
            level: Log level to match
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if the log entry was found, False if timeout
        """
        def check_logs():
            for entry in self.captured_logs:
                if level and entry["level"] != level.upper():
                    continue
                if pattern and pattern.lower() not in entry["text"].lower():
                    continue
                return True
            return False
        
        # Check if already in logs
        if check_logs():
            return True
        
        # Set up verification callback
        found = [False]  # Using a list for mutable state in closure
        
        def verify_func(entry):
            if level and entry["level"] != level.upper():
                return False
            if pattern and pattern.lower() not in entry["text"].lower():
                return False
            found[0] = True
            return True
            
        key = f"wait_for_log_{time.time()}"
        self.register_verification(key, verify_func)
        
        # Wait for the log to appear
        start_time = time.time()
        while time.time() - start_time < timeout:
            if found[0] or key not in self.verify_callbacks:
                return True
            time.sleep(0.1)
        
        # Timeout occurred, remove the callback
        if key in self.verify_callbacks:
            self.verify_callbacks.pop(key)
        return False


@pytest.fixture
def chrome_logger(request, tmp_path):
    """
    Fixture that provides a ChromeLogger instance and log verification tools
    
    This fixture will:
    1. Create a temporary log file for the test
    2. Set up a ChromeLogger with mock or real Chrome tab
    3. Provide utilities to verify logs during the test
    4. Clean up resources after the test
    
    Returns:
        tuple: (logger, log_capture)
            - logger: ChromeLogger instance
            - log_capture: LogCapture utility to access and verify logs
    """
    # Create unique log file name for this test
    test_name = request.node.name.replace(" ", "_").replace(":", "_").replace("[", "_").replace("]", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logs_dir = tmp_path / "chrome_logs"
    logs_dir.mkdir(exist_ok=True)
    log_file = str(logs_dir / f"{test_name}_{timestamp}.log")
    
    # Check if we have a real tab or need to create a mock one
    tab = getattr(request, "param", {}).get("tab", None)
    if tab is None:
        tab = MagicMock()
        tab.Runtime = MagicMock()
        tab.Log = MagicMock()
        tab.Console = MagicMock()
        tab.Page = MagicMock()
    
    # Create log capture utility
    log_capture = LogCapture(log_file)
    
    # Create logger and start it
    logger = ChromeLogger(tab, log_file)
    logger.add_callback(log_capture.log_callback)
    logger.start()
    
    yield logger, log_capture
    
    # Clean up
    logger.stop()


@pytest.fixture
def real_chrome_logger(request):
    """
    Fixture that connects to a real Chrome instance and provides logger
    
    This requires a running Chrome instance with remote debugging enabled.
    
    Args:
        request: Pytest request object, can contain test parameters
        
    Returns:
        tuple: (tab, browser, logger, log_capture) - Chrome tab, browser, logger and log capture utility
    """
    import pychrome
    import tempfile
    
    # Get debugging port from parameters or use default
    port = getattr(request, "param", {}).get("port", 9222)
    
    # Connect to Chrome
    browser = pychrome.Browser(url=f"http://localhost:{port}")
    
    try:
        # Find or create a tab
        tabs = browser.list_tab()
        if not tabs:
            tab = browser.new_tab()
        else:
            tab = tabs[0]
        
        tab.start()
        tab.Page.enable()
        
        # Set up logger with temp file
        temp_dir = tempfile.mkdtemp(prefix="chrome_logger_test_")
        log_file = os.path.join(temp_dir, "chrome_debug.log")
        
        # Create log capture utility
        log_capture = LogCapture(log_file)
        
        # Create the logger
        logger = create_logger(tab, log_file, log_capture.log_callback)
        
        if not logger:
            pytest.skip("Failed to create logger for real Chrome")
            
        yield tab, browser, logger, log_capture
        
        # Clean up
        logger.stop()
        try:
            tab.stop()
        except:
            pass
            
    except Exception as e:
        pytest.skip(f"Failed to connect to Chrome on port {port}: {e}")