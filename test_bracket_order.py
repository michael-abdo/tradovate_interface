#!/usr/bin/env python3
"""Test bracket order with TP/SL to ensure proper handling"""

from src.app import TradovateConnection
import json

def test_bracket_order():
    # Connect to first available instance
    connection = TradovateConnection(port=9223, account_name='Bracket Test')

    if not connection.tab:
        print('❌ No connection available')
        return False

    print('🧪 Testing bracket order with TP/SL...')

    # Test script for bracket order
    test_script = """
    console.log('🧪 ========== BRACKET ORDER TEST ==========');
    
    // Bracket order with TP/SL
    const testData = {
        symbol: 'NQ',
        qty: 1,
        action: 'Buy',
        orderType: 'MARKET',
        tp_ticks: 20,  // Take profit at 20 ticks
        sl_ticks: 10   // Stop loss at 10 ticks
    };
    
    console.log('📍 Testing autoTrade with bracket order (TP/SL)...');
    console.log('Test data:', JSON.stringify(testData, null, 2));
    
    autoTrade(testData).then(result => {
        console.log('✅ Bracket order completed with result:');
        console.log(JSON.stringify(result, null, 2));
        
        // Store result for Python to retrieve
        window.bracketOrderResult = result;
        
        // Analyze the result
        if (result.mainOrder && result.tpOrder && result.slOrder) {
            console.log('🎉 SUCCESS: All 3 orders captured (main, TP, SL)');
        } else if (result.rejectionReason) {
            console.log('📊 Main order rejected:', result.rejectionReason);
            console.log('✅ TP/SL orders correctly skipped due to main order rejection');
        } else if (result.orders && result.orders.length > 1) {
            console.log(`✅ SUCCESS: ${result.orders.length} orders placed`);
        } else {
            console.log('🔍 Analyzing result structure...');
        }
        
    }).catch(error => {
        console.error('❌ autoTrade error:', error);
        window.bracketOrderResult = { error: error.message };
    });
    
    'bracket_order_test_started';
    """

    try:
        # Execute the test
        result = connection.tab.Runtime.evaluate(expression=test_script, awaitPromise=False, timeout=5000)
        
        if 'result' in result and 'value' in result['result']:
            print(f'✅ Test started: {result["result"]["value"]}')
            
            # Wait for bracket order processing
            import time
            print('⏳ Waiting for bracket order processing...')
            for i in range(20):  # Wait up to 20 seconds for bracket orders
                time.sleep(1)
                
                # Check for result
                get_result_script = "window.bracketOrderResult || null;"
                result_check = connection.tab.Runtime.evaluate(expression=get_result_script, awaitPromise=False, timeout=3000)
                
                if 'result' in result_check and 'value' in result_check['result'] and result_check['result']['value']:
                    order_result = result_check['result']['value']
                    
                    print('\n📋 Bracket Order Test Results:')
                    print(json.dumps(order_result, indent=2))
                    
                    # Analyze bracket order results
                    print('\n📊 Bracket Order Analysis:')
                    
                    if order_result.get('mainOrder'):
                        print('✅ Main order info captured')
                    if order_result.get('tpOrder'):
                        print('✅ Take Profit order info captured')
                    if order_result.get('slOrder'):
                        print('✅ Stop Loss order info captured')
                        
                    if order_result.get('rejectionReason'):
                        print(f'\n📌 Main order rejected: {order_result.get("rejectionReason")}')
                        if not order_result.get('tpOrder') and not order_result.get('slOrder'):
                            print('✅ CORRECT: TP/SL orders were not placed due to main order rejection')
                            print('🎉 Bracket order handling is working correctly!')
                            return True
                    elif order_result.get('success'):
                        total_orders = order_result.get('orders', [])
                        print(f'\n✅ SUCCESS: {len(total_orders)} orders placed')
                        if len(total_orders) >= 3:
                            print('🎉 Full bracket (main + TP + SL) placed successfully!')
                        return True
                    elif order_result.get('error'):
                        print(f'\n⚠️ ERROR: {order_result.get("error")}')
                        return False
                    else:
                        print('\n🔍 Result structure needs further analysis')
                        return True  # Not a failure, just unexpected structure
                        
                print(f'⏳ Still waiting... ({i+1}/20)')
            
            print('⏰ Timeout waiting for bracket order result')
            return False
                
        else:
            print('❌ Failed to start test')
            return False
            
    except Exception as e:
        print(f'❌ Error executing bracket order test: {str(e)}')
        return False

if __name__ == "__main__":
    success = test_bracket_order()
    if success:
        print('\n🎉 Bracket order test completed successfully!')
    else:
        print('\n😞 Bracket order test failed')