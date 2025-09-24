# Chrome Cleanup Fix Plan - Protect Port 9222 During Shutdown

## 1. Current Problem

When stopping start_all.py, it kills ALL Chrome instances with remote-debugging-port, including port 9222:
- `pgrep -f "remote-debugging-port"` finds all Chrome with debugging
- `pkill -f "remote-debugging-port"` kills all Chrome with debugging

## 2. Solution Approach

Make Chrome cleanup port-specific:
- Only track Chrome processes on ports 9223+
- Never touch Chrome on port 9222
- Use more precise process matching

## 3. Implementation Steps

### Step 1: Fix collect_chrome_processes()
Instead of using `pgrep -f "remote-debugging-port"`:
- Use `ps aux | grep` to find processes
- Parse the port number from command line
- Only track if port >= 9223

### Step 2: Fix cleanup_chrome_instances()
Remove the dangerous `pkill -f "remote-debugging-port"`:
- Only kill PIDs we explicitly tracked
- No broad pkill commands
- Add port validation before killing

### Step 3: Add Port Protection
Create explicit port range constants:
- PROTECTED_PORT = 9222
- MIN_MANAGED_PORT = 9223
- Never touch anything below MIN_MANAGED_PORT

## 4. Benefits
- Port 9222 remains completely independent
- Can run other Chrome debugging on 9222
- Clean shutdown only affects our managed instances
- No accidental process kills

## 5. Testing
1. Start Chrome on port 9222 manually
2. Run start_all.py (uses 9223+)
3. Stop start_all.py with Ctrl+C
4. Verify Chrome on 9222 still running