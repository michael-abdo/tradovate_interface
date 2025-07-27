#!/usr/bin/env python3
"""
Comprehensive DOM Intelligence System Testing Suite
Tests validation, performance, synchronization, and emergency bypass functionality
"""

import unittest
import time
import json
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.chrome_communication import (
    DOMValidator, ValidationTier, ValidationResult, DOMOperation,
    SelectorEvolution, TradovateElementRegistry, DOMOperationQueue,
    DOMHealthMonitor, HealthStatus, PerformanceMetrics,
    CriticalOperationValidator, DOMStateSynchronizer,
    execute_auto_trade_with_validation, execute_exit_positions_with_validation,
    sync_symbol_across_tabs, sync_account_switch_across_tabs
)

class TestDOMValidator(unittest.TestCase):
    """Test DOM validation with circuit breakers and emergency bypass"""
    
    def setUp(self):
        self.validator = DOMValidator()
        # Reset circuit breakers
        self.validator.circuit_breakers.clear()
        self.validator.validation_cache.clear()
        
    def test_validation_tiers(self):
        """Test different validation tiers"""
        # Zero latency operation
        operation = DOMOperation(
            operation_id="test1",
            tab_id="tab1",
            element_type="order_submit_button",
            selector=".btn-primary",
            operation_type="click",
            validation_tier=ValidationTier.ZERO_LATENCY
        )
        
        result = self.validator.validate_operation("tab1", operation)
        self.assertIsInstance(result, ValidationResult)
        self.assertTrue(result.validation_tier == ValidationTier.ZERO_LATENCY)
        
    def test_emergency_bypass(self):
        """Test emergency bypass activation"""
        # Activate emergency bypass
        self.validator.emergency_bypass.activate_for_element(
            "order_submit_button", 
            "Market volatility", 
            duration=60
        )
        
        operation = DOMOperation(
            operation_id="test2",
            tab_id="tab1",
            element_type="order_submit_button",
            selector=".btn-primary",
            operation_type="click",
            validation_tier=ValidationTier.ZERO_LATENCY,
            emergency_bypass=True
        )
        
        result = self.validator.validate_operation("tab1", operation)
        self.assertTrue("Emergency bypass" in result.message)
        
    def test_circuit_breaker_activation(self):
        """Test circuit breaker trips after failures"""
        # Simulate multiple failures
        for i in range(6):  # Threshold is 5
            self.validator._record_validation_failure("test_element", "Test failure")
            
        # Check circuit breaker is open
        self.assertFalse(self.validator._check_dom_circuit_breaker("test_element"))
        
    def test_validation_caching(self):
        """Test validation result caching"""
        operation = DOMOperation(
            operation_id="test3",
            tab_id="tab1",
            element_type="symbol_input",
            selector="#symbolInput",
            operation_type="input",
            validation_tier=ValidationTier.LOW_LATENCY
        )
        
        # First validation
        result1 = self.validator.validate_operation("tab1", operation)
        
        # Second validation should use cache
        result2 = self.validator.validate_operation("tab1", operation)
        
        # Cache key should exist
        cache_key = f"tab1_symbol_input_{operation.selector}"
        self.assertIn(cache_key, self.validator.validation_cache)

