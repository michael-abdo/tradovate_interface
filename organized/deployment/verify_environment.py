#!/usr/bin/env python3
"""
Environment Verification Script for Chrome Restart Implementation
Checks all dependencies and prerequisites before implementation
"""

import sys
import os
import subprocess
import json
from pathlib import Path


class EnvironmentVerifier:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
        
    def check_python_version(self):
        """Verify Python version is 3.7+"""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 7):
            self.errors.append(f"Python 3.7+ required. Found: {version.major}.{version.minor}.{version.micro}")
        else:
            self.info.append(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")
    
    def check_required_packages(self):
        """Check if required Python packages are installed"""
        required_packages = {
            'psutil': 'Process and system monitoring',
            'requests': 'HTTP requests for network validation',
            'pychrome': 'Chrome DevTools Protocol client',
            'websocket-client': 'WebSocket connections'
        }
        
        for package, description in required_packages.items():
            try:
                __import__(package.replace('-', '_'))
                self.info.append(f"✓ {package}: {description}")
            except ImportError:
                self.errors.append(f"✗ Missing package '{package}': {description}")
    
    def check_chrome_installation(self):
        """Verify Chrome is installed and accessible"""
        chrome_paths = [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '/usr/bin/google-chrome',
            '/usr/bin/chromium',
            '/usr/bin/chromium-browser'
        ]
        
        chrome_found = False
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_found = True
                self.info.append(f"✓ Chrome found at: {path}")
                
                # Check Chrome version
                try:
                    result = subprocess.run([path, '--version'], capture_output=True, text=True)
                    if result.returncode == 0:
                        self.info.append(f"  Version: {result.stdout.strip()}")
                except Exception as e:
                    self.warnings.append(f"  Could not determine Chrome version: {e}")
                break
        
        if not chrome_found:
            self.errors.append("✗ Chrome browser not found in standard locations")
    
    def check_file_permissions(self):
        """Verify we have necessary file permissions"""
        test_locations = [
            '/Users/Mike/trading/',
            '/Users/Mike/trading/src/',
            '/Users/Mike/trading/config/',
            '/Users/Mike/trading/logs/'
        ]
        
        for location in test_locations:
            if os.path.exists(location):
                if os.access(location, os.W_OK):
                    self.info.append(f"✓ Write permission: {location}")
                else:
                    self.errors.append(f"✗ No write permission: {location}")
            else:
                self.warnings.append(f"⚠ Directory not found: {location}")
    
    def check_port_availability(self):
        """Check if required ports are available"""
        import socket
        
        ports_to_check = [9223, 9224]
        for port in ports_to_check:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                self.warnings.append(f"⚠ Port {port} is already in use")
            else:
                self.info.append(f"✓ Port {port} is available")
    
    def check_existing_chrome_processes(self):
        """Check for existing Chrome processes on debug ports"""
        try:
            import psutil
            chrome_debug_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        if '--remote-debugging-port=' in cmdline:
                            port = cmdline.split('--remote-debugging-port=')[1].split()[0]
                            if port in ['9223', '9224']:
                                chrome_debug_processes.append({
                                    'pid': proc.info['pid'],
                                    'port': port
                                })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if chrome_debug_processes:
                self.warnings.append(f"⚠ Found {len(chrome_debug_processes)} Chrome debug processes:")
                for proc in chrome_debug_processes:
                    self.warnings.append(f"  PID {proc['pid']} on port {proc['port']}")
            else:
                self.info.append("✓ No conflicting Chrome debug processes found")
                
        except ImportError:
            self.warnings.append("⚠ Cannot check Chrome processes (psutil not installed)")
    
    def check_disk_space(self):
        """Check available disk space"""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            available_gb = disk.free / (1024**3)
            
            if available_gb < 1:
                self.errors.append(f"✗ Low disk space: {available_gb:.2f}GB available")
            else:
                self.info.append(f"✓ Disk space: {available_gb:.2f}GB available")
        except ImportError:
            self.warnings.append("⚠ Cannot check disk space (psutil not installed)")
    
    def check_existing_backups(self):
        """Check for existing backup files"""
        backup_files = [
            '/Users/Mike/trading/start_all.py.backup',
            '/Users/Mike/trading/src/auto_login.py.backup',
            '/Users/Mike/trading/tradovate_interface/src/utils/process_monitor.py.backup'
        ]
        
        existing_backups = []
        for backup in backup_files:
            if os.path.exists(backup):
                existing_backups.append(backup)
        
        if existing_backups:
            self.warnings.append(f"⚠ Found {len(existing_backups)} existing backup files:")
            for backup in existing_backups:
                stat = os.stat(backup)
                self.warnings.append(f"  {backup} ({stat.st_size} bytes)")
    
    def check_config_files(self):
        """Verify configuration files exist and are valid JSON"""
        config_files = [
            '/Users/Mike/trading/config/connection_health.json',
            '/Users/Mike/trading/tradovate_interface/config/process_monitor.json'
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        json.load(f)
                    self.info.append(f"✓ Valid config: {config_file}")
                except json.JSONDecodeError as e:
                    self.errors.append(f"✗ Invalid JSON in {config_file}: {e}")
                except Exception as e:
                    self.errors.append(f"✗ Cannot read {config_file}: {e}")
            else:
                self.warnings.append(f"⚠ Config file not found: {config_file}")
    
    def run_all_checks(self):
        """Run all environment checks"""
        print("🔍 Chrome Restart Implementation - Environment Verification\n")
        
        checks = [
            ("Python Version", self.check_python_version),
            ("Required Packages", self.check_required_packages),
            ("Chrome Installation", self.check_chrome_installation),
            ("File Permissions", self.check_file_permissions),
            ("Port Availability", self.check_port_availability),
            ("Chrome Processes", self.check_existing_chrome_processes),
            ("Disk Space", self.check_disk_space),
            ("Existing Backups", self.check_existing_backups),
            ("Configuration Files", self.check_config_files)
        ]
        
        for check_name, check_func in checks:
            print(f"\n📋 Checking {check_name}...")
            try:
                check_func()
            except Exception as e:
                self.errors.append(f"✗ Check '{check_name}' failed: {e}")
        
        # Print results
        print("\n" + "="*60)
        print("📊 VERIFICATION RESULTS")
        print("="*60)
        
        if self.info:
            print("\n✅ PASSED CHECKS:")
            for msg in self.info:
                print(f"  {msg}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for msg in self.warnings:
                print(f"  {msg}")
        
        if self.errors:
            print("\n❌ ERRORS (Must Fix):")
            for msg in self.errors:
                print(f"  {msg}")
        
        print("\n" + "="*60)
        
        if self.errors:
            print("❌ Environment verification FAILED")
            print("Fix the errors above before proceeding with implementation.")
            return False
        elif self.warnings:
            print("⚠️  Environment verification PASSED with warnings")
            print("Review warnings above. Implementation can proceed with caution.")
            return True
        else:
            print("✅ Environment verification PASSED")
            print("All checks passed. Safe to proceed with implementation.")
            return True
    
    def generate_fix_script(self):
        """Generate a script to fix common issues"""
        if not self.errors:
            return
        
        print("\n📝 Generating fix script...")
        
        fix_commands = []
        
        # Check for missing packages
        missing_packages = []
        for error in self.errors:
            if "Missing package" in error:
                package = error.split("'")[1]
                missing_packages.append(package)
        
        if missing_packages:
            fix_commands.append("# Install missing Python packages")
            fix_commands.append(f"pip install {' '.join(missing_packages)}")
        
        # Create missing directories
        for warning in self.warnings:
            if "Directory not found" in warning:
                dir_path = warning.split(": ")[1]
                fix_commands.append(f"mkdir -p {dir_path}")
        
        if fix_commands:
            script_content = "#!/bin/bash\n# Auto-generated fix script\n\n"
            script_content += "\n".join(fix_commands)
            
            with open("fix_environment.sh", "w") as f:
                f.write(script_content)
            
            os.chmod("fix_environment.sh", 0o755)
            print("✓ Created fix_environment.sh")
            print("  Run: ./fix_environment.sh")


if __name__ == "__main__":
    verifier = EnvironmentVerifier()
    success = verifier.run_all_checks()
    
    if not success:
        verifier.generate_fix_script()
        sys.exit(1)
    
    sys.exit(0)