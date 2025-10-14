# Order Feedback Extraction Test Plan

## Overview
This document outlines test scenarios for verifying the enhanced order feedback extraction functionality. The system now captures comprehensive order data including prices, fills, timing, costs, and verification details.

## Test Scenarios

### 1. Market Order - Single Fill
**Test Steps:**
1. Place a MARKET order for 1 contract
2. Verify extraction captures:
   - Order type: MARKET
   - Fill price
   - Timing metrics (submission to fill)
   - No price comparison (market orders have no requested price)

**Expected Output:**
- Order type correctly identified as MARKET
- Single fill event with price
- Timing shows rapid execution (<1000ms typical)
- Verification report shows "SUCCESS"

### 2. Limit Order - Complete Fill
**Test Steps:**
1. Place a LIMIT order at current bid/ask
2. Verify extraction captures:
   - Order type: LIMIT
   - Requested price vs fill price
   - Price improvement calculation
   - Fill ratio shows complete (e.g., "5/5")

**Expected Output:**
- Price comparison section populated
- Shows BETTER_THAN_REQUESTED, WORSE_THAN_REQUESTED, or FILLED_AT_REQUESTED
- Fill ratio shows 100%

### 3. Limit Order - Partial Fill
**Test Steps:**
1. Place a large LIMIT order away from market
2. Cancel after partial fill
3. Verify extraction captures:
   - Partial fill ratio (e.g., "3/10")
   - Multiple fill events with individual prices
   - Average fill price calculation

**Expected Output:**
- Fill ratio shows partial percentage
- Individual fills listed with timestamps
- Report shows "⚠️ PARTIAL FILL"

### 4. Bracket Order
**Test Steps:**
1. Place order with both TP and SL enabled
2. Verify extraction captures:
   - Main order ID
   - Stop loss order ID
   - Take profit order ID
   - All three orders in bracket orders array

**Expected Output:**
- Bracket orders section populated
- Separate order IDs for SL and TP
- Console shows "BRACKET ORDERS FOUND: 2 orders"

### 5. Market Order - Multiple Fills (Slippage Test)
**Test Steps:**
1. Place large MARKET order (10+ contracts)
2. Verify extraction captures:
   - Multiple fill prices
   - Slippage calculation (price range)
   - Fill range in ticks

**Expected Output:**
- Slippage section shows price range
- Min/max fill prices displayed
- Tick calculation based on symbol

### 6. Rejected Order - Outside Market Hours
**Test Steps:**
1. Place order when market is closed
2. Verify extraction captures:
   - Rejection reason
   - Order status as REJECTED
   - No fill events

**Expected Output:**
- Status shows "❌ FAILED"
- Rejection reason: "Order placed outside market hours"
- No price or fill information

### 7. Order with Fees/Commission
**Test Steps:**
1. Place order on live account
2. Verify extraction captures:
   - Commission amount
   - Exchange fees
   - Total cost calculation

**Expected Output:**
- Costs section populated (if fees present in events)
- Commission and fees itemized
- Total cost calculated

## Console Commands for Testing

```javascript
// Test MARKET order
autoTrade('NQ', 1, 'Buy', 0, 0, 0.25, 'MARKET');

// Test LIMIT order
autoTrade('NQ', 1, 'Buy', 0, 0, 0.25, 'LIMIT');

// Test bracket order
autoTrade('NQ', 1, 'Buy', 50, 20, 0.25);

// Access last feedback result
console.log(captureOrderFeedback.lastResult);
```

## Verification Report Example

```
📊 ════════════════ ORDER VERIFICATION REPORT ════════════════

🔸 ORDER DETAILS:
   Order ID: 289076630758
   Type: LIMIT
   Action: Buy 5 units
   Status: ✅ SUCCESS

🔸 PRICE VERIFICATION:
   Requested: 24825.50
   Filled: 24824.00
   Difference: -1.50 (-0.006%)
   Result: BETTER_THAN_REQUESTED

🔸 FILL INFORMATION:
   Fill Ratio: 5/5 (100.00%)
   Status: ✅ COMPLETE FILL
   Individual Fills:
     1. 5 @ 24824.00 (09/24/2025 9:49:09 AM)

🔸 EXECUTION TIMING:
   Time to Fill: 245ms
   Risk Check: 12ms
   Total Duration: 267ms

══════════════════════════════════════════════════════════
```

## Logging and Debugging

All enhanced extraction data is logged to:
- Chrome console with `📊` prefix
- Chrome log files in `logs/` directory
- Order feedback HTML captured in full

To view comprehensive feedback data:
1. Open Chrome DevTools Console
2. Look for logs starting with `📊 ORDER FEEDBACK`
3. Check `feedbackResult` object for all extracted data

## Success Criteria

✅ All order types correctly identified
✅ Fill prices accurately extracted
✅ Price comparisons calculated for limit orders
✅ Timing metrics captured for all orders
✅ Partial fills properly tracked
✅ Bracket orders identified and linked
✅ Comprehensive report generated
✅ All data logged for analysis