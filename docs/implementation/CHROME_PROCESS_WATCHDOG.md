# Chrome Process Watchdog Implementation Guide
## Automated Chrome Crash Detection and Recovery for Trading Stability

---

## 🚨 CRITICAL TRADING REQUIREMENT
**Chrome crashes = immediate loss of ALL trading connections**  
**Target**: 99.9% uptime with <30 second automated recovery

---

## OVERVIEW

The Chrome Process Watchdog is a critical stability component that monitors Chrome browser processes used for Tradovate trading automation, detects crashes or failures, and automatically restarts them while preserving trading state.

### Key Features
- **Real-time process monitoring** - Continuous health checks every 10 seconds
- **Multi-level crash detection** - Process death, port unresponsive, tab crashes
- **State preservation** - Save trading context before restart
- **Automated recovery** - Full Chrome restart with state restoration
- **Zero-downtime failover** - Backup connections during recovery

---

## IMPLEMENTATION PHASES

## Phase 1: Process Monitoring Infrastructure

### 1.1 Create Process Monitor Class

**File**: `src/utils/process_monitor.py`

```python
import psutil
import threading
import time
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional, List
import logging

class ProcessState(Enum):
    STARTING = "starting"
    RUNNING = "running" 
    CRASHED = "crashed"
    RESTARTING = "restarting"
    FAILED = "failed"

class ChromeProcessMonitor:
    def __init__(self, config_path: str = "config/process_monitor.json"):
        self.processes: Dict[str, Dict] = {}
        self.config = self._load_config(config_path)
        self.monitoring_thread = None
        self.shutdown_event = threading.Event()
        self.process_lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        
    def _load_config(self, config_path: str) -> Dict:
        """Load monitoring configuration"""
        default_config = {
            "check_interval": 10,  # seconds
            "max_restart_attempts": 3,
            "restart_delay": 5,  # seconds between restarts
            "health_check_timeout": 30,  # seconds
            "crash_confirmation_checks": 3,
            "crash_confirmation_interval": 10  # seconds
        }
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        except FileNotFoundError:
            self.logger.warning(f"Config file {config_path} not found, using defaults")
        return default_config
```

**Implementation Steps**:
- [ ] **1.1.1** Create `src/utils/process_monitor.py` file
- [ ] **1.1.2** Define `ChromeProcessMonitor` class with initialization
- [ ] **1.1.3** Add process tracking dictionary with account mapping
- [ ] **1.1.4** Add process state enumeration
- [ ] **1.1.5** Initialize threading locks for thread safety
- [ ] **1.1.6** Add configuration loading with defaults

### 1.2 Process Health Check Mechanism

```python
def is_process_alive(self, pid: int) -> bool:
    """Check if process with given PID exists and is running"""
    try:
        return psutil.pid_exists(pid) and psutil.Process(pid).is_running()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False

def is_chrome_responsive(self, port: int) -> bool:
    """Test Chrome debugging port responsiveness"""
    import requests
    try:
        response = requests.get(
            f"http://localhost:{port}/json",
            timeout=self.config["health_check_timeout"]
        )
        return response.status_code == 200
    except requests.RequestException:
        return False

def is_tradovate_accessible(self, port: int) -> bool:
    """Verify Tradovate tab exists and responds"""
    try:
        import pychrome
        browser = pychrome.Browser(url=f"http://localhost:{port}")
        tabs = browser.list_tab()
        
        for tab in tabs:
            if "tradovate.com" in tab.url.lower():
                tab.start()
                result = tab.Runtime.evaluate(expression="document.readyState")
                tab.stop()
                return result.get("result", {}).get("value") == "complete"
        return False
    except Exception:
        return False

def check_chrome_health(self, account_name: str) -> Dict:
    """Comprehensive health check for Chrome instance"""
    if account_name not in self.processes:
        return {"healthy": False, "error": "Account not monitored"}
        
    process_info = self.processes[account_name]
    pid = process_info["pid"]
    port = process_info["port"]
    
    health_status = {
        "account": account_name,
        "timestamp": datetime.now().isoformat(),
        "healthy": True,
        "checks": {}
    }
    
    # Process existence check
    process_alive = self.is_process_alive(pid)
    health_status["checks"]["process_alive"] = process_alive
    
    if not process_alive:
        health_status["healthy"] = False
        health_status["error"] = "Chrome process not running"
        return health_status
    
    # Port responsiveness check
    port_responsive = self.is_chrome_responsive(port)
    health_status["checks"]["port_responsive"] = port_responsive
    
    if not port_responsive:
        health_status["healthy"] = False
        health_status["error"] = "Chrome debugging port unresponsive"
        return health_status
    
    # Tradovate accessibility check
    tradovate_accessible = self.is_tradovate_accessible(port)
    health_status["checks"]["tradovate_accessible"] = tradovate_accessible
    
    if not tradovate_accessible:
        health_status["healthy"] = False
        health_status["error"] = "Tradovate interface not accessible"
        return health_status
    
    return health_status
```

