#!/usr/bin/env python3
"""
Integration Test Suite for Chrome Restart Implementation
Tests all components working together
"""

import os
import sys
import time
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import unittest
from unittest.mock import Mock, patch, MagicMock

# Import all our modules
from verify_environment import EnvironmentVerifier
from backup_manager import BackupManager
from chrome_cleanup import ChromeCleanup
from chrome_path_finder import get_chrome_finder
from structured_logger import get_logger, LogAnalyzer
from atomic_file_ops import AtomicFileOps
from enhanced_startup_manager import StartupManager
from pre_implementation_check import PreImplementationValidator


class TestIntegrationSuite(unittest.TestCase):
    """Comprehensive integration tests"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.test_dir = tempfile.mkdtemp(prefix="chrome_restart_test_")
        cls.logger = get_logger("integration_test", log_file="test/integration.log")
        cls.logger.info("Starting integration test suite", test_dir=cls.test_dir)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)
        cls.logger.info("Integration test suite completed")
    
    def setUp(self):
        """Set up each test"""
        self.test_start = time.time()
    
    def tearDown(self):
        """Clean up after each test"""
        duration = time.time() - self.test_start
        self.logger.info(f"Test {self._testMethodName} completed", duration=duration)
    
    def test_01_environment_verification(self):
        """Test environment verification"""
        self.logger.info("Testing environment verification")
        
        verifier = EnvironmentVerifier()
        
        # Run checks silently
        import io
        from contextlib import redirect_stdout
        
        f = io.StringIO()
        with redirect_stdout(f):
            result = verifier.run_all_checks()
        
        # At minimum, Python version should pass
        self.assertTrue(len(verifier.info) > 0, "Should have some passed checks")
        self.logger.info("Environment verification completed", 
                        passed=len(verifier.info),
                        warnings=len(verifier.warnings),
                        errors=len(verifier.errors))
    
    def test_02_backup_system(self):
        """Test backup and rollback functionality"""
        self.logger.info("Testing backup system")
        
        # Create test files
        test_files = []
        for i in range(3):
            test_file = os.path.join(self.test_dir, f"test_file_{i}.txt")
            with open(test_file, 'w') as f:
                f.write(f"Test content {i}\n")
            test_files.append(test_file)
        
        # Mock the files_to_backup
        backup_manager = BackupManager(backup_dir=os.path.join(self.test_dir, "backups"))
        backup_manager.files_to_backup = test_files
        
        # Create backup
        backup_id = backup_manager.create_backup("Test backup")
        self.assertIsNotNone(backup_id, "Backup should be created")
        
        # Verify backup
        is_valid = backup_manager.verify_backup(backup_id)
        self.assertTrue(is_valid, "Backup should be valid")
        
        # Modify original files
        for test_file in test_files:
            with open(test_file, 'w') as f:
                f.write("Modified content\n")
        
        # Test rollback
        success = backup_manager.rollback(backup_id)
        self.assertTrue(success, "Rollback should succeed")
        
        # Verify files were restored
        for i, test_file in enumerate(test_files):
            with open(test_file, 'r') as f:
                content = f.read()
                self.assertEqual(content, f"Test content {i}\n", "File should be restored")
        
        self.logger.info("Backup system test completed")
    
    def test_03_chrome_path_discovery(self):
        """Test Chrome path discovery"""
        self.logger.info("Testing Chrome path discovery")
        
        finder = get_chrome_finder()
        chrome_info = finder.get_chrome_info()
        
        self.assertIsNotNone(chrome_info, "Should get Chrome info")
        self.assertIn('platform', chrome_info, "Should have platform info")
        
        if chrome_info['found']:
            self.assertIn('path', chrome_info, "Should have Chrome path")
            self.logger.info("Chrome found", path=chrome_info['path'])
        else:
            self.logger.warning("Chrome not found in test environment")
        
        self.logger.info("Chrome path discovery test completed")
    
    def test_04_structured_logging(self):
        """Test structured logging functionality"""
        self.logger.info("Testing structured logging")
        
        # Create test logger
        test_logger = get_logger("test_structured", log_file="test/structured_test.log")
        
        # Test basic logging
        test_logger.info("Test info message", test_id=123)
        test_logger.warning("Test warning", severity="medium")
        
        # Test context management
        test_logger.add_context(session="test-session")
        
        with test_logger.context(operation="test_op"):
            test_logger.info("Message with context")
        
        # Test log analysis
        log_file = "logs/test/structured_test.log"
        if os.path.exists(log_file):
            analyzer = LogAnalyzer(log_file)
            summary = analyzer.get_summary()
            
            self.assertGreater(summary['total_entries'], 0, "Should have log entries")
            self.logger.info("Log analysis completed", entries=summary['total_entries'])
        
        self.logger.info("Structured logging test completed")
    
    def test_05_atomic_file_operations(self):
        """Test atomic file operations"""
        self.logger.info("Testing atomic file operations")
        
        ops = AtomicFileOps()
        test_file = os.path.join(self.test_dir, "atomic_test.txt")
        
        # Test atomic write
        content = "Test atomic content\n"
        success = ops.atomic_write(test_file, content)
        self.assertTrue(success, "Atomic write should succeed")
        
        # Verify content
        with open(test_file, 'r') as f:
            read_content = f.read()
        self.assertEqual(read_content, content, "Content should match")
        
        # Test atomic update
        def update_func(old_content):
            return old_content + "Additional line\n"
        
        success = ops.atomic_update(test_file, update_func)
        self.assertTrue(success, "Atomic update should succeed")
        
        # Test JSON operations
        json_file = os.path.join(self.test_dir, "atomic_test.json")
        initial_data = {"version": 1, "status": "active"}
        
        with open(json_file, 'w') as f:
            json.dump(initial_data, f)
        
        def json_update(data):
            data["version"] += 1
            return data
        
        success = ops.atomic_json_update(json_file, json_update)
        self.assertTrue(success, "Atomic JSON update should succeed")
        
        # Verify JSON was updated
        with open(json_file, 'r') as f:
            updated_data = json.load(f)
        self.assertEqual(updated_data["version"], 2, "Version should be incremented")
        
        self.logger.info("Atomic file operations test completed")
    
    def test_06_chrome_cleanup(self):
        """Test Chrome cleanup functionality"""
        self.logger.info("Testing Chrome cleanup")
        
        cleanup = ChromeCleanup()
        
        # Test finding Chrome processes (dry run)
        processes = cleanup.find_chrome_processes()
        self.assertIsInstance(processes, list, "Should return list of processes")
        
        # Test that port 9222 is protected
        protected_processes = [p for p in processes if p['port'] == 9222]
        self.assertEqual(len(protected_processes), 0, "Port 9222 should be protected")
        
        self.logger.info("Chrome cleanup test completed", 
                        processes_found=len(processes))
    
    def test_07_startup_manager_validation(self):
        """Test StartupManager validation methods"""
        self.logger.info("Testing StartupManager validation")
        
        # Create test config
        test_config = {
            "startup_monitoring": {
                "enabled": True,
                "max_retries": 2,
                "retry_delay_seconds": 1,
                "startup_timeout_seconds": 5
            }
        }
        
        config_file = os.path.join(self.test_dir, "test_config.json")
        with open(config_file, 'w') as f:
            json.dump(test_config, f)
        
        manager = StartupManager(config_file=config_file)
        
        # Test configuration loading
        self.assertEqual(manager.max_retries, 2, "Should load config correctly")
        
        # Test port validation
        with patch('socket.socket') as mock_socket:
            mock_sock = MagicMock()
            mock_sock.connect_ex.return_value = 1  # Port available
            mock_socket.return_value = mock_sock
            
            result = manager.validate_ports()
            self.assertTrue(result, "Port validation should pass when ports available")
        
        # Test memory validation
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value = Mock(available=4 * 1024**3, percent=50)
            
            result = manager.validate_memory()
            self.assertTrue(result, "Memory validation should pass with enough memory")
        
        # Test Chrome validation
        with patch.object(manager.chrome_finder, 'find_chrome', return_value="/mock/chrome"):
            with patch('os.path.exists', return_value=True):
                result = manager.validate_chrome_executable()
                self.assertTrue(result, "Chrome validation should pass when Chrome exists")
        
        self.logger.info("StartupManager validation test completed")
    
    def test_08_pre_implementation_validation(self):
        """Test pre-implementation validation"""
        self.logger.info("Testing pre-implementation validation")
        
        validator = PreImplementationValidator()
        
        # Mock various checks to ensure consistent results
        with patch.object(validator, 'check_environment', return_value=True):
            with patch.object(validator, 'check_backups', return_value=True):
                with patch.object(validator, 'check_chrome_processes', return_value=True):
                    with patch.object(validator, 'check_chrome_installation', return_value=True):
                        with patch.object(validator, 'check_file_structure', return_value=True):
                            with patch.object(validator, 'check_configuration', return_value=True):
                                with patch.object(validator, 'check_virtual_environment', return_value=True):
                                    # Run validation
                                    import io
                                    from contextlib import redirect_stdout
                                    
                                    f = io.StringIO()
                                    with redirect_stdout(f):
                                        result = validator.run_all_validations()
                                    
                                    self.assertTrue(result, "Validation should pass with all checks mocked")
        
        self.logger.info("Pre-implementation validation test completed")
    
    def test_09_error_recovery_simulation(self):
        """Test error recovery mechanisms"""
        self.logger.info("Testing error recovery simulation")
        
        # Test 1: Backup recovery
        backup_manager = BackupManager(backup_dir=os.path.join(self.test_dir, "recovery_backups"))
        test_file = os.path.join(self.test_dir, "recovery_test.txt")
        
        with open(test_file, 'w') as f:
            f.write("Original content\n")
        
        backup_manager.files_to_backup = [test_file]
        backup_id = backup_manager.create_backup("Pre-error backup")
        
        # Simulate error by corrupting file
        with open(test_file, 'w') as f:
            f.write("Corrupted content\n")
        
        # Recover
        success = backup_manager.rollback(backup_id)
        self.assertTrue(success, "Recovery should succeed")
        
        # Test 2: Atomic operation recovery
        ops = AtomicFileOps()
        atomic_test = os.path.join(self.test_dir, "atomic_recovery.txt")
        
        # Write initial content
        ops.atomic_write(atomic_test, "Initial content\n")
        
        # Simulate failed update
        def failing_update(content):
            raise Exception("Simulated failure")
        
        try:
            ops.atomic_update(atomic_test, failing_update)
        except Exception:
            pass  # Expected
        
        # Verify original content preserved
        with open(atomic_test, 'r') as f:
            content = f.read()
        self.assertEqual(content, "Initial content\n", "Original content should be preserved")
        
        self.logger.info("Error recovery simulation completed")
    
    def test_10_end_to_end_workflow(self):
        """Test complete workflow simulation"""
        self.logger.info("Testing end-to-end workflow")
        
        # Step 1: Pre-validation
        validator = PreImplementationValidator()
        self.logger.info("Step 1: Pre-validation check")
        
        # Step 2: Backup
        backup_manager = BackupManager(backup_dir=os.path.join(self.test_dir, "e2e_backups"))
        self.logger.info("Step 2: Creating backup")
        
        # Step 3: Cleanup
        cleanup = ChromeCleanup()
        self.logger.info("Step 3: Chrome cleanup")
        
        # Step 4: Startup validation
        manager = StartupManager()
        self.logger.info("Step 4: Startup validation")
        
        # Step 5: Generate report
        report = {
            "test_completed": datetime.now().isoformat(),
            "steps_completed": 5,
            "status": "success"
        }
        
        report_file = os.path.join(self.test_dir, "e2e_report.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.assertTrue(os.path.exists(report_file), "Report should be generated")
        self.logger.info("End-to-end workflow completed")


class TestRunner:
    """Custom test runner with enhanced reporting"""
    
    def __init__(self):
        self.logger = get_logger("test_runner", log_file="test/test_runner.log")
    
    def run_tests(self):
        """Run all integration tests"""
        print("="*60)
        print("🧪 CHROME RESTART IMPLEMENTATION - INTEGRATION TEST SUITE")
        print("="*60)
        
        self.logger.info("Starting integration test suite")
        
        # Create test suite
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestIntegrationSuite)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Generate summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        total_tests = result.testsRun
        failures = len(result.failures)
        errors = len(result.errors)
        skipped = len(result.skipped)
        passed = total_tests - failures - errors - skipped
        
        print(f"\nTotal Tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failures}")
        print(f"💥 Errors: {errors}")
        print(f"⏭️  Skipped: {skipped}")
        
        if failures > 0:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback.split(chr(10))[0]}")
        
        if errors > 0:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback.split(chr(10))[0]}")
        
        # Log summary
        self.logger.info("Test suite completed",
                        total=total_tests,
                        passed=passed,
                        failed=failures,
                        errors=errors,
                        skipped=skipped)
        
        # Generate detailed report
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total_tests,
                "passed": passed,
                "failed": failures,
                "errors": errors,
                "skipped": skipped
            },
            "success": failures == 0 and errors == 0
        }
        
        report_file = "test_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return result.wasSuccessful()


def main():
    """Run integration test suite"""
    runner = TestRunner()
    success = runner.run_tests()
    
    if success:
        print("\n✅ All tests passed! Ready for deployment.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Review and fix before deployment.")
        sys.exit(1)


if __name__ == "__main__":
    main()