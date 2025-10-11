#!/usr/bin/env python3
"""Test single order placement to verify rejection feedback"""

from src.app import TradovateConnection
import json

def test_single_order():
    # Connect to first available instance
    connection = TradovateConnection(port=9223, account_name='Single Order Test')

    if not connection.tab:
        print('❌ No connection available')
        return False

    print('🧪 Testing single order placement with updated symbol selector...')

    # Test script for single order
    test_script = """
    console.log('🧪 ========== SINGLE ORDER TEST ==========');
    
    // Simple market order that should trigger rejection due to risk management
    const testData = {
        symbol: 'NQ',
        qty: 10,  // Large quantity to potentially trigger risk management
        action: 'Buy',
        orderType: 'MARKET'
    };
    
    console.log('📍 Testing autoTrade with single order...');
    console.log('Test data:', JSON.stringify(testData, null, 2));
    
    autoTrade(testData).then(result => {
        console.log('✅ autoTrade completed with result:');
        console.log(JSON.stringify(result, null, 2));
        
        // Store result for Python to retrieve
        window.singleOrderResult = result;
        
        // Analyze the result
        if (result.rejectionReason) {
            console.log('🎉 SUCCESS: Rejection reason captured:', result.rejectionReason);
        } else if (result.error === 'Order history not found') {
            console.log('❌ FAILURE: Still getting Order history not found');
        } else if (result.success) {
            console.log('✅ SUCCESS: Order placed successfully');
        } else {
            console.log('🔍 UNKNOWN: Unexpected result format');
        }
        
    }).catch(error => {
        console.error('❌ autoTrade error:', error);
        window.singleOrderResult = { error: error.message };
    });
    
    'single_order_test_started';
    """

    try:
        # Execute the test
        result = connection.tab.Runtime.evaluate(expression=test_script, awaitPromise=False, timeout=5000)
        
        if 'result' in result and 'value' in result['result']:
            print(f'✅ Test started: {result["result"]["value"]}')
            
            # Wait for order processing
            import time
            print('⏳ Waiting for order processing...')
            for i in range(15):  # Wait up to 15 seconds
                time.sleep(1)
                
                # Check for result
                get_result_script = "window.singleOrderResult || null;"
                result_check = connection.tab.Runtime.evaluate(expression=get_result_script, awaitPromise=False, timeout=3000)
                
                if 'result' in result_check and 'value' in result_check['result'] and result_check['result']['value']:
                    order_result = result_check['result']['value']
                    
                    print('\n📋 Single Order Test Results:')
                    print(json.dumps(order_result, indent=2))
                    
                    # Analyze the result
                    if order_result.get('rejectionReason'):
                        print(f'\n✅ SUCCESS: Rejection captured: {order_result.get("rejectionReason")}')
                        print('🎉 Our fix is working! Rejection details properly returned')
                        return True
                    elif order_result.get('error') == 'Order history not found':
                        print('\n❌ FAILURE: Still getting "Order history not found"')
                        print('😞 Our fix did not work as expected')
                        return False
                    elif order_result.get('success'):
                        print('\n✅ SUCCESS: Order placed successfully')
                        print('📊 This means account can place orders (no risk management rejection)')
                        return True
                    elif order_result.get('error'):
                        print(f'\n⚠️ ERROR: {order_result.get("error")}')
                        return False
                    else:
                        print('\n🔍 UNKNOWN: Unexpected result format')
                        return False
                        
                print(f'⏳ Still waiting... ({i+1}/15)')
            
            print('⏰ Timeout waiting for order result')
            return False
                
        else:
            print('❌ Failed to start test')
            return False
            
    except Exception as e:
        print(f'❌ Error executing single order test: {str(e)}')
        return False

if __name__ == "__main__":
    success = test_single_order()
    if success:
        print('\n🎉 Single order test completed successfully!')
    else:
        print('\n😞 Single order test failed')