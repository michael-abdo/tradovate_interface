#!/usr/bin/env python3
"""Test DOM selectors in Tradovate browser instance"""

from src.app import TradovateConnection
import json

def test_dom_selectors():
    # Connect to first available instance
    connection = TradovateConnection(port=9222, account_name='Selector Test')

    if not connection.tab:
        print('❌ No connection available')
        return False

    print('🔍 Testing DOM selectors in Tradovate UI...')

    # Test script for browser console
    test_script = """
console.log('🧪 ========== DOM SELECTOR TEST ==========');

// Define all selectors to test
const selectors = [
    // Container selectors
    { name: 'Trading Ticket Container', selector: '.trading-ticket', shouldExist: true },
    
    // Input fields
    { name: 'Symbol Input', selector: '.search-box--input', shouldExist: true },
    { name: 'Quantity Input', selector: '.select-input.combobox input', shouldExist: true },
    { name: 'Price Input', selector: '.numeric-input.feedback-wrapper input', shouldExist: false }, // Only for limit orders
    
    // Buttons and controls
    { name: 'Buy/Sell Labels', selector: '.radio-group.btn-group label', shouldExist: true },
    { name: 'Order Type Dropdown', selector: '.group.order-type .select-input div[tabindex]', shouldExist: true },
    { name: 'Submit Button', selector: '.btn-group .btn-primary', shouldExist: true },
    { name: 'Back Button', selector: '.icon.icon-back', shouldExist: false }, // Only when in order entry
    
    // Price controls
    { name: 'Price Controls', selector: '.numeric-input-value-controls', shouldExist: false },
    { name: 'Price Up Arrow', selector: '.numeric-input-increment', shouldExist: false },
    { name: 'Price Down Arrow', selector: '.numeric-input-decrement', shouldExist: false },
    
    // Dropdown menus
    { name: 'Dropdown Menu Items', selector: 'ul.dropdown-menu li', shouldExist: false }, // Only when dropdown open
    
    // Order history
    { name: 'Order History Rows', selector: '.order-history-content .public_fixedDataTable_bodyRow', shouldExist: false },
    { name: 'Order History Cells', selector: '.public_fixedDataTableCell_cellContent', shouldExist: false },
    
    // Checkboxes (custom UI elements)
    { name: 'TP Checkbox', selector: '#tpCheckbox', shouldExist: false }, // Custom element
    { name: 'SL Checkbox', selector: '#slCheckbox', shouldExist: false }  // Custom element
];

const results = [];

selectors.forEach(test => {
    try {
        const elements = document.querySelectorAll(test.selector);
        const count = elements.length;
        const visible = Array.from(elements).filter(el => el.offsetParent).length;
        
        const result = {
            name: test.name,
            selector: test.selector,
            found: count,
            visible: visible,
            shouldExist: test.shouldExist,
            status: count > 0 ? 'FOUND' : 'NOT_FOUND',
            elements: Array.from(elements).slice(0, 3).map(el => ({
                tagName: el.tagName,
                className: el.className,
                id: el.id,
                textContent: el.textContent ? el.textContent.slice(0, 50) : '',
                offsetParent: !!el.offsetParent
            }))
        };
        
        results.push(result);
        
        const statusIcon = count > 0 ? '✅' : (test.shouldExist ? '❌' : '⚪');
        console.log(`${statusIcon} ${test.name}: ${count} found, ${visible} visible`);
        if (count > 0 && elements[0]) {
            console.log(`   First element: <${elements[0].tagName.toLowerCase()}${elements[0].className ? ' class="' + elements[0].className + '"' : ''}${elements[0].id ? ' id="' + elements[0].id + '"' : ''}>`);
        }
        
    } catch (error) {
        console.error(`❌ Error testing ${test.name}: ${error.message}`);
        results.push({
            name: test.name,
            selector: test.selector,
            error: error.message,
            status: 'ERROR'
        });
    }
});

console.log('\\n📊 Summary:');
const found = results.filter(r => r.status === 'FOUND').length;
const notFound = results.filter(r => r.status === 'NOT_FOUND').length;
const errors = results.filter(r => r.status === 'ERROR').length;

console.log(`Found: ${found}, Not Found: ${notFound}, Errors: ${errors}`);

// Return results for Python processing
results;
"""

    try:
        # Execute the test script
        result = connection.tab.Runtime.evaluate(expression=test_script, awaitPromise=False, timeout=10000)
        
        if 'result' in result and 'value' in result['result']:
            test_results = result['result']['value']
            print('\n📋 Detailed Results:')
            
            for test_result in test_results:
                name = test_result.get('name', 'Unknown')
                status = test_result.get('status', 'UNKNOWN')
                found = test_result.get('found', 0)
                visible = test_result.get('visible', 0)
                selector = test_result.get('selector', '')
                
                if status == 'FOUND':
                    print(f'✅ {name}: {found} found, {visible} visible')
                    print(f'   Selector: {selector}')
                elif status == 'NOT_FOUND':
                    print(f'❌ {name}: Not found')
                    print(f'   Selector: {selector}')
                else:
                    error = test_result.get('error', 'Unknown error')
                    print(f'🔥 {name}: Error - {error}')
                    print(f'   Selector: {selector}')
                    
            # Summary
            found_count = len([r for r in test_results if r.get('status') == 'FOUND'])
            not_found_count = len([r for r in test_results if r.get('status') == 'NOT_FOUND'])
            error_count = len([r for r in test_results if r.get('status') == 'ERROR'])
            
            print(f'\n📊 Final Summary: {found_count} found, {not_found_count} not found, {error_count} errors')
            
            # Check critical selectors
            critical_selectors = ['Trading Ticket Container', 'Buy/Sell Labels', 'Quantity Input', 'Submit Button']
            critical_found = [r for r in test_results if r.get('name') in critical_selectors and r.get('status') == 'FOUND']
            
            print(f'\n🔍 Critical Selectors Status: {len(critical_found)}/{len(critical_selectors)} found')
            
            if len(critical_found) < len(critical_selectors):
                print('⚠️  Some critical selectors are missing - this may explain order placement failures')
            else:
                print('✅ All critical selectors found - issue may be in interaction logic')
                
            return test_results
            
        else:
            print('❌ No results returned from browser test')
            print(f'Raw result: {result}')
            return None
            
    except Exception as e:
        print(f'❌ Error executing selector test: {str(e)}')
        return None

if __name__ == "__main__":
    test_dom_selectors()