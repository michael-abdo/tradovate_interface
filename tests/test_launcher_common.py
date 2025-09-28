"""
Tests for launcher common utilities in launchers/common.py
"""

import os
import sys
import pytest
from pathlib import Path
from unittest import mock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from launchers.common import setup_python_path, launch_module, create_launcher


class TestSetupPythonPath:
    """Tests for setup_python_path() function"""
    
    def test_setup_python_path_auto_detect(self):
        """Test auto-detection of project root"""
        # Save original sys.path
        original_path = sys.path.copy()
        
        try:
            # Clear project root from path if present
            project_root = Path(__file__).parent.parent
            project_root_str = str(project_root)
            sys.path = [p for p in sys.path if p != project_root_str]
            
            # Test auto-detection
            result = setup_python_path()
            
            # Should return the project root
            assert result == project_root
            # Should add project root to sys.path
            assert project_root_str in sys.path
            assert sys.path[0] == project_root_str
        finally:
            # Restore original sys.path
            sys.path = original_path
    
    def test_setup_python_path_with_custom_root(self):
        """Test with custom project root"""
        original_path = sys.path.copy()
        
        try:
            custom_root = Path("/custom/project/root")
            result = setup_python_path(custom_root)
            
            assert result == custom_root
            assert str(custom_root) in sys.path
        finally:
            sys.path = original_path
    
    def test_setup_python_path_idempotent(self):
        """Test that setup_python_path doesn't duplicate paths"""
        original_path = sys.path.copy()
        
        try:
            project_root = setup_python_path()
            initial_path_len = len(sys.path)
            
            # Call again
            setup_python_path()
            
            # Should not add duplicate
            assert len(sys.path) == initial_path_len
        finally:
            sys.path = original_path


class TestLaunchModule:
    """Tests for launch_module() function"""
    
    def test_launch_module_with_main_function(self):
        """Test launching module with main() function"""
        # Create a mock module
        mock_module = mock.Mock()
        mock_module.main = mock.Mock()
        
        with mock.patch('launchers.common.setup_python_path') as mock_setup, \
             mock.patch('builtins.__import__', return_value=mock_module) as mock_import:
            
            launch_module('test_module')
            
            mock_setup.assert_called_once()
            mock_import.assert_called_once_with('test_module')
            mock_module.main.assert_called_once()
    
    def test_launch_module_with_nested_path(self):
        """Test launching module with nested path like 'src.app'"""
        # Create mock module hierarchy
        mock_src = mock.Mock()
        mock_app = mock.Mock()
        mock_app.main = mock.Mock()
        mock_src.app = mock_app
        
        with mock.patch('launchers.common.setup_python_path'), \
             mock.patch('builtins.__import__', return_value=mock_src):
            
            launch_module('src.app')
            
            mock_app.main.assert_called_once()
    
    def test_launch_module_with_arguments(self):
        """Test launching module with command-line arguments"""
        mock_module = mock.Mock()
        mock_module.main = mock.Mock()
        
        original_argv = sys.argv.copy()
        
        try:
            with mock.patch('launchers.common.setup_python_path'), \
                 mock.patch('builtins.__import__', return_value=mock_module):
                
                launch_module('test_module', args=['--arg1', 'value1', '--flag'])
                
                assert sys.argv[1:] == ['--arg1', 'value1', '--flag']
                mock_module.main.assert_called_once()
        finally:
            sys.argv = original_argv
    
    def test_launch_module_with_py_extension(self):
        """Test launching module when path includes .py extension"""
        mock_module = mock.Mock()
        mock_module.main = mock.Mock()
        
        with mock.patch('launchers.common.setup_python_path'), \
             mock.patch('builtins.__import__', return_value=mock_module) as mock_import:
            
            launch_module('test_module.py')
            
            # Should strip .py extension
            mock_import.assert_called_once_with('test_module')
    
    def test_launch_module_with_path_separators(self):
        """Test launching module with path separators"""
        mock_src = mock.Mock()
        mock_app = mock.Mock()
        mock_app.main = mock.Mock()
        mock_src.app = mock_app
        
        with mock.patch('launchers.common.setup_python_path'), \
             mock.patch('builtins.__import__', return_value=mock_src) as mock_import:
            
            launch_module('src/app.py')
            
            # Should convert to dot notation
            mock_import.assert_called_once_with('src.app')
    
    def test_launch_module_no_main_function(self):
        """Test launching module without main() function"""
        mock_module = mock.Mock(spec=[])  # No main attribute
        
        with mock.patch('launchers.common.setup_python_path'), \
             mock.patch('builtins.__import__', return_value=mock_module), \
             mock.patch('builtins.print') as mock_print:
            
            launch_module('test_module')
            
            # Should print warning
            mock_print.assert_called_with("Warning: Module test_module has no main() function")
    
    def test_launch_module_import_error(self):
        """Test handling import error"""
        with mock.patch('launchers.common.setup_python_path'), \
             mock.patch('builtins.__import__', side_effect=ImportError("Module not found")), \
             mock.patch('builtins.print') as mock_print:
            
            with pytest.raises(SystemExit) as exc_info:
                launch_module('nonexistent_module')
            
            assert exc_info.value.code == 1
            mock_print.assert_called_with("Error: Failed to import module 'nonexistent_module': Module not found")
    
    def test_launch_module_runtime_error(self):
        """Test handling runtime error in module"""
        mock_module = mock.Mock()
        mock_module.main.side_effect = RuntimeError("Something went wrong")
        
        with mock.patch('launchers.common.setup_python_path'), \
             mock.patch('builtins.__import__', return_value=mock_module), \
             mock.patch('builtins.print') as mock_print:
            
            with pytest.raises(SystemExit) as exc_info:
                launch_module('test_module')
            
            assert exc_info.value.code == 1
            assert "Error: Failed to launch module 'test_module'" in str(mock_print.call_args_list[-1])


