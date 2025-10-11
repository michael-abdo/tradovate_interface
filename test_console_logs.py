#!/usr/bin/env python3
"""Test to check console logs for our modification evidence"""

from src.app import TradovateConnection
import json
import time

def test_console_logs():
    # Connect to first available instance
    connection = TradovateConnection(port=9223, account_name='Console Test')

    if not connection.tab:
        print('❌ No connection available')
        return False

    print('🧪 Testing console logs for modification evidence...')

    # Enable console logging
    connection.tab.Runtime.enable()
    connection.tab.Console.enable()
    
    # Store console messages
    console_messages = []
    
    def console_handler(event):
        if 'message' in event:
            msg = event['message']
            console_messages.append(msg)
            if 'submitOrder captured' in msg.get('text', '') or 'autoTrade' in msg.get('text', ''):
                print(f"📊 LOG: {msg.get('text', '')}")
    
    # Set up console message handler
    connection.tab.Console.messageAdded = console_handler

    try:
        # Clear console and inject a simple test
        clear_script = """
        console.clear();
        console.log('🧪 ========== CONSOLE LOG TEST START ==========');
        
        // Test if our functions exist
        console.log('📍 Checking function availability...');
        console.log('- submitOrder function exists:', typeof submitOrder !== 'undefined');
        console.log('- autoTrade function exists:', typeof autoTrade !== 'undefined');
        console.log('- captureOrderFeedback function exists:', typeof captureOrderFeedback !== 'undefined');
        console.log('- createBracketOrdersManual function exists:', typeof createBracketOrdersManual !== 'undefined');
        
        // Test captureOrderFeedback directly
        console.log('📍 Testing captureOrderFeedback directly...');
        captureOrderFeedback().then(result => {
            console.log('📊 captureOrderFeedback result:', JSON.stringify(result, null, 2));
        }).catch(error => {
            console.log('❌ captureOrderFeedback error:', error.message);
        });
        
        'console_test_started';
        """
        
        result = connection.tab.Runtime.evaluate(expression=clear_script, awaitPromise=False, timeout=5000)
        
        if 'result' in result and 'value' in result['result']:
            print(f'✅ Console test started: {result["result"]["value"]}')
            
            # Wait for console messages
            print('⏳ Waiting for console output...')
            time.sleep(5)
            
            # Check for specific modification evidence in console
            modification_evidence = []
            for msg in console_messages:
                text = msg.get('text', '')
                if any(keyword in text for keyword in [
                    'submitOrder captured',
                    'autoTrade', 
                    'captureOrderFeedback',
                    'bracket execution',
                    'feedback from bracket execution',
                    'Order history not found',
                    'rejection'
                ]):
                    modification_evidence.append(text)
                    
            print('\n📋 Modification Evidence in Console:')
            if modification_evidence:
                for evidence in modification_evidence:
                    print(f'  ✅ {evidence}')
                print(f'\n🎉 Found {len(modification_evidence)} pieces of evidence our modifications are active')
                return True
            else:
                print('❌ No evidence of our modifications found in console logs')
                print('📊 This suggests our changes may not be properly injected')
                
                # Show all console messages for debugging
                print('\n📋 All Console Messages:')
                for msg in console_messages[-10:]:  # Show last 10 messages
                    print(f'  📝 {msg.get("text", "")}')
                return False
                
        else:
            print('❌ Failed to start console test')
            return False
            
    except Exception as e:
        print(f'❌ Error executing console log test: {str(e)}')
        return False

if __name__ == "__main__":
    test_console_logs()