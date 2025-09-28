"""
Tests for core utility functions in src/utils/core.py
"""

import json
import logging
import os
import platform
import pytest
import tempfile
from pathlib import Path
from unittest import mock

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.core import (
    get_project_root,
    find_chrome_executable,
    load_json_config,
    get_script_path,
    setup_logging
)


class TestGetProjectRoot:
    """Tests for get_project_root() function"""
    
    def test_get_project_root_with_git_directory(self):
        """Test finding project root by .git directory"""
        # Should find the project root by traversing up to find .git
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.is_dir()
        # Verify we're in tradovate_interface_refactored directory
        assert root.name == 'tradovate_interface_refactored'
    
    def test_get_project_root_returns_path_object(self):
        """Test that function returns Path object, not string"""
        root = get_project_root()
        assert isinstance(root, Path)
    
    def test_get_project_root_is_absolute(self):
        """Test that returned path is absolute"""
        root = get_project_root()
        assert root.is_absolute()


class TestFindChromeExecutable:
    """Tests for find_chrome_executable() function"""
    
    def test_find_chrome_on_current_platform(self):
        """Test finding Chrome on the current platform"""
        # This test will only pass if Chrome is actually installed
        try:
            chrome_path = find_chrome_executable()
            assert isinstance(chrome_path, str)
            assert os.path.exists(chrome_path)
            assert os.access(chrome_path, os.X_OK)
        except RuntimeError as e:
            # Chrome not installed is an acceptable test result
            assert "Chrome executable not found" in str(e)
    
    @mock.patch('platform.system')
    def test_find_chrome_macos(self, mock_system):
        """Test Chrome detection on macOS"""
        mock_system.return_value = 'darwin'
        
        with mock.patch('os.path.isfile') as mock_isfile, \
             mock.patch('os.access') as mock_access:
            
            # Simulate Chrome found at standard macOS location
            def isfile_side_effect(path):
                return path == '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
            
            mock_isfile.side_effect = isfile_side_effect
            mock_access.return_value = True
            
            chrome_path = find_chrome_executable()
            assert chrome_path == '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    
    @mock.patch('platform.system')
    def test_find_chrome_not_found(self, mock_system):
        """Test Chrome detection when Chrome is not installed"""
        mock_system.return_value = 'linux'
        
        with mock.patch('os.path.isfile', return_value=False):
            with pytest.raises(RuntimeError, match="Chrome executable not found"):
                find_chrome_executable()


class TestLoadJsonConfig:
    """Tests for load_json_config() function"""
    
    def test_load_valid_json_config(self):
        """Test loading a valid JSON configuration file"""
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_config = {
                "username": "test_user",
                "api_key": "test_key",
                "settings": {
                    "timeout": 30,
                    "retry": 3
                }
            }
            json.dump(test_config, f)
            temp_path = f.name
        
        try:
            # Test loading the config
            config = load_json_config(temp_path)
            assert config == test_config
            assert config["username"] == "test_user"
            assert config["settings"]["timeout"] == 30
        finally:
            # Clean up
            os.unlink(temp_path)
    
    def test_load_config_file_not_found(self):
        """Test loading config when file doesn't exist"""
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            load_json_config("/path/that/does/not/exist.json")
    
    def test_load_invalid_json(self):
        """Test loading config with invalid JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json content")
            temp_path = f.name
        
        try:
            with pytest.raises(json.JSONDecodeError):
                load_json_config(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_load_config_relative_path(self):
        """Test loading config with relative path"""
        # Create a temporary config in project root
        project_root = get_project_root()
        config_path = project_root / "test_config.json"
        
        test_config = {"test": "data"}
        with open(config_path, 'w') as f:
            json.dump(test_config, f)
        
        try:
            # Test with relative path
            config = load_json_config("test_config.json")
            assert config == test_config
        finally:
            if config_path.exists():
                config_path.unlink()


class TestGetScriptPath:
    """Tests for get_script_path() function"""
    
    def test_get_existing_script_in_src(self):
        """Test finding a script that exists in src directory"""
        # We know auto_login.py exists in src
        script_path = get_script_path("auto_login.py")
        assert script_path.exists()
        assert script_path.is_file()
        assert script_path.name == "auto_login.py"
    
    def test_get_script_without_extension(self):
        """Test finding a script when extension is not provided"""
        script_path = get_script_path("auto_login")
        assert script_path.exists()
        assert script_path.name == "auto_login.py"
    
    def test_get_script_in_launchers(self):
        """Test finding a script in launchers directory"""
        script_path = get_script_path("app_launcher.py")
        assert script_path.exists()
        assert "launchers" in str(script_path)
    
    def test_get_nonexistent_script(self):
        """Test behavior when script doesn't exist"""
        with pytest.raises(FileNotFoundError, match="Script 'nonexistent_script.py' not found"):
            get_script_path("nonexistent_script.py")
    
    def test_get_script_returns_absolute_path(self):
        """Test that returned path is absolute"""
        script_path = get_script_path("auto_login.py")
        assert script_path.is_absolute()


class TestSetupLogging:
    """Tests for setup_logging() function"""
    
    def test_setup_basic_logging(self):
        """Test basic logging setup with default parameters"""
        logger = setup_logging()
        assert isinstance(logger, logging.Logger)
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0
    
    def test_setup_logging_with_debug_level(self):
        """Test logging setup with DEBUG level"""
        logger = setup_logging(level="DEBUG")
        assert logger.level == logging.DEBUG
    
    def test_setup_logging_with_file_output(self):
        """Test logging setup with file output"""
        with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as f:
            log_file = f.name
        
        try:
            logger = setup_logging(log_file=log_file)
            
            # Test that log file is created
            assert os.path.exists(log_file)
            
            # Test logging to file
            logger.info("Test log message")
            
            # Verify message was written
            with open(log_file, 'r') as f:
                log_content = f.read()
                assert "Test log message" in log_content
        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)
    
    def test_setup_logging_no_console(self):
        """Test logging setup with console output disabled"""
        logger = setup_logging(console_output=False)
        
        # Should have no handlers if console is disabled and no file specified
        assert len(logger.handlers) == 0
    
    def test_setup_logging_invalid_level(self):
        """Test logging setup with invalid level"""
        with pytest.raises(ValueError, match="Invalid log level"):
            setup_logging(level="INVALID_LEVEL")
    
    def test_setup_logging_creates_log_directory(self):
        """Test that logging setup creates directory for log file if needed"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "nested" / "dir" / "test.log"
            
            logger = setup_logging(log_file=str(log_file))
            
            # Directory should be created
            assert log_file.parent.exists()
            assert log_file.parent.is_dir()
            
            # Log file should be created
            logger.info("Test")
            assert log_file.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])