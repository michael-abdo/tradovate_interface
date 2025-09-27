# Market Order Auto-Detection Implementation Plan

## Problem Statement

**Current Issue:** Entry price values persist between trades, causing market orders to unintentionally execute as limit orders at stale prices.

**User Impact:** When users place a limit order and then want to place a market order, they must manually clear the entry price field or the next order will use the old limit price instead of executing at market.

## Root Cause Analysis

### Current Code Flow
1. **Dashboard UI** (`dashboard.html`) collects trade parameters
2. **Flask API** (`src/dashboard.py`) forwards to Chrome injection  
3. **AutoOrder Script** (`autoOrder.user.js`) executes the actual trade

### The Logic Already Works Correctly

**Dashboard Logic (Lines 2188, 2238-2240):**
```javascript
const entryPrice = document.getElementById('entryPriceInput').value || null;

// Only send entry_price parameter when field has a value
if (entryPrice) {
    tradeParams.entry_price = entryPrice;
}
```

**AutoOrder Logic (Lines 1079-1094):**
```javascript
if (customEntryPrice !== null) {
    // LIMIT or STOP order based on price vs market comparison
    orderType = customEntryPrice < marketPrice ? 'LIMIT' : 'STOP';
} else {
    // MARKET order at current bid/offer price
    orderType = 'MARKET';
}
```

### The Real Problem

The issue is **UI state management**, not API logic:
- Entry price field retains old values between trades
- No visual indication of current order type (market vs limit)
- Users don't realize they need to clear the field manually

## Proposed Solution: Auto-Clear + Visual Feedback

### Design Principles
- ✅ **Minimal changes** - No new UI elements needed
- ✅ **Zero backend changes** - API already handles this correctly  
- ✅ **Preserve existing behavior** - Don't break current functionality
- ✅ **Clear user intent** - Make order type obvious

### Implementation Plan

#### 1. Auto-Clear Entry Price After Trades
**Location:** `web/templates/dashboard.html` - executeTradeAction function
**Change:** Modify success callback to clear entry price field

```javascript
.then(result => {
    // Existing success handling...
    
    // Auto-clear entry price for next trade
    document.getElementById('entryPriceInput').value = '';
    
    // Existing reset logic for TP/SL prices...
})
```

#### 2. Visual Order Type Indicator
**Location:** Near entry price input field
**Implementation:** Dynamic text that updates based on field state

```javascript
// Add event listener to entry price input
document.getElementById('entryPriceInput').addEventListener('input', function() {
    const orderTypeDisplay = document.getElementById('orderTypeDisplay');
    const entryPrice = this.value.trim();
    
    if (entryPrice) {
        orderTypeDisplay.textContent = `Limit Order @ $${entryPrice}`;
        orderTypeDisplay.className = 'order-type-indicator limit';
    } else {
        orderTypeDisplay.textContent = 'Market Order';
        orderTypeDisplay.className = 'order-type-indicator market';
    }
});
```

#### 3. Enhanced Placeholder Text
**Location:** Entry price input field
**Change:** More descriptive placeholder

```html
<input type="number" id="entryPriceInput" step="0.01" 
       class="trade-input" 
       placeholder="Leave empty for Market Order">
```

### Files Modified
- `web/templates/dashboard.html` - Add auto-clear logic and visual indicator
- No backend changes required
- No new files needed

### Testing Plan
1. **Market Order Test:**
   - Ensure entry price field is empty
   - Place Buy/Sell order
   - Verify order executes at current market price
   - Confirm field remains empty after trade

2. **Limit Order Test:**
   - Enter specific price in entry price field
   - Place Buy/Sell order  
   - Verify order executes as limit order at specified price
   - Confirm field auto-clears after successful trade

3. **Transition Test:**
   - Place limit order with specific price
   - Verify field auto-clears after trade
   - Place immediate market order
   - Confirm market order executes at market price (not old limit price)

### User Experience Improvements

**Before:**
- User places limit order at $19,000
- User wants next order to be market order
- User forgets to clear entry price field
- Next order executes as limit order at $19,000 (wrong!)

**After:**  
- User places limit order at $19,000
- Entry price field automatically clears after successful trade
- User sees "Market Order" indicator
- Next order automatically executes at market price (correct!)

### Risk Assessment

**Low Risk Implementation:**
- No breaking changes to existing functionality
- Backward compatible with current behavior
- Only adds automatic cleanup and visual feedback
- Can be easily reverted if issues arise

**Benefits:**
- Eliminates "stuck price" problem completely
- Reduces user error and confusion  
- Maintains simple, intuitive interface
- No additional complexity for users

## Alternative Solutions Considered

### Option 1: Order Type Selector (Rejected)
- **Pros:** Explicit user choice
- **Cons:** Adds UI complexity, extra click required
- **Decision:** Overly complex for this use case

### Option 2: Backend Order Type Detection (Rejected)  
- **Pros:** Server-side validation
- **Cons:** Unnecessary when client logic already works
- **Decision:** No backend changes needed

### Option 3: Auto-Clear + Visual Feedback (Selected)
- **Pros:** Minimal, intuitive, preserves existing behavior
- **Cons:** None identified
- **Decision:** Optimal balance of simplicity and effectiveness

## Implementation Timeline

**Phase 1:** Auto-clear functionality (15 minutes)
**Phase 2:** Visual order type indicator (20 minutes)  
**Phase 3:** Enhanced placeholder text (5 minutes)
**Phase 4:** Testing and validation (15 minutes)

**Total Estimated Time:** 55 minutes

## Success Criteria

✅ Market orders (empty entry price) execute at current market price  
✅ Limit orders (specified entry price) execute at specified price  
✅ Entry price field automatically clears after successful trades  
✅ Visual indicator shows current order type clearly  
✅ No regression in existing functionality  
✅ User can seamlessly switch between market and limit orders  

## Conclusion

This solution addresses the core issue with minimal code changes and maximum user benefit. By automatically clearing the entry price field and providing clear visual feedback, we eliminate the "stuck price" problem while maintaining the existing simple interface that users are already familiar with.

The implementation leverages the fact that the underlying API logic already correctly handles market vs limit orders - we just need to ensure the UI state management supports seamless transitions between order types.