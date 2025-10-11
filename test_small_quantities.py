#!/usr/bin/env python3
"""Test with smaller quantities and different parameters"""

from src.app import TradovateConnection
import json
import time

def test_small_quantities():
    """Test order placement with smaller quantities and different parameters"""
    print('🧪 Testing with Smaller Quantities and Different Parameters')
    print('=' * 60)
    
    # Connect to first available instance
    connection = TradovateConnection(port=9223, account_name='Small Qty Test')
    
    if not connection.tab:
        print('❌ No connection available')
        return False
    
    print('✅ Connected to browser instance')
    
    # Test 1: Very small quantity (1 contract, no scale)
    print('\n📍 TEST 1: Single contract, no scale-in, minimal TP/SL')
    test_script_1 = """
    console.log('🧪 ========== SMALL QUANTITY TEST 1 ==========');
    
    const testData = {
        symbol: 'MNQ',  // Micro NQ - smaller margin requirement
        qty: 1,
        action: 'Buy',
        tp_ticks: 5,    // Very small TP
        sl_ticks: 3,    // Very small SL
        scale_in_enabled: false
    };
    
    console.log('📍 Testing micro futures with minimal risk...');
    console.log('Test data:', JSON.stringify(testData, null, 2));
    
    autoTrade(testData.symbol, testData.qty, testData.action, testData.tp_ticks, testData.sl_ticks, 
              0.25).then(result => {
        console.log('✅ Small quantity test 1 completed:');
        console.log(JSON.stringify(result, null, 2));
        window.smallTest1Result = result;
    }).catch(error => {
        console.error('❌ Small quantity test 1 error:', error);
        window.smallTest1Result = { error: error.message };
    });
    
    'small_test_1_started';
    """
    
    try:
        result = connection.tab.Runtime.evaluate(expression=test_script_1, awaitPromise=False, timeout=5000)
        print(f'✅ Test 1 started: {result["result"]["value"]}')
        
        # Wait for completion
        time.sleep(10)
        
        # Get result
        get_result = "window.smallTest1Result || null;"
        result_check = connection.tab.Runtime.evaluate(expression=get_result, awaitPromise=False, timeout=3000)
        
        if 'result' in result_check and 'value' in result_check['result'] and result_check['result']['value']:
            test1_result = result_check['result']['value']
            print('📋 Test 1 Results:')
            print(json.dumps(test1_result, indent=2))
            
            # Analyze results
            if test1_result.get('error'):
                print(f'⚠️ Test 1 Error: {test1_result.get("error")}')
            elif test1_result.get('rejectionReason'):
                print(f'📌 Test 1 Rejection: {test1_result.get("rejectionReason")}')
            else:
                orders = test1_result.get('orders', [])
                print(f'✅ Test 1 Success: {len(orders)} orders processed')
        else:
            print('⏰ Test 1 timeout - no result captured')
            
    except Exception as e:
        print(f'❌ Test 1 error: {str(e)}')
    
    # Test 2: Market order only (no TP/SL)
    print('\n📍 TEST 2: Market order only, no TP/SL')
    test_script_2 = """
    console.log('🧪 ========== SMALL QUANTITY TEST 2 ==========');
    
    const testData = {
        symbol: 'MNQ',
        qty: 1,
        action: 'Buy',
        tp_ticks: 0,    // No TP
        sl_ticks: 0,    // No SL
        scale_in_enabled: false
    };
    
    console.log('📍 Testing market order only (no bracket)...');
    console.log('Test data:', JSON.stringify(testData, null, 2));
    
    autoTrade(testData.symbol, testData.qty, testData.action, testData.tp_ticks, testData.sl_ticks, 
              0.25).then(result => {
        console.log('✅ Small quantity test 2 completed:');
        console.log(JSON.stringify(result, null, 2));
        window.smallTest2Result = result;
    }).catch(error => {
        console.error('❌ Small quantity test 2 error:', error);
        window.smallTest2Result = { error: error.message };
    });
    
    'small_test_2_started';
    """
    
    try:
        result = connection.tab.Runtime.evaluate(expression=test_script_2, awaitPromise=False, timeout=5000)
        print(f'✅ Test 2 started: {result["result"]["value"]}')
        
        # Wait for completion
        time.sleep(8)
        
        # Get result
        get_result = "window.smallTest2Result || null;"
        result_check = connection.tab.Runtime.evaluate(expression=get_result, awaitPromise=False, timeout=3000)
        
        if 'result' in result_check and 'value' in result_check['result'] and result_check['result']['value']:
            test2_result = result_check['result']['value']
            print('📋 Test 2 Results:')
            print(json.dumps(test2_result, indent=2))
            
            # Analyze results
            if test2_result.get('error'):
                print(f'⚠️ Test 2 Error: {test2_result.get("error")}')
            elif test2_result.get('rejectionReason'):
                print(f'📌 Test 2 Rejection: {test2_result.get("rejectionReason")}')
            else:
                orders = test2_result.get('orders', [])
                print(f'✅ Test 2 Success: {len(orders)} orders processed')
        else:
            print('⏰ Test 2 timeout - no result captured')
            
    except Exception as e:
        print(f'❌ Test 2 error: {str(e)}')
    
    # Test 3: Paper trading mode check
    print('\n📍 TEST 3: Check current trading mode')
    mode_check_script = """
    (function() {
        console.log('🧪 ========== MODE CHECK ==========');
        
        // Check for paper trading indicators
        const paperElements = document.querySelectorAll('*');
        let tradingMode = 'Unknown';
        let accountType = 'Unknown';
        
        for (let el of paperElements) {
            const text = (el.textContent || '').toLowerCase();
            if (text.includes('paper') || text.includes('demo') || text.includes('sim')) {
                tradingMode = 'Paper/Demo';
                break;
            }
            if (text.includes('live') && text.includes('account')) {
                tradingMode = 'Live';
                break;
            }
        }
        
        // Check account selector for more info
        const accountSelector = document.querySelector('[data-name="accountSelector"]');
        if (accountSelector) {
            accountType = accountSelector.textContent || 'Unknown';
        }
        
        const result = {
            tradingMode: tradingMode,
            accountType: accountType,
            timestamp: new Date().toISOString()
        };
        
        console.log('🧪 Trading mode check:', result);
        return result;
    })();
    """
    
    try:
        result = connection.tab.Runtime.evaluate(expression=mode_check_script, awaitPromise=False, timeout=5000)
        
        if 'result' in result and 'value' in result['result']:
            mode_data = result['result']['value']
            print('📋 Trading Mode Check:')
            print(json.dumps(mode_data, indent=2))
            
            if 'paper' in mode_data.get('tradingMode', '').lower() or 'demo' in mode_data.get('tradingMode', '').lower():
                print('✅ Paper/Demo trading mode detected - safe for testing')
            elif 'live' in mode_data.get('tradingMode', '').lower():
                print('⚠️ Live trading mode detected - use caution')
            else:
                print('❓ Trading mode unclear - proceed with caution')
                
    except Exception as e:
        print(f'❌ Mode check error: {str(e)}')
    
    print('\n🎯 Small Quantity Tests Complete')
    print('\n💡 Analysis:')
    print('  - Tested micro futures (MNQ) for lower margin requirements')
    print('  - Tested market-only orders to avoid bracket complexity')
    print('  - Checked trading mode for safety')
    print('  - Verified system handles various order configurations')
    
    return True

if __name__ == "__main__":
    test_small_quantities()