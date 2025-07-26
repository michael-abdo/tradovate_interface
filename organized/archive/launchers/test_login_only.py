#!/usr/bin/env python3
"""
Simplified test that only tests Chrome startup and login.
"""

import os
import sys
import time
import json
import logging
import traceback

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules to test
from src import auto_login

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_login_only')

def test_login_only():
    """Test Chrome startup and auto-login only."""
    print("\n=== Running Login-Only Test ===\n")
    chrome_instance = None
    
    try:
        # Use real credentials
        username = "stonkz92224@gmail.com"
        password = "24$tonkZ24"
        
        logger.info(f"Starting Chrome with user: {username}")
        
        # Start Chrome with debugging
        test_port = 9222
        process = auto_login.start_chrome_with_debugging(test_port)
        
        if not process:
            logger.error("Failed to start Chrome")
            return False
        
        logger.info("Chrome started successfully")
        
        # Wait for Chrome to initialize
        time.sleep(5)
        
        # Connect to Chrome
        logger.info("Connecting to Chrome...")
        browser, tab = auto_login.connect_to_chrome(test_port)
        
        if not tab:
            logger.error("Failed to connect to Chrome tab")
            return False
        
        logger.info("Connected to Chrome tab")
        
        # Create a Chrome instance object
        chrome_instance = auto_login.ChromeInstance(test_port, username, password)
        chrome_instance.browser = browser
        chrome_instance.tab = tab
        chrome_instance.process = process
        
        # Save screenshot of initial state
        logger.info("Taking screenshot of initial state...")
        screenshot_js = """
        (function() {
            try {
                const canvas = document.createElement('canvas');
                const context = canvas.getContext('2d');
                const img = new Image();
                
                // Convert current page to image (using html2canvas would be better but this is simple)
                const width = document.documentElement.clientWidth;
                const height = document.documentElement.clientHeight;
                canvas.width = width;
                canvas.height = height;
                
                context.fillStyle = '#FFFFFF';
                context.fillRect(0, 0, width, height);
                context.font = '10px Arial';
                context.fillStyle = '#000000';
                context.fillText('Screenshot of current page state', 10, 20);
                
                return "Screenshot simulation - actual screenshot would be here";
            } catch (e) {
                return "Error taking screenshot: " + e.toString();
            }
        })();
        """
        screenshot_result = tab.Runtime.evaluate(expression=screenshot_js)
        logger.info(f"Screenshot result: {screenshot_result.get('result', {}).get('value', 'unknown')}")
        
        # Disable alerts
        logger.info("Disabling alerts...")
        auto_login.disable_alerts(tab)
        
        # Check initial page status
        check_js = """
        (function() {
            // Check if we're on the login page
            const emailInput = document.getElementById("name-input");
            const passwordInput = document.getElementById("password-input");
            const loginButton = document.querySelector("button.MuiButton-containedPrimary");
            
            if (emailInput && passwordInput && loginButton) {
                return "login_page";
            }
            
            // Check if we're on the account selection page
            const accessButtons = Array.from(document.querySelectorAll("button.tm"))
                .filter(btn => 
                    btn.textContent.trim() === "Access Simulation" || 
                    btn.textContent.trim() === "Launch"
                );
                
            if (accessButtons.length > 0) {
                return "account_selection";
            }
            
            // Check if we're logged in by looking for key elements
            const isLoggedIn = document.querySelector(".bar--heading") || 
                            document.querySelector(".app-bar--account-menu-button") ||
                            document.querySelector(".dashboard--container") ||
                            document.querySelector(".pane.account-selector");
                            
            return isLoggedIn ? "logged_in" : "unknown";
        })();
        """
        
        result = tab.Runtime.evaluate(expression=check_js)
        page_status = result.get("result", {}).get("value", "unknown")
        logger.info(f"Initial page status: {page_status}")
        
        # Inject and execute login script
        logger.info("Injecting login script...")
        login_result = auto_login.inject_login_script(tab, username, password)
        logger.info(f"Login script injection result: {login_result}")
        
        # Enhanced login monitoring
        logger.info("Monitoring login process...")
        max_wait = 60
        for i in range(max_wait):
            # Check if we're logged in
            check_js = """
            (function() {
                try {
                    // Check various login indicators
                    const isLoggedIn = !!(
                        document.querySelector(".bar--heading") || 
                        document.querySelector(".app-bar--account-menu-button") ||
                        document.querySelector(".dashboard--container") ||
                        document.querySelector(".pane.account-selector")
                    );
                    
                    // Check what page we're on
                    let current_page = "unknown";
                    
                    if (document.getElementById("name-input") && 
                        document.getElementById("password-input") && 
                        document.querySelector("button.MuiButton-containedPrimary")) {
                        current_page = "login_page";
                    } else if (Array.from(document.querySelectorAll("button.tm"))
                        .filter(btn => 
                            btn.textContent.trim() === "Access Simulation" || 
                            btn.textContent.trim() === "Launch"
                        ).length > 0) {
                        current_page = "account_selection";
                    } else if (isLoggedIn) {
                        current_page = "logged_in";
                    }
                    
                    return {
                        isLoggedIn: isLoggedIn,
                        current_page: current_page,
                        url: document.location.href,
                        title: document.title
                    };
                } catch (e) {
                    return { error: e.toString() };
                }
            })();
            """
            result = tab.Runtime.evaluate(expression=check_js)
            status = json.loads(result.get("result", {}).get("value", "{}"))
            
            logger.info(f"Status at {i}s: {status}")
            
            if status.get("isLoggedIn"):
                logger.info(f"✅ Successfully logged in after {i} seconds")
                
                # Take screenshot of logged-in state
                logger.info("Taking screenshot of logged-in state...")
                screenshot_result = tab.Runtime.evaluate(expression=screenshot_js)
                
                # Keep session open for a while
                logger.info("Test passed! Keeping browser open for 30 seconds...")
                time.sleep(30)
                
                return True
            
            # Check if on account selection page
            if status.get("current_page") == "account_selection":
                logger.info("Detected account selection page, clicking Access Simulation...")
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
                tab.Runtime.evaluate(expression=account_selection_js)
            
            # If still on login page after a few seconds, try re-entering credentials
            if status.get("current_page") == "login_page" and i > 10 and i % 10 == 0:
                logger.info("Still on login page, re-entering credentials...")
                auto_login.inject_login_script(tab, username, password)
            
            time.sleep(1)
        
        logger.error("❌ Failed to login after waiting 60 seconds")
        return False
    
    except Exception as e:
        logger.error(f"❌ Error during test: {e}")
        traceback.print_exc()
        return False
    
    finally:
        if chrome_instance and chrome_instance.process:
            try:
                logger.info("Terminating Chrome...")
                chrome_instance.process.terminate()
            except:
                logger.error("Failed to terminate Chrome")

if __name__ == "__main__":
    success = test_login_only()
    if success:
        print("\n✅ Login test passed!")
        sys.exit(0)
    else:
        print("\n❌ Login test failed.")
        sys.exit(1)