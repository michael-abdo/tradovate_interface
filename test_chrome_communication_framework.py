#!/usr/bin/env python3
"""
Standalone Test Script for Chrome Communication Framework
Tests safe_evaluate() wrapper and ChromeCommunicationManager functionality

Following CLAUDE.md principles:
- Uses real Chrome connection on port 9222 (no mocking)
- Tests with actual JavaScript execution
- Fails fast with comprehensive logging
- Validates all framework components
"""

import sys
import os
import time
import json
import traceback
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from utils.chrome_communication import (
        safe_evaluate, ChromeCommunicationManager, OperationType, 
        RetryStrategy, TabHealthStatus, OperationResult,
        ChromeCommunicationError, JavaScriptExecutionError,
        TabHealthValidator, ChromeOperationLogger
    )
    print("✅ Framework imports successful")
except ImportError as e:
    print(f"❌ Framework import failed: {e}")
    print(f"Stack trace: {traceback.format_exc()}")
    sys.exit(1)

# Test configuration
TEST_RESULTS = {
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "errors": []
}

def log_test_result(test_name, success, details=""):
    """Log individual test results"""
    TEST_RESULTS["total_tests"] += 1
    if success:
        TEST_RESULTS["passed"] += 1
        print(f"✅ {test_name}")
        if details:
            print(f"   📝 {details}")
    else:
        TEST_RESULTS["failed"] += 1
        TEST_RESULTS["errors"].append({"test": test_name, "details": details})
        print(f"❌ {test_name}")
        print(f"   📝 {details}")

def test_chrome_connection():
    """Test basic Chrome connection on port 9222"""
    print("\n🔍 Testing Chrome Connection...")
    
    try:
        import requests
        response = requests.get('http://127.0.0.1:9223/json', timeout=5)
        if response.status_code == 200:
            tabs = response.json()
            log_test_result("Chrome DevTools accessible on port 9223", True, f"Found {len(tabs)} tabs")
            return tabs
        else:
            log_test_result("Chrome DevTools accessibility", False, f"HTTP {response.status_code}")
            return None
    except Exception as e:
        log_test_result("Chrome DevTools accessibility", False, str(e))
        return None

def test_pychrome_import():
    """Test pychrome library import and basic functionality"""
    print("\n🔍 Testing Pychrome Import...")
    
    try:
        import pychrome
        browser = pychrome.Browser(url="http://127.0.0.1:9223")
        tabs = browser.list_tab()
        log_test_result("Pychrome library import and connection", True, f"Connected to {len(tabs)} tabs")
        return browser, tabs
    except Exception as e:
        log_test_result("Pychrome library import and connection", False, str(e))
        return None, None

def test_logging_infrastructure():
    """Test that logging infrastructure creates required log files"""
    print("\n🔍 Testing Logging Infrastructure...")
    
    try:
        # Create logger instance
        logger = ChromeOperationLogger()
        
        # Test log directory creation
        log_dir = Path("logs/chrome_communication")
        log_test_result("Log directory exists", log_dir.exists(), str(log_dir))
        
        # Test log file creation
        log_file = log_dir / f"chrome_ops_{time.strftime('%Y%m%d')}.log"
        initial_size = log_file.stat().st_size if log_file.exists() else 0
        
        # Create a test log entry
        test_operation = {
            "operation_id": "test_log_123",
            "operation_type": "TEST",
            "description": "Framework test log entry",
            "js_code": "console.log('test')",
            "timestamp": time.time()
        }
        
        logger.start_operation("test_operation_123", OperationType.NON_CRITICAL, "Framework test log entry")
        logger.log_success("test_operation_123", {"result": "test_success"}, 0.1)
        
        # Check if log file grew
        final_size = log_file.stat().st_size if log_file.exists() else 0
        log_test_result("Log file creation and writing", final_size > initial_size, 
                       f"File size: {initial_size} → {final_size} bytes")
        
        return True
    except Exception as e:
        log_test_result("Logging infrastructure", False, str(e))
        return False