**Implementation Steps**:
- [ ] **1.2.1** Implement `is_process_alive()` using psutil
- [ ] **1.2.2** Implement `is_chrome_responsive()` with HTTP test
- [ ] **1.2.3** Implement `is_tradovate_accessible()` with DOM check
- [ ] **1.2.4** Create composite `check_chrome_health()` function
- [ ] **1.2.5** Add detailed health check logging
- [ ] **1.2.6** Implement exponential backoff for failed checks

### 1.3 Continuous Monitoring Loop

```python
def start_monitoring(self):
    """Start background monitoring thread"""
    if self.monitoring_thread and self.monitoring_thread.is_alive():
        self.logger.warning("Monitoring already running")
        return
        
    self.shutdown_event.clear()
    self.monitoring_thread = threading.Thread(
        target=self._monitoring_loop,
        name="ChromeProcessMonitor",
        daemon=True
    )
    self.monitoring_thread.start()
    self.logger.info("Chrome process monitoring started")

def _monitoring_loop(self):
    """Main monitoring loop running in background thread"""
    while not self.shutdown_event.is_set():
        try:
            with self.process_lock:
                accounts_to_check = list(self.processes.keys())
            
            for account_name in accounts_to_check:
                if self.shutdown_event.is_set():
                    break
                    
                try:
                    health_status = self.check_chrome_health(account_name)
                    self._handle_health_result(account_name, health_status)
                except Exception as e:
                    self.logger.error(f"Health check failed for {account_name}: {e}")
            
            # Wait for next check interval
            self.shutdown_event.wait(self.config["check_interval"])
            
        except Exception as e:
            self.logger.error(f"Monitoring loop error: {e}")
            self.shutdown_event.wait(5)  # Brief pause before retry

def stop_monitoring(self):
    """Stop monitoring thread gracefully"""
    if self.monitoring_thread:
        self.shutdown_event.set()
        self.monitoring_thread.join(timeout=10)
        if self.monitoring_thread.is_alive():
            self.logger.warning("Monitoring thread did not stop gracefully")
    self.logger.info("Chrome process monitoring stopped")
```

**Implementation Steps**:
- [ ] **1.3.1** Create background monitoring thread
- [ ] **1.3.2** Implement monitoring loop with configurable interval
- [ ] **1.3.3** Add graceful shutdown mechanism
- [ ] **1.3.4** Implement staggered health checks
- [ ] **1.3.5** Add monitoring state persistence
- [ ] **1.3.6** Create monitoring metrics collection

---

## Phase 2: Crash Detection

### 2.1 Process Crash Detection

