#!/usr/bin/env python3
"""Test order feedback capture manually"""

from src.app import TradovateConnection
import json

def test_manual_order_feedback():
    # Connect to first available instance
    connection = TradovateConnection(port=9222, account_name='Manual Test')

    if not connection.tab:
        print('❌ No connection available')
        return False

    print('🧪 Testing manual order feedback capture...')

    # Test script to manually trigger order placement and capture feedback
    test_script = """
    console.log('🧪 ========== MANUAL ORDER FEEDBACK TEST ==========');
    
    // First, let's try to capture existing order feedback
    console.log('📍 STEP 1: Testing captureOrderFeedback() directly...');
    
    (async function testOrderFeedback() {
        try {
            const result = await captureOrderFeedback();
            console.log('📊 CAPTURE RESULT:', JSON.stringify(result, null, 2));
            return result;
        } catch (error) {
            console.error('❌ Error in captureOrderFeedback:', error);
            return { error: error.message };
        }
    })();
    """

    try:
        # Execute the test script
        result = connection.tab.Runtime.evaluate(expression=test_script, awaitPromise=True, timeout=10000)
        
        if 'result' in result and 'value' in result['result']:
            feedback_result = result['result']['value']
            print('\n📋 Manual Order Feedback Test Results:')
            print(json.dumps(feedback_result, indent=2))
            
            # Now test with waiting function
            wait_test_script = """
            console.log('📍 STEP 2: Testing waitForOrderFeedback() function...');
            
            (async function testWaitFeedback() {
                try {
                    const result = await waitForOrderFeedback(5000, 500);  // 5 second timeout
                    console.log('⏳ WAIT RESULT:', JSON.stringify(result, null, 2));
                    return result;
                } catch (error) {
                    console.error('❌ Error in waitForOrderFeedback:', error);
                    return { error: error.message };
                }
            })();
            """
            
            wait_result = connection.tab.Runtime.evaluate(expression=wait_test_script, awaitPromise=True, timeout=15000)
            
            if 'result' in wait_result and 'value' in wait_result['result']:
                wait_feedback = wait_result['result']['value']
                print('\n⏳ Wait For Order Feedback Test Results:')
                print(json.dumps(wait_feedback, indent=2))
                
                # Analyze results
                if feedback_result.get('success') == False and feedback_result.get('error') == 'Order history not found':
                    print('\n❌ Issue confirmed: Order history div not found')
                    print('   This explains why "Order history not found" is returned')
                    print('   The .order-history selector is not finding any elements')
                    
                elif feedback_result.get('rejectionReason'):
                    print(f'\n✅ Rejection detected: {feedback_result.get("rejectionReason")}')
                    print('   The rejection detection is working properly')
                    
                else:
                    print('\n🔍 Need to analyze current UI state')
                    
                return True
                
        else:
            print('❌ No results returned from browser test')
            print(f'Raw result: {result}')
            return False
            
    except Exception as e:
        print(f'❌ Error executing feedback test: {str(e)}')
        return False

if __name__ == "__main__":
    test_manual_order_feedback()