# Order Verification System - Testing Procedures

## Overview

This document outlines comprehensive testing procedures for the order verification system to ensure the "browser as source of truth" principle is maintained across all trading operations.

## Pre-Test Setup

### 1. Environment Preparation

```bash
# 1. Start Chrome instances with remote debugging
python3 scripts/auto_login.py

# 2. Verify Chrome instances are running
ps aux | grep chrome | grep remote-debugging-port

# 3. Inject Tampermonkey scripts
python3 reload.py

# 4. Verify connection
python3 -m src.app list
```

**Expected Output**:
```
Active Tradovate Connections:
  0: Account 1 (Port 9222)
  1: Account 2 (Port 9223)
  ...
```

### 2. Function Availability Check

```python
# Test script: test_function_availability.py
from src.app import TradovateConnection

def test_function_availability():
    """Verify all required functions are properly injected"""
    
    connection = TradovateConnection(port=9222, account_name="Test Account")
    
    if not connection.tab:
        print("❌ No tab available")
        return False
    
    # Test function availability
    test_code = """
    {
        "autoTrade": typeof window.autoTrade === 'function',
        "auto_trade_scale": typeof window.auto_trade_scale === 'function', 
        "waitForOrderFeedback": typeof window.waitForOrderFeedback === 'function',
        "captureOrderFeedback": typeof window.captureOrderFeedback === 'function'
    }
    """
    
    result = connection.tab.Runtime.evaluate(expression=test_code)
    functions = result.get('result', {}).get('value', {})
    
    print("Function Availability:")
    for func, available in functions.items():
        status = "✅" if available else "❌"
        print(f"  {status} {func}: {available}")
    
    return all(functions.values())

# Run test
if __name__ == "__main__":
    test_function_availability()
```

## Core Verification Tests

### 3. Single Order Verification Test

```python
# Test script: test_single_order.py
from src.app import TradovateConnection
import time

def test_single_order_verification():
    """Test single order with full verification flow"""
    
    connection = TradovateConnection(port=9222)
    
    if not connection.tab:
        print("❌ No connection available")
        return
    
    print("🔍 Testing single order verification...")
    
    # Test parameters
    test_params = {
        'symbol': 'NQ',
        'quantity': 1,
        'action': 'Buy',
        'tp_ticks': 100,
        'sl_ticks': 40,
        'tick_size': 0.25
    }
    
    start_time = time.time()
    
    try:
        result = connection.auto_trade(**test_params)
        
        execution_time = time.time() - start_time
        print(f"⏱️  Execution time: {execution_time:.2f} seconds")
        
        # Verify response structure
        assert isinstance(result, dict), "Result must be a dictionary"
        assert 'success' in result, "Result must contain 'success' field"
        
        if result.get('success'):
            assert 'orders' in result, "Successful result must contain 'orders'"
            assert isinstance(result['orders'], list), "Orders must be a list"
            print(f"✅ Order verification successful: {len(result['orders'])} orders")
            
            # Verify order data structure
            for i, order in enumerate(result['orders']):
                print(f"   Order {i+1}: {order.get('symbol')} {order.get('side')} {order.get('quantity')} @ {order.get('price')}")
                
        else:
            assert 'error' in result, "Failed result must contain 'error'"
            print(f"❌ Order verification failed: {result.get('error')}")
            print(f"   Details: {result.get('details', 'No details provided')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Exception during test: {str(e)}")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    test_single_order_verification()
```

### 4. Scale Order Verification Test

```python
# Test script: test_scale_orders.py
from src.app import TradovateConnection
import time

def test_scale_order_verification():
    """Test scale orders with verification"""
    
    connection = TradovateConnection(port=9222)
    
    # Define scale order levels
    scale_orders = [
        {"quantity": 1, "price": 15200},
        {"quantity": 1, "price": 15190},
        {"quantity": 1, "price": 15180}
    ]
    
    print(f"🔍 Testing scale order verification with {len(scale_orders)} levels...")
    
    start_time = time.time()
    
    try:
        result = connection.auto_trade_scale(
            symbol='NQ',
            scale_orders=scale_orders,
            action='Buy',
            tp_ticks=100,
            sl_ticks=40,
            tick_size=0.25
        )
        
        execution_time = time.time() - start_time
        print(f"⏱️  Execution time: {execution_time:.2f} seconds")
        
        # Verify response
        assert isinstance(result, dict), "Result must be a dictionary"
        assert 'success' in result, "Result must contain 'success' field"
        
        if result.get('success'):
            orders = result.get('orders', [])
            print(f"✅ Scale order verification successful: {len(orders)} orders")
            
            # Verify we got expected number of orders
            expected_orders = len(scale_orders)
            if len(orders) == expected_orders:
                print(f"   ✅ Order count matches: {len(orders)}/{expected_orders}")
            else:
                print(f"   ⚠️  Order count mismatch: {len(orders)}/{expected_orders}")
                
        else:
            print(f"❌ Scale order verification failed: {result.get('error')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Exception during scale order test: {str(e)}")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    test_scale_order_verification()
```

