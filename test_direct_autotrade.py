#!/usr/bin/env python3
"""Test autoTrade function directly to verify new feedback flow"""

from src.app import TradovateConnection
import json

def test_direct_autotrade():
    # Connect to first available instance
    connection = TradovateConnection(port=9222, account_name='Direct Test')

    if not connection.tab:
        print('❌ No connection available')
        return False

    print('🧪 Testing autoTrade function directly...')

    # Test script to call autoTrade directly
    test_script = """
    console.log('🧪 ========== DIRECT AUTOTRADE TEST ==========');
    
    // Define test trade data that should trigger rejection
    const testTradeData = {
        symbol: 'NQ',
        qty: 1,
        action: 'Buy',
        orderType: 'MARKET',
        takeProfit: null,  // Disable TP/SL to simplify
        stopLoss: null
    };
    
    console.log('📍 Calling autoTrade with test data...');
    
    (async function testAutoTrade() {
        try {
            const result = await autoTrade(testTradeData);
            console.log('✅ autoTrade completed, result:', JSON.stringify(result, null, 2));
            return result;
        } catch (error) {
            console.error('❌ Error in autoTrade:', error);
            return { error: error.message };
        }
    })();
    """

    try:
        # Execute the test script
        result = connection.tab.Runtime.evaluate(expression=test_script, awaitPromise=True, timeout=30000)
        
        if 'result' in result and 'value' in result['result']:
            autotrade_result = result['result']['value']
            print('\n📋 Direct autoTrade Test Results:')
            print(json.dumps(autotrade_result, indent=2))
            
            # Analyze the result
            if autotrade_result.get('rejectionReason'):
                print(f'\n✅ SUCCESS: Rejection captured properly: {autotrade_result.get("rejectionReason")}')
                print('🎉 Our fix is working! No more "Order history not found"')
                return True
            elif autotrade_result.get('error') == 'Order history not found':
                print('\n❌ FAILURE: Still getting "Order history not found"')
                print('😞 Our fix did not work as expected')
                return False
            elif autotrade_result.get('success'):
                print('\n✅ SUCCESS: Order placed successfully')
                print('📊 This indicates the verification system is working for success cases')
                return True
            else:
                print('\n🔍 UNKNOWN: Unexpected result format')
                print('🤔 Need to investigate further')
                return False
                
        else:
            print('❌ No results returned from browser test')
            print(f'Raw result: {result}')
            return False
            
    except Exception as e:
        print(f'❌ Error executing autoTrade test: {str(e)}')
        return False

if __name__ == "__main__":
    test_direct_autotrade()