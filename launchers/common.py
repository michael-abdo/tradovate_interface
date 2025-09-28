"""
Common launcher utilities for the Tradovate Interface.

This module contains shared utilities for launching Python modules,
eliminating boilerplate code across individual launcher scripts.
"""

import sys
import os
from pathlib import Path
from typing import Optional, List


def setup_python_path(project_root: Optional[Path] = None) -> Path:
    """Set up Python path to ensure modules can be imported correctly.
    
    Args:
        project_root: Optional project root path. If None, will auto-detect.
        
    Returns:
        Path: The project root directory
    """
    if project_root is None:
        # Assume launchers are in {project_root}/launchers/
        launcher_path = Path(__file__).resolve()
        project_root = launcher_path.parent.parent
    
    # Add project root to Python path if not already there
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
    
    return project_root


def launch_module(module_path: str, args: Optional[List[str]] = None) -> None:
    """Generic function to launch a Python module.
    
    Args:
        module_path: Dot-separated module path (e.g., 'src.app')
        args: Optional list of command-line arguments to pass to the module
    """
    # Set up Python path
    project_root = setup_python_path()
    
    # Set up arguments
    if args:
        sys.argv[1:] = args
    
    try:
        # Import and run the module
        if module_path.endswith('.py'):
            # Handle file path format
            module_path = module_path.replace('/', '.').replace('\\', '.').replace('.py', '')
        
        # Dynamic import
        parts = module_path.split('.')
        module = __import__(module_path)
        
        # Navigate to the actual module
        for part in parts[1:]:
            module = getattr(module, part)
            
        # Check if module has a main function or __main__ section
        if hasattr(module, 'main'):
            module.main()
        elif hasattr(module, '__main__'):
            # Module has if __name__ == '__main__': block
            # It will execute automatically on import
            pass
        else:
            print(f"Warning: Module {module_path} has no main() function")
            
    except ImportError as e:
        print(f"Error: Failed to import module '{module_path}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to launch module '{module_path}': {e}")
        sys.exit(1)


def create_launcher(module_path: str, description: str = "") -> None:
    """Create a launcher function for a specific module.
    
    This is a factory function that creates module-specific launchers.
    
    Args:
        module_path: Dot-separated module path (e.g., 'src.app')
        description: Optional description of what the module does
        
    Returns:
        A function that launches the specified module
    """
    def launcher():
        """Launch the module."""
        if description:
            print(f"Launching: {description}")
        launch_module(module_path, sys.argv[1:])
    
    launcher.__doc__ = f"Launch {module_path}" + (f" - {description}" if description else "")
    return launcher