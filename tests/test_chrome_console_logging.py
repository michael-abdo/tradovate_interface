#!/usr/bin/env python3
"""
Unit tests for Chrome console logging integration functionality.
"""
import unittest
import tempfile
import shutil
import os
import sys
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import start_all
from src.auto_login import set_log_directory, create_log_file_path, set_terminal_callback


class TestChromeConsoleLogging(unittest.TestCase):
    """Test Chrome console logging integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_log_directory = start_all.log_directory
        
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        start_all.log_directory = self.original_log_directory
    
    def test_create_log_directory(self):
        """Test log directory creation with timestamp."""
        # Mock datetime to control timestamp
        with patch('start_all.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '2025-09-20_14-30-00'
            
            # Set project root to test directory
            original_project_root = start_all.project_root
            start_all.project_root = self.test_dir
            
            try:
                log_dir = start_all.create_log_directory()
                
                # Verify directory was created
                expected_path = os.path.join(self.test_dir, 'logs', '2025-09-20_14-30-00')
                self.assertEqual(log_dir, expected_path)
                self.assertTrue(os.path.exists(expected_path))
                self.assertTrue(os.path.isdir(expected_path))
                
            finally:
                start_all.project_root = original_project_root
    
    def test_verify_log_directory(self):
        """Test log directory verification."""
        # Test with no log directory
        start_all.log_directory = None
        self.assertFalse(start_all.verify_log_directory())
        
        # Test with non-existent directory
        start_all.log_directory = '/nonexistent/path'
        self.assertFalse(start_all.verify_log_directory())
        
        # Test with valid directory
        test_log_dir = os.path.join(self.test_dir, 'test_logs')
        os.makedirs(test_log_dir)
        start_all.log_directory = test_log_dir
        self.assertTrue(start_all.verify_log_directory())
    
    def test_create_log_file_path(self):
        """Test log file path creation for Chrome instances."""
        test_log_dir = os.path.join(self.test_dir, 'test_logs')
        set_log_directory(test_log_dir)
        
        # Test single user
        path = create_log_file_path('testuser', 9222)
        expected = os.path.join(test_log_dir, 'chrome_console_testuser_9222.log')
        self.assertEqual(path, expected)
        
        # Test multiple users with different ports
        users = [('user1', 9222), ('user2', 9223), ('user3', 9224)]
        paths = []
        for username, port in users:
            path = create_log_file_path(username, port)
            paths.append(path)
            self.assertIn(f'chrome_console_{username}_{port}.log', path)
        
        # Verify all paths are unique
        self.assertEqual(len(paths), len(set(paths)))
    
    def test_terminal_callback_creation(self):
        """Test terminal callback function creation."""
        callback = start_all.create_terminal_callback()
        self.assertIsNotNone(callback)
        self.assertTrue(callable(callback))
        
        # Test callback execution with mock entry
        test_entry = {
            'level': 'INFO',
            'source': 'test',
            'text': 'Test log message'
        }
        
        # Should not raise any exceptions
        try:
            callback(test_entry)
        except Exception as e:
            self.fail(f"Terminal callback raised an exception: {e}")
    
    def test_terminal_callback_functionality(self):
        """Test terminal callback with various log levels."""
        callback = start_all.create_terminal_callback()
        
        test_entries = [
            {'level': 'DEBUG', 'source': 'console', 'text': 'Debug message'},
            {'level': 'INFO', 'source': 'browser', 'text': 'Info message'},
            {'level': 'WARNING', 'source': 'console', 'text': 'Warning message'},
            {'level': 'ERROR', 'source': 'exception', 'text': 'Error message'},
        ]
        
        for entry in test_entries:
            with patch('builtins.print') as mock_print:
                callback(entry)
                mock_print.assert_called_once()
                # Verify the call contains expected elements
                call_args = mock_print.call_args[0][0]
                self.assertIn(entry['level'], call_args)
                self.assertIn(entry['source'], call_args)
                self.assertIn(entry['text'], call_args)
    
    def test_chrome_debugging_connections_test(self):
        """Test Chrome debugging connection testing."""
        # The function should always return True unless there's an exception
        # because missing Chrome connections are expected before Chrome starts
        result = start_all.test_chrome_debugging_connections()
        self.assertTrue(result)
    
    def test_set_terminal_callback(self):
        """Test setting terminal callback in auto_login module."""
        test_callback = lambda x: print(f"Test: {x}")
        
        set_terminal_callback(test_callback)
        
        # Import to access the global variable
        from src.auto_login import terminal_callback
        self.assertEqual(terminal_callback, test_callback)
    
    def test_chrome_instance_logger_integration(self):
        """Test ChromeLogger integration in ChromeInstance class."""
        from src.auto_login import ChromeInstance, set_log_directory, set_register_chrome_logger
        
        # Setup test environment
        test_log_dir = os.path.join(self.test_dir, 'chrome_logs')
        os.makedirs(test_log_dir, exist_ok=True)
        set_log_directory(test_log_dir)
        
        # Track registered loggers
        registered_loggers = []
        def mock_register(logger):
            registered_loggers.append(logger)
        
        set_register_chrome_logger(mock_register)
        
        # Test ChromeInstance initialization
        instance = ChromeInstance(9222, 'testuser', 'testpass')
        
        # Verify initial state
        self.assertIsNone(instance.chrome_logger)
        self.assertIsNone(instance.log_file_path)
        
        # Set log file path
        log_path = os.path.join(test_log_dir, 'test_chrome.log')
        instance.set_log_file_path(log_path)
        self.assertEqual(instance.log_file_path, log_path)
    
    @patch('src.auto_login.start_chrome_with_debugging')
    @patch('src.auto_login.connect_to_chrome')
    @patch('src.chrome_logger.create_logger')
    def test_chrome_instance_logger_start_success(self, mock_create_logger, mock_connect, mock_start_chrome):
        """Test successful ChromeLogger initialization during ChromeInstance.start()."""
        from src.auto_login import ChromeInstance, set_log_directory, set_register_chrome_logger
        
        # Setup mocks
        mock_process = MagicMock()
        mock_start_chrome.return_value = mock_process
        
        mock_browser = MagicMock()
        mock_tab = MagicMock()
        mock_connect.return_value = (mock_browser, mock_tab)
        
        mock_logger = MagicMock()
        mock_create_logger.return_value = mock_logger
        
        # Setup test environment
        test_log_dir = os.path.join(self.test_dir, 'chrome_logs')
        os.makedirs(test_log_dir, exist_ok=True)
        set_log_directory(test_log_dir)
        
        registered_loggers = []
        def mock_register(logger):
            registered_loggers.append(logger)
        set_register_chrome_logger(mock_register)
        
        # Create and configure instance
        instance = ChromeInstance(9222, 'testuser', 'testpass')
        log_path = os.path.join(test_log_dir, 'test_chrome.log')
        instance.set_log_file_path(log_path)
        
        # Mock login checking to avoid complex setup
        with patch.object(instance, 'check_and_login_if_needed'), \
             patch('src.auto_login.disable_alerts'):
            
            result = instance.start()
        
        # Verify successful start
        self.assertTrue(result)
        self.assertEqual(instance.chrome_logger, mock_logger)
        
        # Verify logger was created with correct parameters
        mock_create_logger.assert_called_once()
        
        # Verify logger was registered
        self.assertEqual(len(registered_loggers), 1)
        self.assertEqual(registered_loggers[0], mock_logger)
    
    @patch('src.auto_login.start_chrome_with_debugging')
    @patch('src.auto_login.connect_to_chrome')
    @patch('src.chrome_logger.create_logger')
    def test_chrome_instance_logger_start_failure(self, mock_create_logger, mock_connect, mock_start_chrome):
        """Test ChromeLogger initialization failure during ChromeInstance.start()."""
        from src.auto_login import ChromeInstance, set_log_directory, set_register_chrome_logger
        
        # Setup mocks
        mock_process = MagicMock()
        mock_start_chrome.return_value = mock_process
        
        mock_browser = MagicMock()
        mock_tab = MagicMock()
        mock_connect.return_value = (mock_browser, mock_tab)
        
        # Make logger creation fail
        mock_create_logger.side_effect = Exception("Logger creation failed")
        
        # Setup test environment
        test_log_dir = os.path.join(self.test_dir, 'chrome_logs')
        os.makedirs(test_log_dir, exist_ok=True)
        set_log_directory(test_log_dir)
        
        registered_loggers = []
        def mock_register(logger):
            registered_loggers.append(logger)
        set_register_chrome_logger(mock_register)
        
        # Create and configure instance
        instance = ChromeInstance(9222, 'testuser', 'testpass')
        log_path = os.path.join(test_log_dir, 'test_chrome.log')
        instance.set_log_file_path(log_path)
        
        # Mock login checking to avoid complex setup
        with patch.object(instance, 'check_and_login_if_needed'), \
             patch('src.auto_login.disable_alerts'):
            
            result = instance.start()
        
        # Verify start still succeeded despite logger failure
        self.assertTrue(result)
        self.assertIsNone(instance.chrome_logger)
        
        # Verify no logger was registered
        self.assertEqual(len(registered_loggers), 0)
    
    def test_chrome_instance_logger_stop(self):
        """Test ChromeLogger cleanup during ChromeInstance.stop()."""
        from src.auto_login import ChromeInstance
        
        # Create instance with mock logger
        instance = ChromeInstance(9222, 'testuser', 'testpass')
        
        mock_logger = MagicMock()
        instance.chrome_logger = mock_logger
        
        # Test stop
        instance.stop()
        
        # Verify logger was stopped
        mock_logger.stop.assert_called_once()
        self.assertIsNone(instance.chrome_logger)
    
    def test_chrome_instance_logger_stop_with_error(self):
        """Test ChromeLogger cleanup with error during stop()."""
        from src.auto_login import ChromeInstance
        
        # Create instance with mock logger that raises error
        instance = ChromeInstance(9222, 'testuser', 'testpass')
        
        mock_logger = MagicMock()
        mock_logger.stop.side_effect = Exception("Stop failed")
        instance.chrome_logger = mock_logger
        
        # Test stop - should handle error gracefully
        try:
            instance.stop()
        except Exception:
            self.fail("ChromeInstance.stop() should handle logger stop errors gracefully")
        
        # Verify logger stop was attempted
        mock_logger.stop.assert_called_once()
        self.assertIsNone(instance.chrome_logger)


if __name__ == '__main__':
    unittest.main()