class TestSelectorEvolution(unittest.TestCase):
    """Test adaptive selector management"""
    
    def setUp(self):
        self.selector_evolution = SelectorEvolution()
        self.selector_evolution.selector_history.clear()
        
    def test_record_success(self):
        """Test recording successful selector usage"""
        self.selector_evolution.record_success(
            "#symbolInput", 
            "symbol_input",
            {"page": "trading"}
        )
        
        # Check history
        self.assertIn("symbol_input", self.selector_evolution.selector_history)
        usage = self.selector_evolution.selector_history["symbol_input"]["#symbolInput"]
        self.assertEqual(usage.success_count, 1)
        self.assertEqual(usage.failure_count, 0)
        
    def test_record_failure(self):
        """Test recording failed selector usage"""
        self.selector_evolution.record_failure(
            ".old-selector",
            "symbol_input", 
            "Element not found",
            {"page": "trading"}
        )
        
        usage = self.selector_evolution.selector_history["symbol_input"][".old-selector"]
        self.assertEqual(usage.failure_count, 1)
        self.assertIn("Element not found", usage.failure_reasons)
        
    def test_confidence_score_calculation(self):
        """Test confidence score calculation"""
        # Record mixed results
        for i in range(7):
            self.selector_evolution.record_success("#good-selector", "test_element")
        for i in range(3):
            self.selector_evolution.record_failure("#good-selector", "test_element", "Timeout")
            
        usage = self.selector_evolution.selector_history["test_element"]["#good-selector"]
        self.assertEqual(usage.success_rate, 0.7)
        self.assertGreater(usage.confidence_score, 0)
        self.assertLess(usage.confidence_score, 1)
        
    def test_pattern_learning(self):
        """Test pattern recognition and learning"""
        # Record successes with patterns
        contexts = [
            {"page": "trading", "account": "demo1"},
            {"page": "trading", "account": "demo2"},
            {"page": "trading", "account": "live1"}
        ]
        
        for context in contexts:
            self.selector_evolution.record_success(
                'button[data-test="submit"]',
                "submit_button",
                context
            )
            
        # Learn patterns
        self.selector_evolution.learn_selector_patterns("submit_button")
        
        patterns = self.selector_evolution.pattern_recognizer.element_patterns.get("submit_button", {})
        self.assertIn("attribute_patterns", patterns)
        self.assertIn("context_patterns", patterns)

class TestTradovateElementRegistry(unittest.TestCase):
    """Test element registry with fallback strategies"""
    
    def setUp(self):
        self.registry = TradovateElementRegistry()
        
    def test_get_element_strategy(self):
        """Test retrieving element strategies"""
        strategy = self.registry.get_element_strategy("order_submit_button")
        
        self.assertIsNotNone(strategy)
        self.assertEqual(strategy.validation_tier, ValidationTier.ZERO_LATENCY)
        self.assertTrue(strategy.emergency_bypass)
        self.assertTrue(len(strategy.primary_selectors) > 0)
        self.assertTrue(len(strategy.fallback_selectors) > 0)
        
    def test_critical_element_detection(self):
        """Test critical element identification"""
        self.assertTrue(self.registry.is_critical_element("order_submit_button"))
        self.assertTrue(self.registry.is_critical_element("position_exit_button"))
        self.assertFalse(self.registry.is_critical_element("notification_area"))
        
    def test_emergency_bypass_requirements(self):
        """Test emergency bypass requirements"""
        self.assertTrue(self.registry.requires_emergency_bypass("order_submit_button"))
        self.assertFalse(self.registry.requires_emergency_bypass("account_selector"))

class TestDOMOperationQueue(unittest.TestCase):
    """Test DOM operation queueing and race condition prevention"""
    
    def setUp(self):
        self.queue = DOMOperationQueue(max_workers=2)
        # Register test tabs
        self.queue.tab_sync_manager.register_tab("tab1", "account1")
        self.queue.tab_sync_manager.register_tab("tab2", "account2")
        
    def tearDown(self):
        self.queue.shutdown()
        
    def test_queue_operation(self):
        """Test basic operation queueing"""
        operation = DOMOperation(
            operation_id="test1",
            tab_id="tab1",
            element_type="symbol_input",
            selector="#symbolInput",
            operation_type="input",
            parameters={"value": "NQ"}
        )
        
        result = self.queue.queue_operation(operation)
        self.assertEqual(result.status, "queued")
        self.assertIsNotNone(result.operation_id)
        
    def test_conflict_detection(self):
        """Test cross-tab conflict detection"""
        # Queue account switch on tab1
        operation1 = DOMOperation(
            operation_id="test2",
            tab_id="tab1",
            element_type="account_selector",
            selector=".account-dropdown",
            operation_type="click"
        )
        
        result1 = self.queue.queue_operation(operation1)
        self.assertEqual(result1.status, "queued")
        
        # Try to queue conflicting operation on tab2
        operation2 = DOMOperation(
            operation_id="test3",
            tab_id="tab2",
            element_type="account_selector",
            selector=".account-dropdown",
            operation_type="click"
        )
        
        # This should detect conflict
        conflicts = self.queue.tab_sync_manager.get_tab_conflicts(operation2)
        self.assertTrue(len(conflicts) > 0)
        
    def test_performance_tracking(self):
        """Test operation performance tracking"""
        operation = DOMOperation(
            operation_id="test4",
            tab_id="tab1",
            element_type="symbol_input",
            selector="#symbolInput",
            operation_type="input"
        )
        
        # Queue and wait briefly
        self.queue.queue_operation(operation)
        time.sleep(0.1)
        
        # Check metrics
        stats = self.queue.get_queue_stats()
        self.assertIn("active_operations", stats)
        self.assertIn("average_execution_times", stats)

