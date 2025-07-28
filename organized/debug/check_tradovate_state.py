#!/usr/bin/env python3
"""Check Tradovate state using Chrome extension messaging"""

import json
import subprocess
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_tampermonkey_scripts():
    """Check which Tampermonkey scripts are installed"""
    logger.info("Checking Tampermonkey scripts...")
    
    # Check for getAllAccountTableData script
    script_path = "/Users/Mike/trading/scripts/tampermonkey/getAllAccountTableData.user.js"
    try:
        with open(script_path, 'r') as f:
            content = f.read()
            if 'getAllAccountTableData' in content:
                logger.info("✅ getAllAccountTableData.user.js exists and contains the function")
            else:
                logger.error("❌ getAllAccountTableData.user.js exists but doesn't contain the function")
    except FileNotFoundError:
        logger.error(f"❌ Script not found: {script_path}")

def check_chrome_extension():
    """Check if Chrome extension is responding"""
    logger.info("\nChecking Chrome extension status...")
    
    # Try to communicate with the extension via native messaging
    try:
        # This would normally use the extension's native messaging host
        logger.info("Note: Direct Chrome extension communication requires native messaging host setup")
    except Exception as e:
        logger.error(f"Error checking extension: {e}")

def check_dashboard_status():
    """Check dashboard server status"""
    logger.info("\nChecking dashboard status...")
    
    try:
        import requests
        response = requests.get("http://localhost:6001/", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Dashboard is running on http://localhost:6001/")
            
            # Check for account data endpoint
            try:
                api_response = requests.get("http://localhost:6001/api/accounts", timeout=5)
                if api_response.status_code == 200:
                    data = api_response.json()
                    logger.info(f"✅ API endpoint working, accounts data: {len(data.get('accounts', []))} accounts")
                else:
                    logger.error(f"❌ API endpoint returned status: {api_response.status_code}")
            except Exception as e:
                logger.error(f"❌ API endpoint error: {e}")
        else:
            logger.error(f"❌ Dashboard returned status: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Dashboard not accessible: {e}")

def suggest_manual_checks():
    """Suggest manual checks to perform"""
    logger.info("\n" + "="*60)
    logger.info("MANUAL CHECKS TO PERFORM:")
    logger.info("="*60)
    
    checks = [
        "1. Open Chrome DevTools on the Tradovate tab (port 9223 or 9224)",
        "2. Go to Console tab",
        "3. Type: getAllAccountTableData()",
        "4. Check if the function exists and returns data",
        "",
        "5. If function doesn't exist, check Tampermonkey:",
        "   - Click Tampermonkey extension icon",
        "   - Go to Dashboard",
        "   - Check if 'getAllAccountTableData' script is enabled",
        "",
        "6. Check for login status:",
        "   - Look for account name in top-right corner",
        "   - Check if positions/accounts tab is visible",
        "",
        "7. Check DOM for account tables:",
        "   - In Console, type: document.querySelectorAll('.public_fixedDataTable_main')",
        "   - Or: document.querySelectorAll('[role=\"table\"]')",
        "",
        "8. Check for JavaScript errors:",
        "   - Look for red error messages in Console",
        "   - Check Network tab for failed requests"
    ]
    
    for check in checks:
        logger.info(check)

def check_selector_presence():
    """Generate JavaScript to check selector presence"""
    logger.info("\n" + "="*60)
    logger.info("JAVASCRIPT TO RUN IN CONSOLE:")
    logger.info("="*60)
    
    js_code = """
// Check all possible selectors
const selectors = [
    '.public_fixedDataTable_main',
    '.module.positions.data-table',
    '.positions .data-table',
    '.positions',
    '[role="table"]',
    '.fixedDataTable',
    'table',
    '.data-table'
];

console.log('Checking selectors...');
selectors.forEach(selector => {
    const elements = document.querySelectorAll(selector);
    if (elements.length > 0) {
        console.log(`✅ Found ${elements.length} elements for: ${selector}`);
        console.log('   First element:', elements[0]);
    } else {
        console.log(`❌ No elements found for: ${selector}`);
    }
});

// Check if getAllAccountTableData exists
if (typeof getAllAccountTableData === 'function') {
    console.log('\\n✅ getAllAccountTableData function exists');
    console.log('Calling it now...');
    try {
        const result = getAllAccountTableData();
        console.log('Result:', result);
    } catch (e) {
        console.error('Error calling function:', e);
    }
} else {
    console.error('\\n❌ getAllAccountTableData function NOT found');
}

// Check login status
const userElements = document.querySelectorAll('[class*="user"], [class*="account"], [id*="user"]');
console.log(`\\nFound ${userElements.length} user-related elements`);
"""
    
    logger.info(js_code)
    
    # Save to file for easy copying
    with open("/Users/Mike/trading/debug_selectors.js", "w") as f:
        f.write(js_code)
    logger.info("\nSaved to: /Users/Mike/trading/debug_selectors.js")

if __name__ == "__main__":
    check_tampermonkey_scripts()
    check_dashboard_status()
    check_selector_presence()
    suggest_manual_checks()