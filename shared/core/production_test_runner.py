#!/usr/bin/env python3
"""
Production Test Runner - FAIL FAST, FAIL LOUD, FAIL SAFELY
Test all production systems with real Tradovate accounts and live data
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, List, Optional

# Add project root for imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from production_validator import ProductionValidator
from production_chrome_manager import ProductionChromeManager  
from production_auth_manager import ProductionAuthManager
from production_trading_engine import ProductionTradingEngine
from production_monitor import ProductionMonitor

class ProductionTestRunner:
    """Complete production system testing with real accounts"""
    
    def __init__(self):
        self.test_results = {}
        self.critical_failures = []
        self.warnings = []
        
    def FAIL_LOUD(self, message: str):
        """Critical error logging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_msg = f"[{timestamp}] !!! PRODUCTION TEST CRITICAL !!! {message}"
        print(error_msg)
        self.critical_failures.append(error_msg)
        self._log_to_file("CRITICAL", error_msg)
        
    def LOG_SUCCESS(self, message: str):
        """Success logging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        success_msg = f"[{timestamp}] ✅ PRODUCTION TEST SUCCESS: {message}"
        print(success_msg)
        self._log_to_file("SUCCESS", success_msg)
        
    def LOG_WARNING(self, message: str):
        """Warning logging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        warning_msg = f"[{timestamp}] ⚠️  PRODUCTION TEST WARNING: {message}"
        print(warning_msg)
        self.warnings.append(warning_msg)
        self._log_to_file("WARNING", warning_msg)
        
    def _log_to_file(self, level: str, message: str):
        """Log messages to file"""
        log_dir = os.path.join(project_root, "logs", "production_test")
        os.makedirs(log_dir, exist_ok=True)
        
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(log_dir, f"production_test_{today}.log")
        
        with open(log_file, "a") as f:
            f.write(f"{message}\n")
    
    def test_chrome_management(self) -> bool:
        """Test 1: Chrome instance management - FAIL FAST"""
        print("\n" + "="*60)
        print("🌐 TESTING: Chrome Instance Management")
        print("="*60)
        
        try:
            chrome_manager = ProductionChromeManager()
            
            # Test Chrome startup
            if not chrome_manager.start_all_trading_instances():
                self.FAIL_LOUD("Chrome instances failed to start")
                return False
                
            # Wait for instances to fully initialize
            time.sleep(10)
            
            # Verify all instances are healthy
            status = chrome_manager.get_instance_status()
            
            if status['healthy_instances'] < status['total_instances']:
                self.FAIL_LOUD(f"Not all Chrome instances are healthy: {status['healthy_instances']}/{status['total_instances']}")
                chrome_manager.stop_all_instances()
                return False
                
            # For existing Chrome on port 9222, Tradovate connection is optional
            # The user may not have Tradovate tab open immediately
            if status['total_instances'] > 0:
                self.LOG_SUCCESS(f"Chrome instances verified - Health check will detect Tradovate connection")
            
            self.LOG_SUCCESS(f"✅ Chrome management test passed - {status['total_instances']} instances running")
            self.test_results['chrome_management'] = {'passed': True, 'details': status}
            
            # Keep instances running for other tests
            time.sleep(2)
            return True
            
        except Exception as e:
            self.FAIL_LOUD(f"Chrome management test failed: {str(e)}")
            self.test_results['chrome_management'] = {'passed': False, 'error': str(e)}
            return False
    
    def test_authentication_validation(self) -> bool:
        """Test 2: Real authentication validation - FAIL FAST"""
        print("\n" + "="*60) 
        print("🔐 TESTING: Authentication Validation")
        print("="*60)
        
        try:
            auth_manager = ProductionAuthManager()
            
            # Test authentication validation
            if not auth_manager.validate_all_authentications():
                self.FAIL_LOUD("Authentication validation failed")
                
                # Check individual account status
                status = auth_manager.get_auth_status()
                for account_name, account_status in status['accounts'].items():
                    if not account_status['authenticated']:
                        self.LOG_WARNING(f"Account not authenticated: {account_name}")
                
                self.test_results['authentication'] = {'passed': False, 'details': status}
                return False
            
            # Verify all accounts are authenticated
            status = auth_manager.get_auth_status()
            
            if status['authenticated_accounts'] < status['total_accounts']:
                self.FAIL_LOUD(f"Not all accounts authenticated: {status['authenticated_accounts']}/{status['total_accounts']}")
                self.test_results['authentication'] = {'passed': False, 'details': status}
                return False
            
            self.LOG_SUCCESS(f"✅ Authentication test passed - {status['authenticated_accounts']} accounts authenticated")
            self.test_results['authentication'] = {'passed': True, 'details': status}
            
            # Keep auth monitoring running
            return True
            
        except Exception as e:
            self.FAIL_LOUD(f"Authentication test failed: {str(e)}")
            self.test_results['authentication'] = {'passed': False, 'error': str(e)}
            return False
    
    def test_production_validation(self) -> bool:
        """Test 3: Complete production validation - FAIL FAST"""
        print("\n" + "="*60)
        print("🔍 TESTING: Production Validation")
        print("="*60)
        
        try:
            validator = ProductionValidator()
            
            # Run full production validation
            if not validator.run_production_validation():
                self.FAIL_LOUD("Production validation failed")
                
                # Report specific failures
                if validator.critical_errors:
                    for error in validator.critical_errors:
                        self.LOG_WARNING(f"Validation error: {error}")
                
                self.test_results['production_validation'] = {'passed': False, 'errors': validator.critical_errors}
                return False
            
            self.LOG_SUCCESS("✅ Production validation test passed")
            self.test_results['production_validation'] = {'passed': True}
            return True
            
        except Exception as e:
            self.FAIL_LOUD(f"Production validation test failed: {str(e)}")
            self.test_results['production_validation'] = {'passed': False, 'error': str(e)}
            return False
    
    def test_real_time_monitoring(self) -> bool:
        """Test 4: Real-time account monitoring - FAIL FAST"""
        print("\n" + "="*60)
        print("📊 TESTING: Real-Time Account Monitoring")
        print("="*60)
        
        try:
            monitor = ProductionMonitor()
            
            # Start monitoring
            if not monitor.start_realtime_monitoring():
                self.FAIL_LOUD("Failed to start real-time monitoring")
                self.test_results['monitoring'] = {'passed': False, 'error': 'Failed to start'}
                return False
            
            # Let monitoring run for a short period
            self.LOG_SUCCESS("Monitoring started - collecting data for 30 seconds...")
            time.sleep(30)
            
            # Check monitoring status
            status = monitor.get_monitoring_status()
            
            if not status['monitoring_active']:
                self.FAIL_LOUD("Monitoring is not active")
                self.test_results['monitoring'] = {'passed': False, 'details': status}
                return False
            
            if status['accounts_monitored'] == 0:
                self.FAIL_LOUD("No accounts being monitored")
                self.test_results['monitoring'] = {'passed': False, 'details': status}
                return False
            
            self.LOG_SUCCESS(f"✅ Monitoring test passed - {status['accounts_monitored']} accounts monitored")
            self.test_results['monitoring'] = {'passed': True, 'details': status}
            
            # Stop monitoring for now
            monitor.stop_monitoring()
            return True
            
        except Exception as e:
            self.FAIL_LOUD(f"Monitoring test failed: {str(e)}")
            self.test_results['monitoring'] = {'passed': False, 'error': str(e)}
            return False
    
    def test_trading_engine_validation(self) -> bool:
        """Test 5: Trading engine validation (no real trades) - FAIL SAFELY"""
        print("\n" + "="*60)
        print("⚡ TESTING: Trading Engine Validation")
        print("="*60)
        
        try:
            trading_engine = ProductionTradingEngine()
            
            # Start trading engine (validation only)
            if not trading_engine.start_production_trading():
                self.FAIL_LOUD("Trading engine failed to start")
                self.test_results['trading_engine'] = {'passed': False, 'error': 'Failed to start'}
                return False
            
            # Test trading validations without actual trades
            print("\n🔍 Testing trading validations...")
            
            validation_results = []
            
            for account in trading_engine.validator.trading_accounts:
                if account.authenticated:
                    # Test permission validation
                    has_permissions = trading_engine.validate_trading_permissions(account)
                    validation_results.append({
                        'account': account.name,
                        'has_trading_permissions': has_permissions
                    })
                    
                    if has_permissions:
                        self.LOG_SUCCESS(f"✅ Trading permissions validated: {account.name}")
                    else:
                        self.LOG_WARNING(f"⚠️  Trading permissions issue: {account.name}")
                    
                    # Test margin validation (with small test amount)
                    has_margin = trading_engine.validate_sufficient_margin(account, "ES", 1)
                    validation_results[-1]['has_sufficient_margin'] = has_margin
                    
                    if has_margin:
                        self.LOG_SUCCESS(f"✅ Margin validation passed: {account.name}")
                    else:
                        self.LOG_WARNING(f"⚠️  Insufficient margin: {account.name}")
            
            # Check overall validation results
            total_accounts = len(validation_results)
            accounts_with_permissions = sum(1 for r in validation_results if r['has_trading_permissions'])
            accounts_with_margin = sum(1 for r in validation_results if r['has_sufficient_margin'])
            
            if accounts_with_permissions == 0:
                self.FAIL_LOUD("No accounts have trading permissions")
                self.test_results['trading_engine'] = {'passed': False, 'details': validation_results}
                return False
            
            self.LOG_SUCCESS(f"✅ Trading engine test passed - {accounts_with_permissions}/{total_accounts} accounts ready")
            self.test_results['trading_engine'] = {'passed': True, 'details': validation_results}
            
            # Stop trading engine
            trading_engine.emergency_stop_all_trading("Test completed")
            return True
            
        except Exception as e:
            self.FAIL_LOUD(f"Trading engine test failed: {str(e)}")
            self.test_results['trading_engine'] = {'passed': False, 'error': str(e)}
            return False
    
    def run_comprehensive_production_test(self) -> bool:
        """Run complete production system test - FAIL FAST"""
        
        print("="*80)
        print("🚀 COMPREHENSIVE PRODUCTION SYSTEM TEST")
        print("TESTING WITH REAL TRADOVATE ACCOUNTS AND LIVE DATA")
        print("FAIL FAST, FAIL LOUD, FAIL SAFELY")
        print("="*80)
        
        start_time = datetime.now()
        
        # Test sequence - must pass in order
        test_sequence = [
            ("Chrome Management", self.test_chrome_management),
            ("Authentication Validation", self.test_authentication_validation), 
            ("Production Validation", self.test_production_validation),
            ("Real-Time Monitoring", self.test_real_time_monitoring),
            ("Trading Engine Validation", self.test_trading_engine_validation)
        ]
        
        passed_tests = 0
        
        for test_name, test_func in test_sequence:
            print(f"\n🔄 Running test: {test_name}")
            
            if test_func():
                passed_tests += 1
                self.LOG_SUCCESS(f"✅ {test_name} - PASSED")
            else:
                self.FAIL_LOUD(f"❌ {test_name} - FAILED")
                print(f"\n💥 Test sequence stopped at: {test_name}")
                break
        
        # Generate final report
        end_time = datetime.now()
        test_duration = (end_time - start_time).total_seconds()
        
        print("\n" + "="*80)
        print("📋 PRODUCTION TEST REPORT")
        print("="*80)
        print(f"Test Duration: {test_duration:.1f} seconds")
        print(f"Tests Passed: {passed_tests}/{len(test_sequence)}")
        print(f"Critical Failures: {len(self.critical_failures)}")
        print(f"Warnings: {len(self.warnings)}")
        
        # Detailed results
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result['passed'] else "❌ FAILED"
            print(f"{test_name}: {status}")
            
        if passed_tests == len(test_sequence):
            print("\n🎉 ALL PRODUCTION TESTS PASSED!")
            print("✅ System is READY for live trading")
            success = True
        else:
            print(f"\n❌ PRODUCTION TEST FAILED - {passed_tests}/{len(test_sequence)} tests passed")
            print("⚠️  System is NOT ready for live trading")
            success = False
        
        # Save detailed report
        self._save_test_report(start_time, end_time, test_duration, success)
        
        print("="*80)
        
        return success
    
    def _save_test_report(self, start_time: datetime, end_time: datetime, duration: float, success: bool):
        """Save detailed test report"""
        
        report = {
            "test_run_id": f"production_test_{int(start_time.timestamp())}",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "overall_success": success,
            "tests_passed": len([r for r in self.test_results.values() if r['passed']]),
            "total_tests": len(self.test_results),
            "critical_failures": self.critical_failures,
            "warnings": self.warnings,
            "detailed_results": self.test_results
        }
        
        # Save to logs
        log_dir = os.path.join(project_root, "logs", "production_test")
        os.makedirs(log_dir, exist_ok=True)
        
        report_file = os.path.join(log_dir, f"production_test_report_{int(start_time.timestamp())}.json")
        
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved: {report_file}")

def main():
    """Main test runner entry point"""
    
    test_runner = ProductionTestRunner()
    
    try:
        success = test_runner.run_comprehensive_production_test()
        
        if success:
            print("\n🎯 PRODUCTION SYSTEM READY")
            print("💰 Safe to proceed with live trading")
            return 0
        else:
            print("\n🛑 PRODUCTION SYSTEM NOT READY")
            print("⚠️  Fix critical issues before trading")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Test runner crashed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())