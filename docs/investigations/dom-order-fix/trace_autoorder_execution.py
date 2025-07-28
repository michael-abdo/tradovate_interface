#!/usr/bin/env python3
"""Trace the full autoOrder execution flow to find where it's failing"""

import asyncio
import websockets
import json
import subprocess

async def trace_execution():
    # Get current WebSocket URL
    result = subprocess.run(['curl', '-s', 'http://localhost:9223/json/list'], capture_output=True, text=True)
    ws_data = json.loads(result.stdout)[0]
    ws_url = ws_data['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url, ping_interval=None) as ws:
        print("🔍 Tracing autoOrder Execution Flow")
        print("=" * 60)
        
        # First check if autoOrder exists and has DOM fix
        msg1 = {
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {
                "expression": """
                    (() => {
                        const hasAutoOrder = typeof window.autoOrder === 'function';
                        const autoOrderCode = hasAutoOrder ? window.autoOrder.toString() : '';
                        const hasDOMFix = autoOrderCode.includes('submitOrderWithDOM');
                        
                        // Check what happens when we call the inner submitOrder
                        const hasSubmitOrder = autoOrderCode.includes('function submitOrder');
                        
                        return {
                            hasAutoOrder: hasAutoOrder,
                            autoOrderLength: autoOrderCode.length,
                            hasDOMFix: hasDOMFix,
                            hasSubmitOrder: hasSubmitOrder,
                            functionPreview: autoOrderCode.substring(0, 200)
                        };
                    })()
                """,
                "returnByValue": True
            }
        }
        
        await ws.send(json.dumps(msg1))
        response1 = await ws.recv()
        func_check = json.loads(response1)['result']['result']['value']
        
        print("Function check:")
        print(f"  Has autoOrder: {func_check['hasAutoOrder']}")
        print(f"  Function length: {func_check['autoOrderLength']}")
        print(f"  Has DOM fix: {func_check['hasDOMFix']}")
        print(f"  Has submitOrder: {func_check['hasSubmitOrder']}")
        
        # Inject comprehensive logging
        print("\n" + "="*60)
        print("Injecting execution tracer...")
        
        tracer_code = """
        window.executionTrace = [];
        
        // Wrap console.log to capture all logs
        const originalLog = console.log;
        console.log = function(...args) {
            window.executionTrace.push({
                type: 'log',
                message: args.join(' '),
                timestamp: Date.now()
            });
            originalLog.apply(console, args);
        };
        
        // Wrap console.error
        const originalError = console.error;
        console.error = function(...args) {
            window.executionTrace.push({
                type: 'error',
                message: args.join(' '),
                timestamp: Date.now()
            });
            originalError.apply(console, args);
        };
        
        // Clear trace
        window.clearTrace = function() {
            window.executionTrace = [];
        };
        
        // Get trace
        window.getTrace = function() {
            return window.executionTrace;
        };
        """
        
        msg2 = {
            "id": 2,
            "method": "Runtime.evaluate",
            "params": {
                "expression": tracer_code
            }
        }
        
        await ws.send(json.dumps(msg2))
        await ws.recv()
        
        # Now execute autoOrder with tracing
        print("\n" + "="*60)
        print("Executing autoOrder with full tracing...")
        
        msg3 = {
            "id": 3,
            "method": "Runtime.evaluate",
            "params": {
                "expression": """
                    (async () => {
                        // Clear previous trace
                        window.clearTrace();
                        
                        // Log current state
                        console.log('=== STARTING AUTOORDER TEST ===');
                        console.log('Current DOM position:', document.querySelector('.module-dom .info-column .number')?.textContent);
                        
                        try {
                            // Call autoOrder
                            console.log('Calling autoOrder...');
                            const result = await window.autoOrder('NQ', 1, 'Buy', 20, 10, 0.25);
                            console.log('autoOrder returned:', result);
                            
                            // Check if submitOrder was called
                            if (window.submitOrderCalled) {
                                console.log('submitOrder was called');
                            }
                            
                            // Check if DOM button was clicked
                            const domClicked = window.executionTrace.some(t => 
                                t.message.includes('Buy Market button') || 
                                t.message.includes('Sell Market button')
                            );
                            console.log('DOM button clicked:', domClicked);
                            
                        } catch (error) {
                            console.error('autoOrder error:', error.message);
                            console.error('Stack:', error.stack);
                        }
                        
                        console.log('=== AUTOORDER TEST COMPLETE ===');
                        
                        // Return the trace
                        return window.getTrace();
                    })()
                """,
                "awaitPromise": True,
                "returnByValue": True
            }
        }
        
        await ws.send(json.dumps(msg3))
        response3 = await ws.recv()
        trace = json.loads(response3)['result']['result']['value']
        
        print("\nExecution trace:")
        print("-" * 60)
        
        important_keywords = ['submitOrder', 'DOM', 'button', 'click', 'error', 'fail', 'CRITICAL', 'validation']
        
        for entry in trace:
            # Highlight important messages
            is_important = any(keyword in entry['message'] for keyword in important_keywords)
            prefix = "⭐" if is_important else "  "
            
            if entry['type'] == 'error':
                print(f"❌ ERROR: {entry['message']}")
            else:
                print(f"{prefix} {entry['message']}")
        
        # Check final DOM position
        print("\n" + "="*60)
        print("Checking final state...")
        
        msg4 = {
            "id": 4,
            "method": "Runtime.evaluate",
            "params": {
                "expression": """
                    (() => {
                        // Get all DOM positions
                        const positions = {};
                        document.querySelectorAll('.module-dom').forEach(mod => {
                            const symbol = mod.querySelector('.contract-symbol')?.textContent;
                            const position = mod.querySelector('.info-column .number')?.textContent;
                            if (symbol) {
                                positions[symbol] = position;
                            }
                        });
                        
                        // Check for any error messages
                        const errors = [];
                        document.querySelectorAll('.alert:not([style*="none"]), .error').forEach(el => {
                            if (el.offsetParent !== null) {
                                errors.push(el.textContent.trim());
                            }
                        });
                        
                        return {
                            domPositions: positions,
                            errors: errors
                        };
                    })()
                """,
                "returnByValue": True
            }
        }
        
        await ws.send(json.dumps(msg4))
        response4 = await ws.recv()
        final_state = json.loads(response4)['result']['result']['value']
        
        print("\nFinal DOM positions:")
        for symbol, position in final_state['domPositions'].items():
            print(f"  {symbol}: {position}")
        
        if final_state['errors']:
            print("\nError messages found:")
            for error in final_state['errors']:
                print(f"  ⚠️  {error}")

if __name__ == "__main__":
    asyncio.run(trace_execution())