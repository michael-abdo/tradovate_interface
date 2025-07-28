# AI Reference: DOM Order Investigation

## CRITICAL FACTS

### Order Execution Status
- **ORDERS ARE WORKING CORRECTLY** - No fix needed
- **FALSE POSITIVE ISSUE** - Orders returned "SUCCESS" but we were checking wrong location
- **VERIFICATION METHOD** - Check DOM position display: `.module-dom .info-column .number`
- **DO NOT CHECK** - Order tables `.module.orders` (may not update immediately)

### Canvas-Based DOM
- **TECHNOLOGY**: Tradovate uses KonvaJS canvas rendering for DOM trading
- **LIMITATION**: Cannot click HTML elements (they don't exist)
- **SELECTORS THAT DON'T WORK**: `.dom-cell-container-bid`, `.dom-cell-container-ask`, `.dom-price-cell`
- **WORKAROUND**: Use market buttons or standard order form

## USEFUL CODE ADDITIONS

### 1. State Capture Function
```javascript
window.captureOrdersState(symbol) // Returns orders, positions, DOM positions
```
**USE FOR**: Verifying order execution by comparing before/after states

### 2. State Comparison Function
```javascript
window.compareOrderStates(beforeState, afterState, expectedSymbol)
```
**RETURNS**: 
- `executionDetected`: boolean
- `confidence`: HIGH/MEDIUM/LOW/NONE
- `positionChanges`: detailed changes
- `orderChanges`: detailed changes

### 3. Testing Commands
```bash
# E2E verification
python3 docs/investigations/dom-order-fix/final_order_verification.py

# Multi-account testing
python3 docs/investigations/dom-order-fix/test_enhanced_dom_submission.py

# Execution tracing
python3 docs/investigations/dom-order-fix/trace_autoorder_execution.py
```

## DEAD CODE TO IGNORE

### submitOrderWithDOM Function
- **STATUS**: Non-functional due to canvas-based DOM
- **LOCATION**: Lines 1491-1701 in autoOrder.user.js
- **BEHAVIOR**: Always fails and falls back to standard submission
- **RECOMMENDATION**: Can be removed in future cleanup

## INFRASTRUCTURE FACTS

### Chrome Connection
- **PORTS**: 9223 (Account 1), 9224 (Account 2), 9225 (Account 3)
- **METHOD**: WebSocket via Chrome DevTools Protocol
- **NO TAMPERMONKEY**: Direct script injection only

### Script Injection
- **WHEN**: Dashboard injects scripts on startup
- **HOW**: Via `inject_tampermonkey()` function (misleading name)
- **WHERE**: Scripts in `scripts/tampermonkey/` directory

## COMMON PITFALLS

### DO NOT
- Try to click DOM price cells (canvas-based, not HTML)
- Check order tables for immediate confirmation
- Assume Tampermonkey is involved
- Create new test files without adding to .gitignore

### ALWAYS
- Check DOM position display for order verification
- Use state comparison for execution confirmation
- Test with real market hours
- Use existing test toolkit for debugging

## QUICK DIAGNOSIS

### "Orders not executing"
1. Run: `python3 docs/investigations/dom-order-fix/final_order_verification.py`
2. Check DOM positions change (not order tables)
3. If positions change = orders ARE executing

### "Can't find price cells"
- **EXPECTED**: DOM uses canvas, not HTML elements
- **SOLUTION**: Use standard submission (already works)

### "Script not loaded"
1. Check if dashboard is running
2. Reload page - dashboard should re-inject
3. Verify with: `typeof window.autoOrder === 'function'`

## KEY INSIGHT
Orders execute successfully through standard submission. The investigation revealed we were checking the wrong indicator (order tables vs DOM position display). No code fix was needed, only correct verification.