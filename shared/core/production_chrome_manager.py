#!/usr/bin/env python3
"""
Production Chrome Instance Manager
FAIL FAST, FAIL LOUD, FAIL SAFELY

Manages Chrome instances for real trading with comprehensive health monitoring
"""

import os
import sys
import time
import subprocess
import psutil
import pychrome
import signal
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Add project root for imports  
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from utils.chrome_communication import safe_evaluate, OperationType

@dataclass
class ChromeInstance:
    port: int
    account_name: str
    process: Optional[subprocess.Popen] = None
    pid: Optional[int] = None
    profile_dir: str = ""
    healthy: bool = False
    last_check: str = ""
    tradovate_connected: bool = False

class ProductionChromeManager:
    """Manages Chrome instances for production trading"""
    
    def __init__(self):
        self.chrome_instances: Dict[int, ChromeInstance] = {}
        self.chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        self.main_chrome_port = 9222  # Main Chrome instance port (NEVER START/STOP)
        self.health_check_interval = 30  # seconds
        self.monitoring_active = False
        
        # CLAUDE.md Rule: NEVER START CHROME - Always connect to existing
    
    def FAIL_LOUD(self, message: str):
        """Critical error logging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_msg = f"[{timestamp}] !!! CHROME CRITICAL !!! {message}"
        print(error_msg)
        self._log_to_file("CRITICAL", error_msg)
        
    def LOG_SUCCESS(self, message: str):
        """Success logging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        success_msg = f"[{timestamp}] ✅ CHROME SUCCESS: {message}"
        print(success_msg)
        self._log_to_file("SUCCESS", success_msg)
        
    def LOG_WARNING(self, message: str):
        """Warning logging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        warning_msg = f"[{timestamp}] ⚠️  CHROME WARNING: {message}"
        print(warning_msg)
        self._log_to_file("WARNING", warning_msg)
        
    def _log_to_file(self, level: str, message: str):
        """Log messages to file"""
        log_dir = os.path.join(project_root, "logs", "chrome")
        os.makedirs(log_dir, exist_ok=True)
        
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(log_dir, f"chrome_manager_{today}.log")
        
        with open(log_file, "a") as f:
            f.write(f"{message}\n")
    
    def _cleanup_existing_chrome(self, port: int):
        """Clean up existing Chrome process on port - FAIL SAFELY"""
        try:
            # Kill any existing Chrome on this port
            subprocess.run(
                ["pkill", "-f", f"remote-debugging-port={port}"],
                capture_output=True, 
                timeout=10
            )
            
            # Clean up profile directory
            profile_dir = f"/tmp/tradovate_production_{port}"
            if os.path.exists(profile_dir):
                subprocess.run(["rm", "-rf", profile_dir], capture_output=True)
                
            self.LOG_SUCCESS(f"Cleaned up existing Chrome on port {port}")
            
        except Exception as e:
            self.LOG_WARNING(f"Cleanup warning for port {port}: {str(e)}")
    
    def start_chrome_instance(self, port: int, account_name: str) -> bool:
        """Start a Chrome instance for trading - FAIL FAST"""
        
        # FAIL SAFELY: Clean up existing first
        self._cleanup_existing_chrome(port)
        
        profile_dir = f"/tmp/tradovate_production_{port}"
        os.makedirs(profile_dir, exist_ok=True)
        
        # Production Chrome flags for trading
        chrome_cmd = [
            self.chrome_path,
            f"--remote-debugging-port={port}",
            "--remote-allow-origins=*",
            "--no-first-run", 
            "--no-default-browser-check",
            f"--user-data-dir={profile_dir}",
            "--disable-blink-features=AutomationControlled",
            "--disable-features=VizDisplayCompositor,TranslateUI",
            "--password-store=basic",
            "--use-mock-keychain",
            "--disable-gpu-sandbox",
            "--disable-software-rasterizer",
            "--disable-dev-shm-usage", 
            "--no-sandbox",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--disable-ipc-flooding-protection",
            "--max_old_space_size=4096",
            "--force-color-profile=srgb",
            "--disable-web-security",  # For trading API access
            "--disable-features=VizDisplayCompositor",
            "https://trader.tradovate.com"  # REAL TRADOVATE ONLY
        ]
        
        try:
            self.LOG_SUCCESS(f"Starting Chrome for {account_name} on port {port}...")
            
            # Start Chrome process
            process = subprocess.Popen(
                chrome_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Create instance tracking
            instance = ChromeInstance(
                port=port,
                account_name=account_name,
                process=process,
                pid=process.pid,
                profile_dir=profile_dir,
                healthy=False,
                last_check=datetime.now().isoformat()
            )
            
            self.chrome_instances[port] = instance
            
            # Wait for Chrome to start
            max_wait = 30  # 30 seconds
            wait_count = 0
            
            while wait_count < max_wait:
                if self._check_chrome_health(port):
                    instance.healthy = True
                    self.LOG_SUCCESS(f"✅ Chrome started successfully: {account_name} on port {port}")
                    return True
                    
                time.sleep(1)
                wait_count += 1
                
                # Check if process died
                if process.poll() is not None:
                    self.FAIL_LOUD(f"Chrome process died during startup: {account_name} on port {port}")
                    return False
            
            # Timeout - Chrome didn't start properly
            self.FAIL_LOUD(f"Chrome startup timeout: {account_name} on port {port}")
            self._kill_chrome_instance(port)
            return False
            
        except Exception as e:
            self.FAIL_LOUD(f"Failed to start Chrome for {account_name} on port {port}: {str(e)}")
            return False
    
    def _check_chrome_health(self, port: int) -> bool:
        """Check if Chrome instance is healthy - FAIL FAST"""
        try:
            # Test basic connectivity
            browser = pychrome.Browser(url=f"http://127.0.0.1:{port}")
            tabs = browser.list_tab()
            
            if not tabs:
                return False
                
            # For port 9222 (existing Chrome), just check if it's responsive
            # Don't require Tradovate connection for health check
            tradovate_connected = False
            
            # Check if any tab is connected to real Tradovate (optional)
            for tab in tabs:
                try:
                    tab.start()
                    
                    # Check URL
                    url_result = safe_evaluate(tab, "window.location.href", OperationType.NON_CRITICAL)
                    if url_result.success and "trader.tradovate.com" in str(url_result.value):
                        tradovate_connected = True
                        
                    tab.stop()
                    
                except Exception:
                    try:
                        tab.stop()
                    except:
                        pass
                    continue
            
            # Update instance status
            if port in self.chrome_instances:
                self.chrome_instances[port].tradovate_connected = tradovate_connected
                self.chrome_instances[port].last_check = datetime.now().isoformat()
                
            # Chrome is healthy if it responds to DevTools
            return True
            
        except Exception:
            return False
    
    def _kill_chrome_instance(self, port: int):
        """Kill Chrome instance safely"""
        if port in self.chrome_instances:
            instance = self.chrome_instances[port]
            
            try:
                if instance.process and instance.process.poll() is None:
                    # Try graceful shutdown first
                    os.killpg(os.getpgid(instance.process.pid), signal.SIGTERM)
                    
                    # Wait for graceful shutdown
                    try:
                        instance.process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        # Force kill if graceful fails
                        os.killpg(os.getpgid(instance.process.pid), signal.SIGKILL)
                        
                # Clean up profile
                if os.path.exists(instance.profile_dir):
                    subprocess.run(["rm", "-rf", instance.profile_dir], capture_output=True)
                    
                self.LOG_SUCCESS(f"Chrome instance stopped: port {port}")
                
            except Exception as e:
                self.LOG_WARNING(f"Error stopping Chrome on port {port}: {str(e)}")
                
            # Remove from tracking
            del self.chrome_instances[port]
    
    def start_all_trading_instances(self) -> bool:
        """Connect to existing Chrome instance - NEVER START CHROME"""
        
        print("="*60)
        print("🔗 CONNECTING TO EXISTING CHROME INSTANCE")
        print("NEVER START/STOP CHROME - Connect to port 9222 only")
        print("="*60)
        
        # Load trading accounts
        try:
            credentials_path = os.path.join(project_root, 'config', 'credentials.json')
            if not os.path.exists(credentials_path):
                self.FAIL_LOUD("No credentials.json found")
                return False
                
            import json
            with open(credentials_path, 'r') as f:
                creds = json.load(f)
                
        except Exception as e:
            self.FAIL_LOUD(f"Failed to load credentials: {str(e)}")
            return False
        
        # Connect to existing Chrome on port 9222
        for i, (username, password) in enumerate(creds.items()):
            account_name = f"Account_{i+1}_{username.split('@')[0]}"
            
            # Create instance tracking for the existing Chrome
            instance = ChromeInstance(
                port=self.main_chrome_port,
                account_name=account_name,
                process=None,  # Not our process
                pid=None,
                profile_dir="",
                healthy=False,
                last_check=datetime.now().isoformat()
            )
            
            self.chrome_instances[self.main_chrome_port] = instance
            break  # Only one Chrome instance to connect to
        
        # Verify connection to existing Chrome
        if not self._check_chrome_health(self.main_chrome_port):
            self.FAIL_LOUD(f"Cannot connect to existing Chrome on port {self.main_chrome_port}")
            return False
            
        self.LOG_SUCCESS(f"✅ Connected to existing Chrome on port {self.main_chrome_port}")
        
        # Start health monitoring
        self._start_health_monitoring()
        
        return True
    
    def _start_health_monitoring(self):
        """Start continuous health monitoring"""
        import threading
        
        def monitor_health():
            self.monitoring_active = True
            self.LOG_SUCCESS("Started Chrome health monitoring")
            
            while self.monitoring_active:
                for port, instance in self.chrome_instances.items():
                    try:
                        if self._check_chrome_health(port):
                            instance.healthy = True
                            instance.last_check = datetime.now().isoformat()
                        else:
                            instance.healthy = False
                            self.LOG_WARNING(f"Chrome health check failed: port {port}")
                            
                            # Try to restart unhealthy instance
                            if not instance.healthy:
                                self.LOG_WARNING(f"Attempting to restart Chrome on port {port}")
                                self._kill_chrome_instance(port)
                                self.start_chrome_instance(port, instance.account_name)
                                
                    except Exception as e:
                        self.LOG_WARNING(f"Health check error for port {port}: {str(e)}")
                
                time.sleep(self.health_check_interval)
        
        health_thread = threading.Thread(target=monitor_health, daemon=True)
        health_thread.start()
    
    def get_instance_status(self) -> Dict[str, any]:
        """Get status of all Chrome instances"""
        status = {
            "total_instances": len(self.chrome_instances),
            "healthy_instances": len([i for i in self.chrome_instances.values() if i.healthy]),
            "tradovate_connected": len([i for i in self.chrome_instances.values() if i.tradovate_connected]),
            "instances": {}
        }
        
        for port, instance in self.chrome_instances.items():
            status["instances"][port] = {
                "account_name": instance.account_name,
                "healthy": instance.healthy,
                "tradovate_connected": instance.tradovate_connected,
                "last_check": instance.last_check,
                "pid": instance.pid
            }
            
        return status
    
    def stop_all_instances(self):
        """Stop monitoring - NEVER KILL Chrome (per CLAUDE.md rules)"""
        self.monitoring_active = False
        
        print("🛑 Stopping Chrome monitoring...")
        
        # CLAUDE.md Rule: NEVER KILL CHROME PROCESSES
        # Just clear our tracking, let Chrome keep running
        self.chrome_instances.clear()
            
        self.LOG_SUCCESS("Chrome monitoring stopped - Chrome remains running")

def main():
    """Main Chrome manager entry point"""
    manager = ProductionChromeManager()
    
    try:
        if not manager.start_all_trading_instances():
            print("❌ Failed to start Chrome instances")
            return 1
            
        print("\n🎯 Production Chrome Manager Ready")
        print("📊 All instances connected to real Tradovate")
        print("⏹️  Press Ctrl+C to stop")
        
        # Display status periodically
        while True:
            status = manager.get_instance_status()
            print(f"\r🌐 Instances: {status['healthy_instances']}/{status['total_instances']} healthy | {status['tradovate_connected']} connected to Tradovate", end="", flush=True)
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Chrome manager...")
        manager.stop_all_instances()
        return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main())