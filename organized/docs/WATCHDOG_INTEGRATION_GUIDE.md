# Chrome Process Watchdog - Integration with start_all.py

## Overview
The Chrome Process Watchdog is now fully integrated with `start_all.py`. When you run `start_all.py`, the watchdog automatically starts monitoring Chrome instances on ports 9223 and above.

## How It Works

### 1. Automatic Integration
When you run `start_all.py`:
```bash
python3 start_all.py
```

The following happens automatically:
1. **auto_login.py** starts Chrome instances
2. **Chrome Process Watchdog** initializes and monitors all Chrome instances
3. **Dashboard** starts and connects to Chrome instances
4. **Port 9222 Protection**: The watchdog will NEVER touch port 9222

### 2. What Gets Monitored
- ✅ Chrome on port 9223 (Account 2)
- ✅ Chrome on port 9224 (Account 3)
- ✅ Chrome on any port 9223+
- ❌ Chrome on port 9222 (PROTECTED - Never monitored)

### 3. Crash Recovery Flow
If a Chrome instance crashes (on ports 9223+):
1. Watchdog detects crash within 10 seconds
2. Saves current state (trading info, credentials)
3. Cleanly shuts down crashed Chrome
4. Restarts Chrome on same port
5. Re-authenticates automatically
6. Total recovery time: ~20-30 seconds

## Usage Examples

### Basic Usage (Recommended)
```bash
# Start everything with watchdog protection
python3 start_all.py
```

### With Custom Wait Time
```bash
# Wait 20 seconds between Chrome start and dashboard
python3 start_all.py --wait 20
```

### Background Mode
```bash
# Run auto_login in background
python3 start_all.py --background
```

### Disable Watchdog (Not Recommended)
```bash
# Start without crash protection
python3 start_all.py --no-watchdog
```

## Monitoring Status

When start_all.py runs, you'll see:
```
============================================================
🛡️  Chrome Process Watchdog: ENABLED
   - Monitoring Chrome instances on ports 9223+
   - Automatic crash recovery in <30 seconds
   - Port 9222 is protected from monitoring
============================================================
```

In the logs, you'll see:
```
[2025-07-25 16:30:05] INFO - Chrome process monitoring started
[2025-07-25 16:30:11] INFO - Registered Chrome process for Account 1 - PID: 49557, Port: 9223
[2025-07-25 16:30:11] INFO - Registered Chrome process for Account 2 - PID: 49558, Port: 9224
```

## Testing Crash Recovery

To test the watchdog while using start_all.py:

1. Start the system:
   ```bash
   python3 start_all.py
   ```

2. In another terminal, find Chrome processes:
   ```bash
   ps aux | grep -E "9223|9224" | grep -v grep
   ```

3. Kill a Chrome instance (NOT 9222!):
   ```bash
   kill -9 [PID_OF_CHROME_ON_9223_OR_9224]
   ```

4. Watch the first terminal - within 30 seconds you should see:
   - Crash detection
   - Chrome restart
   - Re-authentication

## Log Files

### Watchdog Logs
- **General**: `logs/chrome_monitor_YYYYMMDD.log`
- **Crashes**: `logs/crashes/crash_[account]_[timestamp].json`
- **State Backups**: `recovery/[account]_state.json`

### Example Log Entry
```
[2025-07-25 16:47:31] ERROR - Crash confirmed for Account 2: process_died
[2025-07-25 16:47:31] WARNING - Initiating restart for Account 2 due to process_died
[2025-07-25 16:47:37] INFO - Chrome restarted successfully for Account 2
[2025-07-25 16:47:52] INFO - Authentication restored for Account 2
```

## Configuration

The watchdog uses `tradovate_interface/config/process_monitor.json`:
```json
{
    "check_interval": 10,          // Health check every 10 seconds
    "max_restart_attempts": 3,     // Try 3 times before giving up
    "restart_delay": 5,            // Wait 5 seconds before restart
    "enable_state_preservation": true
}
```

## Important Notes

1. **Port 9222 is Sacred**: The watchdog will NEVER monitor or restart Chrome on port 9222
2. **Automatic Start**: You don't need to start the watchdog separately - it's integrated
3. **Credentials Required**: Ensure `config/credentials.json` exists for auto-login after crashes
4. **Multiple Accounts**: Each account/port is monitored independently

## Troubleshooting

### Watchdog Not Starting
Check if you see this message:
```
⚠️  Chrome Process Watchdog: NOT AVAILABLE
```
This means the watchdog module couldn't be loaded. Check:
- `tradovate_interface/src/utils/process_monitor.py` exists
- All dependencies are installed

### Chrome Not Restarting
Check logs for:
- "REFUSING to restart Chrome on protected port 9222" - This is intentional
- "Max restart attempts reached" - Chrome crashed too many times
- "Port still in use" - Old Chrome process didn't clean up

### Manual Recovery
If automatic recovery fails:
```bash
# Find stuck Chrome processes
lsof -ti:9223  # or 9224, 9225, etc.

# Kill them
lsof -ti:9223 | xargs kill -9

# Restart start_all.py
python3 start_all.py
```

## Summary

The Chrome Process Watchdog is now seamlessly integrated with start_all.py:
- ✅ Automatic crash detection and recovery
- ✅ Preserves trading state across restarts
- ✅ Re-authenticates automatically
- ✅ Protects port 9222 from any interference
- ✅ Zero configuration required - just works

Just run `python3 start_all.py` and enjoy crash protection!