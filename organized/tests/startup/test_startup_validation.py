#!/usr/bin/env python3
"""
Pre-test validation for enhanced startup testing
Ensures clean environment before running start_all.py
"""

import os
import sys
import socket
import psutil
import subprocess
import time
from datetime import datetime
from pathlib import Path

# Add project to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from structured_logger import get_logger
from chrome_cleanup import ChromeCleanup


class StartupTestValidator:
    """Validates test environment before startup testing"""
    
    def __init__(self):
        self.logger = get_logger("test_validator", log_file="test/pre_test_validation.log")
        self.issues = []
        self.warnings = []
        self.test_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def check_ports(self) -> bool:
        """Check if required ports are available"""
        self.logger.info("Checking port availability")
        
        ports_to_check = [9223, 9224, 5000]  # Chrome ports + dashboard
        blocked_ports = []
        
        for port in ports_to_check:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                blocked_ports.append(port)
                # Try to identify what's using it
                try:
                    for proc in psutil.process_iter(['pid', 'name']):
                        # Use net_connections to avoid deprecation warning
                        for conn in proc.net_connections(kind='inet'):
                            if conn.laddr.port == port:
                                process_name = proc.info['name']
                                pid = proc.info['pid']
                                self.logger.warning(f"Port {port} in use", 
                                                  pid=pid, 
                                                  process=process_name)
                                
                                # Special handling for port 5000 on macOS
                                if port == 5000 and process_name == "ControlCenter":
                                    self.warnings.append(f"Port {port} used by macOS {process_name} - dashboard will use alternate port")
                                else:
                                    self.issues.append(f"Port {port} blocked by {process_name} (PID: {pid})")
                                break
                except Exception as e:
                    self.logger.debug(f"Error checking process for port {port}: {e}")
                    if port == 5000:
                        self.warnings.append(f"Port {port} in use - dashboard will use alternate port")
                    else:
                        self.issues.append(f"Port {port} blocked by unknown process")
        
        # Check if any critical ports are blocked (9223, 9224)
        critical_blocked = [p for p in blocked_ports if p in [9223, 9224]]
        
        if critical_blocked:
            self.logger.error("Critical ports blocked", ports=critical_blocked)
            return False
        elif blocked_ports:
            self.logger.warning("Non-critical ports blocked", ports=blocked_ports)
            # Port 5000 is not critical - dashboard can use alternate port
            return True
        else:
            self.logger.info("All ports available")
            return True
    
    def check_virtual_env(self) -> bool:
        """Check if we're in the correct virtual environment"""
        self.logger.info("Checking virtual environment")
        
        # Check if we can import required packages
        try:
            import websocket
            import pychrome
            self.logger.info("Virtual environment packages available")
            return True
        except ImportError as e:
            # Check if venv exists
            venv_path = "/Users/Mike/trading/tradovate_interface/venv"
            if os.path.exists(venv_path):
                self.warnings.append(f"Virtual environment exists but not activated: {venv_path}")
                self.logger.warning("Virtual environment not activated", venv_path=venv_path)
            else:
                self.issues.append(f"Required package missing: {e}")
                self.logger.error("Import failed", error=str(e))
            return False
    
    def check_system_resources(self) -> bool:
        """Check available system resources"""
        self.logger.info("Checking system resources")
        
        # Memory check
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        
        if available_gb < 2.0:
            self.issues.append(f"Low memory: {available_gb:.1f}GB available (need 2GB+)")
            self.logger.error("Insufficient memory", available_gb=available_gb)
            return False
        
        # CPU check
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 90:
            self.warnings.append(f"High CPU usage: {cpu_percent}%")
            self.logger.warning("High CPU usage", cpu_percent=cpu_percent)
        
        self.logger.info("System resources adequate", 
                        memory_gb=available_gb, 
                        cpu_percent=cpu_percent)
        return True
    
    def check_log_directories(self) -> bool:
        """Ensure log directories exist and are writable"""
        self.logger.info("Checking log directories")
        
        log_dirs = [
            "logs/startup",
            "logs/test",
            "logs/operations",
            "logs/chrome_cleanup",
            "logs/deployment"
        ]
        
        for log_dir in log_dirs:
            try:
                os.makedirs(log_dir, exist_ok=True)
                # Test write permission
                test_file = os.path.join(log_dir, ".test_write")
                Path(test_file).touch()
                os.remove(test_file)
            except Exception as e:
                self.issues.append(f"Cannot write to {log_dir}: {e}")
                self.logger.error("Log directory not writable", directory=log_dir, error=str(e))
                return False
        
        self.logger.info("All log directories ready")
        return True
    
    def check_chrome_executable(self) -> bool:
        """Verify Chrome is installed and accessible"""
        self.logger.info("Checking Chrome installation")
        
        from chrome_path_finder import get_chrome_finder
        finder = get_chrome_finder()
        chrome_info = finder.get_chrome_info()
        
        if not chrome_info['found']:
            self.issues.append("Chrome browser not found")
            self.logger.error("Chrome not found")
            return False
        
        self.logger.info("Chrome found", 
                        path=chrome_info['path'],
                        version=chrome_info.get('version', 'Unknown'))
        return True
    
    def check_startup_files(self) -> bool:
        """Verify all required startup files exist"""
        self.logger.info("Checking startup files")
        
        required_files = [
            "start_all.py",
            "src/auto_login.py",
            "src/dashboard.py",
            "enhanced_startup_manager.py",
            "structured_logger.py",
            "chrome_cleanup.py"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
                self.issues.append(f"Missing required file: {file_path}")
        
        if missing_files:
            self.logger.error("Required files missing", files=missing_files)
            return False
        
        self.logger.info("All required files present")
        return True
    
    def cleanup_stale_processes(self) -> bool:
        """Clean up any stale Chrome processes from previous tests"""
        self.logger.info("Cleaning up stale processes")
        
        cleanup = ChromeCleanup()
        
        # Find Chrome processes on our ports (not 9222)
        processes = cleanup.find_chrome_processes()
        
        if processes:
            self.warnings.append(f"Found {len(processes)} stale Chrome processes")
            self.logger.warning("Stale processes found", count=len(processes))
            
            # Ask for cleanup
            print(f"\n⚠️  Found {len(processes)} Chrome processes on test ports")
            response = input("Clean them up before testing? (y/n): ")
            
            if response.lower() == 'y':
                results = cleanup.perform_cleanup(
                    kill_processes=True,
                    clean_profiles=False,
                    clean_locks=True
                )
                self.logger.info("Cleanup completed", results=results)
                return True
            else:
                self.warnings.append("Stale processes not cleaned - may cause conflicts")
                return True
        
        self.logger.info("No stale processes found")
        return True
    
    def run_validation(self) -> bool:
        """Run all validation checks"""
        print("\n" + "="*60)
        print("🔍 PRE-TEST VALIDATION")
        print("="*60)
        
        self.logger.info("Starting pre-test validation", timestamp=self.test_timestamp)
        
        validations = [
            ("Port Availability", self.check_ports),
            ("Virtual Environment", self.check_virtual_env),
            ("System Resources", self.check_system_resources),
            ("Log Directories", self.check_log_directories),
            ("Chrome Installation", self.check_chrome_executable),
            ("Startup Files", self.check_startup_files),
            ("Stale Process Cleanup", self.cleanup_stale_processes)
        ]
        
        all_passed = True
        
        for name, check_func in validations:
            print(f"\n📋 {name}...", end='', flush=True)
            try:
                result = check_func()
                if result:
                    print(" ✅")
                else:
                    print(" ❌")
                    all_passed = False
            except Exception as e:
                print(f" ❌ ({e})")
                self.logger.exception(f"Validation failed: {name}")
                self.issues.append(f"{name} check failed: {e}")
                all_passed = False
        
        # Summary
        print("\n" + "="*60)
        print("📊 VALIDATION SUMMARY")
        print("="*60)
        
        if self.issues:
            print("\n❌ Critical Issues:")
            for issue in self.issues:
                print(f"   - {issue}")
        
        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"   - {warning}")
        
        if all_passed and not self.issues:
            print("\n✅ Environment ready for testing!")
            self.logger.info("Pre-test validation passed", 
                           warnings=len(self.warnings),
                           test_id=self.test_timestamp)
        else:
            print("\n❌ Environment not ready - fix issues before testing")
            self.logger.error("Pre-test validation failed", 
                            issues=len(self.issues),
                            warnings=len(self.warnings))
        
        print(f"\n📄 Detailed log: logs/test/pre_test_validation.log")
        
        return all_passed and not self.issues
    
    def save_validation_report(self):
        """Save validation report for test records"""
        report = {
            "timestamp": self.test_timestamp,
            "validation_time": datetime.now().isoformat(),
            "passed": len(self.issues) == 0,
            "issues": self.issues,
            "warnings": self.warnings,
            "environment": {
                "python_version": sys.version,
                "platform": sys.platform,
                "memory_available_gb": psutil.virtual_memory().available / (1024**3),
                "cpu_count": psutil.cpu_count()
            }
        }
        
        report_file = f"logs/test/validation_report_{self.test_timestamp}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        import json
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info("Validation report saved", report_file=report_file)
        return report_file


def main():
    """Run pre-test validation"""
    validator = StartupTestValidator()
    
    if validator.run_validation():
        validator.save_validation_report()
        print("\n✅ Ready to run: python3 start_all.py")
        return 0
    else:
        validator.save_validation_report()
        print("\n❌ Fix issues before running tests")
        return 1


if __name__ == "__main__":
    sys.exit(main())