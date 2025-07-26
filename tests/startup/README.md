# Startup Tests

This directory contains test scripts for the enhanced Chrome startup system.

## Test Scripts

### 1. `test_startup_validation.py`
Pre-test environment validation script that checks:
- Port availability (9223, 9224, 5000)
- Virtual environment setup
- System resources (memory, CPU)
- Chrome installation
- Required file presence

**Usage:** `python3 tests/startup/test_startup_validation.py`

### 2. `monitor_startup_logs.py`
Real-time log monitoring tool that displays:
- JSON-formatted startup logs
- Color-coded output by severity
- Startup phase tracking
- Error/warning counts

**Usage:** `python3 tests/startup/monitor_startup_logs.py`

### 3. `test_enhanced_startup.py`
Comprehensive test runner that:
- Runs pre-test validation
- Executes start_all.py with monitoring
- Collects performance metrics
- Generates test reports

**Usage:** `python3 tests/startup/test_enhanced_startup.py`

### 4. `post_test_decision.py`
Post-test analysis tool that:
- Analyzes test results
- Makes rollback decisions
- Performs cleanup
- Generates recommendations

**Usage:** `python3 tests/startup/post_test_decision.py [test_id]`

## Running Full Test Suite

```bash
# 1. Validate environment
python3 tests/startup/test_startup_validation.py

# 2. Run comprehensive test
python3 tests/startup/test_enhanced_startup.py

# 3. Analyze results and make decision
python3 tests/startup/post_test_decision.py
```

## Test Reports

Test reports are saved to:
- `logs/test/` - Test execution logs
- `logs/test_archives/` - Archived test results
- `docs/deployment/` - Deployment guides and analysis