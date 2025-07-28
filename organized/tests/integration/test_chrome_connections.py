#!/usr/bin/env python3
"""Test Chrome connections to debug dashboard issues"""

import pychrome
import json
import time

def test_chrome_connections():
    """Test all Chrome debug ports"""
    print(f"\n{'='*60}")
    print(f"Chrome Connection Test - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Test ports 9222-9225 (main Chrome and 3 accounts)
    ports = [9222, 9223, 9224, 9225]
    
    for port in ports:
        print(f"\n[Port {port}] Testing connection...")
        try:
            browser = pychrome.Browser(url=f"http://localhost:{port}")
            tabs = browser.list_tab()
            
            print(f"[Port {port}] ✅ Connected! Found {len(tabs)} tabs")
            
            # Check each tab
            for i, tab_info in enumerate(tabs):
                try:
                    print(f"[Port {port}] Tab {i}: {tab_info.title}")
                    print(f"[Port {port}]   URL: {tab_info.url}")
                    
                    # Try to connect to the tab
                    if 'tradovate' in tab_info.url.lower():
                        print(f"[Port {port}]   ⭐ This is a Tradovate tab!")
                        
                        try:
                            tab = tab_info
                            tab.start()
                            tab.Page.enable()
                            
                            # Test JavaScript execution
                            result = tab.Runtime.evaluate(expression="document.readyState")
                            ready_state = result.get("result", {}).get("value", "unknown")
                            print(f"[Port {port}]   Document ready state: {ready_state}")
                            
                            # Test if we can find tables
                            table_test = tab.Runtime.evaluate(expression="""
                                (() => {
                                    const selectors = [
                                        '.public_fixedDataTable_main',
                                        '.fixedDataTable',
                                        '[role="table"]',
                                        '.data-table'
                                    ];
                                    for (const selector of selectors) {
                                        const elements = document.querySelectorAll(selector);
                                        if (elements.length > 0) {
                                            return `Found ${elements.length} elements with selector: ${selector}`;
                                        }
                                    }
                                    return 'No table elements found';
                                })()
                            """)
                            table_result = table_test.get("result", {}).get("value", "error")
                            print(f"[Port {port}]   Table test: {table_result}")
                            
                            tab.stop()
                        except Exception as e:
                            print(f"[Port {port}]   ❌ Error testing tab: {str(e)}")
                except Exception as e:
                    print(f"[Port {port}] Tab {i}: Error accessing tab info - {str(e)}")
                    continue
                        
        except Exception as e:
            print(f"[Port {port}] ❌ Connection failed: {str(e)}")
    
    print(f"\n{'='*60}")
    print("Test complete!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    test_chrome_connections()