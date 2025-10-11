# Order Verification System - Troubleshooting Guide

## Quick Diagnostic Commands

```bash
# Check Chrome instances
ps aux | grep chrome | grep remote-debugging-port

# Check connections
python3 -m src.app list

# Reload scripts
python3 reload.py

# Test function availability
python3 -c "
from src.app import TradovateConnection
conn = TradovateConnection(9222)
result = conn.tab.Runtime.evaluate(expression=\"typeof window.autoTrade\")
print(f'autoTrade available: {result.get(\"result\", {}).get(\"value\") == \"function\"}')"
```

## Common Issues and Solutions

### 1. "No Tradovate connections found"

**Symptoms:**
```
No Tradovate connections found. Make sure auto_login.py is running.
```

**Causes & Solutions:**

#### Chrome Instances Not Running
```bash
# Check if Chrome instances are running
ps aux | grep chrome | grep remote-debugging-port

# If no instances found, start them:
python3 scripts/auto_login.py
```

#### Wrong Port Range
```python
# Check if using custom port range in TradovateController
controller = TradovateController(base_port=9222)  # Default is 9223
```

#### Tradovate Not Logged In
1. Open Chrome instances manually
2. Navigate to tradovate.com
3. Log in to accounts
4. Restart the controller

**Verification:**
```bash
python3 -m src.app list
# Should show: Active Tradovate Connections: 0: Account 1 (Port 9222) ...
```

---

### 2. "autoTrade is not a function"

**Symptoms:**
```
❌ autoTrade is not a function
❌ TypeError: window.autoTrade is not a function
```

**Causes & Solutions:**

#### Scripts Not Injected
```bash
# Reload Tampermonkey scripts
python3 reload.py

# Verify injection worked
python3 -c "
from src.app import TradovateConnection
conn = TradovateConnection(9222)
if conn.tab:
    result = conn.tab.Runtime.evaluate(expression='typeof window.autoTrade')
    print(f'autoTrade type: {result.get(\"result\", {}).get(\"value\")}')
"
```

#### Script Injection Errors
Check for syntax errors in autoOrder.user.js:
```bash
# Look for JavaScript errors during injection
python3 -c "
from src.app import TradovateConnection
conn = TradovateConnection(9222)
conn.inject_tampermonkey()
"
```

Common fixes in autoOrder.user.js:
- Missing semicolons after function definitions
- Variable redeclaration errors
- Scoping issues

#### IIFE Wrapper Issues
The extract_core_functions may not be properly removing the IIFE:
```python
# Check extracted code (in app.py)
print(tampermonkey_functions[:200])  # Should not start with "(function()"
```

**Verification:**
```javascript
// In browser console:
typeof window.autoTrade         // Should return "function"
typeof window.auto_trade_scale  // Should return "function"
typeof window.waitForOrderFeedback  // Should return "function"
```

---

### 3. "Order history not found"

**Symptoms:**
```
❌ Order verification failed: Order history not found
waitForOrderFeedback timed out after 10000ms
```

**Root Cause:** This is the primary known issue - orders aren't being placed by `createBracketOrdersManual`

**Immediate Solutions:**

#### Verify Order Placement Function
```javascript
// In browser console, test order placement directly:
createBracketOrdersManual('NQ', 1, 'Buy', 15200, 15300, 15150);

// Check if orders appear in Tradovate order history manually
```

#### Check Symbol Input
```javascript
// Verify symbol input is working:
updateSymbol('.trading-ticket .search-box--input', 'NQ');

// Check if symbol appears in trading interface
```

#### Verify Tradovate UI State
1. Ensure trading ticket is visible and active
2. Check account has sufficient buying power
3. Verify market is open for the symbol
4. Check if symbol exists and is tradeable

**Long-term Investigation:**

1. Debug `createBracketOrdersManual` step by step
2. Check DOM selectors for Tradovate UI elements
3. Verify click events are properly triggered
4. Check for Tradovate UI changes that broke automation

**Workaround:**
The verification system is working correctly - it properly detects that orders aren't being placed. Focus on fixing the order placement mechanism rather than the verification system.

---

### 4. Promise/Timeout Errors

**Symptoms:**
```
Promise timed out after 15000ms
awaitPromise failed
```

**Causes & Solutions:**

#### Increase Timeout for Complex Operations
```python
# For scale orders, increase timeout
timeout_ms = 15000 + (len(scale_orders) * 2000)  # 2s per order instead of 1s
result = self.tab.Runtime.evaluate(
    expression=js_code, 
    awaitPromise=True, 
    timeout=timeout_ms
)
```

#### Check JavaScript Promise Resolution
```javascript
// Test promise manually in browser console:
autoTrade('NQ', 1, 'Buy', 100, 40, 0.25)
  .then(result => console.log('Promise resolved:', result))
  .catch(error => console.error('Promise rejected:', error));
```

