#!/usr/bin/env python3
import pychrome
import json

def test_chrome_connection(port):
    """Test Chrome connection and check for getAllAccountTableData function"""
    print(f"\n=== Testing Chrome on port {port} ===")
    
    try:
        browser = pychrome.Browser(url=f"http://localhost:{port}")
        tabs = browser.list_tab()
        
        print(f"Found {len(tabs)} tabs")
        
        # Find Tradovate tab
        for tab in tabs:
            try:
                tab.start()
                tab.Page.enable()
                
                # Check URL
                url_result = tab.Runtime.evaluate(expression="document.location.href")
                url = url_result.get('result', {}).get('value', '')
                
                if 'tradovate' in url.lower():
                    print(f"✅ Found Tradovate tab: {url}")
                    
                    # Check if logged in
                    login_check = tab.Runtime.evaluate(expression="""
                        document.querySelector('div[data-testid="account-selector"]') !== null ||
                        document.querySelector('.account-selector') !== null
                    """)
                    is_logged_in = login_check.get('result', {}).get('value', False)
                    print(f"Logged in: {'✅ Yes' if is_logged_in else '❌ No'}")
                    
                    # Check if getAllAccountTableData exists
                    func_check = tab.Runtime.evaluate(expression="typeof window.getAllAccountTableData")
                    func_type = func_check.get('result', {}).get('value', 'undefined')
                    print(f"getAllAccountTableData type: {func_type}")
                    
                    if func_type == 'function':
                        # Try to execute it
                        print("Executing getAllAccountTableData()...")
                        result = tab.Runtime.evaluate(expression="window.getAllAccountTableData()")
                        data = result.get('result', {}).get('value')
                        
                        if data:
                            print(f"✅ Got account data:")
                            print(json.dumps(data, indent=2))
                        else:
                            print("❌ Function returned null/undefined")
                    else:
                        print("❌ getAllAccountTableData function not found")
                        
                        # Check Tampermonkey
                        tm_check = tab.Runtime.evaluate(expression="typeof window.TampermonkeyFunctions")
                        tm_type = tm_check.get('result', {}).get('value', 'undefined')
                        print(f"TampermonkeyFunctions type: {tm_type}")
                        
                        if tm_type == 'object':
                            # List available functions
                            funcs_result = tab.Runtime.evaluate(expression="Object.keys(window.TampermonkeyFunctions || {})")
                            funcs = funcs_result.get('result', {}).get('value', [])
                            print(f"Available Tampermonkey functions: {funcs}")
                    
                    tab.stop()
                    break
                else:
                    tab.stop()
                    
            except Exception as e:
                print(f"Error checking tab: {e}")
                try:
                    tab.stop()
                except:
                    pass
                    
    except Exception as e:
        print(f"Error connecting to Chrome on port {port}: {e}")

# Test both Chrome instances
test_chrome_connection(9223)
test_chrome_connection(9224)