```python
class CrashType(Enum):
    PROCESS_DIED = "process_died"
    PORT_UNRESPONSIVE = "port_unresponsive" 
    TAB_CRASHED = "tab_crashed"
    AUTHENTICATION_FAILED = "auth_failed"

def _handle_health_result(self, account_name: str, health_status: Dict):
    """Process health check results and detect crashes"""
    with self.process_lock:
        if account_name not in self.processes:
            return
            
        process_info = self.processes[account_name]
        
        if health_status["healthy"]:
            # Reset failure counters on successful check
            process_info["consecutive_failures"] = 0
            process_info["last_healthy"] = datetime.now()
            process_info["state"] = ProcessState.RUNNING
        else:
            # Increment failure counter
            process_info["consecutive_failures"] = process_info.get("consecutive_failures", 0) + 1
            
            # Determine crash type
            crash_type = self._classify_crash_type(health_status)
            
            # Check if we should declare a crash
            if self._should_trigger_restart(process_info, crash_type):
                self._trigger_restart(account_name, crash_type, health_status)

def _classify_crash_type(self, health_status: Dict) -> CrashType:
    """Classify the type of crash based on health check results"""
    checks = health_status.get("checks", {})
    
    if not checks.get("process_alive", True):
        return CrashType.PROCESS_DIED
    elif not checks.get("port_responsive", True):
        return CrashType.PORT_UNRESPONSIVE
    elif not checks.get("tradovate_accessible", True):
        return CrashType.TAB_CRASHED
    else:
        return CrashType.AUTHENTICATION_FAILED

def _should_trigger_restart(self, process_info: Dict, crash_type: CrashType) -> bool:
    """Determine if crash is confirmed and restart should be triggered"""
    required_failures = self.config["crash_confirmation_checks"]
    consecutive_failures = process_info.get("consecutive_failures", 0)
    
    # Immediate restart for complete process death
    if crash_type == CrashType.PROCESS_DIED:
        return consecutive_failures >= 1
    
    # Multiple confirmations for other types
    return consecutive_failures >= required_failures
```

**Implementation Steps**:
- [ ] **2.1.1** Detect Chrome process PID death
- [ ] **2.1.2** Detect debugging port unresponsiveness  
- [ ] **2.1.3** Detect Tradovate tab crashes
- [ ] **2.1.4** Implement crash type classification
- [ ] **2.1.5** Add crash timestamp and context logging
- [ ] **2.1.6** Implement crash pattern detection

### 2.2 Crash Validation

```python
def _validate_crash(self, account_name: str, crash_type: CrashType) -> bool:
    """Multi-check validation before declaring crash"""
    validation_checks = []
    
    for i in range(3):  # Triple validation
        time.sleep(2)  # Brief pause between checks
        health_status = self.check_chrome_health(account_name)
        validation_checks.append(health_status["healthy"])
        
        if health_status["healthy"]:
            self.logger.info(f"False crash alarm for {account_name} - process recovered")
            return False
    
    # Log crash confirmation
    self.logger.error(f"Crash confirmed for {account_name}: {crash_type.value}")
    self._log_crash_details(account_name, crash_type, validation_checks)
    return True

def _log_crash_details(self, account_name: str, crash_type: CrashType, validation_results: List[bool]):
    """Log detailed crash information for analysis"""
    crash_details = {
        "timestamp": datetime.now().isoformat(),
        "account": account_name,
        "crash_type": crash_type.value,
        "validation_results": validation_results,
        "process_info": self.processes.get(account_name, {}),
        "system_info": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent
        }
    }
    
    # Write to crash log file
    crash_log_path = f"logs/crashes/crash_{account_name}_{int(time.time())}.json"
    os.makedirs(os.path.dirname(crash_log_path), exist_ok=True)
    
    with open(crash_log_path, 'w') as f:
        json.dump(crash_details, f, indent=2)
    
    self.logger.error(f"Crash details logged to {crash_log_path}")
```

**Implementation Steps**:
- [ ] **2.2.1** Implement multi-check validation (3 checks over 30 seconds)
- [ ] **2.2.2** Add distinction between temporary vs permanent failure
- [ ] **2.2.3** Implement crash confirmation through multiple methods
- [ ] **2.2.4** Add crash false-positive prevention
- [ ] **2.2.5** Create crash severity assessment
- [ ] **2.2.6** Log crash validation with confidence levels

---

## Phase 3: State Preservation Before Restart

### 3.1 Account State Capture

