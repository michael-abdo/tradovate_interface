#!/usr/bin/env python3
"""
Phase 2 Test Script - Startup Monitoring Implementation Tests
Tests the comprehensive Chrome startup monitoring and validation functionality
"""

import os
import sys
import time
import unittest
import tempfile
import subprocess
import json
from pathlib import Path

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import test modules
from enhanced_startup_manager import StartupManager, StartupValidationError
from structured_logger import get_logger

# Import process monitor if available
try:
    sys.path.insert(0, os.path.join(project_root, 'tradovate_interface', 'src'))
    from utils.process_monitor import ChromeProcessMonitor, StartupMonitoringMode
    PROCESS_MONITOR_AVAILABLE = True
except ImportError:
    PROCESS_MONITOR_AVAILABLE = False


class TestPhase2StartupMonitoring(unittest.TestCase):
    """Test Phase 2 startup monitoring implementation"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_logger = get_logger("test_phase2", log_file="test_logs/phase2_test.log")
        self.startup_manager = StartupManager()
        
        # Create temporary directory for test artifacts
        self.test_dir = tempfile.mkdtemp(prefix="chrome_startup_test_")
        
    def tearDown(self):
        """Clean up test environment"""
        pass
    
    def test_startup_monitoring_configuration(self):
        """Test startup monitoring configuration loading"""
        self.test_logger.info("Testing startup monitoring configuration")
        
        config = self.startup_manager.config
        self.assertIn('startup_monitoring', config, "Startup monitoring config should exist")
        
        startup_config = config['startup_monitoring']
        
        # Test required configuration keys
        required_keys = [
            'enabled', 'startup_timeout_seconds', 'startup_retry_attempts',
            'startup_phases', 'startup_failure_actions', 'startup_metrics'
        ]
        for key in required_keys:
            self.assertIn(key, startup_config, f"Configuration should contain {key}")
        
        # Test startup phases configuration
        phases_config = startup_config.get('startup_phases', {})
        expected_phases = ['chrome_launch', 'page_load', 'authentication', 'trading_interface']
        for phase in expected_phases:
            self.assertIn(phase, phases_config, f"Phase {phase} should be configured")
            
            phase_config = phases_config[phase]
            self.assertIn('timeout_seconds', phase_config)
            self.assertIn('validation_required', phase_config)
        
        self.test_logger.info("Startup monitoring configuration validated")
    
    def test_chrome_process_validation(self):
        """Test Chrome process validation"""
        self.test_logger.info("Testing Chrome process validation")
        
        # Test the validation method (will likely fail since no Chrome instances are running)
        result = self.startup_manager.validate_chrome_processes()
        self.assertIsInstance(result, bool, "Chrome process validation should return boolean")
        
        # Check log entries
        process_events = [e for e in self.startup_manager.startup_log 
                         if 'chrome_process_validation' in e['event']]
        self.assertTrue(len(process_events) > 0, "Chrome process validation events should be logged")
        
        if result:
            self.test_logger.info("Chrome process validation passed")
        else:
            self.test_logger.info("Chrome process validation failed (expected in test environment)")
    
    def test_websocket_connection_validation(self):
        """Test WebSocket connection validation"""
        self.test_logger.info("Testing WebSocket connection validation")
        
        # Test the validation method (will likely fail since no Chrome instances are running)
        result = self.startup_manager.validate_websocket_connections()
        self.assertIsInstance(result, bool, "WebSocket validation should return boolean")
        
        # Check log entries
        websocket_events = [e for e in self.startup_manager.startup_log 
                           if 'websocket_validation' in e['event']]
        self.assertTrue(len(websocket_events) > 0, "WebSocket validation events should be logged")
        
        if result:
            self.test_logger.info("WebSocket validation passed")
        else:
            self.test_logger.info("WebSocket validation failed (expected in test environment)")
    
    def test_startup_completion_validation(self):
        """Test startup completion validation suite"""
        self.test_logger.info("Testing startup completion validation")
        
        # Clear previous logs
        initial_log_count = len(self.startup_manager.startup_log)
        
        result = self.startup_manager.validate_startup_completion()
        self.assertIsInstance(result, bool, "Startup completion validation should return boolean")
        
        # Check that validation events were logged
        new_events = self.startup_manager.startup_log[initial_log_count:]
        completion_events = [e for e in new_events if 'completion' in e['event']]
        self.assertTrue(len(completion_events) > 0, "Completion validation events should be logged")
        
        if result:
            self.test_logger.info("Startup completion validation passed")
        else:
            self.test_logger.info("Startup completion validation failed (expected without running Chrome)")
    
    def test_startup_phase_context_manager(self):
        """Test startup phase context manager"""
        self.test_logger.info("Testing startup phase context manager")
        
        initial_log_count = len(self.startup_manager.startup_log)
        
        # Test successful phase
        with self.startup_manager.startup_phase("test_phase"):
            time.sleep(0.1)  # Simulate some work
        
        # Test failed phase
        try:
            with self.startup_manager.startup_phase("test_failure_phase"):
                raise Exception("Test exception")
        except Exception:
            pass  # Expected
        
        # Check log entries
        new_events = self.startup_manager.startup_log[initial_log_count:]
        phase_events = [e for e in new_events if 'test_phase' in e['event']]
        self.assertTrue(len(phase_events) >= 2, "Should have start and complete/failed events")
        
        # Check for start and complete events
        start_events = [e for e in phase_events if e['event'].endswith('_start')]
        end_events = [e for e in phase_events if e['event'].endswith('_complete') or e['event'].endswith('_failed')]
        
        self.assertTrue(len(start_events) >= 1, "Should have start events")
        self.assertTrue(len(end_events) >= 1, "Should have end events")
        
        # Check that successful phase has duration logged
        complete_events = [e for e in end_events if e['event'].endswith('_complete')]
        if complete_events:
            self.assertIn('duration_seconds', complete_events[0], "Complete events should have duration")
    
    def test_startup_event_logging(self):
        """Test comprehensive startup event logging"""
        self.test_logger.info("Testing startup event logging")
        
        initial_log_count = len(self.startup_manager.startup_log)
        
        # Log various types of events
        self.startup_manager.log_event("test_info", "Information event", True, test_data="info")
        self.startup_manager.log_event("test_warning", "Warning event", True, test_data="warning")
        self.startup_manager.log_event("test_error", "Error event", False, test_data="error", error_code=500)
        
        # Check log entries
        new_events = self.startup_manager.startup_log[initial_log_count:]
        self.assertEqual(len(new_events), 3, "Should have 3 new events")
        
        # Verify event structure
        for event in new_events:
            required_fields = ['timestamp', 'event', 'details', 'success', 'attempt']
            for field in required_fields:
                self.assertIn(field, event, f"Event should contain {field}")
            
            # Check timestamp format
            self.assertIsInstance(event['timestamp'], str)
            self.assertTrue(len(event['timestamp']) > 0)
            
            # Check success field matches expected
            if 'error' in event['event']:
                self.assertFalse(event['success'])
            else:
                self.assertTrue(event['success'])
    
    def test_startup_report_comprehensive(self):
        """Test comprehensive startup report generation"""
        self.test_logger.info("Testing comprehensive startup report")
        
        # Generate some events
        self.startup_manager.log_event("report_test_1", "Test event 1", True)
        self.startup_manager.log_event("report_test_2", "Test event 2", True)
        self.startup_manager.log_event("report_test_3", "Test event 3", False)
        
        # Generate report
        report = self.startup_manager.get_startup_report()
        
        # Verify report structure
        required_sections = ['stats', 'total_events', 'success_events', 'failure_events', 'events', 'config']
        for section in required_sections:
            self.assertIn(section, report, f"Report should contain {section}")
        
        # Verify statistics
        self.assertIsInstance(report['total_events'], int)
        self.assertIsInstance(report['success_events'], int)
        self.assertIsInstance(report['failure_events'], int)
        
        # Verify event counts match
        actual_total = len(report['events'])
        actual_success = len([e for e in report['events'] if e['success']])
        actual_failure = len([e for e in report['events'] if not e['success']])
        
        self.assertEqual(report['total_events'], actual_total)
        self.assertEqual(report['success_events'], actual_success)
        self.assertEqual(report['failure_events'], actual_failure)
        
        # Test report saving with JSON validation
        report_file = self.startup_manager.save_startup_report()
        self.assertTrue(os.path.exists(report_file), "Report file should be created")
        
        # Validate JSON structure
        with open(report_file, 'r') as f:
            saved_report = json.load(f)
            self.assertEqual(saved_report['total_events'], report['total_events'])
        
        self.test_logger.info(f"Comprehensive report saved to: {report_file}")
    
    @unittest.skipUnless(PROCESS_MONITOR_AVAILABLE, "Process monitor not available")
    def test_process_monitor_integration(self):
        """Test process monitor integration for startup monitoring"""
        self.test_logger.info("Testing process monitor integration")
        
        if self.startup_manager.process_monitor is not None:
            # Test startup monitoring mode setting
            original_mode = getattr(self.startup_manager.process_monitor, '_startup_mode', None)
            
            try:
                # Test enabling startup monitoring
                self.startup_manager.process_monitor.enable_startup_monitoring(StartupMonitoringMode.ACTIVE)
                
                # Test account registration
                self.startup_manager.register_accounts_for_monitoring()
                
                # Check for registration events in log
                registration_events = [e for e in self.startup_manager.startup_log 
                                     if 'monitor_registration' in e['event']]
                self.assertTrue(len(registration_events) > 0, "Registration events should be logged")
                
                self.test_logger.info("Process monitor integration test completed")
                
            finally:
                # Restore original mode if it existed
                if original_mode is not None:
                    self.startup_manager.process_monitor.enable_startup_monitoring(original_mode)
        else:
            self.test_logger.warning("Process monitor not available for integration test")
    
    def test_startup_failure_handling(self):
        """Test startup failure handling and retry logic"""
        self.test_logger.info("Testing startup failure handling")
        
        # Test failure handling without actual retry
        test_error = Exception("Test startup failure")
        
        # Handle a test failure
        self.startup_manager.handle_startup_failure(test_error, attempt=1, is_final=False)
        
        # Check that failure was logged
        failure_events = [e for e in self.startup_manager.startup_log 
                         if 'attempt_failed' in e['event']]
        self.assertTrue(len(failure_events) > 0, "Failure events should be logged")
        
        # Check failure event details
        failure_event = failure_events[-1]
        self.assertFalse(failure_event['success'])
        self.assertIn('error', failure_event)
        self.assertIn('attempt', failure_event)
        
        self.test_logger.info("Startup failure handling test completed")
    
    def test_startup_configuration_validation(self):
        """Test startup configuration validation"""
        self.test_logger.info("Testing startup configuration validation")
        
        config = self.startup_manager.config
        startup_config = config.get('startup_monitoring', {})
        
        # Test timeout values are reasonable
        startup_timeout = startup_config.get('startup_timeout_seconds', 0)
        self.assertGreater(startup_timeout, 0, "Startup timeout should be positive")
        self.assertLess(startup_timeout, 600, "Startup timeout should be reasonable (< 10 minutes)")
        
        # Test retry configuration
        retry_attempts = startup_config.get('startup_retry_attempts', 0)
        self.assertGreater(retry_attempts, 0, "Retry attempts should be positive")
        self.assertLess(retry_attempts, 10, "Retry attempts should be reasonable (< 10)")
        
        # Test phase timeouts
        phases = startup_config.get('startup_phases', {})
        for phase_name, phase_config in phases.items():
            timeout = phase_config.get('timeout_seconds', 0)
            self.assertGreater(timeout, 0, f"Phase {phase_name} timeout should be positive")
            self.assertLess(timeout, 300, f"Phase {phase_name} timeout should be reasonable (< 5 minutes)")
        
        self.test_logger.info("Configuration validation completed")
    
    def test_startup_metrics_collection(self):
        """Test startup metrics collection"""
        self.test_logger.info("Testing startup metrics collection")
        
        # Test that startup stats are initialized
        stats = self.startup_manager.startup_stats
        self.assertIsInstance(stats, dict)
        
        required_stats = ['start_time', 'end_time', 'attempts', 'success', 'errors']
        for stat in required_stats:
            self.assertIn(stat, stats, f"Stats should contain {stat}")
        
        # Test stats initialization values
        self.assertIsNone(stats['start_time'])  # Should be None before startup
        self.assertIsNone(stats['end_time'])    # Should be None before completion
        self.assertEqual(stats['attempts'], 0)   # Should start at 0
        self.assertFalse(stats['success'])      # Should start as False
        self.assertIsInstance(stats['errors'], list)  # Should be a list
        
        self.test_logger.info("Metrics collection test completed")


class TestPhase2Integration(unittest.TestCase):
    """Test Phase 2 integration scenarios"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.test_logger = get_logger("test_phase2_integration", log_file="test_logs/phase2_integration.log")
    
    def test_enhanced_startup_manager_initialization(self):
        """Test enhanced startup manager initialization"""
        self.test_logger.info("Testing enhanced startup manager initialization")
        
        try:
            startup_manager = StartupManager()
            
            # Test that all components are initialized
            self.assertIsNotNone(startup_manager.config)
            self.assertIsNotNone(startup_manager.chrome_finder)
            self.assertIsNotNone(startup_manager.chrome_cleanup)
            self.assertIsNotNone(startup_manager.startup_log)
            self.assertIsNotNone(startup_manager.startup_stats)
            
            # Test required ports are set
            self.assertIsInstance(startup_manager.required_ports, list)
            self.assertTrue(len(startup_manager.required_ports) > 0)
            
            self.test_logger.info("Enhanced startup manager initialized successfully")
            
        except Exception as e:
            self.fail(f"Enhanced startup manager initialization failed: {e}")
    
    def test_startup_validation_chain(self):
        """Test complete startup validation chain"""
        self.test_logger.info("Testing startup validation chain")
        
        startup_manager = StartupManager()
        
        # Test prerequisite validation
        prereq_result = startup_manager.validate_startup_prerequisites()
        self.assertIsInstance(prereq_result, bool)
        
        # Test completion validation (will fail without Chrome running)
        completion_result = startup_manager.validate_startup_completion()
        self.assertIsInstance(completion_result, bool)
        
        # Verify logging occurred for both validation chains
        all_events = startup_manager.startup_log
        prereq_events = [e for e in all_events if 'prerequisite' in e['event']]
        completion_events = [e for e in all_events if 'completion' in e['event']]
        
        self.assertTrue(len(prereq_events) > 0, "Prerequisite validation should be logged")
        self.assertTrue(len(completion_events) > 0, "Completion validation should be logged")
        
        self.test_logger.info("Startup validation chain test completed")


def run_phase2_tests():
    """Run all Phase 2 tests"""
    print("🧪 Running Phase 2 Startup Monitoring Tests\n")
    
    # Create test logs directory
    os.makedirs("test_logs", exist_ok=True)
    
    # Create test suite
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTests(loader.loadTestsFromTestCase(TestPhase2StartupMonitoring))
    test_suite.addTests(loader.loadTestsFromTestCase(TestPhase2Integration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total_tests - failures - errors
    
    print(f"\n📊 Phase 2 Test Results:")
    print(f"   Total tests: {total_tests}")
    print(f"   Passed: {passed}")
    print(f"   Failed: {failures}")
    print(f"   Errors: {errors}")
    
    if failures > 0:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if errors > 0:
        print(f"\n💥 Errors:")
        for test, traceback in result.errors:
            print(f"   {test}: {traceback.split('Exception:')[-1].strip()}")
    
    success = failures == 0 and errors == 0
    status = "✅ PASSED" if success else "❌ FAILED"
    print(f"\nPhase 2 Tests: {status}")
    
    return success


if __name__ == "__main__":
    success = run_phase2_tests()
    sys.exit(0 if success else 1)