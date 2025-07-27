#!/usr/bin/env python3
import pychrome
import time
import json
import os
import sys

# Add the project root to the path so we can import from src
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Optional Chrome Communication Framework integration
try:
    from utils.chrome_communication import safe_evaluate, OperationType, ChromeCommunicationManager
    FRAMEWORK_AVAILABLE = True
except ImportError:
    FRAMEWORK_AVAILABLE = False

# Unified Chrome Configuration
try:
    from utils.check_chrome import get_chrome_ports, validate_chrome_port, PROTECTED_PORT
    CHROME_CONFIG_AVAILABLE = True
except ImportError:
    CHROME_CONFIG_AVAILABLE = False
    PROTECTED_PORT = 9222

if FRAMEWORK_AVAILABLE:
    print("✅ Chrome Communication Framework loaded - enhanced logging enabled")
    
    # Create a manager instance for this helper
    chrome_manager = ChromeCommunicationManager()
    
    def execute_safe_js(tab, js_code, description="Login helper operation", operation_type=OperationType.NON_CRITICAL):
        """Execute JavaScript with framework safety features if available"""
        try:
            result = safe_evaluate(tab, js_code, operation_type, description)
            if result.success:
                return {"result": {"value": result.value}}
            else:
                print(f"⚠️  JS execution failed: {result.error}")
                # Return None to maintain exact API compatibility when execution fails
                raise Exception(f"Safe execution failed: {result.error}")
        except Exception as e:
            print(f"❌ Framework execution error: {e}")
            # Fallback to direct execution
            try:
                return tab.Runtime.evaluate(expression=js_code)
            except Exception as fallback_error:
                # If both framework AND fallback fail, return None to match original behavior
                print(f"Error executing script: {fallback_error}")
                return None
    
except ImportError:
    FRAMEWORK_AVAILABLE = False
    print("ℹ️  Chrome Communication Framework not available - using standard execution")
    
    def execute_safe_js(tab, js_code, description="Login helper operation", operation_type=None):
        """Fallback to standard Runtime.evaluate when framework unavailable"""
        try:
            return tab.Runtime.evaluate(expression=js_code)
        except Exception as e:
            # Match original error handling behavior exactly
            print(f"Error executing script: {e}")
            return None

# First try importing with src. prefix
try:
    from src.auto_login import inject_login_script, disable_alerts
except ImportError:
    # Fall back to direct import (when run from within src directory)
    try:
        from auto_login import inject_login_script, disable_alerts
    except ImportError as e:
        print(f"Failed to import from auto_login: {e}")
        print("Make sure you're running this script from the project root directory")
        sys.exit(1)

