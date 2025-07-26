# Chrome Process Restart Logic Implementation

## Overview

This implementation adds comprehensive Chrome process restart logic to prevent `start_all.py` crashes when Chrome instances fail during startup. The solution includes error handling, retry mechanisms, and startup phase monitoring.

## Problem Statement

**Issue**: `start_all.py` crashes with `WebSocketConnectionClosedException` when Chrome instances on ports 9223/9224 terminate unexpectedly during startup.

**Root Cause**: Chrome instances fail during the critical startup phase (0-60 seconds) before the existing watchdog can protect them.

## Solution Architecture

### Phase 1: Immediate Crash Fix
- **Enhanced Error Handling**: Comprehensive try/catch blocks in `start_all.py`
- **Startup Validation**: Pre-flight checks for ports, memory, network, and Chrome executable
- **Retry Logic**: Configurable retry attempts with cleanup between attempts
- **Detailed Logging**: Full startup event tracking for debugging

### Phase 2: Startup Monitoring
- **Extended Process Monitor**: Coverage of the 0-60 second startup phase
- **Early Registration**: Monitor Chrome processes before they're fully initialized
- **Startup Health Checks**: Progressive validation of process, port, and WebSocket readiness
- **Integration**: Seamless handoff from startup to runtime monitoring

## Implementation Files

### Modified Files
1. **`/Users/Mike/trading/start_all.py`**
   - Added `StartupManager` class with retry logic
   - Comprehensive error handling and validation
   - Integration with process monitor

2. **`/Users/Mike/trading/src/auto_login.py`**
   - Enhanced `ChromeInstance` with startup validation
   - Added startup phase tracking
   - Detailed health reporting methods

3. **`/Users/Mike/trading/tradovate_interface/src/utils/process_monitor.py`**
   - Added startup monitoring capabilities
   - Early process registration support
   - Startup-specific health checks

### Configuration Files
1. **`/Users/Mike/trading/config/connection_health.json`**
   - Added `startup_monitoring` section
   - Configurable retry policies and timeouts

2. **`/Users/Mike/trading/tradovate_interface/config/process_monitor.json`**
   - Added startup monitoring configuration
   - Validation check settings

## Key Features

### 1. Startup Validation
- **Port Availability**: Ensures ports 9223/9224 are free
- **Memory Check**: Verifies sufficient RAM (2GB minimum)
- **Network Connectivity**: Tests connection to Tradovate
- **Chrome Executable**: Validates Chrome installation

### 2. Error Recovery
- **Automatic Retry**: Up to 3 attempts with 10-second delays
- **Process Cleanup**: Kills failed Chrome instances before retry
- **State Preservation**: Maintains startup context across attempts

### 3. Monitoring Integration
- **Early Registration**: Tracks Chrome processes from launch
- **Progressive Validation**: Checks process → port → WebSocket
- **Seamless Handoff**: Transitions from startup to runtime monitoring

### 4. Comprehensive Logging
- **Event Tracking**: Every startup phase logged with timestamps
- **Error Details**: Full context for debugging failures
- **Success Metrics**: Startup duration and validation results

## Usage

### Basic Usage
```bash
# Run with enhanced error handling
python start_all.py

# The system will automatically:
# 1. Validate prerequisites
# 2. Start Chrome instances with monitoring
# 3. Retry on failures
# 4. Provide detailed error reports
```

### Configuration
Edit `config/connection_health.json`:
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

### Testing
```bash
# Test Phase 1 (error handling)
python test_phase1.py

# Test Phase 2 (startup monitoring)
python test_phase2.py

# Test full integration
python test_integration.py
```

## Error Handling

### Common Startup Failures
1. **Port Already in Use**
   - Detection: Port validation fails
   - Recovery: Automatic cleanup and retry

2. **Chrome Crash During Login**
   - Detection: WebSocket connection fails
   - Recovery: Process killed and restarted

3. **Network Issues**
   - Detection: Tradovate unreachable
   - Recovery: Retry with backoff

4. **Resource Exhaustion**
   - Detection: Memory check fails
   - Recovery: Wait for resources before retry

### Monitoring States
- **INITIALIZING**: Chrome process starting
- **LAUNCHING_CHROME**: Process launched, awaiting response
- **CONNECTING_WEBSOCKET**: Establishing debug connection
- **LOADING_TRADOVATE**: Loading trading interface
- **AUTHENTICATING**: Login process active
- **READY**: Fully operational
- **FAILED**: Startup failed, may retry

## Troubleshooting

### Startup Failures
1. Check logs in `/logs/startup_failures/`
2. Review the startup report for specific validation failures
3. Verify Chrome is installed and accessible
4. Ensure network connectivity to Tradovate

### Configuration Issues
1. Verify JSON syntax in configuration files
2. Check file permissions for config directory
3. Ensure all required fields are present

### Process Monitor Issues
1. Check if process monitor is running: `ps aux | grep process_monitor`
2. Review monitor logs in `/logs/chrome_stability/`
3. Verify port 9222 is excluded from monitoring

## Performance Impact

- **Startup Time**: Adds 2-5 seconds for validation
- **Memory Usage**: Minimal overhead (<50MB)
- **CPU Usage**: Negligible during normal operation
- **Network**: One connectivity check per startup

## Security Considerations

- **Port Protection**: Port 9222 is never monitored or modified
- **Process Isolation**: Each Chrome instance runs in separate profile
- **Credential Safety**: No credentials logged or exposed
- **Clean Shutdown**: Proper cleanup prevents zombie processes

## Future Enhancements

### Phase 3 (Optional)
- Advanced restart coordination between monitors
- Machine learning for failure prediction
- Automated recovery policy optimization
- Dashboard integration for manual control

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs for detailed error information
3. Consult the atomic implementation breakdown in `IMPLEMENTATION_BREAKDOWN.md`