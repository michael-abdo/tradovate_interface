#!/usr/bin/env python3
"""
Chrome Stability Monitor - Detects and logs Chrome GPU/stability issues
"""
import os
import time
import datetime
import json
import logging
from typing import Dict, List, Optional
import subprocess
import re
import requests
import socket
import threading
from enum import Enum

# Import Chrome Communication Framework for unified execution
try:
    from utils.chrome_communication import safe_evaluate, OperationType
    SAFE_EVAL_AVAILABLE = True
except ImportError:
    SAFE_EVAL_AVAILABLE = False

class ConnectionState(Enum):
    """Connection health states"""
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    FAILED = "failed"
    RECOVERING = "recovering"
    UNKNOWN = "unknown"

class FailureType(Enum):
    """Connection failure classification"""
    NETWORK_DISCONNECTION = "network_disconnection"
    SLOW_RESPONSE = "slow_response"
    AUTHENTICATION_EXPIRED = "authentication_expired"
    DOM_UNRESPONSIVE = "dom_unresponsive"
    JAVASCRIPT_FAILURE = "javascript_failure"
    WEBSOCKET_FAILURE = "websocket_failure"
    MARKET_DATA_STALE = "market_data_stale"

class ChromeStabilityMonitor:
    """Monitor Chrome instances for GPU crashes and stability issues"""
    
    def __init__(self, log_dir: str = "logs/chrome_stability", config_file: str = None):
        # Load configuration
        self.config = self._load_configuration(config_file)
        
        # Set up log directory from config or parameter
        if self.config.get('health_monitoring', {}).get('log_directory'):
            self.log_dir = self.config['health_monitoring']['log_directory']
        else:
            self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Set up logging
        log_level = getattr(logging, self.config.get('logging', {}).get('log_level', 'INFO'))
        log_file = os.path.join(self.log_dir, f"chrome_stability_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"ChromeStabilityMonitor initialized with config: {self.config.get('health_monitoring', {})}")
        
        # GPU error patterns to watch for
        self.gpu_error_patterns = [
            r"SharedImageManager",
            r"GPU process",
            r"gpu_memory_buffer",
            r"mailbox.*GPU",
            r"Failed to create shared image",
            r"GPU channel lost",
            r"Graphics pipeline error",
            r"WebGL.*lost context",
            r"GPU.*crashed",
            r"renderer.*crashed"
        ]
        
        # Chrome process tracking
        self.chrome_processes: Dict[int, dict] = {}
        
        # Connection health monitoring
        self.connection_health: Dict[str, dict] = {}  # account_name -> health data
        self.health_check_interval = self.config.get('health_monitoring', {}).get('check_interval_seconds', 10)
        self.health_monitoring_thread = None
        self.shutdown_event = threading.Event()
        self.health_lock = threading.RLock()
        
        # Health check thresholds from configuration
        thresholds = self.config.get('health_thresholds', {})
        self.degraded_response_time = thresholds.get('degraded_response_time_seconds', 2.0)
        self.failed_response_time = thresholds.get('failed_response_time_seconds', 5.0)
        self.failure_threshold = thresholds.get('consecutive_failure_threshold', 3)
        self.recovery_threshold = thresholds.get('consecutive_recovery_threshold', 2)
        
        # Network quality monitoring
        network_config = self.config.get('network_quality', {})
        self.network_monitoring_enabled = network_config.get('enabled', True)
        self.response_time_samples = network_config.get('response_time_samples', 10)
        self.latency_threshold_ms = network_config.get('latency_threshold_ms', 500)
        self.network_quality_data: Dict[str, dict] = {}  # account_name -> network metrics
        
    def _load_configuration(self, config_file: str = None) -> dict:
        """Load connection health configuration from JSON file"""
        if config_file is None:
            # Try to find config file relative to this module
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_file = os.path.join(current_dir, 'config', 'connection_health.json')
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                print(f"Loaded connection health configuration from: {config_file}")
                return config
            else:
                print(f"Configuration file not found at: {config_file}, using defaults")
                return self._get_default_config()
        except Exception as e:
            print(f"Error loading configuration from {config_file}: {e}, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """Get default configuration when config file is not available"""
        return {
            "health_monitoring": {
                "enabled": True,
                "check_interval_seconds": 10,
                "log_directory": "logs/connection_health",
                "background_monitoring": True
            },
            "health_thresholds": {
                "degraded_response_time_seconds": 2.0,
                "failed_response_time_seconds": 5.0,
                "consecutive_failure_threshold": 3,
                "consecutive_recovery_threshold": 2
            },
            "logging": {
                "log_level": "INFO"
            }
        }
        
    def find_chrome_processes(self) -> List[dict]:
        """Find all Chrome processes with remote debugging enabled"""
        processes = []
        try:
            # Use ps to find Chrome processes
            cmd = ["ps", "aux"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'remote-debugging-port' in line and 'Google Chrome' in line:
                        parts = line.split()
                        if len(parts) > 1:
                            pid = int(parts[1])
                            # Extract port from command line
                            port_match = re.search(r'--remote-debugging-port=(\d+)', line)
                            port = int(port_match.group(1)) if port_match else None
                            
                            processes.append({
                                'pid': pid,
                                'port': port,
                                'command': ' '.join(parts[10:]),  # Command and args
                                'start_time': datetime.datetime.now()
                            })
            
            return processes
            
        except Exception as e:
            self.logger.error(f"Error finding Chrome processes: {e}")
            return []
    
    def check_system_logs_for_gpu_errors(self) -> List[str]:
        """Check system logs for GPU-related errors (macOS specific)"""
        errors = []
        try:
            # Check system log for Chrome GPU errors in the last hour
            cmd = [
                "log", "show",
                "--predicate", "process == 'Google Chrome' OR process == 'Google Chrome Helper'",
                "--last", "1h",
                "--style", "syslog"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    for pattern in self.gpu_error_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            errors.append(line.strip())
                            break
            
            return errors
            
        except Exception as e:
            self.logger.error(f"Error checking system logs: {e}")
            return []
    
    def register_connection(self, account_name: str, port: int):
        """Register a connection for health monitoring"""
        with self.health_lock:
            self.connection_health[account_name] = {
                'port': port,
                'state': ConnectionState.UNKNOWN,
                'last_check': None,
                'consecutive_failures': 0,
                'consecutive_successes': 0,
                'response_times': [],
                'error_count': 0,
                'last_error': None,
                'registration_time': datetime.datetime.now()
            }
            self.logger.info(f"Registered connection for {account_name} on port {port}")
    
    def start_health_monitoring(self):
        """Start background connection health monitoring"""
        if self.health_monitoring_thread and self.health_monitoring_thread.is_alive():
            self.logger.warning("Health monitoring already running")
            return
        
        self.shutdown_event.clear()
        self.health_monitoring_thread = threading.Thread(
            target=self._health_monitoring_loop,
            name="ConnectionHealthMonitor",
            daemon=True
        )
        self.health_monitoring_thread.start()
        self.logger.info("Connection health monitoring started")
    
    def stop_health_monitoring(self):
        """Stop background health monitoring"""
        if self.health_monitoring_thread:
            self.logger.info("Stopping connection health monitoring...")
            self.shutdown_event.set()
            self.health_monitoring_thread.join(timeout=10)
            if self.health_monitoring_thread.is_alive():
                self.logger.warning("Health monitoring thread did not stop gracefully")
        
    def _health_monitoring_loop(self):
        """Main health monitoring loop"""
        while not self.shutdown_event.is_set():
            try:
                with self.health_lock:
                    accounts_to_check = list(self.connection_health.keys())
                
                for account_name in accounts_to_check:
                    if self.shutdown_event.is_set():
                        break
                    
                    try:
                        self._check_connection_health(account_name)
                    except Exception as e:
                        self.logger.error(f"Health check failed for {account_name}: {e}")
                
                # Wait for next check interval
                self.shutdown_event.wait(self.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"Health monitoring loop error: {e}")
                self.shutdown_event.wait(5)  # Brief pause before retry
    
    def _check_connection_health(self, account_name: str, process=None, browser=None, tab=None):
        """Perform comprehensive health check for a connection - DRY refactored
        
        Consolidates health checks from:
        - ChromeConnection.check_connection_health() 
        - TabHealthValidator.validate_tab_health()
        - Original _check_connection_health()
        
        Args:
            account_name: Account identifier
            process: Chrome process object (optional, for process checks)
            browser: pychrome Browser object (optional, for browser checks) 
            tab: pychrome Tab object (optional, for tab checks)
        """
        if account_name not in self.connection_health:
            return
        
        conn_info = self.connection_health[account_name]
        port = conn_info['port']
        
        health_result = {
            'account': account_name,
            'timestamp': datetime.datetime.now(),
            'healthy': True,
            'checks': {},
            'response_time': 0.0,
            'errors': []
        }
        
        # Process health check (from ChromeConnection pattern)
        if process is not None:
            if process.poll() is None:
                health_result['checks']['process_running'] = True
            else:
                health_result['checks']['process_running'] = False
                health_result['errors'].append("Chrome process not running")
                health_result['healthy'] = False
                self._update_connection_state(account_name, health_result)
                return
        
        # Browser responsiveness check (from ChromeConnection pattern)
        if browser is not None:
            try:
                tabs = browser.list_tab()
                health_result['checks']['browser_responsive'] = True
                health_result['checks']['tab_count'] = len(tabs)
            except Exception as e:
                health_result['checks']['browser_responsive'] = False
                health_result['errors'].append(f"Browser not responsive: {e}")
                health_result['healthy'] = False
                self._update_connection_state(account_name, health_result)
                return
        
        try:
            # Level 1: TCP Connection Test
            start_time = time.time()
            tcp_healthy = self._test_tcp_connection(port)
            tcp_time = time.time() - start_time
            
            health_result['checks']['tcp_connection'] = tcp_healthy
            health_result['checks']['tcp_response_time'] = tcp_time
            
            if not tcp_healthy:
                health_result['healthy'] = False
                health_result['errors'].append("TCP connection failed")
                self._update_connection_state(account_name, health_result)
                return
            
            # Level 2: HTTP Response Test  
            start_time = time.time()
            http_healthy, http_response_time = self._test_http_response(port)
            total_time = time.time() - start_time
            
            health_result['checks']['http_response'] = http_healthy
            health_result['checks']['http_response_time'] = http_response_time
            health_result['response_time'] = total_time
            
            if not http_healthy:
                health_result['healthy'] = False
                health_result['errors'].append("HTTP response failed")
            elif http_response_time > self.failed_response_time:
                health_result['healthy'] = False
                health_result['errors'].append(f"Response time too slow: {http_response_time:.2f}s")
            elif http_response_time > self.degraded_response_time:
                health_result['degraded'] = True
            
            # Level 3: JavaScript Execution Test
            if health_result['healthy']:
                js_healthy, js_response_time = self._test_javascript_execution(port)
                health_result['checks']['javascript_execution'] = js_healthy
                health_result['checks']['js_response_time'] = js_response_time
                
                if not js_healthy:
                    health_result['healthy'] = False
                    health_result['errors'].append("JavaScript execution failed")
            
            # Level 4: Tradovate Application Health  
            if health_result['healthy']:
                app_healthy = self._test_tradovate_application(port)
                health_result['checks']['tradovate_application'] = app_healthy
                
                if not app_healthy:
                    health_result['healthy'] = False
                    health_result['errors'].append("Tradovate application not responsive")
            
            # Level 5: Network Quality Assessment (if enabled)
            if self.network_monitoring_enabled:
                try:
                    network_metrics = self._assess_network_quality(account_name, port)
                    health_result['network_quality'] = network_metrics
                    
                    # Include network quality in overall health assessment
                    quality_score = network_metrics.get('quality_score', 100)
                    if quality_score < 50:  # Poor network quality threshold
                        health_result['degraded'] = True
                        if quality_score < 25:  # Critical network quality
                            health_result['healthy'] = False
                            health_result['errors'].append(f"Critical network quality: {quality_score:.1f}/100")
                        else:
                            health_result['errors'].append(f"Poor network quality: {quality_score:.1f}/100")
                            
                except Exception as e:
                    self.logger.warning(f"Network quality assessment failed for {account_name}: {e}")
                    health_result['network_quality'] = {'error': str(e)}
            
        except Exception as e:
            health_result['healthy'] = False
            health_result['errors'].append(f"Health check exception: {str(e)}")
        
        self._update_connection_state(account_name, health_result)
    
    def _test_tcp_connection(self, port: int) -> bool:
        """Test basic TCP connection to Chrome debugging port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def _test_http_response(self, port: int) -> tuple[bool, float]:
        """Test HTTP response time to Chrome debugging endpoint"""
        try:
            start_time = time.time()
            response = requests.get(
                f"http://localhost:{port}/json",
                timeout=self.failed_response_time
            )
            response_time = time.time() - start_time
            
            return response.status_code == 200, response_time
        except requests.RequestException:
            return False, float('inf')
    
    def _test_javascript_execution(self, port: int) -> tuple[bool, float]:
        """Test JavaScript execution via pychrome"""
        try:
            import pychrome
            
            start_time = time.time()
            browser = pychrome.Browser(url=f"http://localhost:{port}")
            tabs = browser.list_tab()
            
            if not tabs:
                return False, float('inf')
            
            # Test JavaScript execution on first available tab
            tab = tabs[0]
            tab.start()
            
            # Simple JavaScript execution test
            if SAFE_EVAL_AVAILABLE:
                result = safe_evaluate(
                    tab=tab,
                    js_code="1 + 1",
                    operation_type=OperationType.NON_CRITICAL,
                    description="Chrome stability basic JS execution test"
                )
                js_success = result.success and result.value == 2
            else:
                result = tab.Runtime.evaluate(expression="1 + 1")
                js_success = result.get("result", {}).get("value") == 2
            execution_time = time.time() - start_time
            
            # Don't stop tab - other parts of system may still be using it
            # Let Chrome manage tab lifecycle naturally
            
            # Check if execution was successful
            success = (
                js_success and
                execution_time < self.failed_response_time
            )
            
            return success, execution_time
            
        except Exception:
            return False, float('inf')
    
    def _test_tradovate_application(self, port: int) -> bool:
        """Test Tradovate application responsiveness"""
        try:
            import pychrome
            from utils.chrome_communication import safe_evaluate, OperationType
            
            browser = pychrome.Browser(url=f"http://localhost:{port}")
            tabs = browser.list_tab()
            
            # Find Tradovate tab
            tradovate_tab = None
            for tab in tabs:
                if "tradovate.com" in tab.url.lower():
                    tradovate_tab = tab
                    break
            
            if not tradovate_tab:
                return False
            
            tradovate_tab.start()
            
            # Test basic Tradovate application health
            app_health_js = """
            ({
                authenticated: !document.querySelector('#name-input'),
                tradingInterface: !!document.querySelector('.trading-interface, [data-testid="trading-view"]'),
                responsive: Date.now()
            })
            """
            
            if SAFE_EVAL_AVAILABLE:
                result = safe_evaluate(
                    tab=tradovate_tab,
                    js_code=app_health_js,
                    operation_type=OperationType.NON_CRITICAL,
                    description="Tradovate application health check"
                )
            else:
                result = tradovate_tab.Runtime.evaluate(expression=app_health_js)
            # Don't stop tradovate_tab - other parts of system may still be using it
            # Let Chrome manage tab lifecycle naturally
            
            if SAFE_EVAL_AVAILABLE:
                app_state = result.value if result.success else {}
            else:
                app_state = result.get("result", {}).get("value", {}) if result else {}
            
            return (
                app_state.get("authenticated", False) and
                isinstance(app_state.get("responsive"), (int, float))
            )
            
        except Exception:
            return False
    
    def _assess_network_quality(self, account_name: str, port: int) -> dict:
        """Assess network quality for a specific connection"""
        if not self.network_monitoring_enabled:
            return {}
        
        network_metrics = {
            'latency_ms': 0.0,
            'response_time_avg_ms': 0.0,
            'response_time_variance': 0.0,
            'connection_stability': 0.0,
            'quality_score': 0.0
        }
        
        try:
            # Measure multiple ping samples for better accuracy
            latency_samples = []
            response_time_samples = []
            
            for _ in range(min(5, self.response_time_samples // 2)):
                # TCP latency test
                start_time = time.time()
                tcp_healthy = self._test_tcp_connection(port)
                tcp_latency = (time.time() - start_time) * 1000  # Convert to ms
                
                if tcp_healthy:
                    latency_samples.append(tcp_latency)
                
                # HTTP response time test  
                start_time = time.time()
                http_healthy, http_time = self._test_http_response(port)
                http_response_ms = http_time * 1000  # Convert to ms
                
                if http_healthy:
                    response_time_samples.append(http_response_ms)
                
                # Brief pause between samples
                time.sleep(0.1)
            
            # Calculate network quality metrics
            if latency_samples:
                network_metrics['latency_ms'] = sum(latency_samples) / len(latency_samples)
            
            if response_time_samples:
                avg_response = sum(response_time_samples) / len(response_time_samples)
                network_metrics['response_time_avg_ms'] = avg_response
                
                # Calculate variance for stability assessment
                if len(response_time_samples) > 1:
                    variance = sum((x - avg_response) ** 2 for x in response_time_samples) / (len(response_time_samples) - 1)
                    network_metrics['response_time_variance'] = variance
                
            # Connection stability based on success rate
            total_samples = min(5, self.response_time_samples // 2)
            successful_samples = len(response_time_samples)
            network_metrics['connection_stability'] = successful_samples / total_samples if total_samples > 0 else 0.0
            
            # Overall quality score (0-100)
            quality_score = 100.0
            
            # Penalize high latency
            if network_metrics['latency_ms'] > self.latency_threshold_ms:
                quality_score -= 30
            elif network_metrics['latency_ms'] > self.latency_threshold_ms / 2:
                quality_score -= 15
            
            # Penalize slow response times
            if network_metrics['response_time_avg_ms'] > 2000:
                quality_score -= 25
            elif network_metrics['response_time_avg_ms'] > 1000:
                quality_score -= 10
            
            # Penalize high variance (instability)
            if network_metrics['response_time_variance'] > 500:
                quality_score -= 20
            elif network_metrics['response_time_variance'] > 200:
                quality_score -= 10
            
            # Penalize poor connection stability
            stability_penalty = (1.0 - network_metrics['connection_stability']) * 25
            quality_score -= stability_penalty
            
            network_metrics['quality_score'] = max(0.0, quality_score)
            
            # Store historical data
            if account_name not in self.network_quality_data:
                self.network_quality_data[account_name] = {
                    'samples': [],
                    'last_update': datetime.datetime.now()
                }
            
            # Keep last N samples for trend analysis
            self.network_quality_data[account_name]['samples'].append({
                'timestamp': datetime.datetime.now(),
                'metrics': network_metrics.copy()
            })
            
            # Limit historical data
            max_samples = self.response_time_samples
            if len(self.network_quality_data[account_name]['samples']) > max_samples:
                self.network_quality_data[account_name]['samples'] = \
                    self.network_quality_data[account_name]['samples'][-max_samples:]
            
            self.network_quality_data[account_name]['last_update'] = datetime.datetime.now()
            
        except Exception as e:
            self.logger.error(f"Network quality assessment failed for {account_name}: {e}")
            network_metrics['error'] = str(e)
        
        return network_metrics
    
    def get_network_quality_summary(self) -> dict:
        """Get network quality summary for all monitored connections"""
        summary = {
            'timestamp': datetime.datetime.now().isoformat(),
            'network_monitoring_enabled': self.network_monitoring_enabled,
            'connections': {}
        }
        
        for account_name, quality_data in self.network_quality_data.items():
            if quality_data['samples']:
                latest_sample = quality_data['samples'][-1]
                recent_samples = quality_data['samples'][-5:]  # Last 5 samples
                
                # Calculate trends
                latencies = [s['metrics'].get('latency_ms', 0) for s in recent_samples]
                response_times = [s['metrics'].get('response_time_avg_ms', 0) for s in recent_samples]
                quality_scores = [s['metrics'].get('quality_score', 0) for s in recent_samples]
                
                avg_latency = sum(latencies) / len(latencies) if latencies else 0
                avg_response_time = sum(response_times) / len(response_times) if response_times else 0
                avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
                
                # Determine trend direction
                latency_trend = "stable"
                quality_trend = "stable"
                
                if len(latencies) >= 3:
                    if latencies[-1] > latencies[-3] * 1.2:
                        latency_trend = "increasing"
                    elif latencies[-1] < latencies[-3] * 0.8:
                        latency_trend = "decreasing"
                
                if len(quality_scores) >= 3:
                    if quality_scores[-1] > quality_scores[-3] * 1.1:
                        quality_trend = "improving"
                    elif quality_scores[-1] < quality_scores[-3] * 0.9:
                        quality_trend = "degrading"
                
                summary['connections'][account_name] = {
                    'latest_metrics': latest_sample['metrics'],
                    'trend_analysis': {
                        'avg_latency_ms': round(avg_latency, 2),
                        'avg_response_time_ms': round(avg_response_time, 2),
                        'avg_quality_score': round(avg_quality, 1),
                        'latency_trend': latency_trend,
                        'quality_trend': quality_trend
                    },
                    'sample_count': len(quality_data['samples']),
                    'last_update': quality_data['last_update'].isoformat()
                }
        
        return summary
    
    def _update_connection_state(self, account_name: str, health_result: dict):
        """Update connection state based on health check results"""
        with self.health_lock:
            if account_name not in self.connection_health:
                return
            
            conn_info = self.connection_health[account_name]
            previous_state = conn_info['state']
            
            # Update metrics
            conn_info['last_check'] = health_result['timestamp']
            if 'response_time' in health_result:
                conn_info['response_times'].append(health_result['response_time'])
                # Keep only last 10 response times
                conn_info['response_times'] = conn_info['response_times'][-10:]
            
            # Determine new state
            if health_result['healthy']:
                conn_info['consecutive_successes'] += 1
                conn_info['consecutive_failures'] = 0
                
                if conn_info['consecutive_successes'] >= self.recovery_threshold:
                    new_state = ConnectionState.HEALTHY
                else:
                    new_state = ConnectionState.RECOVERING if previous_state == ConnectionState.FAILED else ConnectionState.HEALTHY
            else:
                conn_info['consecutive_failures'] += 1
                conn_info['consecutive_successes'] = 0
                conn_info['error_count'] += 1
                conn_info['last_error'] = health_result.get('errors', [])
                
                if conn_info['consecutive_failures'] >= self.failure_threshold:
                    new_state = ConnectionState.FAILED
                elif health_result.get('degraded', False):
                    new_state = ConnectionState.DEGRADED
                else:
                    new_state = ConnectionState.DEGRADED
            
            # Update state
            conn_info['state'] = new_state
            
            # Log state changes
            if new_state != previous_state:
                self.logger.info(
                    f"Connection state changed for {account_name}: "
                    f"{previous_state.value if previous_state else 'unknown'} -> {new_state.value}"
                )
    
    def check_unified_health(self, account_name: str, process=None, browser=None, tab=None) -> dict:
        """Unified health check method - DRY refactored entry point
        
        This method consolidates all health check patterns into one place.
        Call this instead of implementing custom health checks.
        
        Args:
            account_name: Account identifier
            process: Chrome process object (optional)
            browser: pychrome Browser object (optional)
            tab: pychrome Tab object (optional)
            
        Returns:
            dict: Health check results with 'healthy' boolean and detailed checks
        """
        # Register connection if not already registered
        if account_name not in self.connection_health:
            # Extract port from browser or use default
            port = None
            if browser:
                try:
                    # Extract port from browser URL
                    import re
                    match = re.search(r':(\d+)', str(browser._url))
                    if match:
                        port = int(match.group(1))
                except:
                    pass
            
            if port:
                self.register_connection(account_name, port)
            else:
                # Return basic health check without registration
                return {
                    'account': account_name,
                    'healthy': False,
                    'checks': {},
                    'errors': ['Connection not registered and port unknown']
                }
        
        # Perform unified health check
        self._check_connection_health(account_name, process, browser, tab)
        
        # Return the latest health result
        with self.health_lock:
            conn_info = self.connection_health.get(account_name, {})
            if conn_info and conn_info.get('health_checks'):
                return conn_info['health_checks'][-1]
            else:
                return {
                    'account': account_name,
                    'healthy': False,
                    'checks': {},
                    'errors': ['No health check data available']
                }
    
    def get_connection_health_status(self) -> dict:
        """Get current health status of all connections"""
        with self.health_lock:
            status = {
                'timestamp': datetime.datetime.now().isoformat(),
                'monitoring_active': self.health_monitoring_thread and self.health_monitoring_thread.is_alive(),
                'connections': {}
            }
            
            for account_name, conn_info in self.connection_health.items():
                avg_response_time = (
                    sum(conn_info['response_times']) / len(conn_info['response_times'])
                    if conn_info['response_times'] else 0.0
                )
                
                status['connections'][account_name] = {
                    'state': conn_info['state'].value,
                    'port': conn_info['port'],
                    'consecutive_failures': conn_info['consecutive_failures'],
                    'consecutive_successes': conn_info['consecutive_successes'],
                    'error_count': conn_info['error_count'],
                    'avg_response_time': round(avg_response_time, 3),
                    'last_check': conn_info['last_check'].isoformat() if conn_info['last_check'] else None,
                    'last_error': conn_info['last_error']
                }
            
            return status
    
    def analyze_chrome_stability(self) -> dict:
        """Analyze Chrome stability and return report"""
        report = {
            'timestamp': datetime.datetime.now().isoformat(),
            'chrome_processes': [],
            'gpu_errors': [],
            'connection_health': {},
            'recommendations': []
        }
        
        # Find Chrome processes
        processes = self.find_chrome_processes()
        report['chrome_processes'] = processes
        
        # Check for GPU errors
        gpu_errors = self.check_system_logs_for_gpu_errors()
        report['gpu_errors'] = gpu_errors
        
        # Get connection health status
        connection_health = self.get_connection_health_status()
        report['connection_health'] = connection_health
        
        # Generate recommendations based on findings
        if gpu_errors:
            report['recommendations'].append(
                "GPU errors detected. Chrome has been configured with GPU workaround flags."
            )
            report['recommendations'].append(
                "If crashes persist, try: 1) Update Chrome, 2) Update macOS, 3) Reset Chrome profile"
            )
        
        if len(processes) > 5:
            report['recommendations'].append(
                f"High number of Chrome processes ({len(processes)}). Consider reducing concurrent instances."
            )
        
        # Generate connection health recommendations
        connections = connection_health.get('connections', {})
        failed_connections = [name for name, info in connections.items() if info['state'] == 'failed']
        degraded_connections = [name for name, info in connections.items() if info['state'] == 'degraded']
        slow_connections = [name for name, info in connections.items() if info.get('avg_response_time', 0) > 2.0]
        
        if failed_connections:
            report['recommendations'].append(
                f"Connection failures detected for: {', '.join(failed_connections)}. Check network and Chrome stability."
            )
        
        if degraded_connections:
            report['recommendations'].append(
                f"Degraded connections detected for: {', '.join(degraded_connections)}. Monitor for recovery."
            )
        
        if slow_connections:
            report['recommendations'].append(
                f"Slow response times detected for: {', '.join(slow_connections)}. Check system performance."
            )
        
        if not connection_health.get('monitoring_active', False):
            report['recommendations'].append(
                "Connection health monitoring is not active. Start monitoring for better reliability."
            )
        
        # Log the report
        # Convert datetime objects to strings for JSON serialization
        report_json = json.dumps(report, indent=2, default=str)
        self.logger.info(f"Stability report: {report_json}")
        
        # Save report to file
        report_file = os.path.join(self.log_dir, f"stability_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return report
    
    def monitor_chrome_logs(self, tab, callback=None):
        """Monitor Chrome console logs for GPU errors"""
        def log_handler(entry):
            """Handle log entries from Chrome"""
            if entry.get('level', '').upper() in ['ERROR', 'WARNING']:
                text = entry.get('text', '')
                
                # Check for GPU-related errors
                for pattern in self.gpu_error_patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        self.logger.error(f"GPU Error detected: {text}")
                        
                        # Save to error log
                        error_file = os.path.join(self.log_dir, "gpu_errors.log")
                        with open(error_file, 'a') as f:
                            f.write(f"{datetime.datetime.now().isoformat()} - {text}\n")
                        
                        if callback:
                            callback('gpu_error', entry)
                        break
        
        return log_handler
    
    def get_chrome_memory_usage(self, pid: int) -> Optional[dict]:
        """Get memory usage for a Chrome process"""
        try:
            cmd = ["ps", "-o", "pid,vsz,rss,comm", "-p", str(pid)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].split()
                    return {
                        'pid': int(parts[0]),
                        'vsz_kb': int(parts[1]),
                        'rss_kb': int(parts[2]),
                        'vsz_mb': int(parts[1]) / 1024,
                        'rss_mb': int(parts[2]) / 1024
                    }
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting memory usage for PID {pid}: {e}")
            return None
    
    def create_stability_report(self) -> str:
        """Create a comprehensive stability report"""
        report = self.analyze_chrome_stability()
        
        # Add memory usage information
        for process in report['chrome_processes']:
            memory = self.get_chrome_memory_usage(process['pid'])
            if memory:
                process['memory'] = memory
        
        # Format report for display
        report_text = f"""
Chrome Stability Report - {report['timestamp']}
{'=' * 60}

Active Chrome Processes: {len(report['chrome_processes'])}
"""
        
        for proc in report['chrome_processes']:
            report_text += f"\n  PID: {proc['pid']}, Port: {proc['port']}"
            if 'memory' in proc:
                report_text += f", Memory: {proc['memory']['rss_mb']:.1f} MB"
        
        if report['gpu_errors']:
            report_text += f"\n\nGPU Errors Found: {len(report['gpu_errors'])}\n"
            report_text += "Recent GPU errors:\n"
            for error in report['gpu_errors'][:5]:  # Show first 5
                report_text += f"  - {error[:100]}...\n"
        else:
            report_text += "\n\nNo GPU errors detected in system logs."
        
        if report['recommendations']:
            report_text += "\n\nRecommendations:\n"
            for rec in report['recommendations']:
                report_text += f"  • {rec}\n"
        
        report_text += "\n" + "=" * 60
        
        return report_text


def main():
    """Run stability check as standalone tool"""
    monitor = ChromeStabilityMonitor()
    print(monitor.create_stability_report())
    
    # Save detailed report
    report = monitor.analyze_chrome_stability()
    print(f"\nDetailed report saved to: {monitor.log_dir}")
    
    if report['gpu_errors']:
        print("\n⚠️  GPU errors detected! Chrome may be experiencing stability issues.")
        print("The Chrome launch parameters have been updated with GPU workarounds.")
    else:
        print("\n✅ No GPU errors detected in recent logs.")


if __name__ == "__main__":
    main()