#!/usr/bin/env python3
import os
import pytest
from unittest.mock import MagicMock, patch
import json

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


# We're using direct patching in tests instead of this fixture approach to avoid recursion issues