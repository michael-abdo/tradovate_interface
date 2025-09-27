# DRY Refactoring Guide for Tradovate Interface

## Overview

This document provides a meticulous, step-by-step procedure to eliminate high-priority DRY (Don't Repeat Yourself) violations throughout the Tradovate Interface codebase. The focus is on real-world duplication that causes bugs, rework, or inconsistencies, ignoring minor duplication in tests, logs, or documentation.

## Executive Summary

The codebase contains **8 major categories** of duplication that create maintenance burden and increase bug risk:

1. **Chrome Path Detection** - Critical system compatibility issue
2. **Project Root Resolution** - 10+ identical lines across modules  
3. **Chrome Process Management** - Complex cleanup logic duplicated
4. **Logging Configuration** - Inconsistent setup patterns
5. **Script Path Construction** - Repeated Tampermonkey script loading
6. **Configuration File Loading** - JSON handling duplication
7. **Launcher Boilerplate** - Identical imports across 6 files
8. **Chrome Tab Management** - Browser connection logic repeated

---

## Step-by-Step Refactoring Procedure

### Step 1: Create Core Utility Module ⭐ **HIGH PRIORITY**

**Problem**: Project root path resolution is duplicated 10+ times across the codebase.

**Canonical Source**: Create `src/utils/core.py` (new utility module)

**Implementation**:

1. **Create the utility module**:
   ```python
   # src/utils/core.py
   import os
   import platform
   import json
   import logging
   from typing import Optional, Dict, Any

   def get_project_root() -> str:
       """Get the project root directory path.
       
       Returns:
           str: Absolute path to the project root directory
       """
       return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

   def get_chrome_executable_path() -> Optional[str]:
       """Detect Chrome executable path across platforms.
       
       Returns:
           Optional[str]: Path to Chrome executable or None if not found
       """
       system = platform.system().lower()
       
       if system == "darwin":  # macOS
           return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
       elif system == "windows":
           paths = [
               r"C:\Program Files\Google\Chrome\Application\chrome.exe",
               r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
           ]
           for path in paths:
               if os.path.exists(path):
                   return path
       elif system == "linux":
           paths = ["/usr/bin/google-chrome", "/usr/bin/chromium-browser"]
           for path in paths:
               if os.path.exists(path):
                   return path
       
       return None

   def load_json_config(config_path: str, default: Dict[str, Any] = None) -> Dict[str, Any]:
       """Load JSON configuration with error handling and defaults.
       
       Args:
           config_path: Path to the JSON configuration file
           default: Default configuration to return if file doesn't exist
           
       Returns:
           Dict containing configuration data
       """
       if default is None:
           default = {}
           
       try:
           if os.path.exists(config_path):
               with open(config_path, 'r') as f:
                   return json.load(f)
           else:
               logging.warning(f"Config file not found: {config_path}, using defaults")
               return default
       except json.JSONDecodeError as e:
           logging.error(f"Invalid JSON in {config_path}: {e}")
           return default
       except Exception as e:
           logging.error(f"Error loading config {config_path}: {e}")
           return default

   def get_script_path(script_name: str) -> str:
       """Get full path to a Tampermonkey script.
       
       Args:
           script_name: Name of the script file
           
       Returns:
           str: Full path to the script file
       """
       project_root = get_project_root()
       return os.path.join(project_root, 'scripts', 'tampermonkey', script_name)
   ```

2. **Update existing files to use utility functions**:

   **In `src/auto_login.py`** - Replace lines 24, 811, 876, 896:
   ```python
   # Remove: project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
   # Add at top:
   from .utils.core import get_project_root, get_chrome_executable_path, get_script_path

   # Replace all instances of project_root calculation with:
   project_root = get_project_root()
   ```

   **In `src/dashboard.py`** - Replace lines 14, 74, 103, 633, 657:
   ```python
   # Add at top:
   from .utils.core import get_project_root, get_script_path, load_json_config

   # Replace project_root calculations and script path constructions
   ```

   **In `src/app.py`** - Replace lines 10, 79, 89:
   ```python
   # Add at top:
   from .utils.core import get_project_root, get_script_path

   # Replace project_root calculations
   ```

   **In `start_all.py`** - Replace line 24:
   ```python
   # Add after other imports:
   from src.utils.core import get_project_root, get_chrome_executable_path

   # Replace: project_root = os.path.dirname(os.path.abspath(__file__))
   project_root = get_project_root()
   ```

**Verification**: Run `python3 -m pytest tests/` to ensure all modules still import correctly.

---

### Step 2: Consolidate Chrome Process Management ⭐ **HIGH PRIORITY**

**Problem**: Chrome process creation, management, and cleanup logic is duplicated between `auto_login.py` and `start_all.py` with slight variations.

**Canonical Source**: Extend `src/auto_login.py` (has most comprehensive implementation)

**Implementation**:

1. **Extract Chrome management class in `src/auto_login.py`**:
   ```python
   class ChromeProcessManager:
       """Manages Chrome process lifecycle and configuration."""
       
       def __init__(self, username: str, port: int, profile_dir: str = None):
           self.username = username
           self.port = port
           self.profile_dir = profile_dir or f"/tmp/tradovate_{username}_{port}"
           self.process = None
           self.chrome_path = get_chrome_executable_path()
           
       def build_chrome_args(self, url: str = None) -> List[str]:
           """Build standardized Chrome command line arguments."""
           if not self.chrome_path:
               raise RuntimeError("Chrome executable not found")
               
           args = [
               self.chrome_path,
               f"--remote-debugging-port={self.port}",
               f"--user-data-dir={self.profile_dir}",
               "--no-first-run",
               "--no-default-browser-check",
               "--disable-notifications",
               "--disable-popup-blocking",
               "--disable-infobars",
               "--disable-session-crashed-bubble",
               "--disable-save-password-bubble",
               "--disable-features=InfiniteSessionRestore",
               "--hide-crash-restore-bubble",
               "--no-crash-upload",
               "--disable-backgrounding-occluded-windows",
               "--disable-dev-shm-usage",
               "--no-sandbox",
               "--disable-gpu-compositing",
               "--disable-background-timer-throttling",
               "--disable-renderer-backgrounding",
               "--disable-features=TranslateUI",
               "--disable-ipc-flooding-protection"
           ]
           
           if url:
               args.append(url)
               
           return args
           
       def start(self, url: str = None) -> subprocess.Popen:
           """Start Chrome process with standardized configuration."""
           os.makedirs(self.profile_dir, exist_ok=True)
           args = self.build_chrome_args(url)
           self.process = subprocess.Popen(args)
           return self.process
           
       def cleanup(self, timeout: int = 5):
           """Clean up Chrome process with graceful -> force escalation."""
           if not self.process or self.process.poll() is not None:
               return
               
           try:
               # Try graceful termination first
               self.process.terminate()
               self.process.wait(timeout=timeout)
           except subprocess.TimeoutExpired:
               # Force kill if graceful fails
               self.process.kill()
               self.process.wait()
   ```

2. **Update `start_all.py` to use ChromeProcessManager**:
   ```python
   # In run_dashboard() function, replace Chrome launch code with:
   from src.auto_login import ChromeProcessManager
   
   dashboard_manager = ChromeProcessManager("dashboard", 9321)
   dashboard_chrome_process = dashboard_manager.start("http://localhost:6001")
   ```

3. **Consolidate cleanup logic**: Move the comprehensive cleanup from `start_all.py` into the `ChromeProcessManager` class.

**Verification**: Start the system with `python3 start_all.py --background` and verify both login and dashboard Chrome instances launch correctly.

---

### Step 3: Standardize Configuration Loading ⭐ **HIGH PRIORITY**

**Problem**: JSON configuration loading is duplicated in `dashboard.py` (lines 17-47, 874-904) and `auto_login.py` (lines 873-891).

**Canonical Source**: Use the `load_json_config` utility created in Step 1

**Implementation**:

1. **Replace in `src/dashboard.py`**:
   ```python
   # Remove lines 17-47 (duplicate config loading)
   # Replace with:
   from .utils.core import load_json_config, get_project_root

   def load_dashboard_config():
       project_root = get_project_root()
       config_path = os.path.join(project_root, 'config', 'dashboard_window.json')
       default_config = {
           "width": 1200,
           "height": 800,
           "x": 100,
           "y": 100
       }
       return load_json_config(config_path, default_config)
   ```

2. **Replace in `src/auto_login.py`**:
   ```python
   # Replace config loading logic with:
   from .utils.core import load_json_config, get_project_root

   def load_credentials():
       project_root = get_project_root()
       config_path = os.path.join(project_root, 'config', 'credentials.json')
       return load_json_config(config_path, {})
   ```

**Verification**: Test configuration loading by running the dashboard and login modules independently.

---

### Step 4: Eliminate Launcher Boilerplate ⭐ **MEDIUM PRIORITY**

**Problem**: Identical import boilerplate repeated in 6 launcher files.

**Canonical Source**: Create `launchers/common.py` (new shared module)

**Implementation**:

1. **Create shared launcher utility**:
   ```python
   # launchers/common.py
   import sys
   import os

   def setup_project_path():
       """Add project root to Python path for imports."""
       project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
       if project_root not in sys.path:
           sys.path.insert(0, project_root)
       return project_root

   def launch_module(module_name: str, main_function: str = "main"):
       """Generic module launcher with proper path setup."""
       setup_project_path()
       
       try:
           module = __import__(module_name, fromlist=[main_function])
           main_func = getattr(module, main_function)
           return main_func()
       except ImportError as e:
           print(f"Failed to import {module_name}: {e}")
           sys.exit(1)
       except AttributeError as e:
           print(f"Function {main_function} not found in {module_name}: {e}")
           sys.exit(1)
   ```

2. **Simplify all launcher files**:
   ```python
   # Example: launchers/app_launcher.py
   from .common import launch_module

   if __name__ == "__main__":
       launch_module("src.app")
   ```

**Verification**: Test each launcher to ensure modules still load correctly.

---

### Step 5: Consolidate Logging Configuration ⭐ **MEDIUM PRIORITY**

**Problem**: Logging setup is inconsistent across modules, with duplicate global variables in `auto_login.py`.

**Canonical Source**: Extend `src/utils/core.py`

**Implementation**:

1. **Add to `src/utils/core.py`**:
   ```python
   def setup_logging(log_level: str = "INFO", log_file: str = None) -> logging.Logger:
       """Configure standardized logging across the application.
       
       Args:
           log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
           log_file: Optional log file path
           
       Returns:
           Configured logger instance
       """
       logger = logging.getLogger()
       logger.setLevel(getattr(logging, log_level.upper()))
       
       # Clear existing handlers
       for handler in logger.handlers[:]:
           logger.removeHandler(handler)
       
       # Console handler
       console_handler = logging.StreamHandler()
       console_format = logging.Formatter(
           '[%(asctime)s] %(levelname)s - %(message)s',
           datefmt='%H:%M:%S'
       )
       console_handler.setFormatter(console_format)
       logger.addHandler(console_handler)
       
       # File handler if specified
       if log_file:
           file_handler = logging.FileHandler(log_file)
           file_format = logging.Formatter(
               '[%(asctime)s] %(name)s - %(levelname)s - %(message)s'
           )
           file_handler.setFormatter(file_format)
           logger.addHandler(file_handler)
       
       return logger
   ```

2. **Replace logging setup in affected files**:
   - Remove duplicate global variables in `auto_login.py` (lines 29-32 and 154-157)
   - Replace logging configuration with calls to `setup_logging()`

**Verification**: Check log output consistency across all modules.

---

### Step 6: Unify Chrome Tab Management ⭐ **MEDIUM PRIORITY**

**Problem**: Browser tab enumeration and Tradovate tab detection duplicated in `auto_login.py` and `app.py`.

**Canonical Source**: `src/auto_login.py` (more comprehensive implementation)

**Implementation**:

1. **Extract tab management class in `src/auto_login.py`**:
   ```python
   class ChromeTabManager:
       """Manages Chrome tab connections and Tradovate detection."""
       
       def __init__(self, port: int):
           self.port = port
           self.browser = None
           
       def connect(self):
           """Connect to Chrome debugging interface."""
           import pychrome
           self.browser = pychrome.Browser(url=f"http://localhost:{self.port}")
           
       def find_tradovate_tab(self) -> Optional[object]:
           """Find and return Tradovate tab."""
           if not self.browser:
               self.connect()
               
           for tab in self.browser.list_tab():
               if 'tradovate.com' in tab.url.lower():
                   tab.start()
                   return tab
           return None
           
       def get_all_tabs(self) -> List[object]:
           """Get all available tabs."""
           if not self.browser:
               self.connect()
           return self.browser.list_tab()
   ```

2. **Update `src/app.py`** to use `ChromeTabManager` instead of duplicate tab logic.

**Verification**: Test tab detection and connection functionality.

---

### Step 7: Remove Global Variable Duplication ⭐ **LOW PRIORITY**

**Problem**: Global logging variables declared twice in `auto_login.py`.

**Canonical Source**: `src/auto_login.py` (remove duplicate declarations)

**Implementation**:

1. **Remove duplicate global variables** in `auto_login.py` (lines 154-157):
   ```python
   # Remove these duplicate lines:
   # log_directory = None  # Global variable for Chrome console logging
   # terminal_callback = None  # Global variable for terminal output callback  
   # register_chrome_logger = None  # Global variable for ChromeLogger registration
   # logger = logging.getLogger(__name__)
   ```

2. **Keep only the original declarations** (lines 29-32).

**Verification**: Ensure no undefined variable errors occur.

---

## Manual Testing Verification

After completing each step, verify the following high-value flows:

### Core Startup Flow
1. **Test**: `python3 start_all.py --background`
2. **Verify**: Both Chrome instances launch correctly
3. **Verify**: Dashboard loads at http://localhost:6001
4. **Verify**: Auto-login processes complete without errors

### Configuration Loading  
1. **Test**: Modify `config/credentials.json` and `config/dashboard_window.json`
2. **Verify**: Changes are properly loaded by respective modules
3. **Verify**: Error handling works with invalid JSON

### Chrome Process Cleanup
1. **Test**: Send SIGINT to `start_all.py` process
2. **Verify**: All Chrome processes terminate within 15 seconds
3. **Verify**: No zombie processes remain

### Script Injection
1. **Test**: Login to Tradovate through auto_login
2. **Verify**: Tampermonkey scripts are properly injected
3. **Verify**: Trading functions are available in browser console

---

## Documentation Updates

### Essential Updates Only

1. **Update `README.md`** - Add note about new utility modules
2. **Update `CLAUDE.md`** - Document the refactored architecture
3. **Inline comments** - Update function docstrings for refactored methods

---

## Risk Assessment

### Low Risk Refactoring
- Steps 1, 4, 5, 7 (utility consolidation)

### Medium Risk Refactoring  
- Steps 3, 6 (configuration and tab management)

### High Risk Refactoring
- Step 2 (Chrome process management)

**Recommendation**: Implement steps 1, 4, 5, 7 first to build confidence, then tackle steps 2, 3, 6 with comprehensive testing.

---

## Success Metrics

- **Reduced Lines of Code**: ~200+ lines eliminated through deduplication
- **Maintenance Burden**: Single source of truth for each duplicated pattern
- **Bug Risk**: Eliminated inconsistency between duplicate implementations  
- **Developer Experience**: Cleaner imports and standardized patterns

---

## File Change Summary

**New Files Created**:
- `src/utils/core.py` - Core utilities
- `launchers/common.py` - Launcher utilities

**Files Modified**:
- `src/auto_login.py` - Use utilities, extract Chrome manager
- `src/dashboard.py` - Use utilities, remove config duplication  
- `src/app.py` - Use utilities, remove tab management duplication
- `start_all.py` - Use utilities and Chrome manager
- All `launchers/*.py` files - Use common launcher pattern

**Files Deleted**: None (preserves existing functionality)

---

*This refactoring guide prioritizes high-impact changes that eliminate real maintenance burden while preserving all existing functionality.*