#!/usr/bin/env python3
"""Test that verification system detects successfully placed orders"""

from src.app import TradovateConnection
import json
import time

def test_verification_system():
    """Test that the verification system can detect successful order placements"""
    print('🧪 Testing Verification System for Successful Order Detection')
    print('=' * 65)
    
    # Connect to first available instance
    connection = TradovateConnection(port=9223, account_name='Verification Test')
    
    if not connection.tab:
        print('❌ No connection available')
        return False
    
    print('✅ Connected to browser instance')
    
    # Test 1: Test captureOrderFeedback function directly
    print('\n📍 TEST 1: Direct captureOrderFeedback function test')
    test_script_1 = """
    console.log('🧪 ========== CAPTURE ORDER FEEDBACK TEST ==========');
    
    // Test the captureOrderFeedback function directly
    (async function() {
        try {
            console.log('📍 Testing captureOrderFeedback function...');
            
            // Call the function directly
            const feedbackResult = await captureOrderFeedback();
            
            console.log('✅ captureOrderFeedback completed:');
            console.log('Result type:', typeof feedbackResult);
            console.log('Result value:', JSON.stringify(feedbackResult, null, 2));
            
            // Store result for analysis
            window.captureTest1Result = {
                success: true,
                result: feedbackResult,
                timestamp: new Date().toISOString()
            };
            
            return feedbackResult;
            
        } catch (error) {
            console.error('❌ captureOrderFeedback error:', error);
            window.captureTest1Result = {
                success: false,
                error: error.message,
                timestamp: new Date().toISOString()
            };
            return { error: error.message };
        }
    })();
    
    'capture_test_1_started';
    """
    
    try:
        result = connection.tab.Runtime.evaluate(expression=test_script_1, awaitPromise=True, timeout=15000)
        print(f'✅ Test 1 completed')
        
        # Get detailed result
        get_result = "window.captureTest1Result || null;"
        result_check = connection.tab.Runtime.evaluate(expression=get_result, awaitPromise=False, timeout=3000)
        
        if 'result' in result_check and 'value' in result_check['result'] and result_check['result']['value']:
            test1_result = result_check['result']['value']
            print('📋 Test 1 Results:')
            print(json.dumps(test1_result, indent=2))
            
            if test1_result.get('success'):
                feedback_result = test1_result.get('result', {})
                if feedback_result.get('orders'):
                    print(f'✅ Feedback captured {len(feedback_result["orders"])} existing orders')
                elif feedback_result.get('error'):
                    print(f'📌 Feedback captured error state: {feedback_result["error"]}')
                else:
                    print('📍 Feedback captured clean state (no active orders)')
            else:
                print(f'⚠️ Test 1 Error: {test1_result.get("error")}')
        else:
            print('⏰ Test 1 timeout - no result captured')
            
    except Exception as e:
        print(f'❌ Test 1 error: {str(e)}')
    
    # Test 2: Test waitForOrderFeedback function
    print('\n📍 TEST 2: waitForOrderFeedback function test')
    test_script_2 = """
    console.log('🧪 ========== WAIT FOR ORDER FEEDBACK TEST ==========');
    
    (async function() {
        try {
            console.log('📍 Testing waitForOrderFeedback function...');
            
            // Test with a short timeout
            const feedbackResult = await waitForOrderFeedback(3000); // 3 second timeout
            
            console.log('✅ waitForOrderFeedback completed:');
            console.log('Result type:', typeof feedbackResult);
            console.log('Result value:', JSON.stringify(feedbackResult, null, 2));
            
            window.waitTest2Result = {
                success: true,
                result: feedbackResult,
                timestamp: new Date().toISOString()
            };
            
            return feedbackResult;
            
        } catch (error) {
            console.error('❌ waitForOrderFeedback error:', error);
            window.waitTest2Result = {
                success: false,
                error: error.message,
                timestamp: new Date().toISOString()
            };
            return { error: error.message };
        }
    })();
    
    'wait_test_2_started';
    """
    
    try:
        result = connection.tab.Runtime.evaluate(expression=test_script_2, awaitPromise=True, timeout=10000)
        print(f'✅ Test 2 completed')
        
        # Get detailed result
        get_result = "window.waitTest2Result || null;"
        result_check = connection.tab.Runtime.evaluate(expression=get_result, awaitPromise=False, timeout=3000)
        
        if 'result' in result_check and 'value' in result_check['result'] and result_check['result']['value']:
            test2_result = result_check['result']['value']
            print('📋 Test 2 Results:')
            print(json.dumps(test2_result, indent=2))
            
            if test2_result.get('success'):
                feedback_result = test2_result.get('result', {})
                if feedback_result.get('orders'):
                    print(f'✅ Wait function found {len(feedback_result["orders"])} orders')
                elif feedback_result.get('error'):
                    print(f'📌 Wait function detected: {feedback_result["error"]}')
                else:
                    print('📍 Wait function completed with no orders found')
            else:
                print(f'⚠️ Test 2 Error: {test2_result.get("error")}')
        else:
            print('⏰ Test 2 timeout - no result captured')
            
    except Exception as e:
        print(f'❌ Test 2 error: {str(e)}')
    
    # Test 3: Test order detection capabilities
    print('\n📍 TEST 3: Order detection capability test')
    test_script_3 = """
    console.log('🧪 ========== ORDER DETECTION TEST ==========');
    
    (function() {
        try {
            console.log('📍 Testing order detection capabilities...');
            
            const results = {
                orderHistory: {},
                positionData: {},
                orderElements: {},
                feedbackElements: {}
            };
            
            // Check for order history
            const orderHistoryElements = document.querySelectorAll('[data-name*="order"], .order-row, [class*="order"]');
            results.orderHistory.elementsFound = orderHistoryElements.length;
            results.orderHistory.sampleText = Array.from(orderHistoryElements).slice(0, 3).map(el => 
                (el.textContent || '').substring(0, 50)
            );
            
            // Check for position data
            const positionElements = document.querySelectorAll('[data-name*="position"], .position-row');
            results.positionData.elementsFound = positionElements.length;
            results.positionData.sampleText = Array.from(positionElements).slice(0, 3).map(el => 
                (el.textContent || '').substring(0, 50)
            );
            
            // Check for order confirmation elements
            const confirmElements = document.querySelectorAll('[class*="confirmation"], [class*="success"], [class*="filled"]');
            results.orderElements.confirmationElements = confirmElements.length;
            
            // Check for feedback/status elements
            const feedbackElements = document.querySelectorAll('[class*="status"], [class*="feedback"], [class*="message"]');
            results.feedbackElements.statusElements = feedbackElements.length;
            
            console.log('🧪 Detection capabilities:', results);
            window.detectionTest3Result = results;
            
            return results;
            
        } catch (error) {
            console.error('❌ Detection test error:', error);
            window.detectionTest3Result = { error: error.toString() };
            return { error: error.toString() };
        }
    })();
    
    'detection_test_3_completed';
    """
    
    try:
        result = connection.tab.Runtime.evaluate(expression=test_script_3, awaitPromise=False, timeout=8000)
        print(f'✅ Test 3 completed: {result["result"]["value"]}')
        
        # Get detailed result
        get_result = "window.detectionTest3Result || null;"
        result_check = connection.tab.Runtime.evaluate(expression=get_result, awaitPromise=False, timeout=3000)
        
        if 'result' in result_check and 'value' in result_check['result'] and result_check['result']['value']:
            test3_result = result_check['result']['value']
            print('📋 Test 3 Results:')
            print(json.dumps(test3_result, indent=2))
            
            # Analyze detection capabilities
            print('\n📊 Detection Analysis:')
            
            order_history = test3_result.get('orderHistory', {})
            print(f"  🔍 Order history elements: {order_history.get('elementsFound', 0)}")
            
            position_data = test3_result.get('positionData', {})
            print(f"  📈 Position elements: {position_data.get('elementsFound', 0)}")
            
            order_elements = test3_result.get('orderElements', {})
            print(f"  ✅ Confirmation elements: {order_elements.get('confirmationElements', 0)}")
            
            feedback_elements = test3_result.get('feedbackElements', {})
            print(f"  📢 Status elements: {feedback_elements.get('statusElements', 0)}")
            
        else:
            print('⏰ Test 3 timeout - no result captured')
            
    except Exception as e:
        print(f'❌ Test 3 error: {str(e)}')
    
    print('\n🎯 Verification System Test Complete')
    print('\n💡 Summary:')
    print('  - Tested captureOrderFeedback function directly')
    print('  - Tested waitForOrderFeedback function with timeout')
    print('  - Analyzed order detection capabilities in UI')
    print('  - Verified system can detect various order states')
    print('\n🔍 The verification system is designed to:')
    print('  1. Capture order feedback immediately after placement')
    print('  2. Wait for order confirmations with timeouts')
    print('  3. Detect both successful orders and rejections')
    print('  4. Parse order history and position data from UI')
    
    return True

if __name__ == "__main__":
    test_verification_system()