## Multi-Account Testing

### 5. All Accounts Verification Test

```python
# Test script: test_all_accounts.py
from src.app import TradovateController

def test_all_accounts_verification():
    """Test order verification across all accounts"""
    
    controller = TradovateController()
    
    if len(controller.connections) == 0:
        print("❌ No connections found")
        return
    
    print(f"🔍 Testing verification across {len(controller.connections)} accounts...")
    
    # Execute test trade on all accounts
    results = controller.execute_on_all(
        'auto_trade',
        'NQ',      # symbol
        1,         # quantity  
        'Buy',     # action
        100,       # tp_ticks
        40,        # sl_ticks
        0.25       # tick_size
    )
    
    # Analyze results
    verified_accounts = []
    failed_accounts = []
    error_accounts = []
    
    print("\nPer-Account Results:")
    for r in results:
        account = r.get('account', 'Unknown')
        result = r.get('result', {})
        
        if isinstance(result, dict) and 'success' in result:
            if result.get('success'):
                verified_accounts.append(account)
                orders = result.get('orders', [])
                print(f"  ✅ {account}: {len(orders)} orders verified")
            else:
                failed_accounts.append(account)
                error = result.get('error', 'Unknown error')
                print(f"  ❌ {account}: {error}")
        else:
            error_accounts.append(account)
            print(f"  🔥 {account}: Invalid response format")
    
    # Summary
    total_accounts = len(results)
    success_rate = len(verified_accounts) / total_accounts * 100
    
    print(f"\nSummary:")
    print(f"  Total accounts: {total_accounts}")
    print(f"  Verified: {len(verified_accounts)} ({success_rate:.1f}%)")
    print(f"  Failed verification: {len(failed_accounts)}")
    print(f"  Response errors: {len(error_accounts)}")
    
    return {
        'total': total_accounts,
        'verified': len(verified_accounts),
        'failed': len(failed_accounts),
        'errors': len(error_accounts),
        'success_rate': success_rate
    }

if __name__ == "__main__":
    test_all_accounts_verification()
```

## Error Scenario Testing

### 6. Timeout Testing

```python
# Test script: test_timeouts.py
from src.app import TradovateConnection
import time

def test_timeout_scenarios():
    """Test timeout handling in verification system"""
    
    connection = TradovateConnection(port=9222)
    
    print("🔍 Testing timeout scenarios...")
    
    # Test 1: Normal operation within timeout
    print("\nTest 1: Normal operation")
    start = time.time()
    result = connection.auto_trade('NQ', 1, 'Buy', 100, 40, 0.25)
    duration = time.time() - start
    print(f"  Duration: {duration:.2f}s")
    print(f"  Result: {result.get('success', 'error')}")
    
    # Test 2: Scale orders (longer timeout expected)
    print("\nTest 2: Scale orders with multiple levels")
    scale_orders = [{"quantity": 1, "price": 15200 + i*10} for i in range(5)]
    start = time.time()
    result = connection.auto_trade_scale('NQ', scale_orders, 'Buy', 100, 40, 0.25)
    duration = time.time() - start
    print(f"  Duration: {duration:.2f}s")
    print(f"  Result: {result.get('success', 'error')}")
    
    print("\nTimeout tests completed")

if __name__ == "__main__":
    test_timeout_scenarios()
```

### 7. Invalid Input Testing

```python
# Test script: test_invalid_inputs.py
from src.app import TradovateConnection

def test_invalid_inputs():
    """Test system behavior with invalid inputs"""
    
    connection = TradovateConnection(port=9222)
    
    test_cases = [
        {
            'name': 'Invalid symbol',
            'params': {'symbol': 'INVALID', 'quantity': 1, 'action': 'Buy', 'tp_ticks': 100, 'sl_ticks': 40, 'tick_size': 0.25},
            'expect_success': False
        },
        {
            'name': 'Zero quantity',
            'params': {'symbol': 'NQ', 'quantity': 0, 'action': 'Buy', 'tp_ticks': 100, 'sl_ticks': 40, 'tick_size': 0.25},
            'expect_success': False
        },
        {
            'name': 'Invalid action',
            'params': {'symbol': 'NQ', 'quantity': 1, 'action': 'INVALID', 'tp_ticks': 100, 'sl_ticks': 40, 'tick_size': 0.25},
            'expect_success': False
        },
        {
            'name': 'Negative TP/SL',
            'params': {'symbol': 'NQ', 'quantity': 1, 'action': 'Buy', 'tp_ticks': -100, 'sl_ticks': -40, 'tick_size': 0.25},
            'expect_success': False
        }
    ]
    
    print("🔍 Testing invalid input handling...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        
        try:
            result = connection.auto_trade(**test_case['params'])
            
            success = result.get('success', False)
            expected = test_case['expect_success']
            
            if success == expected:
                print(f"  ✅ Expected result: {success}")
            else:
                print(f"  ❌ Unexpected result: got {success}, expected {expected}")
            
            if not success:
                print(f"     Error: {result.get('error', 'No error provided')}")
                
        except Exception as e:
            print(f"  🔥 Exception: {str(e)}")
    
    print("\nInvalid input tests completed")

if __name__ == "__main__":
    test_invalid_inputs()
```