#### Verify waitForOrderFeedback Logic
```javascript
// Test feedback waiting manually:
waitForOrderFeedback(15000)
  .then(() => console.log('Order feedback detected'))
  .catch(error => console.error('Feedback timeout:', error));
```

**Prevention:**
- Use appropriate timeouts based on operation complexity
- Monitor JavaScript console for promise-related errors
- Test promise resolution independently

---

### 5. Chrome DevTools Communication Errors

**Symptoms:**
```
pychrome.exceptions.CallMethodException
WebSocketConnectionClosed
```

**Causes & Solutions:**

#### Chrome Instance Crashed
```bash
# Check if Chrome process is still running
ps aux | grep chrome | grep remote-debugging-port

# Restart if needed
pkill -f "chrome.*remote-debugging-port"
python3 scripts/auto_login.py
```

#### Port Conflicts
```python
# Try different port range
controller = TradovateController(base_port=9225)
```

#### Tab Disconnected
```python
# Refresh connection
connection = TradovateConnection(port=9222)
connection.find_tradovate_tab()  # Re-find the tab
connection.inject_tampermonkey()  # Re-inject scripts
```

**Recovery:**
```python
def robust_connection(port, max_retries=3):
    for attempt in range(max_retries):
        try:
            conn = TradovateConnection(port)
            if conn.tab:
                return conn
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            time.sleep(2)
    return None
```

---

### 6. Response Format Issues

**Symptoms:**
```
❌ No result returned from autoTrade
KeyError: 'result'
KeyError: 'value'
```

**Causes & Solutions:**

#### Malformed JavaScript Response
```python
# Add debugging to see raw response
print(f"Raw Chrome response: {result}")

# Check response structure
if 'result' in result:
    print(f"Result field: {result['result']}")
if 'exceptionDetails' in result:
    print(f"JavaScript error: {result['exceptionDetails']}")
```

#### Promise Not Properly Awaited
```python
# Ensure awaitPromise=True is used
result = self.tab.Runtime.evaluate(
    expression=js_code, 
    awaitPromise=True,  # ← Essential for promise-returning functions
    timeout=15000
)
```

#### JavaScript Function Returning Undefined
```javascript
// Check function return values in browser console:
autoTrade('NQ', 1, 'Buy', 100, 40, 0.25);
// Should log the promise and eventually resolve with data
```

**Debugging:**
```python
def debug_response(result):
    print("=== Chrome DevTools Response Debug ===")
    print(f"Type: {type(result)}")
    print(f"Keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
    if isinstance(result, dict):
        for key, value in result.items():
            print(f"{key}: {type(value)} = {value}")
    print("=" * 40)
```

---

### 7. Multi-Account Issues

**Symptoms:**
```
Some accounts succeed, others fail consistently
Mixed success/failure rates
```

**Causes & Solutions:**

#### Account-Specific Issues
```python
# Test each account individually
for i, conn in enumerate(controller.connections):
    print(f"Testing account {i}...")
    result = conn.auto_trade('NQ', 1, 'Buy', 100, 40, 0.25)
    print(f"  Result: {result.get('success', False)}")
```

#### Different Account States
- Check if all accounts are logged in
- Verify buying power across accounts
- Check for account-specific restrictions
- Ensure all accounts have active trading permissions

#### Script Injection Inconsistencies
```python
# Re-inject scripts on all accounts
for conn in controller.connections:
    conn.inject_tampermonkey()
    print(f"Re-injected scripts for {conn.account_name}")
```

---

## Debugging Tools

### JavaScript Console Debugging

```javascript
// Enable verbose logging
window.debugMode = true;

// Test function availability
console.log('Functions available:', {
    autoTrade: typeof window.autoTrade,
    auto_trade_scale: typeof window.auto_trade_scale,
    waitForOrderFeedback: typeof window.waitForOrderFeedback,
    captureOrderFeedback: typeof window.captureOrderFeedback
});

// Test order capture
console.log('Order feedback test:', captureOrderFeedback());

// Test manual order placement
createBracketOrdersManual('NQ', 1, 'Buy', 15200, 15300, 15150);
```

### Python Debugging

```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test connection step by step
from src.app import TradovateConnection

conn = TradovateConnection(port=9222, account_name="Debug")
print(f"Tab available: {conn.tab is not None}")

if conn.tab:
    # Test basic JavaScript execution
    result = conn.tab.Runtime.evaluate(expression="'test'")
    print(f"Basic JS test: {result}")
    
    # Test function injection
    conn.inject_tampermonkey()
    
    # Test function availability
    result = conn.tab.Runtime.evaluate(expression="typeof window.autoTrade")
    print(f"autoTrade available: {result}")
```

