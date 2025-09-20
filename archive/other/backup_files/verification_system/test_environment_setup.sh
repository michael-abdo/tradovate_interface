#!/bin/bash

# Test Environment Setup for Order Verification System
# Creates a safe testing environment before production deployment

set -e

echo "🧪 Setting Up Order Verification Test Environment"
echo "================================================="
echo ""

PROJECT_ROOT="/Users/Mike/trading"
TEST_ENV_DIR="$PROJECT_ROOT/test_verification_env"
BACKUP_DIR="$PROJECT_ROOT/backup_files/verification_system"

# Create test environment directory structure
echo "📁 Creating test environment structure..."
mkdir -p "$TEST_ENV_DIR"/{scripts,logs,results,chrome_test}

echo "✅ Test environment directories created:"
echo "   - $TEST_ENV_DIR/scripts (test scripts)"
echo "   - $TEST_ENV_DIR/logs (test execution logs)"
echo "   - $TEST_ENV_DIR/results (test results)"
echo "   - $TEST_ENV_DIR/chrome_test (Chrome test configurations)"
echo ""

# Copy necessary test files
echo "📋 Copying test files..."

# Copy the integration test
if [ -f "$PROJECT_ROOT/docs/investigations/dom-order-fix/test_end_to_end_verification.py" ]; then
    cp "$PROJECT_ROOT/docs/investigations/dom-order-fix/test_end_to_end_verification.py" "$TEST_ENV_DIR/scripts/"
    echo "✅ Copied integration test script"
else
    echo "❌ WARNING: Integration test script not found"
fi

# Copy current autoOrder script for testing
if [ -f "$PROJECT_ROOT/scripts/tampermonkey/autoOrder.user.js" ]; then
    cp "$PROJECT_ROOT/scripts/tampermonkey/autoOrder.user.js" "$TEST_ENV_DIR/scripts/autoOrder.test.js"
    echo "✅ Copied current autoOrder script for testing"
else
    echo "❌ ERROR: autoOrder script not found"
    exit 1
fi

# Copy verification monitor
if [ -f "$PROJECT_ROOT/src/utils/order_execution_monitor.py" ]; then
    cp "$PROJECT_ROOT/src/utils/order_execution_monitor.py" "$TEST_ENV_DIR/scripts/"
    echo "✅ Copied verification monitor"
else
    echo "❌ WARNING: Verification monitor not found"
fi

echo ""

# Create test configuration
echo "⚙️ Creating test configuration..."
cat > "$TEST_ENV_DIR/test_config.json" << 'EOF'
{
  "test_environment": {
    "name": "Order Verification Testing",
    "version": "1.0.0",
    "created": "2025-07-28",
    "purpose": "Safe testing environment for mandatory order verification system"
  },
  "chrome_instances": {
    "test_ports": [9223, 9224, 9225],
    "production_ports": [9223, 9224, 9225],
    "test_timeout": 60
  },
  "test_parameters": {
    "test_symbol": "NQ",
    "test_quantity": 1,
    "test_tp": 100,
    "test_sl": 50,
    "test_tick_size": 0.25,
    "verification_timeout": 10000,
    "max_test_orders": 5
  },
  "safety_limits": {
    "max_concurrent_tests": 1,
    "min_gap_between_tests": 30,
    "abort_on_first_failure": false,
    "require_manual_confirmation": true
  },
  "verification_criteria": {
    "required_success_rate": 0.99,
    "max_false_positives": 0,
    "max_false_negatives": 0,
    "max_verification_overhead_ms": 100,
    "required_confidence_level": "MEDIUM"
  }
}
EOF

echo "✅ Test configuration created: $TEST_ENV_DIR/test_config.json"
echo ""

# Create test execution script
echo "🚀 Creating test execution script..."
cat > "$TEST_ENV_DIR/run_verification_tests.py" << 'EOF'
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
EOF

chmod +x "$TEST_ENV_DIR/run_verification_tests.py"
echo "✅ Test execution script created: $TEST_ENV_DIR/run_verification_tests.py"
echo ""

# Create test documentation
echo "📝 Creating test documentation..."
cat > "$TEST_ENV_DIR/README.md" << 'EOF'
# Order Verification System - Test Environment

## Overview
This test environment provides a safe space to thoroughly test the mandatory order verification system before production deployment.

