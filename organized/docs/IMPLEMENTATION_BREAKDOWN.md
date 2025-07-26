# Chrome Process Restart Logic - Atomic Implementation Breakdown

## Overview
This document provides atomic, step-by-step breakdowns for implementing Chrome process restart logic to fix start_all.py crashes. Each step is designed to be executed independently and tested incrementally.

## Phase 1: Fix the Immediate Crash (Essential)

### Task 1.1: Add Comprehensive Error Handling to start_all.py

#### Step 1.1.1: Backup and Prepare (5 minutes)
1. **Create backup of start_all.py**
   ```bash
   cp /Users/Mike/trading/start_all.py /Users/Mike/trading/start_all.py.backup
   ```

2. **Verify backup created successfully**
   ```bash
   ls -la /Users/Mike/trading/start_all.py*
   ```

3. **Open start_all.py in editor**
   ```bash
   code /Users/Mike/trading/start_all.py
   ```

#### Step 1.1.2: Create StartupManager Class (45 minutes)

4. **Add imports at top of file (after existing imports)**
   ```python
   import socket
   import requests
   import psutil
   from typing import Dict, List, Optional, Tuple
   import json
   from datetime import datetime
   ```

5. **Create StartupManager class before main() function**
   ```python
   class StartupManager:
       """Manages Chrome startup with error handling and retry logic"""
       
       def __init__(self):
           self.max_retries = 3
           self.retry_delay = 10
           self.startup_timeout = 60
           self.required_ports = [9223, 9224]
           self.startup_log = []
   ```

6. **Add log_event method to StartupManager**
   ```python
   def log_event(self, event: str, details: str = "", success: bool = True):
       """Log startup events for debugging"""
       timestamp = datetime.now().isoformat()
       log_entry = {
           'timestamp': timestamp,
           'event': event,
           'details': details,
           'success': success
       }
       self.startup_log.append(log_entry)
       status = "SUCCESS" if success else "FAILURE"
       print(f"[{timestamp}] STARTUP {status}: {event} - {details}")
   ```

#### Step 1.1.3: Add Prerequisite Validation Methods (45 minutes)

7. **Add validate_ports method**
   ```python
   def validate_ports(self) -> bool:
       """Check if required ports are available"""
       try:
           for port in self.required_ports:
               sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
               sock.settimeout(2)
               result = sock.connect_ex(('localhost', port))
               sock.close()
               
               if result == 0:
                   self.log_event("port_validation", f"Port {port} already in use", False)
                   return False
           
           self.log_event("port_validation", f"Ports {self.required_ports} available", True)
           return True
           
       except Exception as e:
           self.log_event("port_validation", f"Port check failed: {e}", False)
           return False
   ```

8. **Add validate_memory method**
   ```python
   def validate_memory(self) -> bool:
       """Check if sufficient memory is available"""
       try:
           memory = psutil.virtual_memory()
           available_gb = memory.available / (1024**3)
           required_gb = 2.0  # Require 2GB available
           
           if available_gb < required_gb:
               self.log_event("memory_validation", 
                            f"Insufficient memory: {available_gb:.1f}GB < {required_gb}GB", False)
               return False
           
           self.log_event("memory_validation", f"Memory available: {available_gb:.1f}GB", True)
           return True
           
       except Exception as e:
           self.log_event("memory_validation", f"Memory check failed: {e}", False)
           return False
   ```

9. **Add validate_network method**
   ```python
   def validate_network(self) -> bool:
       """Check network connectivity to Tradovate"""
       try:
           response = requests.get("https://trader.tradovate.com", timeout=10)
           if response.status_code == 200:
               self.log_event("network_validation", "Tradovate accessible", True)
               return True
           else:
               self.log_event("network_validation", 
                            f"Tradovate returned {response.status_code}", False)
               return False
               
       except Exception as e:
           self.log_event("network_validation", f"Network check failed: {e}", False)
           return False
   ```

10. **Add validate_chrome_executable method**
    ```python
    def validate_chrome_executable(self) -> bool:
        """Check if Chrome executable exists and is accessible"""
        try:
            from src.auto_login import find_chrome_path
            chrome_path = find_chrome_path()
            
            if os.path.exists(chrome_path):
                self.log_event("chrome_validation", f"Chrome found at {chrome_path}", True)
                return True
            else:
                self.log_event("chrome_validation", f"Chrome not found at {chrome_path}", False)
                return False
                
        except Exception as e:
            self.log_event("chrome_validation", f"Chrome validation failed: {e}", False)
            return False
    ```

#### Step 1.1.4: Add Chrome Instance Validation Methods (30 minutes)

11. **Add validate_chrome_processes method**
    ```python
    def validate_chrome_processes(self) -> bool:
        """Verify Chrome processes are running on required ports"""
        try:
            running_processes = []
            
            for port in self.required_ports:
                # Check if process is listening on port
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if 'chrome' in proc.info['name'].lower():
                            cmdline = ' '.join(proc.info['cmdline'] or [])
                            if f'remote-debugging-port={port}' in cmdline:
                                running_processes.append({'port': port, 'pid': proc.info['pid']})
                                break
            
            if len(running_processes) == len(self.required_ports):
                self.log_event("chrome_processes", 
                             f"All Chrome instances running: {running_processes}", True)
                return True
            else:
                missing = set(self.required_ports) - {p['port'] for p in running_processes}
                self.log_event("chrome_processes", 
                             f"Missing Chrome processes for ports: {missing}", False)
                return False
                
        except Exception as e:
            self.log_event("chrome_processes", f"Process validation failed: {e}", False)
            return False
    ```

12. **Add validate_websocket_connections method**
    ```python
    def validate_websocket_connections(self) -> bool:
        """Test WebSocket connectivity to Chrome instances"""
        try:
            import pychrome
            successful_connections = 0
            
            for port in self.required_ports:
                try:
                    browser = pychrome.Browser(url=f"http://localhost:{port}")
                    tabs = browser.list_tab()
                    
                    if tabs:
                        # Test basic connectivity to first tab
                        tab = tabs[0]
                        tab.start()
                        result = tab.Runtime.evaluate(expression="1 + 1")
                        tab.stop()
                        
                        if result.get("result", {}).get("value") == 2:
                            successful_connections += 1
                            self.log_event("websocket_test", f"Port {port} responsive", True)
                        else:
                            self.log_event("websocket_test", f"Port {port} JavaScript failed", False)
                    else:
                        self.log_event("websocket_test", f"Port {port} no tabs", False)
                        
                except Exception as e:
                    self.log_event("websocket_test", f"Port {port} connection failed: {e}", False)
            
            if successful_connections == len(self.required_ports):
                self.log_event("websocket_validation", "All WebSocket connections working", True)
                return True
            else:
                self.log_event("websocket_validation", 
                             f"Only {successful_connections}/{len(self.required_ports)} connections working", False)
                return False
                
        except Exception as e:
            self.log_event("websocket_validation", f"WebSocket validation failed: {e}", False)
            return False
    ```