```python
def _capture_account_state(self, account_name: str) -> Dict:
    """Capture current account state before restart"""
    state = {
        "timestamp": datetime.now().isoformat(),
        "account": account_name,
        "credentials": {},
        "trading_state": {},
        "ui_state": {},
        "connection_state": {}
    }
    
    try:
        # Capture credentials
        state["credentials"] = self._get_account_credentials(account_name)
        
        # Capture trading state via JavaScript injection
        port = self.processes[account_name]["port"]
        state["trading_state"] = self._capture_trading_state(port)
        
        # Capture UI state
        state["ui_state"] = self._capture_ui_state(port)
        
        # Capture connection state
        state["connection_state"] = self._capture_connection_state(account_name)
        
    except Exception as e:
        self.logger.error(f"State capture failed for {account_name}: {e}")
        state["capture_error"] = str(e)
    
    return state

def _capture_trading_state(self, port: int) -> Dict:
    """Capture current trading state via JavaScript"""
    try:
        import pychrome
        browser = pychrome.Browser(url=f"http://localhost:{port}")
        tab = None
        
        # Find Tradovate tab
        for t in browser.list_tab():
            if "tradovate.com" in t.url.lower():
                tab = t
                break
        
        if not tab:
            return {"error": "No Tradovate tab found"}
        
        tab.start()
        
        # Extract trading state via JavaScript
        js_code = """
        ({
            symbol: document.getElementById('symbolInput')?.value || '',
            quantity: document.getElementById('qtyInput')?.value || '',
            takeProfitTicks: document.getElementById('tpInput')?.value || '',
            stopLossTicks: document.getElementById('slInput')?.value || '',
            tickSize: document.getElementById('tickInput')?.value || '',
            positions: window.getCurrentPositions ? window.getCurrentPositions() : [],
            orders: window.getPendingOrders ? window.getPendingOrders() : [],
            dollarRisk: localStorage.getItem('bracketTrade_dollarRisk') || '',
            riskReward: localStorage.getItem('bracketTrade_riskReward') || ''
        })
        """
        
        result = tab.Runtime.evaluate(expression=js_code)
        tab.stop()
        
        return result.get("result", {}).get("value", {})
        
    except Exception as e:
        return {"error": str(e)}

def _save_state_to_file(self, account_name: str, state: Dict):
    """Save state to recovery file"""
    recovery_dir = "recovery"
    os.makedirs(recovery_dir, exist_ok=True)
    
    state_file = os.path.join(recovery_dir, f"{account_name}_state.json")
    
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)
    
    self.logger.info(f"State saved to {state_file}")
    return state_file
```

**Implementation Steps**:
- [ ] **3.1.1** Extract account credentials from config
- [ ] **3.1.2** Capture current trading symbol from DOM
- [ ] **3.1.3** Capture position information via JavaScript
- [ ] **3.1.4** Capture order book state and pending orders
- [ ] **3.1.5** Capture UI state (TP/SL values, risk parameters)
- [ ] **3.1.6** Save state to recovery JSON file

---

## Phase 4: Restart Procedures

### 4.1 Clean Shutdown Process

```python
def _clean_shutdown_chrome(self, account_name: str) -> bool:
    """Gracefully shutdown Chrome process"""
    if account_name not in self.processes:
        return False
    
    pid = self.processes[account_name]["pid"]
    
    try:
        process = psutil.Process(pid)
        
        # Send SIGTERM for graceful shutdown
        process.terminate()
        
        # Wait up to 10 seconds for graceful shutdown
        try:
            process.wait(timeout=10)
            self.logger.info(f"Chrome process {pid} shut down gracefully")
            return True
        except psutil.TimeoutExpired:
            # Force kill if graceful shutdown failed
            process.kill()
            process.wait(timeout=5)
            self.logger.warning(f"Chrome process {pid} force killed")
            return True
            
    except psutil.NoSuchProcess:
        # Process already dead
        return True
    except Exception as e:
        self.logger.error(f"Failed to shutdown Chrome process {pid}: {e}")
        return False
    finally:
        # Clean up resources
        self._cleanup_chrome_resources(account_name)

def _cleanup_chrome_resources(self, account_name: str):
    """Clean up Chrome-related resources"""
    if account_name not in self.processes:
        return
    
    process_info = self.processes[account_name]
    port = process_info["port"]
    
    # Clean up temp profile directory
    profile_dir = process_info.get("profile_dir")
    if profile_dir and os.path.exists(profile_dir):
        try:
            import shutil
            shutil.rmtree(profile_dir)
            self.logger.info(f"Cleaned up profile directory: {profile_dir}")
        except Exception as e:
            self.logger.error(f"Failed to clean profile directory: {e}")
    
    # Release port resources (kill any lingering processes on port)
    try:
        import subprocess
        subprocess.run(
            ["lsof", "-ti", f":{port}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )
    except Exception:
        pass  # Best effort cleanup
```

