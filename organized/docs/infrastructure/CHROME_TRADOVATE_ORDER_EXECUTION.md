# Chrome Management & Tradovate Interface: Order Execution Infrastructure

## 🏗️ Infrastructure Component
**Component**: Chrome DevTools Protocol + Tradovate Web Interface  
**Category**: Core Trading Infrastructure  
**Criticality**: CRITICAL - Orders depend on this  
**Last Verified**: 2025-07-28

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [The Golden Rule](#the-golden-rule)
3. [Infrastructure Architecture](#infrastructure-architecture)
4. [Daily Operations](#daily-operations)
5. [Monitoring & Health Checks](#monitoring--health-checks)
6. [Troubleshooting Guide](#troubleshooting-guide)
7. [Emergency Procedures](#emergency-procedures)
8. [Technical Details](#technical-details)

---

## Overview

This document covers the **Chrome-Tradovate order execution infrastructure** - the critical layer that ensures trading orders execute correctly through our automated Chrome browser instances.

### Key Components:
- **Chrome Instances**: 3 dedicated Chrome browsers (ports 9223, 9224, 9225)
- **Chrome DevTools Protocol**: WebSocket connections for browser control
- **Script Injection**: Direct JavaScript injection (NOT Tampermonkey extension)
- **Order Verification**: Position-based verification system

---

## 🏆 The Golden Rule

```javascript
// ALWAYS verify orders by checking DOM position changes
// NEVER trust API return values alone!

// ✅ CORRECT - Check DOM positions:
const position = document.querySelector('.module-dom .info-column .number')?.textContent;

// ❌ WRONG - Don't check order tables:
const orders = document.querySelector('.module.orders');  // May not update immediately
```

### Why This Matters
During our investigation, we discovered orders were **always executing correctly**, but we were checking the wrong place for confirmation. The DOM position display is the source of truth.

---

## Infrastructure Architecture

### Chrome Management Layer
```
┌─────────────────────────────────────────────┐
│           Chrome Management Layer            │
├─────────────────────────────────────────────┤
│  Port 9223: Account 1 (Primary)             │
│  Port 9224: Account 2 (Copy)                │
│  Port 9225: Account 3 (APEX/Copy)           │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│        Chrome DevTools Protocol              │
├─────────────────────────────────────────────┤
│  WebSocket Connections                       │
│  Script Injection (autoOrder.user.js)        │
│  Console Interception                        │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│         Tradovate Web Interface              │
├─────────────────────────────────────────────┤
│  Canvas-based DOM (KonvaJS)                  │
│  Position Display (.module-dom)              │
│  Order Execution via autoOrder()             │
└─────────────────────────────────────────────┘
```

### Key Infrastructure Files
- **Chrome Startup**: `/Users/Mike/Desktop/programming/1_proposal_automation/3_submit_proposal/chrome_management/start_chrome_debug.sh`
- **Connection Management**: `src/app.py` (TradovateConnection class)
- **Script Injection**: `inject_tampermonkey()` method (misleading name - uses DevTools, not extension)
- **Order Execution**: `scripts/tampermonkey/autoOrder.user.js`

---

## Daily Operations

### 1. Morning Checklist (Before Market Open)
```bash
# Verify order execution is working
python3 docs/investigations/dom-order-fix/final_order_verification.py

# Expected output:
# ✅ ✅ ✅ SUCCESS! ORDERS ARE EXECUTING SUCCESSFULLY! ✅ ✅ ✅
```

### 2. Start Trading Infrastructure
```bash
# This starts Chrome, logs in, and injects scripts automatically
./start_all.py --ngrok

# Verify all systems running:
# - Chrome on ports 9223, 9224, 9225
# - Dashboard at http://localhost:6001
# - Scripts injected into all accounts
```

### 3. Continuous Monitoring (During Trading)
```bash
# Run the order execution monitor
python3 src/utils/order_execution_monitor.py

# This checks every 5 minutes that:
# - Orders execute successfully
# - Positions update correctly
# - All accounts are healthy
```

---

## Monitoring & Health Checks

### Real-Time Health Indicators

#### 1. Dashboard Status Panel
- Navigate to http://localhost:6001
- Check "Connection Status" for all accounts
- All should show "Connected" with green indicators

#### 2. Position Verification
```javascript
// In browser console (F12) on any Tradovate tab:
window.captureOrdersState('NQ').then(state => {
    console.log('Current NQ position:', state.domPositions.NQ || '0');
});
```

#### 3. Script Loading Verification
```javascript
// Check if order execution script is loaded:
console.log('autoOrder loaded:', typeof window.autoOrder === 'function');
// Should output: autoOrder loaded: true
```

### Automated Monitoring Systems

1. **OrderValidationFramework** - Pre/post submission validation
2. **ErrorRecoveryFramework** - Automatic retry with circuit breakers
3. **PositionMonitoring** - Real-time position change detection
4. **Console Interceptor** - Captures all browser console output

---

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. "Orders Not Executing"
**Symptom**: Orders return success but positions don't change  
**Solution**:
```bash
# First, verify what you're checking:
# ✅ Check: .module-dom .info-column .number (DOM positions)
# ❌ NOT: .module.orders (order tables)

# Run verification:
python3 docs/investigations/dom-order-fix/final_order_verification.py
```

#### 2. "Script Not Loaded"
**Symptom**: `window.autoOrder` is undefined  
**Solution**:
```bash
# Restart dashboard to reinject scripts
pkill -f dashboard.py
python src/dashboard.py
```

#### 3. "Chrome Connection Lost"
**Symptom**: Dashboard shows disconnected  
**Solution**:
```bash
# Check Chrome is running
python3 src/utils/check_chrome.py

# Restart if needed
./start_all.py
```

#### 4. "DOM Not Updating"
**Symptom**: Positions don't change after orders  
**Cause**: Tradovate uses canvas-based rendering (KonvaJS)  
**Solution**: This is normal - the DOM fix doesn't work, but standard submission does

### Infrastructure Health Checks

```bash
# 1. Check all Chrome instances
curl -s http://localhost:9223/json/list | jq '.[0].title'
curl -s http://localhost:9224/json/list | jq '.[0].title'
curl -s http://localhost:9225/json/list | jq '.[0].title'

# 2. Check WebSocket connections
python3 -c "
from src.app import TradovateConnection
conn = TradovateConnection('test', 9223)
print('Connected:', conn.connect())
"

# 3. Verify script injection
python3 -c "
from src.app import TradovateConnection
conn = TradovateConnection('test', 9223)
conn.connect()
result = conn.tab.Runtime.evaluate(expression='typeof window.autoOrder')
print('autoOrder loaded:', result.get('result', {}).get('value') == 'function')
"
```

---

## Emergency Procedures

### 🚨 When Orders Stop Working

#### Step 1: Run Emergency Diagnostics
```bash
python3 src/utils/emergency_order_recovery.py

# This will:
# - Check all Chrome connections
# - Verify script injection
# - Test order execution
# - Provide specific recovery steps
```

#### Step 2: Manual Recovery Steps
If automated recovery fails:

1. **Restart Everything**
   ```bash
   # Stop all services
   pkill -f chrome
   pkill -f dashboard
   
   # Restart
   ./start_all.py
   ```

2. **Verify Tradovate Login**
   - Check each Chrome instance is logged in
   - Look for session timeouts

3. **Check Market Hours**
   - Orders won't execute outside market hours
   - Check for holidays/early closes

4. **Last Resort - Full Reset**
   ```bash
   # Clear Chrome profiles and restart
   rm -rf /tmp/chrome-*
   ./start_all.py
   ```

### Recovery Validation
After any recovery action:
```bash
# Always verify orders work again
python3 docs/investigations/dom-order-fix/final_order_verification.py
```

---

## Technical Details

### Chrome DevTools Protocol Integration

#### Connection Flow
1. Chrome starts with `--remote-debugging-port=922X`
2. Python connects via WebSocket to `ws://localhost:922X/devtools/page/XXX`
3. Scripts injected using `Runtime.evaluate`
4. Orders executed via injected `autoOrder()` function

#### Script Injection Process
```python
# From src/app.py - inject_tampermonkey() method
# Despite the name, this does NOT use Tampermonkey extension!

1. Load console_interceptor.js     # Captures console output
2. Load autoOrder.user.js          # Main trading functions  
3. Load getAllAccountTableData.js  # Account data extraction
```

### Order Execution Flow

1. **User/Bot Triggers Order**
   ```python
   connection.auto_trade('NQ', quantity=1, action='Buy')
   ```

2. **Chrome Executes JavaScript**
   ```javascript
   window.autoOrder('NQ', 1, 'Buy', 20, 10, 0.25)
   ```

3. **Order Submission Path**
   - Attempts DOM click (fails due to canvas)
   - Falls back to standard submission (works)
   - Updates Tradovate interface

4. **Verification**
   - Check DOM position display changes
   - NOT order tables (may lag)

### Canvas-Based DOM Limitation

Tradovate uses **KonvaJS** for canvas rendering:
- Price ladder is drawn on canvas, not HTML
- Cannot click DOM elements (they don't exist)
- `submitOrderWithDOM()` always fails
- Standard submission works perfectly

### Key Code Locations

| Component | File | Purpose |
|-----------|------|---------|
| Chrome Management | `src/app.py` | Connection and script injection |
| Order Execution | `scripts/tampermonkey/autoOrder.user.js` | Main trading logic |
| Position Verification | `window.captureOrdersState()` | State tracking |
| Error Recovery | `scripts/tampermonkey/errorRecoveryFramework.js` | Retry logic |
| Monitoring | `src/utils/order_execution_monitor.py` | Continuous health checks |
| Emergency Recovery | `src/utils/emergency_order_recovery.py` | Diagnostic and fixes |

---

## Best Practices

### DO ✅
- Always verify positions changed after orders
- Check DOM display (`.module-dom .info-column .number`)
- Run morning verification before trading
- Monitor continuously during market hours
- Use existing verification tools

### DON'T ❌
- Don't check order tables for immediate confirmation
- Don't trust API return values alone
- Don't try to click DOM price cells (canvas-based)
- Don't create new verification methods
- Don't modify core order execution without extensive testing

---

## Maintenance Schedule

### Daily
- Morning order verification test
- Start continuous monitoring during trading

### Weekly
- Review error logs for patterns
- Check Chrome memory usage
- Verify all accounts executing trades

### Monthly
- Update Chrome if needed
- Review and test emergency procedures
- Archive old diagnostic logs

---

## Contact & Escalation

### Issues Requiring Immediate Action
- Multiple order execution failures
- All accounts disconnected
- Chrome crashes during market hours

### Log Locations
- Order execution logs: `logs/order_execution_failures.log`
- Emergency diagnostics: `logs/emergency_diagnostic_*.json`
- Chrome console logs: Captured in real-time by dashboard

---

*This document is part of the Trading Infrastructure Documentation. For general Chrome management, see `CHROME_MANAGEMENT.md`. For Tradovate-specific features, see `TRADOVATE_INTERFACE.md`.*