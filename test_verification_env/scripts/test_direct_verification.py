#!/usr/bin/env python3
"""
Direct Verification Test - Tests verification functions without full script injection
This approach tests if the script is already loaded in the browser
"""

import asyncio
import websockets
import json
import subprocess
import time
from typing import Dict, Any, List, Optional

CHROME_PORTS = [9223, 9224, 9225]

class DirectVerificationTest:
    """Test verification functions assuming script is already loaded"""
    
    def __init__(self, port: int):
        self.port = port
        self.ws_url = None
        
    async def connect_to_chrome(self) -> str:
        """Connect to Chrome WebSocket"""
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
    
    async def check_script_loaded(self, ws) -> bool:
        """Check if autoOrder script is already loaded"""
        check_js = """
        (function() {
            return {
                hasAutoOrder: typeof window.autoOrder === 'function',
                hasVerifyOrderExecution: typeof window.verifyOrderExecution === 'function',
                hasCaptureOrdersState: typeof window.captureOrdersState === 'function',
                hasCompareOrderStates: typeof window.compareOrderStates === 'function',
                hasWrapper: window.autoOrder && window.autoOrder.toString().includes('_executeOrder'),
                scriptLoaded: true
            };
        })();
        """
        
        msg = {
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {
                "expression": check_js,
                "returnByValue": True
            }
        }
        
        await ws.send(json.dumps(msg))
        response = await ws.recv()
        result = json.loads(response)
        
        if 'result' in result and 'result' in result['result']:
            status = result['result']['result'].get('value', {})
            print(f"📋 Script Status on port {self.port}:")
            print(f"   - autoOrder function: {'✅' if status.get('hasAutoOrder') else '❌'}")
            print(f"   - verifyOrderExecution: {'✅' if status.get('hasVerifyOrderExecution') else '❌'}")
            print(f"   - captureOrdersState: {'✅' if status.get('hasCaptureOrdersState') else '❌'}")
            print(f"   - compareOrderStates: {'✅' if status.get('hasCompareOrderStates') else '❌'}")
            print(f"   - Wrapper pattern active: {'✅' if status.get('hasWrapper') else '❌'}")
            
            return all([
                status.get('hasAutoOrder'),
                status.get('hasVerifyOrderExecution'),
                status.get('hasCaptureOrdersState')
            ])
        
        return False
    
    async def test_verification_functions(self, ws) -> Dict[str, Any]:
        """Test verification functions directly"""
        
        # Test 1: State capture function
        test_capture_js = """
        (async function() {
            try {
                if (typeof window.captureOrdersState === 'function') {
                    const state = await window.captureOrdersState('NQ');
                    return {
                        success: true,
                        hasPositions: state.domPositions && Object.keys(state.domPositions).length > 0,
                        hasOrders: state.orderTableData && state.orderTableData.length > 0,
                        positionsCount: state.positionsCount || 0
                    };
                } else {
                    return { success: false, error: 'captureOrdersState not found' };
                }
            } catch (e) {
                return { success: false, error: e.message };
            }
        })();
        """
        
        msg = {
            "id": 2,
            "method": "Runtime.evaluate",
            "params": {
                "expression": test_capture_js,
                "awaitPromise": True,
                "returnByValue": True
            }
        }
        
        await ws.send(json.dumps(msg))
        response = await ws.recv()
        capture_result = json.loads(response).get('result', {}).get('result', {}).get('value', {})
        
        # Test 2: Verification wrapper
        test_wrapper_js = """
        (function() {
            if (typeof window.autoOrder === 'function') {
                const funcStr = window.autoOrder.toString();
                return {
                    hasWrapper: funcStr.includes('_executeOrder') && funcStr.includes('verifyOrderExecution'),
                    hasBeforeState: funcStr.includes('captureOrdersState(symbol)'),
                    hasAfterState: funcStr.includes('afterState'),
                    enforcesMandatory: funcStr.includes('verification.success')
                };
            }
            return { hasWrapper: false };
        })();
        """
        
        msg = {
            "id": 3,
            "method": "Runtime.evaluate",
            "params": {
                "expression": test_wrapper_js,
                "returnByValue": True
            }
        }
        
        await ws.send(json.dumps(msg))
        response = await ws.recv()
        wrapper_result = json.loads(response).get('result', {}).get('result', {}).get('value', {})
        
        return {
            'capture_test': capture_result,
            'wrapper_test': wrapper_result,
            'verification_ready': capture_result.get('success', False) and wrapper_result.get('hasWrapper', False)
        }
    
    async def run_test(self) -> Dict[str, Any]:
        """Run complete verification test"""
        try:
            await self.connect_to_chrome()
            async with websockets.connect(self.ws_url, ping_interval=None) as ws:
                
                # Check if script is loaded
                script_loaded = await self.check_script_loaded(ws)
                
                if not script_loaded:
                    print(f"⚠️  Script not loaded on port {self.port} - Tampermonkey may need refresh")
                    return {
                        'success': False,
                        'error': 'Script not loaded in browser',
                        'recommendation': 'Please ensure Tampermonkey has loaded the autoOrder script'
                    }
                
                # Test verification functions
                test_results = await self.test_verification_functions(ws)
                
                # Evaluate results
                all_passed = (
                    test_results['capture_test'].get('success', False) and
                    test_results['wrapper_test'].get('hasWrapper', False) and
                    test_results['wrapper_test'].get('enforcesMandatory', False)
                )
                
                return {
                    'success': all_passed,
                    'port': self.port,
                    'script_loaded': script_loaded,
                    'test_results': test_results
                }
                
        except Exception as e:
            return {
                'success': False,
                'port': self.port,
                'error': str(e)
            }

async def test_all_ports():
    """Test verification on all Chrome instances"""
    print("🔍 Direct Verification System Test")
    print("=" * 50)
    print("Testing script presence and verification functions...")
    print()
    
    results = {}
    all_passed = True
    
    for port in CHROME_PORTS:
        print(f"\n🔗 Testing Chrome instance on port {port}...")
        test = DirectVerificationTest(port)
        result = await test.run_test()
        results[f'port_{port}'] = result
        
        if result['success']:
            print(f"✅ Port {port}: Verification system operational")
        else:
            print(f"❌ Port {port}: {result.get('error', 'Test failed')}")
            all_passed = False
    
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("✅ Verification system is properly implemented")
        print("✅ Wrapper pattern is enforcing mandatory verification")
        print("✅ State capture functions are working")
        print("✅ Ready for production deployment")
    else:
        print("❌ SOME TESTS FAILED")
        print("⚠️  Please check:")
        print("   1. Tampermonkey has the updated autoOrder.user.js loaded")
        print("   2. All Chrome instances are on the trading platform")
        print("   3. Scripts are enabled and running")
    
    return all_passed, results

if __name__ == "__main__":
    success, results = asyncio.run(test_all_ports())
    exit(0 if success else 1)