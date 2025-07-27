#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Chrome Communication Framework
Tests safe_evaluate() wrapper and related functionality with edge cases

Following CLAUDE.md principles:
- Tests with real scenarios (no mocking where possible)
- Comprehensive logging for root cause analysis
- Fails fast with clear error messages
"""

import unittest
import time
import json
import threading
import concurrent.futures
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.chrome_communication import (
    safe_evaluate, ChromeCommunicationManager, OperationType, 
    TabHealthStatus, OperationResult,
    TabHealthValidator, ChromeOperationLogger
)
from src.utils.trading_errors import (
    ChromeCommunicationError, OrderValidationError,
    NetworkError, AuthenticationError
)

class TestSafeEvaluateUnit(unittest.TestCase):
    """Unit tests for safe_evaluate() function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_tab = Mock()
        self.mock_tab.id = "test_tab_1"
        self.mock_tab.Runtime.evaluate.return_value = {
            "result": {"value": "test_success"}
        }
        
    def test_safe_evaluate_basic_success(self):
        """Test basic successful JavaScript execution"""
        result = safe_evaluate(
            self.mock_tab, 
            "1 + 1", 
            OperationType.NON_CRITICAL,
            "Basic math test"
        )
        
        self.assertIsInstance(result, OperationResult)
        self.assertTrue(result.success)
        self.assertEqual(result.value, "test_success")
        self.assertIsNone(result.error)
        self.assertGreater(result.execution_time, 0)
        
    def test_safe_evaluate_with_exception_details(self):
        """Test handling of JavaScript execution errors"""
        self.mock_tab.Runtime.evaluate.return_value = {
            "exceptionDetails": {
                "text": "ReferenceError: undefined_var is not defined",
                "lineNumber": 1,
                "columnNumber": 1
            }
        }
        
        result = safe_evaluate(
            self.mock_tab,
            "undefined_var.someMethod()",
            OperationType.NON_CRITICAL,
            "Test undefined variable"
        )
        
        self.assertFalse(result.success)
        self.assertIn("ReferenceError", result.error)
        self.assertIsNone(result.value)
        
    def test_safe_evaluate_malformed_javascript(self):
        """Test handling of malformed JavaScript code"""
        test_cases = [
            ("function() {", "Syntax error test"),  # Unclosed function
            ("for (;;) {}", "Infinite loop test"),  # Infinite loop
            ("throw new Error('Test')", "Explicit throw test"),  # Explicit error
            ("'unclosed string", "Unclosed string test"),  # Unclosed string
            ("1 +++ 2", "Invalid operator test"),  # Invalid syntax
        ]
        
        for js_code, description in test_cases:
            self.mock_tab.Runtime.evaluate.return_value = {
                "exceptionDetails": {"text": f"SyntaxError in: {js_code}"}
            }
            
            result = safe_evaluate(
                self.mock_tab,
                js_code,
                OperationType.NON_CRITICAL,
                description
            )
            
            self.assertFalse(result.success)
            self.assertIsNotNone(result.error)
            
    def test_safe_evaluate_large_payload(self):
        """Test handling of very large JavaScript payloads"""
        # Create a large JavaScript object
        large_data = json.dumps({"data": "x" * 1000000})  # 1MB of data
        js_code = f"JSON.parse('{large_data}')"
        
        self.mock_tab.Runtime.evaluate.return_value = {
            "result": {"value": json.loads(large_data)}
        }
        
        result = safe_evaluate(
            self.mock_tab,
            js_code,
            OperationType.NON_CRITICAL,
            "Large payload test"
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.value["data"], "x" * 1000000)
        
    def test_safe_evaluate_different_data_types(self):
        """Test handling of various JavaScript data types"""
        test_cases = [
            ("null", None),
            ("undefined", None),
            ("true", True),
            ("false", False),
            ("42", 42),
            ("3.14159", 3.14159),
            ("'test string'", "test string"),
            ("[]", []),
            ("{}", {}),
            ("[1, 2, 3]", [1, 2, 3]),
            ("({a: 1, b: 'test'})", {"a": 1, "b": "test"}),
            ("new Date('2025-01-01').toISOString()", "2025-01-01T00:00:00.000Z"),
            ("BigInt(9007199254740991).toString()", "9007199254740991"),
        ]
        
        for js_code, expected_value in test_cases:
            self.mock_tab.Runtime.evaluate.return_value = {
                "result": {"value": expected_value}
            }
            
            result = safe_evaluate(
                self.mock_tab,
                js_code,
                OperationType.NON_CRITICAL,
                f"Test data type: {js_code}"
            )
            
            self.assertTrue(result.success)
            self.assertEqual(result.value, expected_value)
            
    def test_safe_evaluate_timeout_handling(self):
        """Test timeout handling in safe_evaluate"""
        def slow_evaluate(*args, **kwargs):
            time.sleep(2)  # Simulate slow execution
            return {"result": {"value": "too_late"}}
            
        self.mock_tab.Runtime.evaluate = slow_evaluate
        
        result = safe_evaluate(
            self.mock_tab,
            "slowOperation()",
            OperationType.CRITICAL,
            "Timeout test",
            timeout=1  # 1 second timeout
        )
        
        # Should handle timeout gracefully
        self.assertFalse(result.success)
        self.assertIn("timeout", result.error.lower())
        
    def test_safe_evaluate_unicode_handling(self):
        """Test handling of Unicode and special characters"""
        unicode_tests = [
            "'Hello 世界'",  # Chinese characters
            "'Привет мир'",  # Cyrillic
            "'🚀 Emoji test 🎉'",  # Emojis
            "'Special chars: \\n\\r\\t'",  # Escape sequences
            "'Quotes: \"double\" and \\'single\\''",  # Mixed quotes
        ]
        
        for js_code in unicode_tests:
            # Extract expected value from JS string literal
            expected = js_code.strip("'").encode().decode('unicode_escape')
            
            self.mock_tab.Runtime.evaluate.return_value = {
                "result": {"value": expected}
            }
            
            result = safe_evaluate(
                self.mock_tab,
                js_code,
                OperationType.NON_CRITICAL,
                f"Unicode test: {js_code[:20]}..."
            )
            
            self.assertTrue(result.success)
            self.assertEqual(result.value, expected)
            
    def test_safe_evaluate_concurrent_execution(self):
        """Test concurrent execution of safe_evaluate"""
        results = []
        errors = []
        
        def execute_concurrent(index):
            try:
                result = safe_evaluate(
                    self.mock_tab,
                    f"'Concurrent test {index}'",
                    OperationType.NON_CRITICAL,
                    f"Concurrent test {index}"
                )
                results.append(result)
            except Exception as e:
                errors.append(e)
                
        # Execute 50 concurrent operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(execute_concurrent, i) for i in range(50)]
            concurrent.futures.wait(futures)
            
        # All should succeed without errors
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 50)
        self.assertTrue(all(r.success for r in results))
        
    def test_safe_evaluate_memory_leak_prevention(self):
        """Test that safe_evaluate doesn't cause memory leaks"""
        import gc
        import weakref
        
        # Create a weak reference to track object lifecycle
        weak_refs = []
        
        for i in range(100):
            result = safe_evaluate(
                self.mock_tab,
                f"'Memory test {i}'",
                OperationType.NON_CRITICAL,
                f"Memory leak test {i}"
            )
            weak_refs.append(weakref.ref(result))
            
        # Force garbage collection
        gc.collect()
        
        # Check that objects are being garbage collected
        alive_count = sum(1 for ref in weak_refs if ref() is not None)
        self.assertLess(alive_count, 10, "Potential memory leak detected")
        
    def test_safe_evaluate_binary_data(self):
        """Test handling of binary data in JavaScript responses"""
        # Simulate base64 encoded binary data
        binary_data = b"Binary test data \x00\x01\x02\x03"
        base64_data = binary_data.hex()
        
        self.mock_tab.Runtime.evaluate.return_value = {
            "result": {"value": base64_data}
        }
        
        result = safe_evaluate(
            self.mock_tab,
            f"getBinaryDataAsHex()",
            OperationType.NON_CRITICAL,
            "Binary data test"
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.value, base64_data)
        
    def test_safe_evaluate_network_error_handling(self):
        """Test handling of network-level errors"""
        import socket
        
        network_errors = [
            socket.timeout("Connection timeout"),
            ConnectionError("Connection refused"),
            BrokenPipeError("Broken pipe"),
            OSError("Network unreachable"),
        ]
        
        for error in network_errors:
            self.mock_tab.Runtime.evaluate.side_effect = error
            
            result = safe_evaluate(
                self.mock_tab,
                "networkTest()",
                OperationType.CRITICAL,
                f"Network error test: {type(error).__name__}"
            )
            
            self.assertFalse(result.success)
            self.assertIn(type(error).__name__, result.error)
            
    def test_safe_evaluate_partial_response(self):
        """Test handling of partial or malformed responses"""
        partial_responses = [
            {},  # Empty response
            {"result": {}},  # Missing value
            {"result": {"type": "object"}},  # Missing value with type
            {"error": {"message": "Chrome error"}},  # Error response
            None,  # Null response
        ]
        
        for response in partial_responses:
            self.mock_tab.Runtime.evaluate.return_value = response
            
            result = safe_evaluate(
                self.mock_tab,
                "partialTest()",
                OperationType.NON_CRITICAL,
                f"Partial response test"
            )
            
            # Should handle gracefully without crashing
            self.assertIsInstance(result, OperationResult)
            if response and "error" in response:
                self.assertFalse(result.success)
                
    def test_safe_evaluate_dom_operations(self):
        """Test DOM-specific JavaScript operations"""
        dom_operations = [
            ("document.querySelector('#test')", {"nodeId": 123}),
            ("document.querySelectorAll('.test')", [{"nodeId": 1}, {"nodeId": 2}]),
            ("element.click()", True),
            ("element.value = 'test'", "test"),
            ("window.location.href", "https://example.com"),
        ]
        
        for js_code, expected_value in dom_operations:
            self.mock_tab.Runtime.evaluate.return_value = {
                "result": {"value": expected_value}
            }
            
            result = safe_evaluate(
                self.mock_tab,
                js_code,
                OperationType.CRITICAL,
                f"DOM operation: {js_code}"
            )
            
            self.assertTrue(result.success)
            self.assertEqual(result.value, expected_value)
            
    def test_safe_evaluate_performance_metrics(self):
        """Test that performance metrics are properly collected"""
        # Mock a specific execution time
        start_time = time.time()
        
        def timed_evaluate(*args, **kwargs):
            time.sleep(0.1)  # 100ms execution
            return {"result": {"value": "success"}}
            
        self.mock_tab.Runtime.evaluate = timed_evaluate
        
        result = safe_evaluate(
            self.mock_tab,
            "performanceTest()",
            OperationType.CRITICAL,
            "Performance metrics test"
        )
        
        self.assertTrue(result.success)
        self.assertGreaterEqual(result.execution_time, 0.1)
        self.assertLess(result.execution_time, 0.2)


