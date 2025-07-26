# Chrome Restart Logic - Quick Start Guide

## 🚀 Quick Implementation (30 minutes)

### Prerequisites
- Python 3.7+ with existing trading environment
- Chrome browser installed
- Access to `/Users/Mike/trading` directory

### Step 1: Backup Existing Files (2 minutes)
```bash
cd /Users/Mike/trading

# Create backups
cp start_all.py start_all.py.backup
cp src/auto_login.py src/auto_login.py.backup
cp tradovate_interface/src/utils/process_monitor.py tradovate_interface/src/utils/process_monitor.py.backup
```

### Step 2: Apply Phase 1 Changes (10 minutes)

#### 2.1 Update start_all.py
Add the StartupManager class and error handling as detailed in `IMPLEMENTATION_BREAKDOWN.md` steps 1-21.

Key changes:
- Add StartupManager class with retry logic
- Replace run_auto_login() calls with StartupManager.start_with_retry()
- Add comprehensive error handling

#### 2.2 Update auto_login.py
Enhance ChromeInstance with validation methods as detailed in steps 22-32.

Key changes:
- Add StartupPhase enum
- Add start_with_validation() method
- Add health reporting methods

#### 2.3 Update Configuration
Add to `config/connection_health.json`:
```json
{
  "startup_monitoring": {
    "enabled": true,
    "max_retries": 3,
    "retry_delay_seconds": 10,
    "startup_timeout_seconds": 60
  }
}
```

### Step 3: Test Phase 1 (5 minutes)
```bash
# Create and run test script
python test_phase1.py

# Verify:
# ✓ No import errors
# ✓ Prerequisite validation passes
# ✓ Configuration loads correctly
```

### Step 4: Apply Phase 2 Changes (10 minutes)

#### 4.1 Update process_monitor.py
Add startup monitoring capabilities as detailed in steps 1-18 of Phase 2.

Key changes:
- Add StartupMonitoringMode and StartupProcessInfo
- Add startup monitoring methods
- Update existing methods for integration

#### 4.2 Update process_monitor.json
Add startup monitoring configuration:
```json
{
  "startup_monitoring": {
    "enabled": true,
    "mode": "active",
    "check_interval_seconds": 2,
    "max_startup_duration_seconds": 120,
    "max_launch_attempts": 3
  }
}
```

### Step 5: Test Complete Implementation (3 minutes)
```bash
# Run integration test
python test_integration.py

# Start the system with new error handling
python start_all.py
```

## 🎯 Verification Checklist

### Immediate Benefits
- [ ] start_all.py no longer crashes on Chrome failures
- [ ] Detailed error messages show exactly what failed
- [ ] Automatic retry attempts work with cleanup
- [ ] Chrome processes are monitored from startup

### Quick Validation
1. **Test Failure Recovery**
   ```bash
   # Kill a Chrome process during startup
   pkill -f "remote-debugging-port=9223"
   # System should detect and retry
   ```

2. **Check Logs**
   ```bash
   # View startup events
   tail -f logs/startup_failures/*.log
   ```

3. **Monitor Status**
   ```bash
   # Check process monitor status
   curl http://localhost:5000/api/health
   ```

## ⚡ Common Issues & Quick Fixes

### Import Errors
```python
# Add to start_all.py if missing
import socket
import requests
import psutil
from typing import Dict, List, Optional, Tuple
```

### Configuration Not Found
```bash
# Create config directory if missing
mkdir -p config
# Copy default configuration
cp config/connection_health.json.example config/connection_health.json
```

### Process Monitor Not Starting
```python
# Add fallback in StartupManager.__init__
try:
    self.process_monitor = ChromeProcessMonitor()
except:
    self.process_monitor = None  # Continue without monitoring
```

## 📊 Success Metrics

You'll know the implementation is working when:
1. **No Crashes**: start_all.py completes even with Chrome failures
2. **Retry Works**: Failed Chrome instances are automatically restarted
3. **Clear Errors**: Logs show exactly why failures occurred
4. **Recovery Time**: Failed instances recover within 30-60 seconds

## 🆘 Need Help?

1. **Check Full Documentation**: See `IMPLEMENTATION_BREAKDOWN.md` for detailed steps
2. **Review Architecture**: See `README_CHROME_RESTART.md` for design details
3. **Debug Mode**: Run with verbose logging:
   ```bash
   LOGLEVEL=DEBUG python start_all.py
   ```

## ⏱️ Time Estimates

- **Minimal Fix** (Phase 1 only): 20 minutes
- **Full Implementation** (Phase 1 + 2): 45 minutes
- **With Testing**: 60 minutes
- **Production Deployment**: 90 minutes

Remember: You can implement Phase 1 first and add Phase 2 later if needed!