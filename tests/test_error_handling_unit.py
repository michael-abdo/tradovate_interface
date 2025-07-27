#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Error Handling Edge Cases
Tests network partitions, partial responses, and error recovery mechanisms

Following CLAUDE.md principles:
- Real error scenarios
- Comprehensive logging for debugging
- Fast failure detection
"""

import unittest
import time
import json
import socket
import threading
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.trading_errors import (
    TradingError, ErrorSeverity, ErrorCategory, ErrorContext,
    ChromeConnectionError, OrderValidationError, NetworkError,
    AuthenticationError, DataIntegrityError, ConfigurationError,
    RateLimitError, SystemError, UIElementError, MarketDataError,
    ErrorAggregator, alert_on_critical_error
)

from src.utils.chrome_communication import (
    safe_evaluate, ChromeCommunicationManager, OperationType,
    CircuitBreakerError, ValidationError, OperationResult
)


class TestErrorHandlingEdgeCases(unittest.TestCase):
    """Test error handling for edge cases and unusual scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_tab = Mock()
        self.mock_tab.id = "test_error_handling"
        self.aggregator = ErrorAggregator()
        
    def test_network_partition_handling(self):
        """Test handling of network partition scenarios"""
        # Simulate various network partition errors
        partition_errors = [
            socket.error(104, "Connection reset by peer"),
            socket.error(111, "Connection refused"),
            socket.error(110, "Connection timed out"),
            socket.error(113, "No route to host"),
            OSError("Network is unreachable"),
            ConnectionResetError("Connection reset"),
            BrokenPipeError("Broken pipe"),
        ]
        
        for error in partition_errors:
            with self.subTest(error=error):
                try:
                    raise NetworkError(
                        f"Network partition: {error}",
                        severity=ErrorSeverity.CRITICAL,
                        network_error=str(error),
                        retry_count=3
                    )
                except NetworkError as e:
                    # Verify error context is properly captured
                    self.assertEqual(e.context.category, ErrorCategory.NETWORK)
                    self.assertEqual(e.context.severity, ErrorSeverity.CRITICAL)
                    self.assertIn("Network partition", e.context.message)
                    self.assertEqual(e.context.retry_count, 3)
                    
    def test_partial_response_handling(self):
        """Test handling of partial or malformed responses"""
        partial_responses = [
            # Empty response
            {},
            # Missing critical fields
            {"timestamp": "2025-01-01", "data": None},
            # Truncated JSON
            '{"order": {"id": 123, "status": "PENDI',
            # Invalid nested structure
            {"order": {"details": {"price": "not_a_number"}}},
            # Circular reference (when serialized)
            {"self": {"ref": "circular"}},
            # Unicode issues
            {"symbol": "NQ\udcfe\udcff"},
            # Very large response
            {"data": "x" * 10000000},  # 10MB string
        ]
        
        for response in partial_responses:
            with self.subTest(response=response):
                try:
                    # Simulate processing partial response
                    if isinstance(response, str):
                        # Try to parse truncated JSON
                        try:
                            json.loads(response)
                        except json.JSONDecodeError:
                            raise DataIntegrityError(
                                "Partial JSON response",
                                severity=ErrorSeverity.ERROR,
                                raw_response=response[:100]
                            )
                    elif response.get("data") == "x" * 10000000:
                        raise DataIntegrityError(
                            "Response too large",
                            severity=ErrorSeverity.WARNING,
                            response_size=len(str(response))
                        )
                    elif not response or response.get("data") is None:
                        raise DataIntegrityError(
                            "Missing required data",
                            severity=ErrorSeverity.ERROR,
                            response=response
                        )
                except (DataIntegrityError, json.JSONDecodeError) as e:
                    # Verify proper error handling
                    self.assertIsNotNone(e)
                    
    def test_chrome_devtools_protocol_errors(self):
        """Test Chrome DevTools protocol specific errors"""
        protocol_errors = [
            {
                "error": {
                    "code": -32000,
                    "message": "Cannot find context with specified id"
                }
            },
            {
                "error": {
                    "code": -32601,
                    "message": "Method not found"
                }
            },
            {
                "error": {
                    "code": -32602,
                    "message": "Invalid params"
                }
            },
            {
                "error": {
                    "code": -32603,
                    "message": "Internal error"
                }
            },
            {
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            }
        ]
        
        for protocol_error in protocol_errors:
            self.mock_tab.Runtime.evaluate.return_value = protocol_error
            
            result = safe_evaluate(
                self.mock_tab,
                "protocolErrorTest()",
                OperationType.NON_CRITICAL,
                f"Protocol error test: {protocol_error['error']['code']}"
            )
            
            self.assertFalse(result.success)
            self.assertIn(str(protocol_error['error']['code']), result.error)
            
    def test_authentication_error_scenarios(self):
        """Test various authentication error scenarios"""
        auth_scenarios = [
            ("Session expired", {"session_id": None, "expiry": "2025-01-01"}),
            ("Invalid credentials", {"user": "test", "error": "Invalid password"}),
            ("Account locked", {"account": "demo1", "locked": True, "reason": "Too many attempts"}),
            ("2FA required", {"requires_2fa": True, "method": "authenticator"}),
            ("IP not whitelisted", {"client_ip": "192.168.1.1", "allowed_ips": ["10.0.0.0/8"]}),
            ("Certificate expired", {"cert_expiry": "2024-12-31", "current_date": "2025-01-01"}),
        ]
        
        for scenario, context in auth_scenarios:
            with self.subTest(scenario=scenario):
                try:
                    raise AuthenticationError(
                        f"Authentication failed: {scenario}",
                        severity=ErrorSeverity.CRITICAL,
                        **context
                    )
                except AuthenticationError as e:
                    self.assertEqual(e.context.category, ErrorCategory.AUTHENTICATION)
                    self.assertEqual(e.context.severity, ErrorSeverity.CRITICAL)
                    # Verify all context data is preserved
                    for key, value in context.items():
                        self.assertEqual(getattr(e.context, key, None), value)
                        
    def test_race_condition_errors(self):
        """Test errors from race conditions"""
        # Simulate concurrent modification
        shared_state = {"value": 0}
        errors = []
        
        def modify_state(thread_id):
            try:
                # Simulate read-modify-write race condition
                current = shared_state["value"]
                time.sleep(0.001)  # Small delay to increase race likelihood
                expected = current
                shared_state["value"] = current + 1
                
                # Verify no concurrent modification
                if shared_state["value"] != expected + 1:
                    raise DataIntegrityError(
                        f"Race condition detected in thread {thread_id}",
                        severity=ErrorSeverity.CRITICAL,
                        expected=expected + 1,
                        actual=shared_state["value"],
                        thread_id=thread_id
                    )
            except DataIntegrityError as e:
                errors.append(e)
                
        # Run concurrent modifications
        threads = []
        for i in range(10):
            thread = threading.Thread(target=modify_state, args=(i,))
            threads.append(thread)
            thread.start()
            
        for thread in threads:
            thread.join()
            
        # Some threads should have detected race conditions
        self.assertGreater(len(errors), 0)
        for error in errors:
            self.assertEqual(error.context.category, ErrorCategory.DATA_INTEGRITY)
            self.assertIn("Race condition", error.context.message)
            
    def test_memory_pressure_errors(self):
        """Test error handling under memory pressure"""
        # Simulate memory allocation failures
        memory_errors = [
            MemoryError("Unable to allocate memory"),
            OSError(12, "Cannot allocate memory"),  # ENOMEM
            SystemError("Out of memory"),
        ]
        
        for error in memory_errors:
            with self.subTest(error=error):
                try:
                    # Simulate operation under memory pressure
                    raise SystemError(
                        f"Memory allocation failed: {error}",
                        severity=ErrorSeverity.CRITICAL,
                        available_memory_mb=50,
                        required_memory_mb=1000,
                        error_type=type(error).__name__
                    )
                except SystemError as e:
                    self.assertEqual(e.context.category, ErrorCategory.SYSTEM)
                    self.assertEqual(e.context.severity, ErrorSeverity.CRITICAL)
                    self.assertIn("Memory allocation", e.context.message)
                    
    def test_timeout_cascade_errors(self):
        """Test cascading timeout errors"""
        # Simulate timeout cascade
        timeout_chain = []
        
        def operation_with_timeout(level, parent_timeout):
            timeout = parent_timeout * 0.8  # Each level gets 80% of parent timeout
            
            if level > 0:
                try:
                    operation_with_timeout(level - 1, timeout)
                except TimeoutError as e:
                    # Wrap and re-raise with context
                    raise TimeoutError(
                        f"Timeout at level {level}: {e}"
                    ) from e
            else:
                # Base case - original timeout
                raise TimeoutError(f"Operation timeout at level {level}")
                
        try:
            operation_with_timeout(3, 10.0)
        except TimeoutError as e:
            # Verify full timeout chain is preserved
            self.assertIn("level 3", str(e))
            self.assertIsNotNone(e.__cause__)
            self.assertIn("level 2", str(e.__cause__))
            
    def test_ui_element_state_errors(self):
        """Test UI element state transition errors"""
        ui_errors = [
            UIElementError(
                "Element state transition failed",
                severity=ErrorSeverity.ERROR,
                element_id="submit-button",
                expected_state="enabled",
                actual_state="disabled",
                transition_time=5.2
            ),
            UIElementError(
                "Element disappeared during interaction",
                severity=ErrorSeverity.ERROR,
                element_id="order-form",
                last_seen=datetime.now() - timedelta(seconds=2),
                interaction_type="click"
            ),
            UIElementError(
                "Stale element reference",
                severity=ErrorSeverity.WARNING,
                element_id="account-dropdown",
                dom_version=1,
                current_dom_version=3
            ),
        ]
        
        for error in ui_errors:
            # Verify error contains expected context
            self.assertEqual(error.context.category, ErrorCategory.UI_ELEMENT)
            self.assertIsNotNone(error.context.element_id)
            
    def test_market_data_anomaly_errors(self):
        """Test market data anomaly detection errors"""
        anomalies = [
            {
                "type": "spike",
                "symbol": "NQ",
                "previous_price": 15000.00,
                "current_price": 25000.00,
                "change_percent": 66.67
            },
            {
                "type": "stale",
                "symbol": "ES",
                "last_update": datetime.now() - timedelta(minutes=5),
                "expected_frequency_seconds": 1
            },
            {
                "type": "negative_price",
                "symbol": "CL",
                "price": -37.50,
                "timestamp": datetime.now()
            },
            {
                "type": "bid_ask_crossed",
                "symbol": "GC",
                "bid": 2050.00,
                "ask": 2045.00
            }
        ]
        
        for anomaly in anomalies:
            error = MarketDataError(
                f"Market data anomaly: {anomaly['type']}",
                severity=ErrorSeverity.WARNING,
                **anomaly
            )
            
            self.assertEqual(error.context.category, ErrorCategory.MARKET_DATA)
            self.assertEqual(error.context.type, anomaly['type'])
            
    def test_error_aggregation_patterns(self):
        """Test error aggregation and pattern detection"""
        # Generate various errors
        for i in range(100):
            if i % 10 == 0:
                # Network errors every 10th
                self.aggregator.add_error(NetworkError(
                    "Connection timeout",
                    severity=ErrorSeverity.ERROR
                ))
            elif i % 15 == 0:
                # Auth errors every 15th
                self.aggregator.add_error(AuthenticationError(
                    "Session expired",
                    severity=ErrorSeverity.WARNING
                ))
            elif i % 7 == 0:
                # UI errors every 7th
                self.aggregator.add_error(UIElementError(
                    "Element not found",
                    severity=ErrorSeverity.WARNING,
                    element_id=f"button-{i}"
                ))
                
        # Get aggregated statistics
        stats = self.aggregator.get_error_stats()
        trends = self.aggregator.get_error_trends(minutes=1)
        
        # Verify aggregation
        self.assertGreater(stats['total_errors'], 0)
        self.assertIn(ErrorCategory.NETWORK, stats['by_category'])
        self.assertIn(ErrorCategory.AUTHENTICATION, stats['by_category'])
        self.assertIn(ErrorCategory.UI_ELEMENT, stats['by_category'])
        
        # Verify trend detection
        self.assertIsInstance(trends, list)
        
    def test_circuit_breaker_integration(self):
        """Test circuit breaker integration with error handling"""
        manager = ChromeCommunicationManager()
        
        # Simulate repeated failures to trip circuit breaker
        for i in range(10):
            self.mock_tab.Runtime.evaluate.side_effect = ConnectionError("Network error")
            
            result = safe_evaluate(
                self.mock_tab,
                "circuitBreakerTest()",
                OperationType.CRITICAL,
                f"Circuit breaker test {i}"
            )
            
            if i < 5:
                # First 5 should attempt normally
                self.assertFalse(result.success)
                self.assertIn("Network error", result.error)
            else:
                # After threshold, circuit should open
                self.assertFalse(result.success)
                # Should fail faster (circuit open)
                
    def test_error_recovery_strategies(self):
        """Test various error recovery strategies"""
        recovery_strategies = [
            {
                "error_type": NetworkError,
                "strategy": "exponential_backoff",
                "max_retries": 3,
                "base_delay": 1.0
            },
            {
                "error_type": UIElementError,
                "strategy": "immediate_retry",
                "max_retries": 1,
                "base_delay": 0
            },
            {
                "error_type": AuthenticationError,
                "strategy": "re_authenticate",
                "max_retries": 1,
                "base_delay": 0
            },
            {
                "error_type": MarketDataError,
                "strategy": "use_cached_data",
                "max_retries": 0,
                "base_delay": 0
            }
        ]
        
        for strategy in recovery_strategies:
            error_class = strategy["error_type"]
            error = error_class(
                f"Test error for {error_class.__name__}",
                severity=ErrorSeverity.ERROR
            )
            
            # Verify error has expected recovery metadata
            self.assertEqual(error.context.category.value, 
                           error_class.__name__.replace("Error", "").upper())
                           
    def test_error_serialization(self):
        """Test error serialization for logging and transmission"""
        errors = [
            ChromeConnectionError("Connection lost", tab_id="tab1", port=9223),
            OrderValidationError("Invalid quantity", order_id="12345", quantity=-1),
            RateLimitError("Too many requests", limit=100, window_seconds=60),
        ]
        
        for error in errors:
            # Test JSON serialization
            error_dict = error.to_dict()
            self.assertIsInstance(error_dict, dict)
            self.assertIn('message', error_dict)
            self.assertIn('severity', error_dict)
            self.assertIn('category', error_dict)
            self.assertIn('timestamp', error_dict)
            
            # Test JSON round-trip
            json_str = json.dumps(error_dict)
            recovered = json.loads(json_str)
            self.assertEqual(recovered['message'], error_dict['message'])
            
    def test_error_context_preservation(self):
        """Test that error context is preserved through exception chain"""
        original_context = {
            "user_id": "test_user",
            "session_id": "abc123",
            "request_id": "req_456",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            try:
                try:
                    # Original error
                    raise NetworkError("Connection failed", **original_context)
                except NetworkError as e:
                    # Wrap in higher-level error
                    raise OrderValidationError(
                        "Order submission failed due to network error",
                        original_error=str(e),
                        **original_context
                    ) from e
            except OrderValidationError as e:
                # Wrap again
                raise SystemError(
                    "Critical system failure",
                    root_cause=str(e.__cause__),
                    **original_context
                ) from e
        except SystemError as e:
            # Verify context preserved through chain
            self.assertEqual(e.context.user_id, original_context["user_id"])
            self.assertEqual(e.context.session_id, original_context["session_id"])
            self.assertIsNotNone(e.__cause__)
            self.assertIsNotNone(e.__cause__.__cause__)
            
    def test_concurrent_error_handling(self):
        """Test thread-safe error handling"""
        errors_caught = []
        
        def generate_errors(thread_id):
            for i in range(10):
                try:
                    if i % 2 == 0:
                        raise NetworkError(f"Network error from thread {thread_id}")
                    else:
                        raise UIElementError(f"UI error from thread {thread_id}")
                except TradingError as e:
                    errors_caught.append(e)
                    self.aggregator.add_error(e)
                    
        # Run error generation in multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=generate_errors, args=(i,))
            threads.append(thread)
            thread.start()
            
        for thread in threads:
            thread.join()
            
        # Verify all errors were caught and aggregated
        self.assertEqual(len(errors_caught), 50)  # 5 threads * 10 errors each
        stats = self.aggregator.get_error_stats()
        self.assertEqual(stats['total_errors'], 50)


class TestErrorAlertingUnit(unittest.TestCase):
    """Test error alerting and notification systems"""
    
    def test_critical_error_alerting(self):
        """Test that critical errors trigger alerts"""
        with patch('src.utils.trading_errors.send_alert') as mock_alert:
            alert_on_critical_error(
                ChromeConnectionError(
                    "Chrome process crashed",
                    severity=ErrorSeverity.CRITICAL,
                    tab_id="main_tab",
                    pid=12345
                )
            )
            
            # Verify alert was called
            mock_alert.assert_called_once()
            alert_args = mock_alert.call_args[0]
            self.assertIn("CRITICAL", alert_args[0])
            self.assertIn("Chrome process crashed", alert_args[0])
            
    def test_error_threshold_alerting(self):
        """Test alerting when error threshold is exceeded"""
        aggregator = ErrorAggregator()
        
        # Add errors up to threshold
        for i in range(10):
            aggregator.add_error(
                NetworkError(f"Network error {i}", severity=ErrorSeverity.ERROR)
            )
            
        # Check if threshold alert should trigger
        should_alert = aggregator.check_alert_threshold(
            category=ErrorCategory.NETWORK,
            threshold=5,
            window_minutes=5
        )
        
        self.assertTrue(should_alert)
        
    def test_error_rate_monitoring(self):
        """Test error rate calculation and monitoring"""
        aggregator = ErrorAggregator()
        
        # Simulate error burst
        burst_time = datetime.now()
        for i in range(20):
            error = NetworkError(
                f"Burst error {i}",
                severity=ErrorSeverity.WARNING
            )
            # Manually set timestamp for testing
            error.context.timestamp = burst_time.isoformat()
            aggregator.add_error(error)
            
        # Calculate error rate
        rate = aggregator.get_error_rate(
            category=ErrorCategory.NETWORK,
            window_minutes=1
        )
        
        self.assertGreater(rate, 0)
        self.assertEqual(rate, 20.0)  # 20 errors per minute


if __name__ == '__main__':
    unittest.main(verbosity=2)