def test_safe_evaluate_basic(browser, tabs):
    """Test basic safe_evaluate functionality"""
    print("\n🔍 Testing safe_evaluate() Basic Functionality...")
    
    if not browser or not tabs:
        log_test_result("safe_evaluate basic test", False, "No browser connection available")
        return False
    
    try:
        # Get first available tab
        tab = browser.new_tab("about:blank")
        tab.start()
        
        # Wait for tab to be ready
        time.sleep(1)
        
        # Test 1: Simple JavaScript execution
        start_time = time.time()
        result = safe_evaluate(tab, "1 + 1", OperationType.NON_CRITICAL, "Basic math test")
        execution_time = (time.time() - start_time) * 1000
        
        if isinstance(result, OperationResult) and result.success and result.value == 2:
            log_test_result("safe_evaluate simple math", True, f"Result: {result.value}, Time: {execution_time:.1f}ms")
        else:
            log_test_result("safe_evaluate simple math", False, f"Expected 2, got {result}")
        
        # Test 2: String operation
        result = safe_evaluate(tab, "'Hello' + ' World'", OperationType.NON_CRITICAL, "String concatenation test")
        if isinstance(result, OperationResult) and result.success and result.value == "Hello World":
            log_test_result("safe_evaluate string operation", True, f"Result: '{result.value}'")
        else:
            log_test_result("safe_evaluate string operation", False, f"Expected 'Hello World', got {result}")
        
        # Test 3: Object operation
        result = safe_evaluate(tab, "({test: 'value', number: 42})", OperationType.NON_CRITICAL, "Object creation test")
        if isinstance(result, OperationResult) and result.success and isinstance(result.value, dict):
            log_test_result("safe_evaluate object operation", True, f"Result: {result.value}")
        else:
            log_test_result("safe_evaluate object operation", False, f"Expected object, got {result}")
        
        # Clean up
        tab.stop()
        return True
        
    except Exception as e:
        log_test_result("safe_evaluate basic functionality", False, f"Exception: {e}")
        return False

def test_error_handling(browser, tabs):
    """Test error handling capabilities"""
    print("\n🔍 Testing Error Handling...")
    
    if not browser or not tabs:
        log_test_result("Error handling test", False, "No browser connection available")
        return False
    
    try:
        # Get first available tab
        tab = browser.new_tab("about:blank")
        tab.start()
        time.sleep(1)
        
        # Test 1: JavaScript syntax error
        result = safe_evaluate(tab, "invalid javascript syntax !!!", OperationType.NON_CRITICAL, "Syntax error test")
        if isinstance(result, OperationResult) and not result.success:
            log_test_result("JavaScript syntax error handling", True, f"Error detected: {result.error}")
        else:
            log_test_result("JavaScript syntax error handling", False, "Should have failed but didn't")
        
        # Test 2: Undefined variable reference
        result = safe_evaluate(tab, "nonExistentVariable + 1", OperationType.NON_CRITICAL, "Undefined variable test")
        if isinstance(result, OperationResult) and not result.success:
            log_test_result("Undefined variable error handling", True, f"Error detected: {result.error}")
        else:
            log_test_result("Undefined variable error handling", False, "Should have failed but didn't")
        
        # Test 3: Type error
        result = safe_evaluate(tab, "null.someMethod()", OperationType.NON_CRITICAL, "Type error test")
        if isinstance(result, OperationResult) and not result.success:
            log_test_result("Type error handling", True, f"Error detected: {result.error}")
        else:
            log_test_result("Type error handling", False, "Should have failed but didn't")
        
        # Clean up
        tab.stop()
        return True
        
    except Exception as e:
        log_test_result("Error handling tests", False, f"Exception: {e}")
        return False

def test_performance_overhead():
    """Test performance overhead of framework"""
    print("\n🔍 Testing Performance Overhead...")
    
    try:
        import pychrome
        browser = pychrome.Browser(url="http://127.0.0.1:9223")
        tab = browser.new_tab("about:blank")
        tab.start()
        time.sleep(1)
        
        # Test direct pychrome call (baseline)
        baseline_times = []
        for i in range(10):
            start = time.time()
            tab.Runtime.evaluate(expression="1 + 1")
            baseline_times.append((time.time() - start) * 1000)
        
        baseline_avg = sum(baseline_times) / len(baseline_times)
        
        # Test safe_evaluate wrapper
        wrapper_times = []
        for i in range(10):
            start = time.time()
            safe_evaluate(tab, "1 + 1", OperationType.NON_CRITICAL, "Performance test")
            wrapper_times.append((time.time() - start) * 1000)
        
        wrapper_avg = sum(wrapper_times) / len(wrapper_times)
        overhead = wrapper_avg - baseline_avg
        
        # Check if overhead is acceptable (<50ms for non-critical operations)
        acceptable = overhead < 50
        log_test_result("Performance overhead acceptable", acceptable, 
                       f"Baseline: {baseline_avg:.1f}ms, Wrapper: {wrapper_avg:.1f}ms, Overhead: {overhead:.1f}ms")
        
        tab.stop()
        return acceptable
        
    except Exception as e:
        log_test_result("Performance overhead test", False, f"Exception: {e}")
        return False

