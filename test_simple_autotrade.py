#!/usr/bin/env python3
"""Simple test to verify autoTrade modifications work"""

from src.app import TradovateConnection
import json

def test_simple_autotrade():
    # Connect to first available instance
    connection = TradovateConnection(port=9223, account_name='Simple Test')

    if not connection.tab:
        print('❌ No connection available')
        return False

    print('🧪 Testing autoTrade function with simple market order...')

    # Simple test script
    test_script = """
    console.log('🧪 ========== SIMPLE AUTOTRADE TEST ==========');
    
    // Simple trade data
    const testData = {
        symbol: 'NQ',
        qty: 1,
        action: 'Buy',
        orderType: 'MARKET'
    };
    
    console.log('📍 Starting autoTrade test...');
    
    // Call autoTrade and capture result
    autoTrade(testData).then(result => {
        console.log('✅ autoTrade completed:', JSON.stringify(result, null, 2));
        window.autoTradeTestResult = result;  // Store for Python to retrieve
    }).catch(error => {
        console.error('❌ autoTrade error:', error);
        window.autoTradeTestResult = { error: error.message };
    });
    
    'test_started';  // Return value
    """

    try:
        # Execute the test script
        result = connection.tab.Runtime.evaluate(expression=test_script, awaitPromise=False, timeout=5000)
        
        if 'result' in result and 'value' in result['result']:
            print(f'✅ Test script started: {result["result"]["value"]}')
            
            # Wait a moment for autoTrade to complete
            import time
            print('⏳ Waiting for autoTrade to complete...')
            time.sleep(10)
            
            # Retrieve the result
            get_result_script = "window.autoTradeTestResult || 'still_running';"
            result_check = connection.tab.Runtime.evaluate(expression=get_result_script, awaitPromise=False, timeout=5000)
            
            if 'result' in result_check and 'value' in result_check['result']:
                autotrade_result = result_check['result']['value']
                
                if autotrade_result == 'still_running':
                    print('⏳ AutoTrade still running, waiting longer...')
                    time.sleep(10)
                    result_check = connection.tab.Runtime.evaluate(expression=get_result_script, awaitPromise=False, timeout=5000)
                    autotrade_result = result_check['result']['value']
                
                print('\n📋 AutoTrade Test Results:')
                if isinstance(autotrade_result, dict):
                    print(json.dumps(autotrade_result, indent=2))
                    
                    # Analyze the result
                    if autotrade_result.get('rejectionReason'):
                        print(f'\n✅ SUCCESS: Rejection captured: {autotrade_result.get("rejectionReason")}')
                        print('🎉 Our fix is working! No more "Order history not found"')
                        return True
                    elif autotrade_result.get('error') == 'Order history not found':
                        print('\n❌ FAILURE: Still getting "Order history not found"')
                        print('😞 Our fix did not work as expected')
                        return False
                    elif autotrade_result.get('success'):
                        print('\n✅ SUCCESS: Order placed successfully')
                        print('📊 This indicates the verification system is working')
                        return True
                    else:
                        print('\n🔍 UNKNOWN: Unexpected result format')
                        return False
                else:
                    print(f'📊 Result: {autotrade_result}')
                    return False
            else:
                print('❌ Could not retrieve autoTrade result')
                return False
                
        else:
            print('❌ Failed to start test script')
            print(f'Raw result: {result}')
            return False
            
    except Exception as e:
        print(f'❌ Error executing simple autoTrade test: {str(e)}')
        return False

if __name__ == "__main__":
    test_simple_autotrade()