#### Step 1.1.5: Add Main Startup Logic (30 minutes)

13. **Add start_with_retry method**
    ```python
    def start_with_retry(self):
        """Start auto-login with comprehensive retry logic"""
        self.log_event("startup_begin", f"Starting with max {self.max_retries} retries")
        
        for attempt in range(self.max_retries):
            try:
                self.log_event("attempt_start", f"Attempt {attempt + 1}/{self.max_retries}")
                
                # Phase 1: Validate prerequisites
                if not self.validate_startup_prerequisites():
                    raise Exception("Prerequisite validation failed")
                
                # Phase 2: Start auto-login
                self.log_event("auto_login_start", "Starting auto-login process")
                result = run_auto_login()
                
                # Phase 3: Validate Chrome instances
                if not self.validate_chrome_startup():
                    raise Exception("Chrome startup validation failed")
                
                self.log_event("startup_success", f"Startup completed on attempt {attempt + 1}")
                return result
                
            except Exception as e:
                is_final_attempt = (attempt == self.max_retries - 1)
                self.handle_startup_failure(e, attempt + 1, is_final_attempt)
                
                if is_final_attempt:
                    self.log_event("startup_failed", f"All {self.max_retries} attempts failed")
                    raise Exception(f"Startup failed after {self.max_retries} attempts. Last error: {e}")
    ```

14. **Add validate_startup_prerequisites method**
    ```python
    def validate_startup_prerequisites(self) -> bool:
        """Run all prerequisite validations"""
        validations = [
            ("ports", self.validate_ports),
            ("memory", self.validate_memory),
            ("network", self.validate_network),
            ("chrome_executable", self.validate_chrome_executable)
        ]
        
        for name, validation_func in validations:
            if not validation_func():
                self.log_event("prerequisite_failed", f"{name} validation failed", False)
                return False
        
        self.log_event("prerequisites_ok", "All prerequisite validations passed", True)
        return True
    ```

15. **Add validate_chrome_startup method**
    ```python
    def validate_chrome_startup(self) -> bool:
        """Validate Chrome instances started successfully"""
        import time
        
        # Wait for Chrome to fully start
        self.log_event("chrome_wait", f"Waiting {self.startup_timeout}s for Chrome startup")
        time.sleep(self.startup_timeout)
        
        validations = [
            ("processes", self.validate_chrome_processes),
            ("websockets", self.validate_websocket_connections)
        ]
        
        for name, validation_func in validations:
            if not validation_func():
                self.log_event("chrome_validation_failed", f"{name} validation failed", False)
                return False
        
        self.log_event("chrome_startup_ok", "Chrome startup validation passed", True)
        return True
    ```

16. **Add handle_startup_failure method**
    ```python
    def handle_startup_failure(self, error: Exception, attempt: int, is_final: bool):
        """Handle startup failure with cleanup and retry logic"""
        self.log_event("attempt_failed", f"Attempt {attempt} failed: {error}", False)
        
        # Cleanup any partial Chrome instances
        self.cleanup_failed_startup()
        
        if not is_final:
            self.log_event("retry_wait", f"Waiting {self.retry_delay}s before retry")
            time.sleep(self.retry_delay)
    ```

17. **Add cleanup_failed_startup method**
    ```python
    def cleanup_failed_startup(self):
        """Clean up any partially started Chrome instances"""
        try:
            self.log_event("cleanup_start", "Cleaning up failed startup")
            
            # Kill any Chrome processes on our ports
            for port in self.required_ports:
                subprocess.run(["pkill", "-f", f"remote-debugging-port={port}"], 
                             capture_output=True)
            
            self.log_event("cleanup_complete", "Cleanup completed")
            
        except Exception as e:
            self.log_event("cleanup_failed", f"Cleanup failed: {e}", False)
    ```

18. **Add get_startup_report method**
    ```python
    def get_startup_report(self) -> dict:
        """Get detailed startup report for debugging"""
        return {
            'total_events': len(self.startup_log),
            'success_events': len([e for e in self.startup_log if e['success']]),
            'failure_events': len([e for e in self.startup_log if not e['success']]),
            'events': self.startup_log
        }
    ```

#### Step 1.1.6: Modify main() Function (30 minutes)

19. **Replace auto-login calls in main() function**
    - Find the existing calls to `run_auto_login()` in both background and foreground modes
    - Replace with StartupManager usage

20. **For background mode (around line 180)**
    ```python
    # Replace this block:
    # auto_login_process = subprocess.Popen(...)
    
    # With this:
    try:
        startup_manager = StartupManager()
        print("Starting auto-login process with enhanced error handling...")
        startup_manager.start_with_retry()
        print("Auto-login completed successfully")
    except Exception as e:
        print(f"Startup failed: {e}")
        print("Startup report:")
        report = startup_manager.get_startup_report()
        for event in report['events'][-5:]:  # Show last 5 events
            status = "✓" if event['success'] else "✗"
            print(f"  {status} {event['event']}: {event['details']}")
        sys.exit(1)
    ```

21. **For foreground mode (around line 200)**
    ```python
    # Replace this block:
    # auto_login_thread = threading.Thread(target=run_auto_login)
    
    # With this:
    def enhanced_auto_login():
        try:
            startup_manager = StartupManager()
            return startup_manager.start_with_retry()
        except Exception as e:
            print(f"Auto-login thread failed: {e}")
            sys.exit(1)
    
    auto_login_thread = threading.Thread(target=enhanced_auto_login)
    ```

### Task 1.2: Add Startup Validation to auto_login.py

#### Step 1.2.1: Backup and Prepare (5 minutes)

22. **Create backup of auto_login.py**
    ```bash
    cp /Users/Mike/trading/src/auto_login.py /Users/Mike/trading/src/auto_login.py.backup
    ```

23. **Open auto_login.py in editor**
    ```bash
    code /Users/Mike/trading/src/auto_login.py
    ```

#### Step 1.2.2: Add Validation Methods to ChromeInstance (45 minutes)

24. **Add startup validation imports to auto_login.py**
    ```python
    # Add after existing imports
    from datetime import datetime
    from typing import Dict, Any, Optional
    from enum import Enum
    ```

25. **Create StartupPhase enum**
    ```python
    class StartupPhase(Enum):
        """Chrome instance startup phases"""
        INITIALIZING = "initializing"
        LAUNCHING_CHROME = "launching_chrome"
        CONNECTING_WEBSOCKET = "connecting_websocket"
        LOADING_TRADOVATE = "loading_tradovate"
        AUTHENTICATING = "authenticating"
        READY = "ready"
        FAILED = "failed"
    ```

