# CRITICAL: Order Execution Stability Assurance

## 🚨 The Most Important Rule
**ALWAYS verify orders by checking DOM position changes, NEVER trust return values alone!**

## Verification Hierarchy
1. **Primary**: `.module-dom .info-column .number` (DOM position display)
2. **Secondary**: Positions table
3. **Tertiary**: Orders table
4. **Never Rely On**: API return values alone

## Daily Checks
Run this every morning before trading:
```bash
python3 docs/investigations/dom-order-fix/final_order_verification.py
```

## Real-Time Monitoring
The following systems monitor order execution:
- **OrderValidationFramework**: Pre/post submission validation
- **PositionMonitoring**: Real-time position change detection
- **ErrorRecoveryFramework**: Automatic retry with circuit breakers

## Emergency Recovery
If orders stop working:
1. Check DOM positions are updating (not order tables)
2. Verify `typeof window.autoOrder === 'function'`
3. Run: `python3 src/utils/check_chrome.py`
4. Restart dashboard if needed

## Key Code Locations
- **Order Execution**: `scripts/tampermonkey/autoOrder.user.js`
- **Position Verification**: `window.captureOrdersState()` and `window.compareOrderStates()`
- **Health Checks**: `src/app.py` - `get_connection_health()`
- **Error Recovery**: `scripts/tampermonkey/errorRecoveryFramework.js`

## What We Learned
During the DOM investigation, we discovered:
- Orders were ALWAYS executing correctly
- We were checking the wrong place (order tables vs DOM positions)
- Tradovate uses canvas-based DOM (KonvaJS) - can't click price cells
- The system uses direct script injection, not Tampermonkey extensions

## Stability Guarantees
1. **Multi-layer validation** prevents invalid orders
2. **Position-based verification** confirms execution
3. **Circuit breakers** prevent cascade failures
4. **Comprehensive logging** enables debugging
5. **Retry mechanisms** handle transient issues

## Never Break These Rules
1. Always verify positions changed after orders
2. Use existing code - follow DRY principles
3. Log everything for root cause analysis
4. Test with real data to fail fast
5. Never create new files unless absolutely necessary

Last verified working: 2025-07-28