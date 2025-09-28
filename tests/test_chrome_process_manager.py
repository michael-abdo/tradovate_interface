"""
Tests for ChromeProcessManager class in src/auto_login.py
"""

import os
import subprocess
import tempfile
import threading
import time
import pytest
from pathlib import Path
from unittest import mock

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.auto_login import ChromeProcessManager


class TestChromeProcessManager:
    """Tests for ChromeProcessManager class"""
    
    @pytest.fixture
    def chrome_manager(self):
        """Create a ChromeProcessManager instance for testing"""
        with mock.patch('src.auto_login.find_chrome_executable') as mock_find:
            mock_find.return_value = '/fake/chrome/path'
            manager = ChromeProcessManager()
            yield manager
            # Cleanup any processes that might have been created
            manager.cleanup()
    
    def test_init_with_default_path(self):
        """Test initialization with auto-detected Chrome path"""
        with mock.patch('src.auto_login.find_chrome_executable') as mock_find:
            mock_find.return_value = '/auto/detected/chrome'
            manager = ChromeProcessManager()
            assert manager.chrome_path == '/auto/detected/chrome'
            assert manager.processes == {}
            assert isinstance(manager.lock, threading.Lock)
    
    def test_init_with_custom_path(self):
        """Test initialization with custom Chrome path"""
        custom_path = '/custom/chrome/path'
        manager = ChromeProcessManager(chrome_path=custom_path)
        assert manager.chrome_path == custom_path
    
    def test_launch_chrome_success(self, chrome_manager):
        """Test successful Chrome launch"""
        port = 9999
        mock_process = mock.Mock(spec=subprocess.Popen)
        mock_process.poll.return_value = None  # Process is running
        
        with mock.patch('subprocess.Popen', return_value=mock_process) as mock_popen, \
             mock.patch('tempfile.mkdtemp', return_value='/tmp/chrome_9999'), \
             mock.patch('src.auto_login.logger') as mock_logger:
            
            result = chrome_manager.launch_chrome(port)
            
            # Verify Chrome was launched with correct arguments
            mock_popen.assert_called_once()
            args = mock_popen.call_args[0][0]
            assert args[0] == '/fake/chrome/path'
            assert f'--remote-debugging-port={port}' in args
            assert '--no-first-run' in args
            assert '--no-sandbox' in args
            
            # Verify process was stored
            assert chrome_manager.processes[port] == mock_process
            assert result == mock_process
    
    def test_launch_chrome_already_running(self, chrome_manager):
        """Test launching Chrome when already running on same port"""
        port = 9999
        existing_process = mock.Mock(spec=subprocess.Popen)
        existing_process.poll.return_value = None  # Still running
        
        # Pre-populate with existing process
        chrome_manager.processes[port] = existing_process
        
        with mock.patch('subprocess.Popen') as mock_popen, \
             mock.patch('src.auto_login.logger') as mock_logger:
            
            result = chrome_manager.launch_chrome(port)
            
            # Should not create new process
            mock_popen.assert_not_called()
            
            # Should return existing process
            assert result == existing_process
            
            # Should log warning
            mock_logger.warning.assert_called_with(f"Chrome already running on port {port}")
    
    def test_launch_chrome_with_user_data_dir(self, chrome_manager):
        """Test launching Chrome with custom user data directory"""
        port = 9999
        user_data_dir = '/custom/user/data'
        mock_process = mock.Mock(spec=subprocess.Popen)
        mock_process.poll.return_value = None
        
        with mock.patch('subprocess.Popen', return_value=mock_process) as mock_popen:
            
            chrome_manager.launch_chrome(port, user_data_dir=user_data_dir)
            
            # Verify user data dir was included in arguments
            args = mock_popen.call_args[0][0]
            assert f'--user-data-dir={user_data_dir}' in args
            
            # Should not create temp directory when user_data_dir provided
            with mock.patch('tempfile.mkdtemp') as mock_mkdtemp:
                chrome_manager.launch_chrome(port + 1, user_data_dir=user_data_dir)
                mock_mkdtemp.assert_not_called()
    
    def test_launch_chrome_subprocess_error(self, chrome_manager):
        """Test handling subprocess launch error"""
        port = 9999
        
        with mock.patch('subprocess.Popen', side_effect=OSError("Chrome not found")), \
             mock.patch('src.auto_login.logger') as mock_logger:
            
            with pytest.raises(RuntimeError, match="Chrome launch failed"):
                chrome_manager.launch_chrome(port)
            
            # Should not store failed process
            assert port not in chrome_manager.processes
    
    def test_stop_chrome_success(self, chrome_manager):
        """Test successfully stopping Chrome process"""
        port = 9999
        mock_process = mock.Mock(spec=subprocess.Popen)
        mock_process.poll.return_value = None  # Still running
        mock_process.terminate.return_value = None
        mock_process.wait.return_value = 0
        
        chrome_manager.processes[port] = mock_process
        
        with mock.patch('src.auto_login.logger'):
            result = chrome_manager.stop_chrome(port)
        
        assert result is True
        assert port not in chrome_manager.processes
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once_with(timeout=5)
    
    def test_stop_chrome_already_stopped(self, chrome_manager):
        """Test stopping Chrome that's already stopped"""
        port = 9999
        mock_process = mock.Mock(spec=subprocess.Popen)
        mock_process.poll.return_value = 0  # Already exited
        
        chrome_manager.processes[port] = mock_process
        
        result = chrome_manager.stop_chrome(port)
        
        assert result is True
        assert port not in chrome_manager.processes
        mock_process.terminate.assert_not_called()
    
    def test_stop_chrome_nonexistent_port(self, chrome_manager):
        """Test stopping Chrome on port with no process"""
        result = chrome_manager.stop_chrome(9999)
        assert result is True
    
    def test_stop_chrome_force_kill(self, chrome_manager):
        """Test force killing Chrome when graceful shutdown fails"""
        port = 9999
        mock_process = mock.Mock(spec=subprocess.Popen)
        mock_process.poll.return_value = None
        # First wait times out, but second wait (after kill) succeeds
        mock_process.wait.side_effect = [subprocess.TimeoutExpired('chrome', 5), None]
        mock_process.kill.return_value = None
        
        chrome_manager.processes[port] = mock_process
        
        with mock.patch('src.auto_login.logger') as mock_logger:
            result = chrome_manager.stop_chrome(port)
        
        # The method should return True after force kill succeeds
        assert result is True
        # Process should be removed from processes dict
        assert port not in chrome_manager.processes
        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()
        # wait() is called twice - once for terminate, once after kill
        assert mock_process.wait.call_count == 2
        mock_logger.warning.assert_called()
    
    def test_stop_all(self, chrome_manager):
        """Test stopping all Chrome processes"""
        # Set up multiple processes
        processes = {}
        for port in [9222, 9223, 9224]:
            mock_process = mock.Mock(spec=subprocess.Popen)
            mock_process.poll.return_value = None
            mock_process.terminate.return_value = None
            mock_process.wait.return_value = 0
            processes[port] = mock_process
            chrome_manager.processes[port] = mock_process
        
        with mock.patch('src.auto_login.logger'):
            chrome_manager.stop_all()
        
        # All processes should be stopped and removed
        assert len(chrome_manager.processes) == 0
        for process in processes.values():
            process.terminate.assert_called_once()
    
    def test_cleanup(self, chrome_manager):
        """Test cleanup method"""
        # Add some processes
        for port in [9222, 9223]:
            chrome_manager.processes[port] = mock.Mock()
        
        with mock.patch.object(chrome_manager, 'stop_all') as mock_stop_all:
            chrome_manager.cleanup()
        
        mock_stop_all.assert_called_once()
        assert len(chrome_manager.processes) == 0
    
    def test_thread_safety(self, chrome_manager):
        """Test thread safety of ChromeProcessManager"""
        results = []
        errors = []
        ports_used = []
        
        # Create all mock processes upfront to avoid threading issues with mock
        mock_processes = {}
        for i in range(10):
            port = 9000 + i
            mock_process = mock.Mock(spec=subprocess.Popen)
            mock_process.poll.return_value = None
            mock_process.terminate.return_value = None
            mock_process.wait.return_value = 0
            mock_processes[port] = mock_process
            ports_used.append(port)
        
        def launch_and_stop(port):
            try:
                with mock.patch('subprocess.Popen', return_value=mock_processes[port]), \
                     mock.patch('tempfile.mkdtemp', return_value=f'/tmp/chrome_{port}'):
                    # Launch
                    chrome_manager.launch_chrome(port)
                    time.sleep(0.001)  # Small delay to increase chance of race conditions
                    
                    # Stop
                    with mock.patch('src.auto_login.logger'):
                        chrome_manager.stop_chrome(port)
                    
                results.append(port)
            except Exception as e:
                errors.append((port, e))
        
        # Launch multiple threads
        threads = []
        for port in ports_used:
            thread = threading.Thread(target=launch_and_stop, args=(port,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify no errors and all completed
        if errors:
            print(f"Errors encountered: {errors}")
        assert len(errors) == 0
        assert len(results) == 10
        assert len(chrome_manager.processes) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])