26. **Add startup tracking to ChromeInstance.__init__**
    ```python
    # Add to __init__ method after existing attributes
    self.startup_phase = StartupPhase.INITIALIZING
    self.startup_start_time = None
    self.startup_errors = []
    self.startup_log = []
    ```

27. **Add log_startup_event method to ChromeInstance**
    ```python
    def log_startup_event(self, event: str, details: str = "", success: bool = True):
        """Log startup events for this instance"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'phase': self.startup_phase.value,
            'event': event,
            'details': details,
            'success': success,
            'username': self.username,
            'port': self.port
        }
        self.startup_log.append(log_entry)
        
        if not success:
            self.startup_errors.append(log_entry)
        
        status = "SUCCESS" if success else "FAILURE"
        print(f"[{timestamp}] {self.username}:{self.port} {status}: {event} - {details}")
    ```

28. **Add set_startup_phase method to ChromeInstance**
    ```python
    def set_startup_phase(self, phase: StartupPhase, details: str = ""):
        """Update startup phase with logging"""
        old_phase = self.startup_phase
        self.startup_phase = phase
        self.log_startup_event("phase_change", f"{old_phase.value} -> {phase.value}: {details}")
    ```

29. **Add start_with_validation method to ChromeInstance**
    ```python
    def start_with_validation(self, timeout: int = 60) -> bool:
        """Start Chrome instance with comprehensive validation"""
        self.startup_start_time = datetime.now()
        self.log_startup_event("startup_begin", f"Starting with {timeout}s timeout")
        
        try:
            # Phase 1: Launch Chrome
            self.set_startup_phase(StartupPhase.LAUNCHING_CHROME, "Starting Chrome process")
            self.process = start_chrome_with_debugging(self.port)
            
            if not self.process:
                self.set_startup_phase(StartupPhase.FAILED, "Chrome process failed to start")
                return False
            
            self.log_startup_event("chrome_launched", f"Chrome PID: {self.process.pid}")
            
            # Phase 2: Connect WebSocket
            self.set_startup_phase(StartupPhase.CONNECTING_WEBSOCKET, "Connecting to Chrome")
            self.browser, self.tab = connect_to_chrome(self.port)
            
            if not self.tab:
                self.set_startup_phase(StartupPhase.FAILED, "WebSocket connection failed")
                return False
            
            self.log_startup_event("websocket_connected", "Chrome WebSocket connected")
            
            # Phase 3: Load Tradovate
            self.set_startup_phase(StartupPhase.LOADING_TRADOVATE, "Loading Tradovate page")
            if not self.validate_tradovate_loaded():
                self.set_startup_phase(StartupPhase.FAILED, "Tradovate page load failed")
                return False
            
            # Phase 4: Authenticate
            self.set_startup_phase(StartupPhase.AUTHENTICATING, "Performing authentication")
            self.check_and_login_if_needed()
            
            if not self.validate_authentication():
                self.set_startup_phase(StartupPhase.FAILED, "Authentication failed")
                return False
            
            # Phase 5: Final validation
            disable_alerts(self.tab)
            
            if self.validate_ready_for_trading():
                self.set_startup_phase(StartupPhase.READY, "Instance ready for trading")
                
                # Start monitoring thread
                self.is_running = True
                self.login_monitor_thread = threading.Thread(
                    target=self.monitor_login_status,
                    daemon=True
                )
                self.login_monitor_thread.start()
                
                self.log_startup_event("startup_complete", f"Total time: {self.get_startup_duration()}s")
                return True
            else:
                self.set_startup_phase(StartupPhase.FAILED, "Final validation failed")
                return False
                
        except Exception as e:
            self.set_startup_phase(StartupPhase.FAILED, f"Exception: {e}")
            self.log_startup_event("startup_exception", str(e), False)
            return False
    ```

30. **Add validation helper methods to ChromeInstance**
    ```python
    def validate_tradovate_loaded(self) -> bool:
        """Verify Tradovate page is loaded and accessible"""
        try:
            result = self.tab.Runtime.evaluate(expression="document.location.href")
            url = result.get("result", {}).get("value", "")
            
            if "tradovate" in url.lower():
                self.log_startup_event("tradovate_loaded", f"URL: {url}")
                return True
            else:
                self.log_startup_event("tradovate_load_failed", f"Wrong URL: {url}", False)
                return False
                
        except Exception as e:
            self.log_startup_event("tradovate_load_error", str(e), False)
            return False
    
    def validate_authentication(self) -> bool:
        """Verify authentication was successful"""
        try:
            # Wait a moment for authentication to complete
            time.sleep(5)
            
            # Check if we're still on login page
            check_js = '''
            (function() {
                const emailInput = document.getElementById("name-input");
                const passwordInput = document.getElementById("password-input");
                return !emailInput && !passwordInput;
            })();
            '''
            
            result = self.tab.Runtime.evaluate(expression=check_js)
            authenticated = result.get("result", {}).get("value", False)
            
            if authenticated:
                self.log_startup_event("authentication_verified", "No login form visible")
                return True
            else:
                self.log_startup_event("authentication_failed", "Still on login page", False)
                return False
                
        except Exception as e:
            self.log_startup_event("authentication_error", str(e), False)
            return False
    
    def validate_ready_for_trading(self) -> bool:
        """Verify instance is ready for trading operations"""
        try:
            # Check for trading interface elements
            trading_check_js = '''
            (function() {
                const tradingElements = document.querySelector('.trading-interface, [data-testid="trading-view"], .chart-container');
                const accountMenu = document.querySelector('.app-bar--account-menu-button, .account-selector');
                return {
                    hasTradingInterface: !!tradingElements,
                    hasAccountMenu: !!accountMenu,
                    pageLoaded: document.readyState === 'complete'
                };
            })();
            '''
            
            result = self.tab.Runtime.evaluate(expression=trading_check_js)
            status = result.get("result", {}).get("value", {})
            
            is_ready = (
                status.get("hasTradingInterface", False) or 
                status.get("hasAccountMenu", False)
            ) and status.get("pageLoaded", False)
            
            if is_ready:
                self.log_startup_event("trading_ready", f"Status: {status}")
                return True
            else:
                self.log_startup_event("trading_not_ready", f"Status: {status}", False)
                return False
                
        except Exception as e:
            self.log_startup_event("trading_ready_error", str(e), False)
            return False
    ```