class TestDOMHealthMonitor(unittest.TestCase):
    """Test DOM health monitoring and degradation detection"""
    
    def setUp(self):
        self.monitor = DOMHealthMonitor()
        
    def test_record_operation_metric(self):
        """Test recording operation metrics"""
        metric = PerformanceMetrics(
            timestamp=datetime.now(),
            element_type="order_submit_button",
            operation_type="click",
            execution_time=0.1,
            validation_time=0.01,
            queue_wait_time=0.05,
            success=True
        )
        
        self.monitor.record_operation_metric(metric)
        
        # Check counters
        self.assertEqual(self.monitor.performance_counters["total_operations"], 1)
        self.assertEqual(self.monitor.performance_counters["successful_operations"], 1)
        
    def test_health_status_calculation(self):
        """Test system health status calculation"""
        # Record mostly successful operations
        for i in range(8):
            self.monitor.record_operation_metric(PerformanceMetrics(
                timestamp=datetime.now(),
                element_type="test_element",
                operation_type="click",
                execution_time=0.1,
                validation_time=0.01,
                queue_wait_time=0.05,
                success=True
            ))
            
        # Record some failures
        for i in range(2):
            self.monitor.record_operation_metric(PerformanceMetrics(
                timestamp=datetime.now(),
                element_type="test_element",
                operation_type="click",
                execution_time=0.1,
                validation_time=0.01,
                queue_wait_time=0.05,
                success=False
            ))
            
        status = self.monitor.check_system_health()
        self.assertIn(status, [HealthStatus.HEALTHY, HealthStatus.WARNING])
        
    def test_degradation_detection(self):
        """Test performance degradation detection"""
        # Establish baseline with fast operations
        for i in range(50):
            self.monitor.degradation_detector.add_metric(PerformanceMetrics(
                timestamp=datetime.now(),
                element_type="test_element",
                operation_type="click",
                execution_time=0.1,  # 100ms baseline
                validation_time=0.01,
                queue_wait_time=0.05,
                success=True
            ))
            
        # Add degraded performance
        for i in range(10):
            self.monitor.degradation_detector.add_metric(PerformanceMetrics(
                timestamp=datetime.now(),
                element_type="test_element",
                operation_type="click",
                execution_time=0.5,  # 500ms - degraded
                validation_time=0.01,
                queue_wait_time=0.05,
                success=True
            ))
            
        # Check for degradation alerts
        alerts = self.monitor.degradation_detector.detect_degradation("test_element_click")
        self.assertTrue(len(alerts) > 0)