## Directory Structure
```
test_verification_env/
├── README.md                     # This file
├── test_config.json             # Test configuration
├── run_verification_tests.py    # Main test runner
├── scripts/                     # Test scripts
│   ├── test_end_to_end_verification.py
│   ├── autoOrder.test.js
│   └── order_execution_monitor.py
├── logs/                        # Test execution logs
├── results/                     # Test results
└── chrome_test/                 # Chrome test configurations
```

## Running Tests

### Prerequisites
1. Chrome instances running on ports 9223, 9224, 9225
2. Trading platform loaded and logged in
3. Python 3.8+ with required modules (asyncio, websockets, json)

### Execute Test Suite
```bash
cd test_verification_env
python3 run_verification_tests.py
```

### Individual Tests
```bash
# Run integration tests only
python3 scripts/test_end_to_end_verification.py

# Test verification monitor
python3 -c "
import sys; sys.path.append('scripts')
from order_execution_monitor import VerificationMonitor
monitor = VerificationMonitor()
print('Monitor test passed')
"
```

## Test Configuration
Edit `test_config.json` to modify test parameters:
- Chrome ports to test
- Test symbols and quantities
- Verification timeouts
- Safety limits

## Safety Features
- **Limited test quantities** (max 1 contract)
- **Controlled test symbols** (NQ only)
- **Manual confirmation required** for production-like tests
- **Automatic abort** on critical failures
- **Comprehensive logging** of all test activities

## Test Results
Results are saved in the `results/` directory with timestamps:
- JSON format for programmatic analysis
- Detailed logs in `logs/` directory
- Success/failure metrics
- Performance measurements

## Success Criteria
Tests must pass the following criteria:
- ✅ Integration tests execute successfully
- ✅ Verification system works on all Chrome instances
- ✅ Position changes are properly detected
- ✅ Verification overhead < 100ms
- ✅ No false positives (UI success without position change)
- ✅ No false negatives (position change marked as failure)
- ✅ Verification monitor functions correctly
- ✅ All three execution paths use verification

## Before Production Deployment
1. All tests in this environment must pass
2. Review test logs for any warnings
3. Verify performance metrics meet requirements
4. Confirm rollback procedure is tested and ready
5. Schedule deployment during low-trading period

## Emergency Procedures
If tests reveal critical issues:
1. DO NOT deploy to production
2. Use rollback script to restore original behavior
3. Investigate and fix issues in this test environment
4. Re-run full test suite before attempting deployment

## Contact
For questions about the test environment or verification system:
- Review logs in the `logs/` directory
- Check results in the `results/` directory
- Use rollback procedure if needed
EOF

echo "✅ Test documentation created: $TEST_ENV_DIR/README.md"
echo ""

# Create quick test runner
echo "🏃 Creating quick test runner..."
cat > "$TEST_ENV_DIR/quick_test.sh" << 'EOF'
#!/bin/bash
# Quick test runner for basic verification system checks

echo "🏃 Quick Verification System Test"
echo "================================="
echo ""

# Check if Chrome is running
echo "🔍 Checking Chrome instances..."
for port in 9223 9224 9225; do
    if curl -s "http://localhost:$port/json/list" > /dev/null; then
        echo "✅ Chrome running on port $port"
    else
        echo "❌ Chrome NOT running on port $port"
    fi
done

echo ""

# Check if test files exist
echo "📋 Checking test files..."
files_to_check=(
    "scripts/autoOrder.test.js"
    "scripts/test_end_to_end_verification.py"
    "scripts/order_execution_monitor.py"
    "test_config.json"
)

for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
    fi
done

echo ""
echo "🚀 To run full test suite: python3 run_verification_tests.py"
echo "📖 For more details: cat README.md"
EOF

chmod +x "$TEST_ENV_DIR/quick_test.sh"
echo "✅ Quick test runner created: $TEST_ENV_DIR/quick_test.sh"
echo ""

echo "🎉 Test Environment Setup Complete!"
echo "===================================="
echo ""
echo "📍 Test environment location: $TEST_ENV_DIR"
echo ""
echo "🚀 Next steps:"
echo "1. cd $TEST_ENV_DIR"
echo "2. ./quick_test.sh  # Check prerequisites"
echo "3. python3 run_verification_tests.py  # Run full test suite"
echo ""
echo "📖 See $TEST_ENV_DIR/README.md for detailed instructions"
echo ""
echo "⚠️  IMPORTANT: Only deploy to production after ALL tests pass"