**Implementation Steps**:
- [ ] **4.1.1** Send SIGTERM for graceful Chrome shutdown
- [ ] **4.1.2** Wait for graceful shutdown (max 10 seconds)
- [ ] **4.1.3** Force kill with SIGKILL if needed
- [ ] **4.1.4** Clean up temporary Chrome profile directories
- [ ] **4.1.5** Release debugging port resources
- [ ] **4.1.6** Clear zombie pychrome connections

### 4.2 Chrome Process Restart

```python
def _restart_chrome_process(self, account_name: str, state: Dict) -> bool:
    """Restart Chrome process with preserved state"""
    try:
        # Generate new profile directory
        profile_dir = f"/tmp/chrome-dev-profile-{account_name}-{int(time.time())}"
        port = self.processes[account_name]["port"]
        
        # Verify port is available
        if not self._is_port_available(port):
            self.logger.error(f"Port {port} still in use, cannot restart")
            return False
        
        # Build Chrome command
        chrome_path = self._find_chrome_executable()
        chrome_cmd = [
            chrome_path,
            f"--remote-debugging-port={port}",
            f"--user-data-dir={profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "https://trader.tradovate.com"
        ]
        
        # Start Chrome process
        import subprocess
        process = subprocess.Popen(
            chrome_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid if hasattr(os, 'setsid') else None
        )
        
        # Update process tracking
        with self.process_lock:
            self.processes[account_name].update({
                "pid": process.pid,
                "profile_dir": profile_dir,
                "restart_time": datetime.now(),
                "state": ProcessState.STARTING
            })
        
        # Wait for Chrome to be ready
        if self._wait_for_chrome_ready(port, timeout=30):
            self.logger.info(f"Chrome restarted successfully for {account_name}")
            return True
        else:
            self.logger.error(f"Chrome restart failed - not ready within timeout")
            return False
            
    except Exception as e:
        self.logger.error(f"Chrome restart failed for {account_name}: {e}")
        return False

def _wait_for_chrome_ready(self, port: int, timeout: int = 30) -> bool:
    """Wait for Chrome to be ready for connections"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if self.is_chrome_responsive(port):
            return True
        time.sleep(1)
    
    return False
```

**Implementation Steps**:
- [ ] **4.2.1** Generate new Chrome profile directory path
- [ ] **4.2.2** Verify debugging port availability
- [ ] **4.2.3** Launch Chrome with identical parameters
- [ ] **4.2.4** Implement startup verification with timeout
- [ ] **4.2.5** Verify Chrome process health
- [ ] **4.2.6** Update process tracking with new PID

---

## Phase 5: State Restoration After Restart

### 5.1 Authentication Recovery

```python
def _restore_authentication(self, account_name: str, state: Dict) -> bool:
    """Restore authentication state after restart"""
    try:
        port = self.processes[account_name]["port"]
        credentials = state.get("credentials", {})
        
        if not credentials.get("username") or not credentials.get("password"):
            self.logger.error(f"No credentials found for {account_name}")
            return False
        
        # Navigate to login and authenticate
        success = self._execute_login_sequence(port, credentials)
        
        if success:
            self.logger.info(f"Authentication restored for {account_name}")
            return True
        else:
            self.logger.error(f"Authentication failed for {account_name}")
            return False
            
    except Exception as e:
        self.logger.error(f"Authentication restoration failed: {e}")
        return False

def _execute_login_sequence(self, port: int, credentials: Dict) -> bool:
    """Execute complete login sequence"""
    try:
        import pychrome
        browser = pychrome.Browser(url=f"http://localhost:{port}")
        
        # Wait for login page to load
        time.sleep(5)
        
        # Get first tab (should be Tradovate)
        tabs = browser.list_tab()
        if not tabs:
            return False
        
        tab = tabs[0]
        tab.start()
        
        # Inject login credentials
        login_js = f"""
        // Fill login form
        const emailInput = document.getElementById('name-input');
        const passwordInput = document.getElementById('password-input');
        
        if (emailInput && passwordInput) {{
            emailInput.value = '{credentials["username"]}';
            emailInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
            
            passwordInput.value = '{credentials["password"]}';  
            passwordInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
            
            // Click login button
            setTimeout(() => {{
                const loginButton = document.querySelector('button.MuiButton-containedPrimary');
                if (loginButton) {{
                    loginButton.click();
                }}
            }}, 500);
        }}
        """
        
        tab.Runtime.evaluate(expression=login_js)
        
        # Wait for login to complete and check for success
        time.sleep(10)
        
        # Check if login was successful
        check_login_js = """
        document.querySelector('.trading-interface') !== null ||
        document.querySelector('[data-testid="trading-view"]') !== null ||
        !document.querySelector('#name-input')
        """
        
        result = tab.Runtime.evaluate(expression=check_login_js)
        login_success = result.get("result", {}).get("value", False)
        
        tab.stop()
        return login_success
        
    except Exception as e:
        self.logger.error(f"Login sequence failed: {e}")
        return False
```