31. **Add startup status methods to ChromeInstance**
    ```python
    def get_startup_health(self) -> Dict[str, Any]:
        """Return detailed startup status for validation"""
        return {
            'username': self.username,
            'port': self.port,
            'phase': self.startup_phase.value,
            'start_time': self.startup_start_time.isoformat() if self.startup_start_time else None,
            'duration_seconds': self.get_startup_duration(),
            'error_count': len(self.startup_errors),
            'latest_errors': self.startup_errors[-3:] if self.startup_errors else [],
            'is_ready': self.startup_phase == StartupPhase.READY,
            'process_running': self.process and self.process.poll() is None if self.process else False
        }
    
    def get_startup_duration(self) -> float:
        """Get startup duration in seconds"""
        if not self.startup_start_time:
            return 0.0
        return (datetime.now() - self.startup_start_time).total_seconds()
    
    def is_ready_for_trading(self) -> bool:
        """Check if instance is fully ready for trading operations"""
        return (
            self.startup_phase == StartupPhase.READY and
            self.process and self.process.poll() is None and
            self.tab is not None
        )
    ```

#### Step 1.2.3: Update Original start() Method (15 minutes)

32. **Modify the original start() method to use validation**
    ```python
    def start(self):
        """Start Chrome with remote debugging (legacy method with validation)"""
        print(f"Starting Chrome instance for {self.username} with validation...")
        return self.start_with_validation()
    ```

### Task 1.3: Basic Retry Logic with Cleanup

#### Step 1.3.1: Add Configuration Support (15 minutes)

33. **Create/update configuration file**
    ```bash
    # Edit config/connection_health.json to add startup section
    code /Users/Mike/trading/config/connection_health.json
    ```

34. **Add startup_monitoring section to config/connection_health.json**
    ```json
    {
      "startup_monitoring": {
        "enabled": true,
        "max_retries": 3,
        "retry_delay_seconds": 10,
        "startup_timeout_seconds": 60,
        "validation_checks": {
          "ports": true,
          "memory": true,
          "network": true,
          "chrome_executable": true,
          "websocket_connectivity": true
        },
        "cleanup_on_failure": true
      }
    }
    ```

#### Step 1.3.2: Update StartupManager to Use Configuration (15 minutes)

35. **Add configuration loading to StartupManager.__init__**
    ```python
    def __init__(self, config_file: str = None):
        # Load configuration
        self.config = self._load_startup_config(config_file)
        
        # Apply configuration
        startup_config = self.config.get('startup_monitoring', {})
        self.max_retries = startup_config.get('max_retries', 3)
        self.retry_delay = startup_config.get('retry_delay_seconds', 10)
        self.startup_timeout = startup_config.get('startup_timeout_seconds', 60)
        
        # Other initialization...
        self.required_ports = [9223, 9224]
        self.startup_log = []
    ```

36. **Add _load_startup_config method to StartupManager**
    ```python
    def _load_startup_config(self, config_file: str = None) -> dict:
        """Load startup configuration from JSON file"""
        if config_file is None:
            config_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'config', 'connection_health.json'
            )
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                print(f"Loaded startup configuration from: {config_file}")
                return config
            else:
                print(f"Configuration file not found: {config_file}, using defaults")
                return self._get_default_startup_config()
        except Exception as e:
            print(f"Error loading configuration: {e}, using defaults")
            return self._get_default_startup_config()
    
    def _get_default_startup_config(self) -> dict:
        """Get default startup configuration"""
        return {
            "startup_monitoring": {
                "enabled": True,
                "max_retries": 3,
                "retry_delay_seconds": 10,
                "startup_timeout_seconds": 60,
                "validation_checks": {
                    "ports": True,
                    "memory": True,
                    "network": True,
                    "chrome_executable": True,
                    "websocket_connectivity": True
                },
                "cleanup_on_failure": True
            }
        }
    ```

#### Step 1.3.3: Testing Phase 1 Implementation (1 hour)

37. **Create test script for Phase 1**
    ```python
    # Create test_phase1.py
    code /Users/Mike/trading/test_phase1.py
    ```

38. **Add Phase 1 test content**
    ```python
    #!/usr/bin/env python3
    """
    Test Phase 1: Enhanced start_all.py with error handling
    """
    import sys
    import os
    
    # Add project root to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    from start_all import StartupManager
    
    def test_startup_manager():
        """Test StartupManager functionality"""
        print("Testing StartupManager...")
        
        manager = StartupManager()
        
        # Test prerequisite validation
        print("\n1. Testing prerequisite validation...")
        prereq_result = manager.validate_startup_prerequisites()
        print(f"Prerequisites: {'PASS' if prereq_result else 'FAIL'}")
        
        # Test configuration loading
        print("\n2. Testing configuration...")
        config = manager.config
        print(f"Config loaded: {bool(config)}")
        print(f"Max retries: {manager.max_retries}")
        
        # Get startup report
        print("\n3. Startup log:")
        report = manager.get_startup_report()
        for event in manager.startup_log:
            status = "✓" if event['success'] else "✗"
            print(f"  {status} {event['event']}: {event['details']}")
    
    if __name__ == "__main__":
        test_startup_manager()
    ```

39. **Run Phase 1 tests**
    ```bash
    cd /Users/Mike/trading
    python test_phase1.py
    ```

40. **Fix any issues found in testing**
    - Debug import errors
    - Fix path issues
    - Resolve configuration loading problems
    - Address validation failures

## Testing Checklist for Phase 1

### Validation Tests
- [ ] Port validation works correctly
- [ ] Memory validation detects low memory
- [ ] Network validation detects connectivity issues
- [ ] Chrome executable validation finds Chrome
- [ ] Chrome process validation detects running instances
- [ ] WebSocket validation tests connectivity

### Error Handling Tests
- [ ] Startup failure triggers cleanup
- [ ] Retry logic works with delays
- [ ] Maximum retry limit is respected
- [ ] Error logging captures detailed information
- [ ] Configuration loading handles missing files

### Integration Tests
- [ ] StartupManager integrates with auto_login.py
- [ ] ChromeInstance validation methods work
- [ ] Enhanced start_all.py handles failures gracefully
- [ ] Startup phases are tracked correctly

## Phase 1 Success Criteria

1. **start_all.py no longer crashes** when Chrome instances fail to start
2. **Detailed error logging** shows exactly what failed and why
3. **Retry logic** attempts startup multiple times with cleanup between attempts
4. **Validation** catches common startup issues before they cause crashes
5. **Configuration** allows tuning of retry behavior and validation settings

---

## Ready for Phase 2

Once Phase 1 is complete and tested, proceed to Phase 2 implementation below.

---

## Phase 2: Add Startup Monitoring (Important)

### Task 2.1: Enhance process_monitor.py to Cover Startup Phase

#### Step 2.1.1: Backup and Prepare (5 minutes)

1. **Create backup of process_monitor.py**
   ```bash
   cp /Users/Mike/trading/tradovate_interface/src/utils/process_monitor.py \
      /Users/Mike/trading/tradovate_interface/src/utils/process_monitor.py.backup
   ```