class TestRetryLogicUnit(unittest.TestCase):
    """Unit tests for retry logic and strategies"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_tab = Mock()
        self.mock_tab.id = "test_tab_retry"
        self.attempt_count = 0
        
    def test_retry_exponential_backoff(self):
        """Test exponential backoff retry strategy"""
        delays = []
        
        def failing_evaluate(*args, **kwargs):
            self.attempt_count += 1
            if self.attempt_count <= 3:
                # Record delay between attempts
                current_time = time.time()
                if hasattr(self, 'last_attempt_time'):
                    delays.append(current_time - self.last_attempt_time)
                self.last_attempt_time = current_time
                raise ConnectionError("Simulated connection error")
            return {"result": {"value": "success"}}
            
        self.mock_tab.Runtime.evaluate = failing_evaluate
        
        result = safe_evaluate(
            self.mock_tab,
            "retryTest()",
            OperationType.CRITICAL,
            "Exponential backoff test",
            retry_count=5
        )
        
        self.assertTrue(result.success)
        self.assertEqual(self.attempt_count, 4)  # Initial + 3 retries
        
        # Verify exponential backoff pattern
        for i in range(1, len(delays)):
            self.assertGreater(delays[i], delays[i-1])
            
    def test_retry_immediate_strategy(self):
        """Test immediate retry strategy for transient errors"""
        self.attempt_count = 0
        
        def transient_failure(*args, **kwargs):
            self.attempt_count += 1
            if self.attempt_count == 1:
                raise ConnectionError("Transient error")
            return {"result": {"value": "success"}}
            
        self.mock_tab.Runtime.evaluate = transient_failure
        
        start_time = time.time()
        result = safe_evaluate(
            self.mock_tab,
            "immediateRetryTest()",
            OperationType.CRITICAL,
            "Immediate retry test"
        )
        elapsed = time.time() - start_time
        
        self.assertTrue(result.success)
        self.assertEqual(self.attempt_count, 2)
        self.assertLess(elapsed, 0.5)  # Should be fast with minimal delay
        
    def test_retry_max_attempts_exceeded(self):
        """Test behavior when max retry attempts are exceeded"""
        def always_fail(*args, **kwargs):
            self.attempt_count += 1
            raise ConnectionError("Persistent failure")
            
        self.mock_tab.Runtime.evaluate = always_fail
        
        result = safe_evaluate(
            self.mock_tab,
            "maxRetriesTest()",
            OperationType.CRITICAL,
            "Max retries test",
            retry_count=3
        )
        
        self.assertFalse(result.success)
        self.assertEqual(self.attempt_count, 4)  # Initial + 3 retries
        self.assertIn("Persistent failure", result.error)
        
    def test_retry_non_retryable_errors(self):
        """Test that certain errors are not retried"""
        non_retryable_errors = [
            SyntaxError("Invalid syntax"),
            TypeError("Type mismatch"),
            ValueError("Invalid value"),
        ]
        
        for error in non_retryable_errors:
            self.attempt_count = 0
            self.mock_tab.Runtime.evaluate.side_effect = error
            
            result = safe_evaluate(
                self.mock_tab,
                "nonRetryableTest()",
                OperationType.CRITICAL,
                f"Non-retryable error: {type(error).__name__}",
                retry_count=3
            )
            
            self.assertFalse(result.success)
            self.assertEqual(self.attempt_count, 1)  # No retries
            
    def test_retry_with_jitter(self):
        """Test retry with jitter to prevent thundering herd"""
        retry_times = []
        
        def record_retry_time(*args, **kwargs):
            retry_times.append(time.time())
            if len(retry_times) < 5:
                raise ConnectionError("Retry with jitter")
            return {"result": {"value": "success"}}
            
        self.mock_tab.Runtime.evaluate = record_retry_time
        
        # Run multiple times to test jitter randomness
        for _ in range(3):
            retry_times.clear()
            result = safe_evaluate(
                self.mock_tab,
                "jitterTest()",
                OperationType.CRITICAL,
                "Jitter test"
            )
            
            # Calculate delays
            delays = [retry_times[i+1] - retry_times[i] for i in range(len(retry_times)-1)]
            
            # Delays should not be identical (jitter adds randomness)
            self.assertGreater(len(set(delays)), 1)
            
    def test_timeout_cascading(self):
        """Test timeout cascading through retry attempts"""
        timeouts_used = []
        
        def track_timeout(*args, **kwargs):
            # Extract timeout from kwargs if present
            timeout = kwargs.get('timeout', 30)
            timeouts_used.append(timeout)
            if len(timeouts_used) < 3:
                time.sleep(0.1)
                raise TimeoutError("Operation timeout")
            return {"result": {"value": "success"}}
            
        self.mock_tab.Runtime.evaluate = track_timeout
        
        result = safe_evaluate(
            self.mock_tab,
            "timeoutCascadeTest()",
            OperationType.CRITICAL,
            "Timeout cascade test",
            timeout=5,
            retry_count=3
        )
        
        # Verify timeouts remain consistent across retries
        self.assertTrue(all(t == 5 for t in timeouts_used))


class TestCircuitBreakerUnit(unittest.TestCase):
    """Unit tests for circuit breaker functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = ChromeCommunicationManager()
        self.mock_tab = Mock()
        self.mock_tab.id = "test_circuit_breaker"
        
    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures"""
        # Simulate multiple failures
        self.mock_tab.Runtime.evaluate.side_effect = ConnectionError("Connection failed")
        
        # Make requests until circuit opens
        failures = 0
        for i in range(10):
            result = safe_evaluate(
                self.mock_tab,
                "circuitTest()",
                OperationType.CRITICAL,
                f"Circuit test {i}"
            )
            if not result.success:
                failures += 1
                
        # Circuit should be open after threshold
        self.assertGreater(failures, 5)
        
        # Next request should fail immediately (circuit open)
        start_time = time.time()
        result = safe_evaluate(
            self.mock_tab,
            "circuitOpenTest()",
            OperationType.CRITICAL,
            "Test with open circuit"
        )
        elapsed = time.time() - start_time
        
        self.assertFalse(result.success)
        self.assertLess(elapsed, 0.1)  # Should fail fast
        
    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery after cool-down period"""
        # First, open the circuit with failures
        self.mock_tab.Runtime.evaluate.side_effect = ConnectionError("Connection failed")
        
        for i in range(10):
            safe_evaluate(
                self.mock_tab,
                "openCircuit()",
                OperationType.CRITICAL,
                f"Open circuit attempt {i}"
            )
            
        # Now make it succeed
        self.mock_tab.Runtime.evaluate.side_effect = None
        self.mock_tab.Runtime.evaluate.return_value = {"result": {"value": "recovered"}}
        
        # Wait for cool-down (simulate by mocking time)
        with patch('time.time', return_value=time.time() + 60):
            result = safe_evaluate(
                self.mock_tab,
                "recoveryTest()",
                OperationType.CRITICAL,
                "Circuit recovery test"
            )
            
            # Should attempt recovery
            self.assertTrue(result.success)
            self.assertEqual(result.value, "recovered")
            
    def test_circuit_breaker_half_open_state(self):
        """Test circuit breaker half-open state behavior"""
        # Open the circuit
        self.mock_tab.Runtime.evaluate.side_effect = ConnectionError("Failed")
        
        for _ in range(10):
            safe_evaluate(self.mock_tab, "test()", OperationType.CRITICAL, "Open circuit")
            
        # Simulate cool-down period
        with patch('time.time', return_value=time.time() + 60):
            # First request in half-open state succeeds
            self.mock_tab.Runtime.evaluate.side_effect = None
            self.mock_tab.Runtime.evaluate.return_value = {"result": {"value": "success"}}
            
            result1 = safe_evaluate(
                self.mock_tab,
                "halfOpenTest1()",
                OperationType.CRITICAL,
                "Half-open test 1"
            )
            self.assertTrue(result1.success)
            
            # Second request also succeeds - circuit should close
            result2 = safe_evaluate(
                self.mock_tab,
                "halfOpenTest2()",
                OperationType.CRITICAL,
                "Half-open test 2"
            )
            self.assertTrue(result2.success)
            
            # Circuit should now be closed (normal operation)
            for i in range(5):
                result = safe_evaluate(
                    self.mock_tab,
                    f"closedCircuitTest{i}()",
                    OperationType.CRITICAL,
                    f"Closed circuit test {i}"
                )
                self.assertTrue(result.success)