**Implementation Steps**:
- [ ] **5.1.1** Navigate to Tradovate login page
- [ ] **5.1.2** Inject credentials from preserved state
- [ ] **5.1.3** Execute login sequence with validation
- [ ] **5.1.4** Verify successful authentication
- [ ] **5.1.5** Handle multi-factor authentication
- [ ] **5.1.6** Restore session cookies and tokens

---

## Phase 6: Integration with Existing Code

### 6.1 Auto-Login Integration

**File Modifications**: `src/auto_login.py`

```python
# Add to imports
from utils.process_monitor import ChromeProcessMonitor

class MultiAccountLogin:
    def __init__(self):
        # ... existing code ...
        self.process_monitor = ChromeProcessMonitor()
        
    def launch_chrome_instances(self):
        """Modified to register with process monitor"""
        # ... existing launch code ...
        
        # Register each Chrome process with monitor
        for account_name, process_info in chrome_processes.items():
            self.process_monitor.register_process(
                account_name=account_name,
                pid=process_info["pid"],
                port=process_info["port"],
                profile_dir=process_info["profile_dir"]
            )
        
        # Start monitoring
        self.process_monitor.start_monitoring()
        
    def shutdown(self):
        """Clean shutdown with process monitor"""
        if hasattr(self, 'process_monitor'):
            self.process_monitor.stop_monitoring()
        # ... existing shutdown code ...
```

**Implementation Steps**:
- [ ] **6.1.1** Modify `src/auto_login.py` to register processes
- [ ] **6.1.2** Add watchdog initialization to launch function
- [ ] **6.1.3** Update process tracking integration
- [ ] **6.1.4** Modify shutdown to stop watchdog cleanly
- [ ] **6.1.5** Add watchdog status to monitoring reports
- [ ] **6.1.6** Update configuration loading

---

## TESTING REQUIREMENTS

### Unit Tests
```python
# test_process_monitor.py
def test_process_health_check():
    """Test health check mechanisms"""
    
def test_crash_detection():
    """Test crash detection logic"""
    
def test_state_preservation():
    """Test state capture and restoration"""
```

### Integration Tests
- Simulate Chrome process crashes during trading
- Test state preservation across restart cycles  
- Validate authentication recovery
- Test monitoring under load

### Load Tests
- Multiple simultaneous process failures
- High frequency health checks
- Memory usage under extended monitoring

---

## CONFIGURATION

**File**: `config/process_monitor.json`
```json
{
    "check_interval": 10,
    "max_restart_attempts": 3,
    "restart_delay": 5,
    "health_check_timeout": 30,
    "crash_confirmation_checks": 3,
    "crash_confirmation_interval": 10,
    "enable_state_preservation": true,
    "recovery_timeout": 300,
    "log_level": "INFO"
}
```

---

## SUCCESS METRICS

- **Process Uptime**: >99.9% availability
- **Recovery Time**: <30 seconds average restart time
- **False Positive Rate**: <1% crash detection errors  
- **State Preservation**: 100% successful state recovery
- **Authentication Success**: >99% login restoration rate

---

## OPERATIONAL PROCEDURES

### Monitoring Dashboard
- Real-time process health status
- Crash frequency and patterns
- Recovery success rates
- Performance metrics

### Alerting
- Immediate alerts on process crashes
- Escalation for repeated failures
- Performance degradation warnings

### Maintenance
- Regular health check calibration
- Log rotation and cleanup
- Configuration updates
- Performance optimization