2. **Verify backup created successfully**
   ```bash
   ls -la /Users/Mike/trading/tradovate_interface/src/utils/process_monitor.py*
   ```

3. **Open process_monitor.py in editor**
   ```bash
   code /Users/Mike/trading/tradovate_interface/src/utils/process_monitor.py
   ```

#### Step 2.1.2: Add Startup Monitoring Data Structures (20 minutes)

4. **Add StartupMonitoringMode enum after ProcessState enum**
   ```python
   class StartupMonitoringMode(Enum):
       """Monitoring modes for Chrome startup phase"""
       DISABLED = "disabled"
       PASSIVE = "passive"  # Monitor but don't restart
       ACTIVE = "active"    # Monitor and restart on failure
   ```

5. **Add StartupProcessInfo class after ChromeProcessInfo**
   ```python
   @dataclass
   class StartupProcessInfo:
       """Information about a Chrome process during startup phase"""
       account_name: str
       expected_port: int
       startup_time: datetime
       launch_attempts: int = 0
       last_check_time: Optional[datetime] = None
       validation_status: Dict[str, bool] = field(default_factory=dict)
       startup_errors: List[str] = field(default_factory=list)
       
       def add_validation_result(self, check_name: str, passed: bool, error_msg: str = ""):
           """Record validation check result"""
           self.validation_status[check_name] = passed
           if not passed and error_msg:
               self.startup_errors.append(f"{check_name}: {error_msg}")
       
       def is_startup_complete(self) -> bool:
           """Check if all validation checks have passed"""
           required_checks = ["process_exists", "port_responsive", "websocket_ready"]
           return all(self.validation_status.get(check, False) for check in required_checks)
       
       def get_startup_duration(self) -> float:
           """Get startup duration in seconds"""
           return (datetime.now() - self.startup_time).total_seconds()
   ```

6. **Add startup monitoring attributes to ChromeProcessMonitor.__init__**
   ```python
   # Add after existing attributes in __init__
   self.startup_monitoring_mode = StartupMonitoringMode.DISABLED
   self.startup_processes: Dict[str, StartupProcessInfo] = {}
   self.startup_monitoring_thread: Optional[threading.Thread] = None
   self.startup_check_interval = 2  # Check every 2 seconds during startup
   self.max_startup_duration = 120  # Maximum 2 minutes for startup
   self.max_launch_attempts = 3
   
   # Load startup configuration
   self.startup_config = self.config.get('startup_monitoring', {})
   if self.startup_config.get('enabled', False):
       self.startup_monitoring_mode = StartupMonitoringMode.ACTIVE
   ```

#### Step 2.1.3: Add Startup Monitoring Methods (45 minutes)

7. **Add enable_startup_monitoring method**
   ```python
   def enable_startup_monitoring(self, mode: StartupMonitoringMode = StartupMonitoringMode.ACTIVE):
       """Enable monitoring during Chrome startup phase"""
       self.startup_monitoring_mode = mode
       self.logger.info(f"Startup monitoring enabled in {mode.value} mode")
       
       # Start startup monitoring thread if not already running
       if not self.startup_monitoring_thread or not self.startup_monitoring_thread.is_alive():
           self.startup_monitoring_thread = threading.Thread(
               target=self._startup_monitoring_loop,
               daemon=True
           )
           self.startup_monitoring_thread.start()
           self.logger.info("Startup monitoring thread started")
   ```

8. **Add register_for_startup_monitoring method**
   ```python
   def register_for_startup_monitoring(self, account_name: str, expected_port: int) -> bool:
       """Register a Chrome process for startup monitoring before it's launched"""
       try:
           # Don't monitor port 9222
           if expected_port == 9222:
               self.logger.warning(f"Refusing to monitor port 9222 for {account_name}")
               return False
           
           # Create startup process info
           startup_info = StartupProcessInfo(
               account_name=account_name,
               expected_port=expected_port,
               startup_time=datetime.now()
           )
           
           self.startup_processes[account_name] = startup_info
           self.logger.info(f"Registered {account_name} for startup monitoring on port {expected_port}")
           
           # Enable startup monitoring if not already enabled
           if self.startup_monitoring_mode == StartupMonitoringMode.DISABLED:
               self.enable_startup_monitoring()
           
           return True
           
       except Exception as e:
           self.logger.error(f"Failed to register {account_name} for startup monitoring: {e}")
           return False
   ```

9. **Add _startup_monitoring_loop method**
   ```python
   def _startup_monitoring_loop(self):
       """Background thread that monitors Chrome instances during startup"""
       self.logger.info("Startup monitoring loop started")
       
       while self.startup_monitoring_mode != StartupMonitoringMode.DISABLED:
           try:
               # Check all registered startup processes
               for account_name, startup_info in list(self.startup_processes.items()):
                   self._check_startup_process(account_name, startup_info)
               
               # Clean up completed or failed startups
               self._cleanup_completed_startups()
               
           except Exception as e:
               self.logger.error(f"Error in startup monitoring loop: {e}")
           
           time.sleep(self.startup_check_interval)
       
       self.logger.info("Startup monitoring loop stopped")
   ```

10. **Add _check_startup_process method**
    ```python
    def _check_startup_process(self, account_name: str, startup_info: StartupProcessInfo):
        """Check a single Chrome process during startup"""
        try:
            startup_info.last_check_time = datetime.now()
            
            # Check if startup is taking too long
            if startup_info.get_startup_duration() > self.max_startup_duration:
                self.logger.error(f"{account_name} startup timeout after {self.max_startup_duration}s")
                startup_info.add_validation_result("timeout", False, "Startup timeout exceeded")
                
                if self.startup_monitoring_mode == StartupMonitoringMode.ACTIVE:
                    self._handle_startup_failure(account_name, startup_info)
                return
            
            # Validation check 1: Process exists
            pid = self._find_chrome_process_by_port(startup_info.expected_port)
            if pid:
                startup_info.add_validation_result("process_exists", True)
                
                # If this is first time we found the process, try to register it
                if account_name not in self.processes:
                    self._attempt_early_registration(account_name, pid, startup_info.expected_port)
            else:
                startup_info.add_validation_result("process_exists", False, "Chrome process not found")
                return
            
            # Validation check 2: Port responsive
            if self._check_port_responsive(startup_info.expected_port):
                startup_info.add_validation_result("port_responsive", True)
            else:
                startup_info.add_validation_result("port_responsive", False, "Debug port not responsive")
                return
            
            # Validation check 3: WebSocket ready
            if self._check_websocket_ready(startup_info.expected_port):
                startup_info.add_validation_result("websocket_ready", True)
            else:
                startup_info.add_validation_result("websocket_ready", False, "WebSocket not ready")
                return
            
            # Check if startup is complete
            if startup_info.is_startup_complete():
                self.logger.info(f"{account_name} startup completed successfully in {startup_info.get_startup_duration():.1f}s")
                
                # Transition to normal monitoring if registered
                if account_name in self.processes:
                    self.processes[account_name].state = ProcessState.RUNNING
                    
        except Exception as e:
            self.logger.error(f"Error checking startup process {account_name}: {e}")
            startup_info.add_validation_result("exception", False, str(e))
    ```