class TestCriticalOperationValidator(unittest.TestCase):
    """Test critical operation validation with emergency bypass"""
    
    def setUp(self):
        self.validator = CriticalOperationValidator()
        
    def test_emergency_bypass_conditions(self):
        """Test emergency bypass decision making"""
        # Normal conditions
        should_bypass, reason = self.validator.should_bypass_validation(
            "auto_trade", 
            {"market_volatility": 0.02}
        )
        self.assertFalse(should_bypass)
        
        # High volatility
        should_bypass, reason = self.validator.should_bypass_validation(
            "auto_trade",
            {"market_volatility": 0.06}  # > 5% threshold
        )
        self.assertTrue(should_bypass)
        self.assertIn("volatility", reason.lower())
        
        # Manual override
        self.validator.enable_manual_emergency_override("Testing")
        should_bypass, reason = self.validator.should_bypass_validation("auto_trade")
        self.assertTrue(should_bypass)
        self.assertIn("manual", reason.lower())
        
    def test_critical_operation_validation(self):
        """Test validation of critical trading operations"""
        with patch('src.utils.chrome_communication.default_dom_validator') as mock_validator:
            mock_validator.validate_operation.return_value = ValidationResult(
                success=True,
                message="Validation successful"
            )
            
            result = self.validator.validate_critical_operation(
                "auto_trade",
                "tab1",
                {
                    "symbol": "NQ",
                    "quantity": 1,
                    "action": "Buy"
                }
            )
            
            self.assertTrue(result["success"])
            self.assertFalse(result["emergency_bypass"])
            
    def test_performance_metrics_update(self):
        """Test critical operation performance tracking"""
        # Simulate operations
        for i in range(10):
            self.validator._update_operation_metrics(
                "auto_trade",
                0.1,  # 100ms
                True  # success
            )
            
        metrics = self.validator.critical_operation_metrics["auto_trade"]
        self.assertEqual(metrics["count"], 10)
        self.assertGreater(metrics["avg_time"], 0)
        self.assertEqual(metrics["success_rate"], 1.0)

class TestDOMStateSynchronizer(unittest.TestCase):
    """Test DOM state synchronization across tabs"""
    
    def setUp(self):
        self.synchronizer = DOMStateSynchronizer()
        # Register test tabs
        self.synchronizer.tab_sync_manager.register_tab("tab1", "account1")
        self.synchronizer.tab_sync_manager.register_tab("tab2", "account1")
        self.synchronizer.tab_sync_manager.register_tab("tab3", "account2")
        
        # Enable auto-sync for all tabs
        for tab_id in ["tab1", "tab2", "tab3"]:
            self.synchronizer.enable_auto_sync(tab_id)
            self.synchronizer.tab_sync_manager.tab_states[tab_id].is_trading_active = True
            
    def test_symbol_sync(self):
        """Test symbol synchronization across tabs"""
        result = self.synchronizer.sync_dom_state_across_tabs(
            "tab1",
            "symbol_change",
            {"symbol": "ES"},
            priority="high"
        )
        
        self.assertIn("sync_id", result)
        self.assertEqual(result["state_type"], "symbol_change")
        self.assertEqual(result["source_tab"], "tab1")
        
        # Should sync to tab2 (same account, auto-sync enabled)
        # May or may not sync to tab3 (different account)
        self.assertTrue(len(result["synced_tabs"]) >= 1)
        
    def test_account_switch_sync(self):
        """Test account switch synchronization"""
        result = self.synchronizer.sync_dom_state_across_tabs(
            "tab1",
            "account_switch",
            {"account_name": "account3"},
            priority="critical"
        )
        
        self.assertEqual(result["state_type"], "account_switch")
        # Account switches should affect all tabs
        
    def test_conflict_detection(self):
        """Test sync conflict detection"""
        # Start first sync
        thread1_result = {}
        def sync1():
            thread1_result["result"] = self.synchronizer.sync_dom_state_across_tabs(
                "tab1",
                "symbol_change",
                {"symbol": "NQ"},
                priority="normal"
            )
            
        thread1 = threading.Thread(target=sync1)
        thread1.start()
        
        # Try conflicting sync immediately
        time.sleep(0.01)  # Small delay to ensure first sync starts
        result2 = self.synchronizer.sync_dom_state_across_tabs(
            "tab2",
            "symbol_change",
            {"symbol": "ES"},  # Different symbol
            priority="normal"
        )
        
        # Should detect conflict
        self.assertTrue(len(result2["conflicts"]) > 0)
        
        thread1.join()
        
    def test_sync_performance_tracking(self):
        """Test synchronization performance metrics"""
        # Perform multiple syncs
        for i in range(5):
            self.synchronizer.sync_dom_state_across_tabs(
                "tab1",
                "symbol_change",
                {"symbol": f"TEST{i}"},
                priority="normal"
            )
            
        status = self.synchronizer.get_sync_status()
        self.assertEqual(status["metrics"]["total_syncs"], 5)
        self.assertGreater(status["metrics"]["avg_sync_time"], 0)

