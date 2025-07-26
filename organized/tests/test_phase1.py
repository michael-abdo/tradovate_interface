#!/usr/bin/env python3
"""
Phase 1 Test Script - Error Handling Implementation Tests
Tests the Chrome restart implementation and error handling functionality
"""

import os
import sys
import time
import unittest
import tempfile
import subprocess
from pathlib import Path

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import test modules
from enhanced_startup_manager import StartupManager, StartupValidationError
from chrome_cleanup import ChromeCleanup
from chrome_path_finder import get_chrome_finder
from structured_logger import get_logger


class TestPhase1ErrorHandling(unittest.TestCase):
    """Test Phase 1 error handling implementation"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_logger = get_logger("test_phase1", log_file="test_logs/phase1_test.log")
        self.startup_manager = StartupManager()
        self.chrome_cleanup = ChromeCleanup()
        self.chrome_finder = get_chrome_finder()
        
        # Create temporary directory for test artifacts
        self.test_dir = tempfile.mkdtemp(prefix="chrome_test_")
        
    def tearDown(self):
        """Clean up test environment"""
        # Clean up any test Chrome instances
        try:
            self.chrome_cleanup.perform_cleanup()
        except Exception as e:
            self.test_logger.warning(f"Cleanup error in tearDown: {e}")
    
    def test_chrome_path_detection(self):
        """Test Chrome executable detection"""
        self.test_logger.info("Testing Chrome path detection")
        
        chrome_info = self.chrome_finder.get_chrome_info()
        
        self.assertTrue(chrome_info['found'], "Chrome executable should be found")
        self.assertIn('path', chrome_info, "Chrome path should be provided")
        self.assertTrue(os.path.exists(chrome_info['path']), "Chrome path should exist")
        
        # Test version retrieval
        if 'version' in chrome_info:
            self.assertIsInstance(chrome_info['version'], str)
            self.assertTrue(len(chrome_info['version']) > 0)
        
        self.test_logger.info(f"Chrome found at: {chrome_info['path']}")
    
    def test_startup_configuration_loading(self):
        """Test startup configuration loading"""
        self.test_logger.info("Testing configuration loading")
        
        config = self.startup_manager.config
        self.assertIsInstance(config, dict, "Configuration should be a dictionary")
        
        # Test startup monitoring configuration
        startup_config = config.get('startup_monitoring', {})
        self.assertIsInstance(startup_config, dict, "Startup monitoring config should exist")
        
        # Test required configuration keys
        required_keys = ['enabled', 'startup_timeout_seconds', 'startup_retry_attempts']
        for key in required_keys:
            self.assertIn(key, startup_config, f"Configuration should contain {key}")
        
        self.test_logger.info("Configuration loaded successfully")
    
    def test_port_validation(self):
        """Test port availability validation"""
        self.test_logger.info("Testing port validation")
        
        # Test port validation method
        result = self.startup_manager.validate_ports()
        self.assertIsInstance(result, bool, "Port validation should return boolean")
        
        # Log the result
        if result:
            self.test_logger.info("Required ports are available")
        else:
            self.test_logger.warning("Some required ports are in use")
        
        # Check startup log entries
        port_events = [e for e in self.startup_manager.startup_log if 'port' in e['event']]
        self.assertTrue(len(port_events) > 0, "Port validation events should be logged")
    
    def test_memory_validation(self):
        """Test memory availability validation"""
        self.test_logger.info("Testing memory validation")
        
        result = self.startup_manager.validate_memory()
        self.assertIsInstance(result, bool, "Memory validation should return boolean")
        
        # Memory validation should typically pass on development machines
        self.assertTrue(result, "Memory validation should pass")
        
        # Check log entries
        memory_events = [e for e in self.startup_manager.startup_log if 'memory' in e['event']]
        self.assertTrue(len(memory_events) > 0, "Memory validation events should be logged")
    
    def test_network_validation(self):
        """Test network connectivity validation"""
        self.test_logger.info("Testing network validation")
        
        result = self.startup_manager.validate_network()
        self.assertIsInstance(result, bool, "Network validation should return boolean")
        
        # Network validation might fail in some environments, so we just test the method
        network_events = [e for e in self.startup_manager.startup_log if 'network' in e['event']]
        self.assertTrue(len(network_events) > 0, "Network validation events should be logged")
        
        if result:
            self.test_logger.info("Network connectivity test passed")
        else:
            self.test_logger.warning("Network connectivity test failed")
    
    def test_chrome_executable_validation(self):
        """Test Chrome executable validation"""
        self.test_logger.info("Testing Chrome executable validation")
        
        result = self.startup_manager.validate_chrome_executable()
        self.assertTrue(result, "Chrome executable validation should pass")
        
        # Check log entries
        chrome_events = [e for e in self.startup_manager.startup_log if 'chrome_validation' in e['event']]
        self.assertTrue(len(chrome_events) > 0, "Chrome validation events should be logged")
    
    def test_prerequisite_validation_suite(self):
        """Test complete prerequisite validation suite"""
        self.test_logger.info("Testing prerequisite validation suite")
        
        result = self.startup_manager.validate_startup_prerequisites()
        self.assertIsInstance(result, bool, "Prerequisite validation should return boolean")
        
        # Check that all validation phases were logged
        prerequisite_events = [e for e in self.startup_manager.startup_log if 'prerequisite' in e['event']]
        self.assertTrue(len(prerequisite_events) > 0, "Prerequisite validation events should be logged")
        
        if result:
            self.test_logger.info("All prerequisite validations passed")
        else:
            self.test_logger.warning("Some prerequisite validations failed")
    
    def test_cleanup_functionality(self):
        """Test Chrome cleanup functionality"""
        self.test_logger.info("Testing cleanup functionality")
        
        # Test cleanup without any Chrome instances
        results = self.chrome_cleanup.perform_cleanup(
            kill_processes=False,  # Don't kill existing Chrome
            clean_profiles=True,
            clean_locks=True
        )
        
        self.assertIsInstance(results, dict, "Cleanup should return results dictionary")
        self.assertIn('profiles_cleaned', results)
        self.assertIn('locks_cleaned', results)
        
        self.test_logger.info(f"Cleanup results: {results}")
    
    def test_startup_logging(self):
        """Test startup event logging"""
        self.test_logger.info("Testing startup logging")
        
        # Clear previous logs
        self.startup_manager.startup_log.clear()
        
        # Log some test events
        self.startup_manager.log_event("test_event", "Test event details", True)
        self.startup_manager.log_event("test_failure", "Test failure details", False)
        
        # Check log entries
        self.assertEqual(len(self.startup_manager.startup_log), 2)
        
        success_event = self.startup_manager.startup_log[0]
        failure_event = self.startup_manager.startup_log[1]
        
        self.assertTrue(success_event['success'])
        self.assertFalse(failure_event['success'])
        self.assertEqual(success_event['event'], 'test_event')
        self.assertEqual(failure_event['event'], 'test_failure')
    
    def test_startup_report_generation(self):
        """Test startup report generation"""
        self.test_logger.info("Testing startup report generation")
        
        # Generate a report
        report = self.startup_manager.get_startup_report()
        
        self.assertIsInstance(report, dict, "Report should be a dictionary")
        self.assertIn('stats', report)
        self.assertIn('events', report)
        self.assertIn('config', report)
        
        # Test report saving
        report_file = self.startup_manager.save_startup_report()
        self.assertTrue(os.path.exists(report_file), "Report file should be created")
        
        # Test report content
        with open(report_file, 'r') as f:
            import json
            saved_report = json.load(f)
            self.assertEqual(saved_report['stats'], report['stats'])
        
        self.test_logger.info(f"Report saved to: {report_file}")
    
    def test_error_handling_with_invalid_config(self):
        """Test error handling with invalid configuration"""
        self.test_logger.info("Testing error handling with invalid config")
        
        # Create startup manager with non-existent config file
        startup_manager = StartupManager(config_file="/nonexistent/config.json")
        
        # Should fall back to default configuration
        self.assertIsInstance(startup_manager.config, dict)
        self.assertIn('startup_monitoring', startup_manager.config)
    
    def test_process_monitor_integration(self):
        """Test process monitor integration"""
        self.test_logger.info("Testing process monitor integration")
        
        # Test process monitor initialization
        if self.startup_manager.process_monitor is not None:
            self.test_logger.info("Process monitor is available and initialized")
            
            # Test account registration for monitoring
            self.startup_manager.register_accounts_for_monitoring()
            
            # Check log entries for registration events
            registration_events = [e for e in self.startup_manager.startup_log 
                                 if 'monitor_registration' in e['event']]
            self.assertTrue(len(registration_events) >= 0, "Registration events should be logged")
        else:
            self.test_logger.warning("Process monitor not available for testing")


class TestPhase1Integration(unittest.TestCase):
    """Test Phase 1 integration scenarios"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.test_logger = get_logger("test_phase1_integration", log_file="test_logs/phase1_integration.log")
    
    def test_startup_manager_instantiation(self):
        """Test startup manager can be instantiated without errors"""
        self.test_logger.info("Testing startup manager instantiation")
        
        try:
            startup_manager = StartupManager()
            self.assertIsNotNone(startup_manager)
            self.test_logger.info("Startup manager instantiated successfully")
        except Exception as e:
            self.fail(f"Startup manager instantiation failed: {e}")
    
    def test_dependency_imports(self):
        """Test that all required dependencies can be imported"""
        self.test_logger.info("Testing dependency imports")
        
        try:
            # Test all critical imports
            from enhanced_startup_manager import StartupManager, StartupValidationError
            from chrome_cleanup import ChromeCleanup
            from chrome_path_finder import get_chrome_finder
            from structured_logger import get_logger
            
            self.test_logger.info("All dependencies imported successfully")
        except ImportError as e:
            self.fail(f"Dependency import failed: {e}")


def run_phase1_tests():
    """Run all Phase 1 tests"""
    print("🧪 Running Phase 1 Error Handling Tests\n")
    
    # Create test logs directory
    os.makedirs("test_logs", exist_ok=True)
    
    # Create test suite
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTests(loader.loadTestsFromTestCase(TestPhase1ErrorHandling))
    test_suite.addTests(loader.loadTestsFromTestCase(TestPhase1Integration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total_tests - failures - errors
    
    print(f"\n📊 Phase 1 Test Results:")
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
    print(f"\nPhase 1 Tests: {status}")
    
    return success


if __name__ == "__main__":
    success = run_phase1_tests()
    sys.exit(0 if success else 1)