11. **Add helper methods for startup validation**
    ```python
    def _find_chrome_process_by_port(self, port: int) -> Optional[int]:
        """Find Chrome process PID by debugging port"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if 'chrome' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if f'--remote-debugging-port={port}' in cmdline:
                        return proc.info['pid']
            return None
        except Exception as e:
            self.logger.error(f"Error finding Chrome process for port {port}: {e}")
            return None
    
    def _check_websocket_ready(self, port: int) -> bool:
        """Check if Chrome WebSocket is ready for connections"""
        try:
            import pychrome
            browser = pychrome.Browser(url=f"http://localhost:{port}")
            tabs = browser.list_tab()
            
            if tabs:
                # Try basic JavaScript execution
                tab = tabs[0]
                tab.start()
                result = tab.Runtime.evaluate(expression="1 + 1")
                tab.stop()
                
                return result.get("result", {}).get("value") == 2
            return False
            
        except Exception:
            return False
    
    def _attempt_early_registration(self, account_name: str, pid: int, port: int):
        """Attempt to register a Chrome process during startup"""
        try:
            # Create minimal process info for registration
            process_info = ChromeProcessInfo(
                account_name=account_name,
                pid=pid,
                port=port,
                profile_path=f"/tmp/tradovate_debug_profile_{port}",  # Default path
                start_time=datetime.now(),
                state=ProcessState.STARTING
            )
            
            self.processes[account_name] = process_info
            self.logger.info(f"Early registration of {account_name} (PID: {pid}, Port: {port}) during startup")
            
        except Exception as e:
            self.logger.error(f"Failed early registration of {account_name}: {e}")
    ```

12. **Add startup failure handling**
    ```python
    def _handle_startup_failure(self, account_name: str, startup_info: StartupProcessInfo):
        """Handle Chrome startup failure with retry logic"""
        try:
            self.logger.warning(f"Handling startup failure for {account_name}")
            
            # Kill any partial Chrome process
            pid = self._find_chrome_process_by_port(startup_info.expected_port)
            if pid:
                self.logger.info(f"Killing failed Chrome process {pid}")
                os.kill(pid, signal.SIGTERM)
                time.sleep(2)
            
            # Check if we should retry
            if startup_info.launch_attempts < self.max_launch_attempts:
                startup_info.launch_attempts += 1
                self.logger.info(f"Scheduling retry {startup_info.launch_attempts}/{self.max_launch_attempts} for {account_name}")
                
                # Reset validation status for retry
                startup_info.validation_status.clear()
                startup_info.startup_time = datetime.now()
                
                # Signal that a retry is needed (caller should handle actual restart)
                self._signal_startup_retry_needed(account_name, startup_info)
            else:
                self.logger.error(f"Max startup attempts ({self.max_launch_attempts}) reached for {account_name}")
                # Remove from startup monitoring
                del self.startup_processes[account_name]
                
        except Exception as e:
            self.logger.error(f"Error handling startup failure for {account_name}: {e}")
    
    def _signal_startup_retry_needed(self, account_name: str, startup_info: StartupProcessInfo):
        """Signal that a Chrome instance needs to be restarted"""
        # This is a hook for integration with start_all.py
        # The actual restart should be handled by the caller
        self.logger.info(f"Startup retry needed for {account_name} on port {startup_info.expected_port}")
    ```

13. **Add cleanup methods**
    ```python
    def _cleanup_completed_startups(self):
        """Remove successfully started processes from startup monitoring"""
        completed = []
        
        for account_name, startup_info in self.startup_processes.items():
            # Remove if startup is complete or failed permanently
            if startup_info.is_startup_complete():
                completed.append(account_name)
            elif startup_info.launch_attempts >= self.max_launch_attempts:
                self.logger.info(f"Removing {account_name} from startup monitoring (max attempts reached)")
                completed.append(account_name)
            elif startup_info.get_startup_duration() > self.max_startup_duration * 2:
                self.logger.info(f"Removing {account_name} from startup monitoring (timeout)")
                completed.append(account_name)
        
        for account_name in completed:
            del self.startup_processes[account_name]
    ```

14. **Add validate_startup_completion method**
    ```python
    def validate_startup_completion(self, account_name: str) -> bool:
        """Verify that a Chrome instance has completed startup successfully"""
        if account_name in self.startup_processes:
            startup_info = self.startup_processes[account_name]
            return startup_info.is_startup_complete()
        
        # If not in startup monitoring, check if it's in regular monitoring
        return account_name in self.processes
    ```

#### Step 2.1.4: Integration with Existing Methods (25 minutes)

15. **Modify register_chrome_process to check startup status**
    ```python
    def register_chrome_process(self, account_name: str, pid: int, port: int, profile_path: str):
        """Register a Chrome process for monitoring"""
        # Check if port 9222 protection
        if port == 9222:
            self.logger.warning(f"Refusing to register process on port 9222 for {account_name}")
            return
        
        # Check if this was a startup-monitored process
        if account_name in self.startup_processes:
            startup_info = self.startup_processes[account_name]
            self.logger.info(f"Transitioning {account_name} from startup to regular monitoring")
            
            # Verify startup was successful
            if not startup_info.is_startup_complete():
                self.logger.warning(f"Registering {account_name} but startup validation incomplete")
        
        # Create process info
        process_info = ChromeProcessInfo(
            account_name=account_name,
            pid=pid,
            port=port,
            profile_path=profile_path,
            start_time=datetime.now(),
            state=ProcessState.RUNNING
        )
        
        self.processes[account_name] = process_info
        self.logger.info(f"Registered Chrome process for {account_name} - PID: {pid}, Port: {port}")
        
        # Remove from startup monitoring if present
        if account_name in self.startup_processes:
            del self.startup_processes[account_name]
    ```

