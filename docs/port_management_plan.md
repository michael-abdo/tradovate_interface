# Port Management Plan - Protecting Port 9222

## 1. Scan the Codebase

### Current Port Usage:
- **Port 9222**: Currently used as BASE_DEBUGGING_PORT in auto_login.py
- **Ports 9222+**: Used for Tradovate account Chrome instances (9222, 9223, 9224...)
- **Port 9321**: Reserved for dashboard Chrome window
- **Port 6001**: Flask dashboard server
- **Port 5000**: Webhook server (when active)

### Files That Reference Ports:
- `src/auto_login.py`: BASE_DEBUGGING_PORT = 9222
- `src/app.py`: TradovateController(base_port=9222)
- `src/dashboard.py`: app.run(port=6001)
- `start_all.py`: dashboard_port = 9321, tests ports starting at 9222
- `README.md`: Documents port 9222 as starting point

## 2. Find What's Affected

### Components That Will Change:
1. **auto_login.py**
   - BASE_DEBUGGING_PORT needs to change from 9222 to 9223
   - Port assignment logic (currently: BASE_DEBUGGING_PORT + idx)

2. **app.py**
   - TradovateController default base_port parameter
   - Connection initialization loop

3. **start_all.py**
   - test_chrome_debugging_connections() currently tests from port 9222
   - Dashboard port remains 9321 (no change needed)

4. **Documentation**
   - README.md port references
   - Any other docs mentioning port numbers

### Side Effects to Consider:
- Existing Chrome profiles on ports 9222+ will need migration
- Running instances will need to be stopped and restarted
- Any external tools expecting port 9222 for first account will break

✅ **Verification Step**:
- We've identified all port references
- The change is straightforward: shift from 9222→9223 as base
- Port 9222 will be completely untouched
- This is the simplest approach that achieves the goal

## 3. Plan the Project Structure

### No New Files Needed
- All changes are to existing files
- No structural reorganization required
- Configuration remains in same locations

### Files to Modify:
```
src/
├── auto_login.py      # Change BASE_DEBUGGING_PORT
├── app.py             # Change default base_port
└── dashboard.py       # No changes needed

start_all.py           # Update port testing range
README.md              # Update documentation
```

## 4. Make a Simple Plan

### What to Build:
Nothing new - only configuration changes

### What to Change:
1. Shift base port from 9222 to 9223
2. Update all references to reflect new base
3. Ensure port 9222 is never touched by our code

### Port Allocation After Changes:
- **Port 9222**: PROTECTED - Never touched by Tradovate Interface
- **Port 9223**: First Tradovate account
- **Port 9224**: Second Tradovate account
- **Port 9225+**: Additional accounts
- **Port 9321**: Dashboard Chrome window (unchanged)
- **Port 6001**: Flask server (unchanged)

✅ **Verification Step**:
- This plan is minimal and direct
- No new complexity introduced
- Preserves all existing functionality
- Simply shifts port range by 1

## 5. Keep it Simple

### Simplest Approach:
- Change one constant: BASE_DEBUGGING_PORT = 9223
- Update documentation
- No new features or abstractions
- No configuration files needed

### What We're NOT Doing:
- Not adding port configuration files
- Not building port management systems
- Not adding validation layers
- Not changing the port assignment algorithm

## 6. List Clear Steps

### Implementation Steps:

1. **Update auto_login.py**
   ```python
   # Change line ~110
   BASE_DEBUGGING_PORT = 9223  # Changed from 9222
   ```

2. **Update app.py**
   ```python
   # Change TradovateController.__init__ default
   def __init__(self, base_port=9223):  # Changed from 9222
   ```

3. **Update start_all.py**
   ```python
   # In test_chrome_debugging_connections()
   base_port = 9223  # Changed from 9222
   ```

4. **Update README.md**
   - Change all references from "starting at 9222" to "starting at 9223"
   - Add note that port 9222 is reserved/protected

5. **Create Migration Instructions**
   - Document how to stop existing instances
   - Explain the port shift
   - Provide commands to verify changes

### Testing Steps:

1. Stop all Chrome instances
2. Run `start_all.py --stop-chrome` to clean up
3. Start fresh with `python3 start_all.py`
4. Verify:
   - Port 9222 remains untouched (`lsof -i :9222` shows nothing from our app)
   - First account runs on 9223
   - Dashboard still works on 6001
   - All functionality preserved

### Time Required: 10 minutes
- 5 minutes for code changes
- 5 minutes for testing

### Resources Required:
- Text editor
- Terminal for testing
- No external dependencies