class TestIntegrationScenarios(unittest.TestCase):
    """Test real-world integration scenarios"""
    
    def setUp(self):
        # Create mock Chrome tab
        self.mock_tab = Mock()
        self.mock_tab.id = "test_tab_1"
        self.mock_tab.Runtime.evaluate.return_value = {
            "result": {"value": "Success"}
        }
        
    def test_auto_trade_with_validation(self):
        """Test complete auto trade flow with validation"""
        with patch('src.utils.chrome_communication.default_critical_validator') as mock_validator:
            mock_validator.validate_critical_operation.return_value = {
                "success": True,
                "emergency_bypass": False,
                "validation_time": 5.0,
                "message": "Validation successful"
            }
            
            result = execute_auto_trade_with_validation(
                self.mock_tab,
                symbol="NQ",
                quantity=1,
                action="Buy",
                tp_ticks=10,
                sl_ticks=5,
                tick_size=0.25,
                context={"market_volatility": 0.02}
            )
            
            self.assertIn("validation_result", result)
            self.assertIn("execution_result", result)
            self.assertTrue(result["dom_intelligence_enabled"])
            
    def test_emergency_position_exit(self):
        """Test emergency position exit scenario"""
        with patch('src.utils.chrome_communication.default_critical_validator') as mock_validator:
            mock_validator.validate_critical_operation.return_value = {
                "success": True,
                "emergency_bypass": True,
                "validation_time": 1.0,
                "message": "Emergency bypass: High market volatility"
            }
            
            result = execute_exit_positions_with_validation(
                self.mock_tab,
                symbol="ES",
                option="cancel-option-Exit-at-Mkt-Cxl",
                context={
                    "market_volatility": 0.08,  # 8% - high volatility
                    "position_exit": True
                }
            )
            
            validation_result = result.get("validation_result", {})
            self.assertTrue(validation_result.get("emergency_bypass", False))

class TestPerformanceBenchmarks(unittest.TestCase):
    """Performance benchmarks to ensure <10ms overhead"""
    
    def setUp(self):
        self.validator = DOMValidator()
        self.registry = TradovateElementRegistry()
        
    def test_validation_performance(self):
        """Test validation performance for critical operations"""
        operation = DOMOperation(
            operation_id="perf_test",
            tab_id="tab1",
            element_type="order_submit_button",
            selector=".btn-primary",
            operation_type="click",
            validation_tier=ValidationTier.ZERO_LATENCY,
            emergency_bypass=True
        )
        
        # Warm up
        for _ in range(10):
            self.validator.validate_operation("tab1", operation)
            
        # Measure
        times = []
        for _ in range(100):
            start = time.perf_counter()
            self.validator.validate_operation("tab1", operation)
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to ms
            
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        print(f"\nValidation Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Max: {max_time:.2f}ms")
        print(f"  Min: {min(times):.2f}ms")
        
        # Zero-latency operations should be < 10ms on average
        self.assertLess(avg_time, 10.0)
        
    def test_emergency_bypass_performance(self):
        """Test emergency bypass performance"""
        validator = CriticalOperationValidator()
        
        # Enable emergency override
        validator.enable_manual_emergency_override("Performance test")
        
        times = []
        for _ in range(100):
            start = time.perf_counter()
            should_bypass, reason = validator.should_bypass_validation(
                "auto_trade",
                {"test": True}
            )
            end = time.perf_counter()
            times.append((end - start) * 1000)
            
        avg_time = sum(times) / len(times)
        
        print(f"\nEmergency Bypass Decision Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        
        # Emergency bypass decision should be < 1ms
        self.assertLess(avg_time, 1.0)


def run_performance_suite():
    """Run only performance-critical tests"""
    suite = unittest.TestSuite()
    suite.addTest(TestPerformanceBenchmarks('test_validation_performance'))
    suite.addTest(TestPerformanceBenchmarks('test_emergency_bypass_performance'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)
    
    # Or run only performance tests:
    # run_performance_suite()