#!/usr/bin/env python3
import pychrome

for port in [9223, 9224]:
    print(f"\n=== Chrome on port {port} ===")
    browser = pychrome.Browser(url=f"http://localhost:{port}")
    tabs = browser.list_tab()
    
    for i, tab in enumerate(tabs):
        try:
            tab.start()
            tab.Page.enable()
            
            # Check URL
            url_result = tab.Runtime.evaluate(expression="document.location.href")
            url = url_result.get('result', {}).get('value', '')
            
            print(f"Tab {i}: {url}")
            
            if 'tradovate' in url.lower():
                print("  ✅ Tradovate tab")
                
                # Check domain
                domain_result = tab.Runtime.evaluate(expression="document.location.hostname")
                domain = domain_result.get('result', {}).get('value', '')
                print(f"  Domain: {domain}")
                
                # Check if function exists
                func_result = tab.Runtime.evaluate(expression="typeof window.getAllAccountTableData")
                func_type = func_result.get('result', {}).get('value', '')
                print(f"  getAllAccountTableData: {func_type}")
                
            tab.stop()
        except Exception as e:
            print(f"  Error: {e}")
            try:
                tab.stop()
            except:
                pass