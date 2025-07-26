#!/usr/bin/env python3
"""
Pre-Implementation Validation Script
Ensures everything is ready before implementing Chrome restart logic
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Import our utility modules
from verify_environment import EnvironmentVerifier
from backup_manager import BackupManager
from chrome_cleanup import ChromeCleanup
from chrome_path_finder import get_chrome_finder
from structured_logger import get_logger


class PreImplementationValidator:
    """Validates system readiness for implementation"""
    
    def __init__(self):
        self.logger = get_logger("pre_implementation", log_file="validation/pre_implementation.log")
        self.checks_passed = []
        self.checks_failed = []
        self.checks_warning = []
        
    def log_check(self, check_name: str, passed: bool, message: str, is_warning: bool = False):
        """Log check result"""
        if passed:
            self.checks_passed.append((check_name, message))
            self.logger.info(f"Check passed: {check_name}", check=check_name, result="passed")
        elif is_warning:
            self.checks_warning.append((check_name, message))
            self.logger.warning(f"Check warning: {check_name} - {message}", check=check_name, result="warning")
        else:
            self.checks_failed.append((check_name, message))
            self.logger.error(f"Check failed: {check_name} - {message}", check=check_name, result="failed")
    
    def check_environment(self) -> bool:
        """Run environment verification"""
        print("\n🔍 Checking environment...")
        verifier = EnvironmentVerifier()
        
        # Run checks silently
        import io
        from contextlib import redirect_stdout
        
        f = io.StringIO()
        with redirect_stdout(f):
            result = verifier.run_all_checks()
        
        if result:
            self.log_check("environment", True, "All environment checks passed")
        else:
            errors = "\n".join(verifier.errors)
            self.log_check("environment", False, f"Environment issues: {errors}")
        
        return result
    
    def check_backups(self) -> bool:
        """Verify backup system is working"""
        print("\n💾 Checking backup system...")
        try:
            manager = BackupManager()
            backups = manager.list_backups()
            
            if backups:
                latest_backup = backups[-1]
                backup_age = datetime.now() - datetime.strptime(latest_backup['timestamp'], "%Y%m%d_%H%M%S")
                
                if backup_age.total_seconds() < 3600:  # Less than 1 hour old
                    self.log_check("backups", True, f"Recent backup found: {latest_backup['id']}")
                    return True
                else:
                    self.log_check("backups", False, f"Latest backup is {backup_age.total_seconds()/3600:.1f} hours old", is_warning=True)
                    return True  # Warning, not failure
            else:
                self.log_check("backups", False, "No backups found")
                return False
                
        except Exception as e:
            self.log_check("backups", False, f"Backup system error: {e}")
            return False
    
    def check_chrome_processes(self) -> bool:
        """Check for conflicting Chrome processes"""
        print("\n🔍 Checking Chrome processes...")
        try:
            cleanup = ChromeCleanup()
            processes = cleanup.find_chrome_processes()
            
            # Check if any processes are on our target ports
            target_ports = [9223, 9224]
            conflicts = [p for p in processes if p['port'] in target_ports]
            
            if conflicts:
                details = ", ".join([f"PID {p['pid']} on port {p['port']}" for p in conflicts])
                self.log_check("chrome_processes", False, f"Found conflicting processes: {details}", is_warning=True)
                return True  # Warning, not failure
            else:
                self.log_check("chrome_processes", True, "No conflicting Chrome processes")
                return True
                
        except Exception as e:
            self.log_check("chrome_processes", False, f"Process check error: {e}")
            return False
    
    def check_chrome_installation(self) -> bool:
        """Verify Chrome is properly installed"""
        print("\n🌐 Checking Chrome installation...")
        try:
            finder = get_chrome_finder()
            info = finder.get_chrome_info()
            
            if info['found']:
                self.log_check("chrome_installation", True, f"Chrome found: {info.get('version', 'Unknown version')}")
                return True
            else:
                self.log_check("chrome_installation", False, "Chrome not found")
                return False
                
        except Exception as e:
            self.log_check("chrome_installation", False, f"Chrome check error: {e}")
            return False
    
    def check_file_structure(self) -> bool:
        """Verify required files exist"""
        print("\n📁 Checking file structure...")
        required_files = [
            "/Users/Mike/trading/start_all.py",
            "/Users/Mike/trading/src/auto_login.py",
            "/Users/Mike/trading/tradovate_interface/src/utils/process_monitor.py",
            "/Users/Mike/trading/config/connection_health.json"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            self.log_check("file_structure", False, f"Missing files: {', '.join(missing_files)}")
            return False
        else:
            self.log_check("file_structure", True, "All required files exist")
            return True
    
    def check_configuration(self) -> bool:
        """Verify configuration is valid"""
        print("\n⚙️  Checking configuration...")
        try:
            # Check connection_health.json
            config_path = "/Users/Mike/trading/config/connection_health.json"
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Check for required sections
            if 'health_monitoring' in config:
                self.log_check("configuration", True, "Configuration valid")
                return True
            else:
                self.log_check("configuration", False, "Missing health_monitoring section", is_warning=True)
                return True  # Warning, not failure
                
        except Exception as e:
            self.log_check("configuration", False, f"Configuration error: {e}")
            return False
    
    def check_virtual_environment(self) -> bool:
        """Check if running in correct virtual environment"""
        print("\n🐍 Checking virtual environment...")
        
        # Check if we're in a virtual environment
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        
        if in_venv:
            venv_path = sys.prefix
            self.log_check("virtual_environment", True, f"Running in venv: {venv_path}")
            return True
        else:
            # Check if tradovate venv exists
            tradovate_venv = "/Users/Mike/trading/tradovate_interface/venv"
            if os.path.exists(tradovate_venv):
                self.log_check("virtual_environment", False, 
                             f"Not in venv. Activate with: source {tradovate_venv}/bin/activate", 
                             is_warning=True)
                return True  # Warning, not failure
            else:
                self.log_check("virtual_environment", False, "No virtual environment found")
                return False
    
    def run_all_validations(self) -> bool:
        """Run all pre-implementation validations"""
        print("="*60)
        print("🚀 PRE-IMPLEMENTATION VALIDATION")
        print("="*60)
        
        self.logger.info("Starting pre-implementation validation")
        
        checks = [
            ("Environment", self.check_environment),
            ("Backups", self.check_backups),
            ("Chrome Processes", self.check_chrome_processes),
            ("Chrome Installation", self.check_chrome_installation),
            ("File Structure", self.check_file_structure),
            ("Configuration", self.check_configuration),
            ("Virtual Environment", self.check_virtual_environment)
        ]
        
        all_passed = True
        for check_name, check_func in checks:
            try:
                if not check_func():
                    all_passed = False
            except Exception as e:
                self.log_check(check_name.lower(), False, f"Unexpected error: {e}")
                all_passed = False
        
        # Print summary
        print("\n" + "="*60)
        print("📊 VALIDATION SUMMARY")
        print("="*60)
        
        if self.checks_passed:
            print(f"\n✅ PASSED ({len(self.checks_passed)}):")
            for check, message in self.checks_passed:
                print(f"   {check}: {message}")
        
        if self.checks_warning:
            print(f"\n⚠️  WARNINGS ({len(self.checks_warning)}):")
            for check, message in self.checks_warning:
                print(f"   {check}: {message}")
        
        if self.checks_failed:
            print(f"\n❌ FAILED ({len(self.checks_failed)}):")
            for check, message in self.checks_failed:
                print(f"   {check}: {message}")
        
        print("\n" + "="*60)
        
        if self.checks_failed:
            print("❌ VALIDATION FAILED - Fix errors before proceeding")
            self.logger.error("Pre-implementation validation failed", 
                            passed=len(self.checks_passed),
                            warnings=len(self.checks_warning),
                            failed=len(self.checks_failed))
            return False
        else:
            print("✅ VALIDATION PASSED - Ready to implement!")
            if self.checks_warning:
                print(f"   ({len(self.checks_warning)} warnings - review before proceeding)")
            
            self.logger.info("Pre-implementation validation passed",
                           passed=len(self.checks_passed),
                           warnings=len(self.checks_warning))
            return True
    
    def generate_report(self, filename: str = "pre_implementation_report.json"):
        """Generate detailed validation report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "passed": len(self.checks_passed),
                "warnings": len(self.checks_warning),
                "failed": len(self.checks_failed),
                "ready_to_implement": len(self.checks_failed) == 0
            },
            "checks": {
                "passed": [{"name": c[0], "message": c[1]} for c in self.checks_passed],
                "warnings": [{"name": c[0], "message": c[1]} for c in self.checks_warning],
                "failed": [{"name": c[0], "message": c[1]} for c in self.checks_failed]
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {filename}")


def main():
    """Run pre-implementation validation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Pre-Implementation Validation")
    parser.add_argument('--report', help="Generate detailed report to file")
    parser.add_argument('--fix', action='store_true', help="Attempt to fix issues automatically")
    
    args = parser.parse_args()
    
    validator = PreImplementationValidator()
    result = validator.run_all_validations()
    
    if args.report:
        validator.generate_report(args.report)
    
    if not result and args.fix:
        print("\n🔧 Attempting to fix issues...")
        # Add auto-fix logic here if needed
        print("   Auto-fix not yet implemented")
    
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()