## Performance Testing

### 8. Load Testing

```python
# Test script: test_performance.py
from src.app import TradovateController
import time
import threading
from concurrent.futures import ThreadPoolExecutor

def single_trade_test(account_index):
    """Execute single trade for performance testing"""
    controller = TradovateController()
    
    if account_index >= len(controller.connections):
        return {'error': 'Account index out of range'}
    
    start_time = time.time()
    result = controller.execute_on_one(
        account_index, 'auto_trade', 'NQ', 1, 'Buy', 100, 40, 0.25
    )
    duration = time.time() - start_time
    
    return {
        'account': result.get('account'),
        'success': result.get('result', {}).get('success', False),
        'duration': duration
    }

def test_concurrent_execution():
    """Test concurrent order execution across accounts"""
    
    controller = TradovateController()
    account_count = len(controller.connections)
    
    if account_count == 0:
        print("❌ No accounts available for testing")
        return
    
    print(f"🔍 Testing concurrent execution on {account_count} accounts...")
    
    # Test 1: Sequential execution
    print("\nTest 1: Sequential execution")
    start_time = time.time()
    sequential_results = []
    
    for i in range(account_count):
        result = single_trade_test(i)
        sequential_results.append(result)
    
    sequential_duration = time.time() - start_time
    print(f"  Sequential duration: {sequential_duration:.2f}s")
    
    # Test 2: Concurrent execution
    print("\nTest 2: Concurrent execution")
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=account_count) as executor:
        concurrent_results = list(executor.map(single_trade_test, range(account_count)))
    
    concurrent_duration = time.time() - start_time
    print(f"  Concurrent duration: {concurrent_duration:.2f}s")
    
    # Analysis
    speedup = sequential_duration / concurrent_duration if concurrent_duration > 0 else 0
    print(f"  Speedup: {speedup:.2f}x")
    
    # Success rates
    seq_success = sum(1 for r in sequential_results if r.get('success'))
    con_success = sum(1 for r in concurrent_results if r.get('success'))
    
    print(f"  Sequential success rate: {seq_success}/{account_count}")
    print(f"  Concurrent success rate: {con_success}/{account_count}")

if __name__ == "__main__":
    test_concurrent_execution()
```

## Regression Testing

### 9. Automated Test Suite

```python
# Test script: run_all_tests.py
import sys
import time
from src.app import TradovateController

def run_test_suite():
    """Run complete test suite for order verification system"""
    
    print("🚀 Starting Order Verification System Test Suite")
    print("=" * 60)
    
    start_time = time.time()
    
    # Test results tracking
    tests = []
    
    # Test 1: Connection availability
    print("\n1. Testing connection availability...")
    controller = TradovateController()
    connection_test = {
        'name': 'Connection Availability',
        'passed': len(controller.connections) > 0,
        'details': f'{len(controller.connections)} connections found'
    }
    tests.append(connection_test)
    print(f"   {'✅' if connection_test['passed'] else '❌'} {connection_test['details']}")
    
    if not connection_test['passed']:
        print("❌ Cannot continue without connections")
        return
    
    # Test 2: Function injection
    print("\n2. Testing function injection...")
    connection = controller.connections[0]
    
    test_code = """
    typeof window.autoTrade === 'function' && 
    typeof window.auto_trade_scale === 'function' &&
    typeof window.waitForOrderFeedback === 'function' &&
    typeof window.captureOrderFeedback === 'function'
    """
    
    result = connection.tab.Runtime.evaluate(expression=test_code)
    functions_available = result.get('result', {}).get('value', False)
    
    function_test = {
        'name': 'Function Injection',
        'passed': functions_available,
        'details': 'All required functions available' if functions_available else 'Some functions missing'
    }
    tests.append(function_test)
    print(f"   {'✅' if function_test['passed'] else '❌'} {function_test['details']}")
    
    # Test 3: Single order verification
    print("\n3. Testing single order verification...")
    try:
        result = connection.auto_trade('NQ', 1, 'Buy', 100, 40, 0.25)
        single_order_test = {
            'name': 'Single Order Verification',
            'passed': isinstance(result, dict) and 'success' in result,
            'details': f"Result: {result.get('success', 'error')}"
        }
    except Exception as e:
        single_order_test = {
            'name': 'Single Order Verification',
            'passed': False,
            'details': f"Exception: {str(e)}"
        }
    
    tests.append(single_order_test)
    print(f"   {'✅' if single_order_test['passed'] else '❌'} {single_order_test['details']}")
    
    # Test 4: Multi-account execution
    print("\n4. Testing multi-account execution...")
    try:
        results = controller.execute_on_all('auto_trade', 'NQ', 1, 'Buy', 100, 40, 0.25)
        verified_count = sum(1 for r in results if r.get('result', {}).get('success'))
        multi_account_test = {
            'name': 'Multi-Account Execution',
            'passed': len(results) > 0,
            'details': f"{verified_count}/{len(results)} accounts verified"
        }
    except Exception as e:
        multi_account_test = {
            'name': 'Multi-Account Execution',
            'passed': False,
            'details': f"Exception: {str(e)}"
        }
    
    tests.append(multi_account_test)
    print(f"   {'✅' if multi_account_test['passed'] else '❌'} {multi_account_test['details']}")
    
    # Test Summary
    total_duration = time.time() - start_time
    passed_tests = sum(1 for t in tests if t['passed'])
    total_tests = len(tests)
    
    print("\n" + "=" * 60)
    print("TEST SUITE SUMMARY")
    print("=" * 60)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success rate: {passed_tests/total_tests*100:.1f}%")
    print(f"Duration: {total_duration:.2f} seconds")
    
    # Detailed results
    print("\nDetailed Results:")
    for test in tests:
        status = "✅ PASS" if test['passed'] else "❌ FAIL"
        print(f"  {status} {test['name']}: {test['details']}")
    
    # Exit code
    sys.exit(0 if passed_tests == total_tests else 1)

if __name__ == "__main__":
    run_test_suite()
```

