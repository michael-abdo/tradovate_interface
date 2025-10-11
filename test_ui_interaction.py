#!/usr/bin/env python3

import sys
import time
import json
from src.app import TradovateController

def test_ui_interaction():
    """Test if the autoTrade function can interact with the UI"""
    controller = TradovateController()
    
    if len(controller.connections) == 0:
        print("No Tradovate connections found.")
        return False
    
    conn = controller.connections[0]
    if not conn.tab:
        print("No tab available")
        return False
    
    print(f"Testing UI interaction on {conn.account_name}...")
    
    # First let's check if we can find any trading UI elements
    check_ui_js = """
    (function() {
        console.log('🔍 CHECKING TRADING UI ELEMENTS...');
        
        // Look for common trading UI elements
        var buyButtons_check = document.querySelectorAll('[data-qa*="buy"], .btn-buy, button:contains("Buy")');
        var sellButtons_check = document.querySelectorAll('[data-qa*="sell"], .btn-sell, button:contains("Sell")');
        var quantityInputs_check = document.querySelectorAll('input[data-qa*="quantity"], input[placeholder*="quantity"], input[name*="quantity"]');
        var priceInputs_check = document.querySelectorAll('input[data-qa*="price"], input[placeholder*="price"], input[name*="price"]');
        var orderButtons_check = document.querySelectorAll('.btn-primary, .btn-success, button[type="submit"]');
        
        console.log('🔍 Found ' + buyButtons_check.length + ' buy buttons');
        console.log('🔍 Found ' + sellButtons_check.length + ' sell buttons');
        console.log('🔍 Found ' + quantityInputs_check.length + ' quantity inputs');
        console.log('🔍 Found ' + priceInputs_check.length + ' price inputs');
        console.log('🔍 Found ' + orderButtons_check.length + ' order buttons');
        
        // Check for Tradovate-specific selectors that autoTrade uses
        var symbolInput_check = document.querySelector('.trading-ticket .search-box--input');
        var qtyInput_check = document.querySelector('.group.quantity input');
        var numericInputs_check = document.querySelectorAll('.numeric-input.feedback-wrapper input');
        var orderTypeSelectors_check = document.querySelectorAll('.group.order-type .select-input div[tabindex]');
        
        console.log('🔍 Symbol input found: ' + !!symbolInput_check);
        console.log('🔍 Quantity input found: ' + !!qtyInput_check);
        console.log('🔍 Numeric inputs found: ' + numericInputs_check.length);
        console.log('🔍 Order type selectors found: ' + orderTypeSelectors_check.length);
        
        if (symbolInput_check) {
            console.log('🔍 Current symbol: ' + symbolInput_check.value);
        }
        if (qtyInput_check) {
            console.log('🔍 Current quantity: ' + qtyInput_check.value);
        }
        
        // Check if we're on the right page
        var currentUrl_check = window.location.href;
        console.log('🔍 Current URL: ' + currentUrl_check);
        
        return JSON.stringify({
            buyButtons: buyButtons_check.length,
            sellButtons: sellButtons_check.length,
            quantityInputs: quantityInputs_check.length,
            priceInputs: priceInputs_check.length,
            symbolInputExists: !!symbolInput_check,
            qtyInputExists: !!qtyInput_check,
            currentUrl: currentUrl_check,
            isTradovate: currentUrl_check.includes('tradovate')
        });
    })();
    """
    
    print("Checking UI elements...")
    ui_result = conn.tab.Runtime.evaluate(expression=check_ui_js)
    print(f"UI check result: {ui_result}")
    
    if 'result' in ui_result and 'value' in ui_result['result']:
        ui_data = json.loads(ui_result['result']['value'])
        print(f"UI Data: {ui_data}")
        
        if not ui_data.get('isTradovate', False):
            print("❌ Not on a Tradovate page!")
            return False
        
        if ui_data.get('symbolInputExists', False):
            print("✅ Found symbol input - attempting simple autoTrade call")
            
            # Test a simple autoTrade call
            simple_trade_js = """
            console.log('🧪 TESTING SIMPLE AUTOTRADE CALL...');
            try {
                // Test with scale disabled explicitly
                const result = autoTrade('NQ', 1, 'Buy', 0, 0, 0.25, null, true);
                console.log('🧪 autoTrade result:', result);
                'autotrade_test_completed';
            } catch (error) {
                console.error('🧪 autoTrade error:', error);
                'autotrade_test_failed: ' + error.toString();
            }
            """
            
            trade_result = conn.tab.Runtime.evaluate(expression=simple_trade_js)
            print(f"Simple trade test result: {trade_result}")
            
            # Wait a moment and check for any changes
            time.sleep(3)
            
            # Check if anything happened
            post_trade_check = """
            console.log('🔍 POST-TRADE CHECK...');
            
            const orderHistory = document.querySelectorAll('[data-qa*="order"], .order-row, .trade-row');
            const positions = document.querySelectorAll('[data-qa*="position"], .position-row');
            
            console.log(`🔍 Order history elements: ${orderHistory.length}`);
            console.log(`🔍 Position elements: ${positions.length}`);
            
            // Check recent console messages or any visible feedback
            JSON.stringify({
                orderHistoryCount: orderHistory.length,
                positionCount: positions.length,
                timestamp: new Date().toISOString()
            });
            """
            
            check_result = conn.tab.Runtime.evaluate(expression=post_trade_check)
            print(f"Post-trade check: {check_result}")
            
        else:
            print("❌ Symbol input not found - UI might not be loaded")
            return False
    
    return True

if __name__ == "__main__":
    test_ui_interaction()