16. **Add startup status to get_status method**
    ```python
    def get_status(self) -> dict:
        """Get current status of all monitored processes"""
        status = {
            'monitoring_active': self.monitoring_active,
            'process_count': len(self.processes),
            'startup_monitoring': {
                'mode': self.startup_monitoring_mode.value,
                'active_startups': len(self.startup_processes),
                'startup_processes': {}
            },
            'processes': {}
        }
        
        # Add regular process status
        for account_name, process_info in self.processes.items():
            status['processes'][account_name] = {
                'pid': process_info.pid,
                'port': process_info.port,
                'state': process_info.state.value,
                'uptime_seconds': (datetime.now() - process_info.start_time).total_seconds(),
                'restart_count': process_info.restart_count,
                'last_check': process_info.last_check_time.isoformat() if process_info.last_check_time else None
            }
        
        # Add startup process status
        for account_name, startup_info in self.startup_processes.items():
            status['startup_monitoring']['startup_processes'][account_name] = {
                'port': startup_info.expected_port,
                'duration_seconds': startup_info.get_startup_duration(),
                'attempts': startup_info.launch_attempts,
                'validation_status': startup_info.validation_status,
                'errors': startup_info.startup_errors[-3:] if startup_info.startup_errors else []
            }
        
        return status
    ```

#### Step 2.1.5: Update Configuration (10 minutes)

17. **Update process_monitor.json configuration**
    ```bash
    code /Users/Mike/trading/tradovate_interface/config/process_monitor.json
    ```

18. **Add startup_monitoring section to configuration**
    ```json
    {
      "monitoring": {
        // ... existing monitoring config ...
      },
      "startup_monitoring": {
        "enabled": true,
        "mode": "active",
        "check_interval_seconds": 2,
        "max_startup_duration_seconds": 120,
        "max_launch_attempts": 3,
        "validation_checks": [
          "process_exists",
          "port_responsive",
          "websocket_ready"
        ],
        "early_registration": true
      }
    }
    ```

### Task 2.2: Early Process Registration Before Full Startup

#### Step 2.2.1: Modify start_all.py Integration (30 minutes)

19. **Import ChromeProcessMonitor in start_all.py**
    ```python
    # Add to imports section
    from tradovate_interface.src.utils.process_monitor import ChromeProcessMonitor, StartupMonitoringMode
    ```

20. **Add process monitor initialization to StartupManager**
    ```python
    def __init__(self, config_file: str = None):
        # Existing initialization...
        
        # Initialize process monitor for startup phase
        self.process_monitor = None
        try:
            self.process_monitor = ChromeProcessMonitor()
            self.process_monitor.enable_startup_monitoring(StartupMonitoringMode.ACTIVE)
            self.log_event("process_monitor_init", "Chrome process monitor initialized for startup")
        except Exception as e:
            self.log_event("process_monitor_init", f"Failed to initialize process monitor: {e}", False)
    ```

21. **Add early registration before Chrome launch**
    ```python
    def start_with_retry(self):
        """Start auto-login with comprehensive retry logic"""
        self.log_event("startup_begin", f"Starting with max {self.max_retries} retries")
        
        # Register accounts for startup monitoring
        if self.process_monitor:
            accounts = [
                ("Account 1", 9224),
                ("Account 2", 9223)
            ]
            for account_name, port in accounts:
                self.process_monitor.register_for_startup_monitoring(account_name, port)
        
        # Continue with existing retry logic...
    ```

22. **Add startup validation using process monitor**
    ```python
    def validate_chrome_startup(self) -> bool:
        """Validate Chrome instances started successfully"""
        import time
        
        # Wait for Chrome to fully start
        self.log_event("chrome_wait", f"Waiting {self.startup_timeout}s for Chrome startup")
        
        # Use process monitor to track startup progress
        if self.process_monitor:
            start_time = time.time()
            while time.time() - start_time < self.startup_timeout:
                # Check startup status
                status = self.process_monitor.get_status()
                startup_procs = status.get('startup_monitoring', {}).get('startup_processes', {})
                
                # Check if all accounts have completed startup
                all_complete = True
                for account_name in ["Account 1", "Account 2"]:
                    if account_name in startup_procs:
                        validation = startup_procs[account_name].get('validation_status', {})
                        if not all(validation.values()):
                            all_complete = False
                            break
                    elif not self.process_monitor.validate_startup_completion(account_name):
                        all_complete = False
                        break
                
                if all_complete:
                    self.log_event("chrome_startup_validated", "All Chrome instances validated via process monitor")
                    return True
                
                time.sleep(2)
            
            # Timeout reached
            self.log_event("chrome_startup_timeout", "Startup validation timeout", False)
            return False
        else:
            # Fallback to original validation
            return super().validate_chrome_startup()
    ```

#### Step 2.2.2: Modify auto_login.py Integration (20 minutes)

23. **Add process monitor integration to ChromeInstance**
    ```python
    def start_with_validation(self, timeout: int = 60) -> bool:
        """Start Chrome instance with comprehensive validation"""
        self.startup_start_time = datetime.now()
        self.log_startup_event("startup_begin", f"Starting with {timeout}s timeout")
        
        # Register with process monitor for startup monitoring
        try:
            from tradovate_interface.src.utils.process_monitor import ChromeProcessMonitor
            monitor = ChromeProcessMonitor()
            monitor.register_for_startup_monitoring(self.username, self.port)
            self.log_startup_event("monitor_registered", f"Registered with process monitor")
        except Exception as e:
            self.log_startup_event("monitor_registration_failed", str(e), False)
        
        # Continue with existing startup logic...
    ```

24. **Add process registration after Chrome launch**
    ```python
    # In start_with_validation, after Chrome process is started:
    if self.process:
        # Register with process monitor if available
        try:
            from tradovate_interface.src.utils.process_monitor import ChromeProcessMonitor
            monitor = ChromeProcessMonitor()
            
            # Get profile path
            profile_path = f"/tmp/tradovate_debug_profile_{self.port}"
            
            # Register the running process
            monitor.register_chrome_process(
                account_name=self.username,
                pid=self.process.pid,
                port=self.port,
                profile_path=profile_path
            )
            
            self.log_startup_event("process_registered", f"Registered PID {self.process.pid} with monitor")
        except Exception as e:
            self.log_startup_event("process_registration_failed", str(e), False)
    ```

### Task 2.3: Testing Phase 2 Implementation

#### Step 2.3.1: Create Phase 2 Test Script (30 minutes)

25. **Create test script for Phase 2**
    ```bash
    code /Users/Mike/trading/test_phase2.py
    ```