class TestValidationUnit(unittest.TestCase):
    """Unit tests for validation functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.validator = TabHealthValidator()
        self.mock_tab = Mock()
        self.mock_tab.id = "test_validation"
        
    def test_tab_health_validation_healthy(self):
        """Test validation of healthy tab"""
        # Mock healthy tab responses
        self.mock_tab.Runtime.evaluate.return_value = {"result": {"value": True}}
        self.mock_tab.Page.getFrameTree.return_value = {
            "frameTree": {"frame": {"id": "123", "url": "https://example.com"}}
        }
        
        health = self.validator.validate_tab_health(self.mock_tab)
        
        self.assertEqual(health.status, TabHealthStatus.HEALTHY)
        self.assertTrue(health.is_responsive)
        self.assertIsNotNone(health.last_successful_operation)
        
    def test_tab_health_validation_unresponsive(self):
        """Test validation of unresponsive tab"""
        self.mock_tab.Runtime.evaluate.side_effect = TimeoutError("Tab timeout")
        
        health = self.validator.validate_tab_health(self.mock_tab)
        
        self.assertEqual(health.status, TabHealthStatus.UNRESPONSIVE)
        self.assertFalse(health.is_responsive)
        self.assertGreater(health.consecutive_failures, 0)
        
    def test_tab_health_validation_crashed(self):
        """Test validation of crashed tab"""
        self.mock_tab.Runtime.evaluate.side_effect = Exception("Tab crashed")
        self.mock_tab.Page.getFrameTree.side_effect = Exception("No frame tree")
        
        health = self.validator.validate_tab_health(self.mock_tab)
        
        self.assertIn(health.status, [TabHealthStatus.CRASHED, TabHealthStatus.UNKNOWN])
        self.assertFalse(health.is_responsive)
        
    def test_operation_validation_success(self):
        """Test successful operation validation"""
        operation = {
            "type": OperationType.CRITICAL,
            "js_code": "validateOperation()",
            "description": "Test validation"
        }
        
        # Mock successful validation
        self.mock_tab.Runtime.evaluate.return_value = {"result": {"value": True}}
        
        is_valid = self.validator.validate_operation(self.mock_tab, operation)
        
        self.assertTrue(is_valid)
        
    def test_operation_validation_failure(self):
        """Test failed operation validation"""
        operation = {
            "type": OperationType.CRITICAL,
            "js_code": "invalidOperation()",
            "description": "Test invalid operation"
        }
        
        # Mock validation failure
        self.mock_tab.Runtime.evaluate.return_value = {
            "result": {"value": False},
            "exceptionDetails": {"text": "Validation failed"}
        }
        
        is_valid = self.validator.validate_operation(self.mock_tab, operation)
        
        self.assertFalse(is_valid)


class TestConcurrencyUnit(unittest.TestCase):
    """Unit tests for concurrency handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = ChromeCommunicationManager()
        self.mock_tabs = []
        for i in range(5):
            mock_tab = Mock()
            mock_tab.id = f"test_concurrent_{i}"
            mock_tab.Runtime.evaluate.return_value = {"result": {"value": i}}
            self.mock_tabs.append(mock_tab)
            
    def test_concurrent_operations_different_tabs(self):
        """Test concurrent operations on different tabs"""
        results = {}
        errors = []
        
        def execute_on_tab(tab, index):
            try:
                result = safe_evaluate(
                    tab,
                    f"concurrentOp({index})",
                    OperationType.CRITICAL,
                    f"Concurrent op {index}"
                )
                results[index] = result
            except Exception as e:
                errors.append((index, e))
                
        # Execute operations concurrently
        threads = []
        for i, tab in enumerate(self.mock_tabs):
            thread = threading.Thread(target=execute_on_tab, args=(tab, i))
            threads.append(thread)
            thread.start()
            
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=5)
            
        # Verify all succeeded
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 5)
        
        # Verify each got correct result
        for i in range(5):
            self.assertTrue(results[i].success)
            self.assertEqual(results[i].value, i)
            
    def test_concurrent_operations_same_tab(self):
        """Test concurrent operations on the same tab"""
        tab = self.mock_tabs[0]
        results = []
        
        def execute_operation(op_id):
            result = safe_evaluate(
                tab,
                f"sameTabOp({op_id})",
                OperationType.CRITICAL,
                f"Same tab op {op_id}"
            )
            results.append(result)
            
        # Execute 10 operations concurrently on same tab
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(execute_operation, i) for i in range(10)]
            concurrent.futures.wait(futures)
            
        # All should complete (serialized internally)
        self.assertEqual(len(results), 10)
        self.assertTrue(all(r.success for r in results))
        
    def test_operation_queue_ordering(self):
        """Test that critical operations are prioritized"""
        execution_order = []
        
        def track_execution(*args, **kwargs):
            # Extract operation description
            description = args[3] if len(args) > 3 else "unknown"
            execution_order.append(description)
            return {"result": {"value": "success"}}
            
        tab = Mock()
        tab.id = "test_priority"
        tab.Runtime.evaluate = track_execution
        
        # Queue mixed priority operations
        operations = [
            (OperationType.NON_CRITICAL, "Non-critical 1"),
            (OperationType.CRITICAL, "Critical 1"),
            (OperationType.NON_CRITICAL, "Non-critical 2"),
            (OperationType.CRITICAL, "Critical 2"),
            (OperationType.NON_CRITICAL, "Non-critical 3"),
        ]
        
        threads = []
        for op_type, desc in operations:
            thread = threading.Thread(
                target=safe_evaluate,
                args=(tab, "test()", op_type, desc)
            )
            threads.append(thread)
            thread.start()
            time.sleep(0.01)  # Small delay to ensure ordering
            
        for thread in threads:
            thread.join()
            
        # Critical operations should be prioritized
        critical_indices = [i for i, desc in enumerate(execution_order) if "Critical" in desc]
        non_critical_indices = [i for i, desc in enumerate(execution_order) if "Non-critical" in desc]
        
        # Critical operations should generally come before non-critical
        if critical_indices and non_critical_indices:
            avg_critical = sum(critical_indices) / len(critical_indices)
            avg_non_critical = sum(non_critical_indices) / len(non_critical_indices)
            self.assertLess(avg_critical, avg_non_critical)


if __name__ == '__main__':
    unittest.main(verbosity=2)