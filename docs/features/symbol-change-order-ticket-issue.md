# Symbol Change: Order Ticket vs Market Analyzer Issue

## Problem Description

When changing symbols using the modular Tampermonkey UI (`scripts/tampermonkey/modules/uiPanel.js`), the symbol update was being applied to the Market Analyzer search box instead of the Order Ticket symbol input. This caused trades to be placed with the wrong symbol or the symbol change to not affect the actual order.

**Status: FIXED** - The issue has been resolved in the split driver/UI architecture by using a more specific selector.

## Previous Behavior (INCORRECT)

The previous UI code used this selector to update symbols:
```javascript
driver.updateSymbol('.search-box--input', normalizedSymbol);
```

This selector `.search-box--input` was too generic and would target the market analyzer/watchlist search box instead of the order ticket.

## Fix Applied

Changed the selector to be more specific:
```javascript
driver.updateSymbol('.trading-ticket .search-box--input', normalizedSymbol);
```

This ensures we only target the search input within the trading ticket area.

## Root Cause Analysis

### 1. Wrong Selector
The `.search-box--input` selector is too generic and matches multiple elements on the page:
- Market Analyzer search box ✗ (currently being updated)
- Order Ticket symbol input ✓ (should be updated)
- Other search boxes on the page

### 2. Current Code Flow
```javascript
// When user changes symbol in the UI panel
document.getElementById('symbolInput').addEventListener('change', e => {
    const normalizedSymbol = normalizeSymbol(e.target.value);
    
    // This updates the WRONG element!
    driver.updateSymbol('.search-box--input', normalizedSymbol);
});
```

### 3. The updateSymbol Function (Enhanced)
The function has been improved with:
- Better selector specificity
- Fallback selectors if primary fails  
- Better debugging output
- Preferred first element (since we now use specific selectors)

```javascript
// Now uses more specific selector and has fallbacks
const input = inputs[0] || inputs[1];  // Changed to prefer first element
```

## Implemented Solution

The fix has been implemented using a combination of approaches:

We need to identify the specific selector for the order ticket symbol input. Based on the code analysis, the order ticket appears to use:

```javascript
// Look for the trading ticket container first
const tradingTicket = document.querySelector('.trading-ticket');
if (tradingTicket) {
    // Then find the symbol input within it
    const symbolInput = tradingTicket.querySelector('input[type="text"]') ||
                       tradingTicket.querySelector('.symbol-input') ||
                       tradingTicket.querySelector('.contract-input');
    
    if (symbolInput) {
        // Update this specific input
        updateSymbolDirect(symbolInput, normalizedSymbol);
    }
}
```

### Option 2: Update Multiple Symbol Locations

Update both the market analyzer AND the order ticket:

```javascript
function updateAllSymbols(symbol) {
    // Update market analyzer
    driver.updateSymbol('.search-box--input', symbol);
    
    // Update order ticket
    driver.updateSymbol('.trading-ticket input[type="text"]', symbol);
    
    // Update any other relevant symbol inputs
    driver.updateSymbol('.order-ticket-symbol', symbol);
}
```

### Option 3: Use More Specific Selectors

Instead of generic `.search-box--input`, use more specific selectors:

```javascript
// For order ticket
'.trading-ticket .search-box--input'
'.order-entry .symbol-input'
'.trade-panel .contract-search'

// For market analyzer
'.market-analyzer .search-box--input'
'.watchlist-panel .symbol-search'
```

## How to Test the Fix

1. **Load the Updated Script**
   - Refresh Tradovate page
   - Ensure the updated modular Tampermonkey script is loaded

2. **Run Diagnostic Script**
   ```javascript
   // Copy and paste scripts/tampermonkey/diagnose_symbol_inputs.js into console
   // This will show all symbol inputs and their locations
   ```

3. **Test Symbol Change**
   - Change symbol in autoOrder UI (e.g., from NQ to MNQ)
   - Observe console logs - should show:
     - `inTradingTicket: true`
     - `inMarketAnalyzer: false`
   - Verify order ticket updates but market analyzer doesn't

4. **Run Test Script**
   ```javascript
   // Copy and paste scripts/test_symbol_update.js into console
   // This will automatically test the functionality
   ```

3. **Test Symbol Updates**
   - Change symbol in autoOrder UI
   - Verify order ticket updates
   - Verify market analyzer doesn't change (unless desired)
   - Place test order to confirm correct symbol

4. **Add Fallback Logic**
   ```javascript
   function updateOrderTicketSymbol(symbol) {
       const selectors = [
           '.trading-ticket input[type="text"]',
           '.order-entry .symbol-input',
           '.trade-panel .contract-search',
           '.search-box--input' // fallback
       ];
       
       for (const selector of selectors) {
           const element = document.querySelector(selector);
           if (element) {
               updateSymbolDirect(element, symbol);
               console.log(`Updated symbol using selector: ${selector}`);
               break;
           }
       }
   }
   ```

## Testing Checklist

- [ ] Symbol updates in order ticket when changed in autoOrder UI
- [ ] Market analyzer remains unchanged (or updates if desired)
- [ ] Orders are placed with correct symbol
- [ ] Symbol persists in localStorage
- [ ] Default values (SL/TP) update based on new symbol
- [ ] Works with both root symbols (NQ) and full contracts (NQZ5)

## Quick Fix (Temporary)

If you need a quick fix while we investigate the correct selectors:

```javascript
// In autoOrder.user.js, line 265
// Comment out the problematic line
// updateSymbol('.search-box--input', normalizedSymbol);

// Add manual instructions
alert(`Please manually update the order ticket symbol to: ${normalizedSymbol}`);
```

## Next Steps

1. Inspect Tradovate's DOM to find exact selectors
2. Test with different Tradovate layouts/themes
3. Consider adding a configuration option for the selector
4. Submit PR with permanent fix

## Related Files

- `/scripts/tampermonkey/modules/uiPanel.js` - UI event wiring
- `/scripts/tampermonkey/modules/autoDriver.js` - Automation driver with `updateSymbol`
- Bundled outputs in `/scripts/tampermonkey/dist/`

## References

- [Tradovate Web Platform](https://trader.tradovate.com/)
- [Chrome DevTools Selectors](https://developer.chrome.com/docs/devtools/css/reference/#select)
