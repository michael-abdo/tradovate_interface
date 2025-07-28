#!/usr/bin/env python3
"""
Comprehensive test suite for Enhanced DOM Order Submission
Tests the new implementation that clicks price cells before submitting orders
"""

import asyncio
import websockets
import json
import time
import sys

class EnhancedDOMTester:
    def __init__(self):
        self.ws_urls = {
            'Account 1': 'ws://localhost:9223/devtools/page/83AE0CC4CF8F03548C32FA104E9C4A5B',
            'Account 2': 'ws://localhost:9224/devtools/page/B6DB6FA6F8779994E5D00608611926C6',
            'Account 3': 'ws://localhost:9225/devtools/page/A8D9E60638F3CCEC09E0205C23F32809'
        }
        self.test_results = []
        
    async def send_command(self, ws, method, params=None):
        """Send Chrome DevTools Protocol command"""
        msg_id = int(time.time() * 1000)
        message = {
            "id": msg_id,
            "method": method,
            "params": params or {}
        }
        
        await ws.send(json.dumps(message))
        
        # Get response
        while True:
            response = await ws.recv()
            data = json.loads(response)
            if data.get("id") == msg_id:
                return data
                
    async def evaluate_js(self, ws, expression, await_promise=False):
        """Execute JavaScript and return result"""
        params = {
            "expression": expression,
            "returnByValue": True
        }
        if await_promise:
            params["awaitPromise"] = True
            
        result = await self.send_command(ws, "Runtime.evaluate", params)
        
        if "result" in result and "result" in result["result"]:
            return result["result"]["result"].get("value")
        return None
        
    async def inject_autoorder_script(self, ws):
        """Inject the updated autoOrder script"""
        print("  💉 Injecting updated autoOrder script...")
        
        try:
            # First check if file exists
            import os
            if not os.path.exists('/Users/Mike/trading/scripts/tampermonkey/autoOrder.user.js'):
                print("  ❌ autoOrder.user.js file not found!")
                return False
                
            with open('/Users/Mike/trading/scripts/tampermonkey/autoOrder.user.js', 'r') as f:
                script_content = f.read()
                print(f"  📄 Loaded script ({len(script_content)} characters)")
                
            # Remove Tampermonkey headers
            lines = script_content.split('\n')
            cleaned_lines = []
            in_header = False
            
            for line in lines:
                if line.strip() == '// ==UserScript==':
                    in_header = True
                elif line.strip() == '// ==/UserScript==':
                    in_header = False
                    continue
                elif not in_header:
                    cleaned_lines.append(line)
                    
            cleaned_script = '\n'.join(cleaned_lines)
            
            # Inject script
            await self.evaluate_js(ws, cleaned_script)
            
            # Verify functions exist
            check_result = await self.evaluate_js(ws, """
                JSON.stringify({
                    autoOrder: typeof window.autoOrder,
                    submitOrderWithDOM: typeof window.submitOrderWithDOM,
                    captureOrdersState: typeof window.captureOrdersState,
                    compareOrderStates: typeof window.compareOrderStates
                })
            """)
            
            if check_result:
                functions = json.loads(check_result)
                print(f"  ✅ Functions loaded: {functions}")
                return all(v == 'function' for v in functions.values())
                
        except Exception as e:
            print(f"  ❌ Script injection failed: {e}")
            return False
            
    async def test_dom_visibility(self, ws):
        """Test 1: Verify DOM trading module is visible"""
        print("\n🧪 Test 1: DOM Module Visibility")
        
        result = await self.evaluate_js(ws, """
            const domModule = document.querySelector('.module.module-dom');
            const orderTicket = document.querySelector('.module.order-ticket');
            
            JSON.stringify({
                domModuleExists: !!domModule,
                domModuleVisible: domModule ? domModule.offsetParent !== null : false,
                orderTicketExists: !!orderTicket,
                orderTicketVisible: orderTicket ? orderTicket.offsetParent !== null : false,
                url: window.location.href
            })
        """)
        
        if result:
            data = json.loads(result)
            print(f"  DOM Module: Exists={data['domModuleExists']}, Visible={data['domModuleVisible']}")
            print(f"  Order Ticket: Exists={data['orderTicketExists']}, Visible={data['orderTicketVisible']}")
            
            test_passed = data['domModuleExists'] and data['domModuleVisible']
            self.test_results.append(('DOM Visibility', test_passed))
            return test_passed
            
        return False
        
    async def test_price_cell_detection(self, ws):
        """Test 2: Verify price cells can be found"""
        print("\n🧪 Test 2: Price Cell Detection")
        
        result = await self.evaluate_js(ws, """
            const cellSelectors = [
                '.dom-cell-container-bid',
                '.dom-cell-container-ask',
                '.dom-price-cell',
                '[class*="dom-cell"]',
                '.dom-bid',
                '.dom-ask'
            ];
            
            const results = {};
            let totalCells = 0;
            
            for (const selector of cellSelectors) {
                const cells = document.querySelectorAll(selector);
                if (cells.length > 0) {
                    results[selector] = cells.length;
                    totalCells += cells.length;
                }
            }
            
            JSON.stringify({
                selectors: results,
                totalCells: totalCells,
                hasBidCells: Object.keys(results).some(s => s.includes('bid')),
                hasAskCells: Object.keys(results).some(s => s.includes('ask'))
            })
        """)
        
        if result:
            data = json.loads(result)
            print(f"  Total price cells found: {data['totalCells']}")
            print(f"  Has bid cells: {data['hasBidCells']}")
            print(f"  Has ask cells: {data['hasAskCells']}")
            
            for selector, count in data['selectors'].items():
                print(f"    {selector}: {count} cells")
                
            test_passed = data['totalCells'] > 0
            self.test_results.append(('Price Cell Detection', test_passed))
            return test_passed
            
        return False
        
    async def test_order_submission_flow(self, ws):
        """Test 3: Full order submission flow with verification"""
        print("\n🧪 Test 3: Order Submission Flow")
        
        # Capture before state
        print("  📊 Capturing before state...")
        before_state = await self.evaluate_js(ws, """
            window.captureOrdersState('NQU5').then(state => JSON.stringify(state))
        """, await_promise=True)
        
        if before_state:
            before = json.loads(before_state)
            print(f"  Before: {before.get('ordersCount', 0)} orders, {before.get('positionsCount', 0)} positions")
        
        # Execute order with enhanced DOM submission
        print("  🚀 Executing order with DOM submission...")
        exec_result = await self.evaluate_js(ws, """
            (async () => {
                try {
                    const result = await window.autoOrder('NQ', 1, 'Buy', 20, 10, 0.25);
                    return JSON.stringify({
                        success: !!result,
                        result: result
                    });
                } catch (error) {
                    return JSON.stringify({
                        success: false,
                        error: error.message
                    });
                }
            })()
        """, await_promise=True)
        
        if exec_result:
            result = json.loads(exec_result)
            print(f"  Execution result: {result}")
            
        # Wait for order processing
        print("  ⏳ Waiting 5 seconds for order processing...")
        await asyncio.sleep(5)
        
        # Capture after state
        print("  📊 Capturing after state...")
        after_state = await self.evaluate_js(ws, """
            window.captureOrdersState('NQU5').then(state => JSON.stringify(state))
        """, await_promise=True)
        
        if after_state:
            after = json.loads(after_state)
            print(f"  After: {after.get('ordersCount', 0)} orders, {after.get('positionsCount', 0)} positions")
            
        # Compare states
        print("  🔍 Comparing states...")
        if before_state and after_state:
            comparison = await self.evaluate_js(ws, f"""
                (() => {{
                    const before = {before_state};
                    const after = {after_state};
                    const comparison = window.compareOrderStates(before, after, 'NQU5');
                    return JSON.stringify(comparison);
                }})()
            """)
            
            if comparison:
                comp_result = json.loads(comparison)
                print(f"\n  📊 VERIFICATION RESULTS:")
                print(f"  - Execution Detected: {comp_result.get('executionDetected', False)}")
                print(f"  - Confidence: {comp_result.get('validation', {}).get('confidence', 'NONE')}")
                print(f"  - Position Changes: {comp_result.get('positionChanges', {}).get('detected', False)}")
                print(f"  - Order Changes: {comp_result.get('orderChanges', {}).get('detected', False)}")
                
                test_passed = comp_result.get('executionDetected', False)
                self.test_results.append(('Order Execution', test_passed))
                return test_passed
                
        self.test_results.append(('Order Execution', False))
        return False
        
    async def test_single_account(self, account_name, ws_url):
        """Run all tests on a single account"""
        print(f"\n{'='*60}")
        print(f"Testing {account_name}")
        print(f"{'='*60}")
        
        try:
            async with websockets.connect(ws_url, ping_interval=None) as ws:
                # Inject script
                if not await self.inject_autoorder_script(ws):
                    print(f"❌ Failed to inject script for {account_name}")
                    return False
                    
                # Run tests
                await self.test_dom_visibility(ws)
                await self.test_price_cell_detection(ws)
                await self.test_order_submission_flow(ws)
                
                return True
                
        except Exception as e:
            print(f"❌ Error testing {account_name}: {e}")
            return False
            
    async def run_all_tests(self):
        """Run tests on all accounts"""
        print("🚀 Enhanced DOM Order Submission Test Suite")
        print("=" * 60)
        
        # Test first account only for now
        account_name = 'Account 1'
        ws_url = self.ws_urls[account_name]
        
        try:
            # Set a timeout for the entire test
            await asyncio.wait_for(
                self.test_single_account(account_name, ws_url),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            print(f"\n❌ Test timed out after 30 seconds")
            self.test_results.append(('Overall Test', False))
        
        # Print summary
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}")
        
        passed = sum(1 for _, result in self.test_results if result)
        total = len(self.test_results)
        
        for test_name, result in self.test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")
            
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All tests passed! Enhanced DOM submission is working correctly.")
        else:
            print("\n⚠️ Some tests failed. Check the implementation.")
            
        return passed == total

async def main():
    tester = EnhancedDOMTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())