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
