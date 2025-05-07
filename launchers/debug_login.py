#!/usr/bin/env python3
"""
Debug script to test the auto-login functionality.
"""

import os
import sys
import time
import json
import traceback

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules to test
from src import auto_login

def debug_login():
    """Debug the auto-login functionality."""
    print("=== Running Auto-Login Debug ===")
    chrome_instance = None
    
    try:
        # Use actual credentials
        username = "stonkz92224@gmail.com"
        password = "24$tonkZ24"
        
        print(f"Starting Chrome with user: {username}")
        
        # Start Chrome with debugging
        test_port = 9222
        process = auto_login.start_chrome_with_debugging(test_port)
        
        if not process:
            print("❌ Failed to start Chrome")
            return False
        
        print("Chrome started successfully")
        
        # Wait longer for Chrome to initialize
        print("Waiting for Chrome to initialize (5 seconds)...")
        time.sleep(5)
        
        # Connect to Chrome
        print("Connecting to Chrome...")
        browser, tab = auto_login.connect_to_chrome(test_port)
        
        if not tab:
            print("❌ Failed to connect to Chrome tab")
            return False
        
        print("Connected to Chrome tab")
        
        # Create a Chrome instance object
        chrome_instance = auto_login.ChromeInstance(test_port, username, password)
        chrome_instance.browser = browser
        chrome_instance.tab = tab
        chrome_instance.process = process
        
        # Disable alerts
        print("Disabling alerts...")
        auto_login.disable_alerts(tab)
        
        # Get the current page URL
        result = tab.Runtime.evaluate(expression="document.location.href")
        current_url = result.get("result", {}).get("value", "unknown")
        print(f"Current page URL: {current_url}")
        
        # Check current page status
        print("Checking page status...")
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
        print(f"Current page status: {page_status}")
        
        # Inject and execute login script
        print("Injecting login script...")
        auto_login.inject_login_script(tab, username, password)
        
        # Wait and check login status
        print("Waiting for login to complete (60 seconds)...")
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
            result = tab.Runtime.evaluate(expression=check_js)
            is_logged_in = result.get("result", {}).get("value", False)
            
            if is_logged_in:
                print(f"✅ Successfully logged in after {i} seconds")
                
                # Stay logged in for a while so you can see it
                print("Keeping browser open for 60 seconds...")
                time.sleep(60)
                
                return True
            
            # Not logged in yet, check if we're on the login page
            login_page_js = """
            (function() {
                const emailInput = document.getElementById("name-input");
                const passwordInput = document.getElementById("password-input");
                const loginButton = document.querySelector("button.MuiButton-containedPrimary");
                
                return !!(emailInput && passwordInput && loginButton);
            })();
            """
            login_result = tab.Runtime.evaluate(expression=login_page_js)
            on_login_page = login_result.get("result", {}).get("value", False)
            
            if on_login_page and i > 5:
                print("Still on login page, trying to re-enter credentials...")
                auto_login.inject_login_script(tab, username, password)
            
            # Check for account selection page
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
            selection_result = tab.Runtime.evaluate(expression=account_selection_js)
            if selection_result.get("result", {}).get("value", False):
                print(f"Clicked account selection button at {i} seconds")
            
            # Debug HTML
            if i % 10 == 0:
                debug_js = """
                (function() {
                    return document.body.innerHTML;
                })();
                """
                debug_result = tab.Runtime.evaluate(expression=debug_js)
                html = debug_result.get("result", {}).get("value", "")
                print(f"\nHTML at {i} seconds (first 500 chars):")
                print(html[:500])
                print("...\n")
            
            time.sleep(1)
        
        print("❌ Failed to login after waiting 60 seconds")
        
        # Keep the browser open for examination
        print("Keeping browser open for debugging...")
        time.sleep(30)
        
        return False
    
    except Exception as e:
        print(f"❌ Error during debug login: {e}")
        traceback.print_exc()
        return False
    
    finally:
        if chrome_instance and chrome_instance.process:
            try:
                print("Terminating Chrome...")
                chrome_instance.process.terminate()
            except:
                print("Failed to terminate Chrome")

if __name__ == "__main__":
    debug_login()