26. **Add Phase 2 test content**
    ```python
    #!/usr/bin/env python3
    """
    Test Phase 2: Enhanced process monitoring with startup phase coverage
    """
    import sys
    import os
    import time
    import threading
    
    # Add project root to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    from tradovate_interface.src.utils.process_monitor import ChromeProcessMonitor, StartupMonitoringMode
    
    def test_startup_monitoring():
        """Test startup monitoring functionality"""
        print("Testing ChromeProcessMonitor startup monitoring...")
        
        # Initialize monitor
        monitor = ChromeProcessMonitor()
        
        # Test 1: Enable startup monitoring
        print("\n1. Testing startup monitoring enablement...")
        monitor.enable_startup_monitoring(StartupMonitoringMode.ACTIVE)
        status = monitor.get_status()
        print(f"Startup monitoring mode: {status['startup_monitoring']['mode']}")
        
        # Test 2: Register for startup monitoring
        print("\n2. Testing startup registration...")
        success = monitor.register_for_startup_monitoring("Test Account", 9999)
        print(f"Registration successful: {success}")
        
        # Test 3: Check startup status
        print("\n3. Checking startup status...")
        time.sleep(2)
        status = monitor.get_status()
        startup_procs = status['startup_monitoring']['startup_processes']
        
        for account, info in startup_procs.items():
            print(f"\n{account}:")
            print(f"  Port: {info['port']}")
            print(f"  Duration: {info['duration_seconds']:.1f}s")
            print(f"  Validation: {info['validation_status']}")
            print(f"  Errors: {info['errors']}")
        
        # Test 4: Validate startup completion
        print("\n4. Testing startup validation...")
        is_complete = monitor.validate_startup_completion("Test Account")
        print(f"Startup complete: {is_complete}")
        
        # Stop monitoring
        monitor.stop_monitoring()
        print("\nTest completed")
    
    def test_integration():
        """Test integration with start_all.py StartupManager"""
        print("\n\nTesting StartupManager integration...")
        
        from start_all import StartupManager
        
        manager = StartupManager()
        
        # Check if process monitor was initialized
        if manager.process_monitor:
            print("✓ Process monitor initialized in StartupManager")
            
            # Get status
            status = manager.process_monitor.get_status()
            print(f"✓ Startup monitoring active: {status['startup_monitoring']['mode']}")
        else:
            print("✗ Process monitor not initialized")
    
    if __name__ == "__main__":
        print("=== Phase 2 Testing ===\n")
        
        # Test startup monitoring
        test_startup_monitoring()
        
        # Test integration
        test_integration()
        
        print("\n=== Testing Complete ===")
    ```

27. **Run Phase 2 tests**
    ```bash
    cd /Users/Mike/trading
    python test_phase2.py
    ```

#### Step 2.3.2: Integration Testing (30 minutes)

28. **Create integration test script**
    ```bash
    code /Users/Mike/trading/test_integration.py
    ```

29. **Add integration test content**
    ```python
    #!/usr/bin/env python3
    """
    Integration test for Phase 1 + Phase 2 implementation
    """
    import sys
    import os
    import subprocess
    import time
    
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    def test_startup_with_monitoring():
        """Test complete startup flow with monitoring"""
        print("Testing integrated startup with monitoring...")
        
        # Import after path setup
        from start_all import StartupManager
        from tradovate_interface.src.utils.process_monitor import ChromeProcessMonitor
        
        # Initialize components
        print("\n1. Initializing components...")
        manager = StartupManager()
        
        # Verify process monitor is active
        if manager.process_monitor:
            status = manager.process_monitor.get_status()
            print(f"✓ Process monitor active: {status['monitoring_active']}")
            print(f"✓ Startup monitoring: {status['startup_monitoring']['mode']}")
        
        # Test prerequisite validation
        print("\n2. Testing prerequisites...")
        prereq_ok = manager.validate_startup_prerequisites()
        print(f"Prerequisites: {'PASS' if prereq_ok else 'FAIL'}")
        
        # Show startup report
        print("\n3. Startup report:")
        report = manager.get_startup_report()
        for event in report['events']:
            status = "✓" if event['success'] else "✗"
            print(f"  {status} {event['event']}: {event['details']}")
        
        print("\nIntegration test completed")
    
    def test_failure_scenarios():
        """Test various failure scenarios"""
        print("\n\nTesting failure scenarios...")
        
        # Test 1: Port already in use
        print("\n1. Testing port conflict detection...")
        # This would require actually binding to a port
        
        # Test 2: Low memory simulation
        print("\n2. Testing memory validation...")
        # This would require mocking psutil
        
        # Test 3: Network failure
        print("\n3. Testing network validation...")
        # This would require mocking requests
        
        print("\nFailure scenario tests completed")
    
    if __name__ == "__main__":
        print("=== Integration Testing ===\n")
        
        # Test integrated startup
        test_startup_with_monitoring()
        
        # Test failure scenarios
        test_failure_scenarios()
        
        print("\n=== Integration Testing Complete ===")
    ```

30. **Run integration tests**
    ```bash
    cd /Users/Mike/trading
    python test_integration.py
    ```

## Testing Checklist for Phase 2

### Startup Monitoring Tests
- [ ] Startup monitoring can be enabled/disabled
- [ ] Early process registration works before Chrome launch
- [ ] Startup validation checks run correctly
- [ ] Timeout detection works
- [ ] Retry signaling functions properly

### Integration Tests
- [ ] StartupManager integrates with ChromeProcessMonitor
- [ ] ChromeInstance registers with monitor during startup
- [ ] Startup status is tracked accurately
- [ ] Transition from startup to regular monitoring works

### Error Handling Tests
- [ ] Failed startups are detected
- [ ] Retry logic is triggered appropriately
- [ ] Maximum retry limits are respected
- [ ] Cleanup occurs after failures

### Configuration Tests
- [ ] Startup monitoring configuration loads correctly
- [ ] Configuration changes affect behavior
- [ ] Default values work when config is missing

## Phase 2 Success Criteria

1. **Process Monitor covers startup phase** (0-60 seconds)
2. **Early registration** allows monitoring before full startup
3. **Startup validation** integrates with existing health checks
4. **Startup failures** are detected and reported accurately
5. **Integration** between all components works seamlessly

---

## Summary of Complete Implementation

### Phase 1 Accomplishments
- ✅ Enhanced start_all.py with comprehensive error handling
- ✅ Added startup validation to auto_login.py ChromeInstance
- ✅ Implemented retry logic with cleanup
- ✅ Created configuration-driven behavior

### Phase 2 Accomplishments
- ✅ Extended process_monitor.py to cover startup phase
- ✅ Implemented early process registration
- ✅ Added startup-specific health checks
- ✅ Integrated all components for seamless monitoring

### Key Benefits
1. **No more crashes** - start_all.py handles failures gracefully
2. **Complete visibility** - Detailed logging of all startup phases
3. **Automatic recovery** - Retry logic with intelligent cleanup
4. **Early detection** - Problems caught during startup, not after
5. **Configuration flexibility** - Easily tune behavior without code changes

### Next Steps
1. Deploy Phase 1 changes and test in production
2. Monitor logs for startup failures
3. Deploy Phase 2 changes after Phase 1 validation
4. Fine-tune configuration based on real-world results
5. Consider Phase 3 (advanced coordination) if needed