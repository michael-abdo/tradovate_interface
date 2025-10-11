#!/usr/bin/env python3
"""Test scale order verification with multiple orders"""

from src.app import TradovateConnection
import json
import time

def test_scale_order_verification():
    """Test that scale orders are verified correctly"""
    print('🧪 Testing Scale Order Verification with Multiple Orders')
    print('=' * 60)
    
    # Connect to first available instance
    connection = TradovateConnection(port=9223, account_name='Scale Test')
    
    if not connection.tab:
        print('❌ No connection available')
        return False
    
    print('✅ Connected to browser instance')
    
    # Test 1: Test scale order with 2 levels (should work)
    print('\n📍 TEST 1: Scale order with 2 levels (2 contracts)')
    test_script_1 = """
    console.log('🧪 ========== SCALE ORDER TEST 1 ==========');
    
    const testData = {
        symbol: 'NQ',
        qty: 2,
        action: 'Buy',
        tp_ticks: 20,
        sl_ticks: 10,
        scale_in_enabled: true,
        scale_levels: 2,
        scale_ticks: 20
    };
    
    console.log('📍 Testing scale order (2 levels, 2 contracts)...');
    console.log('Test data:', JSON.stringify(testData, null, 2));
    
    autoTrade(testData.symbol, testData.qty, testData.action, testData.tp_ticks, testData.sl_ticks, 
              0.25, null, null, null, null, null, null, null, null, null, 
              testData.scale_in_enabled, testData.scale_levels, testData.scale_ticks).then(result => {
        console.log('✅ Scale order test 1 completed:');
        console.log(JSON.stringify(result, null, 2));
        window.scaleTest1Result = result;
    }).catch(error => {
        console.error('❌ Scale order test 1 error:', error);
        window.scaleTest1Result = { error: error.message };
    });
    
    'scale_test_1_started';
    """
    
    try:
        result = connection.tab.Runtime.evaluate(expression=test_script_1, awaitPromise=False, timeout=5000)
        print(f'✅ Test 1 started: {result["result"]["value"]}')
        
        # Wait for completion
        time.sleep(8)
        
        # Get result
        get_result = "window.scaleTest1Result || null;"
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
    
    # Test 2: Test with invalid scale configuration (should be handled)
    print('\n📍 TEST 2: Invalid scale config (1 contract, 4 levels)')
    test_script_2 = """
    console.log('🧪 ========== SCALE ORDER TEST 2 ==========');
    
    const testData = {
        symbol: 'NQ', 
        qty: 1,
        action: 'Buy',
        tp_ticks: 20,
        sl_ticks: 10,
        scale_in_enabled: true,
        scale_levels: 4,
        scale_ticks: 20
    };
    
    console.log('📍 Testing invalid scale order (1 contract, 4 levels)...');
    console.log('Test data:', JSON.stringify(testData, null, 2));
    
    autoTrade(testData.symbol, testData.qty, testData.action, testData.tp_ticks, testData.sl_ticks,
              0.25, null, null, null, null, null, null, null, null, null,
              testData.scale_in_enabled, testData.scale_levels, testData.scale_ticks).then(result => {
        console.log('✅ Scale order test 2 completed:');
        console.log(JSON.stringify(result, null, 2));
        window.scaleTest2Result = result;
    }).catch(error => {
        console.error('❌ Scale order test 2 error:', error);
        window.scaleTest2Result = { error: error.message };
    });
    
    'scale_test_2_started';
    """
    
    try:
        result = connection.tab.Runtime.evaluate(expression=test_script_2, awaitPromise=False, timeout=5000)
        print(f'✅ Test 2 started: {result["result"]["value"]}')
        
        # Wait for completion
        time.sleep(8)
        
        # Get result
        get_result = "window.scaleTest2Result || null;"
        result_check = connection.tab.Runtime.evaluate(expression=get_result, awaitPromise=False, timeout=3000)
        
        if 'result' in result_check and 'value' in result_check['result'] and result_check['result']['value']:
            test2_result = result_check['result']['value']
            print('📋 Test 2 Results:')
            print(json.dumps(test2_result, indent=2))
            
            # This should either be handled gracefully or show clear error
            if test2_result.get('error'):
                print(f'✅ Test 2 correctly handled error: {test2_result.get("error")}')
            elif test2_result.get('rejectionReason'):
                print(f'✅ Test 2 correctly rejected: {test2_result.get("rejectionReason")}')
            else:
                print('⚠️ Test 2 unexpected success - should have been handled')
        else:
            print('⏰ Test 2 timeout - no result captured')
            
    except Exception as e:
        print(f'❌ Test 2 error: {str(e)}')
    
    print('\n🎯 Scale Order Verification Tests Complete')
    return True

if __name__ == "__main__":
    test_scale_order_verification()