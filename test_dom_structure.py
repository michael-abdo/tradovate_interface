#!/usr/bin/env python3
import pychrome
import json
import os
import sys
import time

# Load the debug script
debug_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tampermonkey/debug_dom.user.js')
with open(debug_script_path, 'r') as file:
    debug_script = file.read()

def analyze_tradovate_tab(port=9222):
    print(f"Connecting to Chrome on port {port}...")
    browser = pychrome.Browser(url=f"http://127.0.0.1:{port}")
    
    # List tabs and find Tradovate
    for tab in browser.list_tab():
        try:
            tab.start()
            result = tab.Runtime.evaluate(expression="document.location.href")
            url = result.get("result", {}).get("value", "")
            print(f"Found tab with URL: {url}")
            
            if "tradovate" in url:
                print(f"Found Tradovate tab at {url}")
                
                # Inject and run our analysis script
                print("Injecting DOM analysis script...")
                tab.Runtime.evaluate(expression=debug_script)
                
                print("Analyzing DOM structure...")
                result = tab.Runtime.evaluate(expression="analyzeTradovateDom()")
                
                if result and 'result' in result and 'value' in result['result']:
                    # Parse the result
                    dom_analysis = json.loads(result['result']['value'])
                    print("\nDOM ANALYSIS RESULTS:")
                    print(json.dumps(dom_analysis, indent=2))
                
                # Also test the actual data gathering function
                print("\nTesting getAllAccountTableData function...")
                # First check if we have the script
                account_data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                       'tampermonkey/getAllAccountTableData.user.js')
                
                if os.path.exists(account_data_path):
                    with open(account_data_path, 'r') as file:
                        get_account_data_js = file.read()
                        
                    # Inject it
                    tab.Runtime.evaluate(expression=get_account_data_js)
                    
                    # Run it
                    print("Running getAllAccountTableData()...")
                    result = tab.Runtime.evaluate(expression="getAllAccountTableData()")
                    
                    if result and 'result' in result and 'value' in result['result']:
                        try:
                            # Try to parse the JSON
                            data = json.loads(result['result']['value'])
                            print(f"Successfully parsed data with {len(data)} items")
                            print(json.dumps(data[:2], indent=2))  # Show first two items as sample
                        except json.JSONDecodeError as e:
                            print(f"Error parsing JSON: {e}")
                            value = result['result']['value']
                            print(f"Raw value: {value[:200]}...") # Show first 200 chars
                    else:
                        print("No valid result from getAllAccountTableData()")
                        print(f"Result: {result}")
                else:
                    print(f"Account data script not found at {account_data_path}")
                    
                tab.stop()
                return
            
            tab.stop()
        except Exception as e:
            print(f"Error processing tab: {e}")
            try:
                tab.stop()
            except:
                pass
    
    print("No Tradovate tab found")

if __name__ == "__main__":
    port = 9222  # Default port
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}, using default port 9222")
    
    analyze_tradovate_tab(port)