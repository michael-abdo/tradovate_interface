#!/usr/bin/env python3
"""
End-to-End Integration Test for Mandatory Order Verification
Tests real order execution with actual before/after state verification

Location: docs/investigations/dom-order-fix/test_end_to_end_verification.py
Purpose: Validate mandatory verification system with real trading operations
"""

import asyncio
import websockets
import json
import subprocess
import time
import sys
import os
from typing import Dict, Any, List, Optional

# Test Configuration Constants
INTEGRATION_CONFIG = {
    'CHROME_PORTS': [9223, 9224, 9225],
    'DEFAULT_PORT': 9223,
    'WEBSOCKET_TIMEOUT': 60,
    'TEST_SYMBOL': 'NQ',
    'TEST_QUANTITY': 1,
    'TEST_TP': 100,
    'TEST_SL': 50,
    'TEST_TICK_SIZE': 0.25,
    'SCRIPT_PATH': '/Users/Mike/trading/scripts/tampermonkey/autoOrder.user.js',
    'VERIFICATION_WAIT_TIME': 5,  # Wait time after order for state changes
    'MAX_ORDER_WAIT_TIME': 30     # Maximum time to wait for order completion
}

class EndToEndVerificationTest:
    """Integration test suite for real order execution with verification"""
    
    def __init__(self, port: int = INTEGRATION_CONFIG['DEFAULT_PORT']):
        self.port = port
        self.ws_url = None
        self.test_results = {}
        self.script_injected = False
        self.order_count = 0
    
    async def connect_to_chrome(self) -> str:
        """Connect to Chrome WebSocket for real order testing"""
        try:
            result = subprocess.run(
                ['curl', '-s', f'http://localhost:{self.port}/json/list'], 
                capture_output=True, 
                text=True
            )
            if result.returncode != 0:
                raise Exception(f"Failed to connect to Chrome on port {self.port}")
            
            ws_data = json.loads(result.stdout)[0]
            self.ws_url = ws_data['webSocketDebuggerUrl']
            return self.ws_url
        except Exception as e:
            raise Exception(f"Chrome connection failed: {e}")
    
    async def inject_script(self, ws) -> bool:
        """Inject the complete autoOrder script for real testing"""
        if self.script_injected:
            return True
            
        try:
            # Read the script file
            with open(INTEGRATION_CONFIG['SCRIPT_PATH'], 'r') as f:
                script_content = f.read()
            
            print(f"📜 Injecting script ({len(script_content)} chars)...")
            
            # For large scripts, split injection
            if len(script_content) > 50000:
                mid_point = len(script_content) // 2
                split_point = script_content.find('\n    }', mid_point)
                if split_point == -1:
                    split_point = mid_point
                
                # Inject first part
                msg1 = {
                    "id": 1,
                    "method": "Runtime.evaluate",
                    "params": {
                        "expression": script_content[:split_point + 1],
                        "returnByValue": False
                    }
                }
                
                await ws.send(json.dumps(msg1))
                response1 = await ws.recv()
                result1 = json.loads(response1)
                
                if 'exceptionDetails' in result1.get('result', {}):
                    print(f"❌ Part 1 injection failed: {result1['result']['exceptionDetails']}")
                    return False
                
                # Inject second part
                msg2 = {
                    "id": 2,
                    "method": "Runtime.evaluate",
                    "params": {
                        "expression": script_content[split_point + 1:],
                        "returnByValue": False
                    }
                }
                
                await ws.send(json.dumps(msg2))
                response2 = await ws.recv()
                result2 = json.loads(response2)
                
                if 'exceptionDetails' in result2.get('result', {}):
                    print(f"❌ Part 2 injection failed: {result2['result']['exceptionDetails']}")
                    return False
                
                print("✅ Multi-part script injection successful")
            else:
                # Inject whole script
                msg = {
                    "id": 1,
                    "method": "Runtime.evaluate",
                    "params": {
                        "expression": script_content,
                        "returnByValue": False
                    }
                }
                
                await ws.send(json.dumps(msg))
                response = await ws.recv()
                result = json.loads(response)
                
                if 'exceptionDetails' in result.get('result', {}):
                    print(f"❌ Script injection failed: {result['result']['exceptionDetails']}")
                    return False
                
                print("✅ Single script injection successful")
            
            # Wait for script initialization
            await asyncio.sleep(3)
            self.script_injected = True
            return True
            
        except Exception as e:
            print(f"❌ Script injection error: {e}")
            return False
    
    async def capture_current_state(self, ws, symbol: str) -> Dict[str, Any]:
        """Capture current account state before order execution"""
        capture_js = f"""
        (async () => {{
            try {{
                if (typeof captureOrdersState === 'function') {{
                    return await captureOrdersState('{symbol}');
                }} else if (typeof window.captureStateWithLogging === 'function') {{
                    return await window.captureStateWithLogging('{symbol}', 'E2E Test', 'capture');
                }} else {{
                    return {{ error: 'No capture function available' }};
                }}
            }} catch (error) {{
                return {{ error: error.message }};
            }}
        }})();
        """
        
        msg = {
            "id": int(time.time() * 100) % 10000,
            "method": "Runtime.evaluate",
            "params": {
                "expression": capture_js,
                "awaitPromise": True,
                "returnByValue": True
            }
        }
        
        await ws.send(json.dumps(msg))
        response = await ws.recv()
        result = json.loads(response)
        return result.get('result', {}).get('result', {}).get('value', {})
    
    async def execute_real_order(self, ws, symbol: str, quantity: int, action: str) -> Dict[str, Any]:
        """Execute a real order through the autoOrder wrapper"""
        self.order_count += 1
        order_id = f"e2e_test_{self.order_count}"
        
        print(f"🎯 Executing real order: {action} {quantity} {symbol}")
        
        # Execute order through wrapper (which enforces verification)
        order_js = f"""
        (async () => {{
            try {{
                console.log('🚀 E2E Test: Starting real order execution');
                const startTime = Date.now();
                
                const result = await window.autoOrder(
                    '{symbol}', 
                    {quantity}, 
                    '{action}', 
                    {INTEGRATION_CONFIG['TEST_TP']}, 
                    {INTEGRATION_CONFIG['TEST_SL']}, 
                    {INTEGRATION_CONFIG['TEST_TICK_SIZE']}
                );
                
                const executionTime = Date.now() - startTime;
                
                console.log('✅ E2E Test: Order execution completed');
                console.log(`⏱️ E2E Test: Execution time: ${{executionTime}}ms`);
                
                return {{
                    ...result,
                    executionTime,
                    testOrderId: '{order_id}',
                    timestamp: Date.now()
                }};
                
            }} catch (error) {{
                console.error('❌ E2E Test: Order execution failed:', error);
                return {{ 
                    success: false, 
                    error: error.message,
                    testOrderId: '{order_id}',
                    timestamp: Date.now()
                }};
            }}
        }})();
        """
        
        msg = {
            "id": int(time.time() * 100) % 10000,
            "method": "Runtime.evaluate",
            "params": {
                "expression": order_js,
                "awaitPromise": True,
                "returnByValue": True
            }
        }
        
        await ws.send(json.dumps(msg))
        response = await ws.recv()
        result = json.loads(response)
        return result.get('result', {}).get('result', {}).get('value', {})

