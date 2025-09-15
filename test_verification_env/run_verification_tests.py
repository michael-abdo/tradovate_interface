#!/usr/bin/env python3
"""
Comprehensive Test Suite for Order Verification System
Runs all verification tests in a controlled environment
"""

import asyncio
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Test configuration
TEST_DIR = Path(__file__).parent
CONFIG_FILE = TEST_DIR / "test_config.json"
LOG_DIR = TEST_DIR / "logs"
RESULTS_DIR = TEST_DIR / "results"

class VerificationTestSuite:
    def __init__(self):
        self.config = self.load_config()
        self.test_results = {}
        self.start_time = None
        
    def load_config(self):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
        # Also write to log file
        log_file = LOG_DIR / f"test_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_file.parent.mkdir(exist_ok=True)
        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] {level}: {message}\n")
    
    def check_prerequisites(self):
        """Check if test environment is ready"""
        self.log("🔍 Checking test prerequisites...")
        
        checks = {
            'config_file': CONFIG_FILE.exists(),
            'integration_test': (TEST_DIR / "scripts" / "test_end_to_end_verification.py").exists(),
            'autoorder_script': (TEST_DIR / "scripts" / "autoOrder.test.js").exists(),
            'monitor_script': (TEST_DIR / "scripts" / "order_execution_monitor.py").exists()
        }
        
        all_passed = True
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            self.log(f"  {status} {check_name}: {'PASS' if passed else 'FAIL'}")
            if not passed:
                all_passed = False
        
        if not all_passed:
            self.log("❌ Prerequisites not met. Aborting tests.", "ERROR")
            return False
        
        self.log("✅ All prerequisites met. Ready to run tests.")
        return True
    
    async def run_integration_tests(self):
        """Run the end-to-end integration tests"""
        self.log("🧪 Running integration tests...")
        
        try:
            # Run the integration test
            cmd = [
                sys.executable, 
                str(TEST_DIR / "scripts" / "test_end_to_end_verification.py")
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300  # 5 minutes timeout
            )
            
            success = result.returncode == 0
            
            self.test_results['integration_tests'] = {
                'success': success,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode,
                'timestamp': datetime.now().isoformat()
            }
            
            if success:
                self.log("✅ Integration tests PASSED")
            else:
                self.log("❌ Integration tests FAILED", "ERROR")
                self.log(f"Error output: {result.stderr}", "ERROR")
                
            return success
            
        except Exception as e:
            self.log(f"❌ Integration test execution failed: {e}", "ERROR")
            self.test_results['integration_tests'] = {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            return False
    
    def run_verification_monitor_check(self):
        """Check verification monitor functionality"""
        self.log("🔍 Testing verification monitor...")
        
        try:
            # Import and test the verification monitor
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "monitor", 
                TEST_DIR / "scripts" / "order_execution_monitor.py"
            )
            monitor_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(monitor_module)
            
            # Test VerificationMonitor class
            if hasattr(monitor_module, 'VerificationMonitor'):
                monitor = monitor_module.VerificationMonitor()
                
                # Test basic functionality
                test_data = {
                    'symbol': 'NQ',
                    'success': True,
                    'executionTime': 150,
                    'totalOverhead': 80
                }
                
                monitor.record_verification_attempt(test_data)
                report = monitor.generate_monitoring_report()
                
                success = 'health_score' in report
                
                self.test_results['verification_monitor'] = {
                    'success': success,
                    'health_score': report.get('health_score', 0),
                    'timestamp': datetime.now().isoformat()
                }
                
                if success:
                    self.log("✅ Verification monitor test PASSED")
                else:
                    self.log("❌ Verification monitor test FAILED", "ERROR")
                    
                return success
            else:
                self.log("❌ VerificationMonitor class not found", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Verification monitor test failed: {e}", "ERROR")
            self.test_results['verification_monitor'] = {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            return False
    
    def save_results(self):
        """Save test results to file"""
        results_file = RESULTS_DIR / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        results_file.parent.mkdir(exist_ok=True)
        
        final_results = {
            'test_session': {
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'end_time': datetime.now().isoformat(),
                'config': self.config,
                'environment': 'test'
            },
            'results': self.test_results,
            'summary': {
                'total_tests': len(self.test_results),
                'passed_tests': sum(1 for r in self.test_results.values() if r.get('success', False)),
                'failed_tests': sum(1 for r in self.test_results.values() if not r.get('success', False)),
                'overall_success': all(r.get('success', False) for r in self.test_results.values())
            }
        }
        
        with open(results_file, 'w') as f:
            json.dump(final_results, f, indent=2)
        
        self.log(f"📊 Test results saved to: {results_file}")
        return final_results
    
    async def run_all_tests(self):
        """Run complete test suite"""
        self.start_time = datetime.now()
        self.log("🚀 Starting Order Verification Test Suite")
        self.log("=" * 50)
        
        if not self.check_prerequisites():
            return False
        
        # Run tests
        tests = [
            ("Integration Tests", self.run_integration_tests()),
            ("Verification Monitor", self.run_verification_monitor_check())
        ]
        
        all_passed = True
        for test_name, test_coro in tests:
            self.log(f"\n🧪 Running {test_name}...")
            try:
                if asyncio.iscoroutine(test_coro):
                    result = await test_coro
                else:
                    result = test_coro
                    
                if not result:
                    all_passed = False
            except Exception as e:
                self.log(f"❌ {test_name} failed with exception: {e}", "ERROR")
                all_passed = False
        
        # Save results
        final_results = self.save_results()
        
        # Print summary
        self.log("\n" + "=" * 50)
        if all_passed:
            self.log("🎉 ALL TESTS PASSED! Verification system ready for deployment.")
        else:
            self.log("❌ SOME TESTS FAILED! Review results before deployment.", "ERROR")
        
        self.log(f"📊 Test Summary:")
        self.log(f"   Total: {final_results['summary']['total_tests']}")
        self.log(f"   Passed: {final_results['summary']['passed_tests']}")
        self.log(f"   Failed: {final_results['summary']['failed_tests']}")
        
        return all_passed

if __name__ == "__main__":
    suite = VerificationTestSuite()
    result = asyncio.run(suite.run_all_tests())
    sys.exit(0 if result else 1)
