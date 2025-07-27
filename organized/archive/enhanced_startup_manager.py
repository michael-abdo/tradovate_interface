#!/usr/bin/env python3
"""
Enhanced Startup Manager - Implements robust Chrome startup with comprehensive error handling
"""

import os
import sys
import time
import socket
import subprocess
import psutil
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from contextlib import contextmanager

# Import our utility modules
from chrome_path_finder import get_chrome_finder
from structured_logger import get_logger
from chrome_cleanup import ChromeCleanup


class StartupValidationError(Exception):
    """Custom exception for startup validation failures"""
    pass


class StartupManager:
    """Enhanced Chrome startup manager with comprehensive error handling and retry logic"""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize with configuration and utilities"""
        self.logger = get_logger("startup_manager", log_file="startup/startup_manager.log")
        self.config = self._load_startup_config(config_file)
        
        # Apply configuration
        startup_config = self.config.get('startup_monitoring', {})
        self.max_retries = startup_config.get('startup_retry_attempts', startup_config.get('max_retries', 3))
        self.retry_delay = startup_config.get('startup_retry_delay_seconds', startup_config.get('retry_delay_seconds', 10))
        self.startup_timeout = startup_config.get('startup_timeout_seconds', 60)
        self.required_ports = [9223, 9224]
        
        # Initialize utilities
        self.chrome_finder = get_chrome_finder()
        self.chrome_cleanup = ChromeCleanup()
        
        # Process monitor integration
        self.process_monitor = None
        self._init_process_monitor()
        
        # Startup tracking
        self.startup_log = []
        self.startup_stats = {
            'start_time': None,
            'end_time': None,
            'attempts': 0,
            'success': False,
            'errors': []
        }
    
    def _load_startup_config(self, config_file: Optional[str] = None) -> dict:
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
                self.logger.info("Loaded startup configuration", config_file=config_file)
                return config
            else:
                self.logger.warning("Configuration file not found, using defaults", config_file=config_file)
                return self._get_default_startup_config()
        except Exception as e:
            self.logger.error("Error loading configuration, using defaults", error=str(e))
            return self._get_default_startup_config()
    
    def _get_default_startup_config(self) -> dict:
        """Get default startup configuration"""
        return {
            "startup_monitoring": {
                "enabled": True,
                "startup_retry_attempts": 3,
                "startup_retry_delay_seconds": 10,
                "startup_timeout_seconds": 60,
                "startup_phases": {
                    "chrome_launch": {
                        "timeout_seconds": 30,
                        "validation_required": True
                    },
                    "page_load": {
                        "timeout_seconds": 45,
                        "validation_required": True
                    },
                    "authentication": {
                        "timeout_seconds": 60,
                        "validation_required": True
                    },
                    "trading_interface": {
                        "timeout_seconds": 45,
                        "validation_required": True
                    }
                },
                "startup_failure_actions": {
                    "log_failure": True,
                    "alert_on_failure": True,
                    "auto_retry": True,
                    "escalate_after_retries": 3
                },
                "startup_metrics": {
                    "collect_timing_data": True,
                    "track_resource_usage": True,
                    "log_performance_metrics": True
                },
                "validation_checks": {
                    "ports": True,
                    "memory": True,
                    "network": True,
                    "chrome_executable": True,
                    "websocket_connectivity": True
                },
                "cleanup_on_failure": True,
                "required_memory_gb": 2.0,
                "network_test_url": "https://trader.tradovate.com",
                "network_timeout_seconds": 10
            }
        }
    
    def _init_process_monitor(self):
        """Initialize process monitor if available"""
        try:
            # Import inside method to avoid circular dependencies
            # Process monitor was moved to archive with tradovate_interface
            from tradovate_interface.src.utils.process_monitor import ChromeProcessMonitor, StartupMonitoringMode
            
            self.process_monitor = ChromeProcessMonitor()
            self.process_monitor.enable_startup_monitoring(StartupMonitoringMode.ACTIVE)
            self.logger.info("Chrome process monitor initialized for startup")
        except Exception as e:
            self.logger.warning("Process monitor not available", error=str(e))
            self.process_monitor = None
    
    def log_event(self, event: str, details: str = "", success: bool = True, **kwargs):
        """Log startup events with structured data"""
        timestamp = datetime.now()
        log_entry = {
            'timestamp': timestamp.isoformat(),
            'event': event,
            'details': details,
            'success': success,
            'attempt': self.startup_stats['attempts'],
            **kwargs
        }
        self.startup_log.append(log_entry)
        
        # Log to structured logger
        if success:
            self.logger.info(f"Startup event: {event}", event_type=event, details=details, **kwargs)
        else:
            self.logger.error(f"Startup failure: {event}", event_type=event, details=details, **kwargs)
            self.startup_stats['errors'].append(log_entry)
    
    @contextmanager
    def startup_phase(self, phase_name: str):
        """Context manager for tracking startup phases"""
        self.log_event(f"{phase_name}_start", f"Starting {phase_name}")
        start_time = time.time()
        
        try:
            yield
            duration = time.time() - start_time
            self.log_event(f"{phase_name}_complete", 
                         f"Completed {phase_name} in {duration:.2f}s",
                         duration_seconds=duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_event(f"{phase_name}_failed", 
                         f"Failed {phase_name} after {duration:.2f}s: {e}",
                         success=False,
                         duration_seconds=duration,
                         error=str(e))
            raise
    
    def validate_ports(self) -> bool:
        """Check if required ports are available"""
        validation_config = self.config.get('startup_monitoring', {}).get('validation_checks', {})
        if not validation_config.get('ports', True):
            self.log_event("port_validation", "Port validation disabled by config")
            return True
        
        try:
            for port in self.required_ports:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                
                if result == 0:
                    self.log_event("port_validation", f"Port {port} already in use", False, port=port)
                    
                    # Try to identify what's using the port
                    try:
                        for proc in psutil.process_iter(['pid', 'name']):
                            for conn in proc.connections(kind='inet'):
                                if conn.laddr.port == port:
                                    self.logger.warning("Port in use by process", 
                                                      port=port, 
                                                      pid=proc.info['pid'], 
                                                      name=proc.info['name'])
                    except Exception:
                        pass
                    
                    return False
            
            self.log_event("port_validation", f"Ports {self.required_ports} available", True)
            return True
            
        except Exception as e:
            self.log_event("port_validation", f"Port check failed: {e}", False, error=str(e))
            return False
    
    def validate_memory(self) -> bool:
        """Check if sufficient memory is available"""
        validation_config = self.config.get('startup_monitoring', {}).get('validation_checks', {})
        if not validation_config.get('memory', True):
            self.log_event("memory_validation", "Memory validation disabled by config")
            return True
        
        try:
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)
            required_gb = self.config.get('startup_monitoring', {}).get('required_memory_gb', 2.0)
            
            if available_gb < required_gb:
                self.log_event("memory_validation", 
                             f"Insufficient memory: {available_gb:.1f}GB < {required_gb}GB", 
                             False,
                             available_gb=available_gb,
                             required_gb=required_gb,
                             total_gb=memory.total / (1024**3),
                             percent_used=memory.percent)
                return False
            
            self.log_event("memory_validation", 
                         f"Memory available: {available_gb:.1f}GB", 
                         True,
                         available_gb=available_gb,
                         percent_available=100 - memory.percent)
            return True
            
        except Exception as e:
            self.log_event("memory_validation", f"Memory check failed: {e}", False, error=str(e))
            return False
    
    def validate_network(self) -> bool:
        """Check network connectivity to Tradovate"""
        validation_config = self.config.get('startup_monitoring', {}).get('validation_checks', {})
        if not validation_config.get('network', True):
            self.log_event("network_validation", "Network validation disabled by config")
            return True
        
        try:
            test_url = self.config.get('startup_monitoring', {}).get('network_test_url', 'https://trader.tradovate.com')
            timeout = self.config.get('startup_monitoring', {}).get('network_timeout_seconds', 10)
            
            start_time = time.time()
            response = requests.get(test_url, timeout=timeout)
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            if response.status_code == 200:
                self.log_event("network_validation", 
                             "Tradovate accessible", 
                             True,
                             url=test_url,
                             status_code=response.status_code,
                             response_time_ms=response_time)
                return True
            else:
                self.log_event("network_validation", 
                             f"Tradovate returned {response.status_code}", 
                             False,
                             url=test_url,
                             status_code=response.status_code)
                return False
                
        except requests.exceptions.Timeout:
            self.log_event("network_validation", 
                         f"Network timeout after {timeout}s", 
                         False,
                         error="timeout")
            return False
        except Exception as e:
            self.log_event("network_validation", 
                         f"Network check failed: {e}", 
                         False,
                         error=str(e))
            return False
    
    def validate_chrome_executable(self) -> bool:
        """Check if Chrome executable exists and is accessible"""
        validation_config = self.config.get('startup_monitoring', {}).get('validation_checks', {})
        if not validation_config.get('chrome_executable', True):
            self.log_event("chrome_validation", "Chrome validation disabled by config")
            return True
        
        try:
            chrome_path = self.chrome_finder.find_chrome()
            
            if chrome_path and os.path.exists(chrome_path):
                # Get Chrome version
                chrome_info = self.chrome_finder.get_chrome_info()
                self.log_event("chrome_validation", 
                             f"Chrome found at {chrome_path}", 
                             True,
                             path=chrome_path,
                             version=chrome_info.get('version', 'Unknown'))
                return True
            else:
                self.log_event("chrome_validation", 
                             "Chrome executable not found", 
                             False)
                return False
                
        except Exception as e:
            self.log_event("chrome_validation", 
                         f"Chrome validation failed: {e}", 
                         False,
                         error=str(e))
            return False
    
    def validate_chrome_processes(self) -> bool:
        """Check if Chrome processes are running correctly on required ports"""
        validation_config = self.config.get('startup_monitoring', {}).get('validation_checks', {})
        if not validation_config.get('chrome_processes', True):
            self.log_event("chrome_process_validation", "Chrome process validation disabled by config")
            return True
        
        try:
            running_processes = []
            
            for port in self.required_ports:
                # Check if a Chrome process is listening on the port
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                            cmdline = ' '.join(proc.info['cmdline'] or [])
                            if f'--remote-debugging-port={port}' in cmdline:
                                # Verify the process is actually listening on the port
                                for conn in proc.connections(kind='inet'):
                                    if conn.laddr.port == port and conn.status == 'LISTEN':
                                        running_processes.append({
                                            'port': port,
                                            'pid': proc.info['pid'],
                                            'status': 'running'
                                        })
                                        break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            
            if len(running_processes) == len(self.required_ports):
                self.log_event("chrome_process_validation", 
                             f"All {len(self.required_ports)} Chrome processes running", 
                             True,
                             processes=running_processes)
                return True
            else:
                missing_ports = [port for port in self.required_ports 
                               if not any(p['port'] == port for p in running_processes)]
                self.log_event("chrome_process_validation", 
                             f"Missing Chrome processes on ports: {missing_ports}", 
                             False,
                             running_processes=running_processes,
                             missing_ports=missing_ports)
                return False
                
        except Exception as e:
            self.log_event("chrome_process_validation", 
                         f"Chrome process validation failed: {e}", 
                         False,
                         error=str(e))
            return False
    
    def validate_websocket_connections(self) -> bool:
        """Check if WebSocket connections to Chrome instances are working"""
        validation_config = self.config.get('startup_monitoring', {}).get('validation_checks', {})
        if not validation_config.get('websocket_connectivity', True):
            self.log_event("websocket_validation", "WebSocket validation disabled by config")
            return True
        
        try:
            successful_connections = 0
            
            for port in self.required_ports:
                try:
                    # Test basic HTTP connection to Chrome DevTools API
                    response = requests.get(f'http://localhost:{port}/json', timeout=5)
                    
                    if response.status_code == 200:
                        data = response.json()
                        # Check if we get a list of tabs/targets
                        if isinstance(data, list) and len(data) > 0:
                            self.log_event("websocket_validation", 
                                         f"Chrome DevTools API accessible on port {port}", 
                                         True,
                                         port=port,
                                         targets_found=len(data))
                            successful_connections += 1
                        else:
                            self.log_event("websocket_validation", 
                                         f"Chrome DevTools API returned empty response on port {port}", 
                                         False,
                                         port=port)
                    else:
                        self.log_event("websocket_validation", 
                                     f"Chrome DevTools API returned status {response.status_code} on port {port}", 
                                     False,
                                     port=port,
                                     status_code=response.status_code)
                        
                except requests.exceptions.ConnectionError:
                    self.log_event("websocket_validation", 
                                 f"Cannot connect to Chrome DevTools API on port {port}", 
                                 False,
                                 port=port,
                                 error="connection_refused")
                except requests.exceptions.Timeout:
                    self.log_event("websocket_validation", 
                                 f"Timeout connecting to Chrome DevTools API on port {port}", 
                                 False,
                                 port=port,
                                 error="timeout")
                except Exception as e:
                    self.log_event("websocket_validation", 
                                 f"Error testing Chrome DevTools API on port {port}: {e}", 
                                 False,
                                 port=port,
                                 error=str(e))
            
            if successful_connections == len(self.required_ports):
                self.log_event("websocket_validation", 
                             f"All {len(self.required_ports)} WebSocket connections successful", 
                             True,
                             successful_connections=successful_connections)
                return True
            else:
                self.log_event("websocket_validation", 
                             f"Only {successful_connections}/{len(self.required_ports)} WebSocket connections successful", 
                             False,
                             successful_connections=successful_connections,
                             required_connections=len(self.required_ports))
                return False
                
        except Exception as e:
            self.log_event("websocket_validation", 
                         f"WebSocket validation failed: {e}", 
                         False,
                         error=str(e))
            return False
    
    def validate_startup_prerequisites(self) -> bool:
        """Run all prerequisite validations"""
        validations = [
            ("ports", self.validate_ports),
            ("memory", self.validate_memory),
            ("network", self.validate_network),
            ("chrome_executable", self.validate_chrome_executable)
        ]
        
        with self.startup_phase("prerequisite_validation"):
            for name, validation_func in validations:
                if not validation_func():
                    self.log_event("prerequisite_failed", 
                                 f"{name} validation failed", 
                                 False,
                                 validation_name=name)
                    return False
            
            self.log_event("prerequisites_ok", "All prerequisite validations passed", True)
            return True
    
    def validate_startup_completion(self) -> bool:
        """Run post-startup validations to ensure everything is working"""
        validations = [
            ("chrome_processes", self.validate_chrome_processes),
            ("websocket_connections", self.validate_websocket_connections)
        ]
        
        with self.startup_phase("startup_completion_validation"):
            for name, validation_func in validations:
                if not validation_func():
                    self.log_event("completion_validation_failed", 
                                 f"{name} validation failed", 
                                 False,
                                 validation_name=name)
                    return False
            
            self.log_event("startup_completion_ok", "All startup completion validations passed", True)
            return True
    
    def cleanup_failed_startup(self):
        """Clean up any partially started Chrome instances"""
        if not self.config.get('startup_monitoring', {}).get('cleanup_on_failure', True):
            self.log_event("cleanup_skipped", "Cleanup disabled by configuration")
            return
        
        with self.startup_phase("cleanup"):
            try:
                # Clean up Chrome processes on our ports
                results = self.chrome_cleanup.perform_cleanup(
                    kill_processes=True,
                    clean_profiles=True,
                    clean_locks=True
                )
                
                self.log_event("cleanup_complete", 
                             "Cleanup completed",
                             processes_killed=results['processes_killed'],
                             profiles_cleaned=results['profiles_cleaned'],
                             locks_cleaned=results['locks_cleaned'])
                
            except Exception as e:
                self.log_event("cleanup_failed", f"Cleanup failed: {e}", False, error=str(e))
    
    def register_accounts_for_monitoring(self):
        """Register accounts with process monitor for startup monitoring"""
        if not self.process_monitor:
            self.log_event("monitor_registration", "Process monitor not available", success=False)
            return
        
        accounts = [
            ("Account 1", 9224),
            ("Account 2", 9223)
        ]
        
        for account_name, port in accounts:
            success = self.process_monitor.register_for_startup_monitoring(account_name, port)
            self.log_event("monitor_registration", 
                         f"Registered {account_name} for monitoring",
                         success=success,
                         account=account_name,
                         port=port)
    
    def start_with_retry(self):
        """Start auto-login with comprehensive retry logic"""
        self.startup_stats['start_time'] = datetime.now()
        self.log_event("startup_begin", f"Starting with max {self.max_retries} retries")
        
        # Register accounts for monitoring
        self.register_accounts_for_monitoring()
        
        for attempt in range(self.max_retries):
            self.startup_stats['attempts'] = attempt + 1
            
            try:
                with self.startup_phase(f"attempt_{attempt + 1}"):
                    # Phase 1: Validate prerequisites
                    if not self.validate_startup_prerequisites():
                        raise StartupValidationError("Prerequisite validation failed")
                    
                    # Phase 2: Start auto-login
                    self.log_event("auto_login_start", "Starting auto-login process")
                    
                    # Import and run auto-login
                    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                    from src.auto_login import main as auto_login_main
                    result = auto_login_main()
                    
                    # Phase 3: Validate Chrome instances and connections
                    self.log_event("chrome_startup_validation", "Validating Chrome startup completion")
                    time.sleep(10)  # Give Chrome time to fully start and initialize
                    
                    # Run comprehensive startup completion validation
                    if not self.validate_startup_completion():
                        raise StartupValidationError("Chrome startup completion validation failed")
                    
                    # If we get here, startup succeeded
                    self.startup_stats['success'] = True
                    self.startup_stats['end_time'] = datetime.now()
                    duration = (self.startup_stats['end_time'] - self.startup_stats['start_time']).total_seconds()
                    
                    self.log_event("startup_success", 
                                 f"Startup completed on attempt {attempt + 1}",
                                 attempt=attempt + 1,
                                 total_duration_seconds=duration)
                    
                    return result
                    
            except Exception as e:
                is_final_attempt = (attempt == self.max_retries - 1)
                self.handle_startup_failure(e, attempt + 1, is_final_attempt)
                
                if is_final_attempt:
                    self.startup_stats['end_time'] = datetime.now()
                    self.log_event("startup_failed", 
                                 f"All {self.max_retries} attempts failed",
                                 False,
                                 total_attempts=self.max_retries,
                                 last_error=str(e))
                    raise StartupValidationError(
                        f"Startup failed after {self.max_retries} attempts. Last error: {e}"
                    )
    
    def handle_startup_failure(self, error: Exception, attempt: int, is_final: bool):
        """Handle startup failure with cleanup and retry logic"""
        self.log_event("attempt_failed", 
                     f"Attempt {attempt} failed: {error}", 
                     False,
                     attempt=attempt,
                     error=str(error),
                     error_type=type(error).__name__)
        
        # Cleanup any partial Chrome instances
        self.cleanup_failed_startup()
        
        if not is_final:
            self.log_event("retry_wait", 
                         f"Waiting {self.retry_delay}s before retry",
                         delay_seconds=self.retry_delay)
            time.sleep(self.retry_delay)
    
    def get_startup_report(self) -> dict:
        """Get detailed startup report for debugging"""
        return {
            'stats': self.startup_stats,
            'total_events': len(self.startup_log),
            'success_events': len([e for e in self.startup_log if e['success']]),
            'failure_events': len([e for e in self.startup_log if not e['success']]),
            'events': self.startup_log,
            'config': self.config.get('startup_monitoring', {})
        }
    
    def save_startup_report(self, filename: Optional[str] = None):
        """Save startup report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs/startup/startup_report_{timestamp}.json"
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        report = self.get_startup_report()
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info("Startup report saved", filename=filename)
        return filename


def test_startup_manager():
    """Test the startup manager functionality"""
    print("🧪 Testing Enhanced Startup Manager\n")
    
    manager = StartupManager()
    
    # Test prerequisite validation
    print("1. Testing prerequisite validation...")
    prereq_result = manager.validate_startup_prerequisites()
    print(f"   Prerequisites: {'✅ PASSED' if prereq_result else '❌ FAILED'}")
    
    # Show configuration
    print("\n2. Configuration loaded:")
    config = manager.config.get('startup_monitoring', {})
    print(f"   Max retries: {config.get('max_retries', 'Not set')}")
    print(f"   Retry delay: {config.get('retry_delay_seconds', 'Not set')}s")
    print(f"   Startup timeout: {config.get('startup_timeout_seconds', 'Not set')}s")
    
    # Get startup report
    print("\n3. Startup events logged:")
    report = manager.get_startup_report()
    for event in manager.startup_log[-5:]:  # Show last 5 events
        status = "✓" if event['success'] else "✗"
        print(f"   {status} {event['event']}: {event.get('details', '')}")
    
    print("\n✅ Test completed")


if __name__ == "__main__":
    test_startup_manager()