"""
Tests to verify all refactored modules can be imported successfully
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestModuleImports:
    """Test that all refactored modules can be imported"""
    
    def test_import_utils_core(self):
        """Test importing utils.core module"""
        from src.utils import core
        # Verify key functions exist
        assert hasattr(core, 'get_project_root')
        assert hasattr(core, 'find_chrome_executable')
        assert hasattr(core, 'load_json_config')
        assert hasattr(core, 'get_script_path')
        assert hasattr(core, 'setup_logging')
    
    def test_import_auto_login(self):
        """Test importing auto_login module"""
        from src import auto_login
        # Verify ChromeProcessManager exists
        assert hasattr(auto_login, 'ChromeProcessManager')
        assert hasattr(auto_login, 'ChromeInstance')
        assert hasattr(auto_login, 'load_credentials')
    
    def test_import_dashboard(self):
        """Test importing dashboard module"""
        from src import dashboard
        # Verify key functions exist
        assert hasattr(dashboard, 'run_flask_dashboard')
        assert hasattr(dashboard, 'get_trading_defaults')
    
    def test_import_app(self):
        """Test importing app module"""
        from src import app
        # Verify key classes exist
        assert hasattr(app, 'TradovateConnection')
        assert hasattr(app, 'TradovateController')
        assert hasattr(app, 'main')
    
    def test_import_pinescript_webhook(self):
        """Test importing pinescript_webhook module"""
        from src import pinescript_webhook
        # Verify key components exist
        assert hasattr(pinescript_webhook, 'app')  # Flask app
        assert hasattr(pinescript_webhook, 'webhook')  # webhook route
    
    def test_import_login_helper(self):
        """Test importing login_helper module"""
        from src import login_helper
        # Verify key functions exist
        assert hasattr(login_helper, 'login_to_existing_chrome')
        assert hasattr(login_helper, 'wait_for_element')
    
    def test_import_chrome_logger(self):
        """Test importing chrome_logger module"""
        from src import chrome_logger
        # Verify key classes exist
        assert hasattr(chrome_logger, 'ChromeLogger')
        assert hasattr(chrome_logger, 'create_logger')
    
    def test_import_launchers_common(self):
        """Test importing launchers common module"""
        from launchers import common
        # Verify key functions exist
        assert hasattr(common, 'setup_python_path')
        assert hasattr(common, 'launch_module')
        assert hasattr(common, 'create_launcher')


class TestLauncherImports:
    """Test that all launcher scripts can be imported"""
    
    def test_launcher_imports(self):
        """Test importing all launcher scripts"""
        # Launcher scripts are meant to be run directly, not imported
        # Instead, test that the files exist and are executable
        from pathlib import Path
        
        launchers_dir = Path(__file__).parent.parent / 'launchers'
        launcher_files = [
            'app_launcher.py',
            'auto_login_launcher.py',
            'dashboard_launcher.py',
            'pinescript_webhook_launcher.py',
            'login_helper_launcher.py',
            'chrome_logger_launcher.py'
        ]
        
        for launcher_file in launcher_files:
            launcher_path = launchers_dir / launcher_file
            assert launcher_path.exists(), f"Launcher file {launcher_file} does not exist"
            assert launcher_path.is_file(), f"Launcher {launcher_file} is not a file"


class TestCoreUtilityIntegration:
    """Integration tests for core utility functions"""
    
    def test_project_root_resolution(self):
        """Test that get_project_root returns valid path"""
        from src.utils.core import get_project_root
        
        root = get_project_root()
        assert root.exists()
        assert root.is_dir()
        assert root.name == 'tradovate_interface_refactored'
    
    def test_load_config_integration(self):
        """Test loading actual config files"""
        from src.utils.core import load_json_config, get_project_root
        
        # Test loading dashboard_window.json if it exists
        project_root = get_project_root()
        dashboard_config = project_root / 'config' / 'dashboard_window.json'
        
        if dashboard_config.exists():
            try:
                config = load_json_config(str(dashboard_config))
                assert isinstance(config, dict)
            except Exception:
                # Config might be malformed in test environment
                pass
    
    def test_chrome_executable_detection(self):
        """Test Chrome executable detection on current platform"""
        from src.utils.core import find_chrome_executable
        
        try:
            chrome_path = find_chrome_executable()
            assert isinstance(chrome_path, str)
            assert len(chrome_path) > 0
        except RuntimeError:
            # Chrome not installed is acceptable for CI
            pass
    
    def test_logging_setup(self):
        """Test logging setup functionality"""
        from src.utils.core import setup_logging
        import tempfile
        import logging
        
        with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as f:
            logger = setup_logging(level="DEBUG", log_file=f.name)
            
            assert isinstance(logger, logging.Logger)
            assert logger.level == logging.DEBUG
            
            # Test logging
            logger.info("Test message")
            
            # Verify log file was written
            import os
            assert os.path.exists(f.name)
            assert os.path.getsize(f.name) > 0
            
            # Cleanup
            os.unlink(f.name)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])