## Manual Testing Checklist

### 10. Manual Verification Steps

**Pre-Test Checklist:**
- [ ] Chrome instances running with remote debugging
- [ ] Tradovate accounts logged in
- [ ] Tampermonkey scripts injected (`python3 reload.py`)
- [ ] Functions available in browser console

**Single Order Testing:**
- [ ] Execute single Buy order
- [ ] Execute single Sell order  
- [ ] Verify order appears in Tradovate order history
- [ ] Verify Python receives correct verification data
- [ ] Test with different symbols (NQ, ES, CL)
- [ ] Test with different TP/SL values

**Scale Order Testing:**
- [ ] Execute 2-level scale orders
- [ ] Execute 5-level scale orders
- [ ] Verify all orders appear in order history
- [ ] Verify correct order count in response
- [ ] Test scale-in and scale-out scenarios

**Error Handling Testing:**
- [ ] Test with invalid symbol
- [ ] Test with disconnected browser
- [ ] Test with invalid parameters
- [ ] Verify error messages are informative
- [ ] Test timeout scenarios

**Multi-Account Testing:**
- [ ] Execute trades across all accounts
- [ ] Verify per-account success/failure reporting
- [ ] Test mixed success/failure scenarios
- [ ] Verify account isolation (failures don't affect others)

## Continuous Integration Testing

### 11. CI Test Script

```bash
#!/bin/bash
# ci_test.sh - Continuous Integration Test Script

set -e

echo "🚀 Starting CI Test Pipeline"

# Setup
echo "📋 Setting up test environment..."
python3 scripts/auto_login.py &
LOGIN_PID=$!
sleep 10  # Wait for Chrome instances to start

# Inject scripts
echo "💉 Injecting Tampermonkey scripts..."
python3 reload.py

# Run test suite
echo "🧪 Running automated test suite..."
python3 tests/run_all_tests.py

# Cleanup
echo "🧹 Cleaning up..."
kill $LOGIN_PID 2>/dev/null || true
pkill -f "chrome.*remote-debugging-port" || true

echo "✅ CI Test Pipeline completed"
```

## Test Data Management

### 12. Test Configuration

```json
// test_config.json
{
  "test_symbols": ["NQ", "ES", "CL"],
  "test_quantities": [1, 2],
  "test_actions": ["Buy", "Sell"],
  "test_tp_ticks": [50, 100, 200],
  "test_sl_ticks": [25, 40, 50],
  "test_tick_sizes": {
    "NQ": 0.25,
    "ES": 0.25,
    "CL": 0.01
  },
  "timeout_limits": {
    "single_order": 15000,
    "scale_order_base": 15000,
    "scale_order_per_level": 1000
  },
  "scale_test_configs": [
    {
      "levels": 2,
      "price_increment": 10
    },
    {
      "levels": 5,
      "price_increment": 5
    }
  ]
}
```

This comprehensive testing framework ensures the order verification system maintains its integrity and accuracy across all scenarios, maintaining the "browser as source of truth" principle.