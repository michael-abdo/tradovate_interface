#!/usr/bin/env python3
import os
import pytest
from unittest.mock import MagicMock, patch
import json
import sys
import logging
from datetime import datetime

# Add the project root to the path so we can import the chrome_logger_fixture
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from chrome_logger_fixture import chrome_logger, real_chrome_logger, LogCapture

# Set up test logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("tradovate_test")

# Mock for pychrome.Tab
class MockTab:
    def __init__(self):
        # Create mock methods that would be available on a real tab
        self.Page = MagicMock()
        self.Page.enable = MagicMock()
        
        self.Runtime = MagicMock()
        self.Runtime.evaluate = MagicMock()
        
        self.Log = MagicMock()
        self.Log.enable = MagicMock()
        self.Log.entryAdded = None
        
        self.Console = MagicMock()
        self.Console.enable = MagicMock()
        self.Console.messageAdded = None
        
        self.start = MagicMock()
        self.stop = MagicMock()

    def mock_evaluate_result(self, value):
        """Helper to set up a return value for Runtime.evaluate"""
        self.Runtime.evaluate.return_value = {"result": {"value": value}}
        
    def trigger_log_event(self, entry):
        """Simulate a log event being triggered"""
        if callable(self.Log.entryAdded):
            self.Log.entryAdded(entry=entry)
            
    def trigger_console_api(self, type="log", args=None):
        """Simulate a console API call event"""
        if callable(self.Runtime.consoleAPICalled):
            if args is None:
                args = [{"value": "Test message"}]
            self.Runtime.consoleAPICalled(type=type, args=args)
            
    def trigger_exception(self, description="Test exception"):
        """Simulate an exception being thrown"""
        if callable(self.Runtime.exceptionThrown):
            self.Runtime.exceptionThrown(
                exceptionDetails={
                    "exception": {"description": description},
                    "url": "http://example.com"
                }
            )


# Mock for pychrome.Browser
class MockBrowser:
    def __init__(self, tabs=None):
        self.tabs = tabs if tabs is not None else []
        self.list_tab = MagicMock(return_value=self.tabs)
        self.new_tab = MagicMock()
        
    def add_tab(self, tab):
        """Add a tab to the browser's tab list"""
        self.tabs.append(tab)
        self.list_tab.return_value = self.tabs
        
    def set_new_tab(self, tab):
        """Set the tab that will be returned by new_tab"""
        self.new_tab.return_value = tab


@pytest.fixture
def mock_tab():
    """Fixture that provides a mock Tab"""
    return MockTab()


@pytest.fixture
def mock_browser():
    """Fixture that provides a mock Browser"""
    return MockBrowser()


@pytest.fixture
def mock_credentials():
    """Fixture that provides mock credentials"""
    return {
        "testuser": "testpassword",
        "user2": "pass2"
    }


@pytest.fixture
def mock_tab_with_logger(mock_tab, tmp_path):
    """
    Fixture that provides a mock Tab with an integrated logger
    
    Returns:
        tuple: (mock_tab, logger, log_capture)
    """
    # Create a log file in the temp directory
    logs_dir = tmp_path / "chrome_logs"
    logs_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = str(logs_dir / f"chrome_mock_{timestamp}.log")
    
    # Set up the LogCapture
    log_capture = LogCapture(log_file)
    
    # Import ChromeLogger
    from src.chrome_logger import ChromeLogger
    
    # Create and start logger
    logger = ChromeLogger(mock_tab, log_file)
    logger.add_callback(log_capture.log_callback)
    logger.start()
    
    yield mock_tab, logger, log_capture
    
    # Clean up
    logger.stop()


@pytest.fixture(scope="session")
def logs_dir():
    """
    Fixture that provides a directory for test logs
    
    Returns:
        str: Path to logs directory
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = os.path.join(project_root, "logs", "tests")
    os.makedirs(logs_dir, exist_ok=True)
    return logs_dir


# We're using direct patching in tests instead of this fixture approach to avoid recursion issues