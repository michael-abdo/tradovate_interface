#!/usr/bin/env python3
import pytest
import os
import sys
import time
import json
import signal
import subprocess
from unittest.mock import patch
import logging
import threading

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules to test
from src import auto_login
from src import app
from src.chrome_logger import ChromeLogger
from src import dashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'test_full_workflow.log'))
    ]
)
logger = logging.getLogger('test_full_workflow')

class TestFullWorkflow:
    """Full workflow test for Tradovate Interface.
    
    This test executes a complete workflow:
    1. Starts Chrome with debugging
    2. Auto-logins to Tradovate
    3. Starts the dashboard
    4. Executes a trade
    5. Confirms the position in the account
    
    These tests run with actual Chrome instances and interact with the real UI.
    They use a sandbox/paper trading account for safety.
    
    To run this test: pytest -xvs tests/test_full_workflow.py
    """
    
    @classmethod
    def setup_class(cls):
        """Set up test environment once before all tests."""
        # Check if we're in CI or want to skip real browser tests
        if os.environ.get('SKIP_INTEGRATION_TESTS', 'false').lower() == 'true':
            pytest.skip("Skipping integration tests based on environment variable")
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Save current credentials
        cls.backup_credentials()
        
        # Create test credentials for a paper trading account
        # Use environment variables if available, otherwise use test values
        cls.create_test_credentials()
        
        # Store created objects for cleanup
        cls.chrome_instances = []
        cls.dashboard_thread = None
        cls.dashboard_app = None
    
    @classmethod
    def teardown_class(cls):
        """Clean up after all tests have finished."""
        # Stop dashboard if running
        if cls.dashboard_thread and cls.dashboard_thread.is_alive():
            logger.info("Stopping dashboard thread")
            
        # Stop Chrome instances
        for instance in cls.chrome_instances:
            try:
                logger.info(f"Stopping Chrome instance for {instance.username}")
                instance.stop()
            except Exception as e:
                logger.error(f"Error stopping Chrome instance: {e}")
        
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
                logger.info(f"Backed up original credentials")
            except Exception as e:
                logger.error(f"Failed to backup credentials: {e}")
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
            logger.info(f"Created test credentials for {username}")
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
                logger.info("Restored original credentials")
            except Exception as e:
                logger.error(f"Failed to restore credentials: {e}")
    
    def test_full_workflow(self):
        """Test a complete workflow from login to trade execution and position verification."""
        # Skip this test if TRADOVATE_TEST_LOGIN is not set to true
        if os.environ.get('TRADOVATE_TEST_LOGIN', 'false').lower() != 'true':
            pytest.skip("Test requires login, set TRADOVATE_TEST_LOGIN=true to run")
        
        # Step 1: Start Chrome with remote debugging
        logger.info("Step 1: Starting Chrome with remote debugging")
        self._start_chrome()
        
        # Step 2: Auto-login to Tradovate
        logger.info("Step 2: Performing auto-login")
        self._perform_auto_login()
        
        # Step 3: Start the dashboard
        logger.info("Step 3: Starting dashboard")
        self._start_dashboard()
        
        # Step 4: Execute a trade
        logger.info("Step 4: Executing a trade")
        trade_success = self._execute_trade()
        
        # Step 5: Verify position
        logger.info("Step 5: Verifying position")
        position_verified = self._verify_position()
        
        # Final assertions
        assert trade_success, "Failed to execute trade"
        assert position_verified, "Failed to verify position"
    
    def _start_chrome(self):
        """Start Chrome with remote debugging."""
        try:
            # Load credentials
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            credentials_path = os.path.join(project_root, 'config/credentials.json')
            
            with open(credentials_path, 'r') as f:
                creds = json.load(f)
                username, password = next(iter(creds.items()))
            
            # Start Chrome with debugging
            test_port = 9222
            process = auto_login.start_chrome_with_debugging(test_port)
            
            if not process:
                pytest.fail("Failed to start Chrome")
            
            # Wait for Chrome to initialize
            time.sleep(3)
            
            # Connect to Chrome
            browser, tab = auto_login.connect_to_chrome(test_port)
            
            if not tab:
                pytest.fail("Failed to connect to Chrome tab")
            
            # Create a Chrome instance object
            instance = auto_login.ChromeInstance(test_port, username, password)
            instance.browser = browser
            instance.tab = tab
            instance.process = process
            
            # Store the instance for cleanup
            self.__class__.chrome_instances.append(instance)
            
            logger.info(f"Chrome started successfully on port {test_port}")
            return instance
            
        except Exception as e:
            logger.error(f"Error starting Chrome: {e}")
            pytest.fail(f"Failed to start Chrome: {e}")
    
    def _perform_auto_login(self):
        """Perform auto-login to Tradovate."""
        try:
            if not self.__class__.chrome_instances:
                pytest.fail("No Chrome instances available")
            
            instance = self.__class__.chrome_instances[0]
            
            # Disable alerts
            auto_login.disable_alerts(instance.tab)
            
            # Inject and execute login script
            auto_login.inject_login_script(instance.tab, instance.username, instance.password)
            
            # Wait for login to complete (up to 60 seconds)
            max_wait = 60
            for i in range(max_wait):
                # Check if we're logged in
                check_js = """
                (function() {
                    const isLoggedIn = document.querySelector(".bar--heading") || 
                                      document.querySelector(".app-bar--account-menu-button") ||
                                      document.querySelector(".dashboard--container") ||
                                      document.querySelector(".pane.account-selector");
                    return !!isLoggedIn;
                })();
                """
                result = instance.tab.Runtime.evaluate(expression=check_js)
                is_logged_in = result.get("result", {}).get("value", False)
                
                if is_logged_in:
                    logger.info(f"Successfully logged in after {i} seconds")
                    return True
                
                # Not logged in yet, wait and check for account selection page
                account_selection_js = """
                (function() {
                    const accessButtons = Array.from(document.querySelectorAll("button.tm"))
                        .filter(btn => 
                            btn.textContent.trim() === "Access Simulation" || 
                            btn.textContent.trim() === "Launch"
                        );
                    if (accessButtons.length > 0) {
                        console.log("Clicking Access Simulation button");
                        accessButtons[0].click();
                        return true;
                    }
                    return false;
                })();
                """
                selection_result = instance.tab.Runtime.evaluate(expression=account_selection_js)
                if selection_result.get("result", {}).get("value", False):
                    logger.info("Clicked account selection button")
                
                time.sleep(1)
            
            # If we get here, login failed
            pytest.fail("Failed to login after waiting 60 seconds")
            
        except Exception as e:
            logger.error(f"Error during auto-login: {e}")
            pytest.fail(f"Failed to perform auto-login: {e}")
    
    def _start_dashboard(self):
        """Start the dashboard."""
        try:
            if not self.__class__.chrome_instances:
                pytest.fail("No Chrome instances available")
            
            # Create controller with our Chrome instance
            instance = self.__class__.chrome_instances[0]
            controller = app.TradovateController(base_port=instance.port)
            
            # Inject account data function
            dashboard.inject_account_data_function()
            
            # Start dashboard in a separate thread
            def run_dashboard():
                try:
                    dashboard.app.run(host='0.0.0.0', port=6001)
                except Exception as e:
                    logger.error(f"Error running dashboard: {e}")
            
            self.__class__.dashboard_thread = threading.Thread(target=run_dashboard)
            self.__class__.dashboard_thread.daemon = True
            self.__class__.dashboard_thread.start()
            
            # Give the dashboard time to start
            time.sleep(3)
            
            logger.info("Dashboard started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting dashboard: {e}")
            pytest.fail(f"Failed to start dashboard: {e}")
    
    def _execute_trade(self):
        """Execute a trade using the dashboard API."""
        try:
            if not self.__class__.chrome_instances:
                pytest.fail("No Chrome instances available")
            
            import requests
            
            # Trade parameters
            trade_data = {
                "symbol": "NQ",
                "quantity": 1,
                "action": "Buy",
                "tp_ticks": 100,
                "sl_ticks": 40,
                "tick_size": 0.25,
                "enable_tp": True,
                "enable_sl": True,
                "account": "all"
            }
            
            # Execute trade via dashboard API
            response = requests.post("http://localhost:6001/api/trade", json=trade_data, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Trade execution failed: {response.text}")
                return False
            
            result = response.json()
            logger.info(f"Trade execution result: {result}")
            
            # Check if any accounts were affected
            if result.get("accounts_affected", 0) < 1:
                logger.error("No accounts were affected by the trade")
                return False
            
            # Wait for the trade to be processed
            time.sleep(5)
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return False
    
    def _verify_position(self):
        """Verify that the position was created."""
        try:
            if not self.__class__.chrome_instances:
                pytest.fail("No Chrome instances available")
            
            import requests
            
            # Get account data from dashboard API
            response = requests.get("http://localhost:6001/api/accounts", timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Failed to get account data: {response.text}")
                return False
            
            accounts_data = response.json()
            logger.info(f"Retrieved data for {len(accounts_data)} accounts")
            
            # Check if any account has a position for NQ
            has_position = False
            
            for account in accounts_data:
                # Look for Net Pos field which might have different names
                position_fields = ['Net Pos', 'Net Position', 'NetPos']
                for field in position_fields:
                    if field in account and account.get(field) != "0" and account.get(field) != 0:
                        logger.info(f"Found position in account: {account}")
                        has_position = True
                        break
                
                if has_position:
                    break
            
            return has_position
            
        except Exception as e:
            logger.error(f"Error verifying position: {e}")
            return False


if __name__ == "__main__":
    # When running directly, set environment variables for proper tests
    if not os.environ.get('TRADOVATE_TEST_USERNAME'):
        os.environ['TRADOVATE_TEST_USERNAME'] = input("Enter test username: ")
    
    if not os.environ.get('TRADOVATE_TEST_PASSWORD'):
        os.environ['TRADOVATE_TEST_PASSWORD'] = input("Enter test password: ")
    
    if not os.environ.get('TRADOVATE_TEST_LOGIN'):
        os.environ['TRADOVATE_TEST_LOGIN'] = input("Run login tests? (true/false): ")
    
    pytest.main(["-xvs", "tests/test_full_workflow.py"])