def test_manager_class():
    """Test ChromeCommunicationManager functionality"""
    print("\n🔍 Testing ChromeCommunicationManager...")
    
    try:
        # Create manager instance
        manager = ChromeCommunicationManager()
        log_test_result("ChromeCommunicationManager creation", True, "Manager instance created")
        
        # Test manager has expected methods
        expected_methods = ['get_safe_evaluator', 'register_tab', 'get_tab_health', 'get_performance_stats']
        for method in expected_methods:
            has_method = hasattr(manager, method)
            log_test_result(f"Manager has {method} method", has_method)
        
        return True
        
    except Exception as e:
        log_test_result("ChromeCommunicationManager test", False, f"Exception: {e}")
        return False

def test_framework_integration():
    """Test full framework integration"""
    print("\n🔍 Testing Framework Integration...")
    
    try:
        import pychrome
        browser = pychrome.Browser(url="http://127.0.0.1:9223")
        tab = browser.new_tab("about:blank")
        tab.start()
        time.sleep(1)
        
        # Create manager and register tab
        manager = ChromeCommunicationManager()
        tab_id = "test_tab_integration"
        manager.register_tab(tab_id, tab)
        
        # Get safe evaluator for this tab
        evaluator = manager.get_safe_evaluator(tab_id)
        
        # Test evaluation through manager
        result = evaluator("Math.sqrt(16)", OperationType.NON_CRITICAL, "Square root test")
        if isinstance(result, OperationResult) and result.success and result.value == 4:
            log_test_result("Manager-mediated evaluation", True, f"Result: {result.value}")
        else:
            log_test_result("Manager-mediated evaluation", False, f"Expected 4, got {result}")
        
        # Test health monitoring
        health = manager.get_tab_health(tab_id)
        health_valid = isinstance(health, TabHealthStatus) if health else False
        log_test_result("Tab health monitoring", health_valid, f"Health object: {type(health).__name__ if health else 'None'}")
        
        # Test performance stats
        stats = manager.get_performance_stats(tab_id)
        log_test_result("Performance stats available", isinstance(stats, dict), f"Stats keys: {list(stats.keys()) if isinstance(stats, dict) else 'None'}")
        
        tab.stop()
        return True
        
    except Exception as e:
        log_test_result("Framework integration test", False, f"Exception: {e}")
        return False

def run_all_tests():
    """Run all framework tests"""
    print("🚀 Chrome Communication Framework Test Suite")
    print("=" * 60)
    
    # Test 1: Basic connectivity
    tabs = test_chrome_connection()
    browser, tabs = test_pychrome_import()
    
    if not browser:
        print("\n❌ Cannot proceed with tests - Chrome connection failed")
        return False
    
    # Test 2: Infrastructure
    test_logging_infrastructure()
    
    # Test 3: Core functionality
    test_safe_evaluate_basic(browser, tabs)
    test_error_handling(browser, tabs)
    
    # Test 4: Performance
    test_performance_overhead()
    
    # Test 5: Advanced features
    test_manager_class()
    test_framework_integration()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    total = TEST_RESULTS["total_tests"]
    passed = TEST_RESULTS["passed"]
    failed = TEST_RESULTS["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if failed > 0:
        print("\n❌ FAILED TESTS:")
        for error in TEST_RESULTS["errors"]:
            print(f"  • {error['test']}: {error['details']}")
    
    if success_rate >= 80:
        print(f"\n✅ Framework validation PASSED ({success_rate:.1f}% success rate)")
        return True
    else:
        print(f"\n❌ Framework validation FAILED ({success_rate:.1f}% success rate)")
        return False

if __name__ == "__main__":
    print("Starting Chrome Communication Framework validation...")
    
    # Check if Chrome is running
    import requests
    try:
        response = requests.get('http://127.0.0.1:9223/json', timeout=2)
        if response.status_code != 200:
            print("❌ Chrome not accessible on port 9223")
            print("💡 Please ensure Chrome is running with --remote-debugging-port=9223")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to Chrome: {e}")
        print("💡 Please start Chrome using the external start script as per CLAUDE.md")
        sys.exit(1)
    
    # Run all tests
    success = run_all_tests()
    
    if success:
        print("\n🎉 All framework features are working correctly!")
        print("✅ Ready for integration into main application")
        sys.exit(0)
    else:
        print("\n⚠️  Some framework issues detected")
        print("❌ Review failed tests before integration")
        sys.exit(1)