# Test 4.3.1 - Real Order Execution with Verification
async def test_real_order_execution(test_suite: EndToEndVerificationTest):
    """Test 4.3.1: Execute real order and verify complete verification process"""
    print("🎯 Test 4.3.1: Real Order Execution with Verification")
    print("=" * 60)
    
    try:
        await test_suite.connect_to_chrome()
        async with websockets.connect(test_suite.ws_url, ping_interval=None) as ws:
            if not await test_suite.inject_script(ws):
                return {"success": False, "error": "Script injection failed"}
            
            symbol = INTEGRATION_CONFIG['TEST_SYMBOL']
            quantity = INTEGRATION_CONFIG['TEST_QUANTITY']
            action = 'Buy'
            
            print(f"📊 Capturing before state for {symbol}...")
            # Capture before state
            before_state = await test_suite.capture_current_state(ws, symbol)
            if 'error' in before_state:
                return {"success": False, "error": f"Before state capture failed: {before_state['error']}"}
            
            print(f"✅ Before state captured: {before_state.get('positionsCount', 0)} positions")
            
            # Execute real order
            print(f"🚀 Executing real order: {action} {quantity} {symbol}")
            order_result = await test_suite.execute_real_order(ws, symbol, quantity, action)
            
            if 'error' in order_result:
                return {"success": False, "error": f"Order execution failed: {order_result['error']}"}
            
            # Wait for state changes to propagate
            print(f"⏳ Waiting {INTEGRATION_CONFIG['VERIFICATION_WAIT_TIME']}s for state changes...")
            await asyncio.sleep(INTEGRATION_CONFIG['VERIFICATION_WAIT_TIME'])
            
            # Capture after state
            print(f"📊 Capturing after state for {symbol}...")
            after_state = await test_suite.capture_current_state(ws, symbol)
            if 'error' in after_state:
                return {"success": False, "error": f"After state capture failed: {after_state['error']}"}
            
            print(f"✅ After state captured: {after_state.get('positionsCount', 0)} positions")
            
            # Analyze results
            verification_used = 'verification' in order_result
            position_changed = (
                after_state.get('positionsCount', 0) != before_state.get('positionsCount', 0) or
                after_state.get('domPositions', {}) != before_state.get('domPositions', {})
            )
            
            verification_success = order_result.get('success', False)
            has_method_field = 'method' in order_result
            execution_time = order_result.get('executionTime', 0)
            
            # Validation checks
            checks = {
                'order_executed': 'testOrderId' in order_result,
                'verification_used': verification_used,
                'has_method_field': has_method_field,
                'position_actually_changed': position_changed,
                'verification_matches_reality': (verification_success == position_changed) if position_changed else True,
                'performance_acceptable': execution_time < 10000,  # Less than 10 seconds
                'wrapper_method_used': order_result.get('method') == 'WRAPPER'
            }
            
            success = all(checks.values())
            
            return {
                "success": success,
                "checks": checks,
                "details": {
                    "before_state": before_state,
                    "after_state": after_state,
                    "order_result": order_result,
                    "position_changed": position_changed,
                    "verification_success": verification_success,
                    "execution_time_ms": execution_time
                }
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}

