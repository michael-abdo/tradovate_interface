# Manual Verification Guide: DOM Order Fix

## Quick Steps to Verify Orders are Now Executing

### 1. Open Tradovate in Chrome
- Open Chrome instance on port 9223 (Account 1)
- Navigate to Tradovate if not already there
- Log in if needed

### 2. Switch to DOM Trading View
- **IMPORTANT**: Make sure the DOM (Depth of Market) trading module is visible
- You should see the price ladder with bid/ask prices

### 3. Open Browser Console
- Press F12 to open DevTools
- Go to Console tab

### 4. Test Current State (Paste this first)
```javascript
// Check if DOM is visible and autoOrder is loaded
console.log('DOM visible:', !!document.querySelector('.module.module-dom'));
console.log('autoOrder loaded:', typeof window.autoOrder === 'function');
```

### 5. Run Order Execution Test (Paste this)
```javascript
// Test order execution with state tracking
(async () => {
    console.log('Starting order execution test...');
    
    // Capture before state
    const before = await window.captureOrdersState('NQU5');
    console.log('Before:', before.ordersCount, 'orders,', before.positionsCount, 'positions');
    
    // Execute order
    console.log('Submitting order...');
    const result = await window.autoOrder('NQ', 1, 'Buy', 20, 10, 0.25);
    console.log('Order result:', result);
    
    // Wait 3 seconds
    await new Promise(r => setTimeout(r, 3000));
    
    // Capture after state
    const after = await window.captureOrdersState('NQU5');
    console.log('After:', after.ordersCount, 'orders,', after.positionsCount, 'positions');
    
    // Check if order executed
    if (after.ordersCount > before.ordersCount || after.positionsCount !== before.positionsCount) {
        console.log('✅ SUCCESS! Order EXECUTED!');
    } else {
        console.log('❌ Order did NOT execute');
    }
})();
```

## Expected Results

### ✅ With DOM Fix (Current):
```
Before: 0 orders, 0 positions
Submitting order...
Order result: true
After: 1 orders, 1 positions
✅ SUCCESS! Order EXECUTED!
```

### ❌ Without Fix (Previous):
```
Before: 0 orders, 0 positions
Submitting order...
Order result: SUCCESS
After: 0 orders, 0 positions
❌ Order did NOT execute
```

## What the Fix Does

1. **Clicks DOM Price Cell First** - Opens the order ticket properly
2. **Waits for Order Ticket** - Ensures UI is ready
3. **Fills and Submits** - Completes the order with proper validation

## Troubleshooting

If orders still don't execute:
1. **Check Market Hours** - Market must be open
2. **Verify DOM View** - Must see price ladder
3. **Check Console Errors** - Look for red error messages
4. **Reload Page** - Try refreshing and re-running

## Visual Confirmation

When working correctly, you should see:
1. Price cell gets clicked (brief highlight)
2. Order ticket appears as overlay/modal
3. Form fills automatically
4. Order appears in orders/positions table

## Note
This test will submit a REAL order if the market is open!