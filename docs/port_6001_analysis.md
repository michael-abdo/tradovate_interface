# Complete Step-by-Step Analysis of App Startup (commit aab56b3)

## The Problem: Port 6001 "Grey Overlay" Issue

### What's Happening
When you run `lsof -i :6001`, you see multiple connections in CLOSE_WAIT state. This "overlay" of dead connections is caused by Flask's development server not properly closing TCP connections.

## Step-by-Step Startup Sequence

### 1. **start_all.py execution begins**
- Creates log directory
- Registers cleanup handlers
- Tests Chrome debugging connections (ports 9222+)

### 2. **Auto-login thread starts**
```python
auto_login_thread = threading.Thread(target=run_auto_login)
auto_login_thread.start()
```
- This launches Chrome instances for each account
- Chrome instances start on ports 9222, 9223, etc.
- Auto-login logs into Tradovate

### 3. **Wait 15 seconds**
```python
time.sleep(args.wait)  # default: 15 seconds
```
- Gives Chrome time to start and login to complete

### 4. **run_dashboard() is called**
- Creates a new thread for Flask:
```python
dashboard_thread = threading.Thread(target=start_flask)
dashboard_thread.start()
```

### 5. **THE CRITICAL MOMENT - Dashboard import**
When `start_flask()` runs, it does:
```python
from src.dashboard import run_flask_dashboard
```

### 6. **dashboard.py module initialization**
During import, at the **module level**, this executes:
```python
# Line 20 - THIS IS THE PROBLEM!
controller = TradovateController()
```

### 7. **TradovateController initialization**
```python
def __init__(self, base_port=9222):
    self.base_port = base_port
    self.connections = []
    self.initialize_connections()
```

### 8. **initialize_connections() tries to connect**
```python
def initialize_connections(self, max_instances=10):
    for i in range(max_instances):
        port = self.base_port + i  # 9222, 9223, 9224...
        try:
            connection = TradovateConnection(port, f"Account {i+1}")
```

### 9. **TradovateConnection tries to find Chrome tabs**
- Uses pychrome to connect to `http://127.0.0.1:9222`
- Lists all tabs
- Looks for Tradovate tabs
- If successful, injects Tampermonkey scripts

## The Timing Problem

**The issue**: There's a race condition!
- Chrome instances are starting in a separate thread
- Dashboard import happens after only 15 seconds
- If Chrome isn't fully started or logged in yet, the controller initialization fails

## Why This Causes "Grey Overlay"

1. **If Chrome isn't ready**: Controller initialization might partially fail
2. **Flask still starts**: Because the app continues even if controller fails
3. **Connections are unstable**: Half-initialized connections lead to CLOSE_WAIT states
4. **Debug mode makes it worse**: `debug=True` in the main block keeps bad connections alive

## TCP Connection Lifecycle

### Normal flow:
```
Client → FIN → Server (connection closing)
Server → ACK → Client (acknowledged)
Server → FIN → Client (server closes too)
Client → ACK → Server (fully closed)
```

### Problem flow (CLOSE_WAIT):
```
Client → FIN → Server (Chrome closes connection)
Server → ACK → Client (Flask acknowledges)
... Server never sends FIN ... (Flask doesn't close its end)
Connection stuck in CLOSE_WAIT state
```

## How Connections "Overlay"

Each time Chrome refreshes or makes a new request:
1. Chrome opens new connection to 6001
2. Chrome finishes request, sends FIN
3. Flask acknowledges but doesn't close its socket
4. Connection stays in CLOSE_WAIT
5. Repeat → Multiple dead connections accumulate

## Solutions Applied

### Commit 222dea4: Lazy Initialization
- Changed from module-level `controller = TradovateController()` to lazy loading
- Prevents dashboard from trying to connect during import

### Commit 0a856d2: Timeout Mechanisms
- Added timeout to `inject_account_data_function()`
- Prevents Flask from hanging if Chrome connections fail

### Commit 88d99e1: Flask Configuration
- Attempted to fix with `debug=False, threaded=True`
- Added `Connection: close` header
- But this was too aggressive and caused other issues

## Current Status
- Reverted to commit aab56b3 to understand the original working state
- Need to implement a solution that preserves functionality while fixing the overlay issue