def login_to_existing_chrome(port=None, username=None, password=None, tradovate_url="https://trader.tradovate.com"):
    """Login to Tradovate using existing Chrome with unified port configuration"""
    # Use unified Chrome port configuration
    if port is None:
        if CHROME_CONFIG_AVAILABLE:
            port = PROTECTED_PORT  # Default to protected port for existing Chrome
        else:
            port = 9222  # Fallback
    
    # Validate port if configuration is available
    if CHROME_CONFIG_AVAILABLE and port != PROTECTED_PORT:
        if not validate_chrome_port(port):
            print(f"WARNING: Using potentially unsafe port {port}")
    
    print(f"Connecting to Chrome on port {port}")
    """
    Login to Tradovate on an existing Chrome instance running with remote debugging.
    
    Args:
        port: The debugging port Chrome is running on
        username: Username for login (if None, will load from credentials.json)
        password: Password for login (if None, will load from credentials.json)
        tradovate_url: URL to check for (defaults to https://trader.tradovate.com)
        
    Returns:
        tuple: (success, tab_handle, browser) - Boolean success status, tab handle, and browser connection if successful
    """
    # If credentials not provided, use unified credential loading
    if not (username and password):
        try:
            from src.utils.chrome_communication import get_unified_single_credential
            username, password = get_unified_single_credential(0)
            if username and password:
                print(f"Using unified credentials for user: {username}")
            else:
                print("No credentials available from unified authentication manager")
                return False, None, None
        except ImportError:
            print("Unified authentication not available, credentials required")
            return False, None, None
        except Exception as e:
            print(f"Error loading unified credentials: {e}")
            return False, None, None
    
    # Connect to Chrome - DRY refactored to use standardized connection
    try:
        # First try to use the connect_to_chrome function from auto_login
        try:
            from src.auto_login import connect_to_chrome
            print(f"Using standardized connect_to_chrome for port {port}")
            browser, target_tab = connect_to_chrome(port)
            
            if target_tab:
                print("Successfully connected via connect_to_chrome")
                # Skip to after the connection logic
                
        except ImportError:
            print("connect_to_chrome not available, using direct connection")
            raise  # Fall through to original implementation
            
    except:
        # Fallback to original implementation
        print(f"Connecting to Chrome on port {port}...")
        browser = pychrome.Browser(url=f"http://localhost:{port}")
        tabs = browser.list_tab()
        
        print(f"Found {len(tabs)} tabs")
        
        # Find or create Tradovate tab
        target_tab = None
        for tab in tabs:
            try:
                tab.start()
                tab.Page.enable()
                result = execute_safe_js(tab, "document.location.href", "Tab URL detection for Tradovate identification")
                url = result.value if result.success else ""
                print(f"Tab URL: {url}")
                
                if "tradovate" in url.lower():
                    target_tab = tab
                    print("Found Tradovate tab")
                    break
                else:
                    tab.stop()
            except Exception as e:
                print(f"Error checking tab: {e}")
                try:
                    tab.stop()
                except:
                    pass
        
        if not target_tab:
            print("No Tradovate tab found. Creating a new tab...")
            try:
                target_tab = browser.new_tab(url=tradovate_url)
                target_tab.start()
                target_tab.Page.enable()
                print("New tab created and navigated to Tradovate")
                # Wait for page to load
                time.sleep(3)
            except Exception as e:
                print(f"Error creating new tab: {e}")
                return False, None, None
        
        # Inject login script and disable alerts
        print(f"Injecting login script for {username}...")
        inject_login_script(target_tab, username, password)
        disable_alerts(target_tab)
        
        # Add a visual indicator that we're using the helper
        visual_indicator = """
        setTimeout(() => {
            const helperDiv = document.createElement('div');
            helperDiv.id = 'login-helper-indicator';
            helperDiv.style.position = 'fixed';
            helperDiv.style.bottom = '10px';
            helperDiv.style.right = '10px';
            helperDiv.style.background = 'green';
            helperDiv.style.color = 'white';
            helperDiv.style.padding = '5px 10px';
            helperDiv.style.borderRadius = '5px';
            helperDiv.style.zIndex = '9999';
            helperDiv.style.opacity = '0.7';
            helperDiv.innerHTML = 'Login Helper Active';
            document.body.appendChild(helperDiv);
        }, 2000);
        """
        execute_safe_js(target_tab, visual_indicator, "Login helper visual indicator injection")
        
        print("Login script injected successfully")
        return True, target_tab, browser
    
    except Exception as e:
        print(f"Error connecting to Chrome or logging in: {e}")
        return False, None, None

def wait_for_element(tab, selector, timeout=10, visible=True):
    """
    Wait for an element to appear in the DOM and optionally be visible
    
    Args:
        tab: The tab handle
        selector: CSS selector for the element
        timeout: Maximum time to wait in seconds
        visible: Whether to also check if the element is visible
        
    Returns:
        bool: True if element was found (and visible if required), False otherwise
    """
    print(f"Waiting for element: {selector}")
    check_script = f"""
    function checkElement() {{
        const element = document.querySelector('{selector}');
        if (!element) return false;
        
        if ({str(visible).lower()}) {{
            const rect = element.getBoundingClientRect();
            const style = window.getComputedStyle(element);
            return rect.width > 0 && 
                   rect.height > 0 && 
                   style.display !== 'none' && 
                   style.visibility !== 'hidden' &&
                   style.opacity !== '0';
        }}
        return true;
    }}
    checkElement();
    """
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            result = execute_safe_js(tab, check_script, f"Element existence check for selector: {selector}")
            if result.value if result.success else False:
                print(f"Element found: {selector}")
                return True
        except Exception as e:
            print(f"Error checking for element: {e}")
        
        time.sleep(0.5)
    
    print(f"Timed out waiting for element: {selector}")
    return False

def execute_js(tab, script):
    """Execute JavaScript in the tab and return the result"""
    try:
        result = execute_safe_js(tab, script, "Generic JavaScript execution via execute_js function")
        return result.get("result", {})
    except Exception as e:
        print(f"Error executing script: {e}")
        return None

def main():
    """Simple CLI to test the login helper"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Login to Tradovate via Chrome DevTools Protocol")
    parser.add_argument("--port", type=int, default=None, help="Chrome debugging port (default: protected port 9222)")
    parser.add_argument("--username", help="Tradovate username (optional, will use credentials.json if not provided)")
    parser.add_argument("--password", help="Tradovate password (optional)")
    args = parser.parse_args()
    
    success, tab, browser = login_to_existing_chrome(
        port=args.port,
        username=args.username,
        password=args.password
    )
    
    if success:
        print("Successfully logged in")
        
        # Wait for either the login button or dashboard to appear
        if wait_for_element(tab, ".desktop-dashboard", timeout=15) or wait_for_element(tab, ".login-button", timeout=5):
            print("Login page or dashboard loaded successfully")
        
        # Keep browser open
        print("Press Ctrl+C to exit")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Exiting...")
    else:
        print("Login failed")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())