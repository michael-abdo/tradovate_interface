"""
Core utility functions for the Tradovate Interface.

This module contains shared utility functions to eliminate code duplication
across the project, including Chrome path detection, project root resolution,
configuration loading, and logging setup.
"""

import json
import yaml
import logging
import os
import platform
import sys
from pathlib import Path
from typing import Dict, Any, Optional


def get_project_root() -> Path:
    """Get the project root directory using Path-based implementation.
    
    Searches upward from current file location for common project markers:
    - .git directory
    - requirements.txt file
    - setup.py file
    - src directory with __init__.py
    
    Returns:
        Path: The project root directory
        
    Raises:
        RuntimeError: If project root cannot be determined
    """
    current_path = Path(__file__).resolve()
    
    # Search upward for project markers
    for parent in [current_path] + list(current_path.parents):
        # Check for common project markers
        if any(parent.joinpath(marker).exists() for marker in [
            '.git',
            'requirements.txt', 
            'setup.py',
            'pyproject.toml'
        ]):
            return parent
            
        # Check for src directory with __init__.py (common Python project structure)
        src_path = parent / 'src'
        if src_path.is_dir() and (src_path / '__init__.py').exists():
            return parent
    
    # Fallback: use the directory containing this file's parent directory
    # (assumes project structure where utils is in src/utils/)
    return current_path.parent.parent.parent


