#!/usr/bin/env python3
"""
Simple smoke test for Tradovate Interface.

This test does a simple check of the main components:
1. Starts Chrome
2. Auto-logins 
3. Starts dashboard
4. Checks API connectivity
"""

import pytest
import os
import sys
import time
import json
import subprocess
import threading
import logging
import requests

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules to test
from src import auto_login
from src import app
from src import dashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_smoke')

class TestSmoke:
    """Simple smoke test for Tradovate Interface."""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment."""
        cls.chrome_instance = None
        cls.dashboard_thread = None
    
    @classmethod
    def teardown_class(cls):
        """Clean up after tests."""
        # Stop Chrome instance
        if cls.chrome_instance:
            try:
                cls.chrome_instance.stop()
            except Exception as e:
                logger.error(f"Error stopping Chrome: {e}")
    
    def test_smoke(self):
        """Run a basic smoke test."""
        # Check if we should skip browser tests
        if os.environ.get('SKIP_BROWSER_TESTS', 'false').lower() == 'true':
            pytest.skip("Skipping browser tests")
        
        # Step 1: Start Chrome
        logger.info("Starting Chrome...")
        self.chrome_instance = self._start_chrome()
        assert self.chrome_instance, "Failed to start Chrome"
        
        # Step 2: Auto-login if credentials provided
        if os.environ.get('TRADOVATE_TEST_LOGIN', 'false').lower() == 'true':
            logger.info("Performing auto-login...")
            login_success = self._perform_auto_login()
            assert login_success, "Failed to login"
        
        # Step 3: Start dashboard
        logger.info("Starting dashboard...")
        dashboard_started = self._start_dashboard()
        assert dashboard_started, "Failed to start dashboard"
        
        # Step 4: Check API connectivity
        logger.info("Checking API connectivity...")
        api_working = self._check_api()
        assert api_working, "Dashboard API not working"
        
        logger.info("Smoke test completed successfully!")
    
    def _start_chrome(self):
        """Start Chrome with remote debugging."""
        try:
            username = os.environ.get('TRADOVATE_TEST_USERNAME', 'test_user@example.com')
            password = os.environ.get('TRADOVATE_TEST_PASSWORD', 'test_password')
            
            # Start Chrome with debugging
            test_port = 9222
            process = auto_login.start_chrome_with_debugging(test_port)
            
            if not process:
                logger.error("Failed to start Chrome")
                return None
            
            # Wait for Chrome to initialize
            time.sleep(3)
            
            # Connect to Chrome
            browser, tab = auto_login.connect_to_chrome(test_port)
            
            if not tab:
                logger.error("Failed to connect to Chrome tab")
                return None
            
            # Create a Chrome instance object
            instance = auto_login.ChromeInstance(test_port, username, password)
            instance.browser = browser
            instance.tab = tab
            instance.process = process
            
            logger.info(f"Chrome started successfully on port {test_port}")
            return instance
            
        except Exception as e:
            logger.error(f"Error starting Chrome: {e}")
            return None
    
    def _perform_auto_login(self):
        """Perform auto-login to Tradovate."""
        try:
            if not self.chrome_instance:
                logger.error("No Chrome instance available")
                return False
            
            # Disable alerts
            auto_login.disable_alerts(self.chrome_instance.tab)
            
            # Inject and execute login script
            auto_login.inject_login_script(
                self.chrome_instance.tab, 
                self.chrome_instance.username, 
                self.chrome_instance.password
            )
            
            # Wait for login to complete (up to 20 seconds)
            max_wait = 20
            for i in range(max_wait):
                # Check for login status
                check_js = """
                (function() {
                    const isLoggedIn = document.querySelector(".bar--heading") || 
                                    document.querySelector(".app-bar--account-menu-button") ||
                                    document.querySelector(".dashboard--container") ||
                                    document.querySelector(".pane.account-selector");
                    return !!isLoggedIn;
                })();
                """
                result = self.chrome_instance.tab.Runtime.evaluate(expression=check_js)
                is_logged_in = result.get("result", {}).get("value", False)
                
                if is_logged_in:
                    logger.info(f"Successfully logged in after {i} seconds")
                    return True
                
                time.sleep(1)
            
            logger.error("Failed to login after waiting 20 seconds")
            return False
            
        except Exception as e:
            logger.error(f"Error during auto-login: {e}")
            return False
    
    def _start_dashboard(self):
        """Start the dashboard."""
        try:
            if not self.chrome_instance:
                logger.error("No Chrome instance available")
                return False
            
            # Create controller with our Chrome instance
            controller = app.TradovateController(base_port=self.chrome_instance.port)
            
            # Start dashboard in a separate thread
            def run_dashboard():
                try:
                    dashboard.app.run(host='0.0.0.0', port=6001)
                except Exception as e:
                    logger.error(f"Error running dashboard: {e}")
            
            self.dashboard_thread = threading.Thread(target=run_dashboard)
            self.dashboard_thread.daemon = True
            self.dashboard_thread.start()
            
            # Give the dashboard time to start
            time.sleep(3)
            
            logger.info("Dashboard started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting dashboard: {e}")
            return False
    
    def _check_api(self):
        """Check if the dashboard API is working."""
        try:
            # Try to get accounts data
            response = requests.get("http://localhost:6001/api/accounts", timeout=5)
            
            if response.status_code == 200:
                logger.info("Dashboard API is working")
                return True
            else:
                logger.error(f"Dashboard API returned status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking dashboard API: {e}")
            return False


if __name__ == "__main__":
    pytest.main(["-xvs", "tests/test_smoke.py"])