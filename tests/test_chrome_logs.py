#!/usr/bin/env python3
"""
Tests for Chrome logging integration in tests.
This demonstrates how to use the Chrome logger fixtures to capture and verify
browser console logs during tests.
"""
import pytest
import os
import time
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.chrome_logger import ChromeLogger

class TestChromeLogging:
    """Test Chrome logging capabilities"""
    
    def test_mock_chrome_logger(self, mock_tab_with_logger):
        """Test logging with a mock Chrome tab"""
        # Unpack the fixture
        mock_tab, logger, log_capture = mock_tab_with_logger
        
        # Set callbacks on mock tab (these are not set automatically in test fixture)
        mock_tab.Runtime.consoleAPICalled = logger._on_console_api
        mock_tab.Runtime.exceptionThrown = logger._on_exception
        mock_tab.Log.entryAdded = logger._on_log_entry
        mock_tab.Console.messageAdded = logger._on_console_message
        
        # Simulate various log events from Chrome
        mock_tab.trigger_console_api(type="log", args=[{"value": "Test log message"}])
        mock_tab.trigger_console_api(type="warning", args=[{"value": "Test warning message"}])
        mock_tab.trigger_console_api(type="error", args=[{"value": "Test error message"}])
        mock_tab.trigger_exception(description="Test exception description")
        
        # Simulate a log entry (browser log)
        mock_tab.trigger_log_event({"level": "INFO", "text": "Test browser log message"})
        
        # Sleep to ensure async log processing completes
        import time
        time.sleep(0.1)
        
        # Verify that logs were captured
        logs = log_capture.get_logs()
        assert len(logs) > 0  # At least some logs were captured
        
        # Check for specific messages rather than counts
        assert log_capture.get_logs_containing("Test log message")
        assert log_capture.get_logs_containing("Test warning message") or log_capture.get_logs_containing("Test browser log message")
        assert log_capture.get_logs_containing("Test error message")
        assert log_capture.get_logs_containing("Test exception description")
    
    def test_complex_log_verification(self, mock_tab_with_logger):
        """Test more complex log verification capabilities"""
        mock_tab, logger, log_capture = mock_tab_with_logger
        
        # Check verification API
        success, missing = log_capture.verify_logs([
            {"level": "INFO", "text": "This does not exist yet"}
        ])
        
        assert not success
        assert len(missing) == 1
        
        # Trigger a log event
        mock_tab.trigger_console_api(type="info", args=[{"value": "This is a test message"}])
        
        # Verify with partial matching (should succeed)
        success, missing = log_capture.verify_logs([
            {"level": "INFO", "text": "test message"}
        ], partial_match=True)
        
        assert success
        assert len(missing) == 0
        
        # Verify with exact matching (should fail)
        success, missing = log_capture.verify_logs([
            {"level": "INFO", "text": "test message"}
        ], partial_match=False)
        
        assert not success
        assert len(missing) == 1
        
        # Test waiting for logs
        # First test with an already existing log
        assert log_capture.wait_for_log(pattern="test message", level="INFO", timeout=0.1)
        
        # Then test with a log that will appear later
        def trigger_delayed_log():
            time.sleep(0.5)
            mock_tab.trigger_console_api(type="debug", args=[{"value": "Delayed debug message"}])
            
        import threading
        thread = threading.Thread(target=trigger_delayed_log)
        thread.daemon = True
        thread.start()
        
        # Wait for the log that will be triggered soon
        assert log_capture.wait_for_log(pattern="delayed debug", timeout=2.0)

    def test_real_chrome_logger(self, real_chrome_logger):
        """Test logging with a real Chrome browser instance"""
        # This test requires a running Chrome instance with remote debugging
        # You can start one using: ./tests/test_chrome_connection.sh start
        
        # Unpack the fixture
        tab, browser, logger, log_capture = real_chrome_logger
        
        # Navigate to a test URL
        tab.Page.navigate(url="https://example.com")
        
        # Execute JavaScript to generate console logs
        js_code = """
        console.log("Test log from real Chrome");
        console.warn("Test warning from real Chrome");
        console.error("Test error from real Chrome");
        try {
            throw new Error("Test exception from real Chrome");
        } catch (e) {
            console.error(e);
        }
        """
        tab.Runtime.evaluate(expression=js_code)
        
        # Wait for logs to be captured
        time.sleep(1)
        
        # Verify that logs were captured
        logs = log_capture.get_logs()
        
        # Print logs for debugging
        for log in logs:
            print(f"[{log['level']}] {log['text']}")
        
        # Verify specific logs
        assert log_capture.wait_for_log(pattern="Test log from real Chrome", timeout=3.0)
        assert log_capture.wait_for_log(pattern="Test warning from real Chrome", timeout=0.1)
        assert log_capture.wait_for_log(pattern="Test error from real Chrome", timeout=0.1)
        assert log_capture.wait_for_log(pattern="Test exception from real Chrome", timeout=0.1)

if __name__ == "__main__":
    pytest.main(["-v", "test_chrome_logs.py"])