import psutil
import threading
import time
import json
import os
import queue
import requests
import subprocess
import shutil
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

class CrashType(Enum):
    PROCESS_DIED = "process_died"
    PORT_UNRESPONSIVE = "port_unresponsive" 
    TAB_CRASHED = "tab_crashed"
    AUTHENTICATION_FAILED = "auth_failed"

class ChromeProcessMonitor:
    def __init__(self, config_path: str = "config/process_monitor.json"):
        self.processes: Dict[str, Dict] = {}
        self.monitoring_thread = None
        self.shutdown_event = threading.Event()
        self.process_lock = threading.RLock()
        self.logger = self._setup_logger()
        self.config = self._load_config(config_path)
        
    def _setup_logger(self):
        """Setup logging for process monitor"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # File handler
        file_handler = logging.FileHandler(f"logs/chrome_monitor_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
        
    def _load_config(self, config_path: str) -> Dict:
        """Load monitoring configuration"""
        default_config = {
            "check_interval": 10,  # seconds
            "max_restart_attempts": 3,
            "restart_delay": 5,  # seconds between restarts
            "health_check_timeout": 30,  # seconds
            "crash_confirmation_checks": 3,
            "crash_confirmation_interval": 10,  # seconds
            "enable_state_preservation": True,
            "recovery_timeout": 300,  # seconds
            "log_level": "INFO"
        }
        
        # Check if path is relative and adjust
        if not os.path.isabs(config_path):
            # Try multiple possible locations
            possible_paths = [
                config_path,
                os.path.join("tradovate_interface", config_path),
                os.path.join("..", "tradovate_interface", config_path),
                os.path.join(os.path.dirname(__file__), "..", "..", config_path)
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    config_path = path
                    break
        
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
                self.logger.info(f"Loaded config from {config_path}")
        except FileNotFoundError:
            if hasattr(self, 'logger'):
                self.logger.warning(f"Config file {config_path} not found, using defaults")
            else:
                print(f"Warning: Config file {config_path} not found, using defaults")
        except json.JSONDecodeError as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Invalid JSON in config file: {e}")
        
        return default_config

    def register_process(self, account_name: str, pid: int, port: int, profile_dir: Optional[str] = None):
        """Register a Chrome process for monitoring"""
        # SAFETY: Never monitor port 9222 - reserved for main Chrome instance
        if port == 9222:
            self.logger.warning(f"SKIPPING registration for port 9222 - this port is protected from monitoring")
            return
            
        with self.process_lock:
            self.processes[account_name] = {
                "pid": pid,
                "port": port,
                "profile_dir": profile_dir,
                "state": ProcessState.RUNNING,
                "registered_time": datetime.now(),
                "last_healthy": datetime.now(),
                "consecutive_failures": 0,
                "restart_attempts": 0,
                "last_restart": None
            }
            self.logger.info(f"Registered Chrome process for {account_name} - PID: {pid}, Port: {port}")

    def unregister_process(self, account_name: str):
        """Remove a process from monitoring"""
        with self.process_lock:
            if account_name in self.processes:
                del self.processes[account_name]
                self.logger.info(f"Unregistered Chrome process for {account_name}")

    def is_process_alive(self, pid: int) -> bool:
        """Check if process with given PID exists and is running"""
        try:
            return psutil.pid_exists(pid) and psutil.Process(pid).is_running()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def is_chrome_responsive(self, port: int) -> bool:
        """Test Chrome debugging port responsiveness"""
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
                if "tradovate" in tab.url.lower() or "trader.tradovate.com" in tab.url.lower():
                    tab_instance = None
                    try:
                        tab_instance = browser.connect_tab(tab.id)
                        tab_instance.start()
                        result = tab_instance.Runtime.evaluate(expression="document.readyState")
                        return result.get("result", {}).get("value") == "complete"
                    except Exception as e:
                        self.logger.debug(f"Tab evaluation failed: {e}")
                        return False
                    finally:
                        if tab_instance:
                            try:
                                tab_instance.stop()
                            except:
                                pass
            return False
        except Exception as e:
            self.logger.debug(f"Tradovate accessibility check failed: {e}")
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
            self.logger.info("Stopping Chrome process monitoring...")
            self.shutdown_event.set()
            self.monitoring_thread.join(timeout=10)
            if self.monitoring_thread.is_alive():
                self.logger.warning("Monitoring thread did not stop gracefully")
        self.logger.info("Chrome process monitoring stopped")

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

    def _trigger_restart(self, account_name: str, crash_type: CrashType, health_status: Dict):
        """Trigger restart procedure for crashed Chrome"""
        with self.process_lock:
            process_info = self.processes[account_name]
            
            # Check restart attempts
            if process_info["restart_attempts"] >= self.config["max_restart_attempts"]:
                self.logger.error(f"Max restart attempts reached for {account_name}. Marking as FAILED.")
                process_info["state"] = ProcessState.FAILED
                return
            
            # Validate crash before proceeding
            if not self._validate_crash(account_name, crash_type):
                return
            
            self.logger.warning(f"Initiating restart for {account_name} due to {crash_type.value}")
            process_info["state"] = ProcessState.RESTARTING
            process_info["restart_attempts"] += 1
            
            # Capture state before restart
            state = None
            if self.config["enable_state_preservation"]:
                state = self._capture_account_state(account_name)
                if state:
                    self._save_state_to_file(account_name, state)
            
            # Clean shutdown
            if self._clean_shutdown_chrome(account_name):
                # Wait before restart
                time.sleep(self.config["restart_delay"])
                
                # Restart Chrome
                if self._restart_chrome_process(account_name, state):
                    # Restore state if available
                    if state and self.config["enable_state_preservation"]:
                        self._restore_authentication(account_name, state)
                    
                    process_info["last_restart"] = datetime.now()
                    process_info["consecutive_failures"] = 0
                    self.logger.info(f"Successfully restarted Chrome for {account_name}")
                else:
                    process_info["state"] = ProcessState.FAILED
                    self.logger.error(f"Failed to restart Chrome for {account_name}")
            else:
                self.logger.error(f"Failed to shutdown Chrome for {account_name}")

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
        # Convert process_info to serializable format
        process_info = self.processes.get(account_name, {})
        serializable_process_info = {}
        for key, value in process_info.items():
            if isinstance(value, ProcessState):
                serializable_process_info[key] = value.value
            elif isinstance(value, datetime):
                serializable_process_info[key] = value.isoformat()
            else:
                serializable_process_info[key] = value
                
        crash_details = {
            "timestamp": datetime.now().isoformat(),
            "account": account_name,
            "crash_type": crash_type.value,
            "validation_results": validation_results,
            "process_info": serializable_process_info,
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

    def _get_account_credentials(self, account_name: str) -> Dict:
        """Get account credentials from configuration"""
        # Load credentials from the main config
        cred_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "credentials.json")
        try:
            with open(cred_path, 'r') as f:
                all_credentials = json.load(f)
                # Map account name to email
                account_mapping = {
                    "Account 1": "stonkz92224@gmail.com",
                    "Account 2": "zenex3298@gmail.com"
                }
                email = account_mapping.get(account_name)
                if email and email in all_credentials:
                    return {
                        "username": email,
                        "password": all_credentials[email]
                    }
        except Exception as e:
            self.logger.error(f"Failed to load credentials: {e}")
        return {}

    def _capture_trading_state(self, port: int) -> Dict:
        """Capture current trading state via JavaScript"""
        try:
            import pychrome
            browser = pychrome.Browser(url=f"http://localhost:{port}")
            tab = None
            
            # Find Tradovate tab
            for t in browser.list_tab():
                if "tradovate" in t.url.lower():
                    tab = t
                    break
            
            if not tab:
                return {"error": "No Tradovate tab found"}
            
            tab_instance = browser.connect_tab(tab.id)
            tab_instance.start()
            
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
            
            result = tab_instance.Runtime.evaluate(expression=js_code)
            tab_instance.stop()
            
            return result.get("result", {}).get("value", {})
            
        except Exception as e:
            return {"error": str(e)}

    def _capture_ui_state(self, port: int) -> Dict:
        """Capture UI state like selected dropdowns"""
        # Similar to trading state but for UI elements
        return {"placeholder": "UI state capture"}

    def _capture_connection_state(self, account_name: str) -> Dict:
        """Capture connection and session state"""
        process_info = self.processes.get(account_name, {})
        return {
            "port": process_info.get("port"),
            "pid": process_info.get("pid"),
            "uptime": str(datetime.now() - process_info.get("registered_time", datetime.now()))
        }

    def _save_state_to_file(self, account_name: str, state: Dict):
        """Save state to recovery file"""
        recovery_dir = "recovery"
        os.makedirs(recovery_dir, exist_ok=True)
        
        state_file = os.path.join(recovery_dir, f"{account_name}_state.json")
        
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        self.logger.info(f"State saved to {state_file}")
        return state_file

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
                shutil.rmtree(profile_dir)
                self.logger.info(f"Cleaned up profile directory: {profile_dir}")
            except Exception as e:
                self.logger.error(f"Failed to clean profile directory: {e}")
        
        # Release port resources (kill any lingering processes on port)
        try:
            subprocess.run(
                ["lsof", "-ti", f":{port}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
        except Exception:
            pass  # Best effort cleanup

    def _restart_chrome_process(self, account_name: str, state: Dict) -> bool:
        """Restart Chrome process with preserved state"""
        try:
            # Generate new profile directory
            profile_dir = f"/tmp/chrome-dev-profile-{account_name.replace(' ', '-')}-{int(time.time())}"
            port = self.processes[account_name]["port"]
            
            # SAFETY: Never restart Chrome on port 9222
            if port == 9222:
                self.logger.error(f"REFUSING to restart Chrome on protected port 9222")
                return False
            
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
                "--disable-gpu-sandbox",
                "--disable-software-rasterizer",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-gpu-compositing",
                "https://trader.tradovate.com"
            ]
            
            # Start Chrome process
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

    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available for use"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return True
            except OSError:
                return False

    def _find_chrome_executable(self) -> str:
        """Find Chrome executable path"""
        # macOS paths
        chrome_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chrome.app/Contents/MacOS/Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium"
        ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                return path
        
        # Try to find via which command
        try:
            result = subprocess.run(["which", "google-chrome"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        raise FileNotFoundError("Chrome executable not found")

    def _wait_for_chrome_ready(self, port: int, timeout: int = 30) -> bool:
        """Wait for Chrome to be ready for connections"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_chrome_responsive(port):
                return True
            time.sleep(1)
        
        return False

    def _restore_authentication(self, account_name: str, state: Dict) -> bool:
        """Restore authentication state after restart"""
        try:
            port = self.processes[account_name]["port"]
            credentials = state.get("credentials", {})
            
            if not credentials.get("username") or not credentials.get("password"):
                self.logger.error(f"No credentials found for {account_name}")
                return False
            
            # Wait for Tradovate page to load
            time.sleep(10)
            
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
            
            # Get first tab (should be Tradovate)
            tabs = browser.list_tab()
            if not tabs:
                return False
            
            tab = browser.connect_tab(tabs[0].id)
            tab.start()
            
            # Wait for login form
            time.sleep(5)
            
            # Check if already logged in
            check_logged_in = """
            document.querySelector('.trading-interface') !== null ||
            document.querySelector('[data-testid="trading-view"]') !== null ||
            !document.querySelector('#name-input')
            """
            
            result = tab.Runtime.evaluate(expression=check_logged_in)
            if result.get("result", {}).get("value", False):
                self.logger.info("Already logged in")
                tab.stop()
                return True
            
            # Inject login credentials
            login_js = f"""
            // Wait for form elements
            setTimeout(() => {{
                const emailInput = document.getElementById('name-input');
                const passwordInput = document.getElementById('password-input');
                
                if (emailInput && passwordInput) {{
                    // Fill email
                    emailInput.value = '{credentials["username"]}';
                    emailInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    emailInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    
                    // Fill password
                    passwordInput.value = '{credentials["password"]}';  
                    passwordInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    passwordInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    
                    // Click login button
                    setTimeout(() => {{
                        const loginButton = document.querySelector('button.MuiButton-containedPrimary') || 
                                          document.querySelector('button[type="submit"]');
                        if (loginButton) {{
                            loginButton.click();
                        }}
                    }}, 1000);
                }}
            }}, 2000);
            """
            
            tab.Runtime.evaluate(expression=login_js)
            
            # Wait for login to complete
            time.sleep(15)
            
            # Check if login was successful
            result = tab.Runtime.evaluate(expression=check_logged_in)
            login_success = result.get("result", {}).get("value", False)
            
            tab.stop()
            return login_success
            
        except Exception as e:
            self.logger.error(f"Login sequence failed: {e}")
            return False

    def get_status(self) -> Dict:
        """Get current status of all monitored processes"""
        with self.process_lock:
            status = {
                "monitoring_active": self.monitoring_thread and self.monitoring_thread.is_alive(),
                "processes": {}
            }
            
            for account_name, process_info in self.processes.items():
                status["processes"][account_name] = {
                    "state": process_info["state"].value,
                    "pid": process_info["pid"],
                    "port": process_info["port"],
                    "consecutive_failures": process_info["consecutive_failures"],
                    "restart_attempts": process_info["restart_attempts"],
                    "last_healthy": process_info["last_healthy"].isoformat(),
                    "uptime": str(datetime.now() - process_info["registered_time"])
                }
            
            return status