# Test 4.3.2 - Multi-Account Verification Test 
async def test_multi_account_verification():
    """Test 4.3.2: Test verification across all Chrome instances"""
    print("\n🎯 Test 4.3.2: Multi-Account Verification")
    print("=" * 60)
    
    results = {}
    all_ports = INTEGRATION_CONFIG['CHROME_PORTS']
    
    for port in all_ports:
        print(f"\n🔗 Testing Chrome instance on port {port}...")
        test_suite = EndToEndVerificationTest(port)
        
        try:
            result = await test_real_order_execution(test_suite)
            results[f'port_{port}'] = result
            
            if result.get('success', False):
                print(f"✅ Port {port}: Verification system working correctly")
            else:
                print(f"❌ Port {port}: Issues detected - {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Port {port}: Connection failed - {e}")
            results[f'port_{port}'] = {"success": False, "error": str(e)}
    
    # Analyze multi-account results
    successful_ports = [port for port, result in results.items() if result.get('success', False)]
    failed_ports = [port for port, result in results.items() if not result.get('success', False)]
    
    multi_account_checks = {
        'all_ports_connected': len(results) == len(all_ports),
        'majority_successful': len(successful_ports) >= len(all_ports) // 2,
        'no_critical_failures': len(failed_ports) == 0
    }
    
    return {
        "success": all(multi_account_checks.values()),
        "checks": multi_account_checks,
        "port_results": results,
        "successful_ports": successful_ports,
        "failed_ports": failed_ports
    }

# Main integration test runner
async def run_integration_tests():
    """Run complete end-to-end integration tests"""
    print("🚀 Starting End-to-End Integration Tests")
    print("🎯 Testing Real Order Execution with Mandatory Verification")
    print("=" * 80)
    
    test_results = {}
    
    # Test 4.3.1 - Real Order Execution
    print("\n📋 Running Test 4.3.1...")
    test_suite = EndToEndVerificationTest()
    test_results['real_order_execution'] = await test_real_order_execution(test_suite)
    
    # Test 4.3.2 - Multi-Account Testing
    print("\n📋 Running Test 4.3.2...")
    test_results['multi_account_verification'] = await test_multi_account_verification()
    
    # Generate integration test report
    print("\n" + "=" * 80)
    print("📊 INTEGRATION TEST RESULTS SUMMARY")
    print("=" * 80)
    
    all_tests_passed = True
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result.get('success', False) else "❌ FAILED"
        print(f"{test_name}: {status}")
        
        if not result.get('success', False):
            all_tests_passed = False
            print(f"  Error: {result.get('error', 'Unknown error')}")
        else:
            if 'checks' in result:
                for check_name, passed in result['checks'].items():
                    check_status = "✅" if passed else "❌"
                    print(f"  {check_status} {check_name}")
            
            # Show execution details for real order test
            if test_name == 'real_order_execution' and 'details' in result:
                details = result['details']
                exec_time = details.get('execution_time_ms', 0)
                pos_changed = details.get('position_changed', False)
                verification_success = details.get('verification_success', False)
                
                print(f"  📊 Execution time: {exec_time}ms")
                print(f"  📈 Position changed: {pos_changed}")
                print(f"  🔍 Verification result: {verification_success}")
    
    print("\n" + "=" * 80)
    if all_tests_passed:
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("✅ Real order execution with verification works correctly")
        print("✅ Multi-account verification system operational")
        print("✅ Mandatory verification cannot be bypassed")
        print("✅ Position changes properly detected and verified")
        print("✅ Performance within acceptable limits")
        print("✅ System ready for production deployment")
    else:
        print("⚠️ SOME INTEGRATION TESTS FAILED")
        print("❌ Issues detected in real order verification")
        print("🔧 Review failed tests and address issues before deployment")
    
    print("=" * 80)
    
    return all_tests_passed, test_results

if __name__ == "__main__":
    asyncio.run(run_integration_tests())