#!/usr/bin/env python3
"""Final test for account data extraction using proper pychrome approach"""

import pychrome
import json
import time

def test_account_data():
    """Test account data extraction the right way"""
    
    ports = [9223, 9224]
    
    for port in ports:
        print(f"\n{'='*60}")
        print(f"Testing Chrome on port {port}")
        print(f"{'='*60}")
        
        try:
            browser = pychrome.Browser(url=f"http://localhost:{port}")
            
            # Find Tradovate tab
            tradovate_tab = None
            for tab in browser.list_tab():
                try:
                    tab.start()
                    tab.Page.enable()
                    tab.Runtime.enable()
                    
                    # Get URL
                    result = tab.Runtime.evaluate(expression="document.location.href")
                    url = result.get("result", {}).get("value", "")
                    
                    if "tradovate" in url:
                        tradovate_tab = tab
                        print(f"✅ Found Tradovate tab: {url}")
                        break
                    else:
                        tab.stop()
                except Exception as e:
                    print(f"Error checking tab: {e}")
                    try:
                        tab.stop()
                    except:
                        pass
                        
            if not tradovate_tab:
                print(f"❌ No Tradovate tab found on port {port}")
                continue
                
            # Use the found tab
            tab = tradovate_tab
            
            # Check current page state
            state_result = tab.Runtime.evaluate(expression="""
                (() => {
                    const selectors = {
                        '.public_fixedDataTable_main': document.querySelectorAll('.public_fixedDataTable_main').length,
                        '[role="table"]': document.querySelectorAll('[role="table"]').length,
                        '[role="columnheader"]': document.querySelectorAll('[role="columnheader"]').length,
                        '[role="gridcell"]': document.querySelectorAll('[role="gridcell"]').length,
                        '.public_fixedDataTable_bodyRow': document.querySelectorAll('.public_fixedDataTable_bodyRow').length,
                        'table': document.querySelectorAll('table').length
                    };
                    
                    return {
                        title: document.title,
                        readyState: document.readyState,
                        selectors: selectors,
                        hasGetAllAccountTableData: typeof getAllAccountTableData !== 'undefined'
                    };
                })()
            """)
            
            state = state_result.get("result", {}).get("value", {})
            print(f"\nPage state: {json.dumps(state, indent=2)}")
            
            # Inject getAllAccountTableData if needed
            if not state.get('hasGetAllAccountTableData'):
                print("\nInjecting getAllAccountTableData function...")
                with open('/Users/Mike/trading/scripts/tampermonkey/getAllAccountTableData.user.js', 'r') as f:
                    script = f.read()
                    
                inject_result = tab.Runtime.evaluate(expression=script)
                if inject_result.get('error'):
                    print(f"❌ Injection error: {inject_result['error']}")
                else:
                    print("✅ Function injected")
                    
            # Wait a moment
            time.sleep(0.5)
            
            # Execute getAllAccountTableData
            print("\nExecuting getAllAccountTableData()...")
            data_result = tab.Runtime.evaluate(expression="getAllAccountTableData()")
            
            if 'error' in data_result:
                print(f"❌ Execution error: {data_result['error']}")
            elif 'result' in data_result and 'value' in data_result['result']:
                account_data = data_result['result']['value']
                try:
                    data = json.loads(account_data)
                    print(f"✅ Retrieved {len(data)} account records")
                    if data:
                        print("\nFirst record:")
                        print(json.dumps(data[0], indent=2))
                    else:
                        print("\n⚠️  No account data found - table might be empty")
                        
                        # Check what's visible on page
                        visibility_check = tab.Runtime.evaluate(expression="""
                            (() => {
                                // Check for login elements
                                const loginButton = document.querySelector('button[class*="login"], a[href*="login"]');
                                const userMenu = document.querySelector('[class*="user-menu"], [class*="account-menu"]');
                                
                                // Check for any text containing account info
                                const bodyText = document.body.innerText;
                                const hasAccountText = bodyText.includes('Account') || bodyText.includes('Balance');
                                
                                // Check visible elements
                                const visibleDivs = Array.from(document.querySelectorAll('div')).filter(el => {
                                    const rect = el.getBoundingClientRect();
                                    return rect.width > 0 && rect.height > 0;
                                }).length;
                                
                                return {
                                    hasLoginButton: loginButton !== null,
                                    hasUserMenu: userMenu !== null,
                                    hasAccountText: hasAccountText,
                                    visibleDivsCount: visibleDivs,
                                    pageTextSample: bodyText.substring(0, 300)
                                };
                            })()
                        """)
                        
                        visibility = visibility_check.get('result', {}).get('value', {})
                        print(f"\nPage visibility check: {json.dumps(visibility, indent=2)}")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parse error: {e}")
                    print(f"Raw data: {account_data[:500]}...")
            else:
                print("❌ No result from getAllAccountTableData()")
                
            # Don't stop the tab - keep it running
            # tab.stop()
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_account_data()