### Chrome DevTools Manual Testing

1. Open Chrome Developer Tools (F12)
2. Go to Console tab
3. Test functions manually:
```javascript
// Test order placement
createBracketOrdersManual('NQ', 1, 'Buy', 15200, 15300, 15150);

// Test verification functions
waitForOrderFeedback().then(console.log).catch(console.error);
captureOrderFeedback();

// Test full flow
autoTrade('NQ', 1, 'Buy', 100, 40, 0.25).then(console.log).catch(console.error);
```

---

## Performance Troubleshooting

### Slow Order Execution

**Symptoms:** Orders taking longer than expected to execute

**Solutions:**
```python
# Profile execution time
import time

start = time.time()
result = connection.auto_trade('NQ', 1, 'Buy', 100, 40, 0.25)
duration = time.time() - start
print(f"Execution time: {duration:.2f}s")

# Optimize timeouts
if duration > 10:
    print("Consider increasing timeout or investigating order placement delays")
```

### Memory Issues

**Symptoms:** Chrome instances becoming unresponsive

**Solutions:**
```bash
# Monitor Chrome memory usage
ps aux | grep chrome | awk '{print $4, $11}' | sort -nr

# Restart Chrome instances if memory usage too high
pkill -f "chrome.*remote-debugging-port"
python3 scripts/auto_login.py
```

---

## Recovery Procedures

### Complete System Reset

```bash
#!/bin/bash
# reset_system.sh

echo "🔄 Performing complete system reset..."

# Kill all Chrome instances
pkill -f "chrome.*remote-debugging-port" || true

# Wait for processes to terminate
sleep 5

# Restart Chrome instances
python3 scripts/auto_login.py &
sleep 10

# Reload scripts
python3 reload.py

# Test connections
python3 -m src.app list

echo "✅ System reset complete"
```

### Partial Recovery (Keep Chrome, Reload Scripts)

```bash
# Quick script reload without restarting Chrome
python3 reload.py

# Verify functions are available
python3 -c "
from src.app import TradovateController
controller = TradovateController()
for i, conn in enumerate(controller.connections):
    result = conn.tab.Runtime.evaluate(expression='typeof window.autoTrade')
    func_available = result.get('result', {}).get('value') == 'function'
    print(f'Account {i}: autoTrade {\"✅\" if func_available else \"❌\"}')
"
```

---

## Escalation Procedures

### When to Investigate createBracketOrdersManual

**Symptoms:**
- Consistent "Order history not found" errors
- Verification system working but no orders appearing
- Manual order placement in Tradovate works fine

**Investigation Steps:**
1. Check DOM selectors in createBracketOrdersManual function
2. Verify Tradovate UI hasn't changed structure
3. Test order placement step-by-step in browser console
4. Check for new Tradovate security measures blocking automation

### When to Contact Support

**Symptoms that indicate deeper issues:**
- Chrome DevTools consistently failing to connect
- JavaScript injection failing across all accounts
- Verification system not detecting successfully placed orders
- Consistent crashes or memory issues

**Information to Provide:**
- Chrome version and flags used
- Tradovate account types (demo/live)
- Complete error logs
- Steps to reproduce the issue
- System specifications and OS version

---

## Prevention Best Practices

### Regular Maintenance

```bash
# Weekly maintenance script
#!/bin/bash

# Clear Chrome cache and restart
pkill -f "chrome.*remote-debugging-port"
rm -rf ~/.cache/google-chrome/Default/Cache/*
python3 scripts/auto_login.py &
sleep 15

# Update and reload scripts
python3 reload.py

# Run health check
python3 tests/run_all_tests.py
```

### Monitoring

```python
# health_check.py - Run periodically
from src.app import TradovateController
import time

def health_check():
    controller = TradovateController()
    
    if len(controller.connections) == 0:
        print("❌ No connections available")
        return False
    
    # Test each connection
    healthy_connections = 0
    for i, conn in enumerate(controller.connections):
        try:
            result = conn.tab.Runtime.evaluate(expression="typeof window.autoTrade")
            if result.get('result', {}).get('value') == 'function':
                healthy_connections += 1
                print(f"✅ Account {i}: Healthy")
            else:
                print(f"❌ Account {i}: Functions not available")
        except Exception as e:
            print(f"❌ Account {i}: Connection error - {e}")
    
    health_rate = healthy_connections / len(controller.connections)
    print(f"Overall health: {health_rate*100:.1f}% ({healthy_connections}/{len(controller.connections)})")
    
    return health_rate > 0.8  # 80% healthy threshold

if __name__ == "__main__":
    health_check()
```

This troubleshooting guide provides comprehensive solutions for the most common issues encountered with the order verification system while maintaining the "browser as source of truth" principle.