class TestCreateLauncher:
    """Tests for create_launcher() factory function"""
    
    def test_create_launcher_basic(self):
        """Test creating a basic launcher"""
        launcher = create_launcher('src.app')
        
        # Should return a function
        assert callable(launcher)
        assert launcher.__doc__ == "Launch src.app"
        
        # Test that it calls launch_module correctly
        original_argv = sys.argv.copy()
        try:
            sys.argv = ['test_launcher']  # Mock argv without args
            with mock.patch('launchers.common.launch_module') as mock_launch:
                launcher()
                mock_launch.assert_called_once_with('src.app', [])
        finally:
            sys.argv = original_argv
    
    def test_create_launcher_with_description(self):
        """Test creating launcher with description"""
        launcher = create_launcher('src.dashboard', 'Dashboard application')
        
        assert launcher.__doc__ == "Launch src.dashboard - Dashboard application"
        
        original_argv = sys.argv.copy()
        try:
            sys.argv = ['test_launcher']  # Mock argv without args
            with mock.patch('launchers.common.launch_module') as mock_launch, \
                 mock.patch('builtins.print') as mock_print:
                
                launcher()
                
                mock_print.assert_called_with("Launching: Dashboard application")
                mock_launch.assert_called_once_with('src.dashboard', [])
        finally:
            sys.argv = original_argv
    
    def test_create_launcher_passes_arguments(self):
        """Test that created launcher passes command-line arguments"""
        launcher = create_launcher('src.app')
        
        original_argv = sys.argv.copy()
        try:
            sys.argv = ['launcher', '--debug', '--port', '8080']
            
            with mock.patch('launchers.common.launch_module') as mock_launch:
                launcher()
                
                # Should pass along sys.argv[1:]
                mock_launch.assert_called_once_with('src.app', ['--debug', '--port', '8080'])
        finally:
            sys.argv = original_argv
    
    def test_multiple_launchers_independent(self):
        """Test that multiple launchers are independent"""
        launcher1 = create_launcher('src.app', 'App 1')
        launcher2 = create_launcher('src.dashboard', 'App 2')
        
        assert launcher1.__doc__ != launcher2.__doc__
        
        with mock.patch('launchers.common.launch_module') as mock_launch, \
             mock.patch('builtins.print'):
            
            launcher1()
            launcher2()
            
            # Should have different module paths
            calls = mock_launch.call_args_list
            assert len(calls) == 2
            assert calls[0][0][0] == 'src.app'
            assert calls[1][0][0] == 'src.dashboard'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])