def find_chrome_executable() -> str:
    """Find Chrome executable path with cross-platform detection.
    
    Searches for Chrome executable in platform-specific default locations:
    - macOS: /Applications/Google Chrome.app/Contents/MacOS/Google Chrome
    - Windows: Various Program Files locations
    - Linux: /usr/bin/google-chrome, /usr/bin/chromium-browser, etc.
    
    Returns:
        str: Path to Chrome executable
        
    Raises:
        RuntimeError: If Chrome executable cannot be found
    """
    system = platform.system().lower()
    
    if system == 'darwin':  # macOS
        chrome_paths = [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '/Applications/Chromium.app/Contents/MacOS/Chromium'
        ]
    elif system == 'windows':  # Windows
        import winreg
        chrome_paths = []
        
        # Try to get Chrome path from registry
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe")
            path, _ = winreg.QueryValueEx(key, "")
            chrome_paths.append(path)
            winreg.CloseKey(key)
        except (OSError, FileNotFoundError):
            pass
            
        # Fallback to common installation paths
        chrome_paths.extend([
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(
                os.environ.get('USERNAME', '')),
            r"C:\Program Files\Chromium\Application\chromium.exe",
            r"C:\Program Files (x86)\Chromium\Application\chromium.exe"
        ])
    else:  # Linux and other Unix-like systems
        chrome_paths = [
            '/usr/bin/google-chrome',
            '/usr/bin/google-chrome-stable', 
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium',
            '/snap/bin/chromium',
            '/usr/local/bin/chrome',
            '/opt/google/chrome/chrome'
        ]
    
    # Check each potential path
    for chrome_path in chrome_paths:
        if chrome_path and os.path.isfile(chrome_path) and os.access(chrome_path, os.X_OK):
            return chrome_path
    
    # If no path found, raise error
    raise RuntimeError(
        f"Chrome executable not found on {system}. "
        f"Searched paths: {chrome_paths}"
    )


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration file with support for both JSON and YAML formats.
    
    Automatically detects the file format based on extension and uses the
    appropriate parser. Supports .json, .yaml, and .yml extensions.
    
    Args:
        config_path: Path to the configuration file (relative or absolute)
        
    Returns:
        Dict[str, Any]: Parsed configuration data
        
    Raises:
        FileNotFoundError: If configuration file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
        yaml.YAMLError: If file contains invalid YAML
        PermissionError: If file cannot be read due to permissions
    """
    # Convert to Path object for consistent handling
    config_file = Path(config_path)
    
    # If path is relative, make it relative to project root
    if not config_file.is_absolute():
        project_root = get_project_root()
        config_file = project_root / config_file
    
    # Try alternate formats if base file doesn't exist
    original_file = config_file
    possible_files = []
    
    # If file has no extension or doesn't exist, try common extensions
    if not config_file.exists():
        base_path = config_file.with_suffix('')
        for ext in ['.yaml', '.yml', '.json']:
            candidate = base_path.with_suffix(ext)
            possible_files.append(candidate)
            if candidate.exists():
                config_file = candidate
                break
    else:
        possible_files = [config_file]
    
    # Check if file exists
    if not config_file.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {original_file}\n"
            f"Searched locations: {', '.join(str(f) for f in possible_files)}"
        )
    
    # Check if file is readable
    if not config_file.is_file():
        raise ValueError(f"Path is not a file: {config_file}")
    
    # Determine file format based on extension
    file_ext = config_file.suffix.lower()
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            if file_ext in ['.yaml', '.yml']:
                # Use safe_load to prevent arbitrary code execution
                config_data = yaml.safe_load(f)
            elif file_ext == '.json':
                config_data = json.load(f)
            else:
                # Try JSON first, then YAML
                content = f.read()
                try:
                    config_data = json.loads(content)
                except json.JSONDecodeError:
                    config_data = yaml.safe_load(content)
        
        return config_data
        
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in configuration file {config_file}: {e.msg}",
            e.doc, e.pos
        )
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in configuration file {config_file}: {e}")
    except PermissionError as e:
        raise PermissionError(f"Cannot read configuration file {config_file}: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error loading configuration {config_file}: {e}")


def load_json_config(config_path: str) -> Dict[str, Any]:
    """Load JSON configuration file with error handling.
    
    This function now supports both JSON and YAML formats by delegating
    to load_config(). It maintains backward compatibility while adding
    YAML support.
    
    Args:
        config_path: Path to the configuration file (relative or absolute)
        
    Returns:
        Dict[str, Any]: Parsed configuration data
        
    Raises:
        FileNotFoundError: If configuration file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
        yaml.YAMLError: If file contains invalid YAML
        PermissionError: If file cannot be read due to permissions
    """
    return load_config(config_path)


def get_script_path(script_name: str) -> Path:
    """Get consistent script path resolution.
    
    Resolves script paths relative to the project root, handling various
    common script locations and file extensions.
    
    Args:
        script_name: Name of the script file (with or without extension)
        
    Returns:
        Path: Absolute path to the script file
        
    Raises:
        FileNotFoundError: If script cannot be found in expected locations
    """
    project_root = get_project_root()
    
    # Add .py extension if not present
    if not script_name.endswith(('.py', '.js', '.sh')):
        script_name += '.py'
    
    # Common script locations to search
    search_paths = [
        project_root / script_name,  # Root directory
        project_root / 'src' / script_name,  # src directory
        project_root / 'scripts' / script_name,  # scripts directory
        project_root / 'launchers' / script_name,  # launchers directory
        project_root / 'bin' / script_name,  # bin directory
        project_root / 'tools' / script_name,  # tools directory
    ]
    
    # Search for the script in common locations
    for script_path in search_paths:
        if script_path.exists() and script_path.is_file():
            return script_path.resolve()
    
    # If not found, raise error with searched locations
    raise FileNotFoundError(
        f"Script '{script_name}' not found in any of the following locations: "
        f"{[str(p) for p in search_paths]}"
    )


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True
) -> logging.Logger:
    """Setup standardized logging with console and optional file logging.
    
    Creates a standardized logger configuration with consistent formatting
    across all modules in the project.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file (relative to project root)
        console_output: Whether to enable console logging output
        
    Returns:
        logging.Logger: Configured logger instance
        
    Raises:
        ValueError: If invalid logging level is provided
    """
    # Validate logging level
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {level}')
    
    # Create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(numeric_level)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Define consistent log format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    
    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Add file handler if log file specified
    if log_file:
        # Convert to Path object and resolve relative paths
        log_path = Path(log_file)
        if not log_path.is_absolute():
            project_root = get_project_root()
            log_path = project_root / log_path
        
        # Create log directory if it doesn't exist
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create file handler
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger