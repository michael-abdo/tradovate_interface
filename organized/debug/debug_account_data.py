#!/usr/bin/env python3
"""Debug account data extraction from Tradovate interface"""

import json
import requests
import time
from typing import Dict, List, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_chrome_tabs(port: int) -> List[Dict[str, Any]]:
    """Get list of tabs from Chrome instance"""
    try:
        response = requests.get(f"http://localhost:{port}/json/list")
        return response.json()
    except Exception as e:
        logger.error(f"Failed to get tabs from port {port}: {e}")
        return []

def execute_javascript(port: int, tab_id: str, expression: str) -> Dict[str, Any]:
    """Execute JavaScript in a specific tab using Chrome DevTools Protocol"""
    import websocket
    import json
    
    ws_url = f"ws://localhost:{port}/devtools/page/{tab_id}"
    ws = websocket.create_connection(ws_url)
    
    try:
        # Send Runtime.enable command
        ws.send(json.dumps({
            "id": 1,
            "method": "Runtime.enable",
            "params": {}
        }))
        ws.recv()  # Receive acknowledgment
        
        # Execute the JavaScript expression
        ws.send(json.dumps({
            "id": 2,
            "method": "Runtime.evaluate",
            "params": {
                "expression": expression,
                "returnByValue": True
            }
        }))
        
        result = json.loads(ws.recv())
        return result
        
    finally:
        ws.close()

def check_account_data():
    """Check account data on both Chrome instances"""
    ports = [9223, 9224]
    
    for port in ports:
        logger.info(f"\n{'='*60}")
        logger.info(f"Checking Chrome on port {port}")
        logger.info(f"{'='*60}")
        
        tabs = get_chrome_tabs(port)
        
        # Find the main Tradovate tab
        main_tab = None
        for tab in tabs:
            if tab.get('type') == 'page' and 'trader.tradovate.com' in tab.get('url', ''):
                main_tab = tab
                break
        
        if not main_tab:
            logger.error(f"No Tradovate tab found on port {port}")
            continue
            
        tab_id = main_tab['id']
        logger.info(f"Found Tradovate tab: {main_tab['title']} (ID: {tab_id})")
        
        # Check if logged in
        login_check = execute_javascript(port, tab_id, """
            (() => {
                // Check for username in header or any login indicators
                const userElements = document.querySelectorAll('[class*="user"], [class*="account"], [id*="user"], [id*="account"]');
                const loginButton = document.querySelector('button[class*="login"], a[href*="login"]');
                return {
                    userElementsFound: userElements.length,
                    loginButtonVisible: loginButton ? loginButton.offsetParent !== null : false,
                    pageTitle: document.title,
                    url: window.location.href
                };
            })()
        """)
        
        logger.info(f"Login status: {json.dumps(login_check, indent=2)}")
        
        # Execute getAllAccountTableData function
        logger.info("\nExecuting getAllAccountTableData()...")
        account_data_result = execute_javascript(port, tab_id, """
            (() => {
                if (typeof getAllAccountTableData === 'function') {
                    try {
                        return getAllAccountTableData();
                    } catch (e) {
                        return { error: 'Function execution error: ' + e.message };
                    }
                } else {
                    return { error: 'getAllAccountTableData function not found' };
                }
            })()
        """)
        
        if 'result' in account_data_result and 'result' in account_data_result['result']:
            result_value = account_data_result['result']['result']['value']
            logger.info(f"Account data result: {json.dumps(result_value, indent=2)}")
        else:
            logger.error(f"Error getting account data: {account_data_result}")
        
        # Check for account table elements
        logger.info("\nChecking for account table elements...")
        dom_check = execute_javascript(port, tab_id, """
            (() => {
                const selectors = [
                    'table[class*="account"]',
                    'div[class*="account-table"]',
                    'div[class*="AccountTable"]',
                    '[data-testid*="account"]',
                    'table',
                    'div[class*="table"]'
                ];
                
                const results = {};
                for (const selector of selectors) {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {
                        results[selector] = {
                            count: elements.length,
                            firstElement: {
                                tagName: elements[0].tagName,
                                className: elements[0].className,
                                id: elements[0].id,
                                innerHTML: elements[0].innerHTML.substring(0, 200) + '...'
                            }
                        };
                    }
                }
                
                // Also check for any elements containing account-related text
                const textSearch = Array.from(document.querySelectorAll('*')).filter(el => {
                    const text = el.textContent || '';
                    return text.includes('Account') || text.includes('Balance') || text.includes('P&L');
                }).slice(0, 5).map(el => ({
                    tagName: el.tagName,
                    className: el.className,
                    text: el.textContent.substring(0, 100)
                }));
                
                return {
                    selectors: results,
                    textMatches: textSearch,
                    documentReady: document.readyState
                };
            })()
        """)
        
        if 'result' in dom_check and 'result' in dom_check['result']:
            dom_value = dom_check['result']['result']['value']
            logger.info(f"DOM check results: {json.dumps(dom_value, indent=2)}")
        
        # Check console errors
        logger.info("\nChecking for console errors...")
        console_check = execute_javascript(port, tab_id, """
            (() => {
                // This won't capture past errors, but we can check current state
                return {
                    hasJQuery: typeof $ !== 'undefined',
                    hasAngular: typeof angular !== 'undefined',
                    hasReact: typeof React !== 'undefined',
                    customGlobals: Object.keys(window).filter(key => 
                        !key.match(/^(webkit|moz|ms|o)[A-Z]/) && 
                        !['location', 'navigator', 'document', 'window', 'console', 'alert'].includes(key)
                    ).slice(0, 20)
                };
            })()
        """)
        
        if 'result' in console_check and 'result' in console_check['result']:
            console_value = console_check['result']['result']['value']
            logger.info(f"Page environment: {json.dumps(console_value, indent=2)}")

if __name__ == "__main__":
    check_account_data()