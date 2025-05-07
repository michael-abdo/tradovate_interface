#!/usr/bin/env python3
import pytest
import os
import sys
import time
import json
import signal
import subprocess
from unittest.mock import patch

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules to test
from src import auto_login
from src import app
from src.chrome_logger import ChromeLogger

class TestIntegration:
    """Integration tests for the Tradovate Interface.
    
    These tests run with actual Chrome instances and interact with the real UI.
    They use a sandbox/paper trading account for safety.
    
    To run only integration tests: pytest -xvs tests/test_integration.py
    """
    
    @classmethod
    def setup_class(cls):
        """Set up test environment once before all tests."""
        # Check if we're in CI or want to skip real browser tests
        if os.environ.get('SKIP_INTEGRATION_TESTS', 'false').lower() == 'true':
            pytest.skip("Skipping integration tests based on environment variable")
        
        # Save current credentials
        cls.backup_credentials()
        
        # Create test credentials for a paper trading account
        # Use environment variables if available, otherwise use test values
        cls.create_test_credentials()
    
    @classmethod
    def teardown_class(cls):
        """Clean up after all tests have finished."""
        # Restore original credentials
        cls.restore_credentials()
    
    @classmethod
    def backup_credentials(cls):
        """Backup the original credentials file."""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        credentials_path = os.path.join(project_root, 'config/credentials.json')
        backup_path = os.path.join(project_root, 'config/credentials.json.bak')
        
        if os.path.exists(credentials_path):
            try:
                with open(credentials_path, 'r') as f:
                    cls.original_credentials = f.read()
            except Exception as e:
                print(f"Warning: Failed to backup credentials: {e}")
                cls.original_credentials = None
        else:
            cls.original_credentials = None
    
    @classmethod
    def create_test_credentials(cls):
        """Create test credentials for integration testing."""
        # Use environment variables if available
        username = os.environ.get('TRADOVATE_TEST_USERNAME', 'test_user@example.com')
        password = os.environ.get('TRADOVATE_TEST_PASSWORD', 'test_password')
        
        credentials = {username: password}
        
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        credentials_path = os.path.join(project_root, 'config/credentials.json')
        
        # Write test credentials
        try:
            with open(credentials_path, 'w') as f:
                json.dump(credentials, f, indent=2)
        except Exception as e:
            pytest.skip(f"Failed to create test credentials: {e}")
    
    @classmethod
    def restore_credentials(cls):
        """Restore the original credentials file."""
        if cls.original_credentials is not None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            credentials_path = os.path.join(project_root, 'config/credentials.json')
            
            try:
                with open(credentials_path, 'w') as f:
                    f.write(cls.original_credentials)
            except Exception as e:
                print(f"Warning: Failed to restore credentials: {e}")
    
    @pytest.fixture
    def chrome_instance(self):
        """Fixture that provides a Chrome instance for testing."""
        # Check if TRADOVATE_TEST_SKIP_BROWSER is set to skip browser launch
        if os.environ.get('TRADOVATE_TEST_SKIP_BROWSER', 'false').lower() == 'true':
            pytest.skip("Skipping test that requires browser launch")
        
        # Load test credentials
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        credentials_path = os.path.join(project_root, 'config/credentials.json')
        
        try:
            with open(credentials_path, 'r') as f:
                creds = json.load(f)
                username, password = next(iter(creds.items()))
        except Exception as e:
            pytest.skip(f"Failed to load test credentials: {e}")
        
        # Start Chrome with debugging
        test_port = 9222
        process = auto_login.start_chrome_with_debugging(test_port)
        
        if not process:
            pytest.skip("Failed to start Chrome")
        
        try:
            # Wait for Chrome to initialize
            time.sleep(3)
            
            # Connect to Chrome
            browser, tab = auto_login.connect_to_chrome(test_port)
            
            if not tab:
                pytest.skip("Failed to connect to Chrome tab")
            
            # Create a Chrome instance object
            instance = auto_login.ChromeInstance(test_port, username, password)
            instance.browser = browser
            instance.tab = tab
            instance.process = process
            
            # Inject login script but don't execute it (for faster tests)
            if os.environ.get('TRADOVATE_TEST_LOGIN', 'false').lower() == 'true':
                auto_login.inject_login_script(tab, username, password)
                auto_login.disable_alerts(tab)
            
            yield instance
            
        finally:
            # Always clean up Chrome process
            if process:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except:
                    # Force kill if terminate doesn't work
                    try:
                        os.kill(process.pid, signal.SIGKILL)
                    except:
                        pass
    
    def test_chrome_starts_and_connects(self, chrome_instance):
        """Test that Chrome starts and we can connect to it."""
        assert chrome_instance is not None
        assert chrome_instance.process is not None
        assert chrome_instance.browser is not None
        assert chrome_instance.tab is not None
    
    def test_tradovate_connection(self, chrome_instance):
        """Test that TradovateConnection can be created and used."""
        # Create a TradovateConnection using the existing chrome instance
        connection = app.TradovateConnection(chrome_instance.port, "Test Account")
        
        # Override the default tab with our test tab
        connection.tab = chrome_instance.tab
        
        # Test injecting the tampermonkey script
        result = connection.inject_tampermonkey()
        assert result is True
        
        # Test creating UI (don't assert specific response as it depends on the page state)
        connection.create_ui()
        
        # Test updating symbol (this should work regardless of login state)
        result = connection.update_symbol("ES")
        assert "error" not in result
    
    def test_controller_list_connections(self, chrome_instance):
        """Test that the controller can list connections."""
        # Create a controller
        controller = app.TradovateController(base_port=chrome_instance.port)
        
        # There should be at least one connection (our test Chrome)
        assert len(controller.connections) >= 1
    
    def test_chrome_logger(self, chrome_instance):
        """Test that ChromeLogger can log from a real Chrome instance."""
        # Create a logger
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_dir = os.path.join(project_root, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_path = os.path.join(log_dir, 'integration_test.log')
        
        logger = ChromeLogger(chrome_instance.tab, log_path)
        logger.start()
        
        # Execute JavaScript to generate a log
        chrome_instance.tab.Runtime.evaluate(expression="""
            console.log("Integration test log message");
            console.error("Integration test error message");
        """)
        
        # Wait a moment for logs to be processed
        time.sleep(1)
        
        # Stop the logger
        logger.stop()
        
        # Check if the log file contains our messages
        with open(log_path, 'r') as f:
            log_content = f.read()
            assert "Integration test log message" in log_content
            assert "Integration test error message" in log_content
    
    @pytest.mark.skipif(
        os.environ.get('TRADOVATE_TEST_LOGIN', 'false').lower() != 'true',
        reason="Requires actual login, set TRADOVATE_TEST_LOGIN=true to run"
    )
    def test_full_workflow(self, chrome_instance):
        """Test a complete workflow from login to trade operations.
        
        This test is skipped by default as it requires actual login.
        Set TRADOVATE_TEST_LOGIN=true to run it.
        """
        # Create controller and connection
        controller = app.TradovateController(base_port=chrome_instance.port)
        
        # Execute UI creation
        results = controller.execute_on_all('create_ui')
        assert len(results) >= 1
        
        # Update symbol
        results = controller.execute_on_all('update_symbol', 'ES')
        assert len(results) >= 1
        
        # Run risk management
        results = controller.execute_on_all('run_risk_management')
        assert len(results) >= 1
        
        # We don't execute actual trades in integration tests
        # But we can check that the function runs without errors
        results = controller.execute_on_all(
            'auto_trade', 'ES', 1, 'Buy', 100, 40, 0.25
        )
        assert len(results) >= 1
        
        # Execute exit positions (this won't actually close positions if none exist)
        results = controller.execute_on_all('exit_positions', 'ES')
        assert len(results) >= 1


# Allow running the tests directly
if __name__ == "__main__":
    # When running directly, set environment variables for proper tests
    os.environ['TRADOVATE_TEST_USERNAME'] = input("Enter test username: ")
    os.environ['TRADOVATE_TEST_PASSWORD'] = input("Enter test password: ")
    os.environ['TRADOVATE_TEST_LOGIN'] = input("Run login tests? (true/false): ")
    
    pytest.main(["-xvs", "test_integration.py"])