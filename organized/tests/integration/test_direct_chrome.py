#!/usr/bin/env python3
"""Test Chrome directly using tab IDs"""

import pychrome
import json
import time

def test_direct():
    """Test Chrome with known tab IDs"""
    
    # Known tab IDs from the JSON output
    tab_configs = [
        {"port": 9223, "tab_id": "88EA76FA9FC308774E1F84D94C5E0B80"},
        {"port": 9224, "tab_id": "2D1310B0BDFBD0F0E8C7BA16EF2B72E5"}
    ]
    
    for config in tab_configs:
        port = config["port"]
        tab_id = config["tab_id"]
        
        print(f"\n{'='*60}")
        print(f"Testing Chrome on port {port}, tab {tab_id}")
        print(f"{'='*60}")
        
        try:
            browser = pychrome.Browser(url=f"http://localhost:{port}")
            tab = browser.connect_tab(tab_id)
            tab.start()
            
            # Enable runtime
            tab.Runtime.enable()
            time.sleep(1)
            
            # Check current state
            result = tab.Runtime.evaluate(expression="""
                (() => {
                    // Check all possible table selectors
                    const selectors = {
                        '.public_fixedDataTable_main': document.querySelectorAll('.public_fixedDataTable_main').length,
                        '[role="table"]': document.querySelectorAll('[role="table"]').length,
                        '.module.positions': document.querySelectorAll('.module.positions').length,
                        '.data-table': document.querySelectorAll('.data-table').length,
                        'table': document.querySelectorAll('table').length,
                        '[role="columnheader"]': document.querySelectorAll('[role="columnheader"]').length,
                        '[role="gridcell"]': document.querySelectorAll('[role="gridcell"]').length
                    };
                    
                    // Check if getAllAccountTableData exists
                    const hasFunction = typeof getAllAccountTableData !== 'undefined';
                    
                    // Check login status
                    const loginElements = document.querySelectorAll('[class*="login"], button[class*="Login"]');
                    const userElements = document.querySelectorAll('[class*="user"], [class*="User"], [class*="account"]');
                    
                    return {
                        url: window.location.href,
                        title: document.title,
                        readyState: document.readyState,
                        selectors: selectors,
                        hasGetAllAccountTableData: hasFunction,
                        loginElementsCount: loginElements.length,
                        userElementsCount: userElements.length,
                        bodyText: document.body.innerText.substring(0, 200)
                    };
                })()
            """)
            
            if 'result' in result and 'value' in result['result']:
                state = result['result']['value']
                print(json.dumps(state, indent=2))
                
                # If function doesn't exist, inject it
                if not state.get('hasGetAllAccountTableData'):
                    print("\nInjecting getAllAccountTableData function...")
                    with open('/Users/Mike/trading/scripts/tampermonkey/getAllAccountTableData.user.js', 'r') as f:
                        script = f.read()
                    
                    tab.Runtime.evaluate(expression=script)
                    time.sleep(0.5)
                    
                    # Check if injection worked
                    check_result = tab.Runtime.evaluate(expression="typeof getAllAccountTableData !== 'undefined'")
                    if check_result.get('result', {}).get('value'):
                        print("✅ Function injected successfully")
                    else:
                        print("❌ Function injection failed")
                
                # Try to execute getAllAccountTableData
                print("\nExecuting getAllAccountTableData()...")
                data_result = tab.Runtime.evaluate(expression="getAllAccountTableData()")
                
                if 'result' in data_result and 'value' in data_result['result']:
                    account_data = data_result['result']['value']
                    try:
                        data = json.loads(account_data)
                        print(f"✅ Retrieved {len(data)} account records")
                        if data:
                            print("\nFirst record:")
                            print(json.dumps(data[0], indent=2))
                    except:
                        print(f"Raw result: {account_data[:500]}...")
                else:
                    print("❌ No result from getAllAccountTableData()")
                    if 'error' in data_result:
                        print(f"Error: {data_result['